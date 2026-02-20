import os
import json
import random

class AdSelector:
    def __init__(self, rules_path: str, ads_dir: str):
        self.rules_path = rules_path
        self.ads_dir = ads_dir
        self.rules = self._load()
        self.idle_ads = self._load_ads()
        self.idle_index = 0
        self.current_idle = None

    def _load(self):
        with open(self.rules_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_ads(self):
        try:
            files = [f for f in sorted(os.listdir(self.ads_dir)) if os.path.isfile(os.path.join(self.ads_dir, f))]
            # If rules request shuffling, shuffle once on load
            if self.rules.get("SHUFFLE_IDLE"):
                random.shuffle(files)
            return files
        except Exception:
            return []

    def reshuffle_idle_ads(self):
        """Reshuffle the current idle ads list (call after a full cycle).

        Only reshuffles when `SHUFFLE_IDLE` is truthy in rules.
        """
        if self.rules.get("SHUFFLE_IDLE") and self.idle_ads:
            random.shuffle(self.idle_ads)

    def choose_ad_filename(self, payload: dict, advance_idle: bool = False) -> str:
        # payload is your shared/current_users.json content
        if not payload or payload.get("status") == "IDLE":
            # rotate through available ads only when explicitly advanced
            if self.idle_ads:
                if advance_idle or self.current_idle is None:
                    filename = self.idle_ads[self.idle_index]
                    self.current_idle = filename
                    self.idle_index = (self.idle_index + 1) % len(self.idle_ads)
                return self.current_idle
            return self.rules.get("IDLE", "idle_loop.mp4")

        # not idle: clear current idle holder so rotation resumes correctly later
        self.current_idle = None

        primary = payload.get("primary")
        if not primary:
            return self.rules.get("DEFAULT", "generic_ad.mp4")

        key = f"{primary.get('gender')}_{primary.get('age')}"
        return self.rules.get(key, self.rules.get("DEFAULT", "generic_ad.mp4"))

    def get_personalized_ad(self, demographic_key: str) -> str:
        """Takes a demographic string (e.g., '10-15_male') and returns the ad filename."""
        if not demographic_key:
            return self.rules.get("DEFAULT", "generic_ad.mp4")
        
        # According to requirements: "add .mp4 for make the ad name"
        filename = f"{demographic_key}.mp4"
        
        # Optional: check if file exists in ads_dir, otherwise fallback to rules or default
        if os.path.isfile(os.path.join(self.ads_dir, filename)):
            return filename
            
        return self.rules.get(demographic_key, self.rules.get("DEFAULT", "generic_ad.mp4"))

    def ad_path(self, filename: str) -> str:
        return os.path.join(self.ads_dir, filename)
