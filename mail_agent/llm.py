import json
import logging
import re
from typing import Optional

import ollama

from .models import AgentAction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts — written in English for best model performance.
# User instructions (from config) may be in any language; the model handles it.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an email triage agent. Your job is to analyse incoming emails and decide \
what action to take based on the user's instructions below.

USER INSTRUCTIONS:
---
{instructions}
---

For each email you receive, respond with a JSON object ONLY — no explanations, \
no markdown fences, no extra text. The JSON must have this exact structure:

{{
  "action": "<one of: mark_read | move | delete | reply>",
  "target_folder": "<IMAP folder path — required only when action is move>",
  "reason": "<one short sentence explaining your decision>"
}}

Rules:
- Use "reply" only if the email clearly requires a personal response.
- Use "move" only together with a valid "target_folder".
- If unsure, default to "mark_read".
- Respond with valid JSON and nothing else.
"""

EMAIL_TEMPLATE = """\
From: {sender}
Date: {date}
Subject: {subject}

{body}
"""


def _extract_json(text: str) -> dict:
    """Parse JSON from LLM output, tolerating markdown code fences."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


class LLMClient:
    def __init__(self, model: str, base_url: str):
        self._model = model
        self._client = ollama.Client(host=base_url)

    def decide_action(
        self,
        subject: str,
        sender: str,
        date: str,
        body: Optional[str],
        instructions: str,
    ) -> AgentAction:
        system = SYSTEM_PROMPT.format(instructions=instructions.strip())
        body_text = (body or "(no body)")[:4000]  # guard against huge bodies
        user_message = EMAIL_TEMPLATE.format(
            sender=sender,
            date=date,
            subject=subject,
            body=body_text,
        )

        logger.debug("Querying LLM (model=%s) for action decision...", self._model)
        response = self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        raw = response.message.content
        logger.debug("LLM raw response: %s", raw)

        try:
            data = _extract_json(raw)
            action = AgentAction(**data)
            return action
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning(
                "Could not parse LLM response as JSON — falling back to mark_read. Error: %s", exc
            )
            return AgentAction(action="mark_read", reason="LLM response parse error (fallback)")
