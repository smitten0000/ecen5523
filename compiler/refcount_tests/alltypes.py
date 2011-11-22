x = []
y = {}
class Z:
    a = 1
    def __init__(self):
        self.b = 2

c = Z.a
# unbound method
d = Z.__init__
# bound method
e = Z().__init__

