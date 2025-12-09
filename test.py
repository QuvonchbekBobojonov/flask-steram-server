import threading
import time
import cv2
import requests

URL = "http://127.0.0.1:8000/push/quvonchbek-bobojonov"
FPS = 10

session = requests.Session()
latest = None


def reader():
    global latest
    cap = cv2.VideoCapture(0)
    while True:
        ok, frame = cap.read()
        if ok:
            latest = frame


def worker():
    while True:
        if latest is None:
            time.sleep(0.001)
            continue

        _, jpeg = cv2.imencode(".jpg", latest)

        try:
            session.post(
                URL,
                data=jpeg.tobytes(),
                headers={"Content-Type": "image/jpeg"},
                timeout=0.3
            )
        except Exception as e:
            print("Push error:", e)

        time.sleep(1 / FPS)


threading.Thread(target=reader, daemon=True).start()
threading.Thread(target=worker, daemon=True).start()

print("HTTP POST push started for 1 stream")

while True:
    time.sleep(1)
