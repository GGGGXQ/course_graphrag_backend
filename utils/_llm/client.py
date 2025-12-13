from typing import Any, Optional, Dict, List

from zai import ZhipuAiClient
from openai import OpenAI
from .base import BaseLLM, BaseEmb


class ZhipuLLM(BaseLLM):
    """Implementation of the BaseLLM interface using zhipuai."""
    def __init__(
            self, 
            api_key: str,
            model_name, 
            model_params = None, 
            *kwargs
        ):
        super().__init__(model_name, model_params, *kwargs)
        self.client = ZhipuAiClient(api_key=api_key)
    
    def predict(self, input: str) -> str:
        """Sends a text input to the zhipuai model and retrieves a response.

        Args:
            input (str): Text sent to the zhipuai model

        Returns:
            str: The response from the zhipuai model.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": input}],
        )
        return response.choices[0].message.content

class DashscopeEmb(BaseEmb):
    """Implementation of the BaseEmb interface using zhipuai."""
    def __init__(self, model_name: str, base_url: str, api_key: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)
        self.client = OpenAI(base_url=base_url, api_key=api_key)
    
    def get_emb(self, input: str) -> list[float]:
        emb = self.client.embeddings.create(
            model=self.model_name,
            input=input
        )
        return emb.data[0].embedding
