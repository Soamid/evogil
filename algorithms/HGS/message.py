from algorithms.base.model import PopulationMessageAdapter


class HGSMessageAdapter(PopulationMessageAdapter):

    def nominate_delegates(self):
        raise NotImplementedError
