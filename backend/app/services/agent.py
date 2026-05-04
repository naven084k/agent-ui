import asyncio
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from uuid import uuid4

from .openai import openai
from .tools import execute_tool, TOOL_SPECS


MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ROUNDS = 3

ROUTER_PROMPT = (
    "You are a request router. Select the best agent for the user's message.\n"
    "Reply with ONLY the agent key — no explanation, no punctuation.\n\n"
    "Agents:\n{agents}"
)


@dataclass(frozen=True)
class AgentProfile:
    name: str
    description: str
    system_prompt: str
    tool_names: tuple[str, ...]


AGENTS: dict[str, AgentProfile] = {
    "weather": AgentProfile(
        name="WeatherAgent",
        description="ONLY for weather: current conditions, forecasts, and air quality for any location.",
        system_prompt=(
            "You are a weather assistant. Always use tools to fetch real data — "
            "never guess or fabricate weather information. Be concise and clear."
        ),
        tool_names=("weather_current", "weather_forecast", "air_quality"),
    ),
    "search": AgentProfile(
        name="SearchAgent",
        description="Everything else: stock prices, web search, Wikipedia, currency conversion, word definitions, country facts, news, and any general question.",
        system_prompt=(
            "You are a helpful assistant with access to web search, stock data, Wikipedia, "
            "currency rates, a dictionary, and country information. "
            "Always call the most relevant tool before answering — never guess live data. "
            "Be concise and cite sources when applicable."
        ),
        tool_names=(
            "google_search",
            "wikipedia_search",
            "stock_price",
            "currency_convert",
            "dictionary_lookup",
            "country_info",
        ),
    ),
}


STANDARD_ROLES = {"user", "assistant", "system", "tool"}


def _trim(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return messages[-MAX_HISTORY_MESSAGES:] if len(messages) > MAX_HISTORY_MESSAGES else messages


def _clean(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip non-standard fields the frontend adds (e.g. attachments) before sending to OpenAI."""
    cleaned = []
    for m in messages:
        if m.get("role") not in STANDARD_ROLES:
            continue
        entry: dict[str, Any] = {"role": m["role"], "content": m.get("content") or ""}
        if m["role"] == "tool":
            entry["tool_call_id"] = m["tool_call_id"]
        if m["role"] == "assistant" and m.get("tool_calls"):
            entry["tool_calls"] = m["tool_calls"]
        cleaned.append(entry)
    return cleaned


async def _route(request: dict[str, Any]) -> AgentProfile:
    started = perf_counter()
    descriptions = "\n".join(f"{key}: {agent.description}" for key, agent in AGENTS.items())
    recent = _clean(_trim(request.get("messages", [])))[-3:]
    response = await openai.chat_once({
        "model": request["model"],
        "messages": [
            {"role": "system", "content": ROUTER_PROMPT.format(agents=descriptions)},
            *recent,
        ],
    })
    raw_key = (response.get("choices") or [{}])[0].get("message", {}).get("content", "").strip().lower()
    # Take only the first word in case the model adds punctuation or extra text
    key = raw_key.split()[0].strip(".:,") if raw_key else ""
    # Default to "search" (most capable) rather than "weather" on routing failure
    agent = AGENTS.get(key) or AGENTS.get("search") or next(iter(AGENTS.values()))
    print("[router]", {"raw_key": raw_key, "key": key, "selected": agent.name, "ms": round((perf_counter() - started) * 1000)}, flush=True)
    return agent


def _build_conversation(request: dict[str, Any], agent: AgentProfile) -> list[dict[str, Any]]:
    conversation: list[dict[str, Any]] = [{"role": "system", "content": agent.system_prompt}]
    if request.get("system_prompt"):
        conversation.append({"role": "system", "content": request["system_prompt"]})
    conversation.extend(_clean(_trim(request.get("messages", []))))
    return conversation


async def _tool_round(
    request: dict[str, Any],
    agent: AgentProfile,
    conversation: list[dict[str, Any]],
    round_index: int,
) -> dict[str, Any]:
    allowed = {s["function"]["name"] for s in TOOL_SPECS}
    tools = [s for s in TOOL_SPECS if s["function"]["name"] in set(agent.tool_names) & allowed]
    tool_names_sent = [t["function"]["name"] for t in tools]
    # Round 1: force the model to call a tool so it never skips to a training-data answer.
    # Round 2+: auto, so the model can synthesise the tool results into a final reply.
    tool_choice = "required" if round_index == 1 else "auto"
    print(f"[_tool_round] round={round_index} tool_choice={tool_choice!r} tools_sent={tool_names_sent}", flush=True)
    print(f"[_tool_round] conversation has {len(conversation)} message(s)", flush=True)
    started = perf_counter()
    response = await openai.chat_once({
        "model": request["model"],
        "messages": conversation,
        "tools": tools,
        "tool_choice": tool_choice,
    })
    assistant_message = (response.get("choices") or [{}])[0].get("message", {})
    print(
        "[agent.tool_round]",
        {"agent": agent.name, "round": round_index, "tool_choice": tool_choice, "tool_calls": len(assistant_message.get("tool_calls") or []), "ms": round((perf_counter() - started) * 1000)},
        flush=True,
    )
    return assistant_message


async def stream_agent_reply(request: dict[str, Any]):
    print("=" * 60, flush=True)
    print(f"[stream_agent_reply] START", flush=True)
    print(f"  model      : {request.get('model')}", flush=True)
    print(f"  use_tools  : {request.get('use_tools')}", flush=True)
    print(f"  messages   : {len(request.get('messages', []))} message(s)", flush=True)
    last_msg = (request.get("messages") or [{}])[-1]
    print(f"  last_msg   : role={last_msg.get('role')} content={str(last_msg.get('content', ''))[:120]!r}", flush=True)

    agent = await _route(request)
    print(f"[stream_agent_reply] agent selected → {agent.name}", flush=True)
    print(f"  agent tools: {agent.tool_names}", flush=True)

    conversation = _build_conversation(request, agent)
    print(f"[stream_agent_reply] conversation built: {len(conversation)} message(s)", flush=True)

    tool_events: list[dict[str, Any]] = []

    # Tool-calling rounds
    if not request.get("use_tools"):
        print("[stream_agent_reply] use_tools=False — skipping tool rounds", flush=True)
    else:
        for round_index in range(1, MAX_TOOL_ROUNDS + 1):
            print(f"[stream_agent_reply] --- tool round {round_index} ---", flush=True)
            assistant_message = await _tool_round(request, agent, conversation, round_index)

            finish_reason = assistant_message.get("finish_reason", "unknown")
            tool_calls = assistant_message.get("tool_calls") or []
            print(f"[stream_agent_reply] round {round_index} result: finish_reason={finish_reason!r} tool_calls={len(tool_calls)}", flush=True)

            if not tool_calls:
                print(f"[stream_agent_reply] no tool_calls returned — breaking out of tool loop", flush=True)
                break

            conversation.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            })

            for tool_call in tool_calls:
                name = tool_call["function"]["name"]
                raw_args = tool_call["function"].get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                print(f"[stream_agent_reply] calling tool: {name}  args={args}", flush=True)
                event_id = str(uuid4())
                yield {"type": "tool_start", "data": {"id": event_id, "name": name, "status": "running", "input": args, "output": ""}}

                started = perf_counter()
                try:
                    result = await asyncio.to_thread(execute_tool, name, args)
                    elapsed = round((perf_counter() - started) * 1000)
                    event = {"id": event_id, "name": name, "status": "completed", "input": args, "output": result}
                    conversation.append({"role": "tool", "tool_call_id": tool_call["id"], "content": result})
                    print(f"[stream_agent_reply] tool {name} → completed ({elapsed}ms)", flush=True)
                    print(f"  result: {result[:200]!r}", flush=True)
                except Exception as exc:
                    elapsed = round((perf_counter() - started) * 1000)
                    event = {"id": event_id, "name": name, "status": "failed", "input": args, "output": str(exc)}
                    conversation.append({"role": "tool", "tool_call_id": tool_call["id"], "content": str(exc)})
                    print(f"[stream_agent_reply] tool {name} → FAILED ({elapsed}ms): {exc}", flush=True)

                tool_events.append(event)
                yield {"type": "tool_end", "data": event}

    print(f"[stream_agent_reply] streaming final response (conversation={len(conversation)} msgs, tools_run={len(tool_events)})", flush=True)
    # Stream final response
    accumulated = ""
    async for chunk in openai.chat_stream({"model": request["model"], "messages": conversation}):
        token = chunk.get("message", {}).get("content", "")
        if token:
            accumulated += token
            yield {"type": "token", "data": token}
        if chunk.get("done"):
            print(f"[stream_agent_reply] DONE — response length={len(accumulated)} chars", flush=True)
            print("=" * 60, flush=True)
            yield {"type": "done", "data": {"content": accumulated, "tool_events": tool_events, "citations": [], "agent": agent.name}}
