from dataclasses import dataclass, field
from typing import List, Dict, Optional, TypedDict

_ALLOWED_ROLES = {"user", "system", "admin"}


@dataclass
class Headers:
    content_type: str = "application/json"

    def to_dict(self) -> Dict[str, str]:
        return {"Content-Type": self.content_type}


@dataclass
class Params:
    key: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key} if self.key is not None else {}


@dataclass
class ContentPart:
    text: str

    def to_dict(self) -> Dict[str, object]:
        return {"text": self.text}


@dataclass
class Content:
    role: str
    parts: List[ContentPart] = field(default_factory=list)

    def __post_init__(self):
        if self.role not in _ALLOWED_ROLES:
            raise ValueError(f"role must be one of {_ALLOWED_ROLES}: got '{self.role}'")

    def to_dict(self) -> Dict[str, object]:
        return {"role": self.role, "parts": [p.to_dict() for p in self.parts]}


class HttpArgs(TypedDict):
    headers: Dict[str, str]
    params: Dict[str, str]
    json: Dict[str, List[Dict[str, object]]]


@dataclass
class ApiRequest:
    headers: Headers = field(default_factory=Headers)
    params: Params = field(default_factory=Params)
    contents: List[Content] = field(default_factory=list)

    def to_body(self) -> Dict[str, List[Dict[str, object]]]:
        return {"contents": [c.to_dict() for c in self.contents]}

    def to_http(self) -> HttpArgs:
        """
        반환 예:
        {
          "headers": {"Content-Type": "application/json"},
          "params": {"key": "API_KEY"} or {},
          "json": {"contents": [...]}
        }
        """
        return {
            "headers": self.headers.to_dict(),
            "params": self.params.to_dict(),
            "json": self.to_body(),
        }


@dataclass
class ApiResponse:
    texts: List[str]

    @classmethod
    def from_json(cls, data: Dict[str, object]) -> "ApiResponse":
        content_texts: List[str] = []
        for candidate in data.get("candidates", []):
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    content_texts.append(part["text"])
        return cls(texts=content_texts)