import os
import g
import server


class Console:
    def __init__(self):
        pass

    def print_logo(self):
        print("""CLoudify""")

    def update(self):
        # clear the console
        if g.OPERATING_SYSTEM == "Windows":
            os.system('cls')
        else:
            os.system('clear')

        self.print_logo()

        for log_item in server.logger.logs[10:]:
            if log_item['type'] == "plus":
                decoration = f"\u001b[32m[{log_item['formatted_time']}]\u001b[0m"
            elif log_item['type'] == "min":
                decoration = f"\u001b[31m[{log_item['formatted_time']}]\u001b[0m"
            else:
                decoration = f"[{log_item['formatted_time']}]"
            print(decoration, log_item['txt'])
