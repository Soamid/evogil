import pickle
from contextlib import suppress
from pathlib import Path

from simulation.factory import SimulationCase


class Result:
    def __init__(self, population, population_fitnesses, **additional_data):
        self.population = population
        self.fitnesses = population_fitnesses
        self.additional_data = additional_data


class Serializer:
    def __init__(self, simulation_case: SimulationCase):
        self.path = Path(simulation_case.results_dir, simulation_case.problem_name, simulation_case.algorithm_name,
                         simulation_case.id)

    def store(self, result: Result, file_name: str) -> Path:
        with suppress(FileExistsError):
            self.path.mkdir(parents=True)

        store_path = self._get_result_path(file_name)
        with store_path.open(mode='wb') as fh:
            pickle.dump(result, fh)
        return store_path

    def _get_result_path(self, file_name) -> Path:
        return self.path / f"{file_name}.pickle"

    def load(self, file_name) -> Result:
        load_path = self._get_result_path(file_name)
        with load_path.open(mode='rb') as fh:
            result = pickle.load(fh)
            result.store_path = load_path
            return result
