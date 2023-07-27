import json

import yaml

with open("config.yaml", encoding="utf-8") as file:
    config = yaml.safe_load(file)

with open("abi.json", encoding="utf-8-sig") as file:
    abi = json.load(file)

transactions = config["transactions"]

bsca = "0x7e624fa0e1c4abfd309cc15719b7e2580887f570"
