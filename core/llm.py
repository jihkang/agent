
from pydantic import BaseModel


class LLMModel(BaseModel):
    key: str


class LLMRunner(BaseModel):

    def __init__(self, ):
        """ initalize """