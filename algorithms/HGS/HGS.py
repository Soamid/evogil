import logging

import numpy as np

from algorithms.HGS.classic.ClassicHGS import ClassicHGS
from algorithms.HGS.distributed.DistributedHGS import DistributedHGS
from algorithms.base.driver import ComplexDriver

EPSILON = np.finfo(float).eps

logger = logging.getLogger(__name__)


class HGS(ComplexDriver):
    def __init__(
        self,
        population,
        dims,
        fitnesses,
        fitness_errors,
        cost_modifiers,
        driver,
        mutation_etas,
        crossover_etas,
        mutation_rates,
        crossover_rates,
        reference_point,
        mantissa_bits,
        min_progress_ratio,
        metaepoch_len=5,
        max_level=2,
        max_sprouts_no=20,
        sproutiveness=1,
        comparison_multipliers=(1.0, 0.1, 0.01),
        population_sizes=(64, 16, 4),
        hgs_type="classic",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if hgs_type == "distributed":
            algorithm = DistributedHGS
        else:
            algorithm = ClassicHGS

        self.hgs = algorithm(
            population,
            dims,
            fitnesses,
            fitness_errors,
            cost_modifiers,
            driver,
            mutation_etas,
            crossover_etas,
            mutation_rates,
            crossover_rates,
            reference_point,
            mantissa_bits,
            min_progress_ratio,
            metaepoch_len,
            max_level,
            max_sprouts_no,
            sproutiveness,
            comparison_multipliers,
            population_sizes,
            *args,
            **kwargs,
        )

    def shutdown(self):
        self.hgs.shutdown()

    def finalized_population(self):
        return self.hgs.finalized_population()

    def step(self):
        self.hgs.step()
        self.cost = self.hgs.cost
