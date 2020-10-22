class Product:
    def __init__(self, asin, name, price, prev_price, link, rating):
        self.asin = asin
        self.name = name
        self.price = price
        self.prev_price = prev_price
        self.link = link
        self.rating = rating

    def __str__(self):
        msg = "ASIN: " + self.asin + "\n"
        msg += "Name: " + self.name + "\n"
        msg += "Price: " + str(self.price) + "\n"
        msg += "Previous Price: " + str(self.prev_price)
        return msg

    def serialize(self):
        return {
            # "asin": self.asin,
            "name": self.name,
            "price": [self.price],
            "prev_price": self.prev_price,
            "link": self.link
        }

    def from_json(self, json_):
        self.asin = json_["asin"]
        self.name = json_["name"]
        self.price = json_["price"]
        self.prev_price = json_["prev_price"]
        self.link = json_["link"]
        self.rating = json_["rating"]
