x=1
def x(x):
    x = 2
    return lambda x: x + y # y is undef, should throw error
print x(3)(4)
x=2
