import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

install()
load_dotenv()

USDAF_TVL_BOT_TOKEN = os.getenv("USDAF_TVL_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


def format_tvl(tvl: float) -> str:
    # Always format in millions to match supply formatting
    return f"${tvl / 1_000_000:.2f}M"


def fetch_curve_pool_tvl():
    """Fetch USDaf Curve pool TVL and return half to avoid double counting"""
    try:
        # Use httpx with SSL verification disabled to handle certificate issues
        res = httpx.get(
            "https://api.curve.finance/api/getPools/ethereum/factory-stable-ng",
            verify=False,
            timeout=30.0
        )
        data = res.json()
        
        # Find the USDaf pool (factory-stable-ng-516)
        for pool in data['data']['poolData']:
            if pool['id'] == 'factory-stable-ng-516':
                # Return half the pool value to avoid double counting USDaf
                return pool['usdTotal'] / 2
        
        return 0
    except Exception:
        return 0


def fetch_usdaf_tvl():
    """Fetch USDaf TVL from Asymmetry Finance API"""
    try:
        # Get TVL from Asymmetry Finance API
        res = httpx.get("https://asymmetryfinance.github.io/api.usdafv2/docs/v2/mainnet.json")
        data = res.json()
        
        # Extract total_value_locked and convert to float
        total_value_locked = float(data["total_value_locked"])
        return total_value_locked
    except Exception:
        # Return 0 if API call fails
        return 0


async def send_update(bot: hikari.GatewayBot):
    tvl = fetch_usdaf_tvl()
    formatted_tvl = format_tvl(tvl)
    await bot.rest.edit_my_member(GUILD_ID, nickname=formatted_tvl)
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=USDAF_TVL_BOT_TOKEN)

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
                name="USDaf TVL",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
