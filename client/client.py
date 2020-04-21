from g import IP, PORT, PARENT_FOLDER, HEADERSIZE, DB_NAME, SYNC_TIME_OUT
import file_handling
import pickle
import os
import threading
import socket
import sqlite3
import send_object
import time

class Client:
    def __init__(self):
        self.parent_folder = PARENT_FOLDER
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_handling = file_handling.FileHandler(self.parent_folder)
        self.device_ID = None

        try:
            db = sqlite3.connect(DB_NAME)
            self.device_ID = db.execute("SELECT ID FROM device_ID;").fetchone()[0]
            db.close()
        except (sqlite3.OperationalError, TypeError):
            self.file_handling.first_time_setup()
            self.parent_folder = self.file_handling.parent_folder
            from g import IP

    def start(self):
        self.sock.connect((IP, PORT))
        if self.device_ID != None:
            self.send(
                type="device_ID",
                device_ID=self.device_ID
            )
        else:
            print(self.device_ID, "device_ID")
            self.send(type="device_ID_req")

        self.handle_connection()

    def handle_connection(self):
        new_data = True
        data_len = 0
        full_data = b""
        new = b""

        while True:
            data = self.sock.recv(HEADERSIZE)

            if data:
                if new_data:
                    new_data = False
                    if new:
                        data = new + data
                        full_data += data[20:]
                        new = b""
                    data_len = int(data[:20].decode("utf-8"))
                else:
                    full_data += data

                if len(full_data) >= data_len:
                    new_data = True

                    self.handle_data(full_data[:data_len])

                    new = full_data[data_len:]
                    full_data = b""

    def handle_data(self, data):
        data = pickle.loads(data)

        if data.type == 'file':
            self.create_path(data.info['path'])

            f = open(f"{self.parent_folder}/{data.info['path']}/{data.info['name']}", "wb")
            f.write(data.file)
            f.close()

            self.file_handling.get_file_info(path=data.info['path'], name=data.info['name'])

            # set last changed in file system
            os.utime(
                f"{self.parent_folder}/{data.info['path']}/{data.info['name']}",
                ns=(
                    0.0,
                    self.file_handling.get_file_info(path=data.info['path'], name=data.info['name'])['last_changed']
                )
            )

            self.file_handling.received_file(data.info['name'], data.info['path'])

        elif data.type == 'file_req':
            self.file_handling.file_requested(data.info)
            self.send(
                type="file",
                file=open(
                    f"{self.parent_folder}/{data.info['path']}/{data.info['name']}" if data.info['path'] else f"{self.parent_folder}/{data.info['name']}",
                    'rb'
                ).read(),
                path=data.info['path'],
                name=data.info['name']
            )

        elif data.type == "updates":
            for f in data.info['updates']:
                self.file_handling.file_update(f)

        elif data.type == "device_ID":
            self.device_ID = data.info['device_ID']

            db = sqlite3.connect(DB_NAME)
            db.execute(f"INSERT INTO device_ID (ID) VALUES ({self.device_ID});")
            db.commit()
            db.close()


    def create_path(self, path):
        """ Creates paths to files """
        path_list = path.split("/")
        done_path = self.parent_folder + "/"

        for directory in path_list:
            try:
                os.mkdir(done_path + directory + "/")
            except FileExistsError:
                done_path += directory + "/"

    def sync(self):
        """ Peform a synchronisation """

        files = self.file_handling.index()

        for f in files:
            self.file_handling.check_updated_file(f)

        self.file_handling.check_for_deleted()

        updates = self.file_handling.get_updates()

        if updates:
            print("updates:",updates)
            self.send(type="updates", updates=updates)

        req_files = self.file_handling.get_to_be_requested()
        
        if req_files:
            for f in req_files:
                self.send(type="file_req", name=f['name'], path=f['path'])

    def sync_loop(self):
        """ Synchronise now and then """

        while True:
            print("Sync loop")
            self.sync()
            time.sleep(SYNC_TIME_OUT)

    def send(self, type, file=None, **kwargs):
        """ Make a beautifull SendObject and convert it to bytes and send it to <connection> """

        data = send_object.SendObject(
            type=type,
            file=file,
            info=kwargs,
            device_ID=self.device_ID
        )

        bData = pickle.dumps(data)

        # Add the header
        header = bytes(str(len(bData)).ljust(HEADERSIZE), "utf-8")
        fullBData = header + bData

        # DEBUG
        print(f"Sending {type} to server")

        self.sock.send(fullBData)
