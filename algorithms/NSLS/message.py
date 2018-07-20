from algorithms.HGS.message import HGSMessageAdapter, DefaultHGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter, DefaultIMGAMessageAdapter
from algorithms.base.model import SubPopulation


def NSLSIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


def NSLSHGSMessageAdapter(driver):
    return DefaultHGSMessageAdapter(driver)
