def f(x):
    def g(x):
        return lambda w: x + y + z
    return g(x)
y = 2
z = 3
print f(1)(4)
