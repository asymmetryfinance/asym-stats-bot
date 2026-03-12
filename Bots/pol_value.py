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

POL_VALUE_BOT_TOKEN = os.getenv("POL_VALUE_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MAINNET_HTTP_RPC_URL = os.getenv("MAINNET_HTTP_RPC_URL")
POL_ADDRESS = "0xce352181C0f0350F1687e1a44c45BC9D96ee738B"

w3 = Web3(HTTPProvider(MAINNET_HTTP_RPC_URL))


def fetch_price(coingecko_id: str, search_width: str = "4h"):
    # Fetch token price from Defillama API
    res = httpx.get(
        f"https://coins.llama.fi/prices/current/coingecko:{coingecko_id}?searchWidth={search_width}"
    )
    price = res.json()["coins"][f"coingecko:{coingecko_id}"]["price"]
    return price


def fetch_cvx_value():
    # Fetch total value of CVX + vlCVX
    cvx_contract = w3.eth.contract(
        address="0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B",
        abi="""[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]""",
    )
    vlcvx_contract = w3.eth.contract(
        address="0x72a19342e8F1838460eBFCCEf09F6585e32db86E",
        abi="""[{"inputs":[{"internalType":"address","name":"_user","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"stateMutability":"view","type":"function"}]""",
    )

    cvx_price = fetch_price("convex-finance", "4h")

    unstaked_cvx_amount = cvx_contract.functions.balanceOf(POL_ADDRESS).call()
    unstaked_cvx_value: float = (unstaked_cvx_amount / 10**18) * cvx_price

    vlcvx_amount = vlcvx_contract.functions.balanceOf(POL_ADDRESS).call()
    vlcvx_value: float = (vlcvx_amount / 10**18) * cvx_price

    total_cvx_value: float = unstaked_cvx_value + vlcvx_value
    return total_cvx_value


def fetch_usdaf_value():
    # Fetch total value of USDaf
    usdaf_contract = w3.eth.contract(
        address="0x9Cf12ccd6020b6888e4D4C4e4c7AcA33c1eB91f8",
        abi="""[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]""",
    )
    usdaf_amount = usdaf_contract.functions.balanceOf(POL_ADDRESS).call()
    usdaf_value: float = usdaf_amount / 10**18
    return usdaf_value


def total_pol_value() -> str:
    cvx_value = fetch_cvx_value()
    usdaf_value = fetch_usdaf_value()
    total_value: float = cvx_value + usdaf_value
    return f"${total_value:,.2f}"


async def send_update(bot: hikari.GatewayBot):
    total_value = total_pol_value()
    await bot.rest.edit_my_member(GUILD_ID, nickname=total_value)
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=POL_VALUE_BOT_TOKEN)

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
                name="War Chest / POL",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
