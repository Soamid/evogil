from py4j.java_gateway import JavaGateway
import pylab
import time
from ep.utils.driver import Driver
from problems.kursawe import problem as kursawe

class OMOPSO(Driver):

    def __init__(self, gateway, problem, swarm_size, archive_size):
        super().__init__(None, None, None, None, None)
        self.swarm_size = swarm_size
        self.archive_size = archive_size
        self.problem = problem

        self.gateway = gateway

    def create_algorithm(self, max_iterations):
        provider = self.gateway.entry_point
        algorithm_factory = provider.getAlgorithmFactory()

        self.algorithm = algorithm_factory.createOMOPSO(self.problem, self.swarm_size, max_iterations, self.archive_size,
                                                        self.mutation_probability)

    def steps(self, iterator, budget=None):
        max_iterations = 84 #len(iterator)
        self.create_algorithm(max_iterations)
        self.algorithm.run()

    def finish(self):
        final_result = []
        for result in self.algorithm.getResult():
            res = []
            for i in range(result.getNumberOfVariables()):
                res.append(result.getVariableValue(i))
            final_result.append(res)
        return final_result


def save_plot(fitnesses, population, name, analytical, time):
    print("   Finished for benchmark " + name)
    X = [fitnesses[0](x) for x in population]
    Y = [fitnesses[1](x) for x in population]
    fig = pylab.figure()
    pylab.plot()
    pylab.xlabel("funkcja celu I")
    pylab.ylabel("funkcja celu II")
    pylab.figtext(.50, .95, "czas wykonywania: " + str(time) + " s", horizontalalignment='center', verticalalignment='center')
    pylab.scatter(X,Y, c='b')
    # pylab.scatter(analytical[0], analytical[1], c='r')
    fig.savefig('ep/omopso/' + name + '.png')

if __name__ == '__main__':
    start = time.clock()
    gateway = JavaGateway()
    kursawe_problem = gateway.jvm.org.uma.jmetal.problem.multiobjective.Kursawe(3)

    omopso = OMOPSO(gateway, kursawe_problem, 100, 80)
    omopso.steps(range(50))
    results = omopso.finish()
    elapsed = (time.clock() - start)

    save_plot(kursawe.fitnesses, results, 'kursawe_omopso', kursawe.pareto_front, elapsed)

