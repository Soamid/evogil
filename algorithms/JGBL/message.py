from algorithms.NSGAII.message import NSGAIIIMGAMessageAdapter, NSGAIIHGSMessageAdapter


def JGBLIMGAMessageAdapter(driver):
    return NSGAIIIMGAMessageAdapter(driver)


def JGBLHGSMessageAdapter(driver):
    return NSGAIIHGSMessageAdapter(driver)

JGBLDHGSMessageAdapter = JGBLHGSMessageAdapter