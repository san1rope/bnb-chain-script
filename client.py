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
        self.network = network
        self.w3 = Web3(Web3.HTTPProvider(endpoint_uri=network.rpc))
        # self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
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

    def approve(self, contract_address: str, spender_address: str, amount: TokenAmount,
                increase_gas: Optional[float] = 1.5):
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
            return {"hash": None, "amount": approved}

        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)

            transaction_params = {
                "chainId": self.w3.eth.chain_id,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "from": self.account.address
            }
            transaction_params["gas"] = int(self.w3.eth.estimate_gas(transaction_params) * increase_gas)
            approve_tx = contract.functions.approve(spender_address, amount.Wei).build_transaction(transaction_params)
        except Exception:
            logger.info(f'{self.account.address} | Approve failed | {traceback.format_exc()}')
            return False

        sign_approve = self.account.signTransaction(approve_tx)
        return {"hash": self.w3.eth.send_raw_transaction(sign_approve.rawTransaction), "amount": amount}

    def deposit_token(self, contract_address: str, amount: TokenAmount):
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)
        return self.send_transaction(to=contract_address, data=contract.encodeABI("depositToken",
                                                                                  args=(amount.Wei)))

        # contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)
        #
        # try:
        #     transaction_params = {
        #         "chainId": self.w3.eth.chain_id,
        #         "gasPrice": self.w3.to_wei(5, "gwei"),
        #         "nonce": self.w3.eth.get_transaction_count(self.account.address),
        #         "from": self.account.address,
        #     }
        #     transaction_params["gas"] = int(self.w3.eth.estimate_gas(transaction_params) * increase_gas)
        #
        #     deposit = contract.functions.depositToken(amount.Wei).build_transaction(transaction_params)
        # except Exception:
        #     logger.info(f'{self.account.address} | Deposit failed | {traceback.format_exc()}')
        #     return False
        #
        # sign_deposit = self.account.signTransaction(deposit)
        # return self.w3.eth.send_raw_transaction(sign_deposit.rawTransaction)

    @staticmethod
    def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []
        for i in range(latest_block_transaction_count):
            try:
                transaction = w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])
            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            max_priority_fee_per_gas = w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]
        return max_priority_fee_per_gas

    def send_transaction(
            self,
            to,
            data=None,
            from_=None,
            increase_gas=1.0,
            value=None,
            max_priority_fee_per_gas: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None
    ):
        if not from_:
            from_ = self.account.address

        tx_params = {
            'chainId': self.w3.eth.chain_id,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'from': Web3.to_checksum_address(from_),
            'to': Web3.to_checksum_address(to),
        }
        if data:
            tx_params['data'] = data

        if self.network.eip1559_tx:
            w3 = Web3(provider=Web3.HTTPProvider(endpoint_uri=self.network.rpc))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            last_block = w3.eth.get_block('latest')
            if not max_priority_fee_per_gas:
                # max_priority_fee_per_gas = self.w3.eth.max_priority_fee
                max_priority_fee_per_gas = Client.get_max_priority_fee_per_gas(w3=w3, block=last_block)
            if not max_fee_per_gas:
                # base_fee = int(last_block['baseFeePerGas'] * 1.125)
                base_fee = int(last_block['baseFeePerGas'] * increase_gas)
                max_fee_per_gas = base_fee + max_priority_fee_per_gas
            tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx_params['maxFeePerGas'] = max_fee_per_gas

        else:
            tx_params['gasPrice'] = self.w3.eth.gas_price

        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(self.w3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            print(f'{self.account.address} | Transaction failed | {err}')
            return None

        # sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)
        sign = self.account.signTransaction(tx_params)
        return self.w3.eth.send_raw_transaction(sign.rawTransaction)
