import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import os
import threading

_model = None
_device = None
_lock = threading.Lock()

CATEGORY_MAPPING = {
    0: ('电子产品', '手机、电脑、充电器等'),
    1: ('证件卡片', '身份证、学生卡、银行卡等'),
    2: ('钥匙', '各类钥匙'),
    3: ('书籍文具', '书本、笔记本、文具等'),
    4: ('衣物配饰', '衣服、包包、眼镜等'),
    5: ('运动器材', '球类、球拍等'),
    6: ('其他', '其他物品'),
}

ITEM_KEYWORDS = {
    '电子产品': ['phone', 'cellphone', 'mobile', 'laptop', 'computer', 'keyboard', 'mouse', 'charger', 
               'headphone', 'earphone', 'tablet', 'ipad', 'camera', 'usb', 'cable', 'remote',
               '手机', '电脑', '键盘', '鼠标', '充电器', '耳机', '平板', '相机'],
    '证件卡片': ['card', 'id', 'license', 'passport', 'certificate', 'student', 'bank', 'credit',
               '身份证', '学生证', '银行卡', '信用卡', '驾驶证', '护照', '证件'],
    '钥匙': ['key', 'keys', 'keychain', '钥匙'],
    '书籍文具': ['book', 'notebook', 'pen', 'pencil', 'paper', 'folder', 'bag', 'backpack',
               '书', '笔记本', '笔', '文具', '书包', '课本'],
    '衣物配饰': ['shirt', 'coat', 'jacket', 'pants', 'shoes', 'hat', 'cap', 'glasses', 'sunglasses',
               'watch', 'ring', 'necklace', 'bag', 'purse', 'wallet',
               '衣服', '外套', '裤子', '鞋子', '帽子', '眼镜', '手表', '包', '钱包'],
    '运动器材': ['ball', 'basketball', 'football', 'tennis', 'racket', 'bat', 'helmet',
               '球', '篮球', '足球', '球拍', '运动'],
}


def get_model():
    global _model, _device
    with _lock:
        if _model is None:
            _device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            _model = torch.hub.load('pytorch/vision:v0.16.0', 'resnet18', pretrained=True)
            _model.eval()
            _model.to(_device)
    return _model, _device


def preprocess_image(image_path):
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    try:
        img = Image.open(image_path).convert('RGB')
        return preprocess(img).unsqueeze(0)
    except Exception as e:
        print(f"图像预处理失败: {e}")
        return None


def extract_features(image_path):
    model, device = get_model()
    
    input_tensor = preprocess_image(image_path)
    if input_tensor is None:
        return None
    
    input_tensor = input_tensor.to(device)
    
    with torch.no_grad():
        features = model(input_tensor)
        features = F.normalize(features, p=2, dim=1)
    
    return features.cpu().numpy().flatten()


def classify_by_keywords(text):
    if not text:
        return None
    
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in ITEM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None


def compute_feature_similarity(features1, features2):
    if features1 is None or features2 is None:
        return 0.0
    
    import numpy as np
    similarity = np.dot(features1, features2) / (
        np.linalg.norm(features1) * np.linalg.norm(features2)
    )
    return float(similarity)


def predict_category(image_path=None, text=None):
    if text:
        category = classify_by_keywords(text)
        if category:
            return category
    
    if image_path and os.path.exists(image_path):
        return '其他'
    
    return '其他'
