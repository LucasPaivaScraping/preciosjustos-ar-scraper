import csv
import os
import time
from lxml import html
from typing import List

from src.utils import logger_config
from src.classes.browser_manager import PlayWrightManager
from src.classes.dataclasses import UrlRegion, Product
from src.classes.page_scraper import PageScraper

logger = logger_config.get_logger(__name__)


class ScraperBot:

    def __init__(self, input_data):
        self.input_data = input_data

    def process_urls(self):
        for item_data in self.input_data:
            products_list = self.scrape_pages(item_data=item_data)
            self.save_items(item_data=item_data, products_list=products_list)

    def save_items(self, item_data, products_list):
        """
        This methods decides the method of saving data (csv, sqlLite, MySql, Dynamo)
        :param item_data:
        :param products_list:
        :return:
        """
        logger.info("-> save_items")
        self.save_csv(item_data=item_data, products_list=products_list)

    def save_csv(self, item_data, products_list):
        c = 0

        os.makedirs('output/csv', exist_ok=True)

        current_date = time.strftime("%Y-%m-%d")
        file_name = f"output/csv/{item_data.code}_products_{current_date}.csv"

        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['branch_region', 'region_description', 'created', 'ean', 'product_price',
                          'product_catalog_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for product_item in products_list:
                c += 1
                logger.info(f"Saving {item_data.code} - {c}")
                writer.writerow({
                    'branch_region': item_data.code,
                    'region_description': item_data.description,
                    'created': current_date,
                    'ean': product_item.product_ean,
                    'product_price': product_item.product_price,
                    'product_catalog_name': product_item.product_description,
                })

    def scrape_pages(self, item_data):
        logger.info("-> scrape_region")

        manager = PlayWrightManager()
        manager.start()
        page = manager.get_page()
        page.goto(item_data.url)

        page_scrapper = PageScraper(page, item_data)
        products_list = self.iterate_pages(page_scrapper)

        manager.stop()

        return products_list

    def iterate_pages(self, page_scrapper: PageScraper):
        products_list = []

        while page_scrapper.has_next_page():
            page_scrapper.increment_page()

            new_products = page_scrapper.scrape_page()
            products_list.extend(new_products)

            for product in new_products:
                logger.info(
                    f"Region: {page_scrapper.item_data.code} - Page: {page_scrapper.get_page_number()} - EAN: {product.product_ean} - Product: {product.product_description} - Price: {product.product_price}")

            page_scrapper.go_to_next_page()

        return products_list

    def run(self):
        self.process_urls()


def run_scraper_bot():
    url_list = [
        UrlRegion(code='AMBA', description='Area Metropolitanaa de Buenos Aires', url='https://www.argentina.gob.ar/economia/comercio/preciosjustos/supermercados/area-metropolitana-de-buenos-aires-amba'),
    ]

    scraper = ScraperBot(input_data=url_list)
    scraper.run()


if __name__ == "__main__":
    run_scraper_bot()
