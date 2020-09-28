import os

from dotenv import load_dotenv
from archivy import app


def main():
    load_dotenv()
    port = int(os.environ.get("ARCHIVY_PORT", 5000))
    app.run(host='0.0.0.0', port=port)
