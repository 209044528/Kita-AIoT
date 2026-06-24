from datetime import datetime
from typing import Any


def model_to_dict(model: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        result[column.name] = value.isoformat() if isinstance(value, datetime) else value
    return result
