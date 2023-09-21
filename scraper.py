import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
import argparse
import os
import asyncio
from abc import ABC, abstractmethod

class ScraperBase(ABC):
    @abstractmethod
    def scrape_all_pages(self):
        pass


class ScraperMixin:
    # Contains all the common methods so that they can be reused in individual Scraper implementations but arent forced by the ScraperBase abstract class

    def _get_image_url(self, img_element):
        # Get all urls with the width parameter from the data-srcset, then split them by commas, get the first one since all the urls are the same
        try:
            img_url = img_element['src']

        except KeyError:
            imgurls_datascrset = img_element['data-srcset']
            imgurls_list = [url.strip() for url in imgurls_datascrset.split(',')]
            img_url = imgurls_list[0].split(" ")[0]

        return img_url

    def _get_page_range(self, last_page, start_from = 1):
        # Generates a range of page numbers starting from 'start_from' up to and including 'last_page'.
        page_range = range(start_from, last_page +1)
        return page_range
    
    def _extract_last_page_number(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        pagination = soup.find("nav", class_ = "pagination")
        last_page_list_item = pagination.find_all('li', class_='pagination-link')[-1]
        last_page_link = last_page_list_item.find('a')
        try:
            last_page = int(last_page_link.text.strip())
            return last_page
        
        except ValueError as e:
            print("Error converting last page number to int.")
            raise e
        
    def _extract_page(self, content):
        """
        Scrapes content from a specific page URL and returns a list of results.

        Args:
            page_url (str): The URL of the page to be scraped.

        Returns:
            list: A list of tuples containing scraped data (title, summary, URL, image URL) from the page.
        """
        
        soup = BeautifulSoup(content, 'html.parser')
        article_list = soup.find('div', class_=["entry-list", "entries-articles"])
        items = article_list.find_all('div', class_ = "entry-inner")
        results = []

        for item in items:
            title = item.find('h3', class_ = "entry-title").text.strip()
            summary = item.find('p', class_ = "entry-body__text").text.strip()
            article_url = item.find('h3', class_ = "entry-title").find('a')['href']

            img_elem = item.find('a', class_ = "image").find('img')
            img_url = self._get_image_url(img_elem)

            results.append((title, summary, article_url, img_url))

        return results
        

class Scraper(ScraperBase, ScraperMixin):
    # Initial synchronous Scraper implementation
    def __init__(self, base_url: str, max_retries : int = 3, retry_interval : float = 5, between_req_wait : float = 5):
        """
        Initializes a Scraper instance.

        Args:
            base_url (str): The base URL of the website to be scraped.
            max_retries (int, optional): The maximum number of retries on request failure. Default is 3.
            retry_interval (int, optional): The time interval (in seconds) between retries. Default is 5.
            between_req_wait (int, optional): The time interval (in seconds) between page loads. Default is 5.
        """        
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.between_req_wait = between_req_wait 

    def _get_last_page_number(self):
        # Extracts and returns the last page number from the website's pagination.
        response = self._get_response(self.base_url)
        return self._extract_last_page_number(response.content)
            
    
    def _get_response(self, page_url):
        # Sends a GET request to the specified 'page_url' and handles retries according to the 'max_retries' and 'retry_interval' specified during object creation.
        retry_counter = 0
        exception = None
        while retry_counter < self.max_retries:
            try:
                response = requests.get(page_url)
                response.raise_for_status()  
                return response
            
            except requests.exceptions.RequestException as e:
                print(f"Failed to retrieve page {page_url}, sleeping for {self.retry_interval}")
                retry_counter += 1
                time.sleep(self.retry_interval)
                exception = e
        raise exception #Exception(f"Failed to retrieve valid response for {page_url}: e")
                
        

    def scrape_page(self, page_url):
        """
        Scrapes content from a specific page URL and returns a list of results.

        Args:
            page_url (str): The URL of the page to be scraped.

        Returns:
            list: A list of tuples containing scraped data (title, summary, URL, image URL) from the page.
        """
        
        print(f'Scraping {page_url}')
        response = self._get_response(page_url)
        return self._extract_page(response.content)
    

    def scrape_all_pages(self):
        """
        Scrapes content from all pages of the website and returns a list of results.

        Returns:
            list: A list of tuples containing scraped data (title, summary, URL, image URL) from all pages.
        """
        print(f"Running scraper for {self.base_url} with {self.max_retries} max retries, {self.retry_interval} sec retry interval, {self.between_req_wait} secs between page loads")
        last_page = self._get_last_page_number()
        #last_page = 2
        page_range = self._get_page_range(last_page)
        print(f'{page_range[-1]} pages found')
        all_results = []

        for page in page_range:
            page_url = (f'{self.base_url}?p1400={page}')
            page_results = self.scrape_page(page_url)
            all_results.extend(page_results)

            time.sleep(self.between_req_wait)  # Wait between requests

        return all_results




class ScraperAsync(ScraperBase, ScraperMixin):
    # Scraper implementation utilizing the asyncio asynchronous run
    def __init__(self, base_url : str , semaphore_limit : int = 100, max_retries : int = 3 , retry_interval : float = 5, between_req_wait : float = 5):
        """
        Initializes a Scraper instance.

        Args:
            base_url (str): The base URL of the website to be scraped.
            semaphore_limit (int): The limit that asyncio will set for max coroutines to run concurently. 
            max_retries (int, optional): The maximum number of retries on request failure. Default is 3.
            retry_interval (float, optional): The time interval (in seconds) between retries. Default is 5.
            between_req_wait (float, optional): The time interval (in seconds) between page loads. Default is 5.
        """        
        self.base_url = base_url
        self.semaphore_limit = semaphore_limit
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.between_req_wait = between_req_wait 

    async def _get_last_page_number(self):
        # Extracts and returns the last page number from the website's pagination.
        response = await self._get_response(self.base_url)
        return self._extract_last_page_number(response.content)
                
    
    async def _get_response(self, page_url):
        # Sends a GET request to the specified 'page_url' and handles retries according to the 'max_retries' and 'retry_interval' specified during object creation.
        retry_counter = 0
        exception = None
        while retry_counter < self.max_retries:
            try:
                #async with self.semaphore:
                    response = await asyncio.to_thread(requests.get, page_url)
                    response.raise_for_status()  
                    return response
            except asyncio.CancelledError as e:
                # This exception occurs if the coroutine is canceled (e.g., due to a timeout)
                print(e)
                print(f"Coroutine for {page_url} was canceled due to timeout.")         
            except requests.exceptions.RequestException as e:
                retry_counter += 1                
                if response.status_code == 429:
                    # Implement exponential backoff
                    wait_time = 2 ** retry_counter
                    print(f"Received 429 error for {page_url}. Retrying in {wait_time} seconds.")
                    await asyncio.sleep(wait_time)
                else:
                    exception = e
                    await asyncio.sleep(self.between_req_wait)
        raise exception #Exception(f"Failed to retrieve valid response for {page_url}: e")
                
        

    async def scrape_page(self, page_url):
        """
        Scrapes content from a specific page URL and returns a list of results.

        Args:
            page_url (str): The URL of the page to be scraped.

        Returns:
            list: A list of tuples containing scraped data (title, summary, URL, image URL) from the page.
        """
        
        response = await self._get_response(page_url)
        print(f'Scraping {page_url}')

        return self._extract_page(response.content)
    

    def scrape_all_pages(self):
        return asyncio.run(self._scrape_all_pages_async())
    
    async def _scrape_all_pages_async(self):
        last_page = await self._get_last_page_number()
        page_range = range(1, last_page + 1)
        print(f'{last_page} pages found')

        # create semaphore inside asyncio.run so that it is attached to a correct loop. Use semaphore for request throttling so that we dont overload the server
        semaphore = asyncio.Semaphore(self.semaphore_limit)

        all_results = []

        async def scrape_page_async(page):
            page_url = f'{self.base_url}?p1400={page}'
            async with semaphore:
                return await self.scrape_page(page_url)

        tasks = [scrape_page_async(page) for page in page_range]
        results = await asyncio.gather(*tasks)
        for page_results in results:
            all_results.extend(page_results)

        return all_results

    
if __name__ == "__main__":
    # Since the script was specifically built for this URL, it is hardcoded here and not passed as an argument
    base_url = "https://www.bizztreat.com/bizztro"

    parser = argparse.ArgumentParser(description="Web scraping script with optional arguments")
    #parser.add_argument("--base-url", type=str, required=True, help="Base URL for scraping")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries on request failure")
    parser.add_argument("--retry-time", type=float, default=5, help="Time (in seconds) to wait between retries")
    parser.add_argument("--wait-time", type=float, default=2, help="Time (in seconds) to wait between page loads")
    parser.add_argument("--semaphore-limit", type=int, default=5, help="Max concurrent coroutines for asyncio semaphore")
    parser.add_argument("--output", default="data/mnamky.csv", help="Path to the output CSV file")
    parser.add_argument("--no-async", action="store_true", help="Turn of asynchronous run, making the program request one page at a time")

    args = parser.parse_args()

    # check if path is just file name, if directory, check if it exists, else create it
    output = args.output
    if not os.path.exists(output):
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=False)

    #semaphore_limit = 5
    if args.no_async:
        scraper = Scraper(
            base_url=base_url,
            max_retries=args.max_retries,
            retry_interval=args.retry_time,
            between_req_wait=args.wait_time
            )
    else:       
        scraper = ScraperAsync(
            base_url=base_url,
            semaphore_limit = args.semaphore_limit,
            max_retries=args.max_retries,
            retry_interval=args.retry_time,
            between_req_wait=args.wait_time
            )

    try:
        results = scraper.scrape_all_pages()
    except Exception as e:
        print(f"An error occurred: {e}")
        exit()

    columns = ['title', 'summary', 'url', 'image_url']
    df = pd.DataFrame(results, columns=columns)
    df.to_csv(output, sep="\t", encoding="UTF-16", index = False)
    print(df)
