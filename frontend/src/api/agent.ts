import apiClient from './client'

export interface AgentChatRequest {
  user_query: string
  thread_id: string
  user_id: string
}

export interface AgentChatResponse {
  success: boolean
  tool_name?: string | null
  arguments?: Record<string, unknown> | null
  result?: unknown
  answer?: string | null
  error?: string | null
  message?: string | null
}

/**
 * 向 DataPilot Agent 提交业务分析问题。
 */
export async function sendAgentMessage(request: AgentChatRequest): Promise<AgentChatResponse> {
  const response = await apiClient.post<AgentChatResponse>('/agent/chat', request)

  return response.data
}

/**
 * 删除 Agent 会话及其后端历史状态。
 */
export async function deleteAgentConversation(threadId: string, userId: string): Promise<void> {
  await apiClient.delete(`/agent/conversations/${encodeURIComponent(threadId)}`, {
    params: {
      user_id: userId,
    },
  })
}
