"""MNIST 데이터셋으로 CNN을 학습하고 가중치를 mnist_cnn.pt로 저장한다.

실행 방법: python train.py
"""

import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import MnistCNN

# ----- 설정값 -----
배치_크기 = 128
에폭_수 = 5
학습률 = 1e-3
가중치_파일 = "mnist_cnn.pt"

# MNIST 전체 데이터의 평균과 표준편차 (정규화에 사용)
MNIST_평균 = 0.1307
MNIST_표준편차 = 0.3081


def 데이터_로더_만들기():
    """학습용/평가용 데이터 로더를 만든다. 데이터가 없으면 자동으로 내려받는다."""
    # 학습 데이터에는 약간의 회전·이동을 주어 실제 손글씨에 더 강하게 만든다
    학습_변환 = transforms.Compose([
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((MNIST_평균,), (MNIST_표준편차,)),
    ])
    평가_변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MNIST_평균,), (MNIST_표준편차,)),
    ])

    학습_데이터 = datasets.MNIST("./data", train=True, download=True, transform=학습_변환)
    평가_데이터 = datasets.MNIST("./data", train=False, download=True, transform=평가_변환)

    학습_로더 = DataLoader(학습_데이터, batch_size=배치_크기, shuffle=True)
    평가_로더 = DataLoader(평가_데이터, batch_size=1000, shuffle=False)
    return 학습_로더, 평가_로더


def 한_에폭_학습(모델, 로더, 옵티마이저, 손실함수, 장치):
    """한 에폭 동안 모델을 학습하고 평균 손실을 돌려준다."""
    모델.train()
    누적_손실 = 0.0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        옵티마이저.zero_grad()
        출력 = 모델(이미지)
        손실 = 손실함수(출력, 정답)
        손실.backward()
        옵티마이저.step()
        누적_손실 += 손실.item() * 이미지.size(0)
    return 누적_손실 / len(로더.dataset)


@torch.no_grad()
def 평가(모델, 로더, 장치):
    """평가 데이터에 대한 정확도(%)를 계산한다."""
    모델.eval()
    맞은_개수 = 0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        예측 = 모델(이미지).argmax(dim=1)
        맞은_개수 += (예측 == 정답).sum().item()
    return 100.0 * 맞은_개수 / len(로더.dataset)


def main():
    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {장치}")

    학습_로더, 평가_로더 = 데이터_로더_만들기()
    모델 = MnistCNN().to(장치)
    옵티마이저 = torch.optim.Adam(모델.parameters(), lr=학습률)
    스케줄러 = torch.optim.lr_scheduler.StepLR(옵티마이저, step_size=2, gamma=0.5)
    손실함수 = nn.CrossEntropyLoss()

    최고_정확도 = 0.0
    for 에폭 in range(1, 에폭_수 + 1):
        시작 = time.time()
        평균_손실 = 한_에폭_학습(모델, 학습_로더, 옵티마이저, 손실함수, 장치)
        정확도 = 평가(모델, 평가_로더, 장치)
        스케줄러.step()
        print(f"[에폭 {에폭}/{에폭_수}] 손실: {평균_손실:.4f} | "
              f"평가 정확도: {정확도:.2f}% | 소요 시간: {time.time() - 시작:.1f}초")

        # 가장 좋은 성능의 가중치만 저장
        if 정확도 > 최고_정확도:
            최고_정확도 = 정확도
            torch.save(모델.state_dict(), 가중치_파일)
            print(f"  → 최고 정확도 갱신, '{가중치_파일}'에 저장했습니다.")

    print(f"학습 완료! 최고 평가 정확도: {최고_정확도:.2f}%")


if __name__ == "__main__":
    main()
