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

run_rder = [ ('coemoa_e', 'hgs_nsga2' ),
             ('coemoa_d', 'hgs_nsga2' ),
             ('coemoa_d', 'imga_nsga2'),
             ('coemoa_c', 'hgs_nsga2' ),
             ('coemoa_a', 'hgs_nsga2' ),
             ('coemoa_b', 'hgs_nsga2' ),
             ('coemoa_d', 'nsga2'     ),
             ('coemoa_e', 'nsga2'     ),
             ('kursawe',  'hgs_nsga2' ),
             ('coemoa_c', 'nsga2'     ),
             ('coemoa_a', 'nsga2'     ),
             ('coemoa_b', 'nsga2'     ),
             ('coemoa_e', 'imga_nsga2'),
             ('coemoa_c', 'imga_nsga2'),
             ('coemoa_b', 'imga_nsga2'),
             ('coemoa_a', 'imga_nsga2'),
             ('coemoa_b', 'hgs_spea2' ),
             ('coemoa_a', 'hgs_spea2' ),
             ('kursawe',  'imga_nsga2'),
             ('kursawe',  'nsga2'     ),
             ('coemoa_d', 'hgs_spea2' ),
             ('coemoa_d', 'ibea'      ),
             ('coemoa_d', 'imga_ibea' ),
             ('kursawe',  'ibea'      ),
             ('kursawe',  'imga_ibea' ),
             ('kursawe',  'spea2'     ),
             ('kursawe',  'imga_spea2'),
             ('coemoa_e', 'ibea'      ),
             ('coemoa_e', 'imga_ibea' ),
             ('kursawe',  'hgs_spea2' ),
             ('coemoa_c', 'hgs_spea2' ),
             ('coemoa_c', 'ibea'      ),
             ('coemoa_c', 'imga_ibea' ),
             ('coemoa_d', 'imga_spea2'),
             ('coemoa_b', 'imga_ibea' ),
             ('coemoa_b', 'ibea'      ),
             ('coemoa_a', 'ibea'      ),
             ('kursawe',  'hgs_ibea'  ),
             ('coemoa_a', 'imga_ibea' ),
             ('coemoa_d', 'hgs_ibea'  ),
             ('coemoa_e', 'hgs_spea2' ),
             ('coemoa_c', 'hgs_ibea'  ),
             ('coemoa_a', 'hgs_ibea'  ),
             ('coemoa_b', 'hgs_ibea'  ),
             ('coemoa_a', 'imga_spea2'),
             ('coemoa_b', 'imga_spea2'),
             ('coemoa_c', 'imga_spea2'),
             ('coemoa_e', 'imga_spea2'),
             ('ackley',   'imga_nsga2'),
             ('ackley',   'hgs_nsga2' ),
             ('coemoa_d', 'spea2'     ),
             ('coemoa_a', 'spea2'     ),
             ('coemoa_e', 'spea2'     ),
             ('coemoa_b', 'spea2'     ),
             ('coemoa_c', 'spea2'     ),
             ('ackley',   'nsga2'     ),
             ('coemoa_e', 'hgs_ibea'  ),
             ('ackley',   'imga_spea2'),
             ('ackley',   'hgs_spea2' ),
             ('ackley',   'spea2'     ),
             ('ackley',   'imga_ibea' ),
             ('ackley',   'ibea'      ),
             ('ackley',   'hgs_ibea'  ),
             ('parabol',  'hgs_spea2' ),
             ('parabol',  'hgs_ibea'  ),
             ('parabol',  'hgs_nsga2' )
           ]

