import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

install()
load_dotenv()

GLOBAL_TVL_BOT_TOKEN = os.getenv("GLOBAL_TVL_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


def format_tvl(tvl: float) -> str:
    if tvl >= 1_000_000:
        return f"${tvl / 1_000_000:.2f}M"
    return f"${round(tvl, 2):,}"


def fetch_global_tvl():
    res = httpx.get("https://asymmetry.finance/api/tvl", follow_redirects=True)
    tvl = res.json()["asymmetryTVL"]
    return tvl


async def send_update(bot: hikari.GatewayBot):
    tvl = fetch_global_tvl()
    formatted_tvl = format_tvl(tvl)
    await bot.rest.edit_my_member(GUILD_ID, nickname=formatted_tvl)
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=GLOBAL_TVL_BOT_TOKEN)

    @bot.listen()
    async def on_ready(event: hikari.ShardReadyEvent):
        while True:
            try:
                await send_update(bot)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in send_update: {e}")
                await asyncio.sleep(60)

    try:
        await bot.start(
            activity=hikari.Activity(
                name="ASF TVL",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
