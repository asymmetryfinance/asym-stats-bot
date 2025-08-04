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
    """Fetch total USDaf TVL from DeFiLlama + Curve pool"""
    try:
        # Get main TVL from DeFiLlama
        res = httpx.get("https://api.llama.fi/tvl/asymmetry-usdaf")
        main_tvl = res.json()
        
        # Get Curve pool TVL (half value to avoid double counting)
        curve_tvl = fetch_curve_pool_tvl()
        
        # Return combined TVL
        total_tvl = main_tvl + curve_tvl
        return total_tvl
    except Exception:
        # Fallback to just Curve pool if main TVL fails
        return fetch_curve_pool_tvl()


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
