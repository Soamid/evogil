import inspect
import logging
import os
import random
import time
from types import ModuleType

from rx import operators as ops

from algorithms.base.driver import BudgetRun, Driver
from simulation import factory, log_helper
from simulation.run_config import NotViableConfiguration
from simulation.serialization import RunResult
from simulation.timing import log_time, process_time


class SimulationWorker:
    def __init__(self, simulation: factory.SimulationCase, simulation_no: int):
        self.simulation = simulation
        self.simulation_no = simulation_no

    def run(self):
        log_helper.init()
        logger = logging.getLogger(__name__)
        logger.debug(
            "Starting the worker. PID: %d, simulation case: %s",
            os.getpid(),
            self.simulation,
        )

        if self.simulation.renice and os.name == "posix":
            logger.debug(
                "Renice the process PID:%s by %s", os.getpid(), self.simulation
            )
            os.nice(int(self.simulation.renice))  # pylint: disable=no-member

        self._init_random_seed(logger)

        try:
            final_driver, problem_mod = factory.prepare(
                self.simulation.algorithm_name, self.simulation.problem_name
            )

            logger.debug("Creating the driver used to perform computation")
            driver = final_driver()
            proc_time = []
            logger.debug(
                "Beginning processing of %s, simulation: %s", driver, self.simulation
            )
            with log_time(
                process_time,
                logger,
                "Processing done in {time_res}s CPU time",
                out=proc_time,
            ):
                results = self.run_driver(driver, problem_mod, logger)

            return results, proc_time[-1], self.simulation_no

        except NotViableConfiguration as e:
            reason = inspect.trace()[-1]
            logger.info(
                "Configuration disabled by %s:%d:%s. simulation case:%s",
                reason[1],
                reason[2],
                reason[3],
                self.simulation,
            )
            logger.debug("Configuration disabled args:%s. Stack:", exc_info=e)

        except Exception as e:
            logger.exception("Some error", exc_info=e)

        finally:
            logger.debug("Finished processing. simulation case:%s", self.simulation)

    def run_driver(
        self, driver: Driver, problem_mod: ModuleType, logger: logging.Logger
    ):
        raise NotImplementedError()

    def _init_random_seed(self, logger):
        logger.debug("Getting random seed")
        # basically we duplicate the code of https://github.com/python/cpython/blob/master/Lib/random.py#L111 because
        # in case os.urandom is not available, random.seed defaults to epoch time. That would set the seed equal in each
        # process, which is not acceptable.
        try:
            random_seed = int.from_bytes(os.urandom(2500), "big")
        except NotImplementedError:
            random_seed = int(
                time.time() * 256 + os.getpid()
            )  # that's not enough for MT, but will have to do for now.
        random.seed(random_seed)


class BudgetWorker(SimulationWorker):

    def __init__(self, simulation: factory.SimulationCase, simulation_no: int):
        super().__init__(simulation, simulation_no)

    @property
    def budgets(self):
        return self.simulation.params[factory.BUDGETS_PARAM]

    def run_driver(
        self, driver: Driver, problem_mod: ModuleType, logger: logging.Logger
    ):
        runres = RunResult(self.simulation)
        results = []

        def process_results(budget: int):
            finalpop = driver.finalized_population()
            finalpop_fit = [[fit(x) for fit in problem_mod.fitnesses] for x in finalpop]
            runres.store(budget, driver.cost, finalpop, finalpop_fit)
            results.append((driver.cost, finalpop))

        driver.max_budget = self.budgets[-1]
        for budget in self.budgets:
            budget_run = BudgetRun(budget)
            budget_run.create_job(driver).pipe(
                ops.do_action(on_completed=lambda: process_results(budget))
            ).subscribe(
                lambda proxy: logger.debug(
                    "{}{} : Driver progress: budget={}, current cost={}, driver step={}".format(
                        self.simulation.algorithm_name,
                        self.simulation.problem_name,
                        budget,
                        proxy.cost,
                        proxy.step_no,
                    )
                )
            )
        return results


class TimeWorker(SimulationWorker):

    def __init__(self, simulation: factory.SimulationCase, simulation_no: int):
        super().__init__(simulation, simulation_no)

    def run_driver(
            self, driver: Driver, problem_mod: ModuleType, logger: logging.Logger
    ):
        results = []



        return results