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
        self.steps[message.operation](message, sender)


class HgsOperationTask(OperationTask):
    def __init__(self, hgs):
        super().__init__()
        self.hgs = hgs


class MetaepochHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_finished = 0
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.NEW_METAEPOCH] = self.start_metaepoch
        steps[NodeOperation.NEW_RESULT] = self.on_new_result
        steps[NodeOperation.METAEPOCH_END] = self.finish_metaepoch

    def start_metaepoch(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.NEW_METAEPOCH, self.id))

    def on_new_result(self, msg: NodeMessage, sender: Actor):
        print("update cost")
        self.hgs.cost += (
            self.hgs.config.cost_modifiers[msg.data.level] * msg.data.epoch_cost
        )

    def finish_metaepoch(self, msg: NodeMessage, sender: Actor):
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs.nodes):
            print("All nodes have ended their metaepochs")
            self.hgs.send(
                self.sender,
                HgsMessage(
                    HgsOperation.METAEPOCH_END, self.sender_task_id, self.hgs.cost
                ),
            )


class StatusHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_states = []
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.CHECK_STATUS] = self.send_check
        steps[NodeOperation.CHECK_STATUS] = self.finish_check

    def send_check(self, msg: HgsMessage, sender: Actor):
        nodes_lvl = msg.data
        self.sender = sender
        self.sender_task_id = msg.id
        nodes_to_check = (
            self.hgs.level_nodes[nodes_lvl] if nodes_lvl else self.hgs.nodes
        )
        if nodes_to_check:
            for node in nodes_to_check:
                self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))
        else:
            self.send_status()

    def finish_check(self, msg: NodeMessage, sender: Actor):
        self.nodes_states.append(msg.data)
        if len(self.nodes_states) == len(self.hgs.nodes):
            self.send_status()

    def send_status(self):
        self.hgs.send(
            self.sender,
            HgsMessage(
                HgsOperation.CHECK_STATUS, self.sender_task_id, self.nodes_states
            ),
        )


class PopulationHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.merged_population = []
        self.nodes_finished = 0
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.POPULATION] = self.get_nodes_populations
        steps[NodeOperation.POPULATION] = self.receive_population

    def get_nodes_populations(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.POPULATION, self.id))

    def receive_population(self, msg: NodeMessage, sender: Actor):
        self.merged_population.extend(msg.data)
        self.nodes_finished += 1
        if self.nodes_finished == len(self.hgs.nodes):
            self.send_merged_population()

    def send_merged_population(self):
        self.hgs.send(
            self.sender,
            HgsMessage(
                HgsOperation.POPULATION, self.sender_task_id, self.merged_population
            ),
        )


class TrimNotProgressingHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_NOT_PROGRESSING] = self.send_trim_request

    def send_trim_request(self, msg: HgsMessage, sender: Actor):
        for node in self.hgs.nodes:
            self.hgs.send(
                node, NodeMessage(NodeOperation.TRIM_NOT_PROGRESSING, self.id)
            )


class TrimRedundantHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.trim_infos = []
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_REDUNDANT] = self.send_trim_request
        steps[NodeOperation.CHECK_STATUS] = self.receive_trim_confirmation

    def send_trim_request(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))

    def receive_trim_confirmation(self, msg: NodeMessage, sender: Actor):
        trim_info = msg.data
        trim_info.node = sender
        self.trim_infos.append(trim_info)
        if len(self.trim_infos) == len(self.hgs.nodes):
            self.trim_redundant()
            self.hgs.send(
                self.sender,
                HgsMessage(HgsOperation.TRIM_REDUNDANT, self.sender_task_id, True),
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


class ReleaseSproutsHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.RELEASE_SPROUTS] = self.send_release_request
        steps[NodeOperation.RELEASE_SPROUTS_END] = self.send_release_request

    def send_release_request(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        self.hgs.send(
            self.hgs.root, NodeMessage(NodeOperation.RELEASE_SPROUTS, self.id)
        )

    def receive_release_confirmation(self, msg: NodeMessage, sender: Actor):
        self.hgs.send(
            self.sender,
            HgsMessage(HgsOperation.RELEASE_SPROUTS_END, self.sender_task_id),
        )
