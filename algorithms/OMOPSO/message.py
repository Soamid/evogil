from algorithms.HGS.distributed.message import HGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter
from algorithms.base.model import SubPopulation


class OMOPSOIMGAMessageAdapter(IMGAMessageAdapter):
    def get_population(self):
        return [x.value for x in self.driver.individuals]

    def immigrate(self, migrants):
        for migrant in migrants:
            migrant.reset_speed()
            self.driver.individuals.append(migrant)

    def emigrate(self, migrants: SubPopulation):
        immigrants_cp = list(migrants)
        to_remove = []

        for p in self.driver.individuals:
            if p.value in immigrants_cp:
                to_remove.append(p)
                immigrants_cp.remove(p.value)

        for p in to_remove:
            self.driver.individuals.remove(p)
        return to_remove


class OMOPSOHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return self.driver.population

    def nominate_delegates(self):
        return self.get_population()
