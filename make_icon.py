"""손글씨 인식 앱의 아이콘 파일(app_icon.ico)을 만든다.

실행 방법: python make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

아이콘_경로 = Path(__file__).resolve().parent / "app_icon.ico"
원본_크기 = 256


def 아이콘_그리기() -> Image.Image:
    """둥근 파란 사각형 위에 손글씨 느낌의 숫자 '7'과 연필 선을 그린다."""
    그림 = Image.new("RGBA", (원본_크기, 원본_크기), (0, 0, 0, 0))
    붓 = ImageDraw.Draw(그림)

    # 배경: 둥근 모서리의 남색 사각형
    붓.rounded_rectangle((8, 8, 248, 248), radius=52, fill=(33, 64, 154))
    # 안쪽 칠판 느낌의 검은 판
    붓.rounded_rectangle((36, 36, 220, 220), radius=28, fill=(18, 18, 24))

    # 숫자: 굵은 글꼴이 있으면 쓰고, 없으면 선으로 직접 그린다
    try:
        글꼴 = ImageFont.truetype("segoeuib.ttf", 170)
        붓.text((128, 132), "7", font=글꼴, fill=(255, 255, 255), anchor="mm")
    except OSError:
        붓.line((78, 70, 178, 70, 110, 190), fill=(255, 255, 255), width=26, joint="curve")

    # 오른쪽 아래: 인식 완료를 뜻하는 초록 원과 체크 표시
    붓.ellipse((160, 160, 236, 236), fill=(46, 184, 92), outline=(255, 255, 255), width=6)
    붓.line((178, 199, 194, 214, 220, 182), fill=(255, 255, 255), width=10, joint="curve")
    return 그림


def main():
    그림 = 아이콘_그리기()
    # 윈도우가 상황에 맞게 골라 쓰도록 여러 크기를 한 파일에 담는다
    그림.save(아이콘_경로, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                               (64, 64), (128, 128), (256, 256)])
    print(f"아이콘 저장 완료: {아이콘_경로}")


if __name__ == "__main__":
    main()
