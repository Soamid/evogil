from algorithms.HGS.distributed.message import DefaultHGSMessageAdapter
from algorithms.IMGA.message import DefaultIMGAMessageAdapter


def NSLSIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


def NSLSHGSMessageAdapter(driver):
    return DefaultHGSMessageAdapter(driver)
