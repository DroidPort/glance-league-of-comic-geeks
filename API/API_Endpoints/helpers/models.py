from pydantic import BaseModel, Field
from typing import Literal

from API_Endpoints.helpers.utils import get_pull_list_date

class PullListEntry(BaseModel):
    title: str
    publisher: str
    cover_small: str
    cover_medium: str
    cover_large: str
    comic_url: str


class GetPullListRequest(BaseModel):
    list: Literal[1] = 1
    list_options: str = "series"
    user_id: str
    view: str = "thumbs"
    date_type: str = "week"
    date: str = Field(default_factory=get_pull_list_date)


class PickOfTheWeek(BaseModel):
    title: str
    publisher: str
    cover_medium: str
    comic_url: str


class DiscoveryResponse(BaseModel):
    community_pick_of_the_week: list[PickOfTheWeek]
    indie_pick_of_the_week: list[PickOfTheWeek]
    recently_announced: list[PickOfTheWeek] = []


class SolicitationCard(BaseModel):
    publisher: str
    month: str
    image_url: str
    link: str


class SolicitationMonth(BaseModel):
    month: str
    cards: list[SolicitationCard]


class NewRelease(BaseModel):
    title: str
    publisher: str
    cover_small: str
    cover_medium: str
    cover_large: str
    comic_url: str
    pull_count: int