PLOTS_DIR = 'plots'

SPEA_LS = '-'
NSGA_LS = '--'
IBEA_LS = ':'
SPEA_M = 'o'
NSGA_M = '*'
IBEA_M = '^'
BARE_CL = '0.8'
IMGA_CL = '0.4'
HGS_CL = '0.0'

algos = {'spea2': ('SPEA2', SPEA_LS, SPEA_M, BARE_CL), 'nsga2': ('NSGAII', NSGA_LS, NSGA_M, BARE_CL),
         'ibea': ( 'IBEA', IBEA_LS, IBEA_M, BARE_CL),
         'imga_spea2': ('IMGA-SPEA2', SPEA_LS, SPEA_M,  IMGA_CL),
         'imga_nsga2': ( 'IMGA-NSGAII', NSGA_LS,NSGA_M, IMGA_CL), 'imga_ibea': ('IMGA-IBEA', IBEA_LS, IBEA_M, IMGA_CL),
         'hgs_spea2': ( 'HGS-SPEA2', SPEA_LS, SPEA_M, HGS_CL),
         'hgs_nsga2': ( 'HGS-NSGAII', NSGA_LS, NSGA_M, HGS_CL), 'hgs_ibea': ( 'HGS-IBEA', IBEA_LS, IBEA_M, HGS_CL)}
algos_order = ['spea2', 'nsga2', 'ibea', 'imga_spea2', 'imga_nsga2', 'imga_ibea', 'hgs_spea2', 'hgs_nsga2', 'hgs_ibea']

metric_names = [ ("distance_from_pareto", "dst from pareto"),
                 ("distribution", "distribution"),
                 ("extent", "extent")
               ]

