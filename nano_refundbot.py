import asyncio
from nano_lib_py import Block, generate_account_id, get_account_public_key, generate_account_private_key, generate_seed
from nanorpc.client import NanoRpc, NodeVersion


class NanoPingPongBot:
    def __init__(self, rpc_url, node_version, rpc_user=None, rpc_password=None):
        self.rpc = NanoRpc(url=rpc_url, username=rpc_user,
                           password=rpc_password, node_version=node_version)
        self.seed = generate_seed()
        self.private_key = generate_account_private_key(self.seed, 0)
        self.bot_account_address = generate_account_id(self.seed, 0)

        print(f"Generated Seed: {self.seed}")
        print(f"Your Address: {self.bot_account_address}")
        print("Visit https://nanodrop.io/ to get some nano.")

    async def check_for_incoming_transactions(self, count="5", source="true"):
        return await self.rpc.receivable(self.bot_account_address, count=count, source=source)

    async def get_account_frontier(self):
        response = await self.rpc.frontiers(self.bot_account_address, 1)
        return response.get("frontiers", {}).get(self.bot_account_address, "0" * 64)

    async def get_pow_hash(self, account_frontier):
        return get_account_public_key(account_id=self.bot_account_address) if account_frontier == "0" * 64 else account_frontier

    def get_link_as_hash(self, link):
        link = get_account_public_key(account_id=link) if str(
            link).startswith("nano_") else link
        return link

    async def get_pow(self, frontier):
        pow_response = await self.rpc.work_generate(await self.get_pow_hash(frontier), use_peers="true")
        return pow_response["work"]

    async def create_send(self, frontier, current_balance, amount_to_send, destination):
        final_balance = current_balance - amount_to_send
        return await self.create_block(frontier, final_balance, destination)

    async def create_receive(self, frontier, incoming_amount, send_hash):
        return await self.create_block(frontier, incoming_amount, send_hash)

    async def create_block(self, frontier, balance, link):

        block = Block(
            block_type="state",
            account=self.bot_account_address,
            representative=self.bot_account_address,
            previous=frontier,
            balance=balance,
            link=self.get_link_as_hash(link),
            work=await self.get_pow(frontier)
        )
        block.sign(self.private_key)
        return block

    async def return_entire_balance_to_latest_sender(self):
        account_info = await self.rpc.account_info(self.bot_account_address)
        account_balance = int(account_info.get("balance", "0"))

        if account_balance > 0:
            account_frontier_hash = await self.get_account_frontier()
            frontier_info = await self.rpc.blocks_info([account_frontier_hash], source=True)
            received_from = frontier_info.get("blocks", {}).get(
                account_frontier_hash, {})["source_account"]
            amount_to_send = account_balance

            print(f"Returning funds to account: {received_from}")

            send_block = await self.create_send(
                account_frontier_hash, account_balance, amount_to_send, received_from)
            send_hash = await self.rpc.process(send_block.json(), json_block=False)
            print(f"Send block was created successfully: {send_hash}")
            return True

        return False

    async def receive_single_incoming_transaction(self):
        incoming_transactions = await self.check_for_incoming_transactions()

        if incoming_transactions.get("blocks", ""):
            first_block_hash, first_block_info = next(
                iter(incoming_transactions["blocks"].items()))

            print(f"Process incoming tx: {first_block_hash}")
            current_frontier = await self.get_account_frontier()
            receive_amount = int(first_block_info['amount'])
            receive_block = await self.create_receive(
                current_frontier, receive_amount, first_block_hash)

            receive_hash = await self.rpc.process(receive_block.json(), json_block="false")
            print(f"Receive block was created successfully: {receive_hash}")
        else:
            pass

    async def run(self):
        while True:
            await self.receive_single_incoming_transaction()
            await self.return_entire_balance_to_latest_sender()
            await asyncio.sleep(1)


# Main execution
if __name__ == "__main__":
    bot = NanoPingPongBot(rpc_url='http://localhost:7076',
                          rpc_user=None,
                          rpc_password=None,
                          node_version=NodeVersion.V25_0)
    asyncio.run(bot.run())
