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

run_rder = [ ('ZDT4'          , 'hgs_nsga2'     ),  # 896.862s
             ('kursawe'       , 'hgs_nsga2'     ),  # 867.042s
             ('ZDT2'          , 'nsga2'         ),  # 753.007s
             ('kursawe'       , 'imga_nsga2'    ),  # 731.860s
             ('ZDT6'          , 'imga_nsga2'    ),  # 718.351s
             ('ZDT6'          , 'hgs_nsga2'     ),  # 710.019s
             ('kursawe'       , 'nsga2'         ),  # 660.961s
             ('ZDT3'          , 'hgs_nsga2'     ),  # 645.418s
             ('ZDT3'          , 'imga_nsga2'    ),  # 635.487s
             ('ZDT1'          , 'hgs_nsga2'     ),  # 596.658s
             ('ZDT2'          , 'hgs_nsga2'     ),  # 572.698s
             ('ZDT2'          , 'imga_nsga2'    ),  # 559.691s
             ('ZDT1'          , 'imga_nsga2'    ),  # 543.059s
             ('ZDT4'          , 'imga_nsga2'    ),  # 416.692s
             ('ZDT4'          , 'nsga2'         ),  # 389.425s
             ('ZDT6'          , 'nsga2'         ),  # 356.023s
             ('ZDT3'          , 'nsga2'         ),  # 322.246s
             ('ZDT1'          , 'nsga2'         ),  # 209.462s
             ('ZDT4'          , 'ibea'          ),  # 186.222s
             ('kursawe'       , 'spea2'         ),  # 164.000s
             ('ZDT4'          , 'imga_ibea'     ),  # 142.035s
             ('kursawe'       , 'ibea'          ),  # 111.761s
             ('ZDT2'          , 'imga_ibea'     ),  # 107.480s
             ('kursawe'       , 'imga_ibea'     ),  # 107.008s
             ('ZDT1'          , 'ibea'          ),  # 106.333s
             ('kursawe'       , 'hgs_ibea'      ),  # 106.025s
             ('ZDT2'          , 'ibea'          ),  # 105.628s
             ('ZDT1'          , 'imga_ibea'     ),  # 102.817s
             ('kursawe'       , 'imga_spea2'    ),  # 101.375s
             ('ZDT2'          , 'hgs_spea2'     ),  # 101.002s
             ('ZDT1'          , 'imga_spea2'    ),  #  97.327s
             ('ZDT1'          , 'hgs_spea2'     ),  #  96.848s
             ('ZDT6'          , 'ibea'          ),  #  95.664s
             ('ZDT4'          , 'hgs_ibea'      ),  #  95.239s
             ('ZDT4'          , 'imga_spea2'    ),  #  95.203s
             ('ZDT6'          , 'imga_ibea'     ),  #  94.125s
             ('ZDT2'          , 'imga_spea2'    ),  #  92.748s
             ('ZDT4'          , 'hgs_spea2'     ),  #  88.975s
             ('ZDT3'          , 'imga_spea2'    ),  #  85.477s
             ('ZDT3'          , 'ibea'          ),  #  85.068s
             ('ZDT3'          , 'imga_ibea'     ),  #  82.732s
             ('ZDT6'          , 'imga_spea2'    ),  #  82.356s
             ('ackley'        , 'imga_nsga2'    ),  #  80.309s
             ('ZDT6'          , 'hgs_ibea'      ),  #  74.197s
             ('ackley'        , 'hgs_nsga2'     ),  #  73.683s
             ('ZDT3'          , 'hgs_ibea'      ),  #  67.489s
             ('ZDT2'          , 'hgs_ibea'      ),  #  65.186s
             ('ZDT1'          , 'hgs_ibea'      ),  #  65.117s
             ('ZDT4'          , 'spea2'         ),  #  60.446s
             ('kursawe'       , 'hgs_spea2'     ),  #  60.333s
             ('ZDT2'          , 'spea2'         ),  #  59.255s
             ('ZDT3'          , 'spea2'         ),  #  58.726s
             ('ZDT1'          , 'spea2'         ),  #  58.446s
             ('ZDT6'          , 'spea2'         ),  #  57.795s
             ('ackley'        , 'nsga2'         ),  #  49.869s
             ('ZDT3'          , 'hgs_spea2'     ),  #  43.404s
             ('ZDT6'          , 'hgs_spea2'     ),  #  38.250s
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

