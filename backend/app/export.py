from io import StringIO
from .analytics import load_data

def csv_bytes() -> bytes:
    buffer = StringIO()
    load_data().to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
