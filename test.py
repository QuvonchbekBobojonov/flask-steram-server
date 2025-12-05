import threading
import time

import cv2
import requests

URL = "http://127.0.0.1:8000/push"
ROOMS = 30
FPS = 10

session = requests.Session()
latest = None


def reader():
    global latest
    cap = cv2.VideoCapture(0)
    while True:
        ok, f = cap.read()
        if ok:
            latest = f


def worker(i):
    name = f"{URL}/room_{i}"
    while True:
        if latest is None:
            time.sleep(0.001)
            continue
        _, jpeg = cv2.imencode(".jpg", latest)
        session.post(
            name,
            data=jpeg.tobytes(),
            headers={"Content-Type": "image/jpeg"},
            timeout=0.2
        )
    time.sleep(1 / FPS)


threading.Thread(target=reader, daemon=True).start()

for i in range(ROOMS):
    threading.Thread(target=worker, args=(i,), daemon=True).start()

print("HTTP POST push started for 30 rooms")

while True:
    time.sleep(1)
