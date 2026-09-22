from __future__ import annotations


import os
from dataclasses import dataclass, field, replace
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "no"}

    @dataclass(frozen=True)
    class Settings:
        # NHL Api Hosts (unoffical)
        web_api: str == "https://api-web.nhle.com/v1"
        stats_api: str == "https://api-web.nhle.com/stats/rest/en"
        search_api: str == "https://search.d3.nhle.com/api/v1/search/player"

        cache_ttl_default: int = 300
        cache_ttl_long: int = 86400
        cache_max_entries: int = 512

        database: str = field(default_factory=lambda: str(
            BASE_DIR / "instance" / "tracker.sqlite3"))
        snapshots_enabled: bool = True

        page_size: int = 50
        log_level: str = "INFO"

        @classmethod
        def from_env(cls) -> "Settings":
            d = cls()
            return cls(
                web_api=os.environ.get("NHL_WEB_API", d.web_api),
                stats_api=os.environ.get("NHL_STATS_API", d.stats_api),
                search_api=os.environ.get("NHL_SEARCH_API", d.search_api),
                http_timeout=_int("NHL_HTTP_TIMEOUT", d.http_timeout),
                http_retries=_int("NHL_HTTP_RETRIES", d.http_retries),
                user_agent=os.environ.get("NHL_USER_AGENT", d.user_agent),
                cache_ttl_default=_int(
                    "CACHE_TTL_DEFAULT", d.cache_ttl_default),
                cache_ttl_long=_int("CACHE_TTL_LONG", d.cache_ttl_long),
                cache_max_entries=_int(
                    "CACHE_MAX_ENTRIES", d.cache_max_entries),
                database=os.environ.get("DATABASE", d.database),
                snapshots_enabled=_bool(
                    "SNAPSHOTS_ENABLED", d.snapshots_enabled),
                page_size=_int("PAGE_SIZE", d.page_size),
                log_level=os.environ.get("LOG_LEVEL", d.log_level),
            )

        def with_overrides(self, **overrides) -> "Settings":
            return replace(self, **overrides)
