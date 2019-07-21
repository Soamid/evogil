import random
import uuid
from typing import Any, Dict, Callable

import numpy as np
import rx
import rx.operators as ops
from thespian.actors import Actor

from algorithms.HGS.message import OperationType, NodeOperation, NodeMessage
from algorithms.HGS.tasks import OperationTask
from algorithms.base.driver import StepsRun
from algorithms.base.hv import HyperVolume

EPSILON = np.finfo(float).eps


class NodeOperationTask(OperationTask):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def execute(self, message: NodeMessage, sender: Actor):
        self.steps[message.operation](message.data, message.id, sender)


class NodeState:
    def __init__(self, alive, ripe, center):
        self.alive = alive
        self.ripe = ripe
        self.center = center


class CheckStatusTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.CHECK_STATUS] = self.send_status

    def send_status(self, params: Any, task_id: uuid, sender: Actor):
        center = np.mean(self.node.population, axis=0) if self.node.population else None
        self.node.send(
            sender,
            NodeMessage(
                NodeOperation.CHECK_STATUS,
                task_id,
                NodeState(self.node.alive, self.node.ripe, center),
            ),
        )


class GetPopulationTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.POPULATION] = self.send_population

    def send_population(self, params: Any, task_id: uuid, sender: Actor):
        self.node.send(
            sender, NodeMessage(NodeOperation.POPULATION, task_id, self.node.population)
        )


class NewMetaepochTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.NEW_METAEPOCH] = self.stream_metaepoch_results

    def stream_metaepoch_results(self, params: Any, task_id: uuid, sender: Actor):
        self.run_metaepoch().pipe(
            ops.do_action(
                on_completed=lambda: self.node.send(
                    sender, NodeMessage(NodeOperation.METAEPOCH_END, task_id)
                )
            )
        ).subscribe(
            lambda result: self.node.send(
                sender, NodeMessage(NodeOperation.NEW_RESULT, task_id, result)
            )
        )

    def run_metaepoch(self):
        if self.node.alive:
            print("ALIVE SO RUN EPOCH")
            epoch_job = StepsRun(self.node.metaepoch_len)

            return epoch_job.create_job(self.node.driver).pipe(
                ops.map(lambda message: self.fill_node_info(message)),
                ops.do_action(lambda message: self.update_current_cost(message)),
                ops.do_action(on_completed=lambda: self._after_metaepoch()),
            )
        print("DEAD SO EMPTY MSG")
        return rx.empty()

    def fill_node_info(self, driver_message):
        driver_message.level = self.node.level
        driver_message.epoch_cost = driver_message.cost - self.node.current_cost
        return driver_message

    def update_current_cost(self, driver_message):
        self.node.current_cost = driver_message.cost

    def _after_metaepoch(self):
        self.node.population = self.node.driver.finalized_population()
        self.node.delegates = self.node.driver.message_adapter.nominate_delegates()
        random.shuffle(self.node.delegates)
        self.update_dominated_hypervolume()

    def update_dominated_hypervolume(self):
        self.node.old_hypervolume = self.node.hypervolume
        fitness_values = [
            [f(p) for f in self.node.fitnesses] for p in self.node.population
        ]
        hv = HyperVolume(self.node.reference_point)

        if self.node.relative_hypervolume is None:
            self.node.relative_hypervolume = hv.compute(fitness_values)
        else:
            self.node.hypervolume = (
                hv.compute(fitness_values) - self.node.relative_hypervolume
            )


class TrimNotProgressing(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.TRIM_NOT_PROGRESSING] = self.trim_not_progressing

    def trim_not_progressing(self, params: Any, task_id: uuid, sender: Actor):
        if (
            self.node.alive
            and self.node.old_hypervolume is not None
            and self.node.old_hypervolume > 0.0
            and ((self.node.hypervolume / (self.node.old_hypervolume + EPSILON)) - 1.0)
            < (self.node.min_progress_ratio / 2 ** self.node.level)
        ):
            # TODO: kij wie, czy współczynnik kurczący wymagany progress jest potrzebny (to / X**sprout.level)
            self.node.alive = False
            self.node.center = np.mean(self.node.population, axis=0)
            self.node.ripe = True
            # TODO: logging killing not progressing sprouts
            print("   KILL NOT PROGRESSING")
