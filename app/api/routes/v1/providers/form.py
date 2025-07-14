from datetime import date
from uuid import UUID

import phonenumbers
from fastapi import HTTPException, Response
from pydantic import EmailStr, HttpUrl, TypeAdapter, constr
from sqlmodel import Session, select
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.routes.v1.dto.form import (
    FormFieldType,
    FormTranslationModel,
    ResponseCreationDTO,
)
from app.api.routes.v1.dto.message import MessageResponse
from app.core.db.builders.permission import PermissionBuilder
from app.core.db.builders.role import RoleBuilder
from app.core.db.models import (
    AnswerSession,
    FieldAnswer,
    Form,
    FormField,
    User,
)
from app.core.logging.log import log_warning
from app.core.security.checkers import (
    check_conditions,
    check_existence,
)
from app.core.security.permissions import (
    ACTION_READWRITE,
    ADMIN_ROLE_NAME,
    FORM_FIELD_RESOURCE,
    FORM_FIELD_RESPONSE_RESOURCE,
    FORM_RESOURCE,
    SUPER_ADMIN_ROLE_NAME,
    GlobalPermissionCheckModel,
    PermissionChecker,
    PermissionCheckModel,
)
from app.core.services.ai.translation import (
    SupportedLanguages,
    translate,
    translate_json,
)

ANSWER_SESSION_COOKIE_KEY = "response_session_id"


async def create_form(
    db_session: Session,
    current_user: User,
    title: str,
    description: str | None = None,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=FORM_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()
    form = Form(user_id=current_user.id, label=title, description=description)
    rw_role = RoleBuilder().addUser(current_user).make()
    rw_permission = (
        PermissionBuilder()
        .withResourceName(FORM_RESOURCE)
        .withActionName(ACTION_READWRITE)
        .withResourceId(form.id)
        .forRole(rw_role)
    ).make()
    db_session.add_all([form, rw_role, rw_permission])
    db_session.commit()
    db_session.refresh(form)
    return form.to_dto()


async def translate_form(
    db_session: Session, form_id: UUID, language: SupportedLanguages
):
    form = check_existence(db_session.get(Form, form_id))
    form_fields = [form_field.to_dto() for form_field in form.fields]
    data = FormTranslationModel(form=form.to_dto(), fields=form_fields)
    translated_form = await translate_json(
        json_data=data.model_dump_json(), language=language
    )
    log_warning(translated_form)
    return FormTranslationModel.model_validate_json(translated_form)




async def add_field_to_form(
    db_session: Session,
    current_user: User,
    form_id: UUID,
    field_label: str,
    field_description: str,
    field_type: FormFieldType,
    required: bool = True,
    possible_answers: str | None = None,
    number_bounds: str | None = None,
    text_bounds: str | None = None,
):
    PermissionChecker(
        db_session=db_session,
        bypass_role=SUPER_ADMIN_ROLE_NAME,
        roles=current_user.roles,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            ),
            GlobalPermissionCheckModel(
                resource_name=FORM_FIELD_RESOURCE,
                action_names=[ACTION_READWRITE],
            ),
        ],
    ).check(either=True)
    field = FormField(
        form_id=form_id,
        label=field_label,
        description=field_description,
        field_type=field_type,
        required=required,
    )
    check_conditions(
        [
            not (field_type == "Select" and possible_answers is None),
            not (field_type == "Multiselect" and possible_answers is None),
        ]
    )
    field.possible_answers = possible_answers
    field.number_bounds = number_bounds
    field.text_bounds = text_bounds

    rw_role = RoleBuilder().addUser(current_user).make()
    rw_permission = (
        PermissionBuilder()
        .withResourceName(FORM_FIELD_RESOURCE)
        .withResourceId(field.id)
        .withActionName(ACTION_READWRITE)
        .forRole(rw_role)
    ).make()
    db_session.add_all([field, rw_role, rw_permission])
    db_session.commit()
    db_session.refresh(field)
    return field.to_dto()


async def delete_field(
    db_session: Session, current_user: User, field_id: UUID
):
    field = check_existence(db_session.get(FormField, field_id))
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_FIELD_RESOURCE,
                resource_id=field_id,
                action_names=[ACTION_READWRITE],
            ),
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=field.form_id,
                action_names=[ACTION_READWRITE],
            ),
        ],
    ).check()
    db_session.delete(field)
    db_session.commit()
    return MessageResponse(message="Field deleted successfully !")


def validate_answer(answer: str | None, field: FormField):
    number_bounds = (
        [int(bound) for bound in field.number_bounds.split(":")]
        if field.number_bounds is not None
        else None
    )
    text_bounds = (
        [int(bound) for bound in field.text_bounds.split(":")]
        if field.text_bounds is not None
        else None
    )
    possible_answers = (
        [field.strip() for field in field.possible_answers.split("\\")]
        if field.possible_answers is not None
        else None
    )

    value = str(answer or "")
    try:
        check_conditions(
            [
                not (
                    field.required is True and (answer is None or answer == "")
                ),
                not (
                    field.field_type == "Boolean" and answer not in ["0", "1"]
                ),
                not (
                    field.field_type == "Multiselect"
                    and any(
                        value not in (possible_answers or [])
                        for value in (answer or "").split(",")
                    )
                ),
                not (
                    field.field_type == "Select"
                    and answer not in (possible_answers or [])
                ),
                not (
                    field.field_type == "Numerical"
                    and number_bounds is not None
                    and (
                        not value.isdigit()
                        or not (
                            int(value) >= (number_bounds or [0, 0])[0]
                            and int(value) <= (number_bounds or [0, 0])[1]
                        )
                    )
                ),
                not (
                    (
                        field.field_type == "Text"
                        or field.field_type == "LongText"
                    )
                    and text_bounds is not None
                    and not (
                        len(value) >= (text_bounds or [0, 0])[0]
                        and len(value) <= (text_bounds or [0, 0])[1]
                    )
                ),
            ],
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not validate answer",
        )
        # Pydantic validation
        match field.field_type:
            case "Email":
                TypeAdapter(EmailStr).validate_python(value)
            case "Phone":
                try:
                    parsed_phonenumber = phonenumbers.parse(value)
                    check_conditions(
                        [phonenumbers.is_valid_number(parsed_phonenumber)]
                    )
                except phonenumbers.NumberParseException:
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY
                    )
            case "Date":
                TypeAdapter(date).validate_python(value)
            case "URL":
                TypeAdapter(HttpUrl).validate_python(value)
            case "Alpha":
                AlphaStr = constr(pattern=r"^[a-zA-Z ]+$")
                TypeAdapter(AlphaStr).validate_python(value)
            case "Alphanum":
                AlphanumStr = constr(pattern=r"^[a-zA-Z0-9 ]+$")
                TypeAdapter(AlphanumStr).validate_python(value)
    except Exception:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY)


async def respond_to_field(
    api_response: Response,
    db_session: Session,
    response_data: ResponseCreationDTO,
    response_session_id: UUID | None,
):
    field = check_existence(db_session.get(FormField, response_data.field_id))
    check_conditions([field.form.open is True])
    response_session: AnswerSession
    if response_session_id is not None:
        response_session = check_existence(
            db_session.get(AnswerSession, response_session_id)
        )
    else:
        new_rs = AnswerSession(form_id=field.form_id)
        db_session.add(new_rs)
        db_session.commit()
        db_session.refresh(new_rs)
        response_session = new_rs
    answer_fields = [
        response
        for response in response_session.answers
        if response.field.id == field.id
    ]
    field_already_answered = len(answer_fields) > 0
    response = (
        FieldAnswer(field_id=field.id, session_id=response_session.id)
        if not field_already_answered
        else answer_fields[0]
    )
    validate_answer(answer=response_data.value, field=field)
    response.value = response_data.value
    db_session.add(response)
    db_session.commit()
    api_response.set_cookie(
        key="response_session_id",
        value=str(response_session.id),
        httponly=True,
    )
    return response.to_dto()


async def edit_response(
    db_session: Session,
    answer_id: UUID,
    answer_session_id: str | None,
    value: str,
):
    check_existence(
        db_session.get(
            AnswerSession,
            check_existence(
                answer_session_id, detail="Answer session not found."
            ),
        ),
        detail="Answer session not found.",
    )
    answer = check_existence(db_session.get(FieldAnswer, answer_id))
    field: FormField = check_existence(
        db_session.get(FormField, answer.field_id)
    )
    validate_answer(value, field)
    answer.value = value
    db_session.add(answer)
    db_session.commit()


async def delete_response(
    db_session: Session,
    current_user: User | None,
    answer_id: UUID,
    answer_session_id: str | None,
):
    answer = check_existence(db_session.get(FieldAnswer, answer_id))
    if answer_session_id is None:
        PermissionChecker(
            db_session=db_session,
            bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
            roles=(check_existence(current_user)).roles,
            pcheck_models=[
                GlobalPermissionCheckModel(
                    resource_name=FORM_FIELD_RESPONSE_RESOURCE,
                    action_names=[ACTION_READWRITE],
                )
            ],
        ).check()
    else:
        check_existence(
            db_session.get(AnswerSession, check_existence(answer_session_id)),
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to delete this resource",
        )
    db_session.delete(answer)
    db_session.commit()
    return MessageResponse(message="Answer deleted.")


async def submit(
    db_session: Session, answer_session_id: UUID | None, response: Response
):
    answer_session = check_existence(
        db_session.get(
            AnswerSession,
            check_existence(
                answer_session_id, detail="Answer session not found."
            ),
        )
    )

    all_required_fields = db_session.exec(
        select(FormField).where(
            FormField.required == True,
            FormField.form_id == answer_session.form_id,
        )
    ).all()
    answered_required_fields = db_session.exec(
        select(FormField)
        .where(
            FormField.required == True,
            FormField.form_id == answer_session.form_id,
        )
        .join(FieldAnswer)
        .where(FieldAnswer.session_id == answer_session.id)
    ).all()

    for form_field in all_required_fields:
        check_conditions(
            [form_field in answered_required_fields],
            detail=f"Field '{form_field.label}' not answered.",
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        )

    answer_session.submitted = True
    db_session.add(answer_session)
    db_session.commit()
    response.delete_cookie(ANSWER_SESSION_COOKIE_KEY)
    return MessageResponse(message="Responses submitted.")


async def close_form(db_session: Session, current_user: User, form_id: UUID):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=SUPER_ADMIN_ROLE_NAME,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()
    form = check_existence(db_session.get(Form, form_id))
    form.open = False
    db_session.add(form)
    db_session.commit()
    return MessageResponse(message="Form closed.")


async def open_form(
    db_session: Session,
    current_user: User,
    form_id: UUID,
):
    """Open a form to allow new responses"""
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_role=SUPER_ADMIN_ROLE_NAME,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()
    form = check_existence(db_session.get(Form, form_id))
    form.open = True
    db_session.add(form)
    db_session.commit()
    return MessageResponse(message="Form opened.")


async def get_answer_session(
    db_session: Session, answer_session_id: UUID | None
):
    answer_session = check_existence(
        db_session.get(AnswerSession, check_existence(answer_session_id))
    )
    return answer_session.to_dto()


async def get_responses(
    db_session: Session,
    current_user: User,
    form_id: UUID,
    skip: int,
    limit: int,
):
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_roles=[SUPER_ADMIN_ROLE_NAME, ADMIN_ROLE_NAME],
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()
    form = check_existence(db_session.get(Form, form_id))
    answer_sessions = check_existence(
        (
            db_session.exec(
                select(AnswerSession)
                .where(
                    AnswerSession.form_id == form.id,
                    AnswerSession.submitted == True,
                )
                .offset(skip)
                .limit(limit)
            )
        ).all()
    )
    return [answer_session.to_dto() for answer_session in answer_sessions]


async def get_forms(
    db_session: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 10,
):
    """Get all forms with pagination - Admin only"""
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
        pcheck_models=[
            GlobalPermissionCheckModel(
                resource_name=FORM_RESOURCE, action_names=[ACTION_READWRITE]
            )
        ],
    ).check()

    statement = select(Form).offset(skip).limit(limit)
    forms = (db_session.exec(statement)).all()
    return [form.to_dto() for form in forms]


async def get_form_by_id(
    db_session: Session,
    form_id: UUID,
    current_user: User | None = None,
):
    """Get a specific form by ID - Public access for form filling"""
    form = check_existence(db_session.get(Form, form_id))
    if not form.open:
        PermissionChecker(
            db_session=db_session,
            roles=(check_existence(current_user)).roles,
            bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
            pcheck_models=[
                PermissionCheckModel(
                    resource_name=FORM_RESOURCE,
                    resource_id=form_id,
                    action_names=[ACTION_READWRITE],
                )
            ],
        ).check()
    return form.to_dto()


async def get_form_fields(
    db_session: Session,
    form_id: UUID,
    current_user: User | None = None,
):
    """Get all fields for a specific form - Public access for form filling"""
    form = check_existence(db_session.get(Form, form_id))
    if not form.open:
        PermissionChecker(
            db_session=db_session,
            roles=(check_existence(current_user)).roles,
            bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
            pcheck_models=[
                PermissionCheckModel(
                    resource_name=FORM_RESOURCE,
                    resource_id=form_id,
                    action_names=[ACTION_READWRITE],
                )
            ],
        ).check()
    return [field.to_dto() for field in form.fields]


async def update_form(
    db_session: Session,
    current_user: User,
    form_id: UUID,
    title: str | None = None,
    description: str | None = None,
):
    """Update form details"""
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()

    form = check_existence(db_session.get(Form, form_id))

    if title is not None:
        form.label = title
    if description is not None:
        form.description = description

    db_session.add(form)
    db_session.commit()
    db_session.refresh(form)
    return form.to_dto()


async def delete_form(
    db_session: Session,
    current_user: User,
    form_id: UUID,
):
    """Delete a form"""
    PermissionChecker(
        db_session=db_session,
        roles=current_user.roles,
        bypass_roles=[ADMIN_ROLE_NAME, SUPER_ADMIN_ROLE_NAME],
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=form_id,
                action_names=[ACTION_READWRITE],
            )
        ],
    ).check()

    form = check_existence(db_session.get(Form, form_id))
    db_session.delete(form)
    db_session.commit()
    return MessageResponse(message="Form deleted successfully")


async def update_form_field(
    db_session: Session,
    current_user: User,
    field_id: UUID,
    field_label: str | None = None,
    field_description: str | None = None,
    field_position: int | None = None,
    field_type: FormFieldType | None = None,
    required: bool | None = None,
    possible_answers: str | None = None,
    number_bounds: str | None = None,
    text_bounds: str | None = None,
):
    """Update a form field"""
    field = check_existence(db_session.get(FormField, field_id))

    PermissionChecker(
        db_session=db_session,
        bypass_role=SUPER_ADMIN_ROLE_NAME,
        roles=current_user.roles,
        pcheck_models=[
            PermissionCheckModel(
                resource_name=FORM_FIELD_RESOURCE,
                resource_id=field_id,
                action_names=[ACTION_READWRITE],
            ),
            PermissionCheckModel(
                resource_name=FORM_RESOURCE,
                resource_id=field.form_id,
                action_names=[ACTION_READWRITE],
            ),
        ],
    ).check(either=True)

    if field_label is not None:
        field.label = field_label
    if field_description is not None:
        field.description = field_description
    if field_type is not None:
        field.field_type = field_type
    if required is not None:
        field.required = required
    if possible_answers is not None:
        field.possible_answers = possible_answers
    if number_bounds is not None:
        field.number_bounds = number_bounds
    if text_bounds is not None:
        field.text_bounds = text_bounds
    if field_position is not None:
        field.position = field_position

    db_session.add(field)
    db_session.commit()
    db_session.refresh(field)
    return field.to_dto()


async def get_user_forms(
    db_session: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 10,
):
    """Get forms created by the current user"""
    statement = (
        select(Form)
        .where(Form.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    forms = (db_session.exec(statement)).all()
    return [form.to_dto() for form in forms]
