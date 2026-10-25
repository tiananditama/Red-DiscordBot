"""Global default for Discord's ``@silent`` message flag.

Discord lets a message suppress push/desktop notifications by setting the
``suppress_notifications`` message flag, which discord.py exposes as the
``silent`` keyword argument on message-sending methods.

Red sends messages through a handful of discord.py entry points, so instead of
touching every call site this module wraps those entry points once and defaults
``silent`` to :data:`_enabled` unless the caller passed it explicitly.
"""

from __future__ import annotations

import functools
from typing import Any, Callable

import discord

__all__ = ["apply_silent_defaults", "set_silent_default", "silent_default_enabled"]

_enabled: bool = True
_applied: bool = False


def silent_default_enabled() -> bool:
    """Whether ``silent=True`` is currently applied to outgoing messages by default."""
    return _enabled


def set_silent_default(enabled: bool) -> None:
    """Enable or disable the ``silent=True`` default for outgoing messages."""
    global _enabled
    _enabled = bool(enabled)


def _with_silent_default(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if _enabled:
            kwargs.setdefault("silent", True)
        return await func(*args, **kwargs)

    wrapper._red_silent_wrapper = True  # type: ignore[attr-defined]
    return wrapper


def _patch(owner: type, name: str) -> None:
    original = getattr(owner, name)
    if getattr(original, "_red_silent_wrapper", False):
        return
    setattr(owner, name, _with_silent_default(original))


def apply_silent_defaults() -> None:
    """Patch discord.py send methods so messages default to ``silent=True``.

    This is idempotent, so it is safe to call from multiple entry points.
    """
    global _applied
    if _applied:
        return
    _patch(discord.abc.Messageable, "send")
    _patch(discord.InteractionResponse, "send_message")
    _patch(discord.Webhook, "send")
    _applied = True
