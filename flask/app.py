from flask_socketio import SocketIO
from flask import Flask, Response, request, render_template, jsonify, session
import redis
import time

app = Flask(__name__)
app.secret_key = "&,eDm?3s&<pPFnH'@)h!C3QmlZ}?l2"
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

r = redis.Redis(host="redis", port=6379, decode_responses=False)
last_ts = {}
FRAME_TTL = 5

ADMIN_PASSWORD = 'moorfo_12345'

def feeder(name):
    pubsub = r.pubsub()
    pubsub.subscribe(f"notify:{name}")

    try:
        # ✅ 1. Birinchi frame (agar mavjud bo‘lsa)
        first = r.get(f"frame:{name}")
        if first:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(first)).encode() + b"\r\n\r\n"
                + first +
                b"\r\n"
            )

        # ✅ 2. Keyingi frame’lar
        for msg in pubsub.listen():
            if msg["type"] != "message":
                continue

            frame = r.get(f"frame:{name}")
            if not frame:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
                + frame +
                b"\r\n"
            )

    except GeneratorExit:
        pass
    finally:
        pubsub.close()


@app.post("/auth")
def auth():
    data = request.get_json()
    if data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.post("/push/<string:name>")
def push(name):
    data = request.get_data()
    if not data:
        return jsonify({"error": "no data"}), 400

    now_ts = time.time()

    pipe = r.pipeline(transaction=False)
    pipe.set(f"frame:{name}", data)
    pipe.set(f"timestamp:{name}", now_ts)
    pipe.expire(f"frame:{name}", FRAME_TTL)
    pipe.expire(f"timestamp:{name}", FRAME_TTL)
    pipe.publish(f"notify:{name}", b"1")
    pipe.execute()

    last_ts[name] = now_ts
    return jsonify({"status": "ok"}), 200


@app.get("/stream/<string:name>")
def view(name):
    return Response(
        feeder(name),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )



@app.get("/")
def index():
    now = time.time()
    active = [n for n, t in last_ts.items() if now - t < FRAME_TTL]
    return render_template("index.html", streams=active)


@app.get("/update")
def update():
    if not session.get("admin"):
        return jsonify([]), 403

    now = time.time()
    active = [n for n, t in last_ts.items() if now - t < FRAME_TTL]
    return jsonify(active)

@app.get("/test-camera")
def camera():
    return render_template("test-camera.html")

@socketio.on("frame")
def receive_frame(data):
    name = data.get("name")
    image = data.get("image")

    if not name or not image:
        return

    now_ts = time.time()

    pipe = r.pipeline(transaction=False)
    pipe.set(f"frame:{name}", image)
    pipe.set(f"timestamp:{name}", now_ts)
    pipe.expire(f"frame:{name}", FRAME_TTL)
    pipe.expire(f"timestamp:{name}", FRAME_TTL)
    pipe.publish(f"notify:{name}", b"1")
    pipe.execute()

    last_ts[name] = now_ts


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, )

