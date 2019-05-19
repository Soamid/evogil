import pickle
from contextlib import suppress
from pathlib import Path

from simulation.model import SimulationCase


class Result:
    def __init__(self, population, population_fitnesses, **additional_data):
        self.population = population
        self.fitnesses = population_fitnesses
        self.additional_data = additional_data


class ResultWithMetadata(Result):
    def __init__(self, result: Result, path: Path, run_no: int, simulation_case: SimulationCase):
        super().__init__(result.population, result.fitnesses, **result.additional_data)
        self.path = path
        self.name = path.with_suffix('').name
        self.run_no = run_no
        self.simulation_case = simulation_case


def load_file(path):
    with path.open(mode="rb") as fh:
        return pickle.load(fh)


def save_file(path, obj):
    with path.open(mode="wb") as fh:
        pickle.dump(obj, fh)


class Serializer:
    def __init__(self, simulation_case: SimulationCase):
        self.path = Path(
            simulation_case.results_dir,
            simulation_case.problem_name,
            simulation_case.algorithm_name,
            simulation_case.id,
        )

    def store(self, result: Result, file_name: str) -> Path:
        with suppress(FileExistsError):
            self.path.mkdir(parents=True)

        store_path = self.get_result_path(file_name)
        save_file(store_path, result)
        return store_path

    def get_result_path(self, file_name) -> Path:
        return self.path / f"{file_name}.pickle"

    def load(self, file_name) -> Result:
        load_path = self.get_result_path(file_name)
        return load_file(load_path)
