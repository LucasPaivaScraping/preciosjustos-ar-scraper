import time
from lxml import html

from src.classes.dataclasses import Product
from src.utils import logger_config


logger = logger_config.get_logger(__name__)


class PageScraper:

    def __init__(self, page, item_data):
        self.page = page
        self.item_data = item_data
        self.page_number = 0

    def has_next_page(self):
        try:
            next_button = self.page.wait_for_selector("//li[@class='paginate_button next']/a")
            return True
        except Exception:
            logger.info("The pagination has finished, there isn't a next button.")
            return False

    def go_to_next_page(self):
        try:
            next_button = self.page.wait_for_selector("//li[@class='paginate_button next']/a")
            next_button.click()
            time.sleep(0.5)
        except Exception:
            logger.info("The pagination has finished, there isn't a next button.")

    def increment_page(self):
        self.page_number += 1
        logger.info(f"Page: {self.page_number}")

    def get_page_number(self):
        return self.page_number

    def scrape_page(self):
        data_response = self.page.content()
        products_list = []

        if data_response:
            html_tree = html.fromstring(data_response)
            row_items_xpath = "//table[@id='ponchoTable']/tbody/tr"
            products = html_tree.xpath(row_items_xpath)

            for product_elem in products:
                product_ean_xpath = "./td[@data-title='EAN']/p"
                product_description_xpath = "./td[@data-title='Descripción']/p"
                product_price_xpath = "./td[@data-title='Precio']/p"

                product_ean = self.scrape_product(prod_elem=product_elem, xpath=product_ean_xpath)
                product_description = self.scrape_product(prod_elem=product_elem, xpath=product_description_xpath)
                product_price = self.scrape_product(prod_elem=product_elem, xpath=product_price_xpath)

                product_item = Product(
                    product_ean=product_ean,
                    product_description=product_description,
                    product_price=product_price,
                    region=self.item_data.code,
                )

                products_list.append(product_item)

        return products_list

    @staticmethod
    def scrape_product(prod_elem, xpath, default_value=""):
        try:
            return prod_elem.xpath(xpath)[0].text.strip()
        except (IndexError, AttributeError):
            return default_value