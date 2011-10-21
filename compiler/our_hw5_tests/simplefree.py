def y(z):
    return z
def a(b):
    return lambda: y(b())
print a(lambda:1)()
