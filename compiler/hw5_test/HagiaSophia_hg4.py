def f1():
    def f2():
        def f3():
            print y
        y = 17
        f3()
    print 49
    f2()
y = 34
print y
f1()
