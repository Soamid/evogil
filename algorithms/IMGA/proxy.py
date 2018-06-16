from algorithms.base.drivergen import ProgressDriverProxy


class IMGAMigrantProxy(ProgressDriverProxy):
    def __init__(self, migrants):
        self.migrants = migrants