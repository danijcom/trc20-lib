# -*- coding: utf8 -*-
import datetime
import requests

from tronpy import Tron
from loguru import logger
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider


def enum(**enums):
    return type('Enum', (), enums)


Contract = enum(
    USDT='TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    TRX='TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR',
    SUN_SWAP_V2='TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax'
)


def is_valid_address(address: str):
    url = "https://api.shasta.trongrid.io/wallet/validateaddress"
    payload = {
        "address": address,
        "visible": True
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()['result']


def get_trx_price(coinwatch_api_key, amount: float = 1):
    def livecoinwatch():
        url = "https://api.livecoinwatch.com/coins/single"

        payload = {
            "currency": "USD",
            "code": "TRX",
            "meta": True
        }
        headers = {
            'content-type': 'application/json',
            'x-api-key': coinwatch_api_key
        }

        return requests.post(url, headers=headers, json=payload).json()['rate']

    def coingecko():
        result = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd')
        return result.json()['tron']['usd']

    try:
        one_trx = coingecko()
        logger.info('1 TRX = {} USD | CoinGecko'.format(one_trx))
    except Exception as ex:
        logger.info('CoinGecko error: {} | Trying coinwatch...'.format(ex))
        one_trx = livecoinwatch()
        logger.info('1 TRX = {} USD | LiveCoinWatch'.format(one_trx))

    return amount * one_trx


class MyTron:
    def __init__(self, coinwatch_api_key: str, trongrid_api_key: str, private_key: str):
        provider = HTTPProvider(api_key=trongrid_api_key)
        self.coinwatch_api_key = coinwatch_api_key
        self.client = Tron(provider=provider)
        self.private_key = PrivateKey(bytes.fromhex(private_key))
        self.public_key = self.private_key.public_key.to_base58check_address()
        self.block_explorer_tx = 'https://tronscan.org/#/transaction/'
        self.processing = False
        logger.info('Tron chain loaded! Wallet address: {}'.format(self.public_key))

    def coin_to_sun(self, amount: float):
        return int(amount * 1_000_000)

    def get_trx_balance(self, address: str = None):
        address = self.public_key if address is None else address
        return float(self.client.get_account_balance(address))

    def get_coin_balance(self, coin_contract: str, address: str = None):
        contract = self.client.get_contract(coin_contract)
        address = self.public_key if address is None else address
        precision = contract.functions.decimals()
        return contract.functions.balanceOf(address) / 10 ** precision

    def trx_to_usdt(self, amount_trx: float, fee_limit=250):
        contract = self.client.get_contract(Contract.SUN_SWAP_V2)

        time_window = datetime.datetime.now() + datetime.timedelta(seconds=60)
        min_out = get_trx_price(amount_trx) * 0.99

        logger.info('Trying to swap {:.2f} TRX to min of {:.2f} USDT'.format(amount_trx, min_out))

        txn = (
            contract.functions.swapExactETHForTokens.with_transfer(self.coin_to_sun(amount_trx))(
                self.coin_to_sun(min_out),
                [Contract.TRX, Contract.USDT],
                self.public_key,
                int(time_window.timestamp())
            )
            .with_owner(self.public_key)
            .fee_limit(self.coin_to_sun(fee_limit))
            .build()
            .sign(self.private_key)
        )

        tx_id = txn.txid
        logger.info('Transaction built!')

        result = txn.broadcast().wait()
        logger.info('Transaction sent with status {}! URL: {}{}'.format(
            result['receipt']['result'], self.block_explorer_tx, tx_id)
        )

        return tx_id, result['receipt']['result'], result

    def usdt_to_trx(self, amount_usdt: float, fee_limit=250):
        contract = self.client.get_contract(Contract.SUN_SWAP_V2)

        time_window = datetime.datetime.now() + datetime.timedelta(seconds=60)
        min_out = (amount_usdt / get_trx_price(1)) * 0.99

        logger.info('Trying to swap {:.2f} USDT to min of {:.2f} TRX'.format(amount_usdt, min_out))

        txn = (
            contract.functions.swapExactTokensForETH(
                self.coin_to_sun(amount_usdt),
                self.coin_to_sun(min_out),
                [Contract.USDT, Contract.TRX],
                self.public_key,
                int(time_window.timestamp())
            )
            .with_owner(self.public_key)
            .fee_limit(self.coin_to_sun(fee_limit))
            .build()
            .sign(self.private_key)
        )
        tx_id = txn.txid
        logger.info('Transaction built!')

        result = txn.broadcast().wait()
        logger.info('Transaction sent with status {}! URL: {}{}'.format(
            result['receipt']['result'], self.block_explorer_tx, tx_id)
        )

        return tx_id, result['receipt']['result'], result

    def send_trx(self, recipient: str, amount: float, fee_limit=35):
        logger.info('Sending {} TRC to {}'.format(amount, recipient))

        txn = (
            self.client.trx.transfer(self.public_key, recipient, self.coin_to_sun(amount))
            .build()
            .sign(self.private_key)
        )
        tx_id = txn.txid
        logger.info('Transaction built!')

        result = txn.broadcast().wait()
        logger.info('Transaction {} sent! URL: {}{}'.format(
            tx_id, self.block_explorer_tx, tx_id)
        )

        return tx_id, 'SUCCESS', result

    def send_coin(self, coin_contract: str, recipient: str, amount: float, fee_limit=35):
        logger.info('Sending {} USDT to {}'.format(amount, recipient))

        contract = self.client.get_contract(coin_contract)
        txn = (
            contract.functions.transfer(recipient, self.coin_to_sun(amount))
            .with_owner(self.public_key)
            .fee_limit(self.coin_to_sun(fee_limit))
            .build()
            .sign(self.private_key)
        )
        tx_id = txn.txid
        logger.info('Transaction built!')

        result = txn.broadcast().wait()
        logger.info('Transaction sent with status {}! URL: {}{}'.format(
            result['receipt']['result'], self.block_explorer_tx, tx_id)
        )

        return tx_id, result['receipt']['result'], result

    def send_coin_queue(self, coin_contract: str, recipient: str, amount: float, fee_limit=35):
        self.processing = True

        try:
            tx_id, result, data = self.send_coin(coin_contract, recipient, amount, fee_limit)
            self.processing = False
            return tx_id, result, data
        except Exception as ex:
            self.processing = False
            raise ex
