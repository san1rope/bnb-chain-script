import logging

from eth_utils import ValidationError
from client import Client
from models import BNB_Smart_Chain, TokenAmount

from read_config import config, abi

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    logger.info("The script is up and running!")

    contract_address = config["contract_address"]
    bridge_contract_address = config["bridge_contract_address"]
    decimals = config["decimals"]
    max_amount = TokenAmount(amount=config["max_amount"], decimals=decimals)
    for seed in config["seeds"]:
        try:
            client = Client(seed=seed, network=BNB_Smart_Chain, abi=abi)
        except ValidationError:
            logger.error(f"Wrong mnemonic phrase! Check config.json, seed: {seed}")
            continue

        approve = client.approve(
            contract_address=contract_address, spender_address=bridge_contract_address, amount=max_amount)
        if approve:
            if client.verif_tx(approve["hash"]):
                deposit_amount = TokenAmount(amount=approve["amount"], decimals=decimals)
                transaction = client.deposit_token(contract_address=bridge_contract_address, amount=deposit_amount)
                if transaction:
                    if client.verif_tx(transaction):
                        logger.info("The task has been successfully completed!")
                    else:
                        logger.info("Task completed with an error!")

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
