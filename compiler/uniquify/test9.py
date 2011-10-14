x = 1
y = 2
print x == y
z = 3
def y(x):
    y = 2
    return lambda w: w + x + y + z
print y(1)(4)
