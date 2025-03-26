from core.plugin import PluginManager
from core.agent import Agent

if __name__ == "__main__":
    print("run")
    pm = PluginManager()

    agent = Agent(pm)
    agent.run({"role": "ChatAgent", "data" : "hello my name is jiho kang what are you doing"})