from algorithms.HGS.distributed.message import HGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter
from algorithms.base.model import SubPopulation


class SPEA2IMGAMessageAdapter(IMGAMessageAdapter):
    def get_population(self):
        return self.driver.population

    def immigrate(self, migrants):
        self.driver.individuals.extend(migrants)

    def emigrate(self, migrants: SubPopulation):
        immigrants_cp = list(migrants)
        to_remove = []

        for p in self.driver.individuals:
            if p["value"] in immigrants_cp:
                to_remove.append(p)
                immigrants_cp.remove(p["value"])

        for p in to_remove:
            self.driver.individuals.remove(p)
        return to_remove


class SPEA2HGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return self.driver.population

    def nominate_delegates(self):
        return [x["value"] for x in self.driver.archive]
