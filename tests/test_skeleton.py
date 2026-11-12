import importlib

from collector import config

MODULES = [
    "collector.http",
    "collector.fetch",
    "collector.weather",
    "collector.detect",
    "collector.storage",
    "collector.notify",
    "api.main",
    "api.models",
    "api.auth",
    "demo.receiver",
]


def test_every_module_imports():
    for name in MODULES:
        importlib.import_module(name)


def test_data_dir_is_inside_the_repo():
    assert config.DATA_DIR.parent == config.REPO_ROOT
