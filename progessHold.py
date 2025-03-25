import threading

progress = 0
_progress_lock = threading.Lock()


def add_progress():
    global progress
    with _progress_lock:
        progress += 5
        if progress >= 100:
            progress = 95  #cap it at 95, extension displays URL atr 100
        print(f"Progress updated to: {progress}")

def force_progress():
    global progress
    with _progress_lock:
        progress = 100
        print(f"Progress forcefully set to: {progress}")

def reset_progress():
    global progress
    with _progress_lock:
        progress = 0
        print("Progress reset to 0")

