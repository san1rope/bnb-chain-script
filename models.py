from dataclasses import dataclass
from decimal import Decimal
from typing import Union


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


class Network:
    def __init__(self,
                 name: str,
                 rpc: str,
                 chain_id: int,
                 eip1559_tx: bool,
                 coin_symbol: str,
                 explorer: str,
                 decimals: int = 18,
                 ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_tx = eip1559_tx
        self.coin_symbol = coin_symbol
        self.decimals = decimals
        self.explorer = explorer

    def __str__(self):
        return f'{self.name}'


Arbitrum = Network(
    name='arbitrum',
    rpc='https://rpc.ankr.com/arbitrum/',
    chain_id=42161,
    eip1559_tx=True,
    coin_symbol='ETH',
    explorer='https://arbiscan.io/',
)

Optimism = Network(
    name='optimism',
    rpc='https://rpc.ankr.com/optimism/',
    chain_id=10,
    eip1559_tx=True,
    coin_symbol='ETH',
    explorer='https://optimistic.etherscan.io/',
)

Polygon = Network(
    name='polygon',
    rpc='https://polygon-rpc.com/',
    chain_id=137,
    eip1559_tx=True,
    coin_symbol='MATIC',
    explorer='https://polygonscan.com/',
)

Avalanche = Network(
    name='avalanche',
    rpc='https://rpc.ankr.com/avalanche/',
    chain_id=43114,
    eip1559_tx=True,
    coin_symbol='AVAX',
    explorer='https://snowtrace.io/',
)

Fantom = Network(
    name='fantom',
    rpc='https://rpc.ankr.com/fantom/',
    chain_id=250,
    eip1559_tx=True,
    coin_symbol='FTM',
    explorer='https://ftmscan.com/',
)

BNB_Smart_Chain = Network(
    name="bnb smart chain",
    rpc="https://bsc-dataseed.binance.org/",
    chain_id=56,
    eip1559_tx=False,
    coin_symbol='BNB',
    explorer="https://bscscan.com/"
)

BNB_Smart_Chain_Testnet = Network(
    name="bnb smart chain testnet",
    rpc="https://data-seed-prebsc-1-s1.binance.org:8545/",
    chain_id=97,
    eip1559_tx=True,
    coin_symbol="tBNB",
    explorer="https://testnet.bscscan.com/ "
)
