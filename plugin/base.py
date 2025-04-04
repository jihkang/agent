from abc import ABC, abstractmethod, classmethod


class BaseAgent(ABC):

    @classmethod
    @abstractmethod
    def plugin_name(cls):
        pass


    @abstractmethod
    def run(self):
        pass