"""MNIST 손글씨 숫자 인식을 위한 CNN 모델 정의."""

import torch.nn as nn


class MnistCNN(nn.Module):
    """합성곱 층 2개와 완전연결 층 2개로 이루어진 간단한 CNN.

    입력: (배치, 1, 28, 28) 크기의 흑백 이미지
    출력: (배치, 10) 크기의 숫자별 점수(로짓)
    """

    def __init__(self):
        super().__init__()
        # 특징 추출부: 합성곱 → 배치정규화 → ReLU → 최대풀링
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),   # 28x28 → 28x28
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # 28x28 → 14x14
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # 14x14 → 14x14
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),                              # 14x14 → 7x7
        )
        # 분류부: 펼치기 → 완전연결 → 드롭아웃 → 출력 10개
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))
