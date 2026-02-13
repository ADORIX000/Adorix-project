import os
import time
from typing import Dict, Any
from .selector import AdSelector


class LogicEngine:
    def __init__(self, idle_rotate_seconds: int = 12):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = os.path.join(base_dir, "rules.json")
        ads_dir = os.path.join(base_dir, "ads")

        self.selector = AdSelector(rules_path=rules_path, ads_dir=ads_dir)

        self.last_video: str = ""
        self.idle_rotate_seconds = idle_rotate_seconds
        self._next_idle_switch_time = 0.0

    def decide(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload example:
          {"count": 0}
          {"count": 1, "primary": {"gender": "Female", "age": "19-29"}}
        """
        count = int(payload.get("count", 0)) if payload else 0
        now = time.time()

        # -------- IDLE MODE: playlist rotation --------
        if count == 0:
            # rotate only when time is reached or first time
            if now >= self._next_idle_switch_time or not self.last_video:
                video = self.selector.idle_next()
                self._next_idle_switch_time = now + self.idle_rotate_seconds
            else:
                video = self.last_video  # keep current until next switch
        else:
            # -------- ACTIVE MODE: rule-based --------
            video = self.selector.choose_by_rule(payload)
            # reset idle timer so when it goes idle again it rotates fresh
            self._next_idle_switch_time = 0.0

        changed = (video != self.last_video)
        self.last_video = video

        return {
            "type": "ad_update",
            "changed": changed,
            "video": video,
            "count": count
        }
