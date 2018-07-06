from algorithms.base.model import PopulationMessageAdapter, SubPopulation


class IMGAMessageAdapter(PopulationMessageAdapter):

    def emigrate(self, migrants: SubPopulation):
        raise NotImplementedError

    def immigrate(self, migrants: SubPopulation):
        raise NotImplementedError