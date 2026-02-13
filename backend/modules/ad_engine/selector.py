import os
import json
import time
from typing import Dict, List, Optional


class AdSelector:
    def __init__(self, rules_path: str, ads_dir: str):
        self.rules_path = os.path.abspath(rules_path)
        self.ads_dir = os.path.abspath(ads_dir)

        self.rules: Dict[str, str] = self._load_rules()

        self.available_ads: List[str] = []
        self._scan_ads()

        # idle playlist state
        self.idle_idx = 0

    def _load_rules(self) -> Dict[str, str]:
        if not os.path.exists(self.rules_path):
            raise FileNotFoundError(f"rules.json not found: {self.rules_path}")
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("rules.json must be a JSON object")
        return data

    def _scan_ads(self) -> None:
        if not os.path.isdir(self.ads_dir):
            self.available_ads = []
            return

        # Load all mp4s for idle playlist
        self.available_ads = sorted(
            f for f in os.listdir(self.ads_dir)
            if f.lower().endswith(".mp4")
        )

    def _exists(self, filename: str) -> bool:
        return os.path.isfile(os.path.join(self.ads_dir, filename))

    def _safe(self, filename: str) -> str:
        # returns filename only if exists
        if filename and self._exists(filename):
            return filename

        default_file = self.rules.get("DEFAULT", "")
        if default_file and self._exists(default_file):
            return default_file

        if not self.available_ads:
            self._scan_ads()
        if self.available_ads:
            return self.available_ads[0]

        return "idle_loop.mp4"

    # ---------------- IDLE PLAYLIST ----------------
    def idle_next(self) -> str:
        """
        Return the next video in the ads folder (playlist).
        """
        if not self.available_ads:
            self._scan_ads()

        if self.available_ads:
            video = self.available_ads[self.idle_idx % len(self.available_ads)]
            self.idle_idx = (self.idle_idx + 1) % len(self.available_ads)
            return video

        # fallback if folder empty
        return self.rules.get("IDLE", "idle_loop.mp4")

    # ---------------- RULE-BASED SELECT ----------------
    def choose_by_rule(self, payload: dict) -> str:
        primary = payload.get("primary") if payload else None
        if not primary:
            return self._safe(self.rules.get("DEFAULT", "gaming_ad.mp4"))

        gender = primary.get("gender")
        age = primary.get("age")
        if not gender or not age:
            return self._safe(self.rules.get("DEFAULT", "gaming_ad.mp4"))

        key = f"{gender}_{age}"
        return self._safe(self.rules.get(key, self.rules.get("DEFAULT", "gaming_ad.mp4")))
