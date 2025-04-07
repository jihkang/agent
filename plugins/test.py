from typing import Any, Dict
from plugin.base import BaseAgent

class Test(BaseAgent):
    description = "테스트 에이전트"
    version = "1.1"

    @staticmethod
    def plugin_name():
        return f"Test Method"
    
    
    def run(self, data: Dict[str, Any]) -> Any:
        print("run test")