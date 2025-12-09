from flask import Flask, Response, render_template, jsonify, session, request
import redis
import time
import threading
import cv2
import requests

FRAME_TTL = 5
ADMIN_PASSWORD = "moorfo_12345"
MEDIAMTX_API = "http://mediamtx:8889/v2/paths/list"
MEDIAMTX_RTSP = "rtsp://mediamtx:8554"

app = Flask(__name__)
app.secret_key = "&,eDm?3s&<pPFnH'@)h!C3QmlZ}?l2"

r = redis.Redis(host="redis", port=6379, decode_responses=False)

last_ts = {}
workers = {}

def active_cameras():
    try:
        data = requests.get(MEDIAMTX_API, timeout=1).json()
        return [p["name"] for p in data.get("items", []) if p.get("ready") is True]
    except:
        return []

def rtsp_worker(name):
    url = f"{MEDIAMTX_RTSP}/{name}"
    cap = cv2.VideoCapture(url)
    while True:
        if not cap.isOpened():
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(url)
            continue
        ok, frame = cap.read()
        if not ok:
            cap.release()
            time.sleep(0.5)
            cap = cv2.VideoCapture(url)
            continue
        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if not ok:
            continue
        now = time.time()
        pipe = r.pipeline(transaction=False)
        pipe.set(f"frame:{name}", jpg.tobytes())
        pipe.set(f"timestamp:{name}", now)
        pipe.expire(f"frame:{name}", FRAME_TTL)
        pipe.expire(f"timestamp:{name}", FRAME_TTL)
        pipe.publish(f"notify:{name}", b"1")
        pipe.execute()
        last_ts[name] = now
        time.sleep(0.1)

def ensure_worker(name):
    if name in workers:
        return
    t = threading.Thread(target=rtsp_worker, args=(name,), daemon=True)
    t.start()
    workers[name] = t

def feeder(name):
    pubsub = r.pubsub()
    pubsub.subscribe(f"notify:{name}")
    try:
        first = r.get(f"frame:{name}")
        if first:
            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(first)).encode() + b"\r\n\r\n" + first + b"\r\n"
        for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            frame = r.get(f"frame:{name}")
            if not frame:
                continue
            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n"
    finally:
        pubsub.close()

@app.post("/auth")
def auth():
    data = request.get_json(force=True, silent=True) or {}
    if data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.get("/stream/<string:name>")
def stream(name):
    ensure_worker(name)
    return Response(feeder(name), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
def index():
    cams = active_cameras()
    for c in cams:
        ensure_worker(c)
    return render_template("index.html", streams=cams)

@app.get("/update")
def update():
    if not session.get("admin"):
        return jsonify([]), 403
    return jsonify(active_cameras())

@app.get("/test-camera")
def test_camera():
    return render_template("test-camera.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
