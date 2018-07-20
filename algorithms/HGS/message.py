from algorithms.base.model import PopulationMessageAdapter


class HGSMessageAdapter(PopulationMessageAdapter):

    def nominate_delegates(self):
        raise NotImplementedError

class DefaultHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        return [x.v for x in self.driver.front[1]]
