from queue import Queue
from time import sleep

from web3 import Web3, HTTPProvider
from web3.auto import w3
url = "HTTP://127.0.0.1:7545"
web3 = Web3(HTTPProvider(url))

class TransactionQueue(object):

    def __init__(self):
        self.transaction_queue = Queue(maxsize=0)
        self.process_transaction(None)

    def add(self, trade):
        self.transaction_queue.put(trade)

    def process_transaction(self, trade):
        while True:
            print("TX processing...")
            sleep(3)

        # call trade() on DEX sc
        # wait for response
            # if ok return true
            # else try again.