from g import PARENT_FOLDER, DB_NAME
import sqlite3
import os

def sql_ready(val: str):
    return val.replace("'", "''")

class FileHandler:
    def __init__(self, folder):
        self.parent_folder = folder

    def index(self, folder=None, path=None):
        """ Index the server files to know what files are there. """

        if not folder:
            folder = self.parent_folder

        if not path:
            path = folder

        try:
            items = os.listdir(folder)
        except PermissionError:
            return []

        files = []

        for i in items:  # i stands for item
            try:
                files += self.index(folder=path + "/" + i, path=path + "/" + i)
            except (NotADirectoryError, FileNotFoundError):
                f = {  # f stands for file
                    "name": i,
                    "path": path[len(self.parent_folder)+1:],  # + 1 for the first '/'
                    "last_changed": os.path.getmtime(path + "/" + i)
                }  # f stands for file
                files.append(f)

        return files

    def file_update(self, file_info, device_ID):
        db = sqlite3.connect(DB_NAME)

        if file_info['deleted']:
            file_on_server = True
            try:
                os.remove(
                    f"{PARENT_FOLDER}/{file_info['path']}/{file_info['name']}"
                )
            except FileNotFoundError:
                file_on_server = False
            
            if file_on_server:
                db.execute(f"UPDATE files SET deleted=true, last_changed={file_info['last_changed']} WHERE name={sql_ready(file_info['name'])} AND path={sql_ready(file_info['path'])};")
        
    

        db.commit()
        db.close()