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
            files = [f for f in sorted(os.listdir(self.ads_dir)) 
                     if os.path.isfile(os.path.join(self.ads_dir, f)) and f.lower().endswith(".mp4")]
            
            # Check for JSON consistency
            for f in files:
                json_file = f.replace(".mp4", ".json")
                if not os.path.isfile(os.path.join(self.ads_dir, json_file)):
                    print(f"[SELECTOR] Warning: Missing metadata JSON for {f}")
            
            # If rules request shuffling, shuffle once on load
            if self.rules.get("SHUFFLE_IDLE"):
                random.shuffle(files)
            return files
        except Exception as e:
            print(f"[SELECTOR] Error loading ads: {e}")
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

        key = f"{primary.get('age')}_{primary.get('gender')}"
        return self.rules.get(key, self.rules.get("DEFAULT", "generic_ad.mp4"))

    def get_personalized_ad(self, demographic_key: str) -> str:
        """Takes a demographic string (e.g., '10-15_male') and returns the ad filename."""
        if not demographic_key:
            return self.rules.get("DEFAULT", "generic_ad.mp4")
        
        # According to requirements: "add .mp4 for make the ad name"
        filename = f"{demographic_key}.mp4"
        print(f"[SELECTOR] Searching for ad: {filename} in {self.ads_dir}")
        
        # Optional: check if file exists in ads_dir, otherwise fallback to rules or default
        if os.path.isfile(os.path.join(self.ads_dir, filename)):
            print(f"[SELECTOR] Found direct match: {filename}")
            return filename
            
        # Try finding in rules
        rule_ad = self.rules.get(demographic_key)
        if rule_ad and os.path.isfile(os.path.join(self.ads_dir, rule_ad)):
            return rule_ad
            
        return self.rules.get("DEFAULT", "generic_ad.mp4")

    def get_playlist_for_demographics(self, demographics: list) -> list:
        """Returns a list of ad filenames, starting with personalized matches, followed by all other ads."""
        playlist = []
        # First add all specific personalized matches
        for demo in demographics:
            ad = self.get_personalized_ad(demo)
            if ad not in playlist:
                playlist.append(ad)
                
        # Then append all other available ads to ensure "every time use all ads as well"
        for ad in self.idle_ads:
            if ad not in playlist:
                playlist.append(ad)
                
        return playlist

    def ad_path(self, filename: str) -> str:
        return os.path.join(self.ads_dir, filename)

    def get_next_idle_ad(self) -> str:
        """Unconditionally advances to the next ad in the idle rotation."""
        if not self.idle_ads:
            return self.rules.get("DEFAULT", "generic_ad.mp4")
            
        filename = self.idle_ads[self.idle_index]
        self.idle_index = (self.idle_index + 1) % len(self.idle_ads)
        return filename
