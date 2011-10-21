def f1(x, y, z):
	return lambda x, y: x + y + z

g1 = f1(1000, 10000, 10)
print g1(100, 1000)
