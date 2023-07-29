import json

with open("config.json", encoding="utf-8") as file:
    config = json.load(file)

with open("abi.json", encoding="utf-8-sig") as file:
    abi = json.load(file)
