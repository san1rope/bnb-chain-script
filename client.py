import logging
import traceback

from eth_account.signers.local import LocalAccount
from web3 import Web3
from typing import Optional
from web3.middleware import geth_poa_middleware

from models import TokenAmount
from models import Network

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, seed: str, network: Network, abi: dict):
        self.w3 = Web3(Web3.HTTPProvider(endpoint_uri=network.rpc))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.w3.eth.account.enable_unaudited_hdwallet_features()

        self.account: LocalAccount = self.w3.eth.account.from_mnemonic(seed)
        self.abi = abi

    def get_decimals(self, contract_address: str) -> int:
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)
        return int(contract.functions.decimals().call())

    def balance_of(self, contract_address: str, address: Optional[str] = None) -> TokenAmount:
        if not address:
            address = self.account.address

        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)
        return TokenAmount(
            amount=contract.functions.balanceOf(Web3.to_checksum_address(address)).call(),
            decimals=self.get_decimals(contract_address),
            wei=True
        )

    def get_allowance(self, contract_address: str, spender: str) -> TokenAmount:
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)
        return TokenAmount(
            amount=contract.functions.allowance(self.account.address, spender).call(),
            decimals=self.get_decimals(contract_address=contract_address),
            wei=True
        )

    def verif_tx(self, tx_hash) -> bool:
        try:
            data = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if 'status' in data and data['status'] == 1:
                logger.info(f'{self.account.address} | transaction was successful: {tx_hash.hex()}')
                return True
            else:
                logger.warning(f'{self.account.address} | transaction failed {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            logger.error(f'{self.account.address} | unexpected error in <verif_tx> function: {err}')
            return False

    def approve(self, contract_address: str, spender_address: str, amount: TokenAmount):
        logger.info(
            f'{self.account.address} | approve | start approve {contract_address} for spender {spender_address}')

        balance = self.balance_of(contract_address=contract_address)
        if balance.Wei <= 0:
            logger.warning(f"{self.account.address} | approve | zero balance")
            return False

        if amount.Wei > balance.Wei:
            amount = balance

        approved = self.get_allowance(contract_address=contract_address, spender=spender_address)
        if amount.Wei <= approved.Wei:
            logger.info(f"{self.account.address} | approve | already approved")
            return True

        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)

            transaction_params = {
                "chainId": self.w3.eth.chain_id,
                "gas": 200000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "from": self.account.address
            }
            approve = contract.functions.approve(spender_address, amount.Wei).build_transaction(transaction_params)
        except Exception:
            logger.info(f'{self.account.address} | Transaction failed | {traceback.format_exc()}')
            return False

        sign_approve = self.account.signTransaction(approve)
        return {"hash": self.w3.eth.send_raw_transaction(sign_approve.rawTransaction), "amount": amount}

    def deposit(self, contract_address: str, amount: TokenAmount):
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)

        transaction_params = {
            "chainId": self.w3.eth.chain_id,
            "gas": 200000,
            "gasPrice": self.w3.eth.gas_price,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "from": self.account.address,
        }
        deposit_tx = contract.functions.deposit(amount.Wei).build_transaction(transaction_params)

        sign_deposit = self.account.signTransaction(deposit_tx)
        return self.w3.eth.send_raw_transaction(sign_deposit.rawTransaction)
