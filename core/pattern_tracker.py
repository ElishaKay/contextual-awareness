# pattern_tracker.py

class PatternShiftTracker:
    def __init__(self):
        pass

    def track(self, turn_history, current_analysis):
        # For simplicity, detect emotional drift
        if not turn_history:
            return {"change": "none"}

        last_emotion = turn_history[-1].get("emotion") if "emotion" in turn_history[-1] else None
        current_emotion = current_analysis.get("emotion")

        if last_emotion and current_emotion and last_emotion != current_emotion:
            return {"change": "emotion_drift"}
        else:
            return {"change": "stable"}
