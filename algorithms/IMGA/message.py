from algorithms.base.model import PopulationMessageAdapter, SubPopulation


class IMGAMessageAdapter(PopulationMessageAdapter):

    def emigrate(self, migrants: SubPopulation):
        raise NotImplementedError

    def immigrate(self, migrants: SubPopulation):
        raise NotImplementedError


class DefaultIMGAMessageAdapter(IMGAMessageAdapter):

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