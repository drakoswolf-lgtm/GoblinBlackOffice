"""Launch Ledgergut: python run_ledgergut.py"""

import os

from app.ledgergut.web import app

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true"}
    app.run(debug=debug, host="127.0.0.1", port=5000)
