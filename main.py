# app.py
from flask import Flask, Response, request, render_template
from threading import Condition
import time

app = Flask(__name__)

# stream storage: each stream has last_frame (bytes) and a Condition for notify
streams = {}

def ensure_stream(name):
    if name not in streams:
        streams[name] = {"frame": None, "cond": Condition(), "ts": 0.0}

def feeder(name):
    """Yield MJPEG frames; wait on condition to avoid busy loop."""
    boundary = b"--frame\r\n"
    ensure_stream(name)
    st = streams[name]
    while True:
        with st["cond"]:
            # wait until a new frame is available (or timeout)
            st["cond"].wait(timeout=2.0)
            frame = st["frame"]
        if frame:
            # Chrome-friendly headers with Content-Length
            yield (
                boundary +
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
                frame + b"\r\n"
            )
        else:
            # send a tiny keepalive to avoid client timeout (optional)
            time.sleep(0.01)

@app.route("/push/<name>", methods=["POST"])
def push(name):
    """Receive JPEG bytes (OpenCV push) and notify feeder."""
    ensure_stream(name)
    data = request.data
    if not data:
        return "no data", 400

    st = streams[name]
    with st["cond"]:
        st["frame"] = data
        st["ts"] = time.time()
        # notify all viewers waiting for new frame
        st["cond"].notify_all()
    return "OK", 200

@app.route("/<name>")
def view(name):
    ensure_stream(name)
    return Response(feeder(name),
                    mimetype="multipart/x-mixed-replace; boundary=frame",
                    direct_passthrough=True)

@app.route("/")
def grid():
    # only show streams that have frames recently (last 5s)
    active = [n for n, s in streams.items() if s.get("frame") and (time.time() - s.get("ts",0) < 5)]
    return render_template("grid.html", streams=active)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
