# base
from contextlib import contextmanager

# matplotlib
import matplotlib.pyplot as plt


@contextmanager
def pyplot_figure():
    fig = plt.figure()
    yield fig
    plt.close(fig)
