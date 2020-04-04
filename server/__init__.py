import server
import threading

SERVER = server.Server()

sync_loop_thread = threading.Thread(target=SERVER.sync_loop)
sync_loop_thread.daemon = True
sync_loop_thread.start()

SERVER.start()