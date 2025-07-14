from typing import Literal

from app.core.services.ai.providers import LLMProvider

SupportedLanguages = Literal[
    "English", "French", "Chinese", "Japanese", "Spanish", "German"
]


async def translate(text: str, language: SupportedLanguages):
    translation_provider = LLMProvider(model="gemini")
    translated_text = await translation_provider.ask(
        message=f"Translate this text into {language}"
        f'do not comment and be straigtforward. "\n{text}"'
    )
    return translated_text


async def translate_json(json_data: str, language: SupportedLanguages):
    translation_provider = LLMProvider(model="gemini")
    translated_text = await translation_provider.ask(
        message=f"Translate this json into {language} in the same json format."
        + "only translate titles, labels, descriptions and possible answers"
        + "You are a translator. ONLY return raw JSON."
        + "Do NOT use markdown formatting or code blocks."
        + "You do not need to format your answer."
        f"do not comment and be straigtforward. \n{json_data}"
    )
    return translated_text
