from algorithms.HGS.distributed.message import DefaultHGSMessageAdapter
from algorithms.IMGA.message import DefaultIMGAMessageAdapter


def NSGAIIIIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


def NSGAIIIHGSMessageAdapter(driver):
    return DefaultHGSMessageAdapter(driver)
