"""
Client for the Base44 Superagent API — this is what connects the desktop app
to Lena's brain: her personality, her tools (calendar, Gmail, notes, memory),
and her long-term memory all live on the Base44 side.

The full, exact API reference is in the agent editor:
    Settings -> Developer / API Docs panel (you can also copy your API key there).
This client is written defensively (tries common payload shapes) so small
differences in response format won't break the app.
"""
import json
import os
import requests


class AgentClient:
    def __init__(self, api_key, agent_id, base_url, session_file="session.json"):
        self.base = base_url.rstrip("/")
        self.agent_id = agent_id
        self.session_file = session_file
        self.headers = {
            "api_key": api_key,
            "Content-Type": "application/json",
        }
        self.conversation_id = self._load_session()

    # ------------------------------------------------------------------ #
    # Conversation management
    # ------------------------------------------------------------------ #

    def _load_session(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file) as f:
                    return json.load(f).get("conversation_id")
            except Exception:
                return None
        return None

    def _save_session(self, conversation_id):
        with open(self.session_file, "w") as f:
            json.dump({"conversation_id": conversation_id}, f)

    def ensure_conversation(self):
        """Return a conversation id, creating a new one only if needed."""
        if self.conversation_id:
            return self.conversation_id
        url = f"{self.base}/api/agents/{self.agent_id}/conversations"
        resp = requests.post(url, headers=self.headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        cid = self._dig_first_id(data)
        if not cid:
            raise SystemExit(
                "Could not find a conversation id in the API response.\n"
                f"Raw response: {json.dumps(data)[:500]}\n"
                "Check the API docs panel in the agent editor and adjust "
                "agent_client.py accordingly."
            )
        self.conversation_id = cid
        self._save_session(cid)
        return cid

    # ------------------------------------------------------------------ #
    # Messaging
    # ------------------------------------------------------------------ #

    def send_message(self, text):
        """Send a user message; return Lena's reply text (or raise)."""
        cid = self.ensure_conversation()
        url = f"{self.base}/api/agents/{self.agent_id}/conversations/{cid}/messages"

        # Try the most likely body shapes; API docs are authoritative.
        for payload in ({"message": text}, {"content": text}):
            resp = requests.post(url, headers=self.headers, json=payload, timeout=300)
            if resp.status_code < 400:
                return self._extract_reply(resp.json())
            last = resp

        last.raise_for_status()

    def _extract_reply(self, data):
        """Pull the assistant's text out of an unknown response shape."""
        if isinstance(data, str):
            return data
        # Common top-level keys first.
        for key in ("message", "content", "text", "reply", "response", "answer"):
            val = data.get(key) if isinstance(data, dict) else None
            if isinstance(val, str) and val.strip():
                return val.strip()
        # Then nested under "data" or "result".
        for wrap in ("data", "result"):
            if isinstance(data, dict) and isinstance(data.get(wrap), dict):
                for key in ("message", "content", "text", "reply"):
                    val = data[wrap].get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
        raise RuntimeError(
            "Could not parse Lena's reply from the API response.\n"
            f"Raw: {json.dumps(data)[:500]}\n"
            "Paste this output to Lena in chat and she'll fix agent_client.py."
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _dig_first_id(obj):
        """Recursively find the first 'id' string in an unknown JSON shape."""
        if isinstance(obj, dict):
            if isinstance(obj.get("id"), str) and obj["id"]:
                return obj["id"]
            for v in obj.values():
                found = AgentClient._dig_first_id(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for v in obj:
                found = AgentClient._dig_first_id(v)
                if found:
                    return found
        return None
