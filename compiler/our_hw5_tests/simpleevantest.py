def f(x):
    print x
    print y
    print z
    return lambda: x + y + z
y = 2
z = 3
print f(1)()
