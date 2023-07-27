import logging

from eth_utils import ValidationError

from client import Client
from models import BNB_Smart_Chain, TokenAmount
from web3.middleware import geth_poa_middleware

from read_config import transactions, bsca

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    logger.info("The script is up and running!")
    for transact in transactions:
        amount = TokenAmount(amount=transact["amount"], decimals=transact["decimals"])

        try:
            client = Client(private_key=transact["seed"], network=BNB_Smart_Chain)
            client.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ValidationError:
            logger.error(f"Wrong mnemonic phrase! Check config.yaml, transaction: {transact}")
            continue

        client.approve_interface(token_address=bsca, spender=transact["spender_address"], amount=amount)

        transaction = client.send_transaction(to=transact["spender_address"], value=transact["amount"])
        client.verif_tx(transaction)

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
