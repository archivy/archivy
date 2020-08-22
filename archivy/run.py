from dotenv import load_dotenv

from archivy import app


def main():
    load_dotenv()
    app.run(host='0.0.0.0')
