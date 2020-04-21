import client
import threading

CLIENT = client.Client()

sync_loop_thread = threading.Thread(target=CLIENT.sync_loop)
sync_loop_thread.daemon = True
sync_loop_thread.start()

CLIENT.start()