import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    server_url = os.getenv("RDS_SERVER_URL", "http://localhost:5000")
    return render_template("index.html", server_url=server_url)


def main():
    host = os.getenv("RDS_DASHBOARD_HOST", "127.0.0.1")
    port = int(os.getenv("RDS_DASHBOARD_PORT", "5001"))
    print(f"[RDS Dashboard] Starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
