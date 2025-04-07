from plugin.manager import PluginManager
from plugin.scanner import register_scan_directory

if __name__ == "__main__":
    register_scan_directory("plugins")
    
    plugin_name = "Test Method"

    user_input = {
        "content": "OpenAI는 다양한 언어 모델을 제공하며, 자연어 처리 분야에 큰 영향을 주고 있다."
    }

    manager = PluginManager()
    try:
        result = manager.run(plugin_name, user_input)
        print(f"[{plugin_name}] 결과:\n{result}")
    except Exception as e:
        print(f"에러 발생: {e}")