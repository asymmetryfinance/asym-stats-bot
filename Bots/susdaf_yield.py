import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

install()
load_dotenv()

SUSDAF_APY_BOT_TOKEN = os.getenv("SUSDAF_APY_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


def fetch_susdaf_apy():
    url = "https://kong.yearn.farm/api/gql"
    query = """
    query Apy {
        vault(chainId: 1, address: "0x89E93172AEF8261Db8437b90c3dCb61545a05317") {
            apy {
            net
            }
        }
    }
    """
    res = httpx.post(
        url,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"query": query},
    )
    apy = res.json()["data"]["vault"]["apy"]["net"]
    return apy


async def send_update(bot: hikari.GatewayBot):
    apy = fetch_susdaf_apy()
    formatted_apy = f"{round(apy * 100, 2)}%"
    await bot.rest.edit_my_member(GUILD_ID, nickname=formatted_apy)
    await asyncio.sleep(300)


async def run():
    bot = hikari.GatewayBot(token=SUSDAF_APY_BOT_TOKEN)

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
                name="sUSDaf APY",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
