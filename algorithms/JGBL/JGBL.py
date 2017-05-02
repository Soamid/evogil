import random

from algorithms.NSGAII.NSGAII import NSGAII


class JGBL(NSGAII):
    def __init__(self,
                 population,
                 dims,
                 fitnesses,
                 mating_population_size,
                 mutation_eta,
                 crossover_eta,
                 mutation_rate,
                 crossover_rate,
                 jumping_rate,
                 jumping_percentage,
                 trim_function=lambda x: x,
                 fitness_archive=None):
        super().__init__(population,
                         dims,
                         fitnesses,
                         mating_population_size,
                         mutation_eta,
                         crossover_eta,
                         mutation_rate,
                         crossover_rate, trim_function, fitness_archive)
        self.jumping_rate = jumping_rate
        self.jumping_percentage = jumping_percentage

    def _next_step(self):
        old_pop = list(self.individuals)
        super()._next_step()
        new_pop = list(self.individuals)

        self.individuals = set(old_pop + new_pop)

        self._nd_sort()
        self._crowding()
        self._environmental_selection()
        nondominanted = self.front[1]

        if len(nondominanted) > len(self.individuals):
            print('hop')
            pop_set = set(self.individuals)
            nondominanted = [n for n in nondominanted if n not in pop_set]
            print(len(nondominanted))

            jumping_pop = self.jump_genes(self.individuals, nondominanted)
            for ind in jumping_pop:
                ind.v = self.trim_function(ind.v)

            self.individuals = set(self.individuals + jumping_pop)
            self._calculate_objectives()
            self._nd_sort()
            self._crowding()
            self._environmental_selection()
        else:
            self.individuals = new_pop

    def jump_genes(self, pop, nondominated):
        jumping_pop = []
        for ind in pop:
            if random.random() < self.jumping_rate:
                _, cut_self = self.cut_and_paste(ind.v, ind.v)
                _, copy_self = self.copy_and_paste(ind.v, ind.v)

                cut_ind1, cut_ind2 = self.cut_and_paste(ind.v, random.choice(nondominated).v)
                copy_ind1, copy_ind2 = self.copy_and_paste(ind.v, random.choice(nondominated).v)

                jumping_pop.extend([self.Individual(x) for x in [cut_self, copy_self, cut_ind1, cut_ind2, copy_ind1, copy_ind2]])
        return jumping_pop

    def cut_and_paste(self, x, y):
        x_ratio, x_transposon, x_to_cut = self.prepare_transposon(x)
        y_ratio, y_transposon, y_to_cut = self.prepare_transposon(y)

        self.multi_delete(x_ratio, x_to_cut)
        self.multi_delete(y_ratio, y_to_cut)

        x_pos = random.randint(0, len(x_ratio))
        y_pos = random.randint(0, len(y_ratio))

        x_ratio = x_ratio[:x_pos] + y_transposon + x_ratio[x_pos:]
        y_ratio = y_ratio[:y_pos] + x_transposon + y_ratio[y_pos:]

        return self.decode_ratio(x_ratio), self.decode_ratio(y_ratio)

    def copy_and_paste(self, x, y):
        x_ratio, x_transposon, x_to_copy = self.prepare_transposon(x)
        y_ratio, y_transposon, y_to_copy = self.prepare_transposon(y)

        x_pos = random.randint(0, len(x_ratio) - 1)
        y_pos = random.randint(0, len(y_ratio) - 1)

        self.paste(x_ratio, y_transposon, x_pos)
        self.paste(y_ratio, x_transposon, y_pos)

        return self.decode_ratio(x_ratio), self.decode_ratio(y_ratio)

    def paste(self, x, transposon, pos):
        for t in transposon:
            x[pos] = t
            pos += 1
            if pos >= len(x):
                return

    def decode_ratio(self, ratio):
        return [self.dims[i][0] + ratio[i] * (self.dims[i][1] - self.dims[i][0]) for i in range(len(ratio))]

    def prepare_transposon(self, x):
        transposon_pos = sorted(random.sample(range(len(x)), int(self.jumping_percentage * len(x))))
        ratio = self.convert_to_ratio(x)

        transposon = [ratio[i] for i in transposon_pos]

        return ratio, transposon, transposon_pos

    def multi_delete(self, list_, *args):
        indexes = reversed(*args)
        for index in indexes:
            del list_[index]
        return list_

    def convert_to_ratio(self, x):
        return [(x[i] - self.dims[i][0]) / (self.dims[i][1] - self.dims[i][0]) for i in range(len(x))]


if __name__ == '__main__':
    jgbl = JGBL([(1, 5), (1, 5), (1, 5), (1, 5)], 0.5)
    print(jgbl.copy_and_paste([3, 2, 1, 5], [4, 2.5, 2.66, 1.734]))
