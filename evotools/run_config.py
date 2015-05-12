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
    }
}


def init_alg_IBEA(algo_config, problem_mod):
    var = [ abs(maxa-mina)/100
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance":  var,
        "crossover_variance": var
    })
