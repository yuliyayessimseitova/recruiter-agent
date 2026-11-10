import os
import httpx
from .anonymizer import Anonymizer

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
SYSTEM = (
    "Ты помощник рекрутера в Казахстане. По заявке на вакансию составь продающее, "
    "честное описание для публикации в Telegram: заголовок, о компании, чем предстоит "
    "заниматься, требования, условия, как откликнуться. Без выдуманных фактов, "
    "без дискриминационных требований (пол, возраст, семейное положение). Коротко, до 1500 знаков. "
    "Метки вида [NAME_1] оставляй как есть."
)


async def generate_vacancy(request_text: str) -> str:
    an = Anonymizer()
    safe = an.anonymize(request_text)
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": os.environ["ANTHROPICBOT_API_KEY"],
                     "anthropic-version": "2023-06-01"},
            json={"model": MODEL, "max_tokens": 1200, "system": SYSTEM,
                  "messages": [{"role": "user", "content": safe}]},
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
    return an.restore(text)
