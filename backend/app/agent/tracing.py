"""Agent 本地链路追踪基础设施。"""

import json
import logging
import time
from typing import Any
from uuid import uuid4

logger = logging.getLogger("datapilot.tracing")


class TraceSpan:
    """记录单个操作的开始、结束和执行耗时。"""

    def __init__(
        self,
        trace_id: str,
        span_name: str,
        thread_id: str | None = None,
    ) -> None:
        if not isinstance(trace_id, str) or not trace_id.strip():
            raise ValueError("trace_id 不能为空")

        if not isinstance(span_name, str) or not span_name.strip():
            raise ValueError("span_name 不能为空")

        if thread_id is not None and (
            not isinstance(thread_id, str) or not thread_id.strip()
        ):
            raise ValueError("thread_id 必须是非空字符串")

        self.trace_id = trace_id
        self.span_name = span_name
        self.thread_id = thread_id
        self.start_time: int | None = None

    async def __aenter__(self):
        """开始记录 Span。"""

        self.start_time = time.perf_counter_ns()

        self._log(
            event="span_started",
            status="running",
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        """记录 Span 结束状态和耗时。"""

        if self.start_time is None:
            return False

        duration_ns = time.perf_counter_ns() - self.start_time

        if exc_type is None:
            status = "success"
            error_type = None
        else:
            status = "error"
            error_type = exc_type.__name__

        self._log(
            event="span_finished",
            status=status,
            duration_ms=round(duration_ns / 1_000_000, 3),
            error_type=error_type,
        )

        # 不吞掉原始业务异常。
        return False

    def _log(
        self,
        *,
        event: str,
        status: str,
        duration_ms: float | None = None,
        error_type: str | None = None,
    ) -> None:
        """输出结构化追踪日志。"""

        record = {
            "trace_id": self.trace_id,
            "span_name": self.span_name,
            "event": event,
            "status": status,
        }

        if self.thread_id is not None:
            record["thread_id"] = self.thread_id

        if duration_ms is not None:
            record["duration_ms"] = duration_ms

        if error_type is not None:
            record["error_type"] = error_type

        logger.info(
            "%s",
            json.dumps(record, ensure_ascii=False),
        )


class AgentTracer:
    """管理一次 Agent 调用的 Trace。"""

    def __init__(
        self,
        trace_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        if trace_id is None:
            trace_id = uuid4().hex

        if not isinstance(trace_id, str) or not trace_id.strip():
            raise ValueError("trace_id 不能为空")

        if thread_id is not None and (
            not isinstance(thread_id, str) or not thread_id.strip()
        ):
            raise ValueError("thread_id 必须是非空字符串")

        self.trace_id = trace_id
        self.thread_id = thread_id

    def span(self, span_name: str) -> TraceSpan:
        """创建一个关联当前 Trace 的 Span。"""

        return TraceSpan(
            trace_id=self.trace_id,
            span_name=span_name,
            thread_id=self.thread_id,
        )


async def stream_graph_with_tracing(
    graph: Any,
    input_state: dict[str, Any],
    config: dict[str, Any],
    tracer: AgentTracer,
) -> Any:
    """消费 LangGraph 事件流，记录节点 Span 并返回最终状态。"""

    active_spans: dict[str, TraceSpan] = {}
    active_llm_spans: dict[str, TraceSpan] = {}
    active_tool_spans: dict[str, TraceSpan] = {}
    result = None
    result_found = False

    try:
        async for event in graph.astream_events(
            input_state,
            config=config,
            version="v2",
        ):
            event_name = event.get("event")
            run_id = event.get("run_id")
            metadata = event.get("metadata") or {}

            # 采集工具调用事件，不读取工具参数或返回结果。
            if event_name in {
                "on_tool_start",
                "on_tool_end",
                "on_tool_error",
            }:
                if isinstance(run_id, str) and run_id:
                    if event_name == "on_tool_start":
                        tool_name = event.get("name")
                        if not isinstance(tool_name, str) or not tool_name:
                            tool_name = "unknown"

                        span = tracer.span(f"tool.{tool_name}")
                        await span.__aenter__()
                        active_tool_spans[run_id] = span

                    elif event_name == "on_tool_end":
                        span = active_tool_spans.pop(run_id, None)
                        if span is not None:
                            await span.__aexit__(None, None, None)

                    elif event_name == "on_tool_error":
                        span = active_tool_spans.pop(run_id, None)
                        if span is not None:
                            error = RuntimeError("工具调用失败")
                            await span.__aexit__(
                                RuntimeError,
                                error,
                                None,
                            )

                continue

            # 采集 LLM 调用事件，不读取模型输入、输出或流式内容。
            if event_name in {
                "on_chat_model_start",
                "on_chat_model_end",
                "on_chat_model_error",
            }:
                if isinstance(run_id, str) and run_id:
                    if event_name == "on_chat_model_start":
                        model_name = metadata.get("ls_model_name")
                        if not isinstance(model_name, str) or not model_name:
                            model_name = event.get("name") or "unknown"

                        span = tracer.span(f"llm.{model_name}")
                        await span.__aenter__()
                        active_llm_spans[run_id] = span

                    elif event_name == "on_chat_model_end":
                        span = active_llm_spans.pop(run_id, None)
                        if span is not None:
                            await span.__aexit__(None, None, None)

                    elif event_name == "on_chat_model_error":
                        span = active_llm_spans.pop(run_id, None)
                        if span is not None:
                            error = RuntimeError("LLM 调用失败")
                            await span.__aexit__(
                                RuntimeError,
                                error,
                                None,
                            )

                continue

            node_name = metadata.get("langgraph_node")

            # 只处理 LangGraph 节点，不处理根级 Graph 或普通 Runnable。
            if not isinstance(node_name, str) or not node_name:
                if event_name == "on_chain_end" and not event.get("parent_ids"):
                    data = event.get("data") or {}
                    if "output" in data:
                        result = data["output"]
                        result_found = True
                continue

            if not isinstance(run_id, str) or not run_id:
                continue

            if event_name == "on_chain_start":
                span = tracer.span(f"node.{node_name}")
                await span.__aenter__()
                active_spans[run_id] = span

            elif event_name == "on_chain_end":
                span = active_spans.pop(run_id, None)
                if span is not None:
                    await span.__aexit__(None, None, None)

            elif event_name == "on_chain_error":
                span = active_spans.pop(run_id, None)
                if span is not None:
                    error = RuntimeError("LangGraph 节点执行失败")
                    await span.__aexit__(
                        RuntimeError,
                        error,
                        None,
                    )

        if active_spans:
            error = RuntimeError("部分节点缺少结束事件")
            for span in active_spans.values():
                await span.__aexit__(
                    RuntimeError,
                    error,
                    None,
                )
            active_spans.clear()
            raise error

        if active_llm_spans:
            error = RuntimeError("部分 LLM 调用缺少结束事件")
            for span in active_llm_spans.values():
                await span.__aexit__(
                    RuntimeError,
                    error,
                    None,
                )
            active_llm_spans.clear()
            raise error

        if active_tool_spans:
            error = RuntimeError("部分工具调用缺少结束事件")
            for span in active_tool_spans.values():
                await span.__aexit__(
                    RuntimeError,
                    error,
                    None,
                )
            active_tool_spans.clear()
            raise error

        if not result_found:
            raise RuntimeError("LangGraph 事件流未返回最终状态")

        return result

    except BaseException as exc:
        for spans in (
            active_spans,
            active_llm_spans,
            active_tool_spans,
        ):
            for span in spans.values():
                await span.__aexit__(
                    type(exc),
                    exc,
                    exc.__traceback__,
                )
            spans.clear()
        raise
