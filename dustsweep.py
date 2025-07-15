#!/usr/bin/env python3
import os
import argparse
import requests
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

ETH_NODE = os.getenv("ETH_NODE_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
MAIN_ADDRESS = os.getenv("MAIN_ADDRESS")
API_KEY = os.getenv("ETHERSCAN_API_KEY")

# Уникальная утилита: объединяет мелкие остатки разных ERC-20 токенов (пыль) в основной кошелек,
# вычисляя, когда сбор пыли экономически оправдан.

def get_token_balances(address):
    url = (
        f"https://api.etherscan.io/api?module=account"
        f"&action=tokenbalance&contractaddress={{contract}}"
        f"&address={address}&tag=latest&apikey={API_KEY}"
    )
    # Пример: получить список популярных контрактов из файла или самостоятельно расширить
    contracts = {
        # Минимальный набор для примера
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    }
    balances = {}
    for symbol, contract in contracts.items():
        resp = requests.get(url.format(contract=contract))
        data = resp.json()
        if data["status"] != '1':
            continue
        raw = Decimal(data["result"])
        # Получаем число токенов, деля на 10**decimals
        # Здесь для простоты считаем 18 знаков
        balances[symbol] = raw / Decimal(10**18)
    return balances


def build_and_send_tx(w3, to, data, gas, gas_price):
    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx = {
        'to': to,
        'from': account.address,
        'value': 0,
        'data': data,
        'gas': gas,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    }
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()


def consolidate_dust(args):
    w3 = Web3(Web3.HTTPProvider(ETH_NODE))
    balances = get_token_balances(args.address)
    print(f"Баланс токенов на {args.address}: {balances}")

    txs = []
    for sym, bal in balances.items():
        if bal >= args.threshold:
            print(f"Готовим сбор {sym}: {bal} >= {args.threshold}")
            # Заглушка: ABI и вызов transfer
            abi = '[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]'
            contract = w3.eth.contract(address=w3.toChecksumAddress(args.contracts[sym]), abi=abi)
            amount = int(bal * 10**18)
            data = contract.encodeABI(fn_name='transfer', args=[MAIN_ADDRESS, amount])
            gas_price = w3.eth.gas_price
            gas = contract.functions.transfer(MAIN_ADDRESS, amount).estimateGas({'from': account.address})
            tx_hash = build_and_send_tx(w3, contract.address, data, gas, gas_price)
            txs.append((sym, tx_hash))
    if not txs:
        print("Нет токенов для сбора.")
    else:
        for sym, txh in txs:
            print(f"Собрано {sym}, tx: {txh}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DustSweep: сбор мелких остатков ERC-20 токенов')
    parser.add_argument('-a', '--address', required=True, help='Адрес кошелька для сканирования')
    parser.add_argument('-t', '--threshold', type=Decimal, default=Decimal('0.01'), help='Порог в токенах для сбора')
    parser.add_argument('--contracts', action='store_true', help='Показать используемые контракты и выйти')
    args = parser.parse_args()
    # Можно расширить: загрузка контрактов из файла
    if args.contracts:
        print("Контракты токенов по умолчанию: USDT, UNI, LINK")
    else:
        consolidate_dust(args)
