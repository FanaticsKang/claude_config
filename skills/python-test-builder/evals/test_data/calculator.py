from typing import Union, List
import math

Number = Union[int, float]


class Calculator:
    """计算器类 - 有丰富的边界条件"""

    PRECISION = 0.0001

    @staticmethod
    def divide(a: Number, b: Number) -> Number:
        """除法 - 需要处理除零"""
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

    @staticmethod
    def sqrt(x: Number) -> Number:
        """平方根 - 需要处理负数"""
        if x < 0:
            raise ValueError("Cannot compute square root of negative number")
        return math.sqrt(x)

    @staticmethod
    def factorial(n: int) -> int:
        """阶乘 - 需要处理负数和极大数"""
        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")
        if n > 20:  # 防止溢出
            raise OverflowError("Number too large for factorial")
        return math.factorial(n)

    @staticmethod
    def average(numbers: List[Number]) -> float:
        """平均值 - 需要处理空列表"""
        if not numbers:
            raise ValueError("Cannot compute average of empty list")
        return sum(numbers) / len(numbers)

    @staticmethod
    def parse_number(s: str) -> Number:
        """解析数字 - 需要处理各种格式"""
        s = s.strip()
        if not s:
            raise ValueError("Empty string")

        # 处理科学计数法
        if 'e' in s.lower():
            return float(s)

        # 处理整数
        if '.' not in s:
            return int(s)

        return float(s)

    @classmethod
    def compare_float(cls, a: float, b: float) -> bool:
        """比较浮点数 - 处理精度问题"""
        return abs(a - b) < cls.PRECISION
