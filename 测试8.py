while True:
    try:
        a = int(input("请输入成绩："))
        if 0 <= a <= 100:
            if a >= 60:
                if a >= 70:
                    if a >= 80:
                        if a >= 90:
                            grade = "A(优秀)"
                        else:
                            grade = "B(良好)"
                    else:
                        grade = "C(中等)"
                else:
                    grade = "D(及格)"
            else:
                grade = "E(不及格)"
            print(f"等级为：{grade}")
            break
        else:
            print("成绩必须在0~100之间，请重新输入\n")
    except ValueError:
        print("输入不是有效数字，请重新输入\n")
