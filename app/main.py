import os
import hashlib
from fastapi import FastAPI, Request, HTTPException
from . import tg
from .llm import generate_vacancy

app = FastAPI()
TOKEN = os.environ.get("RECRUITER_BOT_TOKEN", "")
SECRET = hashlib.sha256(("wh" + TOKEN).encode()).hexdigest()[:32]
CHANNEL = os.environ.get("TEST_CHANNEL_ID", "")
BOT = {"username": os.environ.get("BOT_USERNAME", "")}
VACANCIES: dict[str, str] = {}
DRAFTS: dict[int, str] = {}  # демо: черновики в памяти
WAIT: set[int] = set()

HELP = ("Я помощник рекрутера (демо).\n/new — новая заявка на вакансию.\n"
        "Пришлите текст заявки — я подготовлю описание, вы одобрите, и я опубликую в тестовый канал.")
KB = {"inline_keyboard": [[{"text": "Опубликовать", "callback_data": "pub"},
                           {"text": "Отмена", "callback_data": "cancel"}]]}


@app.on_event("startup")
async def startup():
    if TOKEN and not BOT["username"]:
        me = await tg.call("getMe")
        BOT["username"] = me.get("result", {}).get("username", "")
    base = os.environ.get("RENDER_EXTERNAL_URL")
    if base and TOKEN:
        await tg.call("setWebhook", url=f"{base}/webhook/{SECRET}",
                      secret_token=SECRET, allowed_updates=["message", "callback_query"])


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/webhook/{secret}")
async def webhook(secret: str, req: Request):
    if secret != SECRET:
        raise HTTPException(404)
    u = await req.json()
    if "callback_query" in u:
        q = u["callback_query"]
        chat = q["message"]["chat"]["id"]
        await tg.call("answerCallbackQuery", callback_query_id=q["id"])
        if q["data"] == "consent":
            await tg.call("sendMessage", chat_id=chat, text="Спасибо! Первый вопрос: как вас зовут?")
        elif q["data"] == "pub" and chat in DRAFTS:
            if not CHANNEL:
                await tg.call("sendMessage", chat_id=chat, text="Не задан TEST_CHANNEL_ID.")
            else:
                d = DRAFTS[chat]
                vid = hashlib.sha1(d.encode()).hexdigest()[:8]
                VACANCIES[vid] = d.split("\n")[0][:80]
                link = f"https://t.me/{BOT['username']}?start=vac_{vid}"
                r = await tg.call("sendMessage", chat_id=CHANNEL, text=d + f"\n\n👉 Откликнуться: {link}",
                                  reply_markup={"inline_keyboard": [[{"text": "Откликнуться", "url": link}]]})
                await tg.call("sendMessage", chat_id=chat,
                              text="Опубликовано." if r.get("ok") else f"Ошибка публикации: {r.get('description')}. Черновик сохранён, нажмите «Опубликовать» ещё раз после исправления.")
                if r.get("ok"):
                    DRAFTS.pop(chat, None)
        else:
            DRAFTS.pop(chat, None)
            await tg.call("sendMessage", chat_id=chat, text="Отменено.")
        return {"ok": True}
    m = u.get("message")
    if not m or "text" not in m:
        return {"ok": True}
    chat, text = m["chat"]["id"], m["text"]
    if text.startswith("/start vac_"):
        vid = text.split("vac_", 1)[1].strip()
        title = VACANCIES.get(vid, "вакансию")
        await tg.call("sendMessage", chat_id=chat, text=(
            f"Здравствуйте! Это бот Smart HR Group. Вы откликаетесь на: {title}.\n\n"
            "Я задам несколько вопросов для первичной оценки. Для этого нужно ваше согласие на обработку "
            "персональных данных (ФИО, контакты, опыт работы) для целей подбора. Данные можно удалить по запросу.\n\n"
            "Нажмите «Согласен», чтобы продолжить."),
            reply_markup={"inline_keyboard": [[{"text": "Согласен", "callback_data": "consent"}]]})
    elif text.startswith("/start"):
        await tg.call("sendMessage", chat_id=chat, text=HELP)
    elif text.startswith("/new"):
        WAIT.add(chat)
        await tg.call("sendMessage", chat_id=chat, text="Пришлите текст заявки одним сообщением.")
    else:
        WAIT.discard(chat)
        await tg.call("sendMessage", chat_id=chat, text="Готовлю описание…")
        try:
            d = await generate_vacancy(text)
        except Exception as e:
            await tg.call("sendMessage", chat_id=chat, text=f"Ошибка ИИ: {type(e).__name__}")
            return {"ok": True}
        DRAFTS[chat] = d
        await tg.call("sendMessage", chat_id=chat, text=d + f"\n\n👉 Откликнуться: https://t.me/{BOT['username']}?start=vac_…\n\nОпубликовать в тестовый канал?", reply_markup=KB)
    return {"ok": True}
