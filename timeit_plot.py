
import timeit
from collections import defaultdict
from itertools import product
import heapq
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import LinearLocator, FormatStrFormatter


def timeit_compare(funcs, inputs, setups='pass', **kwargs):
    """Compares speed of functions across input conditions.
    
    'funcs' should be a list of functions expressed as strings. 
    String substitution is done on each function while iterating 
    over ranges of values in 'inputs' to compare speed. 
    
    'inputs' should be a list of ranges that map to variables in each 
    function string: [var1_range, var2_range,...]. These values may be 
    single numbers or lists that could be used in range(*i). This 
    range tests the corresponding variable in the string substitution. 
    Singlet values in 'inputs' will be interpreted as range(i), 
    testing from 0 to i.  

    'setup' can be 'pass' for no setup, 'main' to import each function 
    from the local environment, or a list of setup strings that maps 
    to the list 'funcs'. 
    
    Returns a defaultdict that has function names as keys, results as values.
    """
    number = kwargs.get('number', 100000)
    print_conditions = kwargs.get('print_conditions', False)
    performance = defaultdict(list)
    if setups == 'pass':
        # specify no setups for built-in functions like join
        setups = ['pass' for f in funcs]
    elif setups == 'main': 
        # uniformly import all setups from the local environment
        fnames = [f[:f.find("(")] for f in funcs]
        setups = ["from __main__ import " + fname for fname in fnames]
    
    # convert the input ranges to a set of conditions
    conditions = get_conditions(inputs)
    if print_conditions: 
        print "conditions: " + conditions
        
    def timer(func, value, setup):
        return timeit.Timer(func.format(*value), setup=setup)

    for i, f in enumerate(funcs):
        print "testing " + f + "..."
        for value in conditions:
            test = timer(f, value, setups[i])
            result = test.timeit(number=number)
            performance[f].append(list(value) + [result])
    return performance

def get_conditions(inputs = []): 
    """Converts a set of ranges for all variables into an 
    exhaustive list of test conditions for timeit_compare(). 
    """
    # Wrap all singlets in a list for range(*i) below
    var = [[n] if not isinstance(n,(list,tuple)) else n for n in inputs]
    
    # Input like [20] will be interpreted as a range of 0-20. 
    # To hold variables constant use [20,21] or just make it a constant
    # in the function string. 
    ranges = [range(*i) for i in var]
    
    # itertools.product summarizes all combinations of ordered conditions
    # at len = 1 it wraps values in tuples (0,) that confuse the timer below
    if len(inputs) > 1:
        conditions = list(product(*ranges))
    else:
        conditions = [[n] for n in ranges[0]]
    
    return conditions


# TODO: think about putting 2 and 3 grams in different colors
def timeit_plot2D(data, xlabel='xlabel', title='title', **kwargs):
    """Plots the results from a defaultdict returned by timeit_compare.
    
    Each function will be plotted as a different series. 
    
    timeit_compare may test many conditions, and the order of the conditions
    in the results data can be understood from the string substitutions 
    noted in the keys of the defaultdict. By default series=0 means
    that the first series is plotted, but this can be changed to plot 
    any of the testing conditions available. 
    """
    series = kwargs.get('series', 0)
    style = kwargs.get('style', 'line')
    bubble_size = kwargs.get('bubble_size', 500)
    ylabel = kwargs.get('ylabel', 'time')
    dataT = {}
    # set color scheme
    c = iter(cm.rainbow(np.linspace(0, 1, len(data))))
    # transpose the data from [x, y, z]... into ([x...], [y...], [z...])
    for k, v in data.items():
        dataT[k] = zip(*v)
    fig, ax = plt.subplots()
    for k, v in dataT.items():
        if style == 'scatter':
            ax.scatter(v[series], v[-1], s=100, c=next(c), alpha=.75)
        elif style == 'bubble':
            x, y, z = v[series[0]], v[series[1]], v[-1]
            ax.scatter(x, y, s=[bubble_size*i for i in z], c=next(c), alpha=.5)
        else: 
            ax.plot(v[series], v[-1], c=next(c), lw=2)
    try:
        # TODO: fix format() for data across multiple variables/substitutions
        ax.legend([k.format("x") for k in dataT.keys()], loc=2)
    except:
        ax.legend(dataT.keys(), loc=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True)
    return fig


def timeit_plot3D(data, xlabel='xlabel', ylabel='ylabel', **kwargs): 
    """3D plot of timeit data, one chart per function. 
    """
    dataT = {}
    figs = []
    series = kwargs.get('series', (0,1))
    cmap = kwargs.get('cmap', cm.coolwarm)
    for k, v in data.items():
        dataT[k] = zip(*v)
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        X, Y, Z = dataT[k][series[0]], dataT[k][series[1]], dataT[k][-1]
        wide, tall = (max(X)-min(X)+1), (max(Y)-min(Y)+1)
        intervalX = max(X) - min(heapq.nlargest(2,set(X)))
        intervalY = max(Y) - min(heapq.nlargest(2,set(Y)))
        wide, tall = 1+wide/intervalX, 1+tall/intervalY
        X = np.reshape(X, [wide, tall])
        Y = np.reshape(Y, [wide, tall])
        Z = np.reshape(Z, [wide, tall])
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cmap, linewidth=0, antialiased=False)
        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        # TODO: add format() to substitute 'x' and 'y' to make titles neater
        ax.set_title(k)
        fig.colorbar(surf, shrink=0.5, aspect=5)
        figs.append(fig)
    return figs
    
    
def timeit_heatmap(data, xlabel='xlabel', ylabel='ylabel', **kwargs):
    """Heatmap plot of timeit data, one chart per function. 
    """
    dataT = {}
    figs = []
    series = kwargs.get('series', (0,1))
    cmap = kwargs.get('cmap', cm.coolwarm)
    for k, v in data.items():
        dataT[k] = zip(*v)
        X, Y, Z = dataT[k][series[0]], dataT[k][series[1]], dataT[k][-1]
        left, right = min(X), max(X)
        bottom, top = min(Y), max(Y)
        extent = [left, right, bottom, top]
        wide, tall = (max(X)-min(X)+1), (max(Y)-min(Y)+1)
        intervalX = max(X) - min(heapq.nlargest(2,set(X)))
        intervalY = max(Y) - min(heapq.nlargest(2,set(Y)))
        try: 
            wide = 1 + wide/intervalX
        except:
            wide = 1
        try: 
            tall = 1 + tall/intervalY
        except: 
            tall = 1
        Z = np.reshape(Z, [wide, -1])
        Z = list(zip(*Z))           # Z is transposed
        Z = [i for i in Z[::-1]]    # Z is upside down
        fig, ax = plt.subplots()
        hmap = ax.imshow(Z, extent=extent, cmap=cmap, interpolation='nearest')
        fig.colorbar(hmap).set_label("time")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        # TODO: add format() to substitute 'x' and 'y' to make titles neater
        ax.set_title(k)
        figs.append(fig)
    return figs
