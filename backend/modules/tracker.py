import time

class AdSessionTracker:
    """
    Utility to track the duration and demographics of an ad viewership session.
    """
    def __init__(self):
        self.ad_filename = None
        self.viewer_data = None
        self.start_time = None
        self.engaged = False

    def start(self, ad_filename, viewer_data=None):
        """Starts a new tracking session."""
        self.ad_filename = ad_filename
        self.viewer_data = viewer_data or {"age": "Unknown", "gender": "Unknown"}
        self.start_time = time.time()
        self.engaged = False
        # print(f"⏱️ [Tracker] Session started for {ad_filename}")

    def set_engaged(self, status=True):
        """Flags the session as engaged (e.g., user talked or interacted)."""
        self.engaged = status

    def stop(self):
        """
        Stops the session and returns a data dictionary for reporting.
        Returns None if no session was active.
        """
        if self.start_time is None:
            return None

        duration = time.time() - self.start_time
        
        # Prepare reporting payload
        event_data = {
            "filename": self.ad_filename,
            "age": self.viewer_data.get("age", "Unknown"),
            "gender": self.viewer_data.get("gender", "Unknown"),
            "duration": round(duration, 2),
            "engaged": self.engaged
        }

        # Reset
        self.start_time = None
        self.ad_filename = None
        
        return event_data
