from itertools import product
from operator import itemgetter
from algorithms.HGS.HGS import HGS
from evotools.random_tools import standard_variance

_drivers = [
    'SPEA2',
    'IBEA',
    'NSGAII',
    'OMOPSO',
    'NSGAIII',
    'SMSEMOA',
]

_metaalgorithms = [
    'HGS',
    'IMGA',
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
    'kursawe',
    'UF1',
    'UF2',
    'UF3',
    'UF4',
    'UF5',
    'UF6',
    'UF7',
    'UF8',
    'UF9',
    'UF10',
    'UF11',
    'UF12'
]

metaconfig_populationsize = 100
metaconfig_budgets = list(range(500, 9500, 1000))

class NotViableConfiguration(Exception):
    pass


algo_base = {
    "IBEA": {
        "kappa":                  0.05,
        "mating_population_size": 0.5,
    },

    "NSGAII": {
        "mating_population_size": 0.5,
    },

    "HGS": {
        "population_per_level": [50,   12, 4],
        "scaling_coefficients": [10., 2.5, 1.],
        "mutation_probability": 0.05,
        "branch_comparison":    0.05,
        "metaepoch_len":        1,
        "max_children":         3,
        "sproutiveness":        2,
        "__metaconfig__crossover_variance":   1.,
        "__metaconfig__sprouting_variance":   1.,
        "__metaconfig__mutation_variance":    1.,
    },

    "SPEA2": {
    },

    "IMGA": {
        "islands_number": 3,
        "migrants_number": 5,
        "epoch_length": 5,
    },

    "SMSEMOA": {
        "__metaconfig__var_mult": 0.1  # "z jakichś powodów dzielimy przez 0.1, wtedy były najlepsze wyniki :<" -- MI
    },

    ('HGS', ('NSGAIII',)): {
        'driver_kwargs_per_level': [
            {"eta_crossover": 20.0, "eta_mutation": 30.0},
            {"eta_crossover": 80.0, "eta_mutation": 120.0},
            {"eta_crossover": 200.0, "eta_mutation": 300.0},
        ]
    },
}

prob_base = {

}

cust_base = {

}


def init_alg___IBEA(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)

def init_alg___SPEA2(algo_config, problem_mod):
    if problem_mod.name in [ "ZDT1", "ZDT2", "ZDT3", "ZDT4", "ZDT6"]:
        standard_variance(algo_config, problem_mod, divider=0.1)
    elif problem_mod.name in ["kursawe"]:
        algo_config.update({
            "mutation_variance":  [0.8, 0.4, 0.2],
            "crossover_variance": [0.8, 0.4, 0.2],
        })
    else:
        standard_variance(algo_config, problem_mod)

def init_alg___NSGAII(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)

    if problem_mod.name in ['ackley', 'kursawe', 'ZDT4']:
        algo_config.update({
            "__metaconfig__populationsize": 75
        })


def init_alg___IMGA(algo_config, problem_mod):
    standard_variance(algo_config, problem_mod)


def init_alg_IMGA___SPEA2(algo_config, problem_mod):
    if problem_mod.name in ["ackley"]:
        standard_variance(algo_config, problem_mod)
    else:
        standard_variance(algo_config, problem_mod, divider=0.1)





def init_alg___HGS(algo_config, problem_mod):
    def multiply_per_dim(x):
        return [x * abs(b-a)
                for (a,b)
                in problem_mod.dims]
    algo_config.update({
        "crossover_variance": multiply_per_dim(algo_config["__metaconfig__crossover_variance"]),
        "sprouting_variance": multiply_per_dim(algo_config["__metaconfig__sprouting_variance"]),
        "mutation_variance":  multiply_per_dim(algo_config["__metaconfig__mutation_variance"]),
    })

def init_alg___SMSEMOA(algo_config, problem_mod):
    var = [abs(maxa - mina) / algo_config["__metaconfig__var_mult"]
           for (mina, maxa)
           in problem_mod.dims]
    reference_point = tuple(max(problem_mod.pareto_front,
                                key=itemgetter(i))[i]
                            for i
                            in range(len(problem_mod.pareto_front[0])))

    algo_config.update({
        "mutation_variance": var,
        "crossover_variance": var,
        "reference_point": reference_point
    })
