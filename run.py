from core.plugin import PluginManager

if __name__ == "__main__":
    print("run")
    pm = PluginManager()
    print(pm.showAll())

    pm.run(WeatherAgent="hello")