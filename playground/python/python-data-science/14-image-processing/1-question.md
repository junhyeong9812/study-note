# python/python-data-science/14 — 이미지 처리 (Pillow) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 400×300 캔버스를 `(50, 20, 250, 120)` 상자로 자르면 (예측)

```python
# 질문용 발췌
from PIL import Image
img = Image.new('RGB', (400, 300), 'white')
part = img.crop((50, 20, 250, 120))
print(part.size)
```

- 마지막 줄은 무엇을 찍는가?

### 2. 1600×1200 이미지의 사본에 `thumbnail((800, 800))` (예측)

```python
# 질문용 발췌
from PIL import Image
img = Image.new('RGB', (1600, 1200), 'white')
small = img.copy()
small.thumbnail((800, 800))
print(img.size, small.size)
```

- 마지막 줄은 무엇을 찍는가?

### 3. 1000×600 이미지의 300 중앙 크롭 상자 (예측)

```python
# 질문용 발췌
w, h = 1000, 600
new_size = 300
left = (w - new_size) // 2
top = (h - new_size) // 2
print((left, top, left + new_size, top + new_size))
```

- 마지막 줄은 무엇을 찍는가?

### 4. `thumbnail()` 앞에 `copy()` 를 두는 까닭 (왜)
- 예제는 왜 `img.thumbnail(...)` 대신 `img.copy()` 로 만든 사본에 `thumbnail()` 을 부르는가?

### 5. RGBA 이미지를 JPEG 로 저장하기 전 `convert('RGB')` (왜)
- 투명 PNG 를 `.jpg` 로 저장하기 전에 왜 `convert('RGB')` 를 거쳐야 하는가?

### 6. `expand` 없이 45도 돌린 결과 (경계)
- `img.rotate(45)` 의 결과 크기는 원본과 어떤 관계이고, 원래 그림의 모서리는 어떻게 되는가?

### 7. 비율이 다른 크기를 `resize()` 에 넘길 때 (경계)
- 1600×1200 사진에 `resize((800, 800))` 을 하면 그림의 모양은 어떻게 되는가?

### 8. RGBA 로고를 마스크 없이 `paste()` 할 때 (경계)
- 세 번째 인자 없이 `background.paste(logo, (50, 50))` 을 하면 로고의 투명한 부분 자리에는 무엇이 남는가?

### 9. `thumbnail` · `paste` · `ImageDraw` 의 공통점 (연결)
- 이 셋이 `resize` · `crop` · `filter` 와 다른 점은 무엇인가?

### 10. 글자 가운데 정렬과 중앙 크롭 (연결)
- `textbbox()` 로 구한 너비로 글자의 x 좌표를 정하는 식은 중앙 크롭의 `left` 식과 어떻게 이어지는가?

## 실습

### 실습 1. Pillow 사용법을 절별로 출력하는 학습 스크립트 만들기

**만들 것** — Pillow 의 주요 기능(열기 · 크기 조정 · 회전 · 필터 · 그리기 · 합성)을 예시 코드 문자열로 절마다 화면에 찍고, 끝에 주요 모듈 요약을 찍는 스크립트를 만든다.

**준비물** — Python 3 만 있으면 된다; 문자열 속 Pillow 코드는 화면에 찍기만 하므로 Pillow 를 설치하지 않아도 스크립트가 끝까지 돈다(문자열 속 코드를 따로 돌려 보려면 `pip install Pillow` 가 필요하다).

**요구 조건**
1. 1단계(공통 꼴) — 절마다 `=== 제목 ===` 줄을 `print` 하고, 이어서 그 절의 예시 코드를 세 따옴표 문자열 하나로 `print` 한다. 절과 절 사이에는 빈 `print()` 를 둔다.
2. 2단계 「이미지 열기, 정보, 저장」 — `Image.open('photo.jpg')` 로 열고, `size` · `mode` · `format` · `info` 를 찍는 줄과, PNG 저장 · `quality=85` JPEG 저장 · `quality=80` WebP 저장 줄을 담는다.
3. 3단계 「리사이즈와 크롭」 — `resize((800, 600))`, `copy()` 후 `thumbnail((800, 800))`, `LANCZOS` · `BILINEAR` · `NEAREST` 세 리샘플링, `crop((100, 100, 500, 400))`, 한 변 300 중앙 크롭을 담는다.
4. 4단계 「회전, 뒤집기, 변환」 — `rotate(45)` 의 세 형태(기본 · `expand=True` · `fillcolor`), `transpose` 세 가지(좌우 · 상하 · 90도), `convert` 로 `L` · `RGBA` · `RGB` 를 만들고 두 모드를 찍는 줄을 담는다.
5. 5단계 「필터 적용」 — `ImageFilter` 의 일곱 필터와 `UnsharpMask(radius=2, percent=150, threshold=3)`, `ImageEnhance` 의 네 보정(배율 1.5 · 1.3 · 0.0 · 2.0)과 요약 두 줄 출력을 담는다.
6. 6단계 「텍스트 오버레이」 — 600×300 새 캔버스와 `ImageDraw.Draw`, `truetype` 실패 시 `load_default()` 로 넘어가는 `try/except`, 글자 두 줄, `textbbox` 로 너비·높이 계산, `Centered` 가운데 정렬, 사각형 · 타원 · 선 그리기, `save('text_overlay.png')` 를 담는다.
7. 7단계 「이미지 합성」 — 800×600 배경에 100×100 로고를 붙이되 RGBA 면 자신을 마스크로 넘기는 분기, 두 이미지를 400×300 으로 맞춘 `Image.blend(..., alpha=0.5)`, 폴더 안 이미지를 `thumbnail` 로 줄여 저장하는 `batch_resize` 함수를 담는다.
8. 8단계 「주요 클래스/모듈 정리」 — 이 절은 문자열 블록 없이 `Image` · `ImageFilter` · `ImageEnhance` · `ImageDraw` · `ImageFont` 의 핵심 이름을 한 줄씩, 다섯 줄 `print` 한다.

**시작 코드**

```python
# Pillow (PIL) - 이미지 처리
# pip install Pillow

print("=== 이미지 열기, 정보, 저장 ===")
print("""
from PIL import Image

# 이미지 열기
# TODO: photo.jpg 를 연다

# 기본 정보
# TODO: size, mode, format, info 를 찍는 네 줄

# 저장
# TODO: png / jpg(quality=85) / webp(quality=80)
""")

print()
print("=== 리사이즈와 크롭 ===")
print("""
from PIL import Image

img = Image.open('photo.jpg')

# 리사이즈
# TODO: 정확한 크기 (800, 600)

# 비율 유지 리사이즈 (thumbnail)
# TODO: 사본을 떠서 (800, 800) 상자에 맞춘다

# 리사이즈 알고리즘
# TODO: LANCZOS / BILINEAR / NEAREST

# 크롭 (잘라내기)
# (left, upper, right, lower)
# TODO: (100, 100, 500, 400)

# 중앙 크롭
w, h = img.size
new_size = 300
# TODO: left, top 계산과 crop
""")

print()
print("=== 회전, 뒤집기, 변환 ===")
print("""
from PIL import Image

img = Image.open('photo.jpg')

# 회전
# TODO: 기본 / expand=True / fillcolor='white'

# 뒤집기
# TODO: 좌우 / 상하 / 90도

# 모드 변환
# TODO: L / RGBA / RGB

print(f"흑백: {gray.mode}")    # L
print(f"RGBA: {rgba.mode}")   # RGBA
""")

print()
print("=== 필터 적용 ===")
print("""
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open('photo.jpg')

# --- ImageFilter (기본 필터) ---
# TODO: BLUR, GaussianBlur(5), SHARPEN, DETAIL, FIND_EDGES, CONTOUR, EMBOSS

# 언샤프 마스크 (사진 보정에 많이 사용)
# TODO: UnsharpMask(radius=2, percent=150, threshold=3)

# --- ImageEnhance (조정) ---
# TODO: Brightness 1.5 / Contrast 1.3 / Color 0.0 / Sharpness 2.0

print("필터: BLUR, GaussianBlur, SHARPEN, FIND_EDGES, CONTOUR, EMBOSS")
print("보정: Brightness, Contrast, Color, Sharpness")
""")

print()
print("=== 텍스트 오버레이 ===")
print("""
from PIL import Image, ImageDraw, ImageFont

# 새 이미지 생성 또는 기존 이미지 열기
img = Image.new('RGB', (600, 300), color='white')
# TODO: 그리기 객체

# 기본 폰트 (시스템 폰트)
# TODO: try 로 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf' 36·18 을 읽고, 실패하면 load_default()

# 텍스트 그리기
# TODO: (50, 50) 'Hello, Pillow!' fill='black' / (50, 120) 'Image Processing' fill='blue'

# 텍스트 크기 측정 (Pillow 10+)
# TODO: textbbox 로 'Hello' 의 너비·높이를 구해 찍는다

# 중앙 정렬 텍스트
# TODO: 'Centered' 를 y=200 에 가운데 정렬, fill='red'

# 도형 그리기
# TODO: rectangle [400, 50, 550, 150] outline='green' width=3
# TODO: ellipse [400, 160, 550, 260] fill='yellow' outline='black'
# TODO: line [(0, 0), (600, 300)] fill='gray' width=2

img.save('text_overlay.png')
""")

print()
print("=== 이미지 합성 ===")
print("""
from PIL import Image

# 이미지 합성 (paste)
background = Image.new('RGB', (800, 600), 'white')
foreground = Image.open('logo.png').resize((100, 100))

# RGBA면 투명도 마스크로 사용
# TODO: 모드에 따라 마스크를 넘기거나 빼고 (50, 50) 에 붙인다

# 블렌딩 (알파 합성)
# TODO: img1.jpg, img2.jpg 를 (400, 300) 으로 맞춰 alpha=0.5 로 섞는다

# 일괄 처리
import os
def batch_resize(input_dir, output_dir, size=(800, 600)):
    # TODO: 폴더 만들기 → 이미지 파일만 골라 열기 → thumbnail → 저장
    print(f"일괄 리사이즈 완료: {output_dir}")
""")

print()
print("=== 주요 클래스/모듈 정리 ===")
# TODO: Image / ImageFilter / ImageEnhance / ImageDraw / ImageFont 다섯 줄
```

**확인 방법** — `python image-processing.py` 로 돌려, 터미널에 여덟 절이 위 순서대로 나오고 각 절 문자열에 요구 조건의 호출이 모두 들어 있는지, 마지막에 `Image:` 로 시작하는 줄부터 `ImageFont:` 로 시작하는 줄까지 다섯 줄이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
