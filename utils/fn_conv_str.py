from datetime import date, datetime

def serialize_data(data: dict) -> dict:
    serialized = {}
    for key, value in data.items():
      if isinstance(value, (datetime, date)):
        serialized[key] = str(value)  # or str(value)
      else:
        serialized[key] = value
    return serialized
