
options_base = {
    "IBEA": {
        "__metaconfig__populationsize": 40,
        "kappa":0.05,
        "mating_population_size":0.5
    }
}


def init_IBEA(algo_config, problem_mod):
    var = [ abs(maxa-mina)/100
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance": var,
        "crossover_variance": var
    })
