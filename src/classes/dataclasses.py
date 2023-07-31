from dataclasses import dataclass


@dataclass
class UrlRegion:
    code: str
    description: str
    url: str


@dataclass
class Product:
    product_ean: str
    product_description: str
    product_price: str
    region: str