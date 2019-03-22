from algorithms.HGS.message import HGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter, DefaultIMGAMessageAdapter
from algorithms.NSGAII.message import NSGAIIIMGAMessageAdapter, NSGAIIHGSMessageAdapter
from algorithms.base.model import SubPopulation
from evotools.ea_utils import paretofront_layers


def JGBLIMGAMessageAdapter(driver):
    return NSGAIIIMGAMessageAdapter(driver)


def JGBLHGSMessageAdapter(driver):
    return NSGAIIHGSMessageAdapter(driver)
