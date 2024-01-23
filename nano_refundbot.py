import asyncio
from nanotopy.client import NanoTo
from config import AUTH_KEY


class NanoPingPongBot:
    def __init__(self, auth_key):
        self.nano_to = NanoTo(auth_key=auth_key)
        self.seed = NanoTo.generate_seed()
        self.private_key = NanoTo.get_private_key_from_seed(self.seed, 0)
        self.bot_account_address = NanoTo.get_account_from_key(
            self.private_key)

        print(f"Generated Seed: {self.seed}")
        print(f"Your Address: {self.bot_account_address}")
        print("Visit https://nanodrop.io/ to get some nano.")

    async def run(self):
        while True:
            receivable_blocks = await self.nano_to.receivable(self.bot_account_address, source=True, threshold=10**24)
            for block in receivable_blocks:
                block_hash = block["hash"]
                amount = block["amount"]
                source_account = block["source"]

                print(f"Process incoming tx: {block_hash} for {amount} raw")
                print(receivable_blocks)
                receive_hash = await self.nano_to.receive_block(self.private_key, block["amount"], block_hash)
                print(f"Receive block created: {receive_hash}")

                print(f"Returning funds to account: {source_account}")
                refund_hash = await self.nano_to.send(self.private_key, amount, source_account)
                print(f"Send block was created successfully: {refund_hash}")

            await asyncio.sleep(10)


# Main execution
if __name__ == "__main__":
    bot = NanoPingPongBot(auth_key=AUTH_KEY)
    asyncio.run(bot.run())
