"""异常检测业务服务。"""

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.anomaly_repository import AnomalyRepository
from app.schemas.anomaly import AnomalyResultUnion


class AnomalyService:
    """业务异常检测服务。"""

    BASELINE_MONTHS = 3
    CATEGORY_GMV_DROP_THRESHOLD = Decimal("0.30")

    ORDER_COUNT_SPIKE_THRESHOLD = Decimal("0.50")

    REGION_GMV_SHARE_THRESHOLD = Decimal("0.20")
    REGION_GMV_SHARE_INCREASE_THRESHOLD = Decimal("0.10")

    OVERALL_GMV_DROP_THRESHOLD = Decimal("0.30")

    ORDER_AMOUNT_RATIO_THRESHOLD = Decimal("6")

    @staticmethod
    def _get_previous_months(month: str) -> list[str]:
        """获取目标月份之前连续三个月，按时间升序排列。"""

        year, month_number = map(int, month.split("-"))

        previous_months = []

        for offset in range(1, 4):
            total_months = year * 12 + month_number - 1 - offset
            previous_year, previous_month = divmod(total_months, 12)

            previous_months.append(f"{previous_year:04d}-{previous_month + 1:02d}")

        return list(reversed(previous_months))

    async def _detect_category_gmv_drop(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """检测商品品类月度 GMV 异常下降。"""

        rows = await AnomalyRepository.get_monthly_category_gmv(session)

        gmv_map = {(row["month"], row["category"]): row["gmv"] for row in rows}

        months = sorted({row["month"] for row in rows})
        categories = {row["category"] for row in rows}

        anomalies = []

        for target_month in months:
            for category in categories:
                actual_gmv = gmv_map.get(
                    (target_month, category),
                    Decimal("0.00"),
                )

                baseline_months = self._get_previous_months(target_month)

                baseline_values = [
                    gmv_map[(month, category)]
                    for month in baseline_months
                    if (month, category) in gmv_map
                ]

                if len(baseline_values) != self.BASELINE_MONTHS:
                    continue

                baseline_gmv = sum(baseline_values, Decimal("0.00")) / Decimal(
                    self.BASELINE_MONTHS
                )

                if baseline_gmv <= 0:
                    continue

                drop_rate = (baseline_gmv - actual_gmv) / baseline_gmv

                if drop_rate < self.CATEGORY_GMV_DROP_THRESHOLD:
                    continue

                anomalies.append(
                    {
                        "anomaly_type": "category_gmv_drop",
                        "target_month": target_month,
                        "category": category,
                        "actual_gmv": actual_gmv,
                        "baseline_gmv": baseline_gmv,
                        "drop_rate": drop_rate,
                        "threshold": self.CATEGORY_GMV_DROP_THRESHOLD,
                    }
                )

        return anomalies

    async def _detect_order_count_spike(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """检测月度订单量同比异常增长。"""

        rows = await AnomalyRepository.get_monthly_order_counts(session)

        count_map = {row["month"]: row["order_count"] for row in rows}

        anomalies = []

        for row in rows:
            target_month = row["month"]
            actual_count = row["order_count"]

            year, month = target_month.split("-")
            previous_year_month = f"{int(year) - 1:04d}-{month}"

            baseline_count = count_map.get(previous_year_month)

            # 缺少去年同期数据，无法进行同比判断。
            if baseline_count is None or baseline_count <= 0:
                continue

            growth_rate = Decimal(actual_count - baseline_count) / Decimal(
                baseline_count
            )

            if growth_rate < self.ORDER_COUNT_SPIKE_THRESHOLD:
                continue

            anomalies.append(
                {
                    "anomaly_type": "order_count_spike",
                    "target_month": target_month,
                    "actual_count": actual_count,
                    "baseline_count": baseline_count,
                    "growth_rate": growth_rate,
                    "threshold": self.ORDER_COUNT_SPIKE_THRESHOLD,
                }
            )

        return anomalies

    async def _detect_region_gmv_concentration(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """检测地区 GMV 占比异常集中。"""

        rows = await AnomalyRepository.get_monthly_region_gmv(session)

        region_gmv_map = {(row["month"], row["region"]): row["gmv"] for row in rows}

        monthly_gmv_map: dict[str, Decimal] = {}

        for row in rows:
            month = row["month"]
            monthly_gmv_map[month] = (
                monthly_gmv_map.get(month, Decimal("0.00")) + row["gmv"]
            )

        anomalies = []

        for row in rows:
            target_month = row["month"]
            region = row["region"]

            actual_total_gmv = monthly_gmv_map[target_month]

            if actual_total_gmv <= 0:
                continue

            actual_region_gmv = row["gmv"]
            actual_share = actual_region_gmv / actual_total_gmv

            baseline_months = self._get_previous_months(target_month)

            baseline_shares = []
            has_complete_baseline = True

            for month in baseline_months:
                total_gmv = monthly_gmv_map.get(month)

                if total_gmv is None or total_gmv <= 0:
                    has_complete_baseline = False
                    break

                region_gmv = region_gmv_map.get(
                    (month, region),
                    Decimal("0.00"),
                )

                baseline_shares.append(region_gmv / total_gmv)

            if not has_complete_baseline:
                continue

            baseline_share = sum(baseline_shares, Decimal("0")) / Decimal(
                self.BASELINE_MONTHS
            )

            share_increase = actual_share - baseline_share

            if (
                actual_share < self.REGION_GMV_SHARE_THRESHOLD
                or share_increase < self.REGION_GMV_SHARE_INCREASE_THRESHOLD
            ):
                continue

            anomalies.append(
                {
                    "anomaly_type": "region_gmv_concentration",
                    "target_month": target_month,
                    "region": region,
                    "actual_share": actual_share,
                    "baseline_share": baseline_share,
                    "share_increase": share_increase,
                    "threshold": self.REGION_GMV_SHARE_THRESHOLD,
                    "increase_threshold": (self.REGION_GMV_SHARE_INCREASE_THRESHOLD),
                }
            )

        return anomalies

    async def _detect_overall_gmv_drop(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """检测整体月度 GMV 异常下降。"""

        rows = await AnomalyRepository.get_monthly_gmv(session)

        gmv_map = {row["month"]: row["gmv"] for row in rows}

        anomalies = []

        for row in rows:
            target_month = row["month"]
            actual_gmv = row["gmv"]

            baseline_months = self._get_previous_months(target_month)

            baseline_values = [
                gmv_map[month] for month in baseline_months if month in gmv_map
            ]

            if len(baseline_values) != self.BASELINE_MONTHS:
                continue

            baseline_gmv = sum(baseline_values, Decimal("0.00")) / Decimal(
                self.BASELINE_MONTHS
            )

            if baseline_gmv <= 0:
                continue

            drop_rate = (baseline_gmv - actual_gmv) / baseline_gmv

            if drop_rate < self.OVERALL_GMV_DROP_THRESHOLD:
                continue

            anomalies.append(
                {
                    "anomaly_type": "overall_gmv_drop",
                    "target_month": target_month,
                    "actual_gmv": actual_gmv,
                    "baseline_gmv": baseline_gmv,
                    "drop_rate": drop_rate,
                    "threshold": self.OVERALL_GMV_DROP_THRESHOLD,
                }
            )

        return anomalies

    async def _detect_abnormal_order_amount(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """检测订单金额相对商品标价异常的订单。"""

        rows = await AnomalyRepository.get_order_amount_details(session)

        anomalies = []

        for row in rows:
            order_amount = row["order_amount"]
            product_price = row["product_price"]

            if product_price <= 0:
                continue

            amount_ratio = order_amount / product_price

            if amount_ratio < self.ORDER_AMOUNT_RATIO_THRESHOLD:
                continue

            anomalies.append(
                {
                    "anomaly_type": "abnormal_order_amount",
                    "target_month": row["order_time"].strftime("%Y-%m"),
                    "order_id": row["order_id"],
                    "product_id": row["product_id"],
                    "order_amount": order_amount,
                    "product_price": product_price,
                    "amount_ratio": amount_ratio,
                    "threshold": self.ORDER_AMOUNT_RATIO_THRESHOLD,
                }
            )

        return anomalies

    async def detect_anomalies(
        self,
        session: AsyncSession,
    ) -> list[AnomalyResultUnion]:
        """执行全部异常检测并返回结构化结果。"""

        from pydantic import TypeAdapter

        adapter = TypeAdapter(AnomalyResultUnion)

        detectors = [
            self._detect_category_gmv_drop,
            self._detect_order_count_spike,
            self._detect_region_gmv_concentration,
            self._detect_overall_gmv_drop,
            self._detect_abnormal_order_amount,
        ]

        anomalies = []

        for detector in detectors:
            results = await detector(session)

            anomalies.extend(adapter.validate_python(result) for result in results)

        return anomalies
