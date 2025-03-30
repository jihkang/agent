import os

import importlib.util
import inspect
from abc import ABC, abstractmethod


class Plugin(ABC):
    @abstractmethod
    def run(self, data):
        pass


class PluginManager:
    """ Plugin """

    def __init__(self, plugin_dir:str = "core/agent"):
        """ initalize """

        self.tools = {}
        self.plugin_dir = os.path.join(os.getcwd(), plugin_dir)
        self.startServer = False
        self.loadPlugs()


    def can_handle(self, name:str) -> bool:
        return name in self.tools
    
    
    def loadPlugs(self) -> None:
        """ load plugins for use """
        
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            return
        
        print(os.listdir(self.plugin_dir))
        for f in os.listdir(self.plugin_dir):
            if f.endswith(".py") and not f.endswith("__init__.py"):
                plugin_path = os.path.join(self.plugin_dir, f)
                self.loadPlug(plugin_path)


    def loadPlug(self, filePath: str) -> None:
        """ load plug with filePath """

        module_name = os.path.splitext(os.path.basename(filePath))[0]
        spec = importlib.util.spec_from_file_location(module_name, filePath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    
        # find all clas in module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj is not Plugin:
                self.addTool(**{name: obj()})


    def addTool(self, **kwargs) -> None:
        """ add Tools for use """
            
        for name, tool in kwargs.items():
            if name in self.tools:
                raise ValueError(f"도구 '{name}'은(는) 이미 존재합니다")
            if not callable(tool.run) or not hasattr(tool, "run"):
                raise TypeError(f"도구 '{name}'은(는) 호출 가능한 객체여야 합니다")
        
        # update tool lists
        self.tools |= kwargs


    def removeTool(self, *args) -> None:
        """ remove tools """

        for name in args:
            if name not in self.tools:
                raise ValueError(f"도구 '{name}'이(가) 존재하지 않습니다")
            
            del self.tools[name]
            # self.mcp.unregist(name)
        

    def showAll(self) -> list[str]:
        return self.tools.keys()


    def run(self, **kwargs) -> None:
        if self.startServer is False:
            # self.mcp.run()
            self.startServer = True

        for name, data in kwargs.items():
            self.tools[name].run(data)
