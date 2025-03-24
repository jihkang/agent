from abc import ABC

class mcp:
    """ mcp protocol """

    def __init__(self):
        self.tools = {}



    def register(self, name: str, func: function):
        """ register """
        
        self.tools[name] = func
        


    def unregister(self, name):
        """ unregister """

        del self.tools[name]

