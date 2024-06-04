def gcf_lcm(x,y,z):

    if x=="lcm":
        for i in range(1,17):
            if y % i == 0 and z % i == 0:
                 lcm = i
        print(int(y*z/lcm))

    elif x=="gcf":
        for i in range(1,17):
          if y % i == 0 and z % i == 0:
                print(i)

gcf_lcm("gcf",10,15)

# def factorial(n):
#     result=1
#     for i in range(1,n+1):
#         result=result*i
#         print(result)
# factorial(5)
