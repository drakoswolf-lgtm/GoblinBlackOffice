"""Run the shared Goblin Black Office application locally."""

from werkzeug.serving import run_simple

from app.office.web import application


if __name__ == "__main__":
    run_simple("127.0.0.1", 5000, application, use_reloader=True)
