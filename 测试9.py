#total = 0
#count = 0
#while True:
#    try:
#        score = float(input("请输入分数："))
#        total += score
#        count += 1
#    except ValueError:
#        print("输入的不是有效分数，请重新输入")
#        continue
#    choice = input("是否继续输入？(y /n )：").strip().lower()
#    if choice == "n":
#        average = total / count
#        print(f"所有分数的平均分是：{average:.2f}")
#        break
#    elif choice != "y":
#        print("输入错误，请输入y 或n ")


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
primes = [a for a in range(0, 101) if is_prime(a)]
print("0到100内的素数有：")
print(primes)
print(f"\n共有 {len(primes)} 个素数")


#能被7，不能5
for i in range(0, 100):
    if i % 7 == 0 and i % 5 != 0:
        print(i)
        print(i, end=" ")
