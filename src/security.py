def is_private_chat(chat) -> bool:
    """Return True only for private bot conversations."""
    return bool(chat and getattr(chat, "type", None) == "private")
