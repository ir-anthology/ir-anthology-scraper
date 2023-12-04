from datetime import datetime
from os import makedirs
from os.path import exists, sep

class Logger:

    def __init__(self, output_directory):
        now = datetime.now()
        self.timestamp = (str(now.year) + "_" + str(now.month) + "_" + (str(now.day).rjust(2,"0")) + "_" +
                          str(now.hour) + "_" + str(now.minute) + "_" + (str(now.second).rjust(2,"0")))
        self.logger_directory = output_directory + sep + "_logs" + sep + self.timestamp
        if output_directory and not exists(self.logger_directory):
            makedirs(self.logger_directory)

    def log(self, message):
        with open(self.logger_directory + sep + "log.txt", "a") as file:
            file.write(message + "\n")