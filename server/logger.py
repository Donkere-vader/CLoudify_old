import console
import datetime


class Logger:
    def __init__(self):
        self.logs = []
        self.log_file_name = "server.log"
        self.console = console.Console()

    def get_formatted_time(self):
        """ Returns the current time for use in the .log and console in day/month/year hour:minute.second format"""
        dttm = datetime.datetime.now()
        return f"{dttm.day}/{dttm.month}/{dttm.year} {dttm.hour}:{dttm.minute}.{dttm.second}"

    def log(self, txt: str, type: str = None):
        """ Log events to console and the .log file """

        formatted_time = self.get_formatted_time()

        self.logs.append({
            "txt": txt,
            "type": type,
            "formatted_time": formatted_time
        })

        # keep a log
        log_file = open(self.log_file_name, 'a')
        log_file.write(f"[{formatted_time}] {str(txt)}\n")
        log_file.close()

        self.console.update()
