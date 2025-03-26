from core.plugin import PluginManager

class Agent:
    
    def __init__(self, pm: PluginManager):
        self.pm = pm

    
    def run(self, problem: dict):        
        
        role = problem.get("role")
        data = problem.get("data")

        if (role is None or data is None):
            return 
        
        self.pm.run(**{f"{role}": f"hello : {data}"})


