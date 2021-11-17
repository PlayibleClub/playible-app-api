from terra_sdk.client.lcd import AsyncLCDClient
from asgiref.sync import async_to_sync

@async_to_sync
async def get_latest_block_height():
    terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
    block_height = await terra.tendermint.block_info()
    return block_height['block']['header']['height']

@async_to_sync
async def get_tx_info(tx_hash):
    terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
    tx_info = await terra.tx.tx_info(tx_hash)
    return tx_info

@async_to_sync
async def query_contract(contract_addr, query_msg):
    terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
    response = await terra.wasm.contract_query(contract_addr, query_msg)
    return response