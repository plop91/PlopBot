import scrapy
from bs4 import BeautifulSoup
import ScanOS
class Spider(scrapy.Spider):
    name = "wiki"
    urls = None
    def geturls(self):
        self.urls = []
        with open('urls.txt',"r") as file:
            for s in file:
                self.urls.append(s)

    def start_requests(self):
        if self.urls is None:
            self.geturls()
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = "html-dump" + ScanOS.getosslash() + response.url.split("/")[2] + "-" + response.url.split("/")[-1]
        filename = '%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        soup = BeautifulSoup(response.body, 'html.parser')