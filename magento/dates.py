from datetime import datetime

DATE_ISO_8601_FORMAT = "%Y-%m-%d %H:%M:%S"


def format_datetime(dt: datetime) -> str:
    """Format a datetime for Magento."""
    # "2021-07-02 13:19:18.300700" -> "2021-07-02 13:19:18"
    return dt.isoformat(sep=" ").split(".", 1)[0]


def parse_datetime(s: str) -> datetime:
    """Parse a datetime string from Magento."""
    return datetime.strptime(s, DATE_ISO_8601_FORMAT)
