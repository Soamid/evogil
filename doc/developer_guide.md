## Developer's Guide

### Creating new algorithms

Currently, you can extend evogil by adding new algorithms to `evogil/algorithms` package. In the future, there will be also a possibility to run external, custom algorithms' scripts, without integrating them into the framework code.

1. Create algorithm class by extending `Driver`:
    ```python
    from algorithms.base.driver import Driver
    
    class MyAlgorithm(Driver):
        pass
    ```
2. Implement missing methods from `Driver` class:
     - `step()` - single step of algorithm. Steps are invoked by simulation runner. Typically step represents a single generation of an algorithm. However, if an algorithm hasn't generational nature (e.g. steady-state), it may be used as other repeatable chunk of calculations. Note that algorithms initialization should be invoked in constructor.
     - `finalized_population()` - this method is called by simulation runner at the end of simulation to obtain final state of algorithm's population. Population should be represented as list of individuals (vectors of real numbers with size equal to dimensions count of a problem domain).

3. Add a constructor with all parameters required by your algorithm. Parameter list has to be extended with `*args, **kwargs` params passed to `super()` (`Driver`) constructor. For example:
    ```python
        def __init__(
            self,
            population,
            dims,
            fitnesses,
            mating_population_size,
            mutation_eta,
            crossover_eta,
            mutation_rate,
            crossover_rate,
            *args,
            **kwargs
        ):
            super().__init__(*args, **kwargs)
            # Further initialization...
    ```
4. Add your algorithm configuration to `run_config.py` script:
    - add the algorithm name to `drivers` list
    - add any specific to your algorithm parameters in `algo_base` dictionary
    - optionally, add custom configuration method with a name `init_alg___X` where `X` is your algorithm name. It is useful to fill typical parameters, such as mutation/crossover rate using default values, for example:
        ```python
        def init_alg___MyAlgorithm(algo_config, problem_mod):
           standard_variance(algo_config, problem_mod)
        ```
 5. Check if everything is ok simply by running `evogil` with your algorithm, for example:
     ```cmd
    run budget 500 -a MyAlgorithm -p zdt1
    ```
 
