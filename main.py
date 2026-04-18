import uvicorn
from api.main import app
from utils.logging_config import setup_logging


def main():
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
