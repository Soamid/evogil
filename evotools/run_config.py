from algorithms.HGS.HGS import HGS

metaconfig_populationsize = 100
metaconfig_budgets = list(range(500, 9500, 1000))


algo_base = {
    "IBEA": {
        "kappa":                  0.05,
        "mating_population_size": 0.5,
    },
    "NSGAII": {
        "mating_population_size": 0.5,
    },
    "HGS": {
        "sproutiveness":                2,
        "max_children":                 3,
        "metaepoch_len":                1,
        "__metaconfig__populationsize": 50,
        "__metaconfig__popln_sizes":    [50, 12, 4],
        "__metaconfig__brnch_comps":    [1, 0.25, 0.05],
        "__metaconfig__sclng_coeffs":   [[10, 10, 10], [2.5, 2.5, 2.5], [1, 1, 1]],
    }
}

prob_base = {
    "ackley": {
        "__metaconfig__budgets": list(range(50, 950, 100)),
    }
}

cust_base = {
    ('IBEA', 'ackley'): {
        "__metaconfig__populationsize": 40,
    },
    
    ('IBEA', 'ZDT3'): {
        "kappa": 0.25,
    },

    ('HGS', 'ackley'): {
        "__metaconfig__sclng_coeffs":   [[4, 4, 4], [2, 2, 2], [1, 1, 1]],
        "__metaconfig__brnch_comps":    [0.05, 0.25, 0.01],
    },

    ('HGS', 'parabol'): {
        "__metaconfig__popln_sizes":    [3, 2, 1],
        "__metaconfig__brnch_comps":    [0.5, 0.125, 0.01],
        "__metaconfig__sclng_coeffs":   [[4, 4], [2, 2], [1, 1]],
        "max_children":                 2,
    },

    ((), 'HGS', ('SPEA2',),  'parabol'): {
        "__metaconfig__popln_sizes":    [75, 10, 5]
    },

    ((), 'HGS', ('NSGAII',),  'parabol'): {
        "__metaconfig__sclng_coeffs":   [[20, 20], [5, 5], [1, 1]],
        "__metaconfig__popln_sizes":    [30, 15, 5],
        "metaepoch_len":                10,
    },

    ((), 'HGS', ('IBEA',),  'ackley'): {
        "max_children":                 2,
    },
    
    ((), 'HGS', ('SPEA2',), 'ackley'): {
        "max_children":                 2,
        "__metaconfig__popln_sizes":    [100, 10, 5],
    },

    ((), 'HGS', ('NSGAII',), 'ackley'): {
        "max_children":                 2,
        "__metaconfig__popln_sizes":    [75, 10, 5],
    }

}


def init_alg_IBEA(algo_config, problem_mod):
    _standard_variance(algo_config, problem_mod)

def init_alg_SPEA2(algo_config, problem_mod):
    if problem_mod.name in [ "ZDT1", "ZDT2", "ZDT3", "ZDT4", "ZDT6"]:
        _standard_variance(algo_config, problem_mod,
                           divider=0.1 # TODO [kgdk]: wtf?
                          )
    elif problem_mod.name in ["kursawe"]:
        _standard_variance(algo_config, problem_mod, divider=[0.8, 0.4, 0.2])
    else:
        _standard_variance(algo_config, problem_mod)

def init_alg_NSGAII(algo_config, problem_mod):
    _standard_variance(algo_config, problem_mod)

    if problem_mod.name in ['ackley', 'kursawe', 'ZDT4']:
        algo_config.update({
            "__metaconfig__populationsize": 75
        })

def init_alg_HGS(algo_config, problem_mod):
    algo_config["__metaconfig__populationsize"] = algo_config["__metaconfig__popln_sizes"][0]

    if problem_mod.name in ["parabol"]:
        csovr, muttn, sprtn = 1, 1, 0.7
    else:
        csovr, muttn, sprtn = 10, 20, 30

    algo_config.update({
        "lvl_params": {
                'popln_sizes':   algo_config["__metaconfig__popln_sizes"],
                'sclng_coeffss': algo_config["__metaconfig__sclng_coeffs"],
                'brnch_comps':   algo_config["__metaconfig__brnch_comps"],
                'csovr_varss':   HGS.make_sigmas(csovr, algo_config["__metaconfig__sclng_coeffs"], problem_mod.dims),
                'muttn_varss':   HGS.make_sigmas(muttn, algo_config["__metaconfig__sclng_coeffs"], problem_mod.dims),
                'sprtn_varss':   HGS.make_sigmas(sprtn, algo_config["__metaconfig__sclng_coeffs"], problem_mod.dims),
            }
    })


def _standard_variance(algo_config, problem_mod, divider=100):
    var = [ abs(maxa-mina)/divider
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance":  var,
        "crossover_variance": var
    })

