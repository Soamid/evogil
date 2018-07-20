from algorithms.HGS.message import HGSMessageAdapter, DefaultHGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter, DefaultIMGAMessageAdapter
from algorithms.base.model import SubPopulation


# This template module for message.py modules used to combining MOEAs. Copy this module to your algorithm module
# and change Xxx to your algorithm name.
# Examples are provided for all supported multi-deme models. Feel free to add or use your own.

class XxxIMGAMessageAdapter(IMGAMessageAdapter):

    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def immigrate(self, migrants):
        self.driver.individuals.extend(migrants)

    def emigrate(self, migrants: SubPopulation):
        immigrants_cp = list(migrants)
        to_remove = []

        for p in self.driver.individuals:
            if p.v in immigrants_cp:
                to_remove.append(p)
                immigrants_cp.remove(p.v)

        for p in to_remove:
            self.driver.individuals.remove(p)
        return to_remove


class XxxHGSMessageAdapter(HGSMessageAdapter):

    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        self.driver.finish()
        return [x.v for x in self.driver.front[1]]

# You can also use default implementations instead. Remember *you have to* declare message adapter explicitly
# in your message.py if you want to enable hybridization, even if your algorithm meets default adapter's implementation
# criteria.
def XxxIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)

def XxxHGSMessageAdapter(driver):
    return DefaultHGSMessageAdapter(driver)
