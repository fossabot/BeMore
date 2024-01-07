import scrapy
import re


def openreview_url(urls):
    for url in urls[::-1]:
        if "openreview" in url:
            return url
    return urls[0]  # if no openreview url, return the first url


class NipsSpider(scrapy.Spider):
    name = "nips"
    start_urls = ["https://nips.cc/Conferences/2023/Schedule?type=Poster"]

    def parse(self, response):
        for article in response.css("div::attr(onclick)"):
            article = re.findall(r"[0-9]+", article.get())
            if len(article) > 0:
                article = article[0]
            else:
                continue
            yield response.follow(
                f"Schedule?showEvent={article}",
                callback=self.parse_abstract,
            )

    def parse_abstract(self, response):
        abstract = response.css("div.abstractContainer::text").get()
        if abstract == "\n" or abstract is None:
            abstract = response.css("div.abstractContainer p::text").get()

        yield {
            "type": response.css("div.maincardType::text").get(),
            "title": response.css("div.maincardBody::text").get(),
            "authors": response.css("div.maincardFooter::text").get(),
            "url": openreview_url(
                response.css("div.maincard span a::attr(href)").getall()
            ),
            "abstract": abstract,
        }
