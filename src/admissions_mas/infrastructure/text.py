import hashlib
import re
from datetime import datetime, timezone


STOP_WORDS = {
    "là", "có", "cho", "và", "của", "một", "những", "các", "em", "anh",
    "chị", "tôi", "mình", "được", "không", "nào", "về", "thì", "để", "the",
    "is", "are", "a", "an", "to", "of", "and", "in", "for", "with",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\wÀ-ỹ]+", text.lower()) if token not in STOP_WORDS and len(token) > 1}


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"
