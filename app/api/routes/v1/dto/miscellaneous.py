from pydantic import BaseModel, Field

from app.core.services.ai.translation import SupportedLanguages


class TextTranslationDTO(BaseModel):
    input: str = Field(max_length=1000)
    language: SupportedLanguages
