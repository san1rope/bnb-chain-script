import json

from eth_account.signers.local import LocalAccount
from web3 import Web3

from models import BNB_Smart_Chain, TokenAmount

w3 = Web3(Web3.HTTPProvider(BNB_Smart_Chain.rpc))
w3.eth.account.enable_unaudited_hdwallet_features()

with open("abi.json") as file:
    abi = json.load(file)

contract_address = "0xbAac55fdbB253b7D1b6A60763e8FFe8D3A451C0c"
contract_checksum = w3.to_checksum_address(contract_address)
contract = w3.eth.contract(address=contract_checksum, abi=abi)

seed = "roof voyage silver board option source panda horse sort tonight people injury"
account: LocalAccount = w3.eth.account.from_mnemonic(seed)

tx = {
    "chainId": w3.eth.chain_id,
    "nonce": w3.eth.get_transaction_count(account.address),
    "from": account.address,
    "to": contract_address,
    "gasPrice": w3.to_wei(5, "gwei"),
    "gas": 120000,
    "data": contract.encodeABI("depositToken", args=(100000,)),
}

sign = account.sign_transaction(tx)

hesh = w3.eth.send_raw_transaction(sign.rawTransaction)
print(hesh)
