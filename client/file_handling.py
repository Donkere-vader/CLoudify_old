from g import DB_NAME
import sqlite3
import os
import json


def sql_ready(val: str):
    return val.replace("'", "''")


class FileHandler:
    def __init__(self, folder):
        self.parent_folder = folder

    def first_time_setup(self):
        db = sqlite3.connect(DB_NAME)
        db.execute('CREATE TABLE IF NOT EXISTS "files" ("ID"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,"name"	STRING NOT NULL,"path"	STRING,"updated"	BOOLEAN NOT NULL DEFAULT (true),"deleted"	BOOLEAN NOT NULL DEFAULT (false),"on_system"	BOOLEAN NOT NULL DEFAULT (true),"last_changed"	float NOT NULL);')
        db.execute('CREATE TABLE IF NOT EXISTS "device_ID" ("ID"	INTEGER,PRIMARY KEY("ID"));')
        db.commit()
        db.close()

        if not self.parent_folder:
            from tkinter import filedialog, Tk, messagebox, simpledialog
            root = Tk()
            root.withdraw()
            messagebox.showinfo("First time setup", "Please select a folder to sync with the server.")
            self.parent_folder = filedialog.askdirectory()

            config_file = json.load(open('config.json'))
            config_file['parent_folder'] = self.parent_folder
            config_file['server_ip'] = simpledialog.askstring("Server IP", "Please enter the server IP adress")

            json.dump(config_file, open("config.json", "w"))

        
        try:
            os.mkdir(self.parent_folder)
        except FileExistsError:
            pass

    def index(self, folder=None):
        """ Indexes the file system and updates the DB accordingly """

        if not folder:
            folder = self.parent_folder

        files = []

        try:
            items = os.listdir(folder)
        except PermissionError:
            return []

        for i in items:
            try:
                files += self.index(folder + "/" + i)
            except (NotADirectoryError, FileNotFoundError):
                f = {
                    "name": i,
                    "path": folder[len(self.parent_folder)+1:],
                    "last_changed": os.path.getmtime(folder + "/" + i)
                }
                files.append(f)

        return files

    def check_updated_file(self, file):
        """ Checks if a file is updated or new """
        db = sqlite3.connect(DB_NAME)

        crsr = db.execute(f"SELECT name, path, last_changed FROM files WHERE name='{sql_ready(file['name'])}' AND path='{sql_ready(file['path'])}';").fetchone()

        if not crsr:
            # new file
            db.execute(f"INSERT INTO files (name, path, last_changed) VALUES ('{sql_ready(file['name'])}', '{sql_ready(file['path'])}', {file['last_changed']});")
        else:
            # updated file
            if file['last_changed'] > crsr[2]:
                db.execute(f"UPDATE files SET last_changed={file['last_changed']}, updated=true, deleted=false WHERE name='{sql_ready(file['name'])}' AND path='{sql_ready(file['path'])}';")

        db.commit()
        db.close()

    def check_for_deleted(self):
        """ Checks if there where any files deleted """
        db = sqlite3.connect(DB_NAME)

        for f in db.execute("SELECT ID, name, path FROM files WHERE on_system=true;").fetchall():
            if not os.path.isfile(self.parent_folder + "/" +  f[2] + f[1]):
                db.execute(f"UPDATE files SET deleted=true WHERE ID={f[0]};")

        db.commit()
        db.close()

    def received_file(self, name, path):
        db = sqlite3.connect(DB_NAME)

        db.execute(f"UPDATE files SET on_system=true WHERE name='{sql_ready(name)}' AND path='{sql_ready(path)}';")

        db.commit()
        db.close()

    def file_update(self, file_info):
        db = sqlite3.connect(DB_NAME)

        if file_info['deleted']:
            # remove the file
            try:
                os.remove(
                    f"{self.parent_folder}/{file_info['path']}/{file_info['name']}"
                )
            except FileNotFoundError: # file was never on the system
                db.close()
                return
            
            db.execute(f"DELETE FROM files WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")


        else:
            file_on_system = db.execute(f"SELECT last_changed FROM files WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';").fetchone()
            
            if file_on_system and file_on_system[0] < file_info['last_changed']:
                # the file is updated
                db.execute(f"UPDATE files SET on_system=false, deleted=false WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")

            elif not file_on_system:
                # it's a new file
                db.execute(f"INSERT INTO files (name, path, last_changed, updated, on_system) VALUES ('{sql_ready(file_info['name'])}', '{sql_ready(file_info['path'])}', {file_info['last_changed']}, false, false);")

            else:
                db.close()
                return

        
        file_ID = db.execute(f"SELECT ID FROM files  WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';").fetchone()[0]

        db.execute(f"UPDATE files SET last_changed={file_info['last_changed']} WHERE ID={file_ID};")

        db.commit()
        db.close()

    def file_requested(self, file_info):
        db = sqlite3.connect(DB_NAME)

        db.execute(f"UPDATE files SET updated=false WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")

        db.commit()
        db.close()

    def deleted_update_send(self, file_info):
        db = sqlite3.connect(DB_NAME)

        db.execute("DELETE FROM files WHERE name='{sql_ready(file_info['name'])}' AND path='{sql_ready(file_info['path'])}';")

        db.commit()
        db.close()

    def get_updates(self):
        db = sqlite3.connect(DB_NAME)

        updates = []

        files = db.execute("SELECT ID, name, path, last_changed, updated, deleted FROM files;").fetchall()

        for f in files:
            if f[4] or f[5]:
                updates.append(
                    {
                        "name":f[1],
                        "path":f[2],
                        "last_changed":f[3],
                        "deleted": f[5]
                    }
                )

        return updates

    def get_to_be_requested(self):
        db = sqlite3.connect(DB_NAME)

        req_files = []

        crsr = db.execute("SELECT name, path FROM files WHERE on_system=false;").fetchall()

        for i in crsr:
            req_files.append(
                {
                    "name": i[0],
                    "path": i[1]
                }
            )

        return req_files

    def get_file_info(self, path, name):
        db = sqlite3.connect(DB_NAME)

        crsr = db.execute(f"SELECT ID, last_changed, deleted, on_system, updated FROM files WHERE path='{path}' AND name='{name}';").fetchone()

        f = {
            "ID": crsr[0],
            "last_changed": crsr[1],
            "deleted": crsr[2],
            "on_system": crsr[3],
            "updated": crsr[4]
        }

        db.close()
        return f