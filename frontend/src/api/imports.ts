import apiClient from './client'
import type { DatasetTable } from './dataInspection'

export type ImportStatus =
  | 'success'
  | 'partial'
  | 'failed'
  | 'processing'
  | 'duplicate'

export interface ImportRecord {
  id: number
  file_name: string
  dataset_type: DatasetTable
  total_rows: number
  imported_rows: number
  skipped_rows: number
  failed_rows: number
  status: ImportStatus
  created_at: string
}

export interface ImportError {
  row_number: number
  field_name: string | null
  error_type: string
  error_message: string
  raw_value: string | null
}

export interface ImportDetailError extends ImportError {
  id: number
}

export interface ImportResult {
  import_record_id: number
  file_name: string
  dataset_type: DatasetTable
  total_rows: number
  imported_rows: number
  skipped_rows: number
  failed_rows: number
  status: ImportStatus
  errors: ImportError[]
}

export interface ImportHistoryResponse {
  items: ImportRecord[]
  total: number
  limit: number
  offset: number
}

export interface ImportDetail extends ImportRecord {
  errors: ImportDetailError[]
}

export async function uploadImport(
  file: File,
  datasetType: DatasetTable,
): Promise<ImportResult> {
  const formData = new FormData()
  formData.append('dataset_type', datasetType)
  formData.append('file', file)

  const response = await apiClient.post<ImportResult>(
    '/imports',
    formData,
    {
      headers: {
        'Content-Type': undefined,
      },
    },
  )

  return response.data
}

export async function getImportHistory(
  limit = 20,
  offset = 0,
): Promise<ImportHistoryResponse> {
  const response = await apiClient.get<ImportHistoryResponse>('/imports', {
    params: { limit, offset },
  })

  return response.data
}

export async function getImportDetail(
  importRecordId: number,
): Promise<ImportDetail> {
  const response = await apiClient.get<ImportDetail>(
    `/imports/${importRecordId}`,
  )

  return response.data
}
