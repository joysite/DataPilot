
<script setup lang="ts">
import type { Conversation } from '../stores/conversation'
import {
  Plus,
  ChatLineRound,
  MoreFilled,
  EditPen,
  Delete,
} from '@element-plus/icons-vue'

defineProps<{
  conversations: Conversation[]
  currentConversationId: string | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  create: []
  select: [id: string]
  rename: [id: string]
  delete: [id: string]
}>()

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()

  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  })
}

function handleCommand(command: string, id: string) {
  if (command === 'rename') {
    emit('rename', id)
  } else if (command === 'delete') {
    emit('delete', id)
  }
}
</script>

<template>
  <aside class="conversation-sidebar">
    <el-button
      type="primary"
      class="new-button"
      :disabled="disabled"
      @click="emit('create')"
    >
      <el-icon><Plus /></el-icon>
      新建会话
    </el-button>

    <div class="history-heading">
      <span>最近会话</span>
      <span class="history-count">{{ conversations.length }}</span>
    </div>

    <div v-if="conversations.length === 0" class="empty-history">
      <el-icon><ChatLineRound /></el-icon>
      <span>暂无历史会话</span>
    </div>

    <div v-else class="conversation-list">
      <div
        v-for="item in conversations"
        :key="item.id"
        class="conversation-item"
        :class="{
          active: item.id === currentConversationId,
        }"
        @click="emit('select', item.id)"
      >
        <div class="conversation-content">
          <div class="conversation-title">
            {{ item.title }}
          </div>
          <div class="conversation-meta">
            <span>{{ formatTime(item.updatedAt) }}</span>
            <span>{{ item.messages.length }} 条消息</span>
          </div>
        </div>

        <el-dropdown
            trigger="click"
            placement="bottom-end"
            :disabled="disabled"
            @command="(command: string) => handleCommand(command, item.id)"
            @click.stop
            >
            <el-button
                class="more-button"
                text
                circle
                :disabled="disabled"
                @click.stop
            >
                <el-icon><MoreFilled /></el-icon>
            </el-button>

            <template #dropdown>
                <el-dropdown-menu>
                <el-dropdown-item command="rename">
                    <el-icon><EditPen /></el-icon>
                    编辑名称
                </el-dropdown-item>

                <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除会话</span>
                </el-dropdown-item>
                </el-dropdown-menu>
            </template>
            </el-dropdown>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.conversation-sidebar {
  display: flex;
  width: 230px;
  min-width: 0;
  flex-direction: column;
  padding: 16px 12px;
  border-right: 1px solid var(--color-border);
  background: #fafbfc;
}

.new-button {
  width: 100%;
  margin-bottom: 24px;
}

.history-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 12px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.history-count {
  color: var(--color-text-muted);
  font-size: 11px;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 11px 9px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #f1f5f9;
}

.conversation-item.active {
  background: #eaf2ff;
}

.conversation-content {
  min-width: 0;
  flex: 1;
}

.conversation-title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-meta {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  margin-top: 6px;
  color: var(--color-text-muted);
  font-size: 10px;
}

.more-button {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  opacity: 0;
  color: var(--color-text-secondary);
}

.conversation-item:hover .more-button,
.conversation-item.active .more-button {
  opacity: 1;
}

.more-button:hover {
  background: #e2e8f0;
  color: var(--color-text-primary);
}

.delete-text {
  color: var(--color-danger);
}

.empty-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 30px 8px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.empty-history .el-icon {
  font-size: 24px;
}

@media (max-width: 768px) {
  .conversation-sidebar {
    width: 180px;
  }
}
</style>
