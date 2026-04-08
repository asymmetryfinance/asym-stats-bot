import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

install()
load_dotenv()

ASF_PRICE_BOT_TOKEN = os.getenv("ASF_PRICE_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


def fetch_asf_price(search_width: str = "4h"):
    # Fetch ASF price from Defillama API
    res = httpx.get(
        f"https://coins.llama.fi/prices/current/coingecko:asymmetry-finance?searchWidth={search_width}"
    )
    price = res.json()["coins"]["coingecko:asymmetry-finance"]["price"]
    return f"${price:.2f}"


async def send_update(bot: hikari.GatewayBot):
    price = fetch_asf_price()
    await bot.rest.edit_my_member(GUILD_ID, nickname=price)
    await asyncio.sleep(300)


async def run():
    bot = hikari.GatewayBot(token=ASF_PRICE_BOT_TOKEN)

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
                name="ASF Price",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
