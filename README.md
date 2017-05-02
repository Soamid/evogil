# evogil

Multi-Objective Evolutionary Algorithms platform written in python with support for multi-deme solutions and flexible hybridization tools.

## Evolutionary tools

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



