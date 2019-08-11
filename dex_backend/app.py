import falcon
import json
from web3 import Web3, HTTPProvider
from web3.auto import w3
import requests
import time
import datetime

from falcon_cors import CORS

# This is terrible practice...
cors = CORS(
    allow_all_origins=True,
    allow_all_headers=True,
    allow_all_methods=True
)

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


class Asset(object):

    def __init__(self, address, symbol, amount):
        self.address = address
        self.symbol = symbol
        self.amount = amount

    def __eq__(self, other):
        if isinstance(other, Asset):
            return self.address == other.address

    def __ne__(self, other):
        eq = Asset.__eq__(self, other)
        return NotImplemented if eq is NotImplemented else not eq

    def serialize(self):
        return {
            "asset": {
                "symbol": self.symbol,
                "address": self.address,
                "amount": self.amount
            }
        }

    def update_asset(self, amount):
        self.amount = self.amount + amount


class Account(object):

    def __init__(self, address):
        self.address = address
        self.assets = list()

    def __eq__(self, other):
        if isinstance(other, Account):
            return self.address == other.address
        return NotImplemented

    def __ne__(self, other):
        eq = Account.__eq__(self, other)
        return NotImplemented if eq is NotImplemented else not eq

    def serialize(self):
        serialized_assets = list()
        for asset in self.assets:
            serialized_assets.append(asset.serialize())
        return {
            "account": {
                "address": self.address,
                "assets": serialized_assets
            }
        }

    def update_balance(self, address, symbol, amount):
        asset = Asset(
            address,
            symbol,
            amount
        )
        if asset not in self.assets:
            self.assets.append(asset)
        else:
            index = self.assets.index(asset)
            self.assets[index].update_asset(amount)

    def balance_of(self, asset_address):
        for asset in self.assets:
            if asset.address == asset_address:
                return asset.amount
        return 0


class AccountManager(object):

    def __init__(self):
        self._accounts = list()

    def register_account(self, address):
        account = Account(address)
        if account not in self._accounts:
            self._accounts.append(account)
            return True
        return False

    def register_asset(self, account_address, asset_address, asset_symbol, asset_amount):
        account = self.get_account(account_address)
        if account in self._accounts:
            account.update_balance(asset_address, asset_symbol, asset_amount)
            return True
        return False

    def get_accounts(self):
        serialized_accounts = list()
        for account in self._accounts:
            serialized_accounts.append(account.serialize())
        return serialized_accounts

    def get_account(self, address):
        for account in self._accounts:
            if account.address == address:
                return account
        return None

    def get_balance_of(self, address, asset):
        for account in self._accounts:
            if account.address == address:
                return account.balance_of(asset)
        return 0


account_manager = AccountManager()


class Accounts(object):

    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        address = data["address"]
        if account_manager.register_account(address):
            resp.status = falcon.HTTP_201
        else:
            resp.status = falcon.HTTP_409

    def on_get(self, req, resp):
        resp.media = account_manager.get_accounts()
        resp.status = falcon.HTTP_202


class AccountsAssets(object):

    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        asset_address = data["asset"]["address"]
        asset_amount = data["asset"]["amount"]
        asset_symbol = data["asset"]["symbol"]
        account_address = data["account_address"]
        if account_manager.register_asset(account_address, asset_address, asset_symbol, asset_amount):
            resp.status = falcon.HTTP_201
        else:
            resp.status = falcon.HTTP_406

    def on_get(self, req, resp):
        # data = json.loads(req.stream.read().decode('utf-8'))
        # account_address = data["address"]
        for key, value in req.params.items():
            if key == 'account':
                account = account_manager.get_account(value)
                if account is None:
                    resp.status = falcon.HTTP_404
                else:
                    resp.media = account.serialize()
            else:
                resp.status = falcon.HTTP_405


class Order(object):

    def __init__(
            self,
            # token_maker_name,
            # token_taker_name,
            timestamp,
            status,
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
        self._timestamp = timestamp
        self._status = status
        self._side = side
        self._token_maker = token_maker
        self._token_taker = token_taker
        self._amount_maker = amount_maker
        self._amount_taker = amount_taker
        self._address_maker = address_maker
        self._nonce = nonce
        self._hash = hash

    def __str__(self):
        return self._timestamp+' [info] Order Placed - aapl_usdx market - account '+self._address_maker[:8]+' placed '+self._side+' order for '+str(self._amount_maker)+' '+self._token_maker[:10]+' @ '+str(self._amount_taker)+' '+self._token_taker[:10]

    def serialize(self):
        if self._side == 'BUY':
            qty = self._amount_taker
            price = self.amount_maker() / 1000000000000000000 / qty
        else:
            qty = self.amount_maker()
            price = self.amount_taker() / 1000000000000000000 / qty

        return {
            "status": self._status,
            "timestamp": self._timestamp,
            "addressMaker": self._address_maker,
            "amountMaker": str(self._amount_maker),
            "amountTaker": str(self._amount_taker),
            "nonce": str(self._nonce),
            "tokenMaker": self._token_maker,
            "tokenTaker": self._token_taker,
            "hash": self._hash,
            "qty": str(qty),
            "price": str(price),
            "side": self._side,
        }

    def timestamp(self):
        return self._timestamp

    def status(self):
        return self._status

    def update_status(self, status):
        self._timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self._status = status

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

    def hash(self):
        return self._hash

    def matches(self, another):
        # TODO: Should also account for <= or =>
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
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
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
        if response.status_code == 201:
            log = timestamp + ' [info] Trade Executed - aapl_usdx market - account ' + address_maker[:8] + ' traded ' + str(amount_maker) + ' ' + token_maker[:10] + ' to ' + address_taker[:8] + ' for ' + str(amount_taker) + ' ' + token_taker[:10]
            print(log)


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

        self._filled_orders = list()
        self._cancelled_orders = list()
        self._open_orders = list()

    def get_open_orders(self):
        self._open_orders = list()
        self._open_orders.extend(self._buy_orders)
        self._open_orders.extend(self._sell_orders)
        self._open_orders.sort(key=lambda order: order.timestamp())
        serialized_orders = list()
        for o in self._open_orders:
            serialized_orders.append(o.serialize())
        return serialized_orders

    def get_filled_orders(self):
        self._filled_orders.sort(key=lambda order: order.timestamp())
        serialized_orders = list()
        for o in self._filled_orders:
            serialized_orders.append(o.serialize())
        return serialized_orders

    def get_orders_of(self, address):
        orders = list()
        buy_orders = list()
        sell_orders = list()
        filled_orders = list()
        cancelled_orders = list()

        for order in self._buy_orders:
            if order.address_maker() == address:
                buy_orders.append(order)

        for order in self._sell_orders:
            if order.address_maker() == address:
                sell_orders.append(order)

        for order in self._filled_orders:
            if order.address_maker() == address:
                filled_orders.append(order)

        for order in self._cancelled_orders:
            if order.address_maker() == address:
                cancelled_orders.append(order)

        orders.extend(buy_orders)
        orders.extend(sell_orders)
        orders.extend(filled_orders)
        orders.extend(cancelled_orders)
        orders.sort(key=lambda order: order.timestamp(), reverse=True)

        serialized_orders = list()
        for order in orders:
            serialized_orders.append(order.serialize())
        return serialized_orders

    def get_cancelled_orders(self):
        self._cancelled_orders.sort(key=lambda order: order.timestamp())
        serialized_orders = list()
        for order in self._cancelled_orders:
            serialized_orders.append(order.serialize())
        return serialized_orders

    def put(self, order):
        side = order.side()
        if side == 'BUY':
            if not self._matched(order):
                self._buy_orders.append(order)
        elif order.side() == 'SELL':
            if not self._matched(order):
                self._sell_orders.append(order)

    def cancel_order(self, hash_):
        for i, order in enumerate(self._buy_orders):
            if order.hash() == hash_:
                self._buy_orders.pop(i)
                self._cancelled_orders.append(order)
                order.update_status("CANCELLED")
                return True
        for i, order in enumerate(self._sell_orders):
            if order.hash() == hash_:
                self._sell_orders.pop(i)
                self._cancelled_orders.append(order)
                order.update_status("CANCELLED")
                return True
        return False

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
        bids.sort(key=lambda x: x.price, reverse=True)
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
        asks.sort(key=lambda x: x.price, reverse=False)
        serialized_asks = list()
        for ask in asks:
            serialized_asks.append(ask.serialize())
        return serialized_asks

    def _matched(self, order_):
        side = order_.side()

        if side == 'BUY':
            self._sell_orders.sort(key=lambda order: order.timestamp())
            for i, order in enumerate(self._sell_orders):
                if order_.matches(order):
                    order.update_status("FILLED")
                    order_.update_status("FILLED")
                    self._sell_orders.pop(i)
                    self._filled_orders.append(order)
                    self._filled_orders.append(order_)
                    self._transaction_queue.put((order, order_))
                    return True
            return False

        elif side == 'SELL':
            self._buy_orders.sort(key=lambda order: order.timestamp)
            for i, order in enumerate(self._buy_orders):
                if order_.matches(order):
                    self._sell_orders.pop(i)
                    self._filled_orders.append(order)
                    self._filled_orders.append(order_)
                    self._transaction_queue.put((order, order_))
                    return True
            return False
        return False


class Orders(object):

    def __init__(self):
        self._order_book = OrderBook()

    def on_post(self, req, resp):
        data = json.loads(req.stream.read().decode('utf-8'))
        signature = data["signature"]
        order_data = data["orderData"]
        message_hash = data["messageHash"]
        sender = order_data["addressMaker"]
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        status = "OPEN"
        if self.is_valid_sig(message_hash, signature, sender):
            order = Order(
                timestamp,
                status,
                order_data["side"],
                order_data["tokenMaker"],
                order_data["tokenTaker"],
                int(order_data["amountMaker"]),
                int(order_data["amountTaker"]),
                order_data["addressMaker"],
                order_data["nonce"],
                signature
            )
            if self._user_has_enough_funds(order):
                print(order)
                self._order_book.put(order)
                resp.status = falcon.HTTP_201
            else:
                resp.status = falcon.HTTP_402
        else:
            resp.status = falcon.HTTP_406

    def is_valid_sig(self, hash, sig, sender):
        signer = w3.eth.account.recoverHash(hash, signature=sig)
        return sender == signer

    def _user_has_enough_funds(self, order):
        return True

    def on_get(self, req, resp):
        for key, value in req.params.items():
            if key == 'side':
                if value == 'bid':
                    resp.media = self._order_book.get_bids()
                    resp.status = falcon.HTTP_200
                elif value == 'ask':
                    resp.media = self._order_book.get_asks()
                    resp.status = falcon.HTTP_200
            if key == 'status':
                if value == 'open':
                    resp.media = self._order_book.get_open_orders()
                if value == 'filled':
                    resp.media = self._order_book.get_filled_orders()
                if value == 'cancelled':
                    resp.media = self._order_book.get_cancelled_orders()
            if key == 'of':
                resp.media = self._order_book.get_orders_of(value)

    def on_delete(self, req, resp):
        for key, value in req.params.items():
            if key == 'hash':
                if self._order_book.cancel_order(value):
                    resp.status = falcon.HTTP_204
                else:
                    resp.status = falcon.HTTP_404
            else:
                resp.status = falcon.HTTP_405



app.add_route('/orders', Orders())
app.add_route('/accounts', Accounts())
app.add_route('/accounts/assets', AccountsAssets())

# verify transactions before add order to order book.
# // let
# signature = signatureObject.signature;
# // // Recover.
# // let
# signer = await web3.eth.accounts.recover(signatureObject.messageHash, signatureObject.signature, true);
