import scrapy
import requests
import xml.dom.minidom


def urls_from_xml() -> list[str]:
    _xml = requests.get(
        "https://dblp.uni-trier.de/search/publ/api?q=toc%3Adb/conf/aaai/aaai2023.bht%3A&h=1000&format=xml"
    ).text
    domTree = xml.dom.minidom.parseString(_xml)
    collection = domTree.documentElement

    hits = collection.getElementsByTagName("hit")
    urls = []
    for hit in hits:
        url = hit.getElementsByTagName("ee")[0]
        urls.append(url.childNodes[0].data)
    return urls


def strlist_to_str(strlist: list[str]) -> str:
    for i in range(len(strlist)):
        strlist[i] = strlist[i].strip()
    return ", ".join(strlist)


class AAAISpider(scrapy.Spider):
    name = "aaai"
    start_urls = urls_from_xml()

    def parse(self, response):
        yield {
            "title": response.css("h1.page_title::text").get().strip(),
            "abstract": response.css("section.abstract::text").getall()[1].strip(),
            "url": response.css("a.pdf::attr(href)").get(),
            "keywords": response.css("section.keywords span.value::text")
            .get()
            .replace("\t", "")
            .replace("\n", "")
            .split(", "),
            "authors": strlist_to_str(response.css("span.name::text").getall()),
        }
