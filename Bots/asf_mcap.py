import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

install()
load_dotenv()

ASF_MCAP_BOT_TOKEN = os.getenv("ASF_MCAP_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


def fetch_asf_price(search_width: str = "4h"):
    # Fetch ASF price from Defillama API
    res = httpx.get(
        f"https://coins.llama.fi/prices/current/coingecko:asymmetry-finance?searchWidth={search_width}"
    )
    price = res.json()["coins"]["coingecko:asymmetry-finance"]["price"]
    return price


def fetch_asf_mcap():
    price = fetch_asf_price()

    # Fetch ASF mcap
    res = httpx.get("https://app.asymmetry.finance/api/asf_circulating_supply")
    circ_supply = res.json()

    mcap = price * circ_supply
    return f"${mcap / 1_000_000:.2f}M"


async def send_update(bot: hikari.GatewayBot):
    mcap = fetch_asf_mcap()
    await bot.rest.edit_my_member(GUILD_ID, nickname=mcap)
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=ASF_MCAP_BOT_TOKEN)

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
                name="ASF Market Cap",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
