class StateManager:
    def __init__(self):
        self.state = "IDLE"

    def update(self, payload: dict):
        self.state = "ACTIVE" if payload and payload.get("status") == "ACTIVE" else "IDLE"
        return self.state
