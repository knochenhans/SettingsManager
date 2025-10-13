import json
import os
import shutil
import tempfile

import pytest

from SettingsManager.settings_manager import SettingsManager


@pytest.fixture
def temp_config_dir(monkeypatch: pytest.MonkeyPatch):
    # Patch user_config_dir to use a temp directory
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr("appdirs.user_config_dir", lambda: temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_set_and_get(temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    sm.set("foo", "bar")
    assert sm.get("foo") == "bar"
    assert sm.get("missing", "default") == "default"


def test_save_and_load(temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    sm.set("a", 1)
    sm.set("b", [1, 2, 3])
    sm.save()
    # Clear and reload
    sm2 = SettingsManager("test", "TestApp")
    sm2.load()
    assert sm2.get("a") == 1
    assert sm2.get("b") == [1, 2, 3]


def test_to_dict_and_from_dict(temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    sm.set("x", 42)
    d = sm.to_dict()
    sm2 = SettingsManager.from_dict(d)
    assert sm2.to_dict() == d


def test_eq(temp_config_dir: str):
    sm1 = SettingsManager("test", "TestApp")
    sm2 = SettingsManager("test", "TestApp")
    sm1.set("foo", "bar")
    sm2.set("foo", "bar")
    assert sm1 == sm2
    sm2.set("foo", "baz")
    assert sm1 != sm2


def test_load_file_not_found(monkeypatch: pytest.MonkeyPatch, temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    # Remove config file if exists
    if os.path.exists(sm.user_config_path):
        os.remove(sm.user_config_path)
    sm.set("foo", "bar")
    sm.settings.clear()
    sm.load()
    # Should not raise, settings remain empty
    assert sm.get("foo") is None


def test_load_invalid_json(temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    os.makedirs(os.path.dirname(sm.user_config_path), exist_ok=True)
    with open(sm.user_config_path, "w", encoding="utf-8") as f:
        f.write("{invalid json}")
    sm.load()
    # Should not raise, settings remain empty
    assert sm.settings == {}


def test_save_creates_directory(temp_config_dir: str):
    sm = SettingsManager("test", "TestApp")
    # Remove config dir
    if os.path.exists(sm.config_dir):
        shutil.rmtree(sm.config_dir)
    sm.set("foo", "bar")
    sm.save()
    assert os.path.exists(sm.user_config_path)
    with open(sm.user_config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["foo"] == "bar"
