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

    def amount_maker(self):
        return self._amount_maker

    def amount_taker(self):
        return self._amount_taker

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