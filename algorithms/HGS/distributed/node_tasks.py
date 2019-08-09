import logging
import random
from typing import Dict, Callable

import numpy as np
import rx
import rx.operators as ops
from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.distributed.message import (
    OperationType,
    NodeOperation,
    NodeMessage,
    HgsMessage,
    HgsOperation,
)
from algorithms.HGS.distributed.hgs_tasks import OperationTask
from algorithms.base.driver import StepsRun
from algorithms.base.hv import HyperVolume

EPSILON = np.finfo(float).eps


class NodeOperationTask(OperationTask):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def log(self, msg, lvl=logging.DEBUG):
        self.node.log(msg, lvl)

class NodeState:
    def __init__(self, address, level, alive, ripe, center, population_len):
        self.address = address
        self.level = level
        self.alive = alive
        self.ripe = ripe
        self.center = center
        self.population_len = population_len


def create_node_state(address, level, alive, ripe, population):
    center = np.mean(population, axis=0) if population else None
    return NodeState(address, level, alive, ripe, center, len(population))


class CheckStatusNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.CHECK_STATUS] = self.send_status

    def send_status(self, msg: NodeMessage, sender: Actor):
        state = create_node_state(sender,
            self.node.level, self.node.alive, self.node.ripe, self.node.population
        )
        self.node.send(sender, NodeMessage(NodeOperation.CHECK_STATUS, msg.id, state))


class ReviveNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.REVIVE] = self.revive

    def revive(self, msg: NodeMessage, sender: Actor):
        self.node.ripe = False
        self.node.alive = True
        self.node.send(sender, NodeMessage(NodeOperation.REVIVE, msg.id))


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
            self.log("ALIVE SO RUN EPOCH")
            epoch_job = StepsRun(self.node.metaepoch_len)

            self.log(
                f"starting metaepoch, len={self.node.metaepoch_len}, pop_len={len(self.node.driver.population)} "
            )

            return epoch_job.create_job(self.node.driver).pipe(
                ops.map(lambda message: self.fill_node_info(message)),
                ops.do_action(lambda message: self.update_current_cost(message)),
                ops.do_action(on_completed=lambda: self._after_metaepoch()),
            )
        self.log("DEAD SO EMPTY MSG")
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
        min_progress_ratio = msg.data
        if (
            self.node.alive
            and self.node.old_hypervolume is not None
            and self.node.old_hypervolume > 0.0
            and ((self.node.hypervolume / (self.node.old_hypervolume + EPSILON)) - 1.0)
            < (min_progress_ratio / 2 ** self.node.level)
        ):
            # TODO: kij wie, czy współczynnik kurczący wymagany progress jest potrzebny (to / X**sprout.level)
            self.node.alive = False
            self.node.center = np.mean(self.node.population, axis=0)
            self.node.ripe = True
            # TODO: logging killing not progressing sprouts
            self.log("   KILL NOT PROGRESSING")

        self.node.send(
            sender, NodeMessage(NodeOperation.TRIM_NOT_PROGRESSING_END, msg.id)
        )


class ReleaseSproutsNodeTask(NodeOperationTask):
    def __init__(self, node):
        super().__init__(node)
        self.sender = None
        self.sender_task_id = None
        self.alive_sprouts_count = 0
        self.next_lvl_sprouts_states = None
        self.sprouts_checked = 0
        self.released_sprouts = 0
        self.current_delegate_index = 0
        self.created_sprouts_states = []

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[NodeOperation.RELEASE_SPROUTS] = self.receive_sprouting_request
        steps[NodeOperation.CHECK_STATUS] = self.receive_sprout_state
        steps[HgsOperation.REGISTER_NODE_END] = self.new_sprout_released

    def receive_sprouting_request(self, msg: NodeMessage, sender: Actor):
        self.log("receiving next level states")
        self.sender = sender
        self.sender_task_id = msg.id
        self.next_lvl_sprouts_states = msg.data

        if self.node.ripe:
            if self.node.sprouts:
                for sprout in self.node.sprouts:
                    self.node.send(
                        sprout, NodeMessage(NodeOperation.CHECK_STATUS, self.id)
                    )
            else:
                self.start_sprouting()
        else:
            self.log("finishing because not ripe")
            self.finish()

    def receive_sprout_state(self, msg: NodeMessage, sender: Actor):
        self.sprouts_checked += 1
        self.alive_sprouts_count += 1 if msg.data.alive else 0

        if self.sprouts_checked == len(self.node.sprouts):
            self.start_sprouting()

    def start_sprouting(self):
        if (
            self.node.level < self.node.max_level
            and self.alive_sprouts_count < self.node.max_hgs_sprouts_no
            and self.node.delegates
        ):
            self.release_next_sprout()
        else:
            self.log("finishing because max lvl reached")
            self.finish()

    def try_relase_next_sprout(self):
        self.log("trying next sprout")
        if self.current_delegate_index < len(self.node.delegates):
            self.release_next_sprout()
        else:
            self.log("finishing because all delegates checked")
            self.finish()

    def release_next_sprout(self):
        if (
            self.released_sprouts >= self.node.sproutiveness
            or self.alive_sprouts_count >= self.node.max_hgs_sprouts_no
        ):
            self.log("finishing because max sprouts reached")
            self.finish()
            return

        delegate = self.node.delegates[self.current_delegate_index]
        self.log(
            f"checking next delegate: {delegate}, index: {self.current_delegate_index}"
        )
        self.current_delegate_index += 1

        if not any(
            [
                tools.redundant(
                    [delegate],
                    [sprout.center],
                    self.node.min_dists[self.node.level + 1],
                )
                for sprout in self.next_lvl_sprouts_states
                if sprout.population_len > 0
            ]
        ):
            candidate_population = tools.population_from_delegate(
                delegate,
                self.node.hgs_population_sizes[self.node.level + 1],
                self.node.hgs_dims,
                self.node.hgs_mutation_rates[self.node.level + 1],
                self.node.hgs_mutation_etas[self.node.level + 1],
            )

            self.log("releasing new sprout!")
            new_sprout_state = create_node_state(self.node.myAddress,
                self.node.level + 1, True, False, candidate_population
            )
            self.created_sprouts_states.append(new_sprout_state)
            self.next_lvl_sprouts_states.append(new_sprout_state)
            self.node.send(
                self.node.supervisor,
                HgsMessage(
                    HgsOperation.REGISTER_NODE,
                    self.id,
                    (self.node.level + 1, candidate_population),
                ),
            )
        else:
            # TODO: logging redundant candidates
            # self.log("   CANDIDATE REDUNDANT")
            self.try_relase_next_sprout()

    def finish(self):
        my_state = create_node_state(self.node.myAddress,
            self.node.level, self.node.alive, self.node.ripe, self.node.population
        )
        self.node.send(
            self.sender,
            NodeMessage(
                NodeOperation.RELEASE_SPROUTS_END,
                self.sender_task_id,
                (my_state, self.created_sprouts_states),
            ),
        )

    def new_sprout_released(self, msg: HgsMessage, sender: Actor):
        self.log("new sprout registered")
        self.node.sprouts.append(msg.data)
        self.released_sprouts += 1

        self.try_relase_next_sprout()
