import collections
It = collections.Iterable
import string

letters = string.ascii_letters
#digits = [ str(i) for i in range(100)]

def load_data(fn,split_lines=False):
    FH = open(fn,'r')
    data = FH.read().strip()
    FH.close()
    if split_lines:  return data.split('\n')
    return data

def flatten(L):
    for e in L:
        if isinstance(e, It) and not isinstance(e, basestring):
            for sub in flatten(e):
                yield sub
        else:
            yield e
            
def print_list(L, n=3):
    while L:
        for e in L[:n]:
	    print e,
        print
        L = L[n:]

def list_elements(t, sort_them=True):
    return sorted(list(set(list(flatten(t)))))
    
def groups(L,N=3):
    R = range(0,len(L),N)
    return [L[i:i+N] for i in R]
