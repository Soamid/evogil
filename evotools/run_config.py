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
        "__metaconfig__popln_sizes":    [50, 12, 4],
        "__metaconfig__brnch_comps":    [1, 0.25, 0.05],
        "__metaconfig__sclng_coeffs":   [[10, 10, 10], [2.5, 2.5, 2.5], [1, 1, 1]],
    },
    "IMGA": {
        "islands_number": 3,
        "migrants_number": 5,
        "epoch_length": 5,
    },

    (("IMGA", ), "IBEA"): {
        "kappa": 0.05,
    },
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


    (('HGS',), 'IBEA', (), 'ackley'): {
        "kappa": 0.05
    },


    ('HGS', 'ackley'): {
        "__metaconfig__sclng_coeffs": [[4, 4], [2, 2], [1, 1]],
        "__metaconfig__brnch_comps": [0.05, 0.25, 0.01],
        "max_children": 2
    },

    ((), 'HGS', ('NSGAII',), 'ackley'): {
        "__metaconfig__popln_sizes":    [75, 10, 5],
    },

    ((), 'HGS', ('SPEA2',), 'ackley'): {
        "__metaconfig__popln_sizes":    [100, 10, 5],
    },

    ((), 'HGS', ('IBEA',), 'ackley'): {
        "__metaconfig__popln_sizes":    [20, 9, 5],
        "__metaconfig__sclng_coeffs":   [[10, 10], [5, 5], [1, 1]],
        "metaepoch_len":                5,
        "__metaconfig__brnch_comps":    [0.5, 0.125, 0.01]
    },

    ((), 'IMGA', ('IBEA',), 'ackley'): {
        "__metaconfig__populationsize": 40,
    },
}


def init_alg_IBEA(algo_config, problem_mod):
    _standard_variance(algo_config, problem_mod)

def init_alg_SPEA2(algo_config, problem_mod):
    if problem_mod.name in [ "ZDT1", "ZDT2", "ZDT3", "ZDT4", "ZDT6"]:
        _standard_variance(algo_config, problem_mod, divider=0.1)
    elif problem_mod.name in ["kursawe"]:
        algo_config.update({
            "mutation_variance":  [0.8, 0.4, 0.2],
            "crossover_variance": [0.8, 0.4, 0.2],
        })
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
        csovr, muttn, sprtn = 10, 20, 100

    print("APPLYING SCLNG COEFFS", algo_config["__metaconfig__sclng_coeffs"])
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


def init_alg_IMGA(algo_config, problem_mod):
    _standard_variance(algo_config, problem_mod)


def init_alg_IMGA__SPEA2(algo_config, problem_mod):
    if problem_mod.name in ["ackley"]:
        _standard_variance(algo_config, problem_mod)
    else:
        _standard_variance(algo_config, problem_mod, divider=0.1)


def _standard_variance(algo_config, problem_mod, divider=100.0):
    var = [ abs(maxa-mina)/divider
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance":  var,
        "crossover_variance": var,
    })

