import falcon
import json
from web3 import Web3, HTTPProvider
from web3.auto import w3
from falcon_cors import CORS

cors = CORS(allow_origins_list=['http://localhost:3000'])

# falcon.API instances are callable WSGI apps
app = falcon.API(middleware=[cors.middleware])

# Web3 config
url = "HTTP://127.0.0.1:7545"
web3 = Web3(HTTPProvider(url))


orders = []

class Order(object):

    def __init__(
            self,
            token_maker,
            token_taker,
            amount_maker,
            amount_taker,
            address_maker,
            nonce,
            hash):
        self._token_maker = token_maker
        self._token_taker = token_taker
        self._amount_maker = amount_maker
        self._amount_taker = amount_taker
        self._address_maker = address_maker
        self._nonce = nonce
        self._hash = hash

    def __str__(self):
        return 'Order ['+str(self._amount_maker)+' '+self._token_maker+' @ '+str(self._amount_taker)+' '+self._token_taker+']'

    def hash(self):
        return self._hash

class Orders(object):

    orders = []

    def on_get(self, req, resp):
        for order in orders:
            print(order)

    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        signature = data["signature"]
        message_data = data["messageData"]
        message_hash = data["messageHash"]
        sender = message_data["addressMaker"]
        if self.is_valid_sig(message_hash, signature, sender):
            if not self._order_exists(signature):
                order = Order(
                    message_data["tokenMaker"],
                    message_data["tokenTaker"],
                    message_data["amountMaker"],
                    message_data["amountTaker"],
                    message_data["addressMaker"],
                    message_data["nonce"],
                    signature
                )
                orders.append(order)
                print(order)
                resp.status = falcon.HTTP_201
            else:
                resp.status = falcon.HTTP_409
        else:
            resp.status = falcon.HTTP_406

    def is_valid_sig(self, hash, sig, sender):
        signer = w3.eth.account.recoverHash(hash, signature=sig)
        return sender == signer

    def _order_exists(self, hash_):
        print(hash_)
        for order in orders:
            if hash_ == order.hash():
                return True
            else:
                return False

app.add_route('/orders', Orders())
