from plugin import PluginManager
from abc import ABC, abstractmethod

class Plugin(ABC):

    @abstractmethod
    def run(self, data):
        pass


class Agent(Plugin):
    """ Plugin """
    def __init__(self):
        """ initalize """
        pass

    def run(self, data):
        print("Simple chat agent")
        print(data)


class WeatherAgent(Plugin):
    """ Weather plugin test """
    def __init__(self):
        """initalize weather """

    def run(self, data):
        print("simple weather test")
        print("today is sunny")
    

plug = PluginManager()
chat = Agent()
plug.addTool(chatbot=chat)
