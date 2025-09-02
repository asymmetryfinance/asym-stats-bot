import asyncio

from rich import print
from rich.traceback import install

from Bots import asf_mcap, asf_price, global_tvl, susdaf_yield, usdaf_supply, usdaf_tvl

install()


async def main():
    tasks = [
        asf_price.run(),
        usdaf_supply.run(),
        usdaf_tvl.run(),
        global_tvl.run(),
        asf_mcap.run(),
        susdaf_yield.run(),
    ]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
        for task in tasks:
            task.cancel()
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Ensure all tasks are properly cleaned up
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Give tasks a chance to clean up
            await asyncio.sleep(0.1)
            # Force cleanup of any remaining tasks
            for task in tasks:
                if not task.done():
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error in main: {e}")
            continue
