import csv
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import time
from dataclasses import dataclass
from lxml import html
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logger.propagate = False

if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class Region:
    code: str
    description: str
    url: str


@dataclass
class Product:
    product_ean: str
    product_description: str
    product_price: str
    region: str


class ScraperBot:
    products_list: List

    def __init__(self, url_list):
        self.url_list = url_list

    def process_urls(self, url_list):
        logger.info("-> process_regions")
        self.scrape_pages(
            url_list=url_list,
        )

        self.save_items(
            url_list=url_list,
        )

    def save_items(self, url_list):
        """
        Save items to CSV
        """
        logger.info("-> save_items")
        c = 0

        # Ensure the directories exist
        os.makedirs('output/csv', exist_ok=True)

        # Choose appropriate name for the file
        current_date = time.strftime("%Y-%m-%d")
        file_name = f"output/csv/{url_list.code}_products_{current_date}.csv"

        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['branch_region', 'region_description', 'created', 'ean', 'product_price', 'product_catalog_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for product_item in self.products_list:
                c += 1
                logger.info(f"Saving {url_list.code} - {c}")
                writer.writerow({
                    'branch_region': url_list.code,
                    'region_description': url_list.description,
                    'created': current_date,
                    'ean': product_item.product_ean,
                    'product_price': product_item.product_price,
                    'product_catalog_name': product_item.product_description,
                })

    def scrape_pages(self, url_list):
        """
        :param url_list:
        :param count:
        :return:
        """
        logger.info("-> scrape_region")
        page_number = 0
        region_code = url_list.code
        description = url_list.description
        url_target = url_list.url

        logger.info("Region: {} - description: {} ".format(region_code, description))
        logger.info("URL Target: {} ".format(url_target))
        logger.info("Products list")

        with sync_playwright() as p:
            browser = p.chromium.launch(slow_mo=50)
            page = browser.new_page()
            page.goto(url_target)

            while True:  # TODO: Para que dirve

                page_number = page_number + 1
                logger.info(f"Page: {page_number}")

                # Load the new items loads
                data_response = page.content()

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
                            region=region_code,
                        )

                        self.products_list.append(product_item)

                        logger.info(f"Region: {region_code} - Page: {page_number} -  EAN: {product_ean} - Product: {product_description} - Price: {product_price}")

                # TODO: click en pagina siguiente
                try:
                    next_button = page.wait_for_selector("//li[@class='paginate_button next']/a")
                    next_button.click()
                    time.sleep(0.5)
                except Exception as e:
                    logger.info("The pagination has finished, there isn't a next button.")
                    break

            # Close the browsers instances when the process has finished
            browser.close()

        return None

    @staticmethod
    def scrape_product(prod_elem, xpath, default_value=""):
        """
        :param prod_elem: lxml.html.HtmlElement
        :param xpath: str
        :param default_value: str
        :return: str
        """
        try:
            return prod_elem.xpath(xpath)[0].text.strip()
        except (IndexError, AttributeError):
            return default_value


def run():
    # Add all the regions
    regions_list = [
        Region(code='AMBA', description='Area Metropolitanaa de Buenos Aires', url='https://www.argentina.gob.ar/economia/comercio/preciosjustos/supermercados/area-metropolitana-de-buenos-aires-amba'),
        Region(code='PBA', description='Provincia de Buenos Aires', url='https://www.argentina.gob.ar/economia/comercio/preciosjustos/provincia-de-buenos-aires-excepto-amba'),
    ]

    scraper = Scraper(regions=regions_list)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(scraper.process_regions, regions_list)


if __name__ == "__main__":
    run()


