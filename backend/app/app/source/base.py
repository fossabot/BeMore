import logging
from datetime import datetime
from typing import Any

import feedparser
import requests
from celery import Task
from feedparser import FeedParserDict
from scrapy.http import HtmlResponse
from sqlmodel import Session, select

from app.models import CrawledItem, Item


def openreview_url(urls):
    for url in urls[::-1]:
        if "openreview" in url:
            return url
    return urls[0]  # if no openreview url, return the first url


class PaperRequestsTask(Task):
    url: str
    ignore_result: bool = True
    name: str

    @property
    def db(self):
        """
        Lazy loading of database connection.
        """
        from app.db.engine import engine

        return Session(engine)

    @staticmethod
    def parse_urls(response: HtmlResponse) -> list[str]:
        # you should return list of absolute urls
        raise NotImplementedError

    @classmethod
    def get_urls(cls) -> list[str]:
        response = cls._request(cls.url)
        if response is None:
            return []
        return cls.parse_urls(response)

    @staticmethod
    def parse(response: HtmlResponse) -> dict[str, str]:
        # you should return dict with fields:
        # title, abstract, url
        raise NotImplementedError

    @staticmethod
    def _request(
        url: str,
    ) -> HtmlResponse | None:  # On the Take class have same method(request)
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            return
        return HtmlResponse(url=url, body=response.content, encoding="utf-8")

    def save(self, data: list[tuple[str, dict[str, Any]]]) -> None:
        with self.db as db:
            objs = [CrawledItem(raw_url=item[0]) for item in data]
            db.add_all(objs)
            db.commit()

            # TODO: add relations between CrawledItem and Item
            objs = [
                Item(
                    **item[1],
                    from_source=self.name,
                )
                for item in data
            ]
            db.add_all(objs)
            db.commit()

    @staticmethod
    def post_parse(data: dict[str, Any]) -> dict[str, Any]:
        # you can do some post processing here
        return data

    def run(self, urls: list[str]):
        results = []
        for url in urls:
            response = PaperRequestsTask._request(url)
            if response is None:
                continue
            item = self.parse(response)
            item = self.post_parse(item)

            if item["title"] is None or item["abstract"] is None:
                logging.warning(f"Empty title or abstract: {url}")
                continue

            results.append((url, item))

        self.save(results)


class RSSTask(Task):
    name: str
    url: str
    ignore_result: bool = True

    @property
    def db(self):
        """
        Lazy loading of database connection.
        """
        from app.db.engine import engine

        return Session(engine)

    @staticmethod
    def parse(entry) -> dict[str, Any]:
        raise NotImplementedError

    def post_parse(self, entry: dict[str, Any]) -> dict[str, Any]:
        return entry

    def save(self, data: list[dict[str, Any]]) -> None:
        with self.db as db:
            # update Item table if exists
            for item in data:
                try:
                    db.add(Item(**item, from_source=self.name))
                    db.commit()
                except Exception:
                    db.rollback()
                    logging.warning(f"Duplicate item: {item['title']}")

                    existing_item = db.exec(
                        select(Item).where(Item.title == item["title"]),
                    ).one()
                    existing_item.category = item["category"]
                    existing_item.url = item["url"]
                    existing_item.abstract = item["abstract"]
                    existing_item.authors = item["authors"]
                    existing_item.last_updated = datetime.utcnow()
                    db.add(existing_item)
                    db.commit()

    def run(self):
        feed: FeedParserDict = feedparser.parse(self.url)
        results = []
        for entry in feed.entries:
            item = self.parse(entry)
            item = self.post_parse(item)

            if item["title"] is None or item["abstract"] is None:
                logging.warning(f"Empty title or abstract: {entry.link}")
                continue

            results.append(item)

        self.save(results)
