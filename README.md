# evogil

Multi-Objective Evolutionary Algorithms platform written in python with support for multi-deme solutions and flexible hybridization tools.

## evogil contents (evolutionary tools)

### Algorithms
evogil contains Python implementations of many popular, single-deme MOEAs:
- Non-dominated Sorting Genetic Algorithm (NSGA-II and θ-NSGA-III)
- Strength Pareto Evolutionary Algorithm 2 (SPEA2)
- Multi-objective PSO (OMOPSO)
- Indicator-Based Evolutionary Algorithm (IBEA)
- Smetric selection EMOA (SMS-EMOA)
- Aproach based on nondominated sorting and local search (NSLS)

True power of evogil lies in possibility of combining these methods in multi-deme solutions. We provide following complex models:
- Hierarchical Genetic Strategy (HGS)
- Island Model Genetic Algorithm (IMGA)
- Jumping Gene Based Learning (JGBL)

HGS model is our own solution, you can find more about it [here](http://www.sciencedirect.com/science/article/pii/S1877750316300254) (denoted as MO-mHGS).

In order to add your own algorithm as Evogil's driver, follow instruction in [Developer's Guide](doc/developer_guide.md).

### Quality indicators

Metrics implemented in evogil:
- Hypervolume
- Generational Distance (GD)
- Inverse Generational Distance (IGD)
- Average Hausdorff Distance (AHD)
- Epsilon
- Extent
- Spacing
- Pareto Dominance Indicator (PDI)

### Benchmarks

Set of Multi-Objective problems included in evogil for testing purposes:
- ZDT family (ZDT1, ZDT2, ZDT3, ZDT4, ZDT6)
- cec2009 family (UF1-UF12)
- kursawe
- ackley

## How to install it?

Currently whole Evogil project source code has to be downloaded in order to run or extend the framework. In order to setup Evogil:
1. Clone evogil repository.
2. Install conda.
3. Prepare the conda environment from environment.yaml configuration (you can simply run `conda-install.bat`).
4. Activate created environment by running command: `activate evogil`
5. Check if everything works, e. g. run: 
```
python evogil.py -h
```
You can use created conda environment as a Python interpreter in your Python IDE (e.g. PyCharm).

## How to use it?

You can add your own solutions and easily extend evogil possibilities. In order to run evogil simulation for specific algorithm, benchmark and simulation budget, just type (in your evogil location):
```
python evogil.py run budget 500 -a nsgaii -p zdt1
```
It will run simulation with budget 500 with algorithm NSGAII for problem ZDT1. All simulation results (represented as values of all quality metrics for specified budget) will be stored in pickle format so that you can load them quickly with python.

You can also specify multiple problems and algorithms (if options -a and -p are not specified at all, all algorithms and all problems are run) and even many budget "checkpoints" in which evogil should store outcomes:
```
python evogil.py run budget 500,1000,1200 -a nsgaii,spea2 -p zdt1,uf2,uf10
```

Complex configurations are also possible with evogil runner - you can specify multi-deme model with subsequent single-deme "driver" by:
```
python evogil.py run budget 500 -a hgs+nsgaii, hgs+omopso -p zdt1
```
Here we run two HGS simulations, but in first case all HGS nodes will run NSGAII algorithm. The second one will be driven by OMOPSO driver.

## How to extend it?
Evogil was designed as a framework so you can write your own algorithms, problems or simulation types. For further information, see [Developer's Guide](doc/developer_guide.md).

TODO: notes about serialization, results analysis and plotting.



