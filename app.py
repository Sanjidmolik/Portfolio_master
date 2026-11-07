"""Entry point.

Development:  flask --app app run --debug
Production:   gunicorn "app:app"   (or: waitress-serve --call app:create_app)
"""
import os

from portfolio import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
