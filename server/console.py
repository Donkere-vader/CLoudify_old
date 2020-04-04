from g import OPERATING_SYSTEM
import os
import server


class Console:
    def __init__(self):
        pass

    def print_logo(self):
        print("""\u001b[31m ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗███████╗██╗   ██╗
██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██║██╔════╝╚██╗ ██╔╝
██║     ██║     ██║   ██║██║   ██║██║  ██║██║█████╗   ╚████╔╝ 
██║     ██║     ██║   ██║██║   ██║██║  ██║██║██╔══╝    ╚██╔╝  
╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝██║██║        ██║   
 ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝        ╚═╝   
\u001b[0m\t\tCLSoftSolutions (C)""")

    def update(self, logs):
        # clear the console
        if OPERATING_SYSTEM == "Windows":
            os.system('cls')
        else:
            os.system('clear')

        self.print_logo()
        print()

        for log_item in logs[-10:]:
            if log_item['type'] == "plus":
                decoration = f"\u001b[32m[{log_item['formatted_time']}]\u001b[0m"
            elif log_item['type'] == "min":
                decoration = f"\u001b[31m[{log_item['formatted_time']}]\u001b[0m"
            else:
                decoration = f"[{log_item['formatted_time']}]"
            print(decoration, log_item['txt'])