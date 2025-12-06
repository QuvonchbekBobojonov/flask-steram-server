from flask import Flask, render_template
import requests

app = Flask(__name__)

MEDIAMTX_API = "http://mediamtx:9997/v3/paths/list"

@app.route("/")
def grid():
    try:
        resp = requests.get(MEDIAMTX_API, timeout=2)
        data = resp.json()
    except Exception:
        data = {"items": []}

    # faqat active (ready) roomlar
    streams = [
        item["name"]
        for item in data.get("items", [])
        if item.get("ready")
    ]

    return render_template("index.html", streams=streams)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
