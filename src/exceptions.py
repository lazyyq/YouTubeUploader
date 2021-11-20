class DailyUploadLimitReachedException(Exception):
    def __init(self):
        super().__init__('Daily upload limit has been reached. Try again later.')
