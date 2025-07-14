from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class LinkCreationDTO(BaseModel):
    label: str = Field(pattern=r"^[a-zA-Z0-9-]+$")
    url: HttpUrl
    description: str | None = None


class LinkUpdateDTO(BaseModel):
    id: str
    label: str = Field(pattern=r"^[a-zA-Z0-9-]+$")
    url: HttpUrl
    description: str | None = None


class LinkDTO(BaseModel):
    id: str
    label: str
    url: str
    description: str | None = None
    created_at: datetime
    author_id: str
