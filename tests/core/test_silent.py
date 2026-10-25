from unittest.mock import Mock

import discord

from redbot.core import _silent


def _reset(monkeypatch):
    monkeypatch.setattr(_silent, "_applied", False)
    monkeypatch.setattr(_silent, "_enabled", True)
    # Register the current attributes so monkeypatch restores them even though
    # apply_silent_defaults() replaces them without going through monkeypatch.
    monkeypatch.setattr(discord.abc.Messageable, "send", discord.abc.Messageable.send)
    monkeypatch.setattr(discord.Webhook, "send", discord.Webhook.send)
    monkeypatch.setattr(
        discord.InteractionResponse, "send_message", discord.InteractionResponse.send_message
    )


def _patch_messageable(monkeypatch, calls):
    async def fake_send(self, *args, **kwargs):
        calls.append(kwargs)
        return Mock(spec=discord.Message)

    monkeypatch.setattr(discord.abc.Messageable, "send", fake_send)


async def test_messageable_send_defaults_to_silent(monkeypatch):
    _reset(monkeypatch)
    calls = []
    _patch_messageable(monkeypatch, calls)

    _silent.apply_silent_defaults()
    await discord.abc.Messageable.send(object(), "hi")

    assert calls == [{"silent": True}]


async def test_explicit_silent_is_preserved(monkeypatch):
    _reset(monkeypatch)
    calls = []
    _patch_messageable(monkeypatch, calls)

    _silent.apply_silent_defaults()
    await discord.abc.Messageable.send(object(), "hi", silent=False)

    assert calls == [{"silent": False}]


async def test_disabled_does_not_add_silent(monkeypatch):
    _reset(monkeypatch)
    calls = []
    _patch_messageable(monkeypatch, calls)

    _silent.apply_silent_defaults()
    _silent.set_silent_default(False)
    await discord.abc.Messageable.send(object(), "hi")

    assert calls == [{}]


async def test_apply_is_idempotent(monkeypatch):
    _reset(monkeypatch)
    calls = []
    _patch_messageable(monkeypatch, calls)

    _silent.apply_silent_defaults()
    _silent.apply_silent_defaults()
    await discord.abc.Messageable.send(object(), "hi")

    assert calls == [{"silent": True}]


async def test_webhook_and_interaction_response_default_to_silent(monkeypatch):
    _reset(monkeypatch)
    webhook_calls = []
    interaction_calls = []

    async def fake_webhook_send(self, *args, **kwargs):
        webhook_calls.append(kwargs)

    async def fake_response_send(self, *args, **kwargs):
        interaction_calls.append(kwargs)

    monkeypatch.setattr(discord.Webhook, "send", fake_webhook_send)
    monkeypatch.setattr(discord.InteractionResponse, "send_message", fake_response_send)

    _silent.apply_silent_defaults()
    await discord.Webhook.send(Mock(spec=discord.Webhook), "hi")
    await discord.InteractionResponse.send_message(Mock(spec=discord.InteractionResponse), "hi")

    assert webhook_calls == [{"silent": True}]
    assert interaction_calls == [{"silent": True}]
