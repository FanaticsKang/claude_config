import json
from pathlib import Path
from typing import Dict, Any, Optional


class DataProcessor:
    """示例数据处理器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.processed_count = 0

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据，返回处理结果

        Args:
            data: 输入数据字典

        Returns:
            处理后的数据字典
        """
        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")

        result = {
            "processed_items": [],
            "total_count": 0,
            "timestamp": None
        }

        for key, value in data.items():
            if isinstance(value, (int, float)):
                result["processed_items"].append({
                    "key": key,
                    "value": value,
                    "doubled": value * 2
                })
                result["total_count"] += 1

        self.processed_count += result["total_count"]
        return result

    def load_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件加载数据"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据格式"""
        if not isinstance(data, dict):
            return False

        required_fields = self.config.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                return False

        return True
