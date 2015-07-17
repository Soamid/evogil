from itertools import product

_drivers = [
    'SPEA2',
    'IBEA',
    'NSGAII',
    'OMOPSO',
    'NSGAIII',
    'SMSEMOA',
]

_metaalgorithms = [
    'IMGA',
    'RHGS'
]

algorithms = [
                 "{}+{}".format(meta, algo)
                 for meta, algo
                 in product(_metaalgorithms, _drivers)
             ] + _drivers

problems = [
    'ZDT1',
    'ZDT2',
    'ZDT3',
    'ZDT4',
    'ZDT6',
    'UF1',
    'UF2',
    'UF3',
    'UF4',
    'UF5',
    'UF6',
    'UF7',
    'UF8',
    'UF9',
    'EWA1',
    'EWA2'
]

metaconfig_populationsize = 100
metaconfig_budgets = list(range(500, 9500, 1000))


class NotViableConfiguration(Exception):
    pass


sclng_coeffs = [10, 2.5, 1]

algo_base = {
    "IBEA": {
        "kappa": 0.05,
        "mating_population_size": 0.5,
    },

    "NSGAII": {
        "mating_population_size": 0.5,
    },

    "IMGA": {
        "islands_number": 3,
        "migrants_number": 5,
        "epoch_length": 5,
    },

    "RHGS": {
        "mutation_etas": (10.0, 20.0, 30.0),
        "crossover_etas": (15.0, 30.0, 40.0),
        "population_sizes": (80, 20, 5),
        "comparison_multipliers": (1.0, 0.15, 0.075),
        "mantissa_bits": (3, 9, 27),
        "max_sprouts_no": 20,
        "sproutiveness": 10,
        "metaepoch_len": 3,
    },
}

prob_base = {

}

cust_base = {

}


def init_alg___RHGS(algo_config, problem_mod):
    reference_point = tuple(50.0
                            for _
                            in range(len(problem_mod.pareto_front[0])))
    algo_config.update({
        "reference_point": reference_point,
        "mutation_rates": [1.0 / len(problem_mod.dims) for _ in range(3)],
        "crossover_rates": [0.9 for _ in range(3)],
    })


def init_alg___IBEA(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg___SPEA2(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg___NSGAII(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg___NSGAIII(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg___OMOPSO(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg___SMSEMOA(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)
    reference_point = tuple(50.0
                            for _
                            in range(len(problem_mod.pareto_front[0])))
    algo_config.update({
        "reference_point": reference_point
    })


def init_alg___IMGA(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def standard_variance(algo_config, problem_mod):
    algo_config.update({
        "mutation_eta": 20.0,
        "crossover_eta": 30.0,
        "mutation_rate": 1.0 / len(problem_mod.dims),
        "crossover_rate": 0.9,
    })