<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getApiErrorMessage } from '../api/client'
import {
  getCategoryComparison,
  getGMVTrend,
  getOrderSummary,
  type CategoryComparison,
  type MonthlyGMV,
  type OrderSummary,
} from '../api/analytics'

const startDate = ref('')
const endDate = ref('')

const summary = ref<OrderSummary | null>(null)
const trend = ref<MonthlyGMV[]>([])
const categories = ref<CategoryComparison[]>([])

const loading = ref(false)
const errorMessage = ref('')

const dateRange = computed(() => {
  return {
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
  }
})

const chartModel = computed(() => {
  const width = 760
  const height = 260
  const left = 56
  const right = 18
  const top = 18
  const bottom = 44
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom

  const values = trend.value.map((item) => {
    const value = Number(item.gmv)
    return Number.isFinite(value) ? value : 0
  })
  const maxValue = Math.max(0, ...values)
  const scaleMax = maxValue > 0 ? maxValue * 1.1 : 1

  const points = trend.value.map((item, index) => {
    const value = values[index]
    const x =
      trend.value.length === 1
        ? left + plotWidth / 2
        : left + (index / (trend.value.length - 1)) * plotWidth
    const y = top + plotHeight - (value / scaleMax) * plotHeight

    return { month: item.month, value, x, y }
  })

  const labels = points.filter((_, index) => {
    const interval = Math.max(1, Math.ceil((points.length - 1) / 5))
    return index === 0 || index === points.length - 1 || index % interval === 0
  })

  const ticks = Array.from({ length: 5 }, (_, index) => {
    const value = (scaleMax / 4) * (4 - index)
    return {
      value,
      y: top + (plotHeight / 4) * index,
      label: formatCompactAmount(value),
    }
  })

  return {
    points,
    labels,
    ticks,
    polyline: points.map((point) => `${point.x},${point.y}`).join(' '),
  }
})

const categoryRows = computed(() => {
  const maxGMV = Math.max(
    0,
    ...categories.value.map((item) => {
      const value = Number(item.gmv)
      return Number.isFinite(value) ? value : 0
    }),
  )

  return categories.value.map((item) => {
    const value = Number(item.gmv)
    const gmv = Number.isFinite(value) ? value : 0

    return {
      ...item,
      barPercent: maxGMV > 0 ? (gmv / maxGMV) * 100 : 0,
    }
  })
})

function formatCompactAmount(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

const metricCards = computed(() => {
  if (!summary.value) return []

  return [
    {
      label: 'GMV',
      value: formatAmount(summary.value.gmv),
      description: '有效订单成交总额',
    },
    {
      label: '有效订单',
      value: summary.value.valid_order_count.toLocaleString('zh-CN'),
      description: `总订单 ${summary.value.total_order_count.toLocaleString('zh-CN')} 笔`,
    },
    {
      label: '客单价',
      value: formatAmount(summary.value.average_order_value),
      description: '有效订单平均成交金额',
    },
    {
      label: '取消率',
      value: `${(summary.value.cancellation_rate * 100).toFixed(2)}%`,
      description: `${summary.value.cancelled_order_count.toLocaleString('zh-CN')} 笔已取消`,
    },
  ]
})

function formatAmount(value: string | number) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return value

  return amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function loadAnalytics() {
  if (startDate.value && endDate.value && startDate.value > endDate.value) {
    errorMessage.value = '开始日期不能晚于结束日期。'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const [summaryResult, trendResult, categoryResult] = await Promise.all([
      getOrderSummary(dateRange.value),
      getGMVTrend(dateRange.value),
      getCategoryComparison(dateRange.value),
    ])

    summary.value = summaryResult
    trend.value = trendResult
    categories.value = categoryResult
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '业务分析数据加载失败，请检查后端服务是否正常。')
    console.error('Failed to load analytics:', error)
  } finally {
    loading.value = false
  }
}

function resetDateRange() {
  startDate.value = ''
  endDate.value = ''
  loadAnalytics()
}

onMounted(loadAnalytics)
</script>

<template>
  <div class="analytics-page">
    <section class="page-heading">
      <div>
        <span class="eyebrow">BUSINESS ANALYTICS</span>
        <h1>业务分析</h1>
        <p>查看订单核心指标、月度 GMV 趋势和商品品类表现。</p>
      </div>

      <button type="button" class="refresh-button" :disabled="loading" @click="loadAnalytics">
        {{ loading ? '加载中...' : '↻ 刷新数据' }}
      </button>
    </section>

    <section class="filter-panel">
      <div class="filter-heading">
        <strong>统计日期</strong>
        <span>默认展示全部历史数据</span>
      </div>

      <div class="filter-controls">
        <label>
          <span>开始日期</span>
          <input v-model="startDate" type="date" :max="endDate || undefined" />
        </label>

        <span class="date-separator">至</span>

        <label>
          <span>结束日期</span>
          <input v-model="endDate" type="date" :min="startDate || undefined" />
        </label>

        <button type="button" class="primary-button" :disabled="loading" @click="loadAnalytics">
          查询
        </button>

        <button
          type="button"
          class="secondary-button"
          :disabled="loading || (!startDate && !endDate)"
          @click="resetDateRange"
        >
          重置
        </button>
      </div>
    </section>

    <div v-if="errorMessage" class="error-message" role="alert">
      {{ errorMessage }}
    </div>

    <div v-if="loading && !summary" class="loading-state">正在加载业务分析数据...</div>

    <template v-else-if="summary">
      <section class="metric-grid">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-card">
          <span class="metric-label">{{ metric.label }}</span>
          <strong class="metric-value">{{ metric.value }}</strong>
          <span class="metric-description">{{ metric.description }}</span>
        </article>
      </section>

      <section class="section">
        <div class="section-heading">
          <div>
            <h2>月度 GMV 趋势</h2>
            <span>按月统计有效订单成交金额</span>
          </div>
        </div>
        <div class="chart-panel">
          <div v-if="!trend.length" class="empty-state">当前日期范围内暂无趋势数据。</div>
          <svg
            v-else
            class="trend-chart"
            viewBox="0 0 760 260"
            role="img"
            aria-label="月度 GMV 趋势折线图"
          >
            <g v-for="tick in chartModel.ticks" :key="tick.y">
              <line x1="56" :y1="tick.y" x2="742" :y2="tick.y" class="chart-grid-line" />
              <text x="46" :y="tick.y + 4" text-anchor="end" class="chart-axis-label">
                {{ tick.label }}
              </text>
            </g>

            <polyline
              v-if="chartModel.points.length > 1"
              :points="chartModel.polyline"
              class="chart-line"
            />

            <circle
              v-for="point in chartModel.points"
              :key="point.month"
              :cx="point.x"
              :cy="point.y"
              r="4"
              class="chart-point"
            >
              <title>{{ point.month }}：{{ formatAmount(point.value) }}</title>
            </circle>

            <text
              v-for="point in chartModel.labels"
              :key="point.month"
              :x="point.x"
              y="238"
              text-anchor="middle"
              class="chart-axis-label"
            >
              {{ point.month }}
            </text>
          </svg>
        </div>
      </section>

      <section class="section">
        <div class="section-heading">
          <div>
            <h2>品类业务对比</h2>
            <span>按 GMV 从高到低排列</span>
          </div>
        </div>
        <div class="table-panel">
          <div v-if="!categories.length" class="empty-state">当前日期范围内暂无品类数据。</div>
          <div v-else class="category-table-wrapper">
            <table class="category-table">
              <thead>
                <tr>
                  <th>商品品类</th>
                  <th>GMV</th>
                  <th>GMV 占比趋势</th>
                  <th>有效订单</th>
                  <th>客单价</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="category in categoryRows" :key="category.category">
                  <td class="category-name">{{ category.category }}</td>
                  <td class="numeric-cell">{{ formatAmount(category.gmv) }}</td>
                  <td class="bar-cell">
                    <div class="category-bar-track">
                      <div class="category-bar" :style="{ width: `${category.barPercent}%` }" />
                    </div>
                  </td>
                  <td class="numeric-cell">
                    {{ category.valid_order_count.toLocaleString('zh-CN') }}
                  </td>
                  <td class="numeric-cell">
                    {{ formatAmount(category.average_order_value) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.analytics-page {
  display: flex;
  flex-direction: column;
  gap: 26px;
}

.page-heading {
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
  font-size: 26px;
}

.page-heading p {
  margin-bottom: 0;
  font-size: 13px;
}

.refresh-button,
.primary-button,
.secondary-button {
  min-height: 36px;
  padding: 0 15px;
  border-radius: var(--radius-md);
  font-size: 12px;
  cursor: pointer;
}

.refresh-button,
.secondary-button {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.primary-button {
  border: 1px solid var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.refresh-button:disabled,
.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.filter-panel,
.metric-card,
.chart-panel,
.table-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.filter-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
}

.filter-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
  white-space: nowrap;
}

.filter-heading strong {
  font-size: 13px;
}

.filter-heading span,
.filter-controls label span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.filter-controls {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.filter-controls label {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-controls input {
  width: 150px;
  height: 36px;
  padding: 0 9px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--color-text-primary);
  font-size: 12px;
}

.date-separator {
  padding-bottom: 8px;
  color: var(--color-text-muted);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
}

.metric-label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.metric-value {
  overflow-wrap: anywhere;
  color: var(--color-text-primary);
  font-size: var(--font-size-metric);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.metric-description {
  color: var(--color-text-muted);
  font-size: 11px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-heading h2 {
  margin: 0 0 4px;
  font-size: 17px;
}

.section-heading span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.chart-panel,
.table-panel {
  min-height: 180px;
  padding: 20px;
}

.trend-chart {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}

.chart-grid-line {
  stroke: var(--color-border);
  stroke-width: 1;
  stroke-dasharray: 4 4;
}

.chart-axis-label {
  fill: var(--color-text-muted);
  font-size: 11px;
}

.chart-line {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-point {
  fill: var(--color-surface);
  stroke: var(--color-primary);
  stroke-width: 2.5;
}

.category-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.category-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  white-space: nowrap;
}

.category-table th,
.category-table td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--color-border);
  font-size: 12px;
}

.category-table th {
  color: var(--color-text-muted);
  font-weight: 600;
}

.category-table td {
  color: var(--color-text-secondary);
}

.category-table tbody tr:last-child td {
  border-bottom: 0;
}

.category-name {
  color: var(--color-text-primary) !important;
  font-weight: 600;
}

.numeric-cell {
  font-variant-numeric: tabular-nums;
}

.bar-cell {
  min-width: 150px;
}

.category-bar-track {
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: 99px;
  background: var(--color-primary-light);
}

.category-bar {
  height: 100%;
  border-radius: inherit;
  background: var(--color-primary);
  transition: width 0.25s ease;
}

.placeholder,
.empty-state,
.loading-state {
  display: flex;
  min-height: 140px;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 12px;
}

.error-message {
  padding: 12px 16px;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  background: #fef2f2;
  color: var(--color-danger);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .filter-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-controls {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-controls input {
    width: 130px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
