<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getApiErrorMessage } from '../api/client'
import { getAnomalies, type Anomaly } from '../api/anomalies'

const anomalies = ref<Anomaly[]>([])
const loading = ref(false)
const errorMessage = ref('')

const anomalyTypes = [
  { key: 'category_gmv_drop', label: '品类 GMV 下降', color: 'danger' },
  { key: 'order_count_spike', label: '订单量突增', color: 'warning' },
  { key: 'region_gmv_concentration', label: '地区 GMV 集中', color: 'info' },
  { key: 'overall_gmv_drop', label: '整体 GMV 下降', color: 'danger' },
  { key: 'abnormal_order_amount', label: '订单金额异常', color: 'warning' },
] as const

const typeCounts = computed(() =>
  anomalyTypes.map((type) => ({
    ...type,
    count: anomalies.value.filter((item) => item.anomaly_type === type.key).length,
  })),
)

const monthCount = computed(() => new Set(anomalies.value.map((item) => item.target_month)).size)

const triggeredTypeCount = computed(() => typeCounts.value.filter((item) => item.count > 0).length)

const sortedAnomalies = computed(() =>
  [...anomalies.value].sort((a, b) => b.target_month.localeCompare(a.target_month)),
)

function formatAmount(value: string | number) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return value

  return amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatPercent(value: string | number) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return value

  return `${(amount * 100).toFixed(2)}%`
}

function formatRatio(value: string | number) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return value

  return `${amount.toFixed(2)} 倍`
}

function getTypeLabel(anomaly: Anomaly) {
  return anomalyTypes.find((item) => item.key === anomaly.anomaly_type)?.label ?? '未知异常'
}

async function loadAnomalies() {
  loading.value = true
  errorMessage.value = ''

  try {
    anomalies.value = await getAnomalies()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '异常检测数据加载失败，请检查后端服务是否正常。')
    console.error('Failed to load anomalies:', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadAnomalies)
</script>

<template>
  <div class="anomalies-page">
    <section class="page-heading">
      <div>
        <span class="eyebrow">ANOMALY DETECTION</span>
        <h1>异常检测</h1>
        <p>自动识别 GMV 波动、订单量突增及其他业务异常。</p>
      </div>

      <button type="button" class="refresh-button" :disabled="loading" @click="loadAnomalies">
        {{ loading ? '检测中...' : '↻ 重新检测' }}
      </button>
    </section>

    <div v-if="errorMessage" class="error-message" role="alert">
      {{ errorMessage }}
    </div>

    <div v-if="loading && !anomalies.length" class="loading-state">正在执行异常检测...</div>

    <template v-else>
      <section class="metric-grid">
        <article class="metric-card">
          <span class="metric-label">异常总数</span>
          <strong class="metric-value">{{ anomalies.length }}</strong>
          <span class="metric-description">当前检测到的异常记录</span>
        </article>

        <article class="metric-card">
          <span class="metric-label">涉及月份</span>
          <strong class="metric-value">{{ monthCount }}</strong>
          <span class="metric-description">存在异常的目标月份</span>
        </article>

        <article class="metric-card">
          <span class="metric-label">触发规则</span>
          <strong class="metric-value">{{ triggeredTypeCount }} / 5</strong>
          <span class="metric-description">已触发的异常检测规则</span>
        </article>
      </section>

      <section class="section">
        <div class="section-heading">
          <div>
            <h2>异常类型统计</h2>
            <span>各检测规则发现的异常数量</span>
          </div>
        </div>

        <div class="type-grid">
          <article v-for="item in typeCounts" :key="item.key" class="type-card">
            <span class="type-label">{{ item.label }}</span>
            <strong class="type-count">{{ item.count }}</strong>
            <span class="type-unit">条异常记录</span>
          </article>
        </div>
      </section>

      <section class="section">
        <div class="section-heading">
          <div>
            <h2>异常记录</h2>
            <span>按目标月份倒序排列，共 {{ anomalies.length }} 条</span>
          </div>
        </div>

        <div v-if="!anomalies.length" class="empty-state">
          当前没有检测到业务异常，数据状态良好。
        </div>

        <div v-else class="anomaly-list">
          <article
            v-for="(item, index) in sortedAnomalies"
            :key="`${item.anomaly_type}-${item.target_month}-${index}`"
            class="anomaly-card"
          >
            <div class="anomaly-header">
              <div class="anomaly-title">
                <span class="anomaly-indicator"></span>
                <strong>{{ getTypeLabel(item) }}</strong>
              </div>
              <span class="anomaly-month">{{ item.target_month }}</span>
            </div>

            <div class="anomaly-details">
              <template v-if="item.anomaly_type === 'category_gmv_drop'">
                <div class="detail-item">
                  <span>商品品类</span>
                  <strong>{{ item.category }}</strong>
                </div>
                <div class="detail-item">
                  <span>实际 GMV</span>
                  <strong>{{ formatAmount(item.actual_gmv) }}</strong>
                </div>
                <div class="detail-item">
                  <span>历史基线</span>
                  <strong>{{ formatAmount(item.baseline_gmv) }}</strong>
                </div>
                <div class="detail-item highlight-danger">
                  <span>下降幅度</span>
                  <strong>{{ formatPercent(item.drop_rate) }}</strong>
                </div>
                <div class="detail-item">
                  <span>判断阈值</span>
                  <strong>{{ formatPercent(item.threshold) }}</strong>
                </div>
              </template>

              <template v-else-if="item.anomaly_type === 'order_count_spike'">
                <div class="detail-item">
                  <span>实际订单量</span>
                  <strong>{{ item.actual_count.toLocaleString('zh-CN') }}</strong>
                </div>
                <div class="detail-item">
                  <span>去年同期</span>
                  <strong>{{ item.baseline_count.toLocaleString('zh-CN') }}</strong>
                </div>
                <div class="detail-item highlight-warning">
                  <span>同比增长</span>
                  <strong>{{ formatPercent(item.growth_rate) }}</strong>
                </div>
                <div class="detail-item">
                  <span>判断阈值</span>
                  <strong>{{ formatPercent(item.threshold) }}</strong>
                </div>
              </template>

              <template v-else-if="item.anomaly_type === 'region_gmv_concentration'">
                <div class="detail-item">
                  <span>异常地区</span>
                  <strong>{{ item.region }}</strong>
                </div>
                <div class="detail-item">
                  <span>当前 GMV 占比</span>
                  <strong>{{ formatPercent(item.actual_share) }}</strong>
                </div>
                <div class="detail-item">
                  <span>历史平均占比</span>
                  <strong>{{ formatPercent(item.baseline_share) }}</strong>
                </div>
                <div class="detail-item highlight-warning">
                  <span>占比增加</span>
                  <strong>{{ formatPercent(item.share_increase) }}</strong>
                </div>
                <div class="detail-item">
                  <span>占比阈值</span>
                  <strong>{{ formatPercent(item.threshold) }}</strong>
                </div>
                <div class="detail-item">
                  <span>增加阈值</span>
                  <strong>{{ formatPercent(item.increase_threshold) }}</strong>
                </div>
              </template>

              <template v-else-if="item.anomaly_type === 'overall_gmv_drop'">
                <div class="detail-item">
                  <span>实际 GMV</span>
                  <strong>{{ formatAmount(item.actual_gmv) }}</strong>
                </div>
                <div class="detail-item">
                  <span>历史基线</span>
                  <strong>{{ formatAmount(item.baseline_gmv) }}</strong>
                </div>
                <div class="detail-item highlight-danger">
                  <span>下降幅度</span>
                  <strong>{{ formatPercent(item.drop_rate) }}</strong>
                </div>
                <div class="detail-item">
                  <span>判断阈值</span>
                  <strong>{{ formatPercent(item.threshold) }}</strong>
                </div>
              </template>

              <template v-else-if="item.anomaly_type === 'abnormal_order_amount'">
                <div class="detail-item">
                  <span>订单 ID</span>
                  <strong>{{ item.order_id }}</strong>
                </div>
                <div class="detail-item">
                  <span>商品 ID</span>
                  <strong>{{ item.product_id }}</strong>
                </div>
                <div class="detail-item">
                  <span>订单金额</span>
                  <strong>{{ formatAmount(item.order_amount) }}</strong>
                </div>
                <div class="detail-item">
                  <span>商品标价</span>
                  <strong>{{ formatAmount(item.product_price) }}</strong>
                </div>
                <div class="detail-item highlight-warning">
                  <span>金额倍数</span>
                  <strong>{{ formatRatio(item.amount_ratio) }}</strong>
                </div>
                <div class="detail-item">
                  <span>判断阈值</span>
                  <strong>{{ formatRatio(item.threshold) }}</strong>
                </div>
              </template>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.anomalies-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
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

.refresh-button {
  padding: 9px 15px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: 12px;
}

.refresh-button:disabled {
  opacity: 0.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.metric-card,
.type-card,
.anomaly-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.metric-card {
  display: flex;
  min-height: 126px;
  flex-direction: column;
  gap: 7px;
  padding: 19px 21px;
}

.metric-label,
.type-label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.metric-value {
  color: var(--color-text-primary);
  font-size: 27px;
  line-height: 1.3;
}

.metric-description,
.type-unit {
  color: var(--color-text-muted);
  font-size: 11px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.section-heading h2 {
  margin: 0 0 4px;
  font-size: 18px;
}

.section-heading span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.type-card {
  display: flex;
  min-height: 112px;
  flex-direction: column;
  gap: 5px;
  padding: 15px;
}

.type-count {
  color: var(--color-text-primary);
  font-size: 24px;
}

.anomaly-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.anomaly-card {
  padding: 18px 20px;
}

.anomaly-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 13px;
  border-bottom: 1px solid var(--color-border);
}

.anomaly-title {
  display: flex;
  align-items: center;
  gap: 9px;
}

.anomaly-title strong {
  font-size: 13px;
}

.anomaly-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
}

.anomaly-month {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.anomaly-details {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  padding-top: 15px;
}

.detail-item {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.detail-item span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.detail-item strong {
  overflow-wrap: anywhere;
  color: var(--color-text-primary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.detail-item.highlight-danger strong {
  color: var(--color-danger);
}

.detail-item.highlight-warning strong {
  color: var(--color-warning);
}

.loading-state,
.empty-state {
  padding: 36px 20px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text-muted);
  text-align: center;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .type-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .anomaly-details {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .type-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .anomaly-details {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .type-grid,
  .anomaly-details {
    grid-template-columns: 1fr;
  }
}
</style>
