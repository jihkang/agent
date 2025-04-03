import torch
from typing import List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from core.llm.base import BaseLLM
from core.mcp import MCPMessage, MCPResponse


class LocalLLM(BaseLLM):
    def __init__(self, model_path: str):
        self.model_path = model_path
        # Mac M1/M2 GPU 지원을 위한 디바이스 설정
        self.device = self._get_device()
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
    
    def _get_device(self) -> str:
        """사용 가능한 최적의 디바이스 선택"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"  # Mac M1/M2 GPU
        return "cpu"
    
    async def load_model(self):
        """로컬 모델 로드"""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # 디바이스별 적절한 dtype 설정
        if self.device == "cuda":
            dtype = torch.float16
        elif self.device == "mps":
            dtype = torch.float32  # MPS는 현재 float16을 완전히 지원하지 않음
        else:
            dtype = torch.float32
            
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=dtype,
            device_map="auto"
        ).to(self.device) 

    async def generate(self, messages: List[MCPMessage]) -> MCPResponse:
        if not self.model or not self.tokenizer:
            await self.load_model()

        prompt = self._convert_messages_to_prompt(messages)
        
        # 토크나이즈 및 생성
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return MCPResponse(
            type="text",
            content=response
        )
    
    def _convert_messages_to_prompt(self, messages: List[MCPMessage]) -> str:
        """메시지를 프롬프트로 변환"""
        prompt = ""
        for msg in messages:
            if msg.role == "user":
                prompt += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n"
            elif msg.role == "system":
                prompt += f"System: {msg.content}\n"
        return prompt
        