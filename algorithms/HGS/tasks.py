import uuid
from typing import Dict, Callable, Any

from thespian.actors import Actor

from algorithms.HGS import tools
from algorithms.HGS.message import (
    NodeOperation,
    NodeMessage,
    HgsMessage,
    HgsOperation,
    OperationType,
    Message,
)


class OperationTask:
    def __init__(self):
        self.id = uuid.uuid4()
        self.steps = {}
        self.configure_steps(self.steps)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        raise NotImplementedError()

    def execute(self, message: Message, sender: Actor):
        self.steps[message.operation](message.data, sender)


class HgsOperationTask(OperationTask):
    def __init__(self, hgs):
        super().__init__()
        self.hgs = hgs


class MetaepochTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.NEW_METAEPOCH] = self.start_metaepoch
        steps[NodeOperation.NEW_RESULT] = self.on_new_result
        steps[NodeOperation.METAEPOCH_END] = self.finish_metaepoch

    def start_metaepoch(self, params: Any, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.NEW_METAEPOCH, self.id))

    def on_new_result(self, params: Any, sender: Actor):
        print("update cost")
        self.hgs.cost += (
            self.hgs.config.cost_modifiers[params.level] * params.epoch_cost
        )

    def finish_metaepoch(self, params: Any, sender: Actor):
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs.nodes):
            print("All nodes have ended their metaepochs")
            self.hgs.send(
                self.hgs.parent_actor,
                HgsMessage(HgsOperation.METAEPOCH_END, self.hgs.cost),
            )


class StatusTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_states = []

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.CHECK_STATUS] = self.send_check
        steps[NodeOperation.CHECK_STATUS] = self.finish_check

    def send_check(self, params: Any, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))

    def finish_check(self, params: Any, sender: Actor):
        self.nodes_states.append(params)
        if len(self.nodes_states) == len(self.hgs.nodes):
            self.hgs.send(self.hgs.parent_actor, self.nodes_states)


class PopulationTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.merged_population = []
        self.nodes_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.POPULATION] = self.get_nodes_populations
        steps[NodeOperation.POPULATION] = self.receive_population

    def get_nodes_populations(self, params: Any, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.POPULATION, self.id))

    def receive_population(self, params: Any, sender: Actor):
        self.merged_population.extend(params)
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs.nodes):
            self.send_merged_population()

    def send_merged_population(self):
        self.hgs.send(
            self.hgs.parent_actor,
            HgsMessage(HgsOperation.POPULATION, self.merged_population),
        )


class TrimNotProgressingTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_NOT_PROGRESSING] = self.send_trim_request

    def send_trim_request(self, params: Any, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(
                node, NodeMessage(NodeOperation.TRIM_NOT_PROGRESSING, self.id)
            )


class TrimRedundantTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.trim_infos = []

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_REDUNDANT] = self.send_trim_request
        steps[NodeOperation.CHECK_STATUS] = self.receive_trim_confirmation

    def send_trim_request(self, params: Any, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))

    def receive_trim_confirmation(self, params: Any, sender: Actor):
        params.node = sender
        self.trim_infos.append(params)
        if len(self.trim_infos) == len(self.hgs.nodes):
            self.trim_redundant()
            self.hgs.send(
                self.hgs.parent_actor, HgsMessage(HgsOperation.TRIM_REDUNDANT, True)
            )

    def trim_redundant(self):
        alive = [x for x in self.trim_infos if x.alive]
        processed = []
        dead = [x for x in self.trim_infos if not x.alive]
        for sprout in alive:
            to_compare = [x for x in dead]
            to_compare.extend(processed)
            for another_sprout in to_compare:
                if not sprout.alive:
                    break
                if (
                    another_sprout.ripe or another_sprout in processed
                ) and tools.redundant(
                    [another_sprout.center],
                    [sprout.center],
                    self.hgs.min_dists[sprout.level],
                ):
                    self.hgs.send(sprout.node, NodeMessage(NodeOperation.KILL, self.id))
                    sprout.alive = False
                    # TODO: logging killing redundant sprouts
                    print("   KILL REDUNDANT")
            processed.append(sprout)
