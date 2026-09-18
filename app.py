"""마우스로 숫자를 그리면 학습된 CNN이 어떤 숫자인지 인식하는 프로그램.

실행 방법: python app.py   (먼저 train.py로 mnist_cnn.pt를 만들어 두어야 한다)
"""

import ctypes
import sys
import tkinter as tk
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

from model import MnistCNN

# 바로가기 등 다른 폴더에서 실행해도 파일을 찾도록 이 파일 기준의 절대 경로를 쓴다
프로젝트_폴더 = Path(__file__).resolve().parent
가중치_파일 = 프로젝트_폴더 / "mnist_cnn.pt"
아이콘_파일 = 프로젝트_폴더 / "app_icon.ico"
# 작업 표시줄에서 이 앱을 구분하는 고유 ID (바로가기에도 같은 값을 넣는다)
앱_ID = "Logistex.MnistHandwriting"
캔버스_크기 = 280        # 화면에 보이는 그림판 크기(픽셀)
붓_두께 = 20             # 그리는 선의 두께
MNIST_평균 = 0.1307
MNIST_표준편차 = 0.3081


def 모델_불러오기():
    """저장된 가중치를 읽어 평가 모드의 모델을 만든다."""
    모델 = MnistCNN()
    모델.load_state_dict(torch.load(가중치_파일, map_location="cpu", weights_only=True))
    모델.eval()
    return 모델


def MNIST_형식으로_변환(그림: Image.Image) -> torch.Tensor:
    """그림판 이미지를 MNIST와 같은 형태(28x28, 가운데 정렬)로 바꾼다.

    MNIST 숫자는 20x20 상자 안에 들어가도록 크기를 맞춘 뒤,
    무게중심이 28x28 이미지의 가운데에 오도록 배치되어 있다.
    같은 방식으로 전처리해야 인식률이 높아진다.
    """
    배열 = np.array(그림, dtype=np.float32)

    # 1) 글씨가 있는 영역만 잘라내기
    행들 = np.where(배열.max(axis=1) > 0)[0]
    열들 = np.where(배열.max(axis=0) > 0)[0]
    if len(행들) == 0:
        return None  # 아무것도 그리지 않음
    잘라낸 = 그림.crop((열들[0], 행들[0], 열들[-1] + 1, 행들[-1] + 1))

    # 2) 가로세로 비율을 유지하며 긴 변이 20픽셀이 되도록 축소
    가로, 세로 = 잘라낸.size
    배율 = 20.0 / max(가로, 세로)
    새_크기 = (max(1, round(가로 * 배율)), max(1, round(세로 * 배율)))
    축소 = 잘라낸.resize(새_크기, Image.LANCZOS)

    # 3) 28x28 검은 바탕 가운데에 붙이기
    바탕 = Image.new("L", (28, 28), 0)
    바탕.paste(축소, ((28 - 새_크기[0]) // 2, (28 - 새_크기[1]) // 2))

    # 4) 무게중심이 정중앙(14, 14)에 오도록 이동
    배열 = np.array(바탕, dtype=np.float32)
    전체 = 배열.sum()
    세로_좌표, 가로_좌표 = np.indices(배열.shape)
    중심_y = (세로_좌표 * 배열).sum() / 전체
    중심_x = (가로_좌표 * 배열).sum() / 전체
    이동_x, 이동_y = round(14 - 중심_x), round(14 - 중심_y)
    배열 = np.roll(배열, (이동_y, 이동_x), axis=(0, 1))

    # 5) 0~1 범위로 바꾼 뒤 MNIST와 같은 방식으로 정규화
    텐서 = torch.from_numpy(배열 / 255.0)
    텐서 = (텐서 - MNIST_평균) / MNIST_표준편차
    return 텐서.view(1, 1, 28, 28)


class 손글씨_인식기:
    """그림판, 버튼, 결과 표시로 이루어진 GUI 창."""

    def __init__(self, 창: tk.Tk):
        self.창 = 창
        self.모델 = 모델_불러오기()
        창.title("손글씨 숫자 인식기 (MNIST CNN)")
        창.resizable(False, False)
        if 아이콘_파일.exists():
            창.iconbitmap(default=str(아이콘_파일))  # 제목 표시줄·작업 표시줄 아이콘

        # 화면용 캔버스: 흰 바탕에 검은 선으로 그린다
        self.캔버스 = tk.Canvas(창, width=캔버스_크기, height=캔버스_크기,
                               bg="white", cursor="cross")
        self.캔버스.grid(row=0, column=0, rowspan=4, padx=10, pady=10)

        # 인식용 이미지: MNIST처럼 검은 바탕에 흰 글씨로 따로 그린다
        self.이미지 = Image.new("L", (캔버스_크기, 캔버스_크기), 0)
        self.붓 = ImageDraw.Draw(self.이미지)
        self.이전_좌표 = None

        self.캔버스.bind("<B1-Motion>", self.그리기)
        self.캔버스.bind("<ButtonRelease-1>", self.붓_떼기)

        # 오른쪽 결과 영역
        self.결과_글자 = tk.Label(창, text="?", font=("맑은 고딕", 72, "bold"), width=2)
        self.결과_글자.grid(row=0, column=1, padx=10)
        self.확률_글자 = tk.Label(창, text="숫자를 그려 주세요", font=("맑은 고딕", 11))
        self.확률_글자.grid(row=1, column=1)
        self.상위3_글자 = tk.Label(창, text="", font=("맑은 고딕", 10),
                               justify="left", fg="gray30")
        self.상위3_글자.grid(row=2, column=1)

        버튼_틀 = tk.Frame(창)
        버튼_틀.grid(row=3, column=1, pady=10)
        tk.Button(버튼_틀, text="인식하기", width=10,
                  command=self.인식하기).pack(pady=3)
        tk.Button(버튼_틀, text="지우기", width=10,
                  command=self.지우기).pack(pady=3)

        # 키보드 단축키: Enter = 인식, Esc/Delete = 지우기
        창.bind("<Return>", lambda 이벤트: self.인식하기())
        창.bind("<Escape>", lambda 이벤트: self.지우기())
        창.bind("<Delete>", lambda 이벤트: self.지우기())

    def 그리기(self, 이벤트):
        """마우스를 끌 때마다 화면과 인식용 이미지 양쪽에 선을 그린다."""
        x, y = 이벤트.x, 이벤트.y
        if self.이전_좌표 is not None:
            px, py = self.이전_좌표
            self.캔버스.create_line(px, py, x, y, width=붓_두께, fill="black",
                                   capstyle=tk.ROUND, smooth=True)
            self.붓.line((px, py, x, y), fill=255, width=붓_두께)
        반지름 = 붓_두께 // 2
        self.캔버스.create_oval(x - 반지름, y - 반지름, x + 반지름, y + 반지름,
                               fill="black", outline="black")
        self.붓.ellipse((x - 반지름, y - 반지름, x + 반지름, y + 반지름), fill=255)
        self.이전_좌표 = (x, y)

    def 붓_떼기(self, 이벤트):
        """마우스 버튼을 떼면 선을 끊고 바로 인식한다."""
        self.이전_좌표 = None
        self.인식하기()

    def 지우기(self):
        """그림판과 결과를 모두 초기화한다."""
        self.캔버스.delete("all")
        self.붓.rectangle((0, 0, 캔버스_크기, 캔버스_크기), fill=0)
        self.결과_글자.config(text="?")
        self.확률_글자.config(text="숫자를 그려 주세요")
        self.상위3_글자.config(text="")

    @torch.no_grad()
    def 인식하기(self):
        """현재 그림을 모델에 넣어 가장 가능성 높은 숫자를 보여준다."""
        입력 = MNIST_형식으로_변환(self.이미지)
        if 입력 is None:
            self.확률_글자.config(text="먼저 숫자를 그려 주세요")
            return
        확률 = torch.softmax(self.모델(입력), dim=1)[0]
        상위_확률, 상위_숫자 = 확률.topk(3)

        self.결과_글자.config(text=str(상위_숫자[0].item()))
        self.확률_글자.config(text=f"확신도: {상위_확률[0].item() * 100:.1f}%")
        self.상위3_글자.config(text="\n".join(
            f"{순위}위: {숫자.item()}  ({p.item() * 100:.1f}%)"
            for 순위, (숫자, p) in enumerate(zip(상위_숫자, 상위_확률), start=1)
        ))


def 작업표시줄_ID_설정():
    """창이 python 대신 이 앱으로 묶이도록 윈도우에 앱 ID를 알린다.

    바로가기에 넣은 ID와 같아야 고정된 아이콘과 실행 중인 창이 하나로 합쳐진다.
    """
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(앱_ID)


def main():
    작업표시줄_ID_설정()  # 창을 만들기 전에 설정해야 한다
    창 = tk.Tk()
    try:
        손글씨_인식기(창)
    except Exception as 오류:
        # 바로가기(pythonw)로 실행하면 콘솔이 없으므로 오류를 대화상자로 보여준다
        from tkinter import messagebox
        창.withdraw()
        messagebox.showerror("손글씨 숫자 인식기 - 오류",
                             f"앱을 시작하지 못했습니다.\n\n{오류}\n\n"
                             f"'{가중치_파일.name}' 파일이 있는지 확인하고, "
                             f"없으면 train.py를 먼저 실행해 주세요.")
        창.destroy()
        return
    창.mainloop()


if __name__ == "__main__":
    main()
