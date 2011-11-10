class A:
    def f(self, a, b):
        print a
        return b
a = A()
print A.f(a, 1, 2)
