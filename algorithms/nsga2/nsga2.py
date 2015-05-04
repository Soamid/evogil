__author__ = 'Prpht'

import collections
import math
import random
import sys
from algorithms.utils import driver


class NSGA2(driver.Driver):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mutation_variance,
                 crossover_variance,
                 mating_population_size):
        super().__init__(population, dims, fitnesses, mutation_variance, crossover_variance)
        self.cost = 0
        self.objectives = fitnesses
        self.mating_size_c = mating_population_size
        self.generation_counter = 0
        self.population = population


    @property
    def population(self):
        return [x.v for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [self.Individual(x) for x in pop]
        self.population_size = len(self.individuals)
        self.mating_size = int(self.mating_size_c*self.population_size)

    def step(self, steps=1):
        for _ in range(steps):
            self._next_step()

    def steps(self, generator, budget=None):
        self.cost = 0
        for _ in generator:
            self._next_step()
            if budget is not None and self.cost > self.budget:
                break
        self._calculate_objectives()
        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        return self.cost

    def get_indivs_inorder(self):
        return self.rank(self.population, self.calculate_objectives)

    def finish(self):
        self._calculate_objectives()
        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        return [x.v for x in self.individuals]

    def _next_step(self):
        self._calculate_objectives()
        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        self._mating_selection(0.9)
        self._crossover()
        self._mutation()#(0.05)
        self.individuals += self.mating_individuals
        self.generation_counter += 1

    def _calculate_objectives(self):
        for ind in self.individuals:
            if ind.objectives is None:
                self.cost += 1
                ind.objectives = {objective : objective(ind.v) for objective in self.objectives}

    def calculate_objectives(self, ind):
        self.cost += 1
        return [objective(ind) for objective in self.objectives]

    def _nd_sort(self):
        self.dominated_by = collections.defaultdict(set)
        self.how_many_dominates = collections.defaultdict(int)
        self.nsga_rank = collections.defaultdict(int)
        self.front = collections.defaultdict(list)
        for x in self.individuals:
            for y in self.individuals:
                if self.dominates(x, y):
                    self.dominated_by[x].add(y)
                elif self.dominates(y, x):
                    self.how_many_dominates[x] += 1
            if self.how_many_dominates[x] is 0:
                self.nsga_rank[x] = 1
                self.front[1].append(x)
        front_no = 1
        while True:
            if len(self.front[front_no]) is 0:
                break
            for x in self.front[front_no]:
                for y in self.dominated_by[x]:
                    self.how_many_dominates[y] -= 1
                    if self.how_many_dominates[y] is 0:
                        self.nsga_rank[y] = front_no + 1
                        self.front[front_no + 1].append(y)
            front_no += 1

    def _crowding(self):
        self.dist = collections.defaultdict(float)
        for front_no, inds in self.front.items():
            if len(inds) == 0:
                break
            elif len(inds) == 1:
                self.dist[inds[0]] = 0
            else:
                for objective in self.objectives:
                    inds.sort(key = lambda x : x.objectives[objective])
                    #self.dist[inds[0]] = self.dist[inds[-1]] = float('inf')
                    max_r = inds[-1].objectives[objective]
                    min_r = inds[0].objectives[objective]
                    self.dist[inds[0]] = float('inf')
                    self.dist[inds[-1]] += 2*(inds[-1].objectives[objective] - inds[-2].objectives[objective])/(max_r - min_r + sys.float_info.epsilon)
                    for k in range(1, len(inds)-1):
                        self.dist[inds[k]] += (inds[k+1].objectives[objective] - inds[k-1].objectives[objective])/(max_r - min_r + sys.float_info.epsilon)


    def _environmental_selection(self):
        fitness = lambda ind : (self.nsga_rank[ind], 1/(self.dist[ind] + sys.float_info.epsilon))
        self.fitness = {ind : fitness(ind) for ind in self.individuals}
        self.individuals = sorted(self.individuals, key=lambda ind : self.fitness[ind])[:self.population_size]

    def _mating_selection(self, p):
        coin = lambda : random.random() < p
        better = lambda x1, x2 : self.fitness[x1] < self.fitness[x2] and x1 or x2 if coin() else self.fitness[x1] > self.fitness[x2] and x1 or x2
        self.mating_individuals = [better(random.choice(self.individuals), random.choice(self.individuals)) for _ in range(2*self.mating_size)]

    def _crossover(self):
        self.mating_individuals = [self.crossover(self.mating_individuals[i].v, self.mating_individuals[self.mating_size+i].v) for i in range(self.mating_size)]

    def _mutation(self):
        self.mating_individuals = [self.Individual(self.mutate(x)) for x in self.mating_individuals]
    #    flip = random.random()
    #    cross = lambda x1, x2 : self.Individual([a * flip + b * (1.0 - flip) for a, b in zip(x1.v, x2.v)])
    #    self.mating_individuals = [cross(self.mating_individuals[i], self.mating_individuals[self.mating_size+i]) for i in range(self.mating_size)]
    #
    #def norm(self, attr, mina, maxa):
    #    if attr < mina:
    #        return mina
    #    elif attr > maxa:
    #        return maxa
    #    else:
    #        return attr
    #
    #def _mutation(self, p):
    #    coin = lambda : random.random() < p
    #    mutate = lambda x : self.Individual([self.norm(random.gauss(a, sigma), mina, maxa) if coin else a for a, sigma, (mina, maxa) in zip(x.v, self.sigmas, self.dims)])
    #    self.mating_individuals = [mutate(x) for x in self.mating_individuals]


    def dominates_weak(self, x, y):
        return all([a <= b for a, b in zip(x.objectives.values(), y.objectives.values())])

    def dominates(self, x,y):
        A = self.dominates_weak(x,y) and not self.dominates_weak(y,x)
        x.objectives = {objective : objective(x.v) for objective in self.objectives}
        y.objectives = {objective : objective(y.v) for objective in self.objectives}
        B = self.dominates_weak(x,y) and not self.dominates_weak(y,x)
        if A is B:
            return A
        elif A is not B:
            print("JEEEEBLOOOO")
        return A

    class Individual:
        def __init__(self, vector):
            self.v = vector
            self.objectives = None

if __name__ == "__main__":
    import pylab
    # objectives = [lambda x : (x[0]+5)*(x[0]+5), lambda x : (x[1]-5)*(x[1]-5)]
    objectives = [lambda x : -10 * math.exp(-0.2 * math.sqrt(x[0]*x[0]+x[1]*x[1])), lambda x : math.pow(abs(x[0]),0.8) + 5*math.pow(math.sin(x[0]),3) + math.pow(abs(x[1]),0.8) + 5*math.pow(math.sin(x[1]),3)]
    dimensions = [(-10,10), (-10,10)]
    individuals = [[random.uniform(-10,10), random.uniform(-10,10)] for _ in range(50)]
    mating_size = 20
    population = NSGA2(objectives, dimensions, individuals, mating_size)
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
