import logging

from eth_utils import ValidationError
from client import Client, deposit_token_browser
from models import BNB_Smart_Chain, TokenAmount

from read_config import config, abi

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    logger.info("The script is up and running!")

    contract_address = config["contract_address"]
    bridge_contract_address = config["bridge_contract_address"]
    max_amount = TokenAmount(amount=config["max_amount"], decimals=config["decimals"])
    for seed in config["seeds"]:
        try:
            client = Client(seed=seed["seed"], network=BNB_Smart_Chain, abi=abi)
        except ValidationError:
            logger.error(f"Wrong mnemonic phrase! Check config.json, seed: {seed['seed']}")
            continue

        approve = client.approve(
            contract_address=contract_address, spender_address=bridge_contract_address, amount=max_amount)
        if approve:
            if approve["hash"]:
                if not client.verif_tx(approve["hash"]):
                    continue

            amount = float(config["deposit_tokens"]) if float(config["deposit_tokens"]) else approve["amount"].Ether
            deposit_token_browser(seed=seed["seed"], password=seed["password"], amount=amount,
                                  delay=config["browser_delay"])

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
