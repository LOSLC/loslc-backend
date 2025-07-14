from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlmodel import Session

from app.api.routes.v1.dto.form import (
    AnswerSessionDTO,
    FieldResponseDTO,
    FormCreationDTO,
    FormDTO,
    FormFieldCreationDTO,
    FormFieldDTO,
    FormFieldUpdateDTO,
    FormTranslationModel,
    FormUpdateDTO,
    ResponseCreationDTO,
)
from app.api.routes.v1.dto.message import MessageResponse
from app.api.routes.v1.providers import form as form_provider
from app.api.routes.v1.providers.auth import (
    get_current_user,
    get_current_user_optional,
)
from app.core.db.models import User
from app.core.db.setup import create_db_session
from app.core.services.ai.translation import SupportedLanguages

router = APIRouter(prefix="/forms", tags=["Forms"])

ANSWER_SESSION_COOKIE_KEY = "response_session_id"

DBSessionDependency = Annotated[Session, Depends(create_db_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]
OptionalUserDependency = Annotated[
    User | None, Depends(get_current_user_optional)
]
CurrentAnswerSessionDependency = Annotated[
    str | None, Cookie(alias=ANSWER_SESSION_COOKIE_KEY)
]


# Form CRUD Operations (Admin/Owner Access)
@router.post("", response_model=FormDTO, status_code=status.HTTP_201_CREATED)
async def create_form(
    form_data: FormCreationDTO,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Create a new form"""
    return await form_provider.create_form(
        db_session=db_session,
        current_user=current_user,
        title=form_data.label,
        description=form_data.description,
    )


@router.get("/", response_model=List[FormDTO])
async def get_all_forms(
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
    skip: int = 0,
    limit: int = 10,
):
    """Get all forms (Admin only)"""
    return await form_provider.get_forms(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get("/my", response_model=List[FormDTO])
async def get_user_forms(
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
    skip: int = 0,
    limit: int = 10,
):
    """Get forms created by the current user"""
    return await form_provider.get_user_forms(
        db_session=db_session,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get("/{form_id}", response_model=FormDTO)
async def get_form(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: OptionalUserDependency,
):
    """Get a specific form by ID (Public for form filling)"""
    return await form_provider.get_form_by_id(
        db_session=db_session,
        form_id=form_id,
        current_user=current_user,
    )


@router.post("/{form_id}/translate", response_model=FormTranslationModel)
async def translate_form(
    db_session: DBSessionDependency,
    form_id: UUID,
    language: SupportedLanguages,
):
    return await form_provider.translate_form(
        db_session=db_session, form_id=form_id, language=language
    )


@router.put("/{form_id}", response_model=FormDTO)
async def update_form(
    form_id: UUID,
    form_data: FormUpdateDTO,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Update a form"""
    return await form_provider.update_form(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
        title=form_data.label,
        description=form_data.description,
    )


@router.delete("/{form_id}", response_model=MessageResponse)
async def delete_form(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Delete a form"""
    return await form_provider.delete_form(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
    )


@router.post("/{form_id}/close", response_model=MessageResponse)
async def close_form(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Close a form to prevent new responses"""
    return await form_provider.close_form(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
    )


@router.post("/{form_id}/open", response_model=MessageResponse)
async def open_form(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Open a form to allow new responses"""
    return await form_provider.open_form(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
    )


# Form Field Operations
@router.get("/{form_id}/fields", response_model=List[FormFieldDTO])
async def get_form_fields(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: OptionalUserDependency,
):
    """Get all fields for a form (Public for form filling)"""
    return await form_provider.get_form_fields(
        db_session=db_session,
        form_id=form_id,
        current_user=current_user,
    )


@router.post(
    "/{form_id}/fields",
    response_model=FormFieldDTO,
    status_code=status.HTTP_201_CREATED,
)
async def add_field_to_form(
    form_id: UUID,
    field_data: FormFieldCreationDTO,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Add a field to a form"""
    return await form_provider.add_field_to_form(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
        field_label=field_data.label,
        field_description=field_data.description,
        field_type=field_data.field_type,
        required=field_data.required,
        possible_answers=field_data.possible_answers,
        number_bounds=field_data.number_bounds,
        text_bounds=field_data.text_bounds,
    )


@router.put("/fields/{field_id}", response_model=FormFieldDTO)
async def update_form_field(
    field_id: UUID,
    field_data: FormFieldUpdateDTO,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Update a form field"""
    return await form_provider.update_form_field(
        db_session=db_session,
        current_user=current_user,
        field_id=field_id,
        field_label=field_data.label,
        field_description=field_data.description,
        field_position=field_data.position,
        field_type=field_data.field_type,
        required=field_data.required,
        possible_answers=field_data.possible_answers,
        number_bounds=field_data.number_bounds,
        text_bounds=field_data.text_bounds,
    )


@router.delete("/fields/{field_id}", response_model=MessageResponse)
async def delete_form_field(
    field_id: UUID,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """Delete a form field"""
    return await form_provider.delete_field(
        db_session=db_session,
        current_user=current_user,
        field_id=field_id,
    )


# Form Response Operations (Public endpoints for form filling)
@router.post(
    "/responses",
    response_model=FieldResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def respond_to_field(
    response: Response,
    response_data: ResponseCreationDTO,
    db_session: DBSessionDependency,
    response_session_id: CurrentAnswerSessionDependency = None,
):
    """Submit a response to a form field (Public endpoint)"""
    return await form_provider.respond_to_field(
        api_response=response,
        db_session=db_session,
        response_data=response_data,
        response_session_id=UUID(response_session_id)
        if response_session_id
        else None,
    )


@router.put("/responses/{answer_id}")
async def edit_response(
    answer_id: UUID,
    value: str,
    db_session: DBSessionDependency,
    answer_session_id: CurrentAnswerSessionDependency = None,
):
    """Edit a response (Public endpoint with session validation)"""
    return await form_provider.edit_response(
        db_session=db_session,
        answer_id=answer_id,
        answer_session_id=answer_session_id,
        value=value,
    )


@router.delete("/responses/{answer_id}", response_model=MessageResponse)
async def delete_response(
    answer_id: UUID,
    db_session: DBSessionDependency,
    current_user: OptionalUserDependency,
    answer_session_id: CurrentAnswerSessionDependency = None,
):
    """Delete a response"""
    return await form_provider.delete_response(
        db_session=db_session,
        current_user=current_user,
        answer_id=answer_id,
        answer_session_id=answer_session_id,
    )


@router.post("/sessions/submit", response_model=MessageResponse)
async def submit_responses(
    response: Response,
    db_session: DBSessionDependency,
    answer_session_id: CurrentAnswerSessionDependency = None,
):
    """Submit all responses in a session (Public endpoint)"""
    return await form_provider.submit(
        db_session=db_session,
        response=response,
        answer_session_id=UUID(answer_session_id),
    )


@router.get("/sessions", response_model=AnswerSessionDTO)
async def get_answer_session(
    db_session: DBSessionDependency,
    answer_session_id: Annotated[
        UUID | None, Cookie(alias=ANSWER_SESSION_COOKIE_KEY)
    ] = None,
):
    """Get an answer session (Public endpoint for session management)"""
    return await form_provider.get_answer_session(
        db_session=db_session,
        answer_session_id=answer_session_id,
    )


# Form Response Management (Admin/Owner Access)
@router.get("/{form_id}/responses", response_model=List[AnswerSessionDTO])
async def get_form_responses(
    form_id: UUID,
    db_session: DBSessionDependency,
    current_user: CurrentUserDependency,
    skip: int = 0,
    limit: int = 10,
):
    """Get all responses for a form (Admin/Owner only)"""
    return await form_provider.get_responses(
        db_session=db_session,
        current_user=current_user,
        form_id=form_id,
        skip=skip,
        limit=limit,
    )
