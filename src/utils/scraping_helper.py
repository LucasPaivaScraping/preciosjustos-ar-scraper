def scrape_by_xpath(dom_elem, xpath, default_value=""):
    """
    :param dom_elem: lxml.html.HtmlElement
    :param xpath: str
    :param default_value: str
    :return: str
    """
    try:
        return dom_elem.xpath(xpath)[0].text.strip()
    except (IndexError, AttributeError):
        return default_value
