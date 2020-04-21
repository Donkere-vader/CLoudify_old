import json
# file for handling all the global variables

try:
    config_file = json.load(open("config.json"))
except FileNotFoundError:
    config_json = {
        "parent_folder": "",
        "server_ip": ""
    }
    json.dump(config_json, open("config.json", "w"))
    config_file = json.load(open("config.json"))


# FILE HANDLING
DB_NAME = 'db.sqlite3'
PARENT_FOLDER = config_file['parent_folder']

# SOCKET
IP = config_file['server_ip']
PORT = 42069 # ;)
HEADERSIZE = 20

# SERVER
SYNC_TIME_OUT = 5 # seconds

# OPERATING SYSTEM
OPERATING_SYSTEM = "Windows" # 'Windows', 'Linux' or 'Mac'
