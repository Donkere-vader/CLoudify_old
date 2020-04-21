from g import OPERATING_SYSTEM
import os
from colorama import Fore, Back, Style


class Console:
    def __init__(self):
        self.percentage: int = 0
        self.load_bar_txt = ""

    def print_logo(self):
        print("""\u001b[31m ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗███████╗██╗   ██╗
██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██║██╔════╝╚██╗ ██╔╝
██║     ██║     ██║   ██║██║   ██║██║  ██║██║█████╗   ╚████╔╝ 
██║     ██║     ██║   ██║██║   ██║██║  ██║██║██╔══╝    ╚██╔╝  
╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝██║██║        ██║   
 ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝        ╚═╝   
\u001b[0m\t\tCLSoftSolutions (C)""")

    def update(self, logs=None):
        # clear the console
        if OPERATING_SYSTEM == "Windows":
            os.system('cls')
        else:
            os.system('clear')

        self.print_logo()
        print()

        for log_item in logs[-50:]:
            if log_item['type'] == "plus":
                decoration = Fore.BLACK + Back.GREEN + f"[{log_item['formatted_time']}]" + Style.RESET_ALL
            elif log_item['type'] == "min":
                decoration = Fore.BLACK + Back.RED + f"[{log_item['formatted_time']}]" + Style.RESET_ALL
            else:
                decoration = f"[{log_item['formatted_time']}]"
            print(decoration, log_item['txt'])

        if self.percentage > 0 and self.percentage < 100:
            print(Style.BRIGHT + self.load_bar_txt + Style.RESET_ALL)
            print(f"{Fore.BLACK + Back.GREEN}PROGRESS [{Fore.BLACK + Back.GREEN}{ '#'*self.percentage }{Style.RESET_ALL}{ ' '*(100-self.percentage) }]")

    def load_bar(self, cur_val, max_val, txt):
        self.load_bar_txt = txt
        new_p = cur_val // max_val 
        if new_p > self.percentage:
            self.percentage
