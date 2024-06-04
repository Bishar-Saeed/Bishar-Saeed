

def fibonacci_num():
    a = 0
    print(a)
    b = 1
    print(b)
    x = 1
    y = 1
    for i in range(0, 10):
        z = x + y
        x = y
        y = z
        print(z)

fibonacci_num()
