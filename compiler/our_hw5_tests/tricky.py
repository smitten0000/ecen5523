def f(x):
    b = lambda: z
    z = x
    return b
a = f(1)
print a()
a = f(2)
print a()
