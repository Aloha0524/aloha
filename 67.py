import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('ex1data1.txt', names=['population', 'profit'])
print(data.head())

data.insert(0, 'ones', 1, True)
print(data.head())
print(data.describe())

X = data.iloc[:, 0:-1]
Y = data.iloc[:, -1]
print(X.head())
print(Y.head())

X = X.values
Y = Y.values
print(X.shape)  # (97, 2)
print(Y.shape)  # (97,)

Y = Y.reshape(97, 1)
print(Y.shape)  # (97, 1)


def CostFunction(X, Y, theta):
    inner = np.power((X @ theta - Y), 2)
    return np.sum(inner) / (2 * len(X))


# 修正这里的theta初始化
theta = np.zeros((2, 1))  # 应该是 (2, 1) 而不是 (2,1)
print(theta.shape)  # (2, 1)


def GradientDescent(X, Y, theta, alpha, times):
    costs = []
    m = len(Y)  # 样本数量

    for i in range(times):
        # 计算预测值
        predictions = X @ theta

        # 计算误差
        error = predictions - Y

        # 计算梯度
        gradient = (X.T @ error) / m

        # 更新theta参数
        theta = theta - alpha * gradient

        # 计算并记录当前代价
        cost = CostFunction(X, Y, theta)
        costs.append(cost)

        # 每100次迭代打印一次成本
        if i % 100 == 0:
            print(f'迭代次数 {i}: 成本 = {cost}')

    return theta, costs


# 使用梯度下降
alpha = 0.01  # 学习率
iterations = 1000  # 迭代次数

final_theta, cost_history = GradientDescent(X, Y, theta, alpha, iterations)

print(f'\n最终参数 theta: {final_theta.ravel()}')
print(f'最终成本: {CostFunction(X, Y, final_theta)}')

# 可视化结果
plt.figure(figsize=(12, 5))

# 子图1：数据点和拟合直线
plt.subplot(1, 2, 1)
plt.scatter(X[:, 1], Y, marker='x', color='red', label='训练数据')
plt.xlabel('人口 (万)')
plt.ylabel('利润 (万)')
plt.title('人口 vs 利润')

# 绘制拟合直线
x_values = np.array([np.min(X[:, 1]), np.max(X[:, 1])])
y_values = final_theta[0] + final_theta[1] * x_values
plt.plot(x_values, y_values, color='blue', label='线性回归拟合')
plt.legend()

# 子图2：成本函数下降曲线
plt.subplot(1, 2, 2)
plt.plot(range(iterations), cost_history, color='green')
plt.xlabel('迭代次数')
plt.ylabel('成本')
plt.title('成本函数下降曲线')
plt.grid(True)

plt.tight_layout()
plt.show()


# 进行预测
def predict(x, theta):
    """预测函数"""
    return theta[0] + theta[1] * x


# 示例预测
population_1 = 3.5
profit_pred_1 = predict(population_1, final_theta)
print(f'\n预测: 人口 {population_1} 万 -> 利润 {profit_pred_1[0]:.2f} 万')

population_2 = 7.0
profit_pred_2 = predict(population_2, final_theta)
print(f'预测: 人口 {population_2} 万 -> 利润 {profit_pred_2[0]:.2f} 万')