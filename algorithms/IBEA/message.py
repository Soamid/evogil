from algorithms.HGS.distributed.message import HGSMessageAdapter
from algorithms.IMGA.message import DefaultIMGAMessageAdapter
from evotools.ea_utils import paretofront_layers


def IBEAIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


class IBEAHGSMessageAdapter(HGSMessageAdapter):
    def get_population(self):
        return [x.v for x in self.driver.individuals]

    def nominate_delegates(self):
        return [
            x.v
            for x in list(
                paretofront_layers(
                    self.driver.individuals,
                    lambda indv: self.driver.calculate_objectives(indv),
                )
            )[0]
        ]
