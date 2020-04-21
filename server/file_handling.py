from g import DB_NAME
import sqlite3
import os

def sql_ready(val: str):
    return val.replace("'", "''")

class FileHandler:
    def __init__(self, folder):
        self.parent_folder = folder

    def to_be_requested_files(self):
        db = sqlite3.connect(DB_NAME)
        files = []

        for f in db.execute(f"SELECT name, path, origin FROM files WHERE file_on_server=false;").fetchall():
            files.append(
                {
                    "name":f[0],
                    "path":f[1],
                    "origin":f[2]
                }
            )

        db.close()
        return files

    def received_file(self, name, path):
        db = sqlite3.connect(DB_NAME)

        db.execute(f"UPDATE files SET file_on_server=true WHERE name='{sql_ready(name)}' AND path='{sql_ready(path)}';")

        db.commit()
        db.close()

    def file_update(self, file_info, device_ID):
        db = sqlite3.connect(DB_NAME)

        if file_info['deleted']:
            # remove the file
            try:
                os.remove(
                    f"{self.parent_folder}/{file_info['path']}/{file_info['name']}"
                )
            except FileNotFoundError: # file was never on the server
                db.close()
                return
            
            db.execute(f"UPDATE files SET deleted=true WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")

        else:
            file_on_server = db.execute(f"SELECT last_changed FROM files WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';").fetchone()
            
            if file_on_server and file_on_server[0] < file_info['last_changed']:
                # the file is updated
                db.execute(f"UPDATE files SET file_on_server=false, deleted=false, origin={device_ID} WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")

            elif not file_on_server:
                # it's a new file
                db.execute(f"INSERT INTO files (name, path, last_changed, origin) VALUES ('{sql_ready(file_info['name'])}', '{sql_ready(file_info['path'])}', {file_info['last_changed']}, {device_ID});")

                file_ID = db.execute(f"SELECT ID FROM files  WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';").fetchone()[0]

                for crsr in db.execute(f"SELECT ID FROM device_IDs;").fetchall():
                    db.execute(f"INSERT INTO device_knows_files (file_ID, last_changed, device_ID) VALUES ({file_ID}, 0.0, {crsr[0]});")
                    
            else:
                db.close()
                return

        file_ID = db.execute(f"SELECT ID FROM files  WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';").fetchone()[0]

        db.execute(f"UPDATE files SET last_changed={file_info['last_changed']} WHERE ID={file_ID};")
        db.execute(f"UPDATE device_knows_files SET last_changed={file_info['last_changed']} WHERE device_ID={device_ID} AND file_ID={file_ID};")
    

        db.commit()
        db.close()

    def get_updates(self, device_ID):
        db = sqlite3.connect(DB_NAME)

        updates = []

        files = db.execute("SELECT ID, name, path, last_changed, deleted FROM files;").fetchall()

        for f in files:
            device_knows = db.execute(f"SELECT last_changed FROM device_knows_files WHERE file_ID={f[0]} AND device_ID={device_ID};").fetchone()


            if device_knows[0] < f[3]:
                db.execute(f"UPDATE device_knows_files SET last_changed={f[3]} WHERE file_ID={f[0]};")
                updates.append({
                    "name":f[1],
                    "path":f[2],
                    "last_changed":f[3],
                    "deleted":f[4]
                }) 

        return updates

    def new_device(self):
        db = sqlite3.connect(DB_NAME)

        id = 0

        while db.execute(f"SELECT ID FROM device_IDs WHERE ID={id};").fetchone():
            id += 1

        db.execute(f"INSERT INTO device_IDs (ID) VALUES ({id});")

        for f in db.execute("SELECT ID, last_changed FROM files;").fetchall():
            db.execute(f"INSERT INTO device_knows_files (file_ID, device_ID, last_changed) VALUES ({f[0]}, {id}, 0);")

        db.commit()
        db.close()
        return id