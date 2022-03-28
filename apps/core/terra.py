from terra_sdk.client.lcd import AsyncLCDClient
from asgiref.sync import async_to_sync
from rest_framework import serializers

from apps.core import utils


@async_to_sync
async def get_latest_block_height():
    terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
    block_height = await terra.tendermint.block_info()
    return block_height['block']['header']['height']


@async_to_sync
async def get_tx_info(tx_hash):
    try:
        terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
        tx_info = await terra.tx.tx_info(tx_hash)
        return tx_info
    except:
        raise serializers.ValidationError('Failed to retrieve information from the blockchain: ' + str(e))


@async_to_sync
async def query_contract(contract_addr, query_msg):
    try:
        terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
        response = await terra.wasm.contract_query(contract_addr, query_msg)
        await terra.session.close()
        return response
    except Exception as e:
        raise serializers.ValidationError('Failed to retrieve information from the blockchain: ' + str(e))
