
def func1(d):
    print(d['c'])

def func2(d):
    print(d['x'])

def func3(d):
    print(d['m'])



d = {'alpha': {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5},
     'beta':  {'z': 11, 'y': 12, 'x': 13},
     'gamma': {'k': 21, 'l': 22, 'm':23, 'n':24}}

funcd = {'R1':func1, 'R2':func2, 'R3':func3}


funcd['R1'](d['alpha'])
funcd['R2'](d['beta'])
funcd['R3'](d['gamma'])


