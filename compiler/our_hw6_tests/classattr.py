class A:
    0
print 1

class B:
    0
print 2

class C(A,B):
    0

C.x = 1
B.y = 2
A.z = 3
print C.x
print B.y
print A.z
