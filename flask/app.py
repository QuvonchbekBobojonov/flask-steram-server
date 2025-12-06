from flask import Flask, Response, request, render_template
import time
import threading

app = Flask(__name__)

# RAM storage (much faster than Redis)
frames = {}
timestamps = {}
locks = {}

MAX_FPS = 8  # ✅ 5–10 optimal

def get_lock(name):
    if name not in locks:
        locks[name] = threading.Lock()
    return locks[name]

def feeder(name):
    boundary = b"--frame\r\n"
    last_sent = 0

    while True:
        now = time.time()

        # FPS limiting for clients
        if now - last_sent < 1 / MAX_FPS:
            time.sleep(0.002)
            continue

        lock = get_lock(name)
        with lock:
            frame = frames.get(name)

        if frame:
            yield (
                boundary +
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
                frame + b"\r\n"
            )
            last_sent = now
        else:
            time.sleep(0.01)

@app.post("/push/<name>")
def push(name):
    data = request.data
    if not data:
        return "no data", 400

    lock = get_lock(name)
    with lock:
        frames[name] = data
        timestamps[name] = time.time()

    return "OK", 200  # ✅ VERY FAST return

@app.get("/view/<name>")
def view(name):
    return Response(
        feeder(name),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/")
def index():
    now = time.time()
    active = [n for n, t in timestamps.items() if now - t < 3]
    return render_template("index.html", streams=active)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        threaded=True,
        processes=1
    )
