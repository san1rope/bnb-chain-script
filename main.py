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

    # contract_address = config["contract_address"]
    # bridge_contract_address = config["bridge_contract_address"]
    # max_amount = TokenAmount(amount=config["max_amount"], decimals=config["decimals"], wei=False)
    # amount = TokenAmount(amount=config["amount"], decimals=config["decimals"], wei=False)
    for seed in config["seeds"]:
        seed_list = seed.split(':')
        mnemonic_phrase, password = seed_list[0].strip(), seed_list[1].strip()
        # try:
        #     client = Client(seed=mnemonic_phrase, network=BNB_Smart_Chain, abi=abi)
        # except ValidationError:
        #     logger.error(f"Wrong mnemonic phrase! Check config.json, seed: {mnemonic_phrase}")
        #     continue
        #
        # approve = client.approve(
        #     contract_address=contract_address, spender_address=bridge_contract_address, max_amount=max_amount,
        #     amount=amount)
        # if approve:
        #     if approve["hash"]:
        #         if not client.verif_tx(approve["hash"]):
        #             continue

        amount = TokenAmount(amount=config["deposit_tokens"])
        deposit_token_browser(seed=mnemonic_phrase, password=password, amount=amount,
                              delay=config["browser_delay"], login_delay=config["login_delay"])

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
