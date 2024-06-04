x=[1,2,3,4,5,6,8,7,9,10]
y=0
for i in range(len(x)):
    if x[i] % 2 == 0:
        y = y + x[i]
print(y)