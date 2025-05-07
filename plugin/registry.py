from typing import Dict
from plugin.base import BaseAgent


PLUGIN_REGISTRY: Dict[str, str] = {}

def register_plugin(name: str,  cls_path: str) -> None:
    if name in PLUGIN_REGISTRY:
        raise ValueError(f"[Registry] '{name}'은 이미 등록되어 있습니다.")

    PLUGIN_REGISTRY[name] = cls_path
