x=[1,2,3,4,5,6,7,8,9,10,12,14,16]
evennumber=0
oddnumber=0
for i in range(0,len(x)):
    if x[i]%2==0:
        evennumber=evennumber+1
    else:
        oddnumber=oddnumber+1j
print(evennumber)
print(oddnumber)