class PluginManager:
    """ Plugin """

    def __init__(self):
        """ initalize """

        self.tools = {}


    def addTool(self, **kwargs):
        """ add Tools for use """
            
        for name, tool in kwargs.items():
            if name in self.tools:
                raise ValueError(f"도구 '{name}'은(는) 이미 존재합니다")
            if not callable(tool.run) or not hasattr(tool, "run"):
                raise TypeError(f"도구 '{name}'은(는) 호출 가능한 객체여야 합니다")

        self.tools |= kwargs


    def removeTool(self, *args):
        """ remove tools """
        for name in args:
            if name not in self.tools:
                raise ValueError(f"도구 '{name}'이(가) 존재하지 않습니다")
            
            del self.tools[name]

    def run(self, name, data):

        self.tools[name].run(data)