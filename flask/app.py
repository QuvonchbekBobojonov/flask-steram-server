from flask import Flask, render_template, jsonify, request, session
from livekit import api
import time

app = Flask(__name__)
app.secret_key = "fdjgbfdkgjbdfjgbjdgdfgdfsg"

ADMIN_PASSWORD = "moorfo"

LIVEKIT_URL = "wss://ic3-o2itc2nx.livekit.cloud"
LIVEKIT_API_KEY = "API4KJnqvB4ggR6"
LIVEKIT_API_SECRET = "88dkD9EwafTA20mYmFOn8q7sl9FSCMBJc0wGBjYHa1N"
ROOM = "exam"

last_seen = {}

def unique_username(name):
    if name not in last_seen:
        return name

    i = 1
    while f"{name}_{i}" in last_seen:
        i += 1
    return f"{name}_{i}"


@app.post("/auth")
def auth():
    if request.get_json(force=True).get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify(ok=True)
    return jsonify(ok=False), 401

@app.get("/token/<string:username>")
def token(username):
    uname = unique_username(username)
    last_seen[uname] = time.time()

    at = api.AccessToken(
        LIVEKIT_API_KEY,
        LIVEKIT_API_SECRET
    ).with_identity(uname).with_grants(
        api.VideoGrants(
            room_join=True,
            room=ROOM_NAME
        )
    )

    return jsonify(
        token=at.to_jwt(),
        url=LIVEKIT_URL,
        room=ROOM_NAME,
        identity=uname
    )


@app.get("/update")
def update():
    if not session.get("admin"):
        return jsonify([]), 403
    now = time.time()
    return jsonify([u for u, t in last_seen.items() if now - t < 10])

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/test-camera")
def test_camera():
    return render_template("test-camera.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
