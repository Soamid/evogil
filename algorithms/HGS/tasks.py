import itertools
import uuid
from typing import Dict, Callable, Any, List

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

    def log(self, msg):
        print(f"SUPERVISOR :  {msg}")


class MetaepochHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_finished = 0
        self.sender = None
        self.sender_task_id = None
        self.requests_count = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.NEW_METAEPOCH] = self.start_metaepoch
        steps[NodeOperation.NEW_RESULT] = self.on_new_result
        steps[NodeOperation.METAEPOCH_END] = self.finish_metaepoch

    def start_metaepoch(self, msg: HgsMessage, sender: Actor):
        self.log("New metaepoch, nodes: ")
        for lvl, nodes in self.hgs.level_nodes.items():
            self.log(f"{lvl} : {nodes}")

        self.sender = sender
        self.sender_task_id = msg.id
        self.requests_count = len(self.hgs.nodes)
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.NEW_METAEPOCH, self.id))

    def on_new_result(self, msg: NodeMessage, sender: Actor):
        self.log(
            f"update cost {msg.data.epoch_cost}, modifier= {self.hgs.config.cost_modifiers[msg.data.level]}"
        )
        self.hgs.cost += (
                self.hgs.config.cost_modifiers[msg.data.level] * msg.data.epoch_cost
        )

    def finish_metaepoch(self, msg: NodeMessage, sender: Actor):
        self.nodes_finished += 1
        if self.nodes_finished == self.requests_count:
            self.log("All nodes have ended their metaepochs")
            self.hgs.send(
                self.sender,
                HgsMessage(
                    HgsOperation.METAEPOCH_END, self.sender_task_id, self.hgs.cost
                ),
            )


class StatusHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.nodes_to_check = None
        self.nodes_states = []
        self.sender = None
        self.sender_task_id = None
        self.nodes_lvl = None
        self.checked = set()

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.CHECK_STATUS] = self.send_check
        steps[NodeOperation.CHECK_STATUS] = self.finish_check

    def send_check(self, msg: HgsMessage, sender: Actor):
        self.nodes_lvl = msg.data
        self.sender = sender
        self.sender_task_id = msg.id
        self.nodes_to_check = self.get_nodes_to_check()
        self.log(f"nodes to check: {self.nodes_to_check}")
        if self.nodes_to_check:
            for node in self.nodes_to_check:
                self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))
        else:
            self.send_status()

    def get_nodes_to_check(self):
        if self.nodes_lvl is not None:
            if self.nodes_lvl <= self.hgs.config.max_level:
                return list(self.hgs.level_nodes[self.nodes_lvl])
            return []
        return list(self.hgs.nodes)

    def finish_check(self, msg: NodeMessage, sender: Actor):
        if sender not in self.nodes_to_check or str(sender) in self.checked:
            self.log(f"unexpected node checked: {sender}")
        self.nodes_states.append(msg.data)
        self.checked.add(str(sender))
        self.log(
            f"status check {len(self.nodes_states)} / {len(self.nodes_to_check)} for {self.sender}, current: {sender}, already checked: {self.checked}")
        if len(self.nodes_states) == len(self.nodes_to_check):
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
        self.requests_count = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.POPULATION] = self.get_nodes_populations
        steps[NodeOperation.POPULATION] = self.receive_population

    def get_nodes_populations(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        self.requests_count = len(self.hgs.nodes)
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.POPULATION, self.id))

    def receive_population(self, msg: NodeMessage, sender: Actor):
        self.merged_population.extend(msg.data)
        self.nodes_finished += 1
        if self.nodes_finished == self.requests_count:
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
        self.sender = None
        self.sender_task_id = None
        self.requests_count = None
        self.nodes_finished = 0

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_NOT_PROGRESSING] = self.send_trim_request
        steps[NodeOperation.TRIM_NOT_PROGRESSING_END] = self.receive_trim_confirmation

    def send_trim_request(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        self.requests_count = len(self.hgs.nodes)
        for node in self.hgs.nodes:
            self.hgs.send(
                node, NodeMessage(NodeOperation.TRIM_NOT_PROGRESSING, self.id)
            )

    def receive_trim_confirmation(self, msg: NodeMessage, sender: Actor):
        self.nodes_finished += 1
        if self.nodes_finished == self.requests_count:
            self.hgs.send(
                self.sender,
                HgsMessage(HgsOperation.TRIM_NOT_PROGRESSING_END, self.sender_task_id),
            )


class TrimRedundantHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.trim_infos = []
        self.sender = None
        self.sender_task_id = None
        self.requests_count = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.TRIM_REDUNDANT] = self.send_trim_request
        steps[NodeOperation.CHECK_STATUS] = self.receive_trim_confirmation

    def send_trim_request(self, msg: HgsMessage, sender: Actor):
        self.sender = sender
        self.sender_task_id = msg.id
        self.requests_count = len(self.hgs.nodes)
        for node in self.hgs.nodes:
            self.hgs.send(node, NodeMessage(NodeOperation.CHECK_STATUS, self.id))

    def receive_trim_confirmation(self, msg: NodeMessage, sender: Actor):
        trim_info = msg.data
        trim_info.node = sender
        self.trim_infos.append(trim_info)
        if len(self.trim_infos) == self.requests_count:
            self.trim_infos.sort(reverse=True, key=lambda info: info.level)
            for level, lvl_infos in itertools.groupby(
                    self.trim_infos, key=lambda info: info.level
            ):
                self.log(f"trim lvl infos: {list(lvl_infos)} for lvl={level}")
                self.trim_redundant(list(lvl_infos))
            self.hgs.send(
                self.sender,
                HgsMessage(HgsOperation.TRIM_REDUNDANT_END, self.sender_task_id, True),
            )

    def trim_redundant(self, lvl_infos):
        alive = [x for x in lvl_infos if x.alive]
        processed = []
        dead = [x for x in lvl_infos if not x.alive]
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
                    self.log("   KILL REDUNDANT")
            processed.append(sprout)


class ReleaseSproutsHgsTask(HgsOperationTask):
    def __init__(self, hgs):
        super().__init__(hgs)
        self.sender = None
        self.sender_task_id = None

    def configure_steps(self, steps: Dict[OperationType, Callable]):
        steps[HgsOperation.RELEASE_SPROUTS] = self.send_release_request
        steps[NodeOperation.RELEASE_SPROUTS_END] = self.receive_release_confirmation

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
