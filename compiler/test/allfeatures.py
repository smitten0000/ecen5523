a = {1:2}
print a
a = 0

class B:
    x = 1

print B.x
b = B()
b.y = 2
print b.y
b = 0

class C(B):
    y = 2
c = C()
c.z = 3
print c.x
print c.y
print c.z

def f(x,y):
    g = lambda x: x
    i = 0
    lst = []
    while i !=  10000:
        lst = lst + [[i]]
        i = i + 1
    return g(lst)

print f(1,2)


