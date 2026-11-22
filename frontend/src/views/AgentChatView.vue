<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { deleteAgentConversation, sendAgentMessage } from '../api/agent'
import { getApiErrorMessage } from '../api/client'
import ConversationSidebar from '../components/ConversationSidebar.vue'
import { useConversationStore } from '../stores/conversation'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

const USER_ID = 'local-dev-user'

const conversationStore = useConversationStore()

// 首次进入页面时，保证至少存在一个会话。
if (!conversationStore.currentConversation) {
  conversationStore.createConversation()
}

const currentConversation = computed(() => conversationStore.currentConversation)

const messages = computed(() => currentConversation.value?.messages ?? [])

const inputText = ref('')
const loading = ref(false)
const sendingConversationId = ref<string | null>(null)
const messageContainer = ref<HTMLElement | null>(null)

const suggestedQuestions = [
  '查询最近一个月的订单 GMV',
  '分析最近几个月的销售趋势',
  '检查当前业务数据是否存在异常',
  '对比各商品品类的销售表现',
]

async function scrollToBottom() {
  await nextTick()

  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

async function sendMessage() {
  const query = inputText.value.trim()
  const conversationId = conversationStore.currentConversationId

  if (!query || loading.value || !conversationId) {
    return
  }

  // 保存用户消息，消息属于当前会话。
  conversationStore.addMessage(conversationId, {
    role: 'user',
    content: query,
  })

  inputText.value = ''
  loading.value = true
  sendingConversationId.value = conversationId

  await scrollToBottom()

  try {
    const response = await sendAgentMessage({
      user_query: query,
      thread_id: conversationId,
      user_id: USER_ID,
    })

    conversationStore.addMessage(conversationId, {
      role: 'assistant',
      content:
        response.answer ||
        response.message ||
        response.error ||
        (response.success ? '任务处理完成。' : '任务处理失败。'),
      response,
      error: !response.success,
    })
  } catch (error: unknown) {
    const errorMessage = getApiErrorMessage(error, '请求失败，请检查后端服务是否正常运行。')

    conversationStore.addMessage(conversationId, {
      role: 'assistant',
      content: errorMessage,
      error: true,
    })
  } finally {
    loading.value = false
    sendingConversationId.value = null

    // 只有仍然停留在原会话时，才滚动消息区域。
    if (conversationStore.currentConversationId === conversationId) {
      await scrollToBottom()
    }
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendMessage()
  }
}

function startNewConversation() {
  if (loading.value) {
    return
  }

  conversationStore.createConversation()
  inputText.value = ''
  void scrollToBottom()
}

function selectConversation(id: string) {
  conversationStore.selectConversation(id)
  inputText.value = ''
  void scrollToBottom()
}
async function renameConversation(id: string) {
  if (loading.value) {
    return
  }

  const conversation = conversationStore.conversations.find((item) => item.id === id)

  if (!conversation) {
    return
  }

  try {
    const result = await ElMessageBox.prompt('请输入新的会话名称', '编辑会话名称', {
      inputValue: conversation.title,
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /\S/,
      inputErrorMessage: '会话名称不能为空',
      inputValidator: (value) => value.trim().length <= 30 || '会话名称不能超过30个字符',
    })

    conversationStore.renameConversation(id, result.value)
  } catch {
    // 用户取消编辑，不修改会话名称。
  }
}

async function deleteConversation(id: string) {
  if (loading.value) {
    return
  }

  loading.value = true

  try {
    // 先删除后端 Checkpoint，成功后再删除本地会话。
    await deleteAgentConversation(id, USER_ID)

    conversationStore.deleteConversation(id)

    // 删除最后一个会话后，自动创建一个空会话。
    if (!conversationStore.currentConversation) {
      conversationStore.createConversation()
    }

    inputText.value = ''
    await scrollToBottom()

    ElMessage.success('会话已删除')
  } catch (error: unknown) {
    const errorMessage = getApiErrorMessage(error, '删除会话失败，请检查后端服务。')

    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

function useSuggestion(question: string) {
  if (loading.value) {
    return
  }

  inputText.value = question
  void sendMessage()
}

function formatResult(result: unknown): string {
  if (typeof result === 'string') {
    return result
  }

  return JSON.stringify(result, null, 2) ?? ''
}
</script>

<template>
  <div class="agent-workspace">
    <header class="chat-header">
      <div>
        <span class="eyebrow">AI WORKSPACE</span>
        <h1>Agent 对话</h1>
        <p>自然语言驱动的电商业务分析助手。</p>
      </div>
    </header>

    <div class="chat-layout">
      <ConversationSidebar
        :conversations="conversationStore.conversations"
        :current-conversation-id="conversationStore.currentConversationId"
        :disabled="loading"
        @create="startNewConversation"
        @select="selectConversation"
        @rename="renameConversation"
        @delete="deleteConversation"
      />

      <section class="chat-panel">
        <div ref="messageContainer" class="message-list">
          <div v-if="messages.length === 0" class="welcome-state">
            <div class="welcome-icon">✦</div>
            <h2>你好，我是 DataPilot</h2>
            <p>你可以向我询问订单指标、销售趋势、品类表现或业务异常。</p>

            <div class="suggestions">
              <button
                v-for="question in suggestedQuestions"
                :key="question"
                :disabled="loading"
                class="suggestion-item"
                @click="useSuggestion(question)"
              >
                {{ question }}
                <span>→</span>
              </button>
            </div>
          </div>

          <template v-else>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message-row"
              :class="message.role"
            >
              <div class="message-avatar">
                {{ message.role === 'user' ? '我' : 'AI' }}
              </div>

              <div class="message-body">
                <div class="message-name">
                  {{ message.role === 'user' ? '你' : 'DataPilot' }}
                </div>

                <div class="message-bubble" :class="{ 'error-bubble': message.error }">
                  {{ message.content }}
                </div>

                <div v-if="message.response?.tool_name" class="tool-info">
                  <span class="tool-label">调用工具</span>
                  <code>{{ message.response.tool_name }}</code>
                </div>

                <details v-if="message.response?.result != null" class="result-details">
                  <summary>查看业务分析结果</summary>
                  <pre>{{ formatResult(message.response.result) }}</pre>
                </details>
              </div>
            </div>

            <div
              v-if="loading && sendingConversationId === conversationStore.currentConversationId"
              class="message-row assistant"
            >
              <div class="message-avatar">AI</div>
              <div class="message-body">
                <div class="message-name">DataPilot</div>
                <div class="loading-bubble">
                  <span class="loading-dot"></span>
                  <span class="loading-dot"></span>
                  <span class="loading-dot"></span>
                  <span>正在分析，请稍候...</span>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div class="composer">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            :maxlength="4000"
            resize="none"
            placeholder="输入业务问题，例如：查询最近一个月的订单 GMV..."
            :disabled="loading"
            @keydown="handleKeydown"
          />

          <div class="composer-footer">
            <span>Enter 发送 · Shift + Enter 换行</span>

            <el-button
              type="primary"
              :disabled="!inputText.trim() || loading"
              :loading="loading"
              @click="sendMessage"
            >
              发送
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.agent-workspace {
  display: flex;
  height: calc(100vh - 124px);
  min-height: 480px;
  flex-direction: column;
  gap: 20px;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.eyebrow {
  color: var(--color-primary);
  font-size: var(--font-size-eyebrow);
  font-weight: 700;
  letter-spacing: 1.5px;
}

.chat-header h1 {
  margin: 6px 0;
  font-size: 24px;
}

.chat-header p {
  margin: 0;
  font-size: 12px;
}

.chat-layout {
  display: flex;
  min-height: 0;
  flex: 1;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: #fff;
  box-shadow: var(--shadow-card);
}

.chat-panel {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: #fff;
  box-shadow: var(--shadow-card);
}

.message-list {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 26px;
}

.welcome-state {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.welcome-icon {
  display: flex;
  width: 56px;
  height: 56px;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 30px;
}

.welcome-state h2 {
  margin: 18px 0 6px;
  font-size: 20px;
}

.welcome-state > p {
  max-width: 440px;
  font-size: 12px;
}

.suggestions {
  display: grid;
  width: min(100%, 540px);
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 22px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 13px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--color-text-secondary);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s;
}

.suggestion-item:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.suggestion-item:disabled {
  cursor: not-allowed;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  display: flex;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}

.user .message-avatar {
  background: #e2e8f0;
  color: #475569;
}

.message-body {
  display: flex;
  max-width: 80%;
  flex-direction: column;
  align-items: flex-start;
  gap: 7px;
}

.user .message-body {
  align-items: flex-end;
}

.message-name {
  color: var(--color-text-muted);
  font-size: 11px;
}

.message-bubble,
.loading-bubble {
  padding: 12px 15px;
  border-radius: 4px 12px 12px;
  background: #f1f5f9;
  color: var(--color-text-primary);
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.user .message-bubble {
  border-radius: 12px 4px 12px 12px;
  background: var(--color-primary);
  color: #fff;
}

.message-bubble.error-bubble {
  background: #fef2f2;
  color: #b91c1c;
}

.tool-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.tool-label {
  color: var(--color-text-muted);
  font-size: 11px;
}

.tool-info code {
  padding: 3px 7px;
  border-radius: 4px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
}

.result-details {
  width: 100%;
  margin-top: 5px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.result-details summary {
  cursor: pointer;
}

.result-details pre {
  max-height: 280px;
  overflow: auto;
  margin-top: 9px;
  padding: 12px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 5px;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: pulse 1s infinite alternate;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  from {
    opacity: 0.3;
  }

  to {
    opacity: 1;
  }
}

.composer {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.composer-footer > span {
  color: var(--color-text-muted);
  font-size: 11px;
}

@media (max-width: 600px) {
  .agent-workspace {
    height: calc(100vh - 110px);
  }

  .chat-header h1 {
    font-size: 21px;
  }

  .message-list {
    padding: 16px;
  }

  .message-body {
    max-width: 88%;
  }

  .suggestions {
    grid-template-columns: 1fr;
  }

  .composer {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .chat-layout {
    min-width: 0;
  }

  .message-list {
    padding: 16px;
  }

  .suggestions {
    grid-template-columns: 1fr;
  }
}
</style>
