package pl.edu.agh.evogil.algorithm;


import org.uma.jmetal.algorithm.multiobjective.omopso.OMOPSO;
import org.uma.jmetal.operator.impl.mutation.NonUniformMutation;
import org.uma.jmetal.operator.impl.mutation.UniformMutation;
import org.uma.jmetal.problem.DoubleProblem;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

public class AlgorithmFactory {


    public OMOPSO createOMOPSO(Problem problem, int swarmSize, int maxIterations, int archiveSize, double mutationProbability) {
        return new OMOPSO((DoubleProblem) problem, new SequentialSolutionListEvaluator(),
                swarmSize, maxIterations, archiveSize, new UniformMutation(mutationProbability, 0.5),
                new NonUniformMutation(mutationProbability, 0.5, 250));
    }
}
