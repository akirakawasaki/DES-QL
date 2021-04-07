
def func(d):
    print(d['c'])



d = {'alpha': {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5},
     'beta':  {'z': 11, 'y': 12, 'x': 13}}

func(d['alpha'])
func(d['beta'])
