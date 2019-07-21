import random
import uuid
from typing import Any, Dict, Callable

import numpy as np
import rx
import rx.operators as ops
from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.message import (
    OperationType,
    NodeOperation,
    NodeMessage,
    HgsMessage,
    HgsOperation,
)
from algorithms.HGS.tasks import OperationTask
from algorithms.base.driver import StepsRun
from algorithms.base.hv import HyperVolume

EPSILON = np.finfo(float).eps


class NodeOperationTask(OperationTask):
    def __init__(self, node):
        super().__init__()
        self.node = node


class NodeState:
    def __init__(self, alive, ripe, center):
        self.alive = alive
        self.ripe = ripe
        self.center = center


class CheckStatusNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.CHECK_STATUS] = self.send_status

    def send_status(self, msg: NodeMessage, sender: Actor):
        center = np.mean(self.node.population, axis=0) if self.node.population else None
        self.node.send(
            sender,
            NodeMessage(
                NodeOperation.CHECK_STATUS,
                msg.id,
                NodeState(self.node.alive, self.node.ripe, center),
            ),
        )


class GetPopulationNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.POPULATION] = self.send_population

    def send_population(self, msg: NodeMessage, sender: Actor):
        self.node.send(
            sender, NodeMessage(NodeOperation.POPULATION, msg.id, self.node.population)
        )


class NewMetaepochNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.NEW_METAEPOCH] = self.stream_metaepoch_results

    def stream_metaepoch_results(self, msg: NodeMessage, sender: Actor):
        self.run_metaepoch().pipe(
            ops.do_action(
                on_completed=lambda: self.node.send(
                    sender, NodeMessage(NodeOperation.METAEPOCH_END, msg.id)
                )
            )
        ).subscribe(
            lambda result: self.node.send(
                sender, NodeMessage(NodeOperation.NEW_RESULT, msg.id, result)
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


class TrimNotProgressingNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.TRIM_NOT_PROGRESSING] = self.trim_not_progressing

    def trim_not_progressing(self, msg: NodeMessage, sender: Actor):
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


class ReleaseSproutsTask(NodeOperationTask):
    def __init__(self,  node):
        super().__init__(node)
        self.sprouts_children_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.RELEASE_SPROUTS] = self.pass_relase_request_to_children
        steps[
            NodeOperation.RELEASE_SPROUTS_END
        ] = self.receive_sprouts_info_from_children
        steps[HgsOperation.CHECK_STATUS]

    def pass_relase_request_to_children(self, params: Any, sender: Actor):
        if self.node.ripe:
            for sprout in self.node.sprouts:
                self.node.send(
                    sprout, NodeMessage(NodeOperation.RELEASE_SPROUTS, self.id)
                )

    def receive_sprouts_info_from_children(self, params: Any, sender: Actor):
        self.sprouts_children_finished += 1
        self.check_next_level_nodes()

    def check_next_level_nodes(self):
        if self.sprouts_children_finished == len(self.node.sprouts):
            self.node.send(
                self.node.supervisor,
                HgsMessage(HgsOperation.CHECK_STATUS, self.node.level + 1),
            )

    def release_new_sprouts(self):
        alive_sprouts_no = len([x for x in self.sprouts_infos if x.alive])
        if (
            self.node.level < self.node.max_level
            and alive_sprouts_no < self.node.max_sprouts_no
        ):
            released_sprouts = 0
            for delegate in self.node.delegates:
                if (
                    released_sprouts >= self.node.sproutiveness
                    or alive_sprouts_no >= self.node.max_sprouts_no
                ):
                    break

                if not any(
                    [
                        tools.redundant(
                            [delegate],
                            [sprout.center],
                            self.owner.min_dists[self.level + 1],
                        )
                        for sprout in [
                            x
                            for x in self.node.level_nodes[self.level + 1]
                            if len(x.population) > 0
                        ]
                    ]
                ):
                    candidate_population = tools.population_from_delegate(
                        delegate,
                        self.owner.population_sizes[self.level + 1],
                        self.owner.dims,
                        self.owner.mutation_rates[self.level + 1],
                        self.owner.mutation_etas[self.level + 1],
                    )

                    new_sprout = HGS.Node(
                        self.owner, self.level + 1, candidate_population
                    )
                    self.sprouts.append(new_sprout)
                    self.owner.nodes.append(new_sprout)
                    self.owner.level_nodes[self.level + 1].append(new_sprout)
                    released_sprouts += 1
                else:
                    # TODO: logging redundant candidates
                    # print("   CANDIDATE REDUNDANT")
                    pass
