x=1
z=2
def a():
    f = lambda: z
    z = 3
    return f
print a()()
