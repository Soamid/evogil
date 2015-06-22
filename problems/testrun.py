# import functools
# import logging
# import os
# import json
# import random
# from unittest import TestCase
# import math
# import itertools
# import time
# import unittest
#
# from evotools import ea_utils
# from evotools.metrics_utils import distance_from_pareto, distribution, extent
# from evotools.serialization import get_current_time
#
#
# #noinspection PyPep8Naming
# class TestRun(TestCase):
#     alg_name = "unspecified alg_name!"
#     # Priorities: ___________________
#     # -1 - final only
#     # 0  - quick
#     # 1  - normal
#     # 2  - heavy, final
#     # None - RUN ALL THE TESTS! But... Ain't nobody got time for that.
#     selected_tests = 2
#
#     def distance_from_pareto_metrics(self, *args, **kwargs):
#         solution = self.result
#         pareto_front = self.problem_mod.pareto_front
#         return distance_from_pareto(solution, pareto_front)
#
#     def distribution_metrics(self, sigma=0.1, *args, **kwargs):
#         solution = self.result
#         return distribution(solution, sigma)
#
#     def extent_metrics(self, *args, **kwargs):
#         solution = self.result
#         return extent(solution)
#
#     metrics = extent_metrics
#
#     @staticmethod
#     def bind_param(key, val):
#         def decor(test_item):
#             @functools.wraps(test_item)
#             def bind_param(*args, **kwargs):
#                 logging.debug("bind_param: for %s binding %s to %s", test_item, key, val)
#                 kwargs[key] = val
#                 return test_item(*args, **kwargs)
#
#             return bind_param
#
#         return decor
#
#     @staticmethod
#     def gather_function(cls_inst=None, fun_name="unknown_test"):
#         """ @type cls_inst : TestRun """
#
#         dir_path = "jsoned/{problem}/{algname}/{test}/{budget}".format(
#             problem=cls_inst.problem_mod.name,
#             algname=cls_inst.__class__.alg_name,
#             test=fun_name,
#             budget=(cls_inst.alg.budget or 0))
#
#         os.makedirs(dir_path, exist_ok=True)
#
#         for metric_name, metric_value in cls_inst.metrics_value:
#
#             filename = "{dir}/{metrics}_{time}_{random}.json".format(
#                 dir=dir_path,
#                 metrics=metric_name,
#                 time=get_current_time(),
#                 random=random.randint(100000,999999))
#
#             with open(filename, "w") as f:
#                 logging.debug("gather_function: pickling to %s (cost: %s)", filename, cls_inst.cost)
#                 json.dump({"cost": cls_inst.cost,
#                            "problem_mod": cls_inst.problem_mod.name,
#                            "result": cls_inst.result,
#                            "metrics": metric_value,
#                            "algorithm": cls_inst.alg_name},
#                           f)
#
#
#     @staticmethod
#     def with_gathering(gather_function):
#         def decor(test_item):
#             @functools.wraps(test_item)
#             def gathered_run(*args, **kwargs):
#                 cls_inst = args[0]
#                 assert isinstance(cls_inst, TestRun)
#                 logging.debug("with_gathering: %s", test_item)
#                 random.seed()
#                 test_item(*args, **kwargs)
#                 try:
#                     gather_function(cls_inst=cls_inst, fun_name=test_item.__name__)
#                 except TypeError as e:
#                     pass
#             return gathered_run
#         return decor
#
#     @staticmethod
#     def map_param(key, vals, gather_function=None):
#         def decor(test_item):
#             @functools.wraps(test_item)
#             def multirun(*args, **kwargs):
#
#                 cls_inst = args[0]
#                 assert isinstance(cls_inst, TestRun)
#
#                 logging.debug("map_param: for %s binding %s to %s in order ", test_item, key, vals)
#                 for val in vals:
#                     kwargs[key] = val
#                     logging.debug("map_param: for %s, now binding %s to %s (out of %s)", test_item, key, val, vals)
#                     random.seed()
#                     test_item(*args, **kwargs)
#                     try:
#                         gather_function(cls_inst=cls_inst, fun_name=test_item.__name__)
#                     except TypeError:
#                         pass
#
#             return multirun
#
#         return decor
#
#     @staticmethod
#     def skipByName():
#         NAMES_DESCR = [("test_quick",  [0, 1, 2], 10.),
#                        ("test_normal", [1, 2],    60.),
#                        ("test_heavy",  [2],        2. * 3600.),
#                        ("test_final",  [2, -1],    2. * 3600.)]
#
#         def decor(test_item):
#             for pattern, lvls, time_limit in NAMES_DESCR:
#                 reason = "{0}'s run-levels: {1}. Current run-level TestRun.selected_tests={2}. Skipping.".format(
#                     test_item.__name__, lvls, TestRun.selected_tests)
#
#                 #noinspection PyUnusedLocal
#                 @functools.wraps(test_item)
#                 def skipped(*args, **kwargs):
#                     raise unittest.SkipTest(reason)
#
#                 skipped.__unittest_skip__ = True
#                 skipped.__unittest_skip_why__ = reason
#
#                 @functools.wraps(test_item)
#                 def measured(*args, **kwargs):
#                     wall_time = -time.clock()
#                     test_item(*args, **kwargs)
#                     wall_time += time.clock()
#                     if wall_time > time_limit:
#                         print("Warning. {0}'s execution time {1:7.3}s exceeded {2:7.3}s. Consider raising its level."
#                               .format(test_item.__name__, wall_time, time_limit))
#
#                 if pattern in test_item.__name__:
#                     if TestRun.selected_tests is False or TestRun.selected_tests in lvls:
#                         return measured
#                     return skipped
#             print((">> Warning. Test name {0} does not start with any of: {1}.\n"
#                    ">> Skipping by name disabled").format(test_item.__name__,
#                                                           ', '.join(pattern
#                                                                     for pattern, lvls, timel in NAMES_DESCR)))
#             return test_item
#
#         return decor
#
#     @staticmethod
#     def printing_range(n):
#         tw = None
#         twp = ""
#         for i in range(n):
#             if tw:
#                 twp = " (previous step took {0:.3} seconds)".format(tw + time.clock())
#             print("  # .. Top-level step #{0}{1}".format(i, twp))
#             tw = -time.clock()
#             yield i
#
#     @staticmethod
#     def andrew(t, zs):
#         t_coeff = itertools.accumulate(itertools.cycle([1, 0]))
#         sin_cos = itertools.cycle([math.sin, math.cos])
#         return zs[0] / math.sqrt(2.) + sum(z * fun(tf * t) for z, tf, fun in zip(zs[1:], t_coeff, sin_cos))
#
#     def setUp(self):
#         self.disabled = False
#         self.alg = None
#         self.result = []
#         self.name = None
#         self.problem_name = None
#         self.problem_mod = None
#         self.imgname = "default"
#         self.imgname = self._testMethodName[5:]
#         logging.basicConfig(level=logging.DEBUG)
#         random.seed()
#         print("{hr}\nExecuting {0}.{1}...".format(self.__class__.__name__, self._testMethodName,
#                                                   hr='-' * 120))
#         self.__wall_time = -time.clock()
#
#     def run_alg(self, budget, problem, steps_gen=itertools.count(), **kwargs):
#         self.alg.budget = budget or 0
#
#         result, cost = None, 0
#         gen = self.alg.steps()
#         while cost <= self.alg.budget:
#             cost, result = next(gen)
#
#         self.cost = cost
#
#         self.problem_mod = problem
#         self.result = [[fit(x) for fit in problem.fitnesses] for x in result]
#         def run_metric(metric):
#             passed_args = {
#                             k[len(metric)+1:]:v
#                             for (k,v) in kwargs.items()
#                             if type(k) is str and k.startswith(metric)
#                           }
#             return metric[:-len('_metrics')], getattr(self, metric)(**passed_args)
#         self.metrics_value = [
#                                 run_metric(x)
#                                 for x in dir(self)
#                                 if x.endswith('_metrics')
#                              ]
#
#     def tearDown(self):
#         import matplotlib.pyplot as plt
#         if self.disabled:
#             return
#
#         if not self.cost:
#             self.cost = -1
#
#         self.__wall_time += time.clock()
#         print("  # Execution finished after {0:.3}s, cost {1}".format(self.__wall_time, self.cost))
#
#         if not self.result:
#             print("  # No results returned! Have you submitted them via `self.result` ?")
#             return
#
#         problem_name = self.problem_mod.name
#         dirname = "problems/{0}/{1}/results".format(problem_name, self.alg_name)
#         if not os.path.isdir(dirname):
#             print("  # Directory {0} did not exist. Consider adding empty {0}/.gitignore to repo".format(dirname))
#             os.makedirs(dirname)
#         filename = "{0}/{1}".format(dirname, self.imgname)
#
#         print("  # Generating plots with output to {0}".format(filename))
#         print("  # plot: fitness ")
#
#         f = plt.figure(figsize=(16, 12), dpi=470)
#         plt.title("Fitness   T={0:8.3} C={1}".format(self.__wall_time, self.cost))
#         plt.xlabel('1st objective')
#         plt.ylabel('2nd objective')
#         plt.axhline(linestyle='--', lw='0.75', c='#dddddd')
#         plt.axvline(linestyle='--', lw='0.75', c='#dddddd')
#
#         if self.problem_mod.pareto_front:
#             prto_x = [x[0] for x in self.problem_mod.pareto_front]
#             prto_y = [x[1] for x in self.problem_mod.pareto_front]
#             plt.scatter(prto_x, prto_y, c='r', s=80, alpha=0.3)
#
#         res_x = [x[0] for x in self.result]
#         res_y = [x[1] for x in self.result]
#         plt.scatter(res_x, res_y, c='b')
#
#         plt.savefig(filename + "_fitnesses.png")
#         plt.close(f)
