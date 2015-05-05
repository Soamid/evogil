package pl.edu.agh.evogil.example;

import org.uma.jmetal.algorithm.multiobjective.omopso.OMOPSO;
import org.uma.jmetal.operator.impl.mutation.NonUniformMutation;
import org.uma.jmetal.operator.impl.mutation.UniformMutation;
import org.uma.jmetal.problem.multiobjective.Kursawe;
import org.uma.jmetal.solution.DoubleSolution;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

import java.util.List;

public class AlgoTest {

    public static void main(String[] args) {
        Kursawe problem = new Kursawe(2);
        OMOPSO algo = new OMOPSO(problem, new SequentialSolutionListEvaluator(), 100, 50, 80, new UniformMutation(0.5, 0.2), new NonUniformMutation(0.5, 0.2, 10));
        algo.run();

        List<DoubleSolution> sol = algo.getResult();

        for (DoubleSolution s : sol) {
            System.out.println(s);
        }
    }
}
