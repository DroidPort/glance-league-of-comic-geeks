from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import re

import httpx
from bs4 import BeautifulSoup
from API_Endpoints.helpers.models import DiscoveryResponse, GetPullListRequest, NewRelease, SolicitationCard, SolicitationMonth
from API_Endpoints.helpers.parser import HomepageParser, NewReleasesParser, PullListParser

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0"}
BASE_URL = "https://leagueofcomicgeeks.com"

_MONTH_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")

# Create a shared async HTTP client for all requests
_async_client: Optional[httpx.AsyncClient] = None


def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=30.0)
    return _async_client


@dataclass
class LeagueOfComicGeeksService:
    _pull_parser = PullListParser()
    _homepage_parser = HomepageParser()
    _new_releases_parser = NewReleasesParser()
    _solicitation_cache: Optional[list[SolicitationCard]] = field(default=None, init=False)
    _solicitation_cache_time: Optional[datetime] = field(default=None, init=False)
    _discovery_cache: Optional[DiscoveryResponse] = field(default=None, init=False)
    _discovery_cache_time: Optional[datetime] = field(default=None, init=False)
    _new_releases_cache: Optional[list[NewRelease]] = field(default=None, init=False)
    _new_releases_cache_time: Optional[datetime] = field(default=None, init=False)

    async def get_pull_list(self, request: GetPullListRequest):
        client = _get_async_client()
        resp = await client.get(
            f"{BASE_URL}/comic/get_comics",
            params=request.model_dump(),
            headers=HEADERS,
        )
        return self._pull_parser._parse_pull_list(resp.json()["list"])

    async def get_discovery(self) -> DiscoveryResponse:
        """Fetch discovery data. Caches for 1 hour."""
        if self._discovery_cache is not None and self._discovery_cache_time is not None:
            elapsed = (datetime.now() - self._discovery_cache_time).total_seconds()
            if elapsed < 3600:
                return self._discovery_cache

        try:
            client = _get_async_client()
            resp = await client.get(
                f"{BASE_URL}/comics",
                headers=HEADERS,
            )
            discovery = self._homepage_parser.parse_discovery(resp.text)
            self._discovery_cache = discovery
            self._discovery_cache_time = datetime.now()
            return discovery
        except Exception:
            return self._discovery_cache or DiscoveryResponse(
                community_pick_of_the_week=[],
                indie_pick_of_the_week=[],
                recently_announced=[],
            )

    async def fetch_solicitations_html(self) -> str:
        client = _get_async_client()
        resp = await client.get(
            f"{BASE_URL}/solicitations",
            headers=HEADERS,
        )
        resp.raise_for_status()
        return resp.text


    async def get_new_releases(self, limit: int = 20) -> list[NewRelease]:
        """Fetch this week's new releases sorted by pull count. Caches for 1 hour."""
        if self._new_releases_cache is not None and self._new_releases_cache_time is not None:
            elapsed = (datetime.now() - self._new_releases_cache_time).total_seconds()
            if elapsed < 3600:
                return self._new_releases_cache[:limit]

        try:
            client = _get_async_client()
            resp = await client.get(
                f"{BASE_URL}/comics/new-comics",
                headers=HEADERS,
            )
            resp.raise_for_status()
            releases = self._new_releases_parser.parse(resp.text, limit=100)  # Cache more than needed
            self._new_releases_cache = releases
            self._new_releases_cache_time = datetime.now()
            return releases[:limit]
        except Exception:
            return (self._new_releases_cache or [])[:limit]

    async def get_next_week_releases(self, limit: int = 20) -> list[NewRelease]:
        """Fetch next week's new releases. Caches for 1 hour."""
        next_week = datetime.now() + timedelta(days=7)
        url = f"{BASE_URL}/comics/new-comics/{next_week.year}/{next_week.month:02d}/{next_week.day:02d}"

        try:
            client = _get_async_client()
            resp = await client.get(url, headers=HEADERS)
            resp.raise_for_status()
            releases = self._new_releases_parser.parse(resp.text, limit=100)
            return releases[:limit]
        except Exception:
            return []

    async def get_solicitations(self) -> list[SolicitationCard]:
        """Fetch and parse solicitation cards. Caches for 1 hour."""
        if self._solicitation_cache is not None and self._solicitation_cache_time is not None:
            elapsed = (datetime.now() - self._solicitation_cache_time).total_seconds()
            if elapsed < 3600:
                return self._solicitation_cache

        try:
            html = await self.fetch_solicitations_html()
            solicitations = _parse_solicitations(html)
            self._solicitation_cache = solicitations
            self._solicitation_cache_time = datetime.now()
            return solicitations
        except Exception:
            return self._solicitation_cache or []

    async def get_solicitations_grouped(self, exclude: list[str] | None = None) -> list[SolicitationMonth]:
        """Return solicitations grouped by month, sorted newest first.

        If exclude is provided, cards matching those publisher names are hidden.
        Matching is case-insensitive. Default shows all publishers.
        """
        cards = await self.get_solicitations()
        if exclude:
            lower = [p.lower() for p in exclude]
            cards = [c for c in cards if c.publisher.lower() not in lower]
        groups: dict[str, list[SolicitationCard]] = {}
        for card in cards:
            groups.setdefault(card.month, []).append(card)

        def month_sort_key(month_str: str):
            try:
                return datetime.strptime(month_str, "%B %Y")
            except ValueError:
                return datetime.min

        sorted_months = sorted(groups.keys(), key=month_sort_key, reverse=True)
        return [SolicitationMonth(month=month, cards=groups[month]) for month in sorted_months]


def _resolve_url(href: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"


def _parse_alt(alt: str) -> tuple[str, str]:
    """
    Parse publisher and month from img alt text.
    Handles any ordering of month name and year, e.g.:
        "Marvel Comics June 2026 Solicitations" -> ("Marvel Comics", "June 2026")
        "Oni Press 2026 May Solicitations"      -> ("Oni Press", "May 2026")
    """
    label = re.sub(r"\s*Solicitations?\s*$", "", alt, flags=re.IGNORECASE).strip()
    month_m = _MONTH_RE.search(label)
    year_m = _YEAR_RE.search(label)
    if month_m and year_m:
        month = f"{month_m.group(0).title()} {year_m.group(0)}"
        publisher = _YEAR_RE.sub("", label)
        publisher = _MONTH_RE.sub("", publisher)
        publisher = re.sub(r"\s+", " ", publisher).strip()
        return publisher, month
    return label, ""


def _parse_solicitations(html: str) -> list[SolicitationCard]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    seen_links = set()

    for card in soup.select(".card-solicitation"):
        img = card.select_one("img.card-img")
        link_tag = card.select_one("a.stretched-link")

        if not img or not link_tag:
            continue

        image_url = _resolve_url(img.get("data-src") or img.get("src") or "")
        link = _resolve_url(link_tag.get("href") or "")

        if not image_url or not link or link in seen_links:
            continue
        seen_links.add(link)

        publisher, month = _parse_alt(img.get("alt", ""))

        results.append(SolicitationCard(
            publisher=publisher,
            month=month,
            image_url=image_url,
            link=link,
        ))

    return results