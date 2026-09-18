# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch CNN으로 MNIST를 학습하고, tkinter 그림판에 마우스로 쓴 숫자를 인식하는 윈도우용 학습 프로젝트. git 저장소 아님, 테스트·린트 설정 없음.

## 작성 규칙

- 주석, 독스트링, 출력 메시지, UI 문구, **직접 만든 변수·함수·클래스 이름까지 한글**로 작성한다 (예: `학습률`, `MNIST_형식으로_변환`, `class 손글씨_인식기`). 라이브러리 API와 `main`만 영어.
- `.ps1` 파일은 반드시 **UTF-8 BOM**으로 저장한다. Windows PowerShell 5.1은 BOM이 없으면 한글을 깨뜨린다.

## 실행 환경 (주의)

- 패키지(torch 2.14 CPU, torchvision, numpy, pillow)는 **Python 3.13에만** 설치되어 있다.
- `python` → 3.13 (정상), `py` → 3.14 (패키지 없음, `ModuleNotFoundError`). `py`를 쓸 땐 `py -3.13`.
- GPU 없음. 학습은 CPU로 에폭당 약 37초.
- 콘솔 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8` 설정.

## 명령어

```bash
python train.py                  # 학습 (5에폭, ./data에 MNIST 자동 다운로드) → mnist_cnn.pt
python app.py                    # 손글씨 인식 GUI
python make_icon.py              # app_icon.ico 재생성
powershell -ExecutionPolicy Bypass -File make_shortcut.ps1   # 바탕 화면·시작 메뉴 바로가기 재생성
```

GUI 없이 전처리 경로를 검증하려면: MNIST 테스트 이미지를 280×280으로 키워 `app.MNIST_형식으로_변환` → 모델에 넣어 정확도를 본다 (현재 약 99.6%).

## 구조와 파일 간 결합

- `model.py`의 `MnistCNN`이 유일한 모델 정의. `mnist_cnn.pt`는 이 구조의 `state_dict`라서 **모델 구조를 바꾸면 반드시 재학습**해야 `app.py`가 로드된다.
- `train.py`는 평가 정확도가 최고일 때만 가중치를 저장한다. 학습 데이터에는 `RandomAffine` 증강을 적용해 실제 손글씨에 강하게 만든다.
- **정규화 상수(`MNIST_평균=0.1307`, `MNIST_표준편차=0.3081`)가 `train.py`와 `app.py`에 중복**되어 있다. 한쪽만 바꾸면 인식률이 떨어진다.
- `app.py`는 화면용 캔버스(흰 바탕·검은 선)와 별도로 인식용 PIL 이미지(검은 바탕·흰 선, MNIST와 동일)에 동시에 그린다. `MNIST_형식으로_변환`이 MNIST 원본 방식대로 전처리한다: 글씨 영역 자르기 → 긴 변 20px로 축소 → 28×28 가운데 배치 → 무게중심을 (14,14)로 이동 → 정규화. 인식률은 이 전처리에 크게 좌우된다.
- `app.py`는 파일을 `Path(__file__)` 기준 절대 경로로 찾는다 (바로가기 실행 대비). 상대 경로로 되돌리지 말 것.

## 윈도우 바로가기

- 바로가기는 `pythonw.exe`(3.13)로 `app.py`를 실행해 콘솔 창이 뜨지 않는다. 그래서 시작 오류는 `messagebox`로만 보인다.
- 작업 표시줄 고정 아이콘과 실행 중인 창이 하나로 묶이도록 **앱 ID `Logistex.MnistHandwriting`이 `app.py`(`SetCurrentProcessExplicitAppUserModelID`)와 `make_shortcut.ps1`(.lnk의 `System.AppUserModel.ID` 속성)에 중복**되어 있다. 둘은 항상 같아야 한다.
- 프로젝트 폴더를 옮기면 `make_shortcut.ps1`을 다시 실행해야 한다. 작업 표시줄 고정은 윈도우 정책상 사용자가 직접 해야 한다.
