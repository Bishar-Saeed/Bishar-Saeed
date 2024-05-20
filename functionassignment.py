
x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
def list_function(x):

    y = 0
    for i in range(len(x)):
        if x[i] % 2 == 0:
            y = y + x[i]
    print(y)

list_function(x)
