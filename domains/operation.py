from pydantic import BaseModel, Field
from typing import Optional, Dict


class OperationResult(BaseModel):
    """操作结果"""

    success: bool = Field(..., title="操作是否成功")
    message: str = Field(..., title="操作结果消息")
    meta: Optional[Dict] = Field(None, title="操作结果元数据")
