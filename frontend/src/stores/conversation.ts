import { computed, ref, watch } from "vue";
import { defineStore } from "pinia";
import type { AgentChatResponse } from "../api/agent";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: AgentChatResponse;
  error?: boolean;
  createdAt: number;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
}

const STORAGE_KEY = "datapilot:conversations:v1";

interface PersistedState {
  conversations: Conversation[];
  currentConversationId: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isValidAgentResponse(value: unknown): value is AgentChatResponse {
  if (!isRecord(value) || typeof value.success !== "boolean") {
    return false;
  }

  if (
    "tool_name" in value &&
    value.tool_name !== null &&
    typeof value.tool_name !== "string"
  ) {
    return false;
  }

  if (
    "arguments" in value &&
    value.arguments !== null &&
    !isRecord(value.arguments)
  ) {
    return false;
  }

  for (const key of ["answer", "error", "message"]) {
    if (key in value && value[key] !== null && typeof value[key] !== "string") {
      return false;
    }
  }

  return true;
}

function parseChatMessage(value: unknown): ChatMessage | null {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    !value.id.trim() ||
    (value.role !== "user" && value.role !== "assistant") ||
    typeof value.content !== "string" ||
    typeof value.createdAt !== "number" ||
    !Number.isFinite(value.createdAt)
  ) {
    return null;
  }

  if ("error" in value && typeof value.error !== "boolean") {
    return null;
  }

  if ("response" in value && !isValidAgentResponse(value.response)) {
    return null;
  }

  const message: ChatMessage = {
    id: value.id,
    role: value.role,
    content: value.content,
    createdAt: value.createdAt,
  };

  if ("error" in value) {
    message.error = value.error as boolean;
  }

  if ("response" in value) {
    message.response = value.response as AgentChatResponse;
  }

  return message;
}

function parseConversation(value: unknown): Conversation | null {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    !value.id.trim() ||
    typeof value.title !== "string" ||
    !value.title.trim() ||
    typeof value.createdAt !== "number" ||
    !Number.isFinite(value.createdAt) ||
    typeof value.updatedAt !== "number" ||
    !Number.isFinite(value.updatedAt) ||
    !Array.isArray(value.messages)
  ) {
    return null;
  }

  const messages: ChatMessage[] = [];
  const messageIds = new Set<string>();

  for (const item of value.messages) {
    const message = parseChatMessage(item);

    if (!message || messageIds.has(message.id)) {
      continue;
    }

    messageIds.add(message.id);
    messages.push(message);
  }

  return {
    id: value.id,
    title: value.title,
    createdAt: value.createdAt,
    updatedAt: value.updatedAt,
    messages,
  };
}

function loadState(): PersistedState {
  const emptyState: PersistedState = {
    conversations: [],
    currentConversationId: null,
  };

  try {
    const raw = localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return emptyState;
    }

    const parsed: unknown = JSON.parse(raw);

    if (!isRecord(parsed) || !Array.isArray(parsed.conversations)) {
      return emptyState;
    }

    const conversations: Conversation[] = [];
    const conversationIds = new Set<string>();

    for (const item of parsed.conversations) {
      const conversation = parseConversation(item);

      if (!conversation || conversationIds.has(conversation.id)) {
        continue;
      }

      conversationIds.add(conversation.id);
      conversations.push(conversation);
    }

    const requestedId =
      typeof parsed.currentConversationId === "string"
        ? parsed.currentConversationId
        : null;

    const currentConversationId = conversations.some(
      (item) => item.id === requestedId,
    )
      ? requestedId
      : null;

    return {
      conversations,
      currentConversationId,
    };
  } catch {
    return emptyState;
  }
}

export const useConversationStore = defineStore("conversation", () => {
  const initialState = loadState();

  const conversations = ref<Conversation[]>(initialState.conversations);

  const currentConversationId = ref<string | null>(
    initialState.currentConversationId,
  );

  const currentConversation = computed(
    () =>
      conversations.value.find(
        (item) => item.id === currentConversationId.value,
      ) ?? null,
  );

  function persist() {
    try {
      const state: PersistedState = {
        conversations: conversations.value,
        currentConversationId: currentConversationId.value,
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error("DataPilot 会话保存失败：", error);
    }
  }

  watch([conversations, currentConversationId], persist, { deep: true });

  function createConversation(): Conversation {
    const now = Date.now();

    const conversation: Conversation = {
      id: crypto.randomUUID(),
      title: "新建会话",
      createdAt: now,
      updatedAt: now,
      messages: [],
    };

    conversations.value.unshift(conversation);
    currentConversationId.value = conversation.id;

    return conversation;
  }

  function selectConversation(id: string) {
    const exists = conversations.value.some((item) => item.id === id);

    if (exists) {
      currentConversationId.value = id;
    }
  }

  function addMessage(
    conversationId: string,
    message: Omit<ChatMessage, "id" | "createdAt">,
  ) {
    const conversation = conversations.value.find(
      (item) => item.id === conversationId,
    );

    if (!conversation) {
      return;
    }

    const now = Date.now();

    conversation.messages.push({
      ...message,
      id: crypto.randomUUID(),
      createdAt: now,
    });

    conversation.updatedAt = now;

    if (message.role === "user" && conversation.title === "新建会话") {
      conversation.title = message.content.trim().slice(0, 30) || "新建会话";
    }
  }
  function renameConversation(id: string, title: string) {
    const conversation = conversations.value.find((item) => item.id === id);

    const normalizedTitle = title.trim();

    if (!conversation || !normalizedTitle) {
      return;
    }

    conversation.title = normalizedTitle.slice(0, 30);
    conversation.updatedAt = Date.now();
  }

  function deleteConversation(id: string) {
    conversations.value = conversations.value.filter((item) => item.id !== id);

    if (currentConversationId.value === id) {
      currentConversationId.value = conversations.value[0]?.id ?? null;
    }
  }

  function clearConversations() {
    conversations.value = [];
    currentConversationId.value = null;
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    createConversation,
    selectConversation,
    addMessage,
    renameConversation,
    deleteConversation,
    clearConversations,
  };
});
