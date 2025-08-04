import asyncio
import os

import hikari
import httpx
from dotenv import load_dotenv
from rich import print
from rich.traceback import install
from web3 import HTTPProvider, Web3

install()
load_dotenv()

USDAF_PRICE_BOT_TOKEN = os.getenv("USDAF_PRICE_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MAINNET_HTTP_RPC_URL = os.getenv("MAINNET_HTTP_RPC_URL")


def fetch_usdaf_price(search_width: str = "4h"):
    # Fetch USDaf price from Defillama API
    res = httpx.get(
        f"https://coins.llama.fi/prices/current/coingecko:asymmetry-usdaf?searchWidth={search_width}"
    )
    price = res.json()["coins"]["coingecko:asymmetry-usdaf"]["price"]
    return f"${price:.2f}"


def fetch_usdaf_supply():
    w3 = Web3(HTTPProvider(MAINNET_HTTP_RPC_URL))
    usdaf_contract = w3.eth.contract(
        address="0x9Cf12ccd6020b6888e4D4C4e4c7AcA33c1eB91f8",
        abi="""[{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]""",
    )
    supply = usdaf_contract.functions.totalSupply().call() / 10**18
    return f"${supply / 1_000_000:.2f}M"


async def send_update(bot: hikari.GatewayBot):
    # price = fetch_usdaf_price()
    supply = fetch_usdaf_supply()
    await bot.rest.edit_my_member(GUILD_ID, nickname=supply)
    # await bot.update_presence(
    #     activity=hikari.Activity(
    #         name=f"{supply} USDaf Total Supply",
    #         type=hikari.ActivityType.WATCHING,
    #     ),
    # )
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=USDAF_PRICE_BOT_TOKEN)

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
                name="USDaf Supply",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
