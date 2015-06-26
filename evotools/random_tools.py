from contextlib import suppress, contextmanager
import copy
import random


def weighted_choice(choices):
    # http://stackoverflow.com/a/3679747/547223
    choices = list(choices)
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w

    assert False, "Shouldn't get here"


def take(n, iterator):
    with suppress(StopIteration):
        for i in range(n):
            yield next(iterator)

def show_partial(x):
    res = "∅"
    try:
        return str(x.func)
    except AttributeError:
        if x:
            return str(type(x))
        else:
            return "∅"

def show_conf(conf):
    conf = copy.deepcopy(conf)
    with suppress(KeyError):
        conf["driver"] = show_partial(conf["driver"])
    with suppress(KeyError):
        conf["population"] = [conf["population"][0], "…snip…"]
    return str(conf)


def standard_variance(algo_config, problem_mod, divider=5.0):
    var = [ abs(maxa-mina)/divider
            for (mina, maxa)
            in problem_mod.dims
          ]
    algo_config.update({
        "mutation_variance":  var,
        "crossover_variance": var,
    })


@contextmanager
def close_and_join(x):
    try:
        yield x
    finally:
        x.close()
        x.join()

