y = 1
class A:
    print y
    y = 2
    x = 1
# should print 1, since assignment to class attribute 'A.y'
# is after print statement
a = A()
print a.x
