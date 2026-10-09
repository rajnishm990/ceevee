import re
import secrets


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def generate_shareable_slug(domain_name: str) -> str:
    """e.g. 'Backend' -> 'backend-x7fQ2a'. Collision handling (retry-until-unique)
    lives in ResumeService, since only it can check the DB."""
    return f"{slugify(domain_name)}-{secrets.token_urlsafe(5)}"
