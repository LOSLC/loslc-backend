from app.core.services.ai.translation import SupportedLanguages, translate


async def translate_text(text: str, language: SupportedLanguages):
    translated_text = await translate(text=text, language=language)
    return translated_text
