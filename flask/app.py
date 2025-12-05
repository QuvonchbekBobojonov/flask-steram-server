from flask import Flask, Response, request, render_template
import redis
import time

app = Flask(__name__)

r = redis.Redis(host="redis", port=6379, decode_responses=False)
last_ts = {}

def feeder(name):
    pubsub = r.pubsub()
    pubsub.subscribe(f"notify:{name}")

    boundary = b"--frame\r\n"

    while True:
        msg = pubsub.get_message(timeout=2)

        if msg and msg['type'] == 'message':
            frame = r.get(f"frame:{name}")
            if frame:
                yield (
                    boundary +
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
                    frame + b"\r\n"
                )
        else:
            # nothing new → wait a bit
            time.sleep(0.01)


@app.post("/push/<name>")
def push(name):
    data = request.data
    if not data:
        return "no data", 400

    r.set(f"frame:{name}", data)
    now_ts = time.time()
    r.set(f"timestamp:{name}", now_ts)

    last_ts[name] = now_ts

    r.publish(f"notify:{name}", "new")

    return "OK", 200


@app.get("/<name>")
def view(name):
    return Response(
        feeder(name),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        direct_passthrough=True
    )


@app.get("/")
def grid():
    now = time.time()
    active = [n for n, t in last_ts.items() if now - t < 5]

    page = int(request.args.get("page", 1))
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page

    total_pages = (len(active) + per_page - 1)
    streams = active[start:end]

    return render_template("index.html", streams=streams, page=page, pages=total_pages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
