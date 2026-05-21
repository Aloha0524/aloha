
import h5py
import numpy as np
import os
import matplotlib.pyplot as plt


# ==============================================
# 猫和非猫图像二分类项目 - 逻辑回归模型
# 开发者：cym  学号：2303080901
# 功能：使用逻辑回归对64×64像素的猫和非猫图像进行二分类
# 特点：手动实现带L2正则化的逻辑回归算法
# ==============================================

def load_dataset():
    """
    加载猫和非猫数据集
    cym - 数据加载模块
    """
    try:
        # 数据集文件路径 - 请确保文件存在正确位置
        training_path = r'C:\Users\admin\Downloads\train_catvnoncat.h5'
        testing_path = r'C:\Users\admin\Downloads\test_catvnoncat(1).h5'

        # 验证文件存在性
        if not os.path.isfile(training_path):
            raise FileNotFoundError(f"训练集文件未找到: {training_path}")
        if not os.path.isfile(testing_path):
            raise FileNotFoundError(f"测试集文件未找到: {testing_path}")

        # 读取训练集数据
        with h5py.File(training_path, 'r') as hf:
            X_train = np.array(hf['train_set_x'])
            y_train = np.array(hf['train_set_y'])

        # 读取测试集数据
        with h5py.File(testing_path, 'r') as hf:
            X_test = np.array(hf['test_set_x'])
            y_test = np.array(hf['test_set_y'])

        print(f"✓ 数据集加载成功")
        print(f"  - 训练集: {X_train.shape[0]} 张图像 ({X_train.shape[1]}×{X_train.shape[2]})")
        print(f"  - 测试集: {X_test.shape[0]} 张图像 ({X_test.shape[1]}×{X_test.shape[2]})")
        return X_train, y_train, X_test, y_test

    except Exception as err:
        print(f"✗ 数据加载失败: {str(err)}")
        return None, None, None, None


def generate_synthetic_data():
    """
    生成合成数据集用于演示
    cym - 数据生成模块
    """
    print("⚠️  使用合成数据集进行演示...")

    # 生成模拟的猫和非猫图像数据
    num_train, num_test = 209, 50
    img_size = 64

    # 训练集数据
    X_train = np.random.randint(0, 256, (num_train, img_size, img_size, 3), dtype=np.uint8)
    y_train = np.concatenate([np.ones(105), np.zeros(104)]).astype(int)
    np.random.shuffle(y_train)

    # 测试集数据
    X_test = np.random.randint(0, 256, (num_test, img_size, img_size, 3), dtype=np.uint8)
    y_test = np.concatenate([np.ones(25), np.zeros(25)]).astype(int)
    np.random.shuffle(y_test)

    return X_train, y_train, X_test, y_test


def sigmoid_function(z):
    """
    Sigmoid激活函数实现
    cym - 激活函数模块
    """
    # 数值稳定处理
    z_clipped = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z_clipped))


def calculate_loss(y_actual, y_prob):
    """
    计算交叉熵损失函数
    cym - 损失函数模块
    """
    # 防止log(0)的数值稳定性处理
    epsilon = 1e-15
    y_prob_clipped = np.clip(y_prob, epsilon, 1 - epsilon)

    # 计算交叉熵损失
    loss = -np.mean(y_actual * np.log(y_prob_clipped) +
                    (1 - y_actual) * np.log(1 - y_prob_clipped))
    return loss


def calculate_accuracy(y_true, y_pred):
    """
    计算分类准确率
    cym - 评估指标模块
    """
    return np.mean(y_true == y_pred)


def visualize_predictions(images, true_labels, pred_probs, pred_labels,
                          title_suffix="", max_display=12):
    """
    可视化图像及其预测结果
    cym - 可视化模块
    """
    # 设置显示布局
    cols = 4
    rows = min((max_display + cols - 1) // cols, len(images))

    # 创建图形
    plt.figure(figsize=(16, 4 * rows))
    plt.suptitle(f'Image Classification Results - {title_suffix}', fontsize=14, y=0.98)

    # 显示图像
    for idx in range(min(max_display, len(images))):
        plt.subplot(rows, cols, idx + 1)

        # 显示图像
        plt.imshow(images[idx])
        plt.axis('off')

        # 获取标签信息
        true_class = "Cat" if true_labels[idx] == 1 else "Non-Cat"
        pred_class = "Cat" if pred_labels[idx] == 1 else "Non-Cat"
        confidence = pred_probs[idx] * 100

        # 设置标题颜色（正确为绿色，错误为红色）
        title_color = 'darkgreen' if true_labels[idx] == pred_labels[idx] else 'darkred'

        # 添加标题
        plt.title(f'True: {true_class}\nPred: {pred_class}\nConfidence: {confidence:.1f}%',
                  color=title_color, fontsize=9, pad=8)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()


class CustomLogisticRegression:
    """
    自定义逻辑回归分类器（带L2正则化）
    cym - 模型实现模块
    """

    def __init__(self, learning_rate=0.01, iterations=1000, regularization=0.1):
        """初始化模型参数"""
        self.learning_rate = learning_rate
        self.iterations = iterations
        self.regularization = regularization
        self.weights = None
        self.bias = None
        self.training_loss = []

    def train(self, X, y):
        """训练逻辑回归模型"""
        num_samples, num_features = X.shape

        # 初始化参数
        self.weights = np.zeros(num_features)
        self.bias = 0.0

        print(f"\n🚀 开始训练逻辑回归模型")
        print(f"   学习率: {self.learning_rate}")
        print(f"   迭代次数: {self.iterations}")
        print(f"   正则化强度: {self.regularization}")
        print("-" * 50)

        # 梯度下降优化
        for epoch in range(self.iterations):
            # 前向传播
            linear_output = np.dot(X, self.weights) + self.bias
            predicted_probs = sigmoid_function(linear_output)

            # 计算损失（包含L2正则化）
            data_loss = calculate_loss(y, predicted_probs)
            reg_loss = 0.5 * self.regularization * np.sum(self.weights ** 2) / num_samples
            total_loss = data_loss + reg_loss
            self.training_loss.append(total_loss)

            # 计算梯度
            weight_gradient = (np.dot(X.T, (predicted_probs - y)) / num_samples) + \
                              (self.regularization * self.weights / num_samples)
            bias_gradient = np.mean(predicted_probs - y)

            # 更新参数
            self.weights -= self.learning_rate * weight_gradient
            self.bias -= self.learning_rate * bias_gradient

            # 定期输出训练进度
            if epoch % 200 == 0 or epoch == self.iterations - 1:
                predictions = (predicted_probs >= 0.5).astype(int)
                accuracy = calculate_accuracy(y, predictions)
                print(f"迭代 {epoch:4d}: 损失 = {total_loss:.4f}, 准确率 = {accuracy:.4f}")

    def predict_probabilities(self, X):
        """预测概率"""
        linear_output = np.dot(X, self.weights) + self.bias
        return sigmoid_function(linear_output)

    def predict_classes(self, X, threshold=0.5):
        """预测类别"""
        probabilities = self.predict_probabilities(X)
        return (probabilities >= threshold).astype(int)


# ==============================================
# 主程序执行入口
# cym - 2303080901
# ==============================================
if __name__ == "__main__":
    print("=" * 70)
    print("🎯 猫和非猫图像二分类系统 - 逻辑回归实现")
    print(f"   开发者: cym | 学号: 2303080901")
    print("=" * 70)

    # 1. 加载数据
    X_train_original, y_train_original, X_test_original, y_test_original = load_dataset()

    # 如果数据加载失败，使用合成数据
    if X_train_original is None:
        X_train_original, y_train_original, X_test_original, y_test_original = generate_synthetic_data()

    # 2. 数据预处理
    print("\n🔧 数据预处理中...")

    # 展平图像数据 (m, 64, 64, 3) -> (m, 12288)
    X_train_flat = X_train_original.reshape(X_train_original.shape[0], -1)
    X_test_flat = X_test_original.reshape(X_test_original.shape[0], -1)

    # 特征标准化 (像素值归一化到[0,1])
    X_train_normalized = X_train_flat / 255.0
    X_test_normalized = X_test_flat / 255.0

    # 标签形状调整
    y_train = y_train_original.reshape(-1)
    y_test = y_test_original.reshape(-1)

    print(f"   ✓ 训练集: {X_train_normalized.shape}")
    print(f"   ✓ 测试集: {X_test_normalized.shape}")
    print(f"   ✓ 训练集标签分布: 猫 {np.sum(y_train)}张, 非猫 {len(y_train) - np.sum(y_train)}张")

    # 3. 模型训练
    model = CustomLogisticRegression(
        learning_rate=0.1,
        iterations=1000,
        regularization=0.01
    )
    model.train(X_train_normalized, y_train)

    # 4. 模型评估
    print("\n📊 模型评估结果")
    print("-" * 50)

    # 训练集评估
    train_predictions = model.predict_classes(X_train_normalized)
    train_probabilities = model.predict_probabilities(X_train_normalized)
    train_accuracy = calculate_accuracy(y_train, train_predictions)

    # 测试集评估
    test_predictions = model.predict_classes(X_test_normalized)
    test_probabilities = model.predict_probabilities(X_test_normalized)
    test_accuracy = calculate_accuracy(y_test, test_predictions)

    print(f"训练集准确率: {train_accuracy:.4f} ({train_accuracy * 100:.2f}%)")
    print(f"测试集准确率: {test_accuracy:.4f} ({test_accuracy * 100:.2f}%)")

    # 5. 结果可视化
    print("\n🖼️  结果可视化展示")

    # 随机选择测试集图像展示
    np.random.seed(42)
    random_test_indices = np.random.choice(len(X_test_original), min(12, len(X_test_original)), replace=False)

    visualize_predictions(
        X_test_original[random_test_indices],
        y_test[random_test_indices],
        test_probabilities[random_test_indices],
        test_predictions[random_test_indices],
        title_suffix="Random Test Samples",
        max_display=12
    )

    # 展示正确预测的猫图像
    correct_cat_indices = np.where((y_test == 1) & (test_predictions == 1))[0]
    if len(correct_cat_indices) > 0:
        selected_indices = correct_cat_indices[:min(8, len(correct_cat_indices))]
        visualize_predictions(
            X_test_original[selected_indices],
            y_test[selected_indices],
            test_probabilities[selected_indices],
            test_predictions[selected_indices],
            title_suffix="Correctly Predicted Cats",
            max_display=len(selected_indices)
        )

    # 展示正确预测的非猫图像
    correct_noncat_indices = np.where((y_test == 0) & (test_predictions == 0))[0]
    if len(correct_noncat_indices) > 0:
        selected_indices = correct_noncat_indices[:min(8, len(correct_noncat_indices))]
        visualize_predictions(
            X_test_original[selected_indices],
            y_test[selected_indices],
            test_probabilities[selected_indices],
            test_predictions[selected_indices],
            title_suffix="Correctly Predicted Non-Cats",
            max_display=len(selected_indices)
        )

    # 展示预测错误的图像
    incorrect_indices = np.where(y_test != test_predictions)[0]
    if len(incorrect_indices) > 0:
        selected_indices = incorrect_indices[:min(8, len(incorrect_indices))]
        visualize_predictions(
            X_test_original[selected_indices],
            y_test[selected_indices],
            test_probabilities[selected_indices],
            test_predictions[selected_indices],
            title_suffix="Incorrect Predictions",
            max_display=len(selected_indices)
        )

    print("\n" + "=" * 70)
    print("🏆 模型训练与评估完成！")
    print(f"   开发者: cym | 学号: 2303080901")
    print("=" * 70)
