from typing import cast
import re

from bs4 import BeautifulSoup as HTMLParser
from bs4 import Tag

from API_Endpoints.helpers.models import DiscoveryResponse, PickOfTheWeek, PullListEntry

BASE_URL = "https://leagueofcomicgeeks.com"


def get_comic_id(tag: Tag):
    return tag.get("data-comic")


def get_comic_title(tag: Tag):
    title_tag = tag.select_one(".title a")
    return title_tag.get_text(strip=True) if title_tag else None


def get_comic_publisher(tag: Tag):
    publisher_tag = tag.select_one(".publisher")
    return publisher_tag.get_text(strip=True) if publisher_tag else None


def get_cover_url(tag: Tag) -> str | None:
    cover_tag = tag.select_one(".cover img")
    return cast(str, cover_tag.get("data-src")) if cover_tag else None


def normalize_cover_size(url: str, size: str) -> str:
    return re.sub(r"/covers/(small|medium|large)-", f"/covers/{size}-", url)


def get_cover_small_url(tag: Tag) -> str | None:
    url = get_cover_url(tag)
    return normalize_cover_size(url, "small") if url else None


def get_cover_medium_url(tag: Tag) -> str | None:
    return get_cover_url(tag)


def get_cover_large_url(tag: Tag) -> str | None:
    url = get_cover_url(tag)
    return normalize_cover_size(url, "large") if url else None


def get_comic_url(tag: Tag) -> str | None:
    cover_link = tag.select_one(".cover a")
    href = cover_link.get("href") if cover_link else None
    return f"{BASE_URL}{href}" if href else None


ATTR_EXTRACTOR_MAP = {
    "id": get_comic_id,
    "title": get_comic_title,
    "publisher": get_comic_publisher,
    "cover_small": get_cover_small_url,
    "cover_medium": get_cover_medium_url,
    "cover_large": get_cover_large_url,
    "comic_url": get_comic_url,
}


class PullListParser:
    def __init__(self) -> None:
        self.parsing_library: str = "lxml"

    @staticmethod
    def _parse_list_item(list_item: Tag):
        target_tags = {
            attr: extractor(list_item) for attr, extractor in ATTR_EXTRACTOR_MAP.items()
        }
        return PullListEntry(**target_tags)

    def _parse_pull_list(self, markup: str):
        parsed_document = HTMLParser(markup, self.parsing_library)
        return [*map(self._parse_list_item, parsed_document.select("li.issue"))]


def _parse_pick(tag: Tag) -> PickOfTheWeek:
    title_tag = tag.select_one(".stretched-link")
    title = title_tag.get_text(strip=True) if title_tag else ""

    href = cast(str, title_tag.get("href")) if title_tag else None
    comic_url = f"{BASE_URL}{href}" if href else ""

    publisher_tag = tag.select_one(".copy-really-small")
    publisher = publisher_tag.get_text(strip=True) if publisher_tag else ""

    img_tag = tag.select_one("img.card-img")
    raw_src = cast(str, img_tag.get("data-src")) if img_tag else ""
    cover_medium = f"{BASE_URL}{raw_src}" if raw_src else ""

    return PickOfTheWeek(title=title, publisher=publisher, cover_medium=cover_medium, comic_url=comic_url)


class HomepageParser:
    def __init__(self) -> None:
        self.parsing_library = "lxml"

    def parse_discovery(self, markup: str) -> DiscoveryResponse:
        doc = HTMLParser(markup, self.parsing_library)
        spotlights = doc.select("#featured-spotlights .col-xl-3")

        community_pick = [_parse_pick(spotlights[0])] if len(spotlights) >= 1 else []
        indie_pick = [_parse_pick(spotlights[1])] if len(spotlights) >= 2 else []

        return DiscoveryResponse(
            community_pick_of_the_week=community_pick,
            indie_pick_of_the_week=indie_pick,
        )


def _parse_new_release(tag: Tag):
    from API_Endpoints.helpers.models import NewRelease

    title_tag = tag.select_one(".title a")
    title = title_tag.get_text(strip=True) if title_tag else ""

    publisher_tag = tag.select_one(".publisher")
    publisher = publisher_tag.get_text(strip=True) if publisher_tag else ""

    img_tag = tag.select_one(".cover img")
    cover_medium = cast(str, img_tag.get("data-src")) if img_tag else ""
    cover_small = normalize_cover_size(cover_medium, "small") if cover_medium else ""
    cover_large = normalize_cover_size(cover_medium, "large") if cover_medium else ""

    cover_link = tag.select_one(".cover a")
    href = cover_link.get("href") if cover_link else None
    comic_url = f"{BASE_URL}{href}" if href else ""

    pull_count = int(tag.get("data-pulls", 0))

    return NewRelease(
        title=title,
        publisher=publisher,
        cover_small=cover_small,
        cover_medium=cover_medium,
        cover_large=cover_large,
        comic_url=comic_url,
        pull_count=pull_count,
    )


class NewReleasesParser:
    def __init__(self) -> None:
        self.parsing_library = "lxml"

    def parse(self, markup: str, limit: int = 20) -> list:
        doc = HTMLParser(markup, self.parsing_library)
        items = doc.select("li.issue")
        releases = [_parse_new_release(item) for item in items]
        releases.sort(key=lambda r: r.pull_count, reverse=True)
        return releases[:limit]