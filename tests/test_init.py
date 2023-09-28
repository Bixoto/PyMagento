import re
from datetime import datetime

import magento


def test_format_datetime():
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
                    magento.format_datetime(datetime.now()))


def test_format_parse_datetime():
    now = datetime.now().replace(microsecond=0)
    assert magento.parse_datetime(magento.format_datetime(now)) == now
