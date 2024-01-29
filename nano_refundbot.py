import asyncio
from nanotopy.client import NanoTo
from nanows.api import NanoWebSocket
from config import AUTH_KEY


class NanoPingPongBot:
    def __init__(self, auth_key):
        self.nano_ws = NanoWebSocket(url="wss://nanowallet.cc/ws")
        self.nano_to = NanoTo(auth_key=auth_key)
        self.seed = NanoTo.generate_seed()
        self.private_key = NanoTo.get_private_key_from_seed(self.seed, 0)
        self.bot_account_address = NanoTo.get_account_from_key(
            self.private_key)

        print(f"Generated Seed: {self.seed}")
        print(f"Your Address: {self.bot_account_address}")
        print("Visit https://nanodrop.io/ to get some nano.")

    async def run(self):
        await self.nano_ws.subscribe_confirmation(self.bot_account_address)

        while True:
            # Wait for new confirmation
            async for confirmation in self.nano_ws.get_confirmations():
                confirmation_message = confirmation.get("message", {})
                block_type = confirmation_message.get(
                    "block", {}).get("subtype")

                if block_type == "send":
                    block_hash = confirmation_message["hash"]
                    amount = confirmation_message["amount"]
                    source_account = confirmation_message["account"]

                    print(f"Process incoming Block: {block_hash}")
                    receive_hash = await self.nano_to.receive_block(self.private_key, amount, block_hash)
                    print(f"Receive Block created: {receive_hash}")

                    print(f"Returning funds to account: {source_account}")
                    refund_hash = await self.nano_to.send(self.private_key, amount, source_account)
                    print(f"Send Block created : {refund_hash}")

            await asyncio.sleep(10)


# Main execution
if __name__ == "__main__":
    bot = NanoPingPongBot(auth_key=AUTH_KEY)
    asyncio.run(bot.run())
