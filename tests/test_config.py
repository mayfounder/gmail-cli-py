"""Minimal config tests."""

import json

import gmail_cli_py.config as cfg


def test_add_and_delete_account(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "home_dir", lambda: tmp_path)
    monkeypatch.setattr(cfg, "config_path", lambda: tmp_path / "config.json")
    monkeypatch.setattr(cfg, "token_dir", lambda: tmp_path / "tokens")

    assert cfg.add_account("a@example.com") is True
    assert cfg.add_account("a@example.com") is False
    assert cfg.get_accounts() == ["a@example.com"]

    assert cfg.delete_account("missing@example.com") is False
    assert cfg.delete_account("a@example.com") is True
    assert cfg.get_accounts() == []


def test_set_oauth_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "home_dir", lambda: tmp_path)
    monkeypatch.setattr(cfg, "config_path", lambda: tmp_path / "config.json")

    cfg.set_oauth_credentials("id-1", "secret-1")
    data = json.loads((tmp_path / "config.json").read_text())
    assert data["id"] == "id-1"
    assert data["secret"] == "secret-1"
