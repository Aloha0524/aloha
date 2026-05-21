import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv1D, MaxPooling1D, Flatten, Dense, Dropout,
    LSTM, Embedding, Concatenate, BatchNormalization
)
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping

# ========================= 1. 加载数据 =========================
df = pd.read_csv('synthetic_dna_dataset.csv')
print("数据集大小:", df.shape)
print("类别分布:\n", df['Class_Label'].value_counts())


# ========================= 2. 序列预处理 =========================
def dna_to_int(seq, max_len=500):
    """将DNA序列转换为固定长度的整数列表（A=1,T=2,G=3,C=4,其他=0）"""
    mapping = {'A': 1, 'T': 2, 'G': 3, 'C': 4}
    # 只取前max_len个字符，不足补0
    int_seq = [mapping.get(char.upper(), 0) for char in seq[:max_len]]
    if len(int_seq) < max_len:
        int_seq += [0] * (max_len - len(int_seq))
    return int_seq

MAX_SEQ_LEN = 500  # 可根据实际序列长度分布调整，当前数据长度均为100，可设为200
df['seq_encoded'] = df['Sequence'].apply(lambda x: dna_to_int(x, MAX_SEQ_LEN))
X_seq = np.array(df['seq_encoded'].tolist())  # shape: (n_samples, MAX_SEQ_LEN)

# ========================= 3. 提取统计特征（可选） =========================
# 使用已有的数值列作为统计特征
stat_cols = ['GC_Content', 'AT_Content', 'Sequence_Length',
             'Num_A', 'Num_T', 'Num_C', 'Num_G', 'kmer_3_freq']
# 检查这些列是否都存在
missing = [col for col in stat_cols if col not in df.columns]
if missing:
    print(f"警告：以下列不存在，将不使用统计特征: {missing}")
    stat_cols = [col for col in stat_cols if col in df.columns]

if stat_cols:
    X_stat = df[stat_cols].values
    scaler = StandardScaler()
    X_stat = scaler.fit_transform(X_stat)
    use_stat = True
else:
    X_stat = None
    use_stat = False

# ========================= 4. 标签编码 =========================
le = LabelEncoder()
y_int = le.fit_transform(df['Class_Label'])
num_classes = len(le.classes_)
y_cat = to_categorical(y_int, num_classes)
print("类别映射:", dict(zip(le.classes_, range(num_classes))))

# ========================= 5. 划分数据集 =========================
X_seq_train, X_seq_test, y_train, y_test = train_test_split(
    X_seq, y_cat, test_size=0.2, random_state=42, stratify=y_int)
if use_stat:
    X_stat_train, X_stat_test = train_test_split(
        X_stat, test_size=0.2, random_state=42, stratify=y_int)
else:
    X_stat_train = X_stat_test = None

# 再从训练集中划分验证集（15%训练，5%验证？这里直接再分，或使用validation_split）
X_seq_train, X_seq_val, y_train, y_val = train_test_split(
    X_seq_train, y_train, test_size=0.2, random_state=42)  # 0.2*0.8=0.16总体验证
if use_stat:
    X_stat_train, X_stat_val = train_test_split(
        X_stat_train, test_size=0.2, random_state=42)

print(f"训练集: {X_seq_train.shape}, 验证集: {X_seq_val.shape}, 测试集: {X_seq_test.shape}")


# ========================= 6. 构建通用模型函数 =========================
def build_cnn(seq_shape, stat_dim=None, num_classes=4):
    seq_input = Input(shape=seq_shape, name='seq_input')
    # Embedding: 输入维度5（0~4），输出16维
    x = Embedding(input_dim=5, output_dim=16, input_length=seq_shape[0])(seq_input)
    x = Conv1D(filters=64, kernel_size=5, activation='relu', padding='same')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=128, kernel_size=5, activation='relu', padding='same')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=256, kernel_size=3, activation='relu', padding='same')(x)
    x = GlobalMaxPooling1D()(x)  # 替代Flatten，减少参数
    x = Dropout(0.3)(x)

    if stat_dim is not None:
        stat_input = Input(shape=(stat_dim,), name='stat_input')
        y = Dense(32, activation='relu')(stat_input)
        y = BatchNormalization()(y)
        combined = Concatenate()([x, y])
        z = Dense(64, activation='relu')(combined)
    else:
        z = x

    z = Dropout(0.3)(z)
    output = Dense(num_classes, activation='softmax')(z)

    if stat_dim is not None:
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        model = Model(inputs=seq_input, outputs=output)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


def build_lstm(seq_shape, stat_dim=None, num_classes=4):
    seq_input = Input(shape=seq_shape, name='seq_input')
    x = Embedding(input_dim=5, output_dim=16, input_length=seq_shape[0])(seq_input)
    x = LSTM(64, return_sequences=False, dropout=0.2)(x)
    x = Dropout(0.3)(x)

    if stat_dim is not None:
        stat_input = Input(shape=(stat_dim,), name='stat_input')
        y = Dense(32, activation='relu')(stat_input)
        y = BatchNormalization()(y)
        combined = Concatenate()([x, y])
        z = Dense(64, activation='relu')(combined)
    else:
        z = x

    z = Dropout(0.3)(z)
    output = Dense(num_classes, activation='softmax')(z)

    if stat_dim is not None:
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        model = Model(inputs=seq_input, outputs=output)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


# 由于TF 2.x中GlobalMaxPooling1D需要导入
from tensorflow.keras.layers import GlobalMaxPooling1D


# 重新定义build_cnn使用GlobalMaxPooling1D
def build_cnn(seq_shape, stat_dim=None, num_classes=4):
    seq_input = Input(shape=seq_shape, name='seq_input')
    x = Embedding(input_dim=5, output_dim=16, input_length=seq_shape[0])(seq_input)
    x = Conv1D(filters=64, kernel_size=5, activation='relu', padding='same')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=128, kernel_size=5, activation='relu', padding='same')(x)
    x = MaxPooling1D(pool_size=2)(x)
    x = Conv1D(filters=256, kernel_size=3, activation='relu', padding='same')(x)
    x = GlobalMaxPooling1D()(x)
    x = Dropout(0.3)(x)

    if stat_dim is not None and stat_dim > 0:
        stat_input = Input(shape=(stat_dim,), name='stat_input')
        y = Dense(32, activation='relu')(stat_input)
        y = BatchNormalization()(y)
        combined = Concatenate()([x, y])
        z = Dense(64, activation='relu')(combined)
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        z = x
        model = Model(inputs=seq_input, outputs=output)
    z = Dropout(0.3)(z)
    output = Dense(num_classes, activation='softmax')(z)
    if stat_dim is not None and stat_dim > 0:
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        model = Model(inputs=seq_input, outputs=output)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


from tensorflow.keras.layers import GlobalMaxPooling1D


def build_cnn(seq_shape, stat_dim=None, num_classes=4):
    seq_input = Input(shape=seq_shape, name='seq_input')
    x = Embedding(5, 16, input_length=seq_shape[0])(seq_input)
    x = Conv1D(64, 5, activation='relu', padding='same')(x)
    x = MaxPooling1D(2)(x)
    x = Conv1D(128, 5, activation='relu', padding='same')(x)
    x = MaxPooling1D(2)(x)
    x = Conv1D(256, 3, activation='relu', padding='same')(x)
    x = GlobalMaxPooling1D()(x)
    x = Dropout(0.3)(x)

    if stat_dim:
        stat_input = Input(shape=(stat_dim,), name='stat_input')
        y = Dense(32, activation='relu')(stat_input)
        y = BatchNormalization()(y)
        combined = Concatenate()([x, y])
        z = Dense(64, activation='relu')(combined)
        z = Dropout(0.3)(z)
        output = Dense(num_classes, activation='softmax')(z)
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        z = Dense(64, activation='relu')(x)
        z = Dropout(0.3)(z)
        output = Dense(num_classes, activation='softmax')(z)
        model = Model(inputs=seq_input, outputs=output)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


def build_lstm(seq_shape, stat_dim=None, num_classes=4):
    seq_input = Input(shape=seq_shape, name='seq_input')
    x = Embedding(5, 16, input_length=seq_shape[0])(seq_input)
    x = LSTM(64, return_sequences=False, dropout=0.2)(x)
    x = Dropout(0.3)(x)

    if stat_dim:
        stat_input = Input(shape=(stat_dim,), name='stat_input')
        y = Dense(32, activation='relu')(stat_input)
        y = BatchNormalization()(y)
        combined = Concatenate()([x, y])
        z = Dense(64, activation='relu')(combined)
        z = Dropout(0.3)(z)
        output = Dense(num_classes, activation='softmax')(z)
        model = Model(inputs=[seq_input, stat_input], outputs=output)
    else:
        z = Dense(64, activation='relu')(x)
        z = Dropout(0.3)(z)
        output = Dense(num_classes, activation='softmax')(z)
        model = Model(inputs=seq_input, outputs=output)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

# ========================= 7. 训练模型 =========================
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# 准备输入数据
if use_stat:
    train_inputs = [X_seq_train, X_stat_train]
    val_inputs = [X_seq_val, X_stat_val]
    test_inputs = [X_seq_test, X_stat_test]
else:
    train_inputs = X_seq_train
    val_inputs = X_seq_val
    test_inputs = X_seq_test

# CNN模型
print("\n===== 训练 CNN 模型 =====")
cnn_model = build_cnn((MAX_SEQ_LEN,), X_stat.shape[1] if use_stat else None, num_classes)
cnn_model.summary()
history_cnn = cnn_model.fit(
    train_inputs, y_train,
    validation_data=(val_inputs, y_val),
    epochs=50, batch_size=32, callbacks=[early_stop], verbose=1
)

# LSTM模型
print("\n===== 训练 LSTM 模型 =====")
lstm_model = build_lstm((MAX_SEQ_LEN,), X_stat.shape[1] if use_stat else None, num_classes)
lstm_model.summary()
history_lstm = lstm_model.fit(
    train_inputs, y_train,
    validation_data=(val_inputs, y_val),
    epochs=50, batch_size=32, callbacks=[early_stop], verbose=1
)

# ========================= 8. 评估与对比 =========================
cnn_test_loss, cnn_test_acc = cnn_model.evaluate(test_inputs, y_test, verbose=0)
lstm_test_loss, lstm_test_acc = lstm_model.evaluate(test_inputs, y_test, verbose=0)

print("\n========== 模型对比 ==========")
print(f"CNN  - 测试损失: {cnn_test_loss:.4f}, 测试准确率: {cnn_test_acc:.4f}")
print(f"LSTM - 测试损失: {lstm_test_loss:.4f}, 测试准确率: {lstm_test_acc:.4f}")

# 损失率相对变化
loss_reduction = (lstm_test_loss - cnn_test_loss) / lstm_test_loss * 100 if lstm_test_loss != 0 else 0
print(f"相对于LSTM，CNN的损失降低了: {loss_reduction:.2f}%")

# 绘制训练曲线
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(history_cnn.history['loss'], label='CNN Train Loss')
plt.plot(history_cnn.history['val_loss'], label='CNN Val Loss')
plt.plot(history_lstm.history['loss'], label='LSTM Train Loss')
plt.plot(history_lstm.history['val_loss'], label='LSTM Val Loss')
plt.title('Loss Curves')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history_cnn.history['accuracy'], label='CNN Train Acc')
plt.plot(history_cnn.history['val_accuracy'], label='CNN Val Acc')
plt.plot(history_lstm.history['accuracy'], label='LSTM Train Acc')
plt.plot(history_lstm.history['val_accuracy'], label='LSTM Val Acc')
plt.title('Accuracy Curves')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.tight_layout()
plt.savefig('model_comparison.png')
plt.show()


# 混淆矩阵
def plot_confusion(model, name, test_inputs, y_true):
    y_pred = model.predict(test_inputs)
    y_pred_class = np.argmax(y_pred, axis=1)
    y_true_class = np.argmax(y_true, axis=1)
    cm = confusion_matrix(y_true_class, y_pred_class)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=le.classes_, yticklabels=le.classes_)
    plt.title(f'Confusion Matrix - {name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.show()
    print(f"\n{classification_report(y_true_class, y_pred_class, target_names=le.classes_)}")


plot_confusion(cnn_model, 'CNN', test_inputs, y_test)
plot_confusion(lstm_model, 'LSTM', test_inputs, y_test)