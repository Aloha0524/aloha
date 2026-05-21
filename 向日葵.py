import turtle
import math


# ---------- 辅助函数：以 (cx, cy) 为圆心画圆 ----------
def draw_circle(t, cx, cy, radius, fill_color=None, pen_color=None):
    """精确绘制以 (cx,cy) 为圆心的圆，支持填充和边框颜色"""
    t.penup()
    # 移动到圆的最底点（此时圆心在海龟正上方）
    t.goto(cx, cy - radius)
    t.setheading(0)  # 朝东
    t.pendown()
    if fill_color:
        t.fillcolor(fill_color)
        t.begin_fill()
    if pen_color:
        t.pencolor(pen_color)
    t.circle(radius)
    if fill_color:
        t.end_fill()
    t.penup()


# ---------- 绘制花盘（圆心对齐） ----------
def draw_flower_disc(t, x, y):
    """花盘：外圈 + 内圈 + 网格纹路，所有圆精确以 (x,y) 为圆心"""
    # 外圈深褐色
    draw_circle(t, x, y, 50, fill_color="#8B4513", pen_color="#8B4513")
    # 内圈棕色
    draw_circle(t, x, y, 45, fill_color="#A0522D", pen_color="#A0522D")
    # 网格纹路
    draw_grid_pattern(t, x, y)


def draw_grid_pattern(t, x, y):
    """同心圆 + 辐射线，所有圆圆心均为 (x,y)"""
    t.pensize(1)
    t.pencolor("#654321")
    # 同心圆
    for radius in range(10, 45, 8):
        draw_circle(t, x, y, radius)  # 只画轮廓，无填充
    # 辐射线
    for angle in range(0, 360, 15):
        t.penup()
        t.goto(x, y)
        t.setheading(angle)
        t.pendown()
        t.forward(45)
        t.penup()


# ---------- 绘制花瓣（从真实花盘边缘开始） ----------
def draw_petals(t, x, y):
    """两层花瓣，起点为以 (x,y) 为圆心、半径 50 的圆上"""
    # 外层 20 片
    draw_petal_layer(t, x, y, 20, 80, 25, "#FFD700", "#FFA500")
    # 内层 12 片
    draw_petal_layer(t, x, y, 12, 60, 20, "#FFC107", "#FF8C00")


def draw_petal_layer(t, x, y, num, length, width, fill_color, edge_color):
    """每片花瓣从花盘边缘 (半径50的圆上) 向外延伸"""
    disc_radius = 50
    angle_step = 360 / num

    for i in range(num):
        angle = i * angle_step
        # 计算花盘边缘的起点坐标
        rad = math.radians(angle)
        start_x = x + disc_radius * math.cos(rad)
        start_y = y + disc_radius * math.sin(rad)

        # 移动到起点，并朝向径向外侧
        t.penup()
        t.goto(start_x, start_y)
        t.setheading(angle)  # 沿半径方向向外
        t.pendown()

        t.fillcolor(fill_color)
        t.pencolor(edge_color)
        t.begin_fill()

        # 绘制花瓣轮廓（简单自然的弧线）
        t.left(30)  # 向左偏转开始画左翼
        t.circle(width, 40)  # 基部凸起
        t.circle(length, 30)  # 中段延伸
        t.circle(width, 40)  # 顶部收拢
        # 闭合路径：直接回到起点
        t.goto(start_x, start_y)

        t.end_fill()
        # 恢复方向（避免影响下一片）
        t.setheading(angle)


# ---------- 花茎 ----------
def draw_stem(t, x, y):
    t.penup()
    t.goto(x, y - 50)
    t.pendown()
    t.pensize(12)
    t.pencolor("#228B22")
    t.goto(x, y - 250)


# ---------- 叶子 (已修改：完全对齐主干) ----------
def draw_leaves(t, x, y):
    t.pensize(2)
    t.color("#228B22", "#98FB98")

    # 左叶子：从主干出发，对称位置
    t.penup()
    t.goto(x, y - 120)  # 直接对齐主干中心线
    t.pendown()
    t.begin_fill()
    t.setheading(160)
    t.forward(75)
    t.right(110)
    t.forward(38)
    t.right(70)
    t.forward(75)
    t.end_fill()
    draw_single_vein(t, x, y - 120, 160, 75)

    # 右叶子：对称高度，对齐主干
    t.penup()
    t.goto(x, y - 180)  # 和左叶对称分布
    t.pendown()
    t.begin_fill()
    t.setheading(20)
    t.forward(75)
    t.left(110)
    t.forward(38)
    t.left(70)
    t.forward(75)
    t.end_fill()
    draw_single_vein(t, x, y - 180, 20, 75)


def draw_single_vein(t, sx, sy, angle, length):
    t.pencolor("#006400")
    t.pensize(1.5)
    # 主脉
    t.penup()
    t.goto(sx, sy)
    t.setheading(angle)
    t.pendown()
    t.forward(length)
    # 侧脉
    for i in range(1, 3):
        # 左侧脉
        t.penup()
        t.goto(sx + math.cos(math.radians(angle)) * (length / 3) * i,
               sy + math.sin(math.radians(angle)) * (length / 3) * i)
        t.setheading(angle + 45)
        t.pendown()
        t.forward(length / 3)
        t.penup()
        # 右侧脉
        t.goto(sx + math.cos(math.radians(angle)) * (length / 3) * i,
               sy + math.sin(math.radians(angle)) * (length / 3) * i)
        t.setheading(angle - 45)
        t.pendown()
        t.forward(length / 3)
        t.penup()


# ---------- 主函数 ----------
def draw_sunflower():
    screen = turtle.Screen()
    screen.setup(700, 700)
    screen.title("向日葵")
    screen.bgcolor("#87CEEB")
    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    center_x, center_y = 0, 50  # 花盘中心

    draw_stem(t, center_x, center_y)
    draw_leaves(t, center_x, center_y)
    draw_petals(t, center_x, center_y)
    draw_flower_disc(t, center_x, center_y)

    screen.mainloop()


if __name__ == "__main__":
    draw_sunflower()