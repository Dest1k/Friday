import hashlib
def _portable_slug(key: str) -> str:
    slug = "".join(ch if ch.isascii() and (ch.isalnum() or ch in "_-") else "-" for ch in key.lower())
    return slug.strip("-_") or "plugin"


def _portable_skill_namespace(key: str) -> str:
    """Return a readable, collision-resistant namespace for a portable plugin."""
    slug = _portable_slug(key)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return f"agent-plugin-{slug}-{digest}"

