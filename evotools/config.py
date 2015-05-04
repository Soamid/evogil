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

run_rder = [ ('coemoa_d'      , 'hgs_nsga2'     ),  # 896.862s
             ('kursawe'       , 'hgs_nsga2'     ),  # 867.042s
             ('coemoa_b'      , 'nsga2'         ),  # 753.007s
             ('kursawe'       , 'imga_nsga2'    ),  # 731.860s
             ('coemoa_e'      , 'imga_nsga2'    ),  # 718.351s
             ('coemoa_e'      , 'hgs_nsga2'     ),  # 710.019s
             ('kursawe'       , 'nsga2'         ),  # 660.961s
             ('coemoa_c'      , 'hgs_nsga2'     ),  # 645.418s
             ('coemoa_c'      , 'imga_nsga2'    ),  # 635.487s
             ('coemoa_a'      , 'hgs_nsga2'     ),  # 596.658s
             ('coemoa_b'      , 'hgs_nsga2'     ),  # 572.698s
             ('coemoa_b'      , 'imga_nsga2'    ),  # 559.691s
             ('coemoa_a'      , 'imga_nsga2'    ),  # 543.059s
             ('coemoa_d'      , 'imga_nsga2'    ),  # 416.692s
             ('coemoa_d'      , 'nsga2'         ),  # 389.425s
             ('coemoa_e'      , 'nsga2'         ),  # 356.023s
             ('coemoa_c'      , 'nsga2'         ),  # 322.246s
             ('coemoa_a'      , 'nsga2'         ),  # 209.462s
             ('coemoa_d'      , 'ibea'          ),  # 186.222s
             ('kursawe'       , 'spea2'         ),  # 164.000s
             ('coemoa_d'      , 'imga_ibea'     ),  # 142.035s
             ('kursawe'       , 'ibea'          ),  # 111.761s
             ('coemoa_b'      , 'imga_ibea'     ),  # 107.480s
             ('kursawe'       , 'imga_ibea'     ),  # 107.008s
             ('coemoa_a'      , 'ibea'          ),  # 106.333s
             ('kursawe'       , 'hgs_ibea'      ),  # 106.025s
             ('coemoa_b'      , 'ibea'          ),  # 105.628s
             ('coemoa_a'      , 'imga_ibea'     ),  # 102.817s
             ('kursawe'       , 'imga_spea2'    ),  # 101.375s
             ('coemoa_b'      , 'hgs_spea2'     ),  # 101.002s
             ('coemoa_a'      , 'imga_spea2'    ),  #  97.327s
             ('coemoa_a'      , 'hgs_spea2'     ),  #  96.848s
             ('coemoa_e'      , 'ibea'          ),  #  95.664s
             ('coemoa_d'      , 'hgs_ibea'      ),  #  95.239s
             ('coemoa_d'      , 'imga_spea2'    ),  #  95.203s
             ('coemoa_e'      , 'imga_ibea'     ),  #  94.125s
             ('coemoa_b'      , 'imga_spea2'    ),  #  92.748s
             ('coemoa_d'      , 'hgs_spea2'     ),  #  88.975s
             ('coemoa_c'      , 'imga_spea2'    ),  #  85.477s
             ('coemoa_c'      , 'ibea'          ),  #  85.068s
             ('coemoa_c'      , 'imga_ibea'     ),  #  82.732s
             ('coemoa_e'      , 'imga_spea2'    ),  #  82.356s
             ('ackley'        , 'imga_nsga2'    ),  #  80.309s
             ('coemoa_e'      , 'hgs_ibea'      ),  #  74.197s
             ('ackley'        , 'hgs_nsga2'     ),  #  73.683s
             ('coemoa_c'      , 'hgs_ibea'      ),  #  67.489s
             ('coemoa_b'      , 'hgs_ibea'      ),  #  65.186s
             ('coemoa_a'      , 'hgs_ibea'      ),  #  65.117s
             ('coemoa_d'      , 'spea2'         ),  #  60.446s
             ('kursawe'       , 'hgs_spea2'     ),  #  60.333s
             ('coemoa_b'      , 'spea2'         ),  #  59.255s
             ('coemoa_c'      , 'spea2'         ),  #  58.726s
             ('coemoa_a'      , 'spea2'         ),  #  58.446s
             ('coemoa_e'      , 'spea2'         ),  #  57.795s
             ('ackley'        , 'nsga2'         ),  #  49.869s
             ('coemoa_c'      , 'hgs_spea2'     ),  #  43.404s
             ('coemoa_e'      , 'hgs_spea2'     ),  #  38.250s
             ('ackley'        , 'imga_spea2'    ),  #  20.072s
             ('ackley'        , 'spea2'         ),  #   6.887s
             ('ackley'        , 'hgs_spea2'     ),  #   5.843s
             ('parabol'       , 'hgs_ibea'      ),  #   0.011s
             ('parabol'       , 'hgs_spea2'     ),  #   0.004s
             ('ackley'        , 'imga_ibea'     ),  #   0.004s
             ('ackley'        , 'ibea'          ),  #   0.004s
             ('parabol'       , 'hgs_nsga2'     ),  #   0.003s
             ('ackley'        , 'hgs_ibea'      )   #   0.003s
           ]

