from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseLLM(ABC):
    """
    大模型接口抽象类

    Args:
        model_name(str): 模型名称
        model_params(Optional[dict[str, Anty]]):当文本发送到模型时传递的附加参数。默认为None。
        *kwargs(Any): 在类初始化时传递给模型的参数。默认为 None。
    """
    def __init__(
            self,
            model_name: str,
            model_params: Optional[dict[str, Any]] = None,
            *kwargs: Any,
    ):
        self.model_name = model_name
        self.model_params = model_params or {}
    
    @abstractmethod
    def predict(self, input: str) -> str:
        """
        将文本发送给模型进行获得响应
        Args:
            input (str): Text sent to the LLM

        Returns:
            str: The response from the LLM.
        """
        pass

class BaseEmb(ABC):
    def __init__(
            self,
            model_name: str,
            model_params: Optional[dict[str, Any]] = None,
            *kwargs: Any,
    ):
        self.model_name = model_name
        self.model_params = model_params or {}
    
    @abstractmethod
    def get_emb(self, input: str) -> list[float]:
        """Sends a text input to the embedding model and retrieves the embedding.

        Args:
            input (str): Text sent to the embedding model

        Returns:
            List[float]: The embedding vector from the model.
        """
        pass