"""Shared dependencies for all routers."""
from API_Endpoints.helpers.service import LeagueOfComicGeeksService

_service_instance: LeagueOfComicGeeksService | None = None


def get_service() -> LeagueOfComicGeeksService:
    """Get or create the singleton service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = LeagueOfComicGeeksService()
    return _service_instance