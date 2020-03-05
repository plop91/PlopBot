from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tools.WebScraper.WebScraper.spiders.wikipedia_spider import Spider as wiki
from tools.WebScraper.WebScraper.spiders.general_spider import Spider as general
import tools.WebScraper.soup as soup

spiders = [wiki, general]

process = CrawlerProcess(get_project_settings())
for spider in spiders:
    process.crawl(spider)
process.start()
soup.basicsoup()
