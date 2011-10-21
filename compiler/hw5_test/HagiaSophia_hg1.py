def fib(a, b, n, top):
	print b
	return b if n == top else fib(b, a+b, n+1, top)

fib(1, 1, 1, input())
