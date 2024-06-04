def gcf_lcm(x,y,z):
    if y < z:
          smaller = y
    elif y > z:
          smaller = z

    if x=="lcm":
      for i in range(1,smaller):
            if y % i == 0 and z % i == 0:
                lcm = i
            print(lcm)
    elif x=="gcf":

      for i in range(1,smaller):
          if y % i == 0 and z % i == 0:
                print(i)

gcf_lcm("lcm", 100, 300)