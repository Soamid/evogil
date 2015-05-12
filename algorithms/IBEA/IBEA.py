__author__ = 'Prpht'

from algorithms.utils import driver
import itertools
import math
import random
import sys
import operator


class IBEA(driver.Driver):
    def __init__(self, population, dims, fitnesses, mutation_variance, crossover_variance, kappa, mating_population_size):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)
        self.objectives = fitnesses  # [Indiv -> Float]
        self.indicator = self.EPlusIndicator(self)
        self.generation_counter = 0
        self.k = kappa
        self.mating_size_c = mating_population_size
        self.population = population

    def steps(self):
        def assign_real_objectives(indivs):
            for ind in indivs:
                ind.real_objectives = [ f(ind.v)
                                        for f
                                        in self.objectives
                                      ]
            return len(indivs)

        cost = assign_real_objectives(self.individuals)

        while True:
            self._scale_objectives()
            self._calculate_fitness()
            self._environmental_selection()

            yield cost, [ x.v
                          for x
                          in self.individuals
                        ]
            cost = 0

            self._mating_selection(0.9)
            self._crossover()
            self._mutation()#(0.05)

            cost += assign_real_objectives( self.mating_individuals )
            self.individuals += self.mating_individuals

            self.generation_counter += 1

    def get_indivs_inorder(self):
        return self.rank(self.population, operator.attrgetter('real_objectives'))

    def finish(self):
        return [ x.v
                 for x
                 in self.individuals
               ]

    def _scale_objectives(self):
        min_max = lambda x : (min(x), max(x))

        # :: [( Indiv -> Float, Int, (Float, Float) )]
        measured = [ (objective, obj_id, min_max([ ind.real_objectives[obj_id]
                                                   for ind
                                                   in self.individuals
                                                 ]) )
                     for obj_id, objective
                     in enumerate(self.objectives)
                   ]
        # :: [ Indiv -> Float ]
        self.scaled_objectives = [ self._scale(obj_id, min_o, max_o)
                                   for objective, obj_id, (min_o, max_o)
                                   in measured
                                 ]

        return len(self.individuals)

    @staticmethod
    # (Int, Float, Float) -> (Indiv -> Float)
    def _scale(fun_id, min_o, max_o):
        def scaled(x):
            return (x.real_objectives[fun_id] - min_o)/(max_o - min_o + sys.float_info.epsilon)
        return scaled

    def _calculate_fitness(self):
        # :: Dict (Individual, Individual) Float
        self.indicators = { (x1, x2) : self.indicator(x1.v, x2.v)
                            for x1, x2
                            in itertools.product(self.individuals, self.individuals)  # yyy chyba chodziło o permutations?
                          }
        # :: Float
        self.c = max([ abs(x)
                       for x
                       in self.indicators.values()
                     ])
        # :: Dict Individual Float
        self.fitness = { x1 : sum([ (-1)*math.exp((-1)*(self.indicators[(x2,x1)]/abs(self.c*self.k + sys.float_info.epsilon)))
                                    for x2
                                    in self.individuals
                                    if x2 != x1
                                  ])
                         for x1
                         in self.individuals
                       }

    def _environmental_selection(self):
        while len(self.individuals) > self.population_size:
            self.individuals = sorted( self.individuals,
                                       key=lambda x : self.fitness[x],
                                       reverse=True
                                     )
            removed = self.individuals.pop()
            for x in self.individuals:
                self.fitness[x] += math.exp((-1)*(self.indicators[(removed, x)] / abs(self.c * self.k + sys.float_info.epsilon)))

    def _mating_selection(self, p):
        coin = lambda : random.random() < p
        better = lambda x1, x2 : self.fitness[x1] < self.fitness[x2] and x1 or x2 if coin() else self.fitness[x1] > self.fitness[x2] and x1 or x2
        self.mating_individuals = [ better(random.choice(self.individuals),
                                           random.choice(self.individuals)
                                          )
                                    for _
                                    in range(2*self.mating_size)
                                  ]

    def _crossover(self):
        self.mating_individuals = [ self.crossover( self.mating_individuals[i].v,
                                                    self.mating_individuals[self.mating_size+i].v
                                                  )
                                    for i
                                    in range(self.mating_size)
                                  ]

    def _mutation(self):
        self.mating_individuals = [ self.Individual(self.mutate(x))
                                    for x
                                    in self.mating_individuals
                                  ]

    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        # :: [Individual]
        self.individuals = [ self.Individual(x)
                             for x
                             in pop
                           ]
        self.population_size = len(self.individuals)
        self.mating_size = int(self.mating_size_c*self.population_size)

    class EPlusIndicator:
        # :: IBEA -> EPlusIndicator
        def __init__(self, population):
            self.population = population  # aculy is Dolan… or rather "parent", ie. the IBEA containing this EPlusIndicator

        # :: (Indiv, Indiv) -> Float
        def __call__(self, x1, x2):
            return max([ objective(x1) - objective(x2)
                         for objective 
                         in self.population.scaled_objectives  # [ Indiv -> Float ]
                       ])

    class Individual:
        def __init__(self, vector):
            self.v = vector
            self.real_objectives = None

if __name__ == "__main__":
    import pylab
    # objectives = [lambda x : (x[0]+5)*(x[0]+5), lambda x : (x[1]-5)*(x[1]-5)]
    objectives = [ lambda x : -10 * math.exp(-0.2 * math.sqrt(x[0]*x[0]+x[1]*x[1])),
                   lambda x : math.pow(abs(x[0]),0.8) + 5*math.pow(math.sin(x[0]),3) + math.pow(abs(x[1]),0.8) + 5*math.pow(math.sin(x[1]),3)
                 ]
    dimensions = [ (-10,10),
                   (-10,10)
                 ]
    individuals = [ [random.uniform(-10,10), random.uniform(-10,10)]
                    for _
                    in range(150)
                  ]
    kappa = 0.05
    mating_size = 50
    population = IBEA(objectives, dimensions, individuals, kappa, mating_size)
    for i in range(100):
        population.step()
        print(i)
    effect = population.finish()
    X = [population.objectives[0](x) for x in effect]
    Y = [population.objectives[1](x) for x in effect]
    pylab.scatter(X,Y)
    # pylab.xlim(-10.,250.)
    # pylab.ylim(-10.,250.)
    pylab.xlim(-15.,5.)
    pylab.ylim(-15.,25.)
    pylab.show()
