<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getOrderSummary, type OrderSummary } from '../api/analytics'
import { getAnomalies, type Anomaly } from '../api/anomalies'

const summary = ref<OrderSummary | null>(null)
const anomalies = ref<Anomaly[]>([])

const summaryLoading = ref(false)
const anomaliesLoading = ref(false)
const summaryError = ref('')
const anomaliesError = ref('')

const sortedAnomalies = computed(() =>
  [...anomalies.value].sort((a, b) => b.target_month.localeCompare(a.target_month)).slice(0, 5),
)

const triggeredRuleCount = computed(
  () => new Set(anomalies.value.map((item) => item.anomaly_type)).size,
)

const metricCards = computed(() => {
  if (!summary.value) return []

  return [
    {
      label: '累计 GMV',
      value: formatAmount(summary.value.gmv),
      description: '有效订单产生的交易总额',
    },
    {
      label: '有效订单数',
      value: summary.value.valid_order_count.toLocaleString('zh-CN'),
      description: '已支付、已发货及已完成订单',
    },
    {
      label: '平均客单价',
      value: formatAmount(summary.value.average_order_value),
      description: '有效订单平均交易金额',
    },
    {
      label: '订单取消率',
      value: formatPercent(summary.value.cancellation_rate),
      description: `${summary.value.cancelled_order_count.toLocaleString('zh-CN')} 笔取消订单`,
    },
  ]
})

function formatAmount(value: string | number) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return value

  return `¥${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function formatPercent(value: number | string) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return String(value)

  return `${(amount * 100).toFixed(2)}%`
}

function getAnomalyLabel(anomaly: Anomaly) {
  const labels: Record<Anomaly['anomaly_type'], string> = {
    category_gmv_drop: '品类 GMV 下降',
    order_count_spike: '订单量突增',
    region_gmv_concentration: '地区 GMV 集中',
    overall_gmv_drop: '整体 GMV 下降',
    abnormal_order_amount: '订单金额异常',
  }

  return labels[anomaly.anomaly_type]
}

function getAnomalyTarget(anomaly: Anomaly) {
  switch (anomaly.anomaly_type) {
    case 'category_gmv_drop':
      return anomaly.category
    case 'order_count_spike':
      return `${anomaly.actual_count.toLocaleString('zh-CN')} 笔订单`
    case 'region_gmv_concentration':
      return anomaly.region
    case 'overall_gmv_drop':
      return '整体业务'
    case 'abnormal_order_amount':
      return `订单 ${anomaly.order_id}`
  }
}

async function loadSummary() {
  summaryLoading.value = true
  summaryError.value = ''

  try {
    summary.value = await getOrderSummary()
  } catch (error) {
    summaryError.value = '经营指标加载失败，请检查后端服务。'
    console.error('Failed to load overview summary:', error)
  } finally {
    summaryLoading.value = false
  }
}

async function loadAnomalies() {
  anomaliesLoading.value = true
  anomaliesError.value = ''

  try {
    anomalies.value = await getAnomalies()
  } catch (error) {
    anomaliesError.value = '异常概况加载失败，请检查后端服务。'
    console.error('Failed to load overview anomalies:', error)
  } finally {
    anomaliesLoading.value = false
  }
}

async function refreshOverview() {
  await Promise.all([loadSummary(), loadAnomalies()])
}

onMounted(refreshOverview)
</script>

<template>
  <div class="overview-page">
    <section class="welcome-section">
      <div>
        <span class="eyebrow">WELCOME TO DATAPILOT</span>
        <h1>智能业务分析工作台</h1>
        <p>通过自然语言与 AI Agent 交互，查询业务指标、分析销售趋势并发现异常。</p>
      </div>
      <div class="welcome-logo">
        <img src="../assets/datapilot-logo.svg" alt="" />
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>经营概况</h2>
          <span>来自业务分析模块的实时统计数据</span>
        </div>
        <button
          type="button"
          class="refresh-button"
          :disabled="summaryLoading || anomaliesLoading"
          @click="refreshOverview"
        >
          {{ summaryLoading || anomaliesLoading ? '刷新中...' : '↻ 刷新数据' }}
        </button>
      </div>

      <div v-if="summaryError" class="error-message" role="alert">
        {{ summaryError }}
      </div>

      <div v-if="summaryLoading && !summary" class="loading-state">正在加载经营指标...</div>

      <div v-else-if="summary" class="metric-grid">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-card">
          <span class="metric-label">{{ metric.label }}</span>
          <strong class="metric-value">{{ metric.value }}</strong>
          <span class="metric-description">{{ metric.description }}</span>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>异常概况</h2>
          <span>当前业务数据检测结果</span>
        </div>
        <RouterLink to="/anomalies" class="section-link"> 查看全部异常 → </RouterLink>
      </div>

      <div v-if="anomaliesError" class="error-message" role="alert">
        {{ anomaliesError }}
      </div>

      <div v-if="anomaliesLoading && !anomalies.length" class="loading-state">
        正在加载异常检测结果...
      </div>

      <template v-else-if="!anomaliesError">
        <div class="anomaly-summary-grid">
          <article class="anomaly-summary-card">
            <span>异常总数</span>
            <strong>{{ anomalies.length }}</strong>
            <small>当前检测到的异常记录</small>
          </article>

          <article class="anomaly-summary-card">
            <span>触发规则</span>
            <strong>{{ triggeredRuleCount }} / 5</strong>
            <small>已触发的异常检测规则</small>
          </article>

          <article class="anomaly-summary-card">
            <span>涉及月份</span>
            <strong>
              {{ new Set(anomalies.map((item) => item.target_month)).size }}
            </strong>
            <small>存在异常的目标月份</small>
          </article>
        </div>

        <div v-if="!anomalies.length" class="empty-state">当前没有检测到业务异常。</div>

        <div v-else class="recent-anomalies">
          <div
            v-for="(item, index) in sortedAnomalies"
            :key="`${item.anomaly_type}-${item.target_month}-${index}`"
            class="recent-anomaly-item"
          >
            <div class="recent-anomaly-main">
              <span class="anomaly-dot"></span>
              <div>
                <strong>{{ getAnomalyLabel(item) }}</strong>
                <span>{{ getAnomalyTarget(item) }}</span>
              </div>
            </div>
            <span class="anomaly-month">{{ item.target_month }}</span>
          </div>
        </div>
      </template>
    </section>

    <section class="section">
      <div class="section-heading">
        <div>
          <h2>工作台</h2>
          <span>选择一个功能开始使用</span>
        </div>
      </div>

      <div class="feature-grid">
        <RouterLink to="/agent" class="feature-card">
          <div class="feature-icon agent-icon">✦</div>
          <h3>Agent 对话</h3>
          <p>使用自然语言查询订单、分析指标和执行多步骤业务任务。</p>
          <span class="feature-action">开始对话 →</span>
        </RouterLink>

        <RouterLink to="/data-management" class="feature-card">
          <div class="feature-icon data-icon">▤</div>
          <h3>数据管理</h3>
          <p>导入业务数据、查看数据质量和检查数据完整性。</p>
          <span class="feature-action">管理数据 →</span>
        </RouterLink>

        <RouterLink to="/analytics" class="feature-card">
          <div class="feature-icon analysis-icon">▥</div>
          <h3>业务分析</h3>
          <p>分析销售趋势、品类表现和区域业务数据。</p>
          <span class="feature-action">查看分析 →</span>
        </RouterLink>

        <RouterLink to="/anomalies" class="feature-card">
          <div class="feature-icon anomaly-icon">⌁</div>
          <h3>异常检测</h3>
          <p>识别 GMV 波动、订单异常和区域销售集中等问题。</p>
          <span class="feature-action">查看异常 →</span>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.overview-page {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.welcome-section {
  display: flex;
  min-height: 170px;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
  padding: 30px 38px;
  border: 1px solid #dbeafe;
  border-radius: var(--radius-lg);
  background: linear-gradient(115deg, #fff 0%, #eff6ff 100%);
}

.eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-eyebrow);
  font-weight: 700;
  letter-spacing: 1.5px;
}

.welcome-section h1 {
  margin: 10px 0;
  font-size: 27px;
}

.welcome-section p {
  max-width: 560px;
  margin-bottom: 0;
  font-size: 13px;
}

.welcome-logo {
  display: flex;
  width: 112px;
  height: 112px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin: 0 30px;
  border-radius: 28px;
  background: rgb(255 255 255 / 75%);
}

.welcome-logo img {
  width: 82px;
  height: 82px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-heading h2 {
  margin: 0 0 5px;
  font-size: 18px;
}

.section-heading span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.refresh-button {
  padding: 8px 13px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: 12px;
  cursor: pointer;
}

.refresh-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card,
.anomaly-summary-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.metric-label,
.anomaly-summary-card > span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.metric-value {
  overflow-wrap: anywhere;
  color: var(--color-text-primary);
  font-size: var(--font-size-metric);
  font-variant-numeric: tabular-nums;
}

.metric-description,
.anomaly-summary-card small {
  color: var(--color-text-muted);
  font-size: 11px;
}

.anomaly-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.anomaly-summary-card strong {
  color: var(--color-text-primary);
  font-size: 25px;
}

.recent-anomalies {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.recent-anomaly-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 17px;
}

.recent-anomaly-item + .recent-anomaly-item {
  border-top: 1px solid var(--color-border);
}

.recent-anomaly-main {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 11px;
}

.anomaly-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--color-danger);
}

.recent-anomaly-main > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.recent-anomaly-main strong {
  color: var(--color-text-primary);
  font-size: 12px;
}

.recent-anomaly-main div span {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anomaly-month {
  flex-shrink: 0;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.section-link {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.loading-state,
.empty-state {
  padding: 25px 18px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  text-align: center;
  font-size: 12px;
}

.error-message {
  padding: 12px 15px;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  background: #fef2f2;
  color: var(--color-danger);
  font-size: 12px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 15px;
}

.feature-card {
  display: flex;
  min-height: 190px;
  flex-direction: column;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  color: inherit;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgb(15 23 42 / 7%);
}

.feature-icon {
  display: flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font-size: 22px;
}

.agent-icon {
  background: #eff6ff;
  color: #2563eb;
}

.data-icon {
  background: #f1f5f9;
  color: #475569;
}

.analysis-icon {
  background: #ecfdf5;
  color: #059669;
}

.anomaly-icon {
  background: #fff7ed;
  color: #ea580c;
}

.feature-card h3 {
  margin: 14px 0 7px;
  font-size: 15px;
}

.feature-card p {
  margin-bottom: 14px;
  font-size: 12px;
  line-height: 1.8;
}

.feature-action {
  margin-top: auto;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .welcome-section {
    min-height: auto;
    padding: 24px;
  }

  .welcome-section h1 {
    font-size: 21px;
  }

  .welcome-logo {
    display: none;
  }

  .metric-grid,
  .anomaly-summary-grid,
  .feature-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    align-items: flex-start;
  }
}
</style>
