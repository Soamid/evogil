from algorithms.HGS.message import HGSMessageAdapter, DefaultHGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter, DefaultIMGAMessageAdapter
from algorithms.base.model import SubPopulation


def NSGAIIIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


class NSGAIIHGSMessageAdapter(DefaultHGSMessageAdapter):
    def nominate_delegates(self):
        self.driver.finish()
        return super().nominate_delegates()
