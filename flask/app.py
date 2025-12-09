from flask import Flask, render_template, jsonify, request, session
from livekit import AccessToken, VideoGrants
import time

app = Flask(__name__)
app.secret_key = "q=lA=VS@Z`:@%El;Y*e**sL:w&Z?["

ADMIN_PASSWORD = "moorfo_12345"

LIVEKIT_URL = "ws://livekit:7880"
LIVEKIT_API_KEY = "API4KJnqvB4ggR6"
LIVEKIT_API_SECRET = "88dkD9EwafTA20mYmFOn8q7sl9FSCMBJc0wGBjYHa1N"
ROOM = "exam"

last_seen = {}

@app.post("/auth")
def auth():
    if request.get_json().get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify(ok=True)
    return jsonify(ok=False), 401

@app.get("/token/<username>")
def token(username):
    last_seen[username] = time.time()
    at = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(username)
        .with_grants(VideoGrants(room_join=True, room=ROOM))
    )
    return jsonify(token=at.to_jwt(), url=LIVEKIT_URL, room=ROOM)

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

app.run(host="0.0.0.0", port=8000)
