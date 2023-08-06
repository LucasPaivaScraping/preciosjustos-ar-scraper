from playwright.sync_api import sync_playwright


class PlayWrightManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def stop(self):
        self.browser.close()
        self.playwright.stop()

    def get_page(self):
        return self.page
