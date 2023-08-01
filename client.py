import logging
import traceback
import time

import user_agent
from eth_account.signers.local import LocalAccount
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from web3 import Web3
from typing import Optional
from web3.middleware import geth_poa_middleware
from webdriver_manager.chrome import ChromeDriverManager

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

        sign_approve = self.account.sign_transaction(approve_tx)
        return {"hash": self.w3.eth.send_raw_transaction(sign_approve.rawTransaction), "amount": amount}


def deposit_token_browser(seed: str, password: str, amount: TokenAmount, delay: float = 0):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-agent={user_agent.generate_user_agent()}")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")

    service = Service(ChromeDriverManager(version="114.0.5735.90").install())

    driver = webdriver.Chrome(service=service, options=options)
    flag = True
    try:
        url = "https://swap.ws/#!/auth"
        driver.get(url)
        if delay:
            time.sleep(delay)

        login_xpath = "/html/body/div[1]/main/section/div/div/div[2]/div[1]/button"
        driver.find_element("xpath", login_xpath).click()
        time.sleep(delay)

        password_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[1]/input"
        password_retry_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[2]/input"
        wallet_data_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[3]/textarea"

        driver.find_element("xpath", password_xpath).send_keys(password)
        time.sleep(delay)

        driver.find_element("xpath", password_retry_xpath).send_keys(password)
        time.sleep(delay)

        driver.find_element("xpath", wallet_data_xpath).send_keys(seed)
        time.sleep(delay)

        entry_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[4]/button"
        driver.find_element("xpath", entry_xpath).click()
        time.sleep(delay * 3)

        bridge_xpath = "/html/body/div[1]/main/section/div[2]/div[1]/div[3]/span"
        driver.find_element("xpath", bridge_xpath).click()
        time.sleep(delay)

        amount_xpath = "/html/body/div[1]/main/section/div[2]/div[2]/div[5]/div/div/div[2]/div[4]/input"
        driver.find_element("xpath", amount_xpath).send_keys(str(amount))
        time.sleep(delay)

        allow_xpath = "/html/body/div[1]/main/section/div[2]/div[2]/div[5]/div/div/div[3]/button"
        driver.find_element("xpath", allow_xpath).click()
        time.sleep(delay)

        driver.find_element("xpath", allow_xpath).click()
        time.sleep(delay)

        confirm_xpath = "/html/body/div[6]/div/div[6]/button[1]"
        driver.find_element("xpath", confirm_xpath).click()
        time.sleep(delay)
    except Exception:
        logger.info(f"Deposit error! \n{traceback.format_exc()}")
        flag = False
    finally:
        driver.close()
        driver.quit()

    logger.info("The deposit has been successfully completed!")
    return flag
