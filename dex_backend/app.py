import falcon
import json
from web3 import Web3, HTTPProvider
from web3.auto import w3
import requests
from eth_account.messages import encode_defunct
import random

from falcon_cors import CORS

from queue import Queue
from time import sleep

cors = CORS(allow_origins_list=['http://localhost:3000'])

# falcon.API instances are callable WSGI apps
app = falcon.API(middleware=[cors.middleware])

# Web3 config
url = "HTTP://127.0.0.1:7545"
web3 = Web3(HTTPProvider(url))

with open("contracts/DEX.json") as dex:
    dex_json = json.load(dex)

network_id = "5777"
abi = dex_json["abi"]
networks = dex_json["networks"]
address = networks[network_id]["address"]

# contract = web3.eth.contract(address=address, abi=abi)


class Order(object):

    def __init__(
            self,
            # token_maker_name,
            # token_taker_name,
            side,
            token_maker,
            token_taker,
            amount_maker,
            amount_taker,
            address_maker,
            nonce,
            hash):
        # self._token_maker_name = token_maker_name
        # self._token_taker_name = token_taker_name
        self._side = side
        self._token_maker = token_maker
        self._token_taker = token_taker
        self._amount_maker = amount_maker
        self._amount_taker = amount_taker
        self._address_maker = address_maker
        self._nonce = nonce
        self._hash = hash

    def __str__(self):
        return 'Order [ '+self._side+' '+str(self._amount_maker)+' '+self._token_maker+' @ '+str(self._amount_taker)+' '+self._token_taker+']'

    def token_maker(self):
        return self._token_maker

    def token_taker(self):
        return self._token_taker

    def amount_maker(self):
        return self._amount_maker

    def amount_taker(self):
        return self._amount_taker

    def address_maker(self):
        return self._address_maker

    def nonce(self):
        return self._nonce

    def side(self):
        return self._side

    def matches(self, another):
        # Should also account for <= or =>
        print("SELF AM: " + str(self.amount_maker()))
        print("ANOT AM: " + str(another.amount_maker()))
        print("SELF AT: " + str(self.amount_taker()))
        print("ANOT AT: " + str(another.amount_taker()))
        if self._amount_taker == another.amount_maker():
            return self._amount_maker == another.amount_taker()
        else:
            return False

class TransactionQueue(object):

    def put(self, trade):
        # Build trade object.
        maker_order = trade[0]
        taker_order = trade[1]
        token_maker = str(maker_order.token_maker())
        token_taker = str(maker_order.token_taker())
        amount_maker = maker_order.amount_maker()
        amount_taker = maker_order.amount_taker()
        address_maker = str(maker_order.address_maker())
        address_taker = str(taker_order.address_maker())
        nonce = 0

        json = {
            "addressMaker": address_maker,
            "addressTaker": address_taker,
            "amountMaker": str(amount_maker),
            "amountTaker": str(amount_taker),
            "nonce": str(nonce),
            "tokenMaker": token_maker,
            "tokenTaker": token_taker,
        }

        url = "http://127.0.0.1:5000/transactions"
        response = requests.post(url, json=json)
        print(response.status_code)


class OrderBook(object):

    def __init__(self):
        self._sell_orders = list()
        self._buy_orders = list()
        self._transaction_queue = TransactionQueue()


    def put(self, order):
        side = order.side()
        if side == 'BUY':
            if not self._matched(order):
                self._buy_orders.append(order)
        elif order.side() == 'SELL':
            if not self._matched(order):
                self._sell_orders.append(order)

    def _matched(self, order_):
        side = order_.side()

        if side == 'BUY':
            for order in self._sell_orders:
                print("order_ " + str(order_))
                print("order " + str(order))
                if order_.matches(order):
                    print('MATCHED')
                    self._transaction_queue.put((order, order_))
                    # self._transaction_queue.process_transaction()
                    return True
            return False

        elif side == 'SELL':
            for order in self._buy_orders:
                print("order_ " + str(order_))
                print("order " + str(order))
                if order_.matches(order):
                    print('MATCHED')
                    self._transaction_queue.put((order, order_))
                    # self._transaction_queue.process_transaction()
                    return True
            return False
        return False



class Orders(object):

    def __init__(self):
        self._order_book = OrderBook()

    # def on_get(self, req, resp):
    #     me_addre = contract.functions.matchingEngine().call()
    #     print(contract.address)

    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        signature = data["signature"]
        order_data = data["orderData"]
        message_hash = data["messageHash"]
        sender = order_data["addressMaker"]
        if self.is_valid_sig(message_hash, signature, sender):
            order = Order(
                order_data["side"],
                order_data["tokenMaker"],
                order_data["tokenTaker"],
                int(order_data["amountMaker"]),
                int(order_data["amountTaker"]),
                order_data["addressMaker"],
                order_data["nonce"],
                signature
            )
            print(order)
            self._order_book.put(order)
            resp.status = falcon.HTTP_201
        else:
            resp.status = falcon.HTTP_406

    def is_valid_sig(self, hash, sig, sender):
        signer = w3.eth.account.recoverHash(hash, signature=sig)
        return sender == signer


app.add_route('/orders', Orders())
