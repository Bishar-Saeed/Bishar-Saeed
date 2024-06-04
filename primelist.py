x=[1,2,3,4,5,6,7,8,9,10]

for num in range(len(x)):
    print(x[num])
    for i in range(len(x)):
        if x[num]:




# x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#
# for num in x:
#     if num > 1:
#         is_prime = True
#         for i in range(2, num):
#             if (num % i) == 0:
#                 is_prime = False
#                 break
#         if is_prime:
#             print(num, "is a prime number")