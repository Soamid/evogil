from algorithms.HGS.distributed.message import HGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter
from algorithms.SMSEMOA.SMSEMOA import nd_sort
from algorithms.base.model import SubPopulation


class SMSEMOAIMGAMessageAdapter(IMGAMessageAdapter):
    def get_population(self):
        return self.driver.population

    def immigrate(self, migrants):
        for emigrant in migrants:
            self.driver.individuals.append(emigrant)

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


class SMSEMOAHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return self.driver.population

    def nominate_delegates(self):
        return [i.value for i in nd_sort(self.driver.individuals)[1]]

SMSEMOADHGSMessageAdapter = SMSEMOAHGSMessageAdapter