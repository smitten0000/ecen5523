x = 1
def a():
    return x
x = 2
# SSA form
# x_0 = 1
# def a_0():
#   return x   <-- do we refer to x_0 or x_1 here, or does it matter?  I think x_1, and it doesn't matter
# x_1 = 2
