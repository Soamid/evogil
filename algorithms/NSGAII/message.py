from algorithms.HGS.message import HGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter
from algorithms.base.model import SubPopulation


class NSGAIIIMGAMessageAdapter(IMGAMessageAdapter):

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

class NSGAIIHGSMessageAdapter(HGSMessageAdapter):

    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        self.driver.finish()
        return [x.v for x in self.driver.front[1]]