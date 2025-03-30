
from pydantic import BaseModel


class LLMRunner(BaseModel):

    def __init__(self, key=""):
