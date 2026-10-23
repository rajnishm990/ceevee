from typing import Optional 
from urllib.parse import urlparse 

def validate_http_url(value: Optional[str] , max_length: int = 300) -> Optional[str]:
    if value is None:
        return None 
    value = value.strip()
    if value== "":
        return None 
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Must be valid http(s) URL")
    if len(value)> max_length:
        raise ValueError("URL is too long")

    return value