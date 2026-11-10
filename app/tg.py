import os
import httpx

API = "https://api.telegram.org/bot{}/{}"


async def call(method: str, **params):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(API.format(os.environ["RECRUITER_BOT_TOKEN"], method), json=params)
        return r.json()
