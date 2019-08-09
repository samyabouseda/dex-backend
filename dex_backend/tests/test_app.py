import unittest
import json

from web3 import Web3, HTTPProvider

# Constants
MATCHING_ENGINE_ADDRESS = '0x8FC9b674Aa37B879F6E9B096C8dB63f92d63A446'

# Web3 config
url = "HTTP://127.0.0.1:7545"
web3 = Web3(HTTPProvider(url))

# Smart Contract config
with open("../contracts/DEX.json") as dex:
    dex_json = json.load(dex)

network_id = "5777"
abi = dex_json["abi"]
networks = dex_json["networks"]
address = networks[network_id]["address"]
contract = web3.eth.contract(address=address, abi=abi)


class TestTrade(unittest.TestCase):

    def test_web3_is_connected(self):
        self.assertTrue(web3.isConnected(), "Web3 should be connected")

    def test_contract_exists(self):
        self.assertEqual(contract.address, address, "Contract should have the correct address")
        matching_engine_address = contract.functions.matchingEngine().call()
        self.assertEqual(matching_engine_address, MATCHING_ENGINE_ADDRESS, "Matching Engine should exists")

if __name__ == '__main__':
    unittest.main()