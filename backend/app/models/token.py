from threading import Lock


_blacklisted_tokens: set[str] = set()
_lock = Lock()


def blacklist_token(token: str) -> None:
    with _lock:
        _blacklisted_tokens.add(token)


def is_token_blacklisted(token: str) -> bool:
    with _lock:
        return token in _blacklisted_tokens
