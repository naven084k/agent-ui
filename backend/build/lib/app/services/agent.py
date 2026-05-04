import asyncio
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import uuid4

from .openai import openai
from .tools import execute_tool, get_tool_specs


MAX_HISTORY_MESSAGES = 12
MAX_TOOL_ROUNDS = 3


@dataclass(frozen=True)
class AgentProfile:
    name: str
    description: str
    system_prompt: str
    tool_names: tuple[str, ...]


AGENT_PROFILES: dict[str, AgentProfile] = {
    "general": AgentProfile(
        name="GeneralAgent",
        description="Fallback assistant for general questions and local workspace tasks.",
        system_prompt=(
            "You are GeneralAgent. Answer clearly and directly. Use tools when needed, but do not overuse them. "
            "If a specialist domain is not obvious, solve the user's request pragmatically."
        ),
        tool_names=("read_local_file", "run_python", "web_search", "news_search", "social_updates"),
    ),
    "finance": AgentProfile(
        name="FinanceAgent",
        description="Handles market quotes, macro moves, finance news, and concise financial summaries.",
        system_prompt=(
            "You are FinanceAgent. Focus on financial accuracy, recent market context, and concise interpretation. "
            "When discussing prices, mention that the numbers are tool-fetched and can move. Prefer finance, news, and web tools."
        ),
        tool_names=("finance_lookup", "news_search", "web_search"),
    ),
    "stock_research": AgentProfile(
        name="StockResearchAgent",
        description="Handles equity research, company-specific analysis, catalysts, and sentiment checks.",
        system_prompt=(
            "You are StockResearchAgent. Produce high-signal stock research: latest price context, catalysts, risks, recent news, "
            "and market sentiment. Cross-check with both market data and recent news. Use social updates only as soft sentiment, not fact."
        ),
        tool_names=("finance_lookup", "news_search", "web_search", "social_updates"),
    ),
    "weather": AgentProfile(
        name="WeatherAgent",
        description="Handles current weather and short forecasts.",
        system_prompt=(
            "You are WeatherAgent. Give concise location-specific weather answers, highlight temperatures, conditions, wind, and "
            "forecast changes. If a forecast is relevant, use the forecast tool instead of guessing."
        ),
        tool_names=("weather_lookup", "weather_forecast", "web_search"),
    ),
    "news": AgentProfile(
        name="NewsAgent",
        description="Handles current events, headline summaries, and topical updates.",
        system_prompt=(
            "You are NewsAgent. Focus on recency, summarize the most important developments first, and separate confirmed reporting "
            "from speculation. Use social updates only for supplementary public reaction, not as the primary source of facts."
        ),
        tool_names=("news_search", "web_search", "social_updates"),
    ),
}


def _message_text(request: dict[str, Any]) -> str:
    return " ".join(message.get("content", "") for message in request.get("messages", [])).lower()


def fallback_agent_key(request: dict[str, Any]) -> str:
    text = _message_text(request)
    if any(word in text for word in ("weather", "temperature", "rain", "forecast", "humidity", "wind")):
        return "weather"
    if any(word in text for word in ("stock", "shares", "equity", "earnings", "valuation", "ticker", "company research")):
        return "stock_research"
    if any(word in text for word in ("market", "finance", "inflation", "fed", "interest rate", "bond", "forex", "crypto", "price of")):
        return "finance"
    if any(word in text for word in ("news", "headline", "current events", "latest update", "breaking")):
        return "news"
    return "general"


def _trim_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages
    return messages[-MAX_HISTORY_MESSAGES:]


def _build_conversation(request: dict[str, Any], profile: AgentProfile) -> list[dict[str, Any]]:
    trimmed_messages = _trim_messages(request.get("messages", []))
    conversation: list[dict[str, Any]] = [{"role": "system", "content": profile.system_prompt}]
    if request.get("system_prompt"):
        conversation.append({"role": "system", "content": request["system_prompt"]})
    conversation.extend(trimmed_messages)
    print(
        "[agent.prepare]",
        {
            "agent": profile.name,
            "input_messages": len(request.get("messages", [])),
            "trimmed_messages": len(trimmed_messages),
            "history_trimmed": len(request.get("messages", [])) - len(trimmed_messages),
        },
        flush=True,
    )
    return conversation


async def _decide_tool_calls(
    request: dict[str, Any],
    profile: AgentProfile,
    conversation: list[dict[str, Any]],
    round_index: int,
) -> dict[str, Any]:
    started_at = perf_counter()
    response = await openai.chat_once(
        {
            "model": request["model"],
            "messages": conversation,
            "tools": get_tool_specs(profile.tool_names),
        }
    )
    elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
    assistant_message = (response.get("choices") or [{}])[0].get("message", {})
    tool_calls = assistant_message.get("tool_calls") or []
    print(
        "[agent.tool_decide]",
        {
            "agent": profile.name,
            "round": round_index,
            "tool_calls": len(tool_calls),
            "elapsed_ms": elapsed_ms,
            "model": request["model"],
        },
        flush=True,
    )
    return assistant_message


async def stream_agent_reply(request: dict[str, Any]):
    total_started_at = perf_counter()
    selected_agent_key = fallback_agent_key(request)
    profile = AGENT_PROFILES[selected_agent_key]
    conversation = _build_conversation(request, profile)
    tool_events: list[dict[str, Any]] = []

    print(
        "[agent.route]",
        {"selected": profile.name, "strategy": "heuristic", "model": request["model"]},
        flush=True,
    )

    if request.get("use_tools"):
        for round_index in range(1, MAX_TOOL_ROUNDS + 1):
            assistant_message = await _decide_tool_calls(request, profile, conversation, round_index)
            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                break

            conversation.append(
                {
                    "role": "assistant",
                    "content": assistant_message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                name = tool_call["function"]["name"]
                raw_arguments = tool_call["function"].get("arguments") or "{}"
                try:
                    arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                except json.JSONDecodeError:
                    arguments = {}
                event_id = str(uuid4())
                yield {"type": "tool_start", "data": {"id": event_id, "name": name, "status": "running", "input": arguments, "output": ""}}

                tool_started_at = perf_counter()
                try:
                    result = await asyncio.to_thread(execute_tool, name, arguments)
                    event = {
                        "id": event_id,
                        "name": name,
                        "status": "completed",
                        "input": arguments,
                        "output": result,
                    }
                    conversation.append({"role": "tool", "tool_call_id": tool_call["id"], "content": result})
                except Exception as exc:  # pragma: no cover - defensive path
                    event = {
                        "id": event_id,
                        "name": name,
                        "status": "failed",
                        "input": arguments,
                        "output": str(exc),
                    }
                    conversation.append({"role": "tool", "tool_call_id": tool_call["id"], "content": str(exc)})

                tool_events.append(event)
                print(
                    "[agent.tool_execute]",
                    {
                        "agent": profile.name,
                        "name": name,
                        "status": event["status"],
                        "elapsed_ms": round((perf_counter() - tool_started_at) * 1000, 1),
                    },
                    flush=True,
                )
                yield {"type": "tool_end", "data": event}
        else:
            print(
                "[agent.tool_decide]",
                {"agent": profile.name, "warning": "max_tool_rounds_reached", "rounds": MAX_TOOL_ROUNDS},
                flush=True,
            )

    stream_started_at = perf_counter()
    first_token_ms: float | None = None
    accumulated = ""

    print(
        "[agent.stream_start]",
        {
            "agent": profile.name,
            "conversation_messages": len(conversation),
            "tool_events": len(tool_events),
            "pre_stream_ms": round((stream_started_at - total_started_at) * 1000, 1),
        },
        flush=True,
    )

    async for chunk in openai.chat_stream(
        {
            "model": request["model"],
            "messages": conversation,
        }
    ):
        token = chunk.get("message", {}).get("content", "")
        if token:
            accumulated += token
            if first_token_ms is None:
                first_token_ms = round((perf_counter() - total_started_at) * 1000, 1)
                print(
                    "[agent.first_token]",
                    {"agent": profile.name, "elapsed_ms": first_token_ms, "model": request["model"]},
                    flush=True,
                )
            yield {"type": "token", "data": token}

        if chunk.get("done"):
            total_elapsed_ms = round((perf_counter() - total_started_at) * 1000, 1)
            stream_elapsed_ms = round((perf_counter() - stream_started_at) * 1000, 1)
            print(
                "[agent.done]",
                {
                    "agent": profile.name,
                    "response_length": len(accumulated),
                    "tool_events": len(tool_events),
                    "first_token_ms": first_token_ms,
                    "stream_ms": stream_elapsed_ms,
                    "total_ms": total_elapsed_ms,
                },
                flush=True,
            )
            yield {
                "type": "done",
                "data": {
                    "content": accumulated,
                    "tool_events": tool_events,
                    "citations": [],
                    "agent": profile.name,
                },
            }
