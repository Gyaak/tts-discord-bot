from .worker import TTSWorker


def main() -> None:
    worker = TTSWorker()
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    main()
