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
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from models import TokenAmount
from models import Network
from read_config import config

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

    def approve(self, contract_address: str, spender_address: str, max_amount: TokenAmount,
                increase_gas: Optional[float] = 1.5, amount: Optional[TokenAmount] = None):
        logger.info(
            f'{self.account.address} | approve | start approve {contract_address} for spender {spender_address}')

        balance = self.balance_of(contract_address=contract_address)
        if balance.Wei <= 0:
            logger.warning(f"{self.account.address} | approve | zero balance")
            return False

        if amount:
            max_amount = amount

        if max_amount.Wei > balance.Wei:
            max_amount = balance

        if max_amount.Wei <= TokenAmount(amount=5).Wei:
            print("1")
            logger.error("Cancel operation! Amount less than 5")
            return False

        approved = self.get_allowance(contract_address=contract_address, spender=spender_address)
        if TokenAmount(amount=(max_amount.Wei - TokenAmount(5).Wei), wei=True).Wei <= approved.Wei:
            if approved.Wei <= TokenAmount(amount=5).Wei:
                print("2")
                logger.error("Cancel operation! Allowance amount less than 5")
                return False

            if TokenAmount(amount=(balance.Wei - TokenAmount(5).Wei), wei=True).Wei < approved.Wei:
                logger.info("Cancel operation!")
                return False

            logger.info(f"{self.account.address} | approve | already approved")
            return {"hash": None, "amount": TokenAmount(amount=approved.Wei, wei=True)}

        if TokenAmount(amount=(balance.Wei - TokenAmount(5).Wei), wei=True).Wei < max_amount.Wei:
            max_amount = TokenAmount(amount=(balance.Wei - TokenAmount(5).Wei), wei=True)

        try:
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=self.abi)

            transaction_params = {
                "chainId": self.w3.eth.chain_id,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "from": self.account.address
            }
            transaction_params["gas"] = int(self.w3.eth.estimate_gas(transaction_params) * increase_gas)
            approve_tx = contract.functions.approve(
                spender_address, max_amount).build_transaction(transaction_params)
        except Exception:
            logger.info(f'{self.account.address} | Approve failed | {traceback.format_exc()}')
            return False

        sign_approve = self.account.sign_transaction(approve_tx)
        return {"hash": self.w3.eth.send_raw_transaction(sign_approve.rawTransaction), "amount": max_amount.Wei}


def deposit_token_browser(seed: str, password: str, amount: TokenAmount, login_delay: int, delay: float = 0,
                          retry: int = 5):
    if config["browser"] == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-agent={user_agent.generate_user_agent()}")
        options.add_argument("--ignore-certificate-errors")

        if config["headless"]:
            options.add_argument("--headless")

        service = Service(ChromeDriverManager(version="114.0.5735.90").install())

        driver = webdriver.Chrome(service=service, options=options)
    elif config["browser"] == "edge":
        options = webdriver.EdgeOptions()
        options.add_argument(f"user-agent={user_agent.generate_user_agent()}")

        if config["headless"]:
            options.add_argument("--headless")

        service = Service(EdgeChromiumDriverManager().install())

        driver = webdriver.Edge(service=service, options=options)
    else:
        logger.error("Browser not specified in config.json!")
        return False

    flag = True
    try:
        url = "https://swap.ws/#!/auth"
        driver.get(url)
        if delay:
            time.sleep(delay)

        login_xpath = "/html/body/div[1]/main/section/div/div/div[2]/div[3]/button"
        password_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[1]/input"
        password_retry_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[2]/input"
        wallet_data_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[3]/textarea"
        entry_xpath = "/html/body/div[1]/main/section/div/div/div[5]/div[4]/button"
        bridge_xpath = "/html/body/div[1]/main/section/div[2]/div[1]/div[3]/span"
        amount_xpath = "/html/body/div[1]/main/section/div[2]/div[2]/div[5]/div/div/div[2]/div[4]/input"
        allow_xpath = "/html/body/div[1]/main/section/div[2]/div[2]/div[5]/div/div/div[3]/button"
        confirm_xpath = "/html/body/div[6]/div/div[6]/button[1]"

        driver.find_element("xpath", login_xpath).click()
        time.sleep(delay)

        driver.find_element("xpath", password_xpath).send_keys(password)
        time.sleep(delay)

        driver.find_element("xpath", password_retry_xpath).send_keys(password)
        time.sleep(delay)

        driver.find_element("xpath", wallet_data_xpath).send_keys(seed)
        time.sleep(delay)

        driver.find_element("xpath", entry_xpath).click()
        time.sleep(login_delay)

        driver.find_element("xpath", bridge_xpath).click()
        time.sleep(delay)

        driver.find_element("xpath", amount_xpath).send_keys(str(amount.Ether))
        time.sleep(delay)

        driver.find_element("xpath", allow_xpath).click()
        time.sleep(delay * 2)

        driver.find_element("xpath", confirm_xpath).click()
        time.sleep(delay)
    except Exception:
        logger.info(f"Item not found, try again.... | retry: {retry}")
        if retry:
            deposit_token_browser(seed=seed, password=password, amount=amount, delay=delay, retry=(retry - 1),
                                  login_delay=login_delay)
        else:
            flag = False
            logger.info(traceback.format_exc())
    finally:
        driver.close()
        driver.quit()

    if flag:
        logger.info("The deposit has been successfully completed!")
    else:
        logging.error("The deposit was not successful!")

    return flag
