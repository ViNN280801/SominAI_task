from time import sleep
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from modules.logger import Logger, LogLevel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TikTokLibraryParser:
    """
    A universal parser for the TikTok Library search API.
    Dynamically constructs URLs based on given parameters.
    """

    BASE_URL = "https://library.tiktok.com/ads"

    def __init__(self):
        self.logger = Logger
        self.logger.configure_logger(name="TikTokLibraryParser", level=LogLevel.DEBUG)

    def build_query(self, region: str, adv_name: str, **kwargs) -> str:
        """
        Constructs a TikTok Library query URL.

        :param region: The region code (e.g., "BE", "US", "AT").
        :param adv_name: The advertiser's name or keyword for search.
        :param kwargs: Optional parameters for the query (e.g., start_time, end_time, sort_type, etc.).
        :return: Constructed URL for the TikTok Library search.
        """
        # Define mandatory parameters
        query_params = {"region": region, "adv_name": adv_name}

        # Add optional parameters if provided
        query_params.update({k: v for k, v in kwargs.items() if v is not None})

        # Encode the query parameters into a URL
        url = f"{self.BASE_URL}?{urlencode(query_params)}"
        self.logger.log_debug(f"Constructed URL: {url}")
        return url

    def fetch_data(self, url: str) -> str:
        """
        Fetches the HTML content of the TikTok Library page by navigating to the URL.

        :param url: The URL of the TikTok Library search page.
        :return: HTML content of the page as a string.
        """
        self.logger.log_info(f"Fetching data from URL: {url}")

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")  # Required for running in Docker
        options.add_argument(
            "--disable-dev-shm-usage"
        )  # To handle shared memory issues
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)

            # Scroll until the page is fully loaded
            SCROLL_PAUSE = 2
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(SCROLL_PAUSE)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ad_card"))
            )

            page_source = driver.page_source
        except Exception as e:
            self.logger.log_error(f"Error fetching data from URL: {e}")
            raise
        finally:
            driver.quit()

        return page_source

    def parse_data(self, html_content: str) -> list[dict]:
        """
        Parses HTML content to extract advertisement details.

        :param html_content: HTML content fetched from TikTok Library.
        :return: List of parsed advertisements.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        ads = []
        ad_cards = soup.find_all("div", class_="ad_card")
        for ad_card in ad_cards:
            title_element = ad_card.find("span", class_="ad_info_text")
            start_date_element = ad_card.find("span", string="First shown:").find_next(
                "span", class_="ad_item_value"
            )
            end_date_element = ad_card.find("span", string="Last shown:").find_next(
                "span", class_="ad_item_value"
            )

            title = title_element.text.strip() if title_element else "N/A"
            start_date = (
                start_date_element.text.strip() if start_date_element else "N/A"
            )
            end_date = end_date_element.text.strip() if end_date_element else "N/A"

            ads.append(
                {
                    "title": title,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

        self.logger.log_info(f"Parsed {len(ads)} ads from the page.")
        return ads

    def search_ads(self, region: str, adv_name: str, **kwargs) -> list[dict]:
        """
        Searches for ads in the TikTok Library with the given parameters.

        :param region: The region code (e.g., "BE").
        :param adv_name: The advertiser's name or keyword for search.
        :param kwargs: Additional parameters for customizing the search.
        :return: List of parsed advertisements.
        """
        try:
            url = self.build_query(region, adv_name, **kwargs)
            html_content = self.fetch_data(url)
            return self.parse_data(html_content)
        except Exception as e:
            self.logger.log_error(f"Error during search: {e}")
            return []
