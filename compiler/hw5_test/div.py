def div(x, y):
    return 0 if x < y else 1 + div(x + -y, y)

print div(12, 3)
