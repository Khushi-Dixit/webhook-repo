from flask import Flask, request, jsonify, render_template
from models import collection
from datetime import datetime, timedelta
from dateutil import tz

app = Flask(__name__)

def utc_now():
    """Return current UTC time"""
    return datetime.now(tz=tz.UTC)

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receives GitHub webhook events
    """
    payload = request.json
    event = request.headers.get("X-GitHub-Event")
    data = None

    if event == "push":
        branch = payload["ref"].split("/")[-1]
        data = {
            "request_id": payload["after"],
            "author": payload["pusher"]["name"],
            "action": "PUSH",
            "from_branch": branch,
            "to_branch": branch,
            "timestamp": utc_now(),
            "created_at": utc_now()
        }

    elif event == "pull_request":
        pr = payload["pull_request"]

        if payload["action"] == "closed" and pr["merged"]:
            data = {
                "request_id": str(pr["id"]),
                "author": pr["user"]["login"],
                "action": "MERGE",
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": utc_now(),
                "created_at": utc_now()
            }
        else:
            data = {
                "request_id": str(pr["id"]),
                "author": pr["user"]["login"],
                "action": "PULL_REQUEST",
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": utc_now(),
                "created_at": utc_now()
            }

    if data:
        collection.insert_one(data)

    return jsonify({"status": "success"}), 200

@app.route("/")
def ui():
    cutoff = datetime.utcnow() - timedelta(seconds=15)
    events = list(
        collection.find({"created_at": {"$gte": cutoff}})
        .sort("created_at", -1)
    )
    return render_template("index.html", events=events)

if __name__ == "__main__":
    app.run(debug=True)
