import os
import httpx
from .anonymizer import Anonymizer

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
SYSTEM = (
    "Ты помощник рекрутера в Казахстане. По заявке на вакансию составь продающее, "
    "честное описание для публикации в Telegram: заголовок, о компании, чем предстоит "
    "заниматься, требования, условия, как откликнуться. Без выдуманных фактов, "
    "без дискриминационных требований (пол, возраст, семейное положение). Коротко, до 1500 знаков. "
    "Работодатель — компания Smart HR Group (всегда называй её в тексте, это не персональные данные). "
    "Формат: обычный текст без Markdown (без #, **, _), допускаются эмодзи в заголовках разделов. "
    "Не пиши контакты, телефоны и способ отклика — ссылку для отклика добавит система. "
    "Метки вида [NAME_1] не используй."
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
    import re
    text = an.restore(text)
    text = re.sub(r"\[[A-Z]+_\d+\]|\[CONTACT\]", "", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M).replace("**", "")
    return text.strip()
