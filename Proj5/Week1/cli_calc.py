# Simple Calc

def add(*args):
    res = 0
    for i in args:
        res+=i
    return res


def sub(*args):
    res = 0
    for i in args:
        res-=i
    return res


def mul(*args):
    res = 1
    for i in args:
        res*=i
    return res


def div(*args):
    res = 0
    for i in args:
        res/=i
    return res



    