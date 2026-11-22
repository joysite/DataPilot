<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getApiErrorMessage } from '../api/client'
import {
  getDataInspection,
  type DataInspectionResponse,
  type DatasetTable,
} from '../api/dataInspection'
import { getImportDetail, uploadImport, type ImportDetail, type ImportResult } from '../api/imports'

const tableOptions: { label: string; value: DatasetTable }[] = [
  { label: '用户表', value: 'users' },
  { label: '商品表', value: 'products' },
  { label: '订单表', value: 'orders' },
]

const activeTable = ref<DatasetTable>('users')
const inspection = ref<DataInspectionResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')

const datasetType = ref<DatasetTable>('users')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const uploadError = ref('')
const uploadResult = ref<ImportResult | null>(null)
const selectedImportDetail = ref<ImportDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

const currentDetail = computed(() => {
  return inspection.value?.table_details[activeTable.value] ?? null
})

const countCards = computed(() => {
  if (!inspection.value) return []

  return [
    { label: '用户数量', value: inspection.value.table_counts.users, icon: '人', type: 'users' },
    {
      label: '商品数量',
      value: inspection.value.table_counts.products,
      icon: '货',
      type: 'products',
    },
    { label: '订单数量', value: inspection.value.table_counts.orders, icon: '单', type: 'orders' },
  ]
})

async function loadInspection() {
  loading.value = true
  errorMessage.value = ''

  try {
    inspection.value = await getDataInspection()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '数据质量信息加载失败，请检查后端服务是否正常。')
    console.error('Failed to load data inspection:', error)
  } finally {
    loading.value = false
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null

  uploadError.value = ''
  uploadResult.value = null
  selectedFile.value = null

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.csv')) {
    uploadError.value = '仅支持 CSV 文件。'
    input.value = ''
    return
  }

  if (file.size > 20 * 1024 * 1024) {
    uploadError.value = '文件大小不能超过 20 MB。'
    input.value = ''
    return
  }

  selectedFile.value = file
}

async function handleUpload() {
  if (!selectedFile.value || uploading.value) return

  uploading.value = true
  uploadError.value = ''
  uploadResult.value = null

  try {
    uploadResult.value = await uploadImport(selectedFile.value, datasetType.value)
    selectedFile.value = null

    if (fileInput.value) {
      fileInput.value.value = ''
    }

    await loadInspection()
  } catch (error) {
    uploadError.value = getApiErrorMessage(error, '数据导入失败，请稍后重试。')
    console.error('Failed to import dataset:', error)
  } finally {
    uploading.value = false
  }
}

async function openImportDetail(importRecordId: number) {
  detailLoading.value = true
  detailError.value = ''
  selectedImportDetail.value = null

  try {
    selectedImportDetail.value = await getImportDetail(importRecordId)
  } catch (error) {
    detailError.value = getApiErrorMessage(error, '导入详情加载失败。')
    console.error('Failed to load import detail:', error)
  } finally {
    detailLoading.value = false
  }
}

function closeImportDetail() {
  selectedImportDetail.value = null
  detailError.value = ''
}

function formatDate(value: string) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString('zh-CN', { hour12: false })
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    success: '成功',
    partial: '部分成功',
    failed: '失败',
    processing: '处理中',
    duplicate: '重复文件',
  }

  return labels[status] ?? status
}

onMounted(loadInspection)
</script>

<template>
  <div class="data-management-page">
    <section class="page-heading">
      <div>
        <span class="eyebrow">DATA MANAGEMENT</span>
        <h1>数据管理</h1>
        <p>查看业务数据规模、字段质量和数据关联完整性。</p>
      </div>

      <button class="refresh-button" :disabled="loading" @click="loadInspection">
        {{ loading ? '刷新中...' : '↻ 刷新数据' }}
      </button>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>数据集导入</h2>
          <span>上传 CSV 文件，将业务数据导入本地数据库（最大 20 MB）</span>
        </div>
      </div>

      <div class="upload-panel">
        <div class="upload-controls">
          <label class="upload-field">
            <span>数据类型</span>
            <select v-model="datasetType" :disabled="uploading">
              <option value="users">用户数据</option>
              <option value="products">商品数据</option>
              <option value="orders">订单数据</option>
            </select>
          </label>

          <div class="upload-field file-field">
            <span>CSV 文件</span>
            <div class="file-picker">
              <button
                type="button"
                class="secondary-button"
                :disabled="uploading"
                @click="openFilePicker"
              >
                选择文件
              </button>
              <span class="file-name">
                {{ selectedFile?.name ?? '尚未选择文件' }}
              </span>
            </div>
            <input
              ref="fileInput"
              class="file-input"
              type="file"
              accept=".csv,text/csv"
              :disabled="uploading"
              @change="handleFileChange"
            />
          </div>

          <button
            type="button"
            class="primary-button"
            :disabled="!selectedFile || uploading"
            @click="handleUpload"
          >
            {{ uploading ? '正在导入...' : '开始导入' }}
          </button>
        </div>

        <p class="upload-hint">请确保 CSV 包含对应数据集的必需字段，重复数据将根据后端规则处理。</p>

        <div v-if="uploadError" class="upload-error" role="alert">
          {{ uploadError }}
        </div>

        <div v-if="uploadResult" class="upload-result">
          <div class="result-heading">
            <strong>导入结果</strong>
            <span class="status-tag" :class="`status-${uploadResult.status}`">
              {{ statusLabel(uploadResult.status) }}
            </span>
          </div>

          <p class="result-filename">{{ uploadResult.file_name }}</p>

          <div class="result-stats">
            <div>
              <span>总行数</span>
              <strong>{{ uploadResult.total_rows }}</strong>
            </div>
            <div>
              <span>成功</span>
              <strong>{{ uploadResult.imported_rows }}</strong>
            </div>
            <div>
              <span>跳过</span>
              <strong>{{ uploadResult.skipped_rows }}</strong>
            </div>
            <div>
              <span>失败</span>
              <strong>{{ uploadResult.failed_rows }}</strong>
            </div>
          </div>

          <div v-if="uploadResult.errors.length" class="result-errors">
            <strong>错误明细（{{ uploadResult.errors.length }} 条）</strong>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>行号</th>
                    <th>字段</th>
                    <th>错误类型</th>
                    <th>错误原因</th>
                    <th>原始值</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(item, index) in uploadResult.errors"
                    :key="`${item.row_number}-${item.field_name ?? ''}-${item.error_type}-${index}`"
                  >
                    <td>{{ item.row_number }}</td>
                    <td>{{ item.field_name ?? '-' }}</td>
                    <td>{{ item.error_type }}</td>
                    <td>{{ item.error_message }}</td>
                    <td>{{ item.raw_value ?? '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="error-message" role="alert">
      {{ errorMessage }}
      <button @click="loadInspection">重试</button>
    </div>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>数据概览</h2>
          <span>当前业务数据集记录数量</span>
        </div>
      </div>

      <div v-if="loading && !inspection" class="loading-state">正在加载数据质量信息...</div>

      <div v-else class="count-grid">
        <article v-for="item in countCards" :key="item.type" class="count-card">
          <div class="count-icon" :class="`${item.type}-icon`">
            {{ item.icon }}
          </div>
          <div>
            <span class="count-label">{{ item.label }}</span>
            <strong class="count-value">{{ item.value.toLocaleString() }}</strong>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>字段质量</h2>
          <span>查看各业务表字段定义及 NULL 数量</span>
        </div>
      </div>

      <div class="quality-panel">
        <div class="table-tabs">
          <button
            v-for="option in tableOptions"
            :key="option.value"
            :class="{ active: activeTable === option.value }"
            @click="activeTable = option.value"
          >
            {{ option.label }}
          </button>
        </div>

        <div v-if="currentDetail" class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>字段名称</th>
                <th>数据类型</th>
                <th>主键</th>
                <th>允许为空</th>
                <th>NULL 数量</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="column in currentDetail.schema" :key="column.field">
                <td class="field-name">{{ column.field }}</td>
                <td>{{ column.type }}</td>
                <td>
                  <span :class="column.primary_key ? 'tag-primary' : 'tag-muted'">
                    {{ column.primary_key ? '是' : '否' }}
                  </span>
                </td>
                <td>{{ column.nullable ? '是' : '否' }}</td>
                <td>
                  <span
                    :class="
                      (currentDetail.null_counts[column.field] ?? 0) > 0
                        ? 'null-warning'
                        : 'null-normal'
                    "
                  >
                    {{ currentDetail.null_counts[column.field] ?? 0 }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-state">
          {{ loading ? '正在加载...' : '暂无字段信息' }}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>关联完整性</h2>
          <span>检查订单是否关联到有效的用户和商品</span>
        </div>
      </div>

      <div v-if="inspection" class="integrity-grid">
        <article class="integrity-card">
          <div>
            <span class="integrity-label">缺失用户关联的订单</span>
            <strong>{{ inspection.integrity.orphan_user_orders }}</strong>
          </div>
          <span
            :class="
              inspection.integrity.orphan_user_orders === 0 ? 'integrity-ok' : 'integrity-warning'
            "
          >
            {{ inspection.integrity.orphan_user_orders === 0 ? '正常' : '需检查' }}
          </span>
        </article>

        <article class="integrity-card">
          <div>
            <span class="integrity-label">缺失商品关联的订单</span>
            <strong>{{ inspection.integrity.orphan_product_orders }}</strong>
          </div>
          <span
            :class="
              inspection.integrity.orphan_product_orders === 0
                ? 'integrity-ok'
                : 'integrity-warning'
            "
          >
            {{ inspection.integrity.orphan_product_orders === 0 ? '正常' : '需检查' }}
          </span>
        </article>
      </div>
      <div v-else class="empty-state">暂无关联完整性数据</div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>最近导入记录</h2>
          <span>最近五次数据导入任务</span>
        </div>
      </div>

      <div class="history-panel">
        <div v-if="inspection?.import_history.length" class="table-wrapper">
          <table class="data-table history-table">
            <thead>
              <tr>
                <th>文件名称</th>
                <th>数据类型</th>
                <th>总行数</th>
                <th>成功</th>
                <th>跳过</th>
                <th>失败</th>
                <th>状态</th>
                <th>导入时间</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in inspection.import_history" :key="record.id">
                <td class="field-name">{{ record.file_name }}</td>
                <td>{{ record.dataset_type }}</td>
                <td>{{ record.total_rows }}</td>
                <td>{{ record.imported_rows }}</td>
                <td>{{ record.skipped_rows }}</td>
                <td>{{ record.failed_rows }}</td>
                <td>
                  <span class="status-tag" :class="`status-${record.status}`">
                    {{ statusLabel(record.status) }}
                  </span>
                </td>
                <td>{{ formatDate(record.created_at) }}</td>
                <td>
                  <button type="button" class="detail-button" @click="openImportDetail(record.id)">
                    查看详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else-if="inspection" class="empty-state">暂无导入记录</div>
        <div v-else class="empty-state">
          {{ loading ? '正在加载...' : '暂无数据' }}
        </div>
      </div>
    </section>

    <section v-if="detailLoading || detailError || selectedImportDetail" class="section">
      <div class="section-heading">
        <div>
          <h2>导入记录详情</h2>
          <span>查看单次导入任务的统计和错误明细</span>
        </div>
        <button type="button" class="secondary-button" @click="closeImportDetail">关闭</button>
      </div>

      <div v-if="detailLoading" class="empty-state">正在加载导入详情...</div>
      <div v-else-if="detailError" class="upload-error" role="alert">
        {{ detailError }}
      </div>
      <div v-else-if="selectedImportDetail" class="upload-panel">
        <div class="result-heading">
          <strong>{{ selectedImportDetail.file_name }}</strong>
          <span class="status-tag" :class="`status-${selectedImportDetail.status}`">
            {{ statusLabel(selectedImportDetail.status) }}
          </span>
        </div>

        <div class="result-stats">
          <div>
            <span>总行数</span>
            <strong>{{ selectedImportDetail.total_rows }}</strong>
          </div>
          <div>
            <span>成功</span>
            <strong>{{ selectedImportDetail.imported_rows }}</strong>
          </div>
          <div>
            <span>跳过</span>
            <strong>{{ selectedImportDetail.skipped_rows }}</strong>
          </div>
          <div>
            <span>失败</span>
            <strong>{{ selectedImportDetail.failed_rows }}</strong>
          </div>
        </div>

        <div v-if="selectedImportDetail.errors.length" class="result-errors">
          <strong>错误明细</strong>
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>行号</th>
                  <th>字段</th>
                  <th>错误类型</th>
                  <th>错误原因</th>
                  <th>原始值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in selectedImportDetail.errors" :key="item.id">
                  <td>{{ item.row_number }}</td>
                  <td>{{ item.field_name ?? '-' }}</td>
                  <td>{{ item.error_type }}</td>
                  <td>{{ item.error_message }}</td>
                  <td>{{ item.raw_value ?? '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="empty-state">该次导入没有错误记录。</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.data-management-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.page-heading,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-eyebrow);
  font-weight: 700;
  letter-spacing: 1.5px;
}

.page-heading h1 {
  margin: 8px 0;
}

.page-heading p {
  margin-bottom: 0;
  font-size: 13px;
}

.refresh-button,
.error-message button {
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--color-text-primary);
  font-size: 12px;
}

.refresh-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.upload-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.upload-controls {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;
}

.upload-field {
  display: flex;
  min-width: 180px;
  flex-direction: column;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.upload-field select {
  min-height: 36px;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--color-text-primary);
}

.file-field {
  flex: 1;
}

.file-picker {
  display: flex;
  min-height: 36px;
  align-items: center;
  gap: 12px;
}

.file-name {
  overflow: hidden;
  color: var(--color-text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-input {
  display: none;
}

.primary-button,
.secondary-button,
.detail-button {
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--color-text-primary);
  font-size: 12px;
  cursor: pointer;
}

.primary-button {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.upload-hint,
.result-filename {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 12px;
}

.upload-error {
  padding: 10px 12px;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  background: #fef2f2;
  color: #b91c1c;
  font-size: 12px;
}

.upload-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.result-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.result-stats > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 12px;
  border-radius: var(--radius-md);
  background: #f8fafc;
}

.result-stats span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.result-stats strong {
  color: var(--color-text-primary);
  font-size: 19px;
}

.result-errors {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  color: var(--color-text-primary);
  font-size: 12px;
}

.detail-button {
  padding: 5px 9px;
  color: var(--color-primary);
}

.section-heading h2 {
  margin: 0 0 4px;
  font-size: 17px;
}

.section-heading span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.count-grid,
.integrity-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.count-card,
.integrity-card,
.quality-panel,
.history-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.count-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.count-icon {
  display: flex;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
}

.users-icon {
  background: #eff6ff;
  color: #2563eb;
}

.products-icon {
  background: #ecfdf5;
  color: #059669;
}

.orders-icon {
  background: #fff7ed;
  color: #ea580c;
}

.count-card > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.count-label,
.integrity-label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.count-value {
  color: var(--color-text-primary);
  font-size: 24px;
  line-height: 1.3;
}

.quality-panel,
.history-panel {
  overflow: hidden;
}

.table-tabs {
  display: flex;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
}

.table-tabs button {
  padding: 7px 15px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.table-tabs button.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  white-space: nowrap;
  font-size: 12px;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #edf0f5;
}

.data-table th {
  background: #f8fafc;
  color: var(--color-text-secondary);
  font-weight: 600;
}

.data-table td {
  color: var(--color-text-secondary);
}

.data-table tbody tr:last-child td {
  border-bottom: 0;
}

.field-name {
  color: var(--color-text-primary) !important;
  font-weight: 500;
}

.tag-primary,
.tag-muted,
.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 11px;
}

.tag-primary {
  background: #eff6ff;
  color: #2563eb;
}

.tag-muted {
  background: #f1f5f9;
  color: #64748b;
}

.null-normal {
  color: var(--color-success);
}

.null-warning {
  color: var(--color-danger);
  font-weight: 600;
}

.integrity-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.integrity-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
}

.integrity-card > div {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.integrity-card strong {
  font-size: 23px;
}

.integrity-ok,
.integrity-warning {
  padding: 4px 9px;
  border-radius: 5px;
  font-size: 11px;
}

.integrity-ok {
  background: #ecfdf5;
  color: #15803d;
}

.integrity-warning {
  background: #fef2f2;
  color: #dc2626;
}

.status-success {
  background: #ecfdf5;
  color: #15803d;
}

.status-partial {
  background: #fff7ed;
  color: #c2410c;
}

.status-failed {
  background: #fef2f2;
  color: #dc2626;
}

.status-processing {
  background: #eff6ff;
  color: #2563eb;
}

.status-duplicate {
  background: #f1f5f9;
  color: #64748b;
}

.empty-state,
.loading-state {
  padding: 28px 16px;
  color: var(--color-text-muted);
  text-align: center;
  font-size: 12px;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  background: #fef2f2;
  color: #b91c1c;
  font-size: 12px;
}

.error-message button {
  flex-shrink: 0;
  border-color: #fecaca;
  color: #b91c1c;
}

@media (max-width: 900px) {
  .count-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .upload-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .upload-field {
    min-width: 0;
  }

  .result-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .integrity-grid {
    grid-template-columns: 1fr;
  }
}
</style>
