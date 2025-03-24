from core.plugin import PluginManager

if __name__ == "__main__":
    print("run")
    pm = PluginManager()


    for f in pm.showAll():
        pm.run(**{f"{f}":f"hello : {f}"})