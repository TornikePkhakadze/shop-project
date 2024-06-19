def raxac(n):
    if n < 0:
        print("araswora")
    elif n == 0:
        return 0
    elif n == 1 or n == 2:
        return 1
    else:
        return raxac(n-1) + raxac(n-2)

print(raxac(3))


 