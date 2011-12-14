# vim: set ts=4 sw=4 expandtab:
def fill(list, i, height):
    if i != height:
        j=0
        while j != 4:
            list[j]=[0,1,2,3]
            fill(list[j], i+1, height)
            j = j + 1
    else:
        0

head=[0,1,2,3]
fill(head, 0, input())
print 777
input()
