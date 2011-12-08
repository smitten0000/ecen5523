def mult(x, y):
    return 0 if x == 0 else (y if x == 1 else y + mult(x + -1, y))

def less_helper(x, y, xp, yp):
    return True if xp == y else (False if yp == x else less_helper(x, y, xp + 1, yp + 1))

def less(x, y):
    return less_helper(x, y, x + 1, y)

def div(x, y):
    return 0 if less(x, y) else 1 + div(x + -y, y)

def derivative(f):
    epsilon = 1
    return lambda x: div(f(mult(10,x)+epsilon) + -f(mult(10,x)), mult(epsilon, 10))

def square(x):
    return mult(x, x)


n = input()
sieve = []

#initialize the sieve values so everything is a prime
i = 0
while less(i,n):
	sieve = sieve + [[i, True]]
	i = i + 1

nover2 = div(n, 2)
i = 2
# mark values with a factor as not a prime
while less(i, nover2):
	if sieve[i][1] is True:
		j = mult(2, i)
		while less(j, n):
			sieve[j] = [j, False]
			j = j + i
	else:
		b=0
		
	i = i + 1

i = 2
while less(i, n):
	if sieve[i][1] is True:
		print sieve[i][0]
	else:
		b = 0
	i = i + 1