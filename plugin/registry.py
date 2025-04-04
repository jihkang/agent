from typing import Type, Dict
from plugin.base import BaseAgent


PLUGIN_REGISTRY: Dict[str, Type[BaseAgent]] = {}

def register_plugin(cls: Type[BaseAgent]) -> Type[BaseAgent]:
    name = cls.plugin_name()
    if name in PLUGIN_REGISTRY:
        raise ValueError(f"[Registry] '{name}'는 이미 등록된 플러그인입니다.")
    
    PLUGIN_REGISTRY[name] = cls
    return cls
