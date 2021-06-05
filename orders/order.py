ORDER_TYPE_LIMIT_BUY = 'limit_buy'
ORDER_TYPE_LIMIT_SELL = 'limit_sell'


class Order:
    LIMIT_SELL = ORDER_TYPE_LIMIT_SELL
    LIMIT_BUY = ORDER_TYPE_LIMIT_BUY

    def __init__(self, asset, limit_price, order_type):
        self.asset = asset
        self.order_id = None
        self.limit_price = limit_price
        self.order_type = order_type
