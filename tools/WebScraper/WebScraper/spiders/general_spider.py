import scrapy
import ScanOS
from bs4 import BeautifulSoup

class Spider(scrapy.Spider):
    name = "general"
    urls = [
        'https://en.wikipedia.org/wiki/Stuffing'
    ]
    
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = "html-dump" + ScanOS.getosslash() + response.url.split("/")[2] + "-" + response.url.split("/")[-1]
        filename = '%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        soup = BeautifulSoup(response.body, 'html.parser')