
import apiClient from './client'

export type DatasetTable = 'users' | 'products' | 'orders'

export interface TableCounts {
  users: number
  products: number
  orders: number
}

export interface ColumnSchema {
  field: string
  type: string
  primary_key: boolean
  nullable: boolean
}

export interface TableDetail {
  schema: ColumnSchema[]
  null_counts: Record<string, number>
}

export interface IntegritySummary {
  orphan_user_orders: number
  orphan_product_orders: number
}

export interface ImportHistoryItem {
  id: number
  file_name: string
  dataset_type: DatasetTable
  total_rows: number
  imported_rows: number
  skipped_rows: number
  failed_rows: number
  status: string
  created_at: string
}

export interface DataInspectionResponse {
  table_counts: TableCounts
  table_details: Partial<Record<DatasetTable, TableDetail>>
  integrity: IntegritySummary
  import_history: ImportHistoryItem[]
}

/**
 * 获取业务数据质量概览。
 * 不传 tableName 时检查全部业务表。
 */
export async function getDataInspection(
  tableName?: DatasetTable,
): Promise<DataInspectionResponse> {
  const response = await apiClient.get<DataInspectionResponse>(
    '/data-inspection',
    {
      params: tableName ? { table_name: tableName } : undefined,
    },
  )

  return response.data
}
