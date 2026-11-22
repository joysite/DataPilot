import apiClient from './client'

export interface AnalyticsDateRange {
  start_date?: string
  end_date?: string
}

export interface OrderSummary {
  gmv: string
  valid_order_count: number
  average_order_value: string
  pending_order_count: number
  cancelled_order_count: number
  total_order_count: number
  cancellation_rate: number
}

export interface MonthlyGMV {
  month: string
  gmv: string
}

export interface CategoryComparison {
  category: string
  gmv: string
  valid_order_count: number
  average_order_value: string
}

/** 获取订单核心指标。 */
export async function getOrderSummary(dateRange?: AnalyticsDateRange): Promise<OrderSummary> {
  const response = await apiClient.get<OrderSummary>('/analytics/summary', {
    params: dateRange,
  })

  return response.data
}

/** 获取月度 GMV 趋势。 */
export async function getGMVTrend(dateRange?: AnalyticsDateRange): Promise<MonthlyGMV[]> {
  const response = await apiClient.get<MonthlyGMV[]>('/analytics/trend', {
    params: dateRange,
  })

  return response.data
}

/** 获取品类业务对比。 */
export async function getCategoryComparison(
  dateRange?: AnalyticsDateRange,
): Promise<CategoryComparison[]> {
  const response = await apiClient.get<CategoryComparison[]>('/analytics/categories', {
    params: dateRange,
  })

  return response.data
}
