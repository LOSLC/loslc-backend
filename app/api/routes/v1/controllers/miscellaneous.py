from fastapi import APIRouter

from app.api.routes.v1.dto.miscellaneous import TextTranslationDTO
from app.api.routes.v1.providers import miscellaneous as miscellaneous_provider

router = APIRouter(prefix="/miscellaneous", tags=["Miscellaneous"])


@router.post("/translate")
async def translate_text(data: TextTranslationDTO):
    return await miscellaneous_provider.translate_text(
        text=data.input, language=data.language
    )
