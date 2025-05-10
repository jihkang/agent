import asyncio
import importlib
from collections import OrderedDict
from typing import Any, List, Tuple
from agent.selector.base import Agent
from plugin.registry import PLUGIN_REGISTRY
from plugin.scanner import register_scan_directory
from scheme.mcp import MCPRequest
from utils.util import get_description_from_class_path
from .base import BaseAgent


class PluginManager:
    """
        Agent를 동적으로 불러와 실행하는 매니저 클래스
    """

    def __init__(self, plugin: str = "plugin", maximum_load = 10):
        self._plugin_package = plugin
        self._loaded_plugins: OrderedDict[str, BaseAgent] = OrderedDict()
        self._maximum_tools = maximum_load
        register_scan_directory("plugins")

    def import_class_from_path(self, path: str) -> type[BaseAgent]:
        """
        'plugins 객체를 동적 로딩' → 실제 클래스 객체 반환
        """    
        module_path, class_name = path.rsplit(".", 1)
        module = importlib.import_module(module_path)    
        cls = getattr(module, class_name)
    
        return cls

    def load_plugin(self, name: str) -> BaseAgent:
        if name in self._loaded_plugins.keys():
            # 최근 사용으로 순서 갱신
            self._loaded_plugins.move_to_end(name)
            return self._loaded_plugins[name]
        
        if name not in PLUGIN_REGISTRY:
            raise ValueError(f"[PluginManager] '{name}' 플러그인은 등록되어 있지 않습니다.")

        cls_path = PLUGIN_REGISTRY[name]
        agent = self.import_class_from_path(cls_path)
    
        if len(self._loaded_plugins) >= self._maximum_tools:
            removed_name, _ = self._loaded_plugins.popitem(last=False)
            print(f"[PluginManager] unload for cached data '{removed_name}'")
            register_scan_directory("plugins")
        
        instance = agent()
        self._loaded_plugins[name] = instance
        return instance

    async def run(self, name: str, request) -> MCPRequest[Any] | MCPRequest[Any]:
        """
        지정된 플러그인을 실행하여 결과 반환
        """
        
        plugin = self.load_plugin(name)
        
        return await plugin.run(request)

    def list_loaded(self) -> List[str]:
        """
        현재 로딩된 플러그인 목록 반환
        """
        return list(self._loaded_plugins.keys())

    def list_registry(self) -> List[str]:
        return [name for name in PLUGIN_REGISTRY.keys()]
    
    def pair_registry_execute_info(self) -> List[str]:
        return [f"{name} - {get_description_from_class_path(PLUGIN_REGISTRY[name])}" if get_description_from_class_path(PLUGIN_REGISTRY[name]) else "" for name in PLUGIN_REGISTRY.keys()]
    
    
    def unload(self, name: str) -> None:
        """
        특정 플러그인 메모리에서 언로드
        """

        if name in self._loaded_plugins:
            del self._loaded_plugins[name]

        print(f"[PluginManager] deleted '{name}' from cache")

