from algorithms.HGS.distributed.message import DefaultHGSMessageAdapter
from algorithms.IMGA.message import DefaultIMGAMessageAdapter


def NSGAIIIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


class NSGAIIHGSMessageAdapter(DefaultHGSMessageAdapter):
    def nominate_delegates(self):
        self.driver.shutdown()
        return super().nominate_delegates()


NSGAIIDHGSMessageAdapter = NSGAIIHGSMessageAdapter
