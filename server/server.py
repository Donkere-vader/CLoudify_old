from g import PARENT_FOLDER, PORT, HEADERSIZE, IP
import file_handling
import logger
import pickle
import socket
import threading
import os


class SendObject:
    """ Class used to store all data in that you want to send so that it can be converted to bytes by the pickle module """

    def __init__(self, type, info, file):
        self.type = type
        self.file = file
        self.info = info


class Server:
    def __init__(self):
        self.threads = []
        self.connections = []

        self.logger = logger.Logger()
        self.file_handling = file_handling.FileHandler(PARENT_FOLDER)

        self.logger.log("Starting...", type="plus")

        # start socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, PORT))
        self.sock.listen(5)

        self.logger.log(f"Server now online at ({socket.gethostbyname(socket.gethostname())}, {PORT})", type="plus")
        self.listen()

    def listen(self):
        while True:
            connection, address = self.sock.accept()

            self.logger.log(f"New connection from {address}", type="plus")

            self.connections.append(
                {
                    "connection":connection,
                    "address":address,
                    "device_ID":None
                }
            )

            # start a thread for this connection
            self.threads.append(
                threading.Thread(
                    target=self.handle_connection,
                    args=(connection, address)
                )
            )
            self.threads[-1].deamon = True
            self.threads[-1].start()

    def handle_connection(self, connection, address):
        new_data = True
        data_len = 0
        full_data = b""

        while True:
            data = connection.recv(HEADERSIZE)

            if data:
                if new_data:
                    new_data = False
                    data_len = int(data.decode("utf-8"))
                else:
                    full_data += data
                
                if len(full_data) >= data_len:
                    new_data = True

                    handle_data_thread = threading.Thread(
                        target=self.handle_data,
                        args=(full_data[:data_len], connection)
                    )
                    handle_data_thread.daemon = True
                    handle_data_thread.start()

                    full_data = full_data[data_len:]


    def handle_data(self, data, connection):
        data = pickle.loads(data)

        if data.type == 'file':
            self.create_path(data.info['path'])

            f = open(f"{PARENT_FOLDER}/{data.info['path']}/{data.info['name']}", "wb")
            f.write(data.file)
            f.close()

        elif data.type == 'file_req':
            self.send(
                type="file",
                connection=connection,
                file=open(
                    f"{PARENT_FOLDER}/{data.info['path']}/{data.info['name']}",
                    'rb'
                ).read(),
                path=data.info['path'],
                name=data.info['name']
            )
                

        elif data.type == 'updates':
            self.file_handling.file_update(data.info, data.device_ID)

        elif data.type == 'full_index':
            # to make a full sync and check everything TODO
            pass

    def create_path(self, path):
        """ Creates paths to files """
        path_list = path.split("/")
        done_path = PARENT_FOLDER + "/"

        for directory in path_list:
            try:
                os.mkdir(done_path + directory + "/")
            finally:
                done_path += directory + "/"

    def send(self, type, connection, file=None, **kwargs):
        """ Make a beautifull SendObject and convert it to bytes and send it to <connection> """

        data = SendObject(
            type=type,
            file=file,
            info=kwargs
        )

        bData = pickle.dumps(data)

        # Add the header
        header = bytes(str(len(bData)).ljust(HEADERSIZE), "utf-8")
        fullBData = header + bData

        self.logger.send(f"Sending {type} to {connection}", type="plus")

        connection.send(fullBData)

global SERVER
SERVER = Server()
