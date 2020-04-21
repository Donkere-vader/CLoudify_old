class SendObject:
    """ Class used to store all data in that you want to send so that it can be converted to bytes by the pickle module """

    def __init__(self, type, info, file, device_ID=None):
        self.type = type
        self.file = file
        self.info = info
        self.device_ID = device_ID
