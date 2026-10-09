from datetime import UTC, datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Vancouver")


def local_time(dt: datetime, fmt: str = "%b %d, %Y %H:%M Vancouver time") -> str:
    # Naive datetimes are UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(LOCAL_TZ).strftime(fmt)
