import apiClient from './client'

interface AnomalyBase {
  target_month: string
}

export interface CategoryGMVDropAnomaly extends AnomalyBase {
  anomaly_type: 'category_gmv_drop'
  category: string
  actual_gmv: string
  baseline_gmv: string
  drop_rate: string
  threshold: string
}

export interface OrderCountSpikeAnomaly extends AnomalyBase {
  anomaly_type: 'order_count_spike'
  actual_count: number
  baseline_count: number
  growth_rate: string
  threshold: string
}

export interface RegionGMVConcentrationAnomaly extends AnomalyBase {
  anomaly_type: 'region_gmv_concentration'
  region: string
  actual_share: string
  baseline_share: string
  share_increase: string
  threshold: string
  increase_threshold: string
}

export interface OverallGMVDropAnomaly extends AnomalyBase {
  anomaly_type: 'overall_gmv_drop'
  actual_gmv: string
  baseline_gmv: string
  drop_rate: string
  threshold: string
}

export interface AbnormalOrderAmountAnomaly extends AnomalyBase {
  anomaly_type: 'abnormal_order_amount'
  order_id: string
  product_id: string
  order_amount: string
  product_price: string
  amount_ratio: string
  threshold: string
}

export type Anomaly =
  | CategoryGMVDropAnomaly
  | OrderCountSpikeAnomaly
  | RegionGMVConcentrationAnomaly
  | OverallGMVDropAnomaly
  | AbnormalOrderAmountAnomaly

/** 获取全部业务异常检测结果。 */
export async function getAnomalies(): Promise<Anomaly[]> {
  const response = await apiClient.get<Anomaly[]>('/anomalies')
  return response.data
}
