metaconfig_populationsize = 100
metaconfig_budgets = list(range(500, 9500, 1000))


algo_base = {
    "IBEA": {
        "kappa":                        0.05,
        "mating_population_size":       0.5
    }
}

prob_base = {
    "ackley": {
        "__metaconfig__budgets": list(range(50, 950, 100))
    }
}

cust_base = {
    ('IBEA', 'ackley'): {
        "__metaconfig__populationsize": 40
    },
    ('IBEA', 'ZDT3'): {
        "kappa": 0.25
    }
}


def init_alg_IBEA(algo_config, problem_mod):
    _standard_variance(algo_config, problem_mod)

def init_alg_SPEA2(algo_config, problem_mod):
    if problem_mod.name in [ "ZDT1", "ZDT2", "ZDT3", "ZDT4", "ZDT6"]:
        _standard_variance(algo_config, problem_mod,
                           divider=0.1 # TODO [kgdk]: wtf?
                          )
    else:
        _standard_variance(algo_config, problem_mod)


def _standard_variance(algo_config, problem_mod, divider=100):
    var = [ abs(maxa-mina)/divider
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance":  var,
        "crossover_variance": var
    })

