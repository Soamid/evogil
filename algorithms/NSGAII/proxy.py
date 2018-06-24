from algorithms.IMGA.proxy import IMGAMessageAdapter
from algorithms.NSGAII import NSGAII
from algorithms.base.model import PopulationMessage, SubPopulation


class ImgaProxyAdapter(IMGAMessageAdapter):

    def emit_proxy(self):
        return PopulationMessage([x.v for x in self.driver.individuals])

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
