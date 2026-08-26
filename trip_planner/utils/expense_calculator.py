# utils/expense_calculator.py
class Calculator:
    @staticmethod
    def multiply(a, b) -> float:
        """
        Multiply two numbers (coerces numeric strings safely).
        """
        return float(a) * float(b)

    @staticmethod
    def calculate_total(*x) -> float:
        return sum(float(v) for v in x)

    @staticmethod
    def calculate_daily_budget(total, days) -> float:
        total, days = float(total), float(days)
        return total / days if days > 0 else 0