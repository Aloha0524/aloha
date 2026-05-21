import os
import time
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from PIL import Image
from tqdm import tqdm

# --- 1. 配置参数 ---
DATA_DIR = r"C:\Users\admin\Desktop\dataset"
TRAIN_DIR = os.path.join(DATA_DIR, 'train')
TEST_DIR = os.path.join(DATA_DIR, 'test')
MODEL_PATH = 'alexnet_cat_dog_best.pth'

BATCH_SIZE = 64
NUM_EPOCHS = 10
LEARNING_RATE = 0.001
MOMENTUM = 0.9


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"当前使用设备: {DEVICE}")

# --- 2. 数据预处理 ---
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

def load_data():

    image_datasets = {
        'train': datasets.ImageFolder(TRAIN_DIR, data_transforms['train']),
        'val': datasets.ImageFolder(TEST_DIR, data_transforms['val'])
    }

    dataloaders = {
        'train': DataLoader(image_datasets['train'], batch_size=BATCH_SIZE, shuffle=True, num_workers=0),
        'val': DataLoader(image_datasets['val'], batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    }

    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    class_names = image_datasets['train'].classes

    return dataloaders, dataset_sizes, class_names

# --- 3. 定义模型 ---
def create_model(num_classes=2):

    model = models.alexnet(weights=models.AlexNet_Weights.IMAGENET1K_V1)

    model.classifier[6] = nn.Linear(4096, num_classes)

    return model.to(DEVICE)

# --- 4. 训练函数  ---
def train_model(model, dataloaders, dataset_sizes):
    criterion = nn.CrossEntropyLoss()

    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM)

    exp_lr_scheduler = lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(NUM_EPOCHS):
        print(f'Epoch {epoch+1}/{NUM_EPOCHS}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            loop = tqdm(dataloaders[phase], desc=f'{phase}', unit='batch', leave=False)

            for inputs, labels in loop:
                inputs = inputs.to(DEVICE)
                labels = labels.to(DEVICE)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

                loop.set_postfix(loss=loss.item())

            if phase == 'train':
                exp_lr_scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print(f'训练完成，耗时 {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'最佳验证准确率: {best_acc:.4f}')

    model.load_state_dict(best_model_wts)
    return model

# --- 5. 测试功能 ---
def run_tests(model, class_names):
    print("\n" + "="*30)
    print("开始执行最终测试任务...")
    print("="*30)

    # 任务1：单张图片测试
    sample_img_path = None
    true_label = None
    for root, dirs, files in os.walk(TEST_DIR):
        if files:
            sample_img_path = os.path.join(root, files[0])
            true_label = root.split(os.sep)[-1]
            break

    if sample_img_path:
        transform = data_transforms['val']
        img = Image.open(sample_img_path).convert('RGB')
        img_t = transform(img).unsqueeze(0).to(DEVICE)

        model.eval()
        with torch.no_grad():
            out = model(img_t)
            prob = torch.nn.functional.softmax(out[0], dim=0)
            conf, pred = torch.max(prob, 0)

        pred_name = class_names[pred.item()]
        print(f"1. 单张照片测试:")
        print(f"   图片: {os.path.basename(sample_img_path)}")
        print(f"   预测: {pred_name} (置信度: {conf.item():.2f}) | 真实: {true_label}")
        print(f"   结果: {'✅ 正确' if pred_name == true_label else '❌ 错误'}")

    # 任务2：批量测试前10张
    print(f"\n2. 10张照片批量测试:")
    test_images = []
    for root, dirs, files in os.walk(TEST_DIR):
        for file in files:
            if file.endswith(('.jpg', '.png', '.jpeg')):
                test_images.append((os.path.join(root, file), root.split(os.sep)[-1]))

    test_images = test_images[:10]
    correct_count = 0

    for i, (path, true_label) in enumerate(test_images):
        img = Image.open(path).convert('RGB')
        img_t = transform(img).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            out = model(img_t)
            _, pred = torch.max(out, 1)

        pred_name = class_names[pred.item()]
        is_correct = pred_name == true_label
        if is_correct: correct_count += 1

        status = "✅" if is_correct else "❌"
        print(f"   [{i+1}] {os.path.basename(path)} | 真实: {true_label}, 预测: {pred_name} | {status}")

    acc = (correct_count / len(test_images)) * 100
    print("-" * 20)
    print(f"   准确率: {acc:.1f}% ({correct_count}/{len(test_images)})")
    if acc >= 70:
        print("   🎉 结果: 达标 (>=70%)")
    else:
        print("   ⚠️ 结果: 未达标 (<70%)")

if __name__ == '__main__':
    # 1. 加载数据
    dataloaders, dataset_sizes, class_names = load_data()

    # 2. 创建模型
    model = create_model()

    # 3. 开始训练
    model = train_model(model, dataloaders, dataset_sizes)

    # 4. 保存模型
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"模型已保存至: {MODEL_PATH}")

    # 5. 运行测试
    run_tests(model, class_names)