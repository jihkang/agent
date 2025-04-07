import os
import importlib.util
from plugin.base import BaseAgent
from plugin.registry import register_plugin


def register_scan_directory(path: str):
    package_prefix: str = path
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)
                module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                full_module_path = f"{package_prefix}.{module_path}"

                try:
                    module = importlib.import_module(full_module_path)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseAgent)
                            and attr is not BaseAgent
                            and hasattr(attr, "plugin_name")
                        ):
                            name = attr.plugin_name()
                            class_path = f"{module.__name__}.{attr.__name__}"
                            register_plugin(name, class_path)

                except Exception as e:
                    print(f"[AutoScan] {full_module_path} 로딩 실패: {e}")