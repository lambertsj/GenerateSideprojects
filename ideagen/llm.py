import json
import re

import anthropic


class LLM:
    def __init__(self):
        self.client = anthropic.Anthropic(max_retries=4)

    def text(self, model, system, prompt, tools=None, max_tokens=8000) -> str:
        messages = [{"role": "user", "content": prompt}]
        resp = None
        for _ in range(6):  # server tools such as web search can pause a turn
            kw = dict(model=model, max_tokens=max_tokens, system=system, messages=messages)
            if tools:
                kw["tools"] = tools
            resp = self.client.messages.create(**kw)
            if resp.stop_reason != "pause_turn":
                break
            messages = messages + [{"role": "assistant", "content": resp.content}]
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def json(self, model, system, prompt, tools=None, attempts=2):
        error = None
        for _ in range(attempts):
            try:
                return parse_json(self.text(model, system, prompt, tools))
            except (ValueError, json.JSONDecodeError) as e:
                error = e
        raise RuntimeError(f"Could not parse JSON from the response: {error}")


def parse_json(text: str):
    m = re.search(r"<json>(.*?)</json>", text, re.S)
    body = m.group(1) if m else text
    body = re.sub(r"```(?:json)?", "", body).strip()
    starts = [i for i in (body.find("{"), body.find("[")) if i != -1]
    if not starts:
        raise ValueError("No JSON found")
    obj, _ = json.JSONDecoder().raw_decode(body[min(starts):])
    return obj
