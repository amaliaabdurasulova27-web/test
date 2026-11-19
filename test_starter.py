
import asyncio
import unittest
from decimal import Decimal

from starter import recommend_price


class RecommendPriceTests(unittest.IsolatedAsyncioTestCase):

    async def test_normal_calculation(self):
        """Проверяем обычный расчёт из задания."""

        async def fetch():
            return {
                "status": "success",
                "offers": [
                    {
                        "seller": "myshop",
                        "price": Decimal("4300.00"),
                        "delivery_days": 2,
                    },
                    {
                        "seller": "PARTS",
                        "price": Decimal("4800.00"),
                        "delivery_days": 3,
                    },
                    {
                        "seller": "SLOW",
                        "price": Decimal("4700.00"),
                        "delivery_days": 8,
                    },
                ],
            }

        result = await recommend_price(
            fetch,
            Decimal("4900.00"),
            Decimal("4500.00"),
        )

        self.assertEqual(result["price"], Decimal("4728.00"))
        self.assertEqual(result["decision"], "APPLY")

    async def test_timeout_returns_hold(self):
        """При тайм-ауте текущая цена не изменяется."""

        async def fetch():
            await asyncio.sleep(1)

        result = await recommend_price(
            fetch,
            Decimal("4900.00"),
            Decimal("4500.00"),
            timeout_s=0.01,
        )

        self.assertEqual(result["price"], Decimal("4900.00"))
        self.assertEqual(result["decision"], "HOLD")

    async def test_filtering_and_empty_offers(self):
        """MYSHOP и неизвестная доставка исключаются."""

        async def fetch():
            return {
                "status": "success",
                "offers": [
                    {
                        "seller": " MyShop ",
                        "price": Decimal("100.00"),
                        "delivery_days": 1,
                    },
                    {
                        "seller": "PARTS",
                        "price": Decimal("200.00"),
                        "delivery_days": None,
                    },
                ],
            }

        result = await recommend_price(
            fetch,
            Decimal("400.00"),
            Decimal("450.00"),
        )

        self.assertEqual(result["price"], Decimal("400.00"))
        self.assertEqual(result["decision"], "HOLD")

    async def test_partial_status_returns_hold(self):
        """Неполные данные не должны менять цену."""

        async def fetch():
            return {
                "status": "partial",
                "offers": [
                    {
                        "seller": "PARTS",
                        "price": Decimal("4000.00"),
                        "delivery_days": 2,
                    }
                ],
            }

        result = await recommend_price(
            fetch,
            Decimal("4900.00"),
            Decimal("4500.00"),
        )

        self.assertEqual(result["price"], Decimal("4900.00"))
        self.assertEqual(result["decision"], "HOLD")

    async def test_rounding_and_deviation_threshold(self):
        """Проверяем ROUND_DOWN, ровно 30% и превышение 30%."""

        async def fetch_exact():
            return {
                "status": "success",
                "offers": [
                    {
                        "seller": "PARTS",
                        "price": Decimal("131.98"),
                        "delivery_days": 2,
                    }
                ],
            }

        exact = await recommend_price(
            fetch_exact,
            Decimal("100.00"),
            Decimal("1.00"),
        )

        self.assertEqual(exact["price"], Decimal("130.00"))
        self.assertEqual(exact["decision"], "APPLY")

        async def fetch_over():
            return {
                "status": "success",
                "offers": [
                    {
                        "seller": "PARTS",
                        "price": Decimal("131.99"),
                        "delivery_days": 2,
                    }
                ],
            }

        over = await recommend_price(
            fetch_over,
            Decimal("100.00"),
            Decimal("1.00"),
        )

        self.assertEqual(over["price"], Decimal("130.01"))
        self.assertEqual(over["decision"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
