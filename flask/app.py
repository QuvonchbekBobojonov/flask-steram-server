from flask import Flask, Response, request, render_template, jsonify
import redis
import time

app = Flask(__name__)

r = redis.Redis(host="redis", port=6379, decode_responses=False)
last_ts = {}
FRAME_TTL = 5


def feeder(name):
    pubsub = r.pubsub()
    pubsub.subscribe(f"notify:{name}")

    try:
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
        # client disconnected
        pass
    finally:
        pubsub.close()


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


@app.get("/<string:name>")
def view(name):
    return Response(
        feeder(name),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        direct_passthrough=True
    )


@app.get("/")
def index():
    now = time.time()
    active = [n for n, t in last_ts.items() if now - t < FRAME_TTL]
    return render_template("index.html", streams=active)


@app.get("/update")
def update():
    now = time.time()
    active = [n for n, t in last_ts.items() if now - t < FRAME_TTL]
    return jsonify(active)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
