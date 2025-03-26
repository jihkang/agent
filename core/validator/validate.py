from typing import TypeVar


validType = set(["text", "function_call", "data"])


# will be change to db
def registType(validType: str) -> bool:
    validType.add(validType)
    return True


# valid check
def isValid(type: str) -> bool:
    return type in validType
    

T = TypeVar("T")