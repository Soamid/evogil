import random
import time

import math
import numpy as np
import rx
import rx.operators as ops
from rx import Observable
from thespian.actors import ActorSystem

from algorithms.HGS import tools
from algorithms.HGS.actors import HgsNodeSupervisor, HgsConfig
from algorithms.HGS.message import HgsMessage, HgsOperation
from algorithms.base.driver import StepsRun, ComplexDriver
from algorithms.base.hv import HyperVolume
from evotools import rxtools

EPSILON = np.finfo(float).eps


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
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.hgs_config = HgsConfig()

        self.hgs_config.driver = driver
        self.hgs_config.population = population

        self.hgs_config.dims = dims
        self.hgs_config.reference_point = reference_point
        self.hgs_config.fitnesses = fitnesses

        self.hgs_config.fitness_errors = fitness_errors
        self.hgs_config.cost_modifiers = cost_modifiers

        corner_a = np.array([x for x, _ in dims])
        corner_b = np.array([x for _, x in dims])
        corner_dist = np.linalg.norm(corner_a - corner_b)
        self.hgs_config.min_dists = [x * corner_dist for x in comparison_multipliers]

        self.hgs_config.metaepoch_len = metaepoch_len
        self.hgs_config.max_level = max_level
        self.hgs_config.max_sprouts_no = max_sprouts_no
        self.hgs_config.sproutiveness = sproutiveness
        self.hgs_config.min_progress_ratio = min_progress_ratio

        self.hgs_config.mutation_etas = mutation_etas
        self.hgs_config.mutation_rates = mutation_rates
        self.hgs_config.crossover_etas = crossover_etas
        self.hgs_config.crossover_rates = crossover_rates
        self.hgs_config.population_sizes = population_sizes

        self.hgs_config.mantissa_bits = mantissa_bits
        self.hgs_config.driver_message_adapter_factory = (
            self.driver_message_adapter_factory
        )

        # TODO this is shared variable which is a problem in actor model
        self.hgs_config.global_fitness_archive = [
            tools.ResultArchive() for _ in range(3)
        ]

        # TODO add preconditions checking if message adapter is HGS message adapter

        print("HGS CREATED")
        self.hgs_system = ActorSystem("multiprocTCPBase")
        self.node_supervisor = self.hgs_system.createActor(HgsNodeSupervisor)

        self.hgs_system.ask(
            self.node_supervisor, HgsMessage(HgsOperation.START, self.hgs_config)
        )
        self.hgs_system.tell(
            self.node_supervisor, HgsMessage(HgsOperation.CHECK_STATUS)
        )
        node_states = self.hgs_system.listen()
        print("STATES: " + str(node_states))
        self.cost = 0

    def shutdown(self):
        ActorSystem().shutdown()

    def finalized_population(self):
        return (
            ActorSystem()
            .ask(self.node_supervisor, HgsMessage(HgsOperation.POPULATION))
            .data
        )

    def step(self):
        ActorSystem().tell(self.node_supervisor, HgsMessage(HgsOperation.NEW_METAEPOCH))
        epoch_end_message = ActorSystem().listen()
        self.cost += epoch_end_message.data
        print(f"step finished, current cost = {self.cost}")
        # TODO: status debug print
        # print(
        #     "nodes:",
        #     len(self.nodes),
        #     len([x for x in self.nodes if x.alive]),
        #     len([x for x in self.nodes if x.ripe]),
        #     "   zer:",
        #     len(self.level_nodes[0]),
        #     len([x for x in self.level_nodes[0] if x.alive]),
        #     len([x for x in self.level_nodes[0] if x.ripe]),
        #     "   one:",
        #     len(self.level_nodes[1]),
        #     len([x for x in self.level_nodes[1] if x.alive]),
        #     len([x for x in self.level_nodes[1] if x.ripe]),
        #     "   two:",
        #     len(self.level_nodes[2]),
        #     len([x for x in self.level_nodes[2] if x.alive]),
        #     len([x for x in self.level_nodes[2] if x.ripe]),
        # )
        #
        # self.run_metaepoch()
        # self.trim_sprouts()
        # self.release_new_sprouts()
        # self.revive_root()
        # print("Nodes:")
        # for i in range(3):
        #     print(
        #         "level {} : {} / {}".format(
        #             i + 1,
        #             len([n for n in self.level_nodes[i] if n.ripe]),
        #             len(self.level_nodes[i]),
        #         )
        #     )

    def run_metaepoch(self):
        node_jobs = []
        for node in self.level_nodes[2]:
            node_jobs.append(node.run_metaepoch)
        for node in self.level_nodes[1]:
            node_jobs.append(node.run_metaepoch)
        for node in self.level_nodes[0]:
            node_jobs.append(node.run_metaepoch)
            # _plot_node(node, 'r', [[0, 1], [0, 3]])
        rxtools.multiprocess_observable(node_jobs).pipe(
            ops.do_action(on_next=lambda message: self._update_cost(message))
        ).run()

    def trim_sprouts(self):
        self.trim_all(self.level_nodes[2])
        self.trim_all(self.level_nodes[1])
        self.trim_all(self.level_nodes[0])

    def trim_all(self, nodes):
        self.trim_not_progressing(nodes)
        self.trim_redundant(nodes)

    def trim_not_progressing(self, nodes):
        for sprout in [x for x in nodes if x.alive]:
            if (
                sprout.old_hypervolume is not None
                and (sprout.old_hypervolume > 0.0)
                and ((sprout.hypervolume / (sprout.old_hypervolume + EPSILON)) - 1.0)
                < self.min_progress_ratio[sprout.level] / 2 ** sprout.level
            ):
                # TODO: kij wie, czy współczynnik kurczący wymagany progress jest potrzebny (to / X**sprout.level)
                sprout.alive = False
                sprout.center = np.mean(sprout.population, axis=0)
                sprout.ripe = True
                # TODO: logging killing not progressing sprouts
                print("   KILL NOT PROGRESSING")

    def trim_redundant(self, nodes):
        alive = [x for x in nodes if x.alive]
        processed = []
        dead = [x for x in nodes if not x.alive]
        for sprout in alive:
            to_compare = [x for x in dead]
            to_compare.extend(processed)
            sprout.center = np.mean(sprout.population, axis=0)
            for another_sprout in to_compare:
                if not sprout.alive:
                    break
                if (
                    another_sprout.ripe or another_sprout in processed
                ) and tools.redundant(
                    [another_sprout.center],
                    [sprout.center],
                    self.min_dists[sprout.level],
                ):
                    sprout.alive = False
                    # TODO: logging killing redundant sprouts
                    print("   KILL REDUNDANT")
            processed.append(sprout)

    def release_new_sprouts(self):
        self.root.release_new_sprouts()

    def revive_root(self):
        if len([x for x in self.nodes if x.alive]) == 0:
            for ripe_node in [x for x in self.nodes if x.ripe]:
                ripe_node.alive = True
                ripe_node.ripe = False
            for i in range(3):
                self.min_progress_ratio[i] /= 2

            # TODO: logging root revival
            print("!!!   RESURRECTION")

    class Node:
        def __init__(self, owner, level, population):
            self.alive = True
            self.ripe = False
            self.owner = owner
            self.level = level
            self.current_cost = 0
            self.driver = owner.driver(
                population=population,
                dims=owner.dims,
                fitnesses=owner.blurred_fitnesses(self.level),
                mutation_eta=owner.mutation_etas[self.level],
                mutation_rate=owner.mutation_rates[self.level],
                crossover_eta=owner.crossover_etas[self.level],
                crossover_rate=owner.crossover_rates[self.level],
                fitness_archive=self.owner.global_fitness_archive[self.level],
                trim_function=lambda x: tools.trim_vector(
                    x, self.owner.mantissa_bits[self.level]
                ),
                message_adapter_factory=owner.driver_message_adapter_factory,
            )

            self.population = []
            self.sprouts = []
            self.delegates = []

            self.old_average_fitnesses = [float("inf") for _ in self.owner.fitnesses]
            self.average_fitnesses = [float("inf") for _ in self.owner.fitnesses]

            self.relative_hypervolume = None
            self.old_hypervolume = float("-inf")
            self.hypervolume = float("-inf")

        def run_metaepoch(self) -> Observable:
            if self.alive:
                epoch_job = StepsRun(self.owner.metaepoch_len)

                return epoch_job.create_job(self.driver).pipe(
                    ops.map(lambda message: self.fill_node_info(message)),
                    ops.do_action(lambda message: self.update_current_cost(message)),
                    ops.do_action(on_completed=lambda: self._after_metaepoch()),
                )
            return rx.empty()

        def fill_node_info(self, driver_message):
            driver_message.level = self.level
            driver_message.epoch_cost = driver_message.cost - self.current_cost
            return driver_message

        def update_current_cost(self, driver_message):
            self.current_cost = driver_message.cost

        def _after_metaepoch(self):
            self.population = self.driver.finalized_population()
            self.delegates = self.driver.message_adapter.nominate_delegates()
            random.shuffle(self.delegates)
            self.update_dominated_hypervolume()

        def update_dominated_hypervolume(self):
            self.old_hypervolume = self.hypervolume
            fitness_values = [
                [f(p) for f in self.owner.fitnesses] for p in self.population
            ]
            hv = HyperVolume(self.owner.reference_point)

            if self.relative_hypervolume is None:
                self.relative_hypervolume = hv.compute(fitness_values)
            else:
                self.hypervolume = (
                    hv.compute(fitness_values) - self.relative_hypervolume
                )

        def release_new_sprouts(self):
            if self.ripe:
                for sprout in self.sprouts:
                    sprout.release_new_sprouts()
                if (
                    self.level < self.owner.max_level
                    and len([x for x in self.sprouts if x.alive])
                    < self.owner.max_sprouts_no
                ):
                    released_sprouts = 0
                    for delegate in self.delegates:
                        if (
                            released_sprouts >= self.owner.sproutiveness
                            or len([x for x in self.sprouts if x.alive])
                            >= self.owner.max_sprouts_no
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
                                    for x in self.owner.level_nodes[self.level + 1]
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
