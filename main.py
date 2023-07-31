import csv
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import time

from lxml import html
from playwright.sync_api import sync_playwright

from src.classes import scraper_multithreading, scraper_bot

logger = logging.getLogger(__name__)
logger.propagate = False

if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Initial settings
MAX_WORKERS = 20

regions = [
        {
            "code": "AMBA",  # Include CABA
            "description": "Area Metropolitanaa de Buenos Aires",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/supermercados/area-metropolitana-de-buenos-aires-amba"
        },
        {
            "code": "PBA",  # Include LPL, BHB y MDQ
            "description": "Provincia de Buenos Aires",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/provincia-de-buenos-aires-excepto-amba",
        },
        {
            "code": "CAT",
            "description": "Catamarca",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/catamarca",
        },
        {
            "code": "CHA",
            "description": "Chaco",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/chaco",
        },
        {
            "code": "CHU",
            "description": "Chubut",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/chubut",
        },
        {
            "code": "CBA",
            "description": "Cordoba",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/cordoba",
        },
        {
            "code": "MDZ",
            "description": "Mendoza",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/mendoza",
        },
        {
            "code": "TUC",
            "description": "Tucuman",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/tucuman",
        },
        {
            "code": "ERI",
            "description": "Entre Rios",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/entre-rios",
        },
        {
            "code": "COR",
            "description": "Corrientes",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/corrientes",
        },
        {
            "code": "FOR",
            "description": "Formosa",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/formosa",
        },
        {
            "code": "JUJ",
            "description": "Jujuy",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/jujuy",
        },
        {
            "code": "PAM",
            "description": "La Pampa",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/la-pampa",
        },
        {
            "code": "RIO",
            "description": "La Rioja",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/la-rioja",
        },
        {
            "code": "MIS",
            "description": "Misiones",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/misiones",
        },
        {
            "code": "NEU",
            "description": "Neuquen",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/neuquen",
        },
        {
            "code": "RNE",
            "description": "Rio Negro",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/rio-negro",
        },
        {
            "code": "SAL",
            "description": "Salta",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/salta",
        },
        {
            "code": "SCR",
            "description": "Santa Cruz",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/santa-cruz",
        },
        {
            "code": "SFE",
            "description": "Santa Fe",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/santa-fe",
        },
        {
            "code": "SES",
            "description": "Santiago del Estero",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/santiago-del-estero",
        },
        {
            "code": "FUE",
            "description": "Tierra del Fuego",
            "url": "https://www.argentina.gob.ar/economia/comercio/preciosjustos/tierra-del-fuego-antartida-e-islas-del-atlantico-sur",
        },
    ]


def process_regions(region):
    logger.info("-> process_regions")
    products_list = scrape_region(
        region=region,
    )

    save_items(
        result_data=products_list,
        region=region,
    )


def save_items(result_data, region):
    """
    Save items to CSV
    """
    logger.info("-> save_items")
    c = 0

    # Ensure the directories exist
    os.makedirs('output/csv', exist_ok=True)

    # Choose appropriate name for the file
    current_date = time.strftime("%Y-%m-%d")
    file_name = f"output/csv/{region.get('code')}_products_{current_date}.csv"

    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['branch_region', 'region_description', 'created', 'ean', 'product_price', 'product_catalog_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for product_item in result_data:
            c += 1
            logger.info(f"Saving {region.get('code')} - {c}")
            writer.writerow({
                'branch_region': region.get("code"),
                'region_description': region.get("description"),
                'created': current_date,
                'ean': product_item.get("product_ean"),
                'product_price': product_item.get("product_price"),
                'product_catalog_name': product_item.get("product_description"),
            })


def scrape_region(region):
    """

    :param region:
    :param count:
    :return:
    """
    logger.info("-> scrape_region")
    page_number = 0
    products_list = []
    region_code = region.get("code")
    description = region.get("description")
    url_target = region.get("url")

    logger.info("Region: {} - description: {} ".format(region_code, description))
    logger.info("URL Target: {} ".format(url_target))
    logger.info("Products list")

    with sync_playwright() as p:
        browser = p.chromium.launch(slow_mo=50)
        # browser = p.chromium.launch(slow_mo=50, proxy={"server": proxy_server})
        # browser = p.firefox.launch(headless=False, slow_mo=50)
        # browser = p.webkit.launch(headless=False, slow_mo=50)
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

                for product in products:
                    product_ean_xpath = "./td[@data-title='EAN']/p"
                    product_description_xpath = "./td[@data-title='Descripción']/p"
                    product_price_xpath = "./td[@data-title='Precio']/p"

                    product_ean = get_text_or_default(product=product, xpath=product_ean_xpath)
                    product_description = get_text_or_default(product=product, xpath=product_description_xpath)
                    product_price = get_text_or_default(product=product, xpath=product_price_xpath)

                    product_item = {
                        "product_ean": product_ean,
                        "product_description": product_description,
                        "product_price": product_price,
                        "region": region_code,
                    }

                    products_list.append(product_item)

                    logger.info(f"Region: {region_code} - Page: {page_number} -  EAN: {product_ean} - Product: {product_description} - Price: {product_price}")

            # TODO: click en pagina siguiente
            try:
                next_button = page.wait_for_selector("//li[@class='paginate_button next']/a")
                next_button.click()
                time.sleep(0.5)
            except Exception as e:
                logger.info("The pagination has finished, there isnt next button.")
                break

        # Close the browsers insrtances when the process has finished
        browser.close()

    return products_list


def get_text_or_default(product, xpath, default="NOT_AVAILABLE"):
    if product.xpath(xpath):
        return product.xpath(xpath)[0].text
    else:
        return default


def main():
    """
    Scraper for PreciosJustos
    Site: https://www.argentina.gob.ar/economia/comercio/preciosjustos/supermercados
    """
    logger.info("START PreciosJustosAR- Scraping")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for region in regions:
            # one thread
            # process_regions(region=region)
            # Launch n multithreading workers
            executor.submit(process_regions, region)

    # logger.info(f"{bulk_model.objects.exclude(sku='NOT_AVAILABLE').count()} Registros obtenidos.")
    logger.info("END - Scraping")


if __name__ == "__main__":
    # main()
    # scraper_multithreading.run()
    scraper_bot.run_process()
