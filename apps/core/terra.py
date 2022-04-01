from terra_sdk.client.lcd import AsyncLCDClient
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.wasm.msgs import MsgExecuteContract
from terra_sdk.key.mnemonic import MnemonicKey
from asgiref.sync import async_to_sync
from rest_framework import serializers

from apps.core import utils
from config.settings.base import ADMIN_WALLET_MNEMONIC


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


@async_to_sync
async def create_and_sign_tx(msgs):
    try:
        mk = MnemonicKey(mnemonic=ADMIN_WALLET_MNEMONIC)
        terra = AsyncLCDClient("https://bombay-lcd.terra.dev", "bombay-12")
        wallet = terra.wallet(mk)
        tx = await wallet.create_and_sign_tx(
            CreateTxOptions(
                msgs=msgs,
                memo="",
            )
        )
        response = await terra.tx.broadcast(tx)
        await terra.session.close()
        return response
    except Exception as e:
        raise serializers.ValidationError(str(e))
