import logging
from concurrent.futures.process import ProcessPoolExecutor

from eth_utils import ValidationError
from client import Client, deposit_token_browser
from models import BNB_Smart_Chain, TokenAmount

from read_config import config, abi

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    logger.info("The script is up and running!")

    with ProcessPoolExecutor(max_workers=int(config["max_workers"])) as executor:
        for seed in config["seeds"]:
            seed_list = seed.split(':')
            mnemonic_phrase, password = seed_list[0].strip(), seed_list[1].strip()

            amount = TokenAmount(amount=config["deposit_tokens"])
            executor.submit(deposit_token_browser, mnemonic_phrase, password, amount, config["login_delay"],
                            config["browser_delay"])

    logger.info("The script has finished its work!")


if __name__ == "__main__":
    main()
