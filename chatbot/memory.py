import os, json
from typing import List, Dict

class MemoryStore:
    """Very small, file-backed memory per session_id.

    - Keeps last N turns
    - Maintains a lightweight running summary (first assistant answer + last user topic)
    """
    def __init__(self, base_dir: str = "sessions", max_turns: int = 6):
        self.base_dir = base_dir
        self.max_turns = max_turns
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        return os.path.join(self.base_dir, f"{session_id}.json")

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        p = self._path(session_id)
        if not os.path.exists(p):
            return []
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("history", [])
        except Exception:
            return []

    def get_summary(self, session_id: str) -> str:
        p = self._path(session_id)
        if not os.path.exists(p):
            return ""
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("summary", "")
        except Exception:
            return ""

    def append_turn(self, session_id: str, user: str, assistant: str):
        p = self._path(session_id)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"history": [], "summary": ""}

        data["history"].append({"role": "user", "content": user})
        data["history"].append({"role": "assistant", "content": assistant})
        data["history"] = data["history"][-(2*self.max_turns):]

        if not data["summary"] and assistant:
            first_sent = assistant.split(".")[0].strip()
            data["summary"] = first_sent
        else:
            data["summary"] = (data.get("summary","")[:300] + " | last_topic: " + user[:100]).strip()

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
