from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel

FormFieldType = Literal[
    "Boolean",
    "Numerical",
    "Text",
    "LongText",
    "Select",
    "Multiselect",
    "Email",
    "Phone",
    "Currency",
    "Date",
    "URL",
    "Alpha",
    "Alphanum",
]


class FormTranslationModel(BaseModel):
    form: "FormDTO"
    fields: List["FormFieldDTO"]


class FormCreationDTO(BaseModel):
    label: str
    description: str | None = None


class FormUpdateDTO(BaseModel):
    label: str | None = None
    description: str | None = None


class FormDTO(BaseModel):
    id: UUID
    label: str
    description: str | None
    fields_length: int  # Number of fields
    open: bool


class FormFieldCreationDTO(BaseModel):
    form_id: UUID
    label: str
    description: str
    field_type: FormFieldType
    required: bool = True
    possible_answers: str | None = None
    number_bounds: str | None = None  # min:max
    text_bounds: str | None = None  # min:max


class FormFieldUpdateDTO(BaseModel):
    label: str | None = None
    description: str | None = None
    position: int | None = None
    field_type: FormFieldType | None = None
    required: bool | None = None
    possible_answers: str | None = None
    number_bounds: str | None = None  # min:max
    text_bounds: str | None = None  # min:max


class FormFieldDTO(BaseModel):
    id: UUID
    form_id: UUID
    label: str
    description: str
    position: int | None
    required: bool
    field_type: str
    possible_answers: str | None
    number_bounds: str | None  # min:max
    text_bounds: str | None  # min:max


class ResponseCreationDTO(BaseModel):
    field_id: UUID
    value: str | None


class FieldResponseDTO(BaseModel):
    id: UUID
    field_id: UUID
    session_id: UUID
    value: str | None
    field: FormFieldDTO


class AnswerSessionDTO(BaseModel):
    id: UUID
    form_id: UUID
    answers: List[FieldResponseDTO]
    submitted: bool
