class OrderBook(object):

    def __init__(self):
        self._sell_orders = list()
        self._buy_orders = list()

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
                    return True
            return False

        elif side == 'SELL':
            for order in self._buy_orders:
                print("order_ " + str(order_))
                print("order " + str(order))
                if order_.matches(order):
                    print('MATCHED')
                    return True
            return False
        return False