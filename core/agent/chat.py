from core import Plugin


class Agent(Plugin):
    """ Plugin """
    def __init__(self):
        """ initalize """
        pass

    def run(self, data):
        print("Simple chat agent")
        print(data)

