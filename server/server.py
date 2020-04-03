import file_handling
import logger


# GLOBALS
PORT = 42069  # ;)


class Server:
    def __init__(self):
        self.logger = logger.Logger()

    def send(self, file, **kwargs):
        pass


if __name__ == "__main__":
    global SERVER
    SERVER = Server()
