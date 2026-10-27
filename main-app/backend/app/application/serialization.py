import json
from datetime import datetime
from typing import Any


def json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=lambda item: item.isoformat() if isinstance(item, datetime) else str(item)))
