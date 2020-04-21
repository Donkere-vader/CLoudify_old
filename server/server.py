from g import PARENT_FOLDER, PORT, HEADERSIZE, IP, DB_NAME, SYNC_TIME_OUT
import file_handling
import logger
import pickle
import socket
import threading
import os
import time
import send_object
import console


class Server:
    def __init__(self):
        self.threads = []
        self.connections = []

        # detect if database exists
        if not os.path.isfile(DB_NAME):
            import sqlite3

            # create the new database
            db = sqlite3.connect(DB_NAME)

            # create all the tables
            db.execute("CREATE TABLE device_IDs (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE);")
            db.execute("CREATE TABLE device_knows_files (file_ID      INTEGER REFERENCES files (ID) ON DELETE CASCADE NOT NULL,device_ID    STRING  NOT NULL REFERENCES device_IDs (ID),last_changed FLOAT   NOT NULL DEFAULT 0);")
            db.execute("CREATE TABLE files (ID             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,name           STRING  NOT NULL,path           STRING,last_changed   FLOAT   NOT NULL DEFAULT 0,deleted        BOOLEAN NOT NULL DEFAULT false,file_on_server BOOLEAN NOT NULL DEFAULT (false),origin         INTEGER NOT NULL);")

            db.commit()
            db.close()

        # detect if the folder exists
        if not os.path.exists(PARENT_FOLDER):
            # create the folder
            os.mkdir(PARENT_FOLDER)

        self.console = console.Console()
        self.logger = logger.Logger("server.log", console=self.console)
        self.file_handling = file_handling.FileHandler(PARENT_FOLDER)

        self.logger.log("Starting...", type="plus")

        # start socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((IP, PORT))
        self.sock.listen(5)

        self.logger.log(f"Server now online at ({socket.gethostbyname(socket.gethostname())}, {PORT})", type="plus")

    def start(self):
        while True:
            connection, address = self.sock.accept()

            self.logger.log(f"New connection from {address}", type="plus")

            self.connections.append(
                {
                    "connection": connection,
                    "address": address,
                    "device_ID": None
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
        new = b""

        while True:
            try:
                data = connection.recv(10024)
            except (ConnectionResetError, ConnectionAbortedError):
                self.logger.log(f"Lost connection with {address}", type="min")
                for i in range(len(self.connections)):
                    self.logger.log(
                        self.connections[i]['address'], type(self.connections[i]['address'])
                    )
                    self.logger.log(
                        address, type(address)
                    )
                    if self.connections[i]['address'] == address:
                        del self.connections[i]
                    break
                break

            if data != b"":
                if new_data:
                    new_data = False
                    if new != b"":
                        data = new + data
                        new = b""
                    data_len = int(data[:HEADERSIZE].decode("utf-8"))
                    full_data += data[HEADERSIZE:]
                else:
                    full_data += data

                self.console.load_bar(len(full_data), data_len, txt="RECEIVING DATA")
                if len(full_data) >= data_len:
                    new_data = True

                    self.handle_data(full_data[:data_len], connection, address)

                    new = full_data[data_len:]
                    full_data = b""

    def handle_data(self, data, connection, address):
        while True:
            try:
                data = pickle.loads(data)
                break
            except pickle.UnpicklingError as e:
                self.logger.log(f"Pickle loads error {e}  |  Retrying..", type="min")

        self.logger.log(f"Incomming {data.type}", type="plus")

        if data.type == 'file':
            self.create_path(data.info['path'])

            f = open(f"{PARENT_FOLDER}/{data.info['path']}/{data.info['name']}", "wb")
            f.write(data.file)
            f.close()
            self.file_handling.received_file(data.info['name'], data.info['path'])

            self.logger.log(f"Received file: {data.info['path']}/{data.info['name']} succesfully", type="plus")

        elif data.type == 'file_req':
            try:
                self.send(
                    type="file",
                    connection=connection,
                    file=open(
                        f"{PARENT_FOLDER}/{data.info['path']}/{data.info['name']}".replace("//","/"),
                        'rb'
                    ).read(),
                    path=data.info['path'],
                    name=data.info['name']
                )
            except FileNotFoundError:
                self.logger.log(f"Requested file { (PARENT_FOLDER + '/' + data.info['path'] + '/' + data.info['name']).replace('//','/') }. But file not on server system.", type="min")

        elif data.type == 'updates':
            for f in data.info['updates']:
                self.file_handling.file_update(f, data.device_ID)

        elif data.type == "device_ID":
            for i in range(len(self.connections)):
                if self.connections[i]['address'] == address:
                    self.connections[i]['device_ID'] = data.info['device_ID']
                    break

        elif data.type == "device_ID_req":
            new_ID = self.file_handling.new_device()

            for i in range(len(self.connections)):
                if self.connections[i]['address'] == address:
                    self.connections[i]['device_ID'] = new_ID
                    break
                
            self.send(type="device_ID", connection=connection, device_ID=new_ID)

    def create_path(self, path):
        """ Creates paths to files """
        path_list = path.split("/")
        done_path = PARENT_FOLDER

        for directory in path_list:
            try:
                os.mkdir(done_path + "/" + directory + "/")
            except FileExistsError:
                pass
            done_path += directory

    def get_connection_by_device_ID(self, device_ID):
        """ Get the connection of by a device_ID """

        for c in self.connections:
            if c['device_ID'] == device_ID:
                return c
        return None

    def sync_server(self):
        """ Peform a synchronisation """

        files = self.file_handling.to_be_requested_files()
        
        for f in files:
            connection = self.get_connection_by_device_ID(f['origin'])

            if connection:
                connection = connection['connection']
                self.send(
                    type="file_req",
                    name=f['name'],
                    path=f['path'],
                    connection=connection
                )

        # DEBUG
        self.logger.log("-----")
        for c in self.connections:
            # DEBUG
            self.logger.log(c)
            if c['device_ID']:
                updates = self.file_handling.get_updates(c['device_ID'])
                
                if updates:
                    self.logger.log(f"updates: {updates}")
                    self.send(type="updates", updates=updates, connection=c['connection'])
                
                self.logger.log("")

    def sync_loop(self):
        """ Check all files now and then """

        while True:
            self.sync_server()
            time.sleep(SYNC_TIME_OUT)

    def send(self, type, connection, file=None, **kwargs):
        """ Make a beautifull SendObject and convert it to bytes and send it to <connection> """

        data = send_object.SendObject(
            type=type,
            file=file,
            info=kwargs
        )

        bData = pickle.dumps(data)

        # Add the header
        header = bytes(str(len(bData)).ljust(HEADERSIZE), "utf-8")
        fullBData = header + bData

        self.logger.log(f"Sending {type}", type="plus")

        connection.send(fullBData)
