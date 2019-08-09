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

    def serialize(self):
        return {
            "addressMaker": self._address_maker,
            "amountMaker": str(self._amount_maker),
            "amountTaker": str(self._amount_taker),
            "nonce": str(self._nonce),
            "tokenMaker": self._token_maker,
            "tokenTaker": self._token_taker,
        }

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


class Bid(object):

    def __init__(self, price, size):
        self.price = price
        self.size = size
        self.total = price * size

    def __eq__(self, other):
        if isinstance(other, Bid):
            return self.price == other.price
        return NotImplemented

    def __ne__(self, other):
        eq = Bid.__eq__(self, other)
        return NotImplemented if eq is NotImplemented else not eq

    def serialize(self):
        return {
            "bid": self.price,
            "size": self.size,
            "total": self.total
        }

    def update_bid(self, size):
        self.size = self.size + size
        self.total = self._calc_total()

    def _calc_total(self):
        return self.price * self.size


class Ask(object):

    def __init__(self, price, size):
        self.price = price
        self.size = size
        self.total = price * size

    def __eq__(self, other):
        if isinstance(other, Ask):
            return self.price == other.price
        return NotImplemented

    def __ne__(self, other):
        eq = Ask.__eq__(self, other)
        return NotImplemented if eq is NotImplemented else not eq

    def serialize(self):
        return {
            "ask": self.price,
            "size": self.size,
            "total": self.total
        }

    def update_ask(self, size):
        self.size = self.size + size
        self.total = self._calc_total()

    def _calc_total(self):
        return self.price * self.size


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

    def get_bids(self):
        # TODO: Add filter "token" to get only the bids/ask for this token.
        bids = list()
        for order in self._buy_orders:
            price = order.amount_maker() / 1000000000000000000 / order.amount_taker()
            size = order.amount_taker()
            bid = Bid(price, size)
            if bid in bids:
                bid_index = bids.index(bid)
                existing_bid = bids[bid_index]
                existing_bid.update_bid(size)
            else:
                bids.append(bid)
        serialized_bids = list()
        for bid in bids:
            serialized_bids.append(bid.serialize())
        return serialized_bids

    def get_asks(self):
        asks = list()
        for order in self._sell_orders:
            price = order.amount_taker() / 1000000000000000000 / order.amount_maker()
            size =  order.amount_maker()
            ask = Ask(price, size)
            if ask in asks:
                ask_index = asks.index(ask)
                existing_ask = asks[ask_index]
                existing_ask.update_ask(size)
            else:
                asks.append(ask)
        serialized_asks = list()
        for ask in asks:
            serialized_asks.append(ask.serialize())
        return serialized_asks

    def _matched(self, order_):
        side = order_.side()

        if side == 'BUY':
            for order in self._sell_orders:
                if order_.matches(order):
                    print('MATCHED')
                    self._transaction_queue.put((order, order_))
                    return True
            return False

        elif side == 'SELL':
            for order in self._buy_orders:
                if order_.matches(order):
                    print('MATCHED')
                    self._transaction_queue.put((order, order_))
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

    def on_get(self, req, resp):
        for key, value in req.params.items():
            if key == 'side':
                if value == 'bid':
                    resp.media = self._order_book.get_bids()
                    resp.status = falcon.HTTP_200
                elif value == 'ask':
                    resp.media = self._order_book.get_asks()
                    resp.status = falcon.HTTP_200


app.add_route('/orders', Orders())

# verify transactions before add order to order book.
# // let
# signature = signatureObject.signature;
# // // Recover.
# // let
# signer = await web3.eth.accounts.recover(signatureObject.messageHash, signatureObject.signature, true);
