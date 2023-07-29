import logging

from eth_utils import ValidationError

from client import Client
from models import BNB_Smart_Chain, TokenAmount
from web3.middleware import geth_poa_middleware

from read_config import config

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    logger.info("The script is up and running!")

    contract_address = config["contract_address"]
    recipient_address = config["recipient_address"]
    for seed in config["seeds"]:
        try:
            client = Client(seed=seed, network=BNB_Smart_Chain)
            client.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ValidationError:
            logger.error(f"Wrong mnemonic phrase! Check config.json, seed: {seed}")
            continue

        approve = client.approve_interface(token_address=contract_address, spender=recipient_address)
        if approve:
            transaction = client.send_transaction(to=recipient_address)
            if transaction:
                client.verif_tx(transaction)

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
