# python/python-data-science/14 — 이미지 처리 (Pillow) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `(200, 100)` — 상자의 네 값은 좌표다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
(200, 100)
```

**왜 그런가**
`crop` 상자는 `(left, upper, right, lower)` 좌표다.
가로 = 250 − 50 = 200, 세로 = 120 − 20 = 100 이다.
250 이나 120 을 크기로 읽으면 틀린다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 원본은 `(1600, 1200)`, 사본은 `(800, 600)`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
(1600, 1200) (800, 600)
```

**왜 그런가**
`thumbnail` 은 비율을 유지해 (800, 800) 상자 안에 들어가게 줄인다.
배율은 min(800/1600, 800/1200) = 0.5 라서 1600×0.5 = 800, 1200×0.5 = 600 이다.
`thumbnail` 은 `small` 자체만 바꾸므로, `copy()` 로 떼어 둔 `img` 는 그대로 1600×1200 이다.
근거: 2-summary 「동작 방식 (2)」.

### 3. `(350, 150, 650, 450)`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
(350, 150, 650, 450)
```

**왜 그런가**
left = (1000 − 300) // 2 = 350, top = (600 − 300) // 2 = 150 이다.
오른쪽 = 350 + 300 = 650, 아래 = 150 + 300 = 450 이다.
남는 여백을 양쪽으로 반씩 나눈 자리가 시작점이다.
근거: 2-summary 「동작 방식 (3)」.

### 4. `thumbnail()` 이 호출한 객체 자체를 줄이기 때문이다

`thumbnail()` 은 새 이미지를 돌려주지 않고 그 객체를 제자리에서 줄인다.
원본에 바로 부르면 원래 크기의 이미지를 잃는다.
사본에 부르면 원본은 다른 작업(크롭 · 필터 등)에 그대로 쓸 수 있다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 5. JPEG 는 투명도 채널을 담지 못하기 때문이다

RGBA 는 RGB 에 알파 채널이 붙은 모드다.
JPEG 형식은 알파를 담을 자리가 없어 RGBA 그대로 저장하면 에러가 난다.
`convert('RGB')` 로 알파를 떼어 낸 새 이미지를 저장해야 한다.
근거: 2-summary 「어디서 틀리나 2」, 「동작 방식 (1)」의 모드 설명.

### 6. 크기는 원본과 같고, 모서리는 잘린다

`expand` 를 주지 않으면 결과 캔버스는 원본 크기 그대로다.
45도 기운 그림은 그 캔버스를 벗어나므로 모서리가 잘려 나간다.
캔버스 안쪽에 생긴 빈 곳은 채움색으로 메워지며, 색은 `fillcolor` 로 정할 수 있다.
전부 보이게 하려면 `expand=True` 로 캔버스를 넓힌다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 7. 정사각형 800×800 이 되며 그림이 가로로 눌린다

`resize` 는 주어진 크기를 정확히 맞출 뿐 비율을 지키지 않는다.
4:3 이던 그림이 1:1 이 되므로 가로 방향이 상대적으로 줄어든 듯 찌그러진다.
비율을 지키려면 `thumbnail` 을 쓰거나 비율에 맞는 크기를 계산해 넘긴다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 3」.

### 8. 배경이 아니라 로고 네모 전체가 덮어쓴다

마스크가 없으면 `paste` 는 붙이는 이미지의 네모 영역 전체로 배경을 덮는다.
그래서 로고의 투명한 부분 자리에도 배경이 남지 않는다.
세 번째 인자로 로고 자신을 넘기면 그 투명도가 마스크가 되어 투명한 곳에 배경이 보인다.
근거: 2-summary 「동작 방식 (7)」, 「어디서 틀리나 6」.

### 9. 셋 다 새 이미지를 만들지 않고 그 객체를 제자리에서 바꾼다

`resize` · `crop` · `filter` 는 새 `Image` 를 돌려주고 원래 객체는 그대로 둔다.
`thumbnail` 은 호출한 이미지를, `paste` 는 배경 이미지를, `ImageDraw` 의 펜은 `Draw(img)` 에 넘긴 `img` 를 직접 바꾼다.
그래서 원본을 지켜야 하면 이 셋 앞에서 `copy()` 를 떠 둔다.
근거: 2-summary 「문법 — 형태와 규칙」, 「핵심 문장 1」.

### 10. 둘 다 `(전체 − 대상) // 2` 한 공식이다

가운데 정렬의 x 는 `(img_w − tw) // 2`, 중앙 크롭의 left 는 `(w − new_size) // 2` 다.
전체 길이에서 대상 길이를 빼면 남는 여백이 나오고, 그 절반이 왼쪽 여백이 된다.
글자는 `textbbox` 의 `bbox[2] − bbox[0]` 로 대상 너비를 재고, 크롭은 `new_size` 가 대상 너비다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (6)」.

## 실습 정답

### 실습 1. Pillow 사용법을 절별로 출력하는 학습 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 공통 꼴 | 절마다 `print("=== … ===")` + `print("""…""")`, 절 사이 `print()` |
| 2단계 열기 · 정보 · 저장 | `Image.open('photo.jpg')`, `img.size` · `img.mode` · `img.format` · `img.info`, `img.save(...)` 세 줄 |
| 3단계 리사이즈와 크롭 | `img.resize((800, 600))`, `img_copy.thumbnail((800, 800))`, `Image.Resampling.LANCZOS` 등, `img.crop((100, 100, 500, 400))`, `center_crop` |
| 4단계 회전 · 뒤집기 · 변환 | `img.rotate(45, ...)` 세 줄, `Image.Transpose.*` 세 줄, `convert('L')` · `convert('RGBA')` · `convert('RGB')` |
| 5단계 필터 적용 | `ImageFilter.BLUR` … `EMBOSS`, `ImageFilter.UnsharpMask(...)`, `ImageEnhance.Brightness` 등 네 줄, `print("필터: …")` · `print("보정: …")` |
| 6단계 텍스트 오버레이 | `Image.new('RGB', (600, 300), ...)`, `ImageDraw.Draw(img)`, `try/except` 와 `load_default()`, `draw.text`, `draw.textbbox`, `x = (img_w - tw) // 2`, `rectangle` · `ellipse` · `line`, `img.save('text_overlay.png')` |
| 7단계 이미지 합성 | `if foreground.mode == 'RGBA':` 분기의 `paste`, `Image.blend(img1, img2, alpha=0.5)`, `def batch_resize(...)` |
| 8단계 모듈 정리 | 마지막 다섯 줄 `print("Image: …")` … `print("ImageFont: …")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/image-processing.py`

```python
# [데이터 과학 & 수학] 이미지 처리 (Pillow)
# 설명: Pillow, 리사이즈, 필터, 텍스트 오버레이
# 팁: thumbnail()은 원본 객체를 수정하므로 copy() 후 사용하는 것이 안전하다. LANCZOS 리샘플링이 품질이 가장 좋다. RGBA 이미지를 JPEG로 저장하면 에러가 나므로 convert('RGB') 후 저장해야 한다. with문은 지원하지 않으므로 직접 close() 하거나 그냥 두면 된다.

# Pillow (PIL) - 이미지 처리
# pip install Pillow

# 섹션 제목 출력: 이미지 열기, 정보 확인, 저장 방법을 다룬다
print("=== 이미지 열기, 정보, 저장 ===")
# 멀티라인 문자열로 코드 예시를 출력 (실제 실행 코드가 아닌 학습 자료)
print("""
from PIL import Image

# 이미지 열기
img = Image.open('photo.jpg')

# 기본 정보
print(f"크기: {img.size}")         # (width, height)
print(f"모드: {img.mode}")         # 'RGB', 'RGBA', 'L'(흑백)
print(f"포맷: {img.format}")       # 'JPEG', 'PNG'
print(f"정보: {img.info}")         # EXIF 등 메타데이터

# 저장
img.save('output.png')              # 포맷 자동 감지
img.save('output.jpg', quality=85)  # JPEG 품질 지정
img.save('output.webp', quality=80) # WebP 형식
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: resize와 crop으로 크기 조정과 영역 추출
print("=== 리사이즈와 크롭 ===")
# 리사이즈/크롭 학습용 코드 예시 출력
print("""
from PIL import Image

img = Image.open('photo.jpg')

# 리사이즈
resized = img.resize((800, 600))  # 정확한 크기
print(f"리사이즈: {resized.size}")

# 비율 유지 리사이즈 (thumbnail)
img_copy = img.copy()
img_copy.thumbnail((800, 800))  # 비율 유지, 원본 수정
print(f"썸네일: {img_copy.size}")

# 리사이즈 알고리즘
resized = img.resize((400, 300), Image.Resampling.LANCZOS)   # 최고 품질
resized = img.resize((400, 300), Image.Resampling.BILINEAR)  # 빠름
resized = img.resize((400, 300), Image.Resampling.NEAREST)   # 가장 빠름

# 크롭 (잘라내기)
# (left, upper, right, lower)
cropped = img.crop((100, 100, 500, 400))
print(f"크롭: {cropped.size}")  # (400, 300)

# 중앙 크롭
w, h = img.size
new_size = 300
left = (w - new_size) // 2
top = (h - new_size) // 2
center_crop = img.crop((left, top, left + new_size, top + new_size))
print(f"중앙 크롭: {center_crop.size}")
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: 회전, 뒤집기, 모드 변환
print("=== 회전, 뒤집기, 변환 ===")
# 회전/변환 예시 코드 출력
print("""
from PIL import Image

img = Image.open('photo.jpg')

# 회전
rotated = img.rotate(45)                      # 45도 반시계
rotated = img.rotate(45, expand=True)          # 크기 확장
rotated = img.rotate(45, fillcolor='white')    # 빈 공간 색상

# 뒤집기
flipped_h = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # 좌우
flipped_v = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)  # 상하
rotated_90 = img.transpose(Image.Transpose.ROTATE_90)       # 90도

# 모드 변환
gray = img.convert('L')       # 흑백
rgba = img.convert('RGBA')    # 투명도 추가
rgb = rgba.convert('RGB')     # 투명도 제거

print(f"흑백: {gray.mode}")    # L
print(f"RGBA: {rgba.mode}")   # RGBA
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: 이미지 필터와 보정
print("=== 필터 적용 ===")
# 필터/보정 예시 코드 출력
print("""
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open('photo.jpg')

# --- ImageFilter (기본 필터) ---
blur = img.filter(ImageFilter.BLUR)               # 블러
gaussian = img.filter(ImageFilter.GaussianBlur(5)) # 가우시안 (반경 5)
sharpen = img.filter(ImageFilter.SHARPEN)          # 샤프닝
detail = img.filter(ImageFilter.DETAIL)            # 디테일 강조
edge = img.filter(ImageFilter.FIND_EDGES)          # 엣지 검출
contour = img.filter(ImageFilter.CONTOUR)          # 윤곽선
emboss = img.filter(ImageFilter.EMBOSS)            # 엠보싱

# 언샤프 마스크 (사진 보정에 많이 사용)
sharpened = img.filter(ImageFilter.UnsharpMask(
    radius=2,       # 블러 반경
    percent=150,    # 효과 강도
    threshold=3     # 임계값
))

# --- ImageEnhance (조정) ---
# 밝기
bright = ImageEnhance.Brightness(img).enhance(1.5)  # 1.0=원본, >1 밝게

# 대비
contrast = ImageEnhance.Contrast(img).enhance(1.3)

# 색상
color = ImageEnhance.Color(img).enhance(0.0)  # 0=흑백, 1=원본, 2=강조

# 선명도
sharp = ImageEnhance.Sharpness(img).enhance(2.0)

print("필터: BLUR, GaussianBlur, SHARPEN, FIND_EDGES, CONTOUR, EMBOSS")
print("보정: Brightness, Contrast, Color, Sharpness")
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: 텍스트와 도형을 이미지 위에 그리기
print("=== 텍스트 오버레이 ===")
# 텍스트/도형 그리기 예시 코드 출력
print("""
from PIL import Image, ImageDraw, ImageFont

# 새 이미지 생성 또는 기존 이미지 열기
img = Image.new('RGB', (600, 300), color='white')
draw = ImageDraw.Draw(img)

# 기본 폰트 (시스템 폰트)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except:
    font = ImageFont.load_default()
    font_small = font

# 텍스트 그리기
draw.text((50, 50), 'Hello, Pillow!', fill='black', font=font)
draw.text((50, 120), 'Image Processing', fill='blue', font=font_small)

# 텍스트 크기 측정 (Pillow 10+)
bbox = draw.textbbox((0, 0), 'Hello', font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
print(f"텍스트 크기: {text_width} x {text_height}")

# 중앙 정렬 텍스트
img_w, img_h = img.size
bbox = draw.textbbox((0, 0), 'Centered', font=font)
tw = bbox[2] - bbox[0]
x = (img_w - tw) // 2
draw.text((x, 200), 'Centered', fill='red', font=font)

# 도형 그리기
draw.rectangle([400, 50, 550, 150], outline='green', width=3)
draw.ellipse([400, 160, 550, 260], fill='yellow', outline='black')
draw.line([(0, 0), (600, 300)], fill='gray', width=2)

img.save('text_overlay.png')
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: 이미지 합성과 일괄 처리
print("=== 이미지 합성 ===")
# 합성/배치 처리 예시 코드 출력
print("""
from PIL import Image

# 이미지 합성 (paste)
background = Image.new('RGB', (800, 600), 'white')
foreground = Image.open('logo.png').resize((100, 100))

# RGBA면 투명도 마스크로 사용
if foreground.mode == 'RGBA':
    background.paste(foreground, (50, 50), foreground)  # 3번째: 마스크
else:
    background.paste(foreground, (50, 50))

# 블렌딩 (알파 합성)
img1 = Image.open('img1.jpg').resize((400, 300))
img2 = Image.open('img2.jpg').resize((400, 300))
blended = Image.blend(img1, img2, alpha=0.5)  # 50:50 합성

# 일괄 처리
import os
def batch_resize(input_dir, output_dir, size=(800, 600)):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(os.path.join(input_dir, filename))
            img.thumbnail(size)
            img.save(os.path.join(output_dir, filename))
    print(f"일괄 리사이즈 완료: {output_dir}")
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: Pillow의 주요 클래스와 모듈을 정리
print("=== 주요 클래스/모듈 정리 ===")
# Image 클래스의 핵심 메서드 안내
print("Image: open(), new(), save(), resize(), crop(), rotate()")
# ImageFilter 모듈의 주요 필터 안내
print("ImageFilter: BLUR, SHARPEN, FIND_EDGES, GaussianBlur()")
# ImageEnhance 모듈의 주요 보정 안내
print("ImageEnhance: Brightness, Contrast, Color, Sharpness")
# ImageDraw로 가능한 그리기 메서드 안내
print("ImageDraw: text(), rectangle(), ellipse(), line()")
# ImageFont로 폰트 로딩 메서드 안내
print("ImageFont: truetype(), load_default()")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 이미지 열기, 정보, 저장 ===

from PIL import Image

# 이미지 열기
img = Image.open('photo.jpg')

# 기본 정보
print(f"크기: {img.size}")         # (width, height)
print(f"모드: {img.mode}")         # 'RGB', 'RGBA', 'L'(흑백)
print(f"포맷: {img.format}")       # 'JPEG', 'PNG'
print(f"정보: {img.info}")         # EXIF 등 메타데이터

# 저장
img.save('output.png')              # 포맷 자동 감지
img.save('output.jpg', quality=85)  # JPEG 품질 지정
img.save('output.webp', quality=80) # WebP 형식


=== 리사이즈와 크롭 ===

from PIL import Image

img = Image.open('photo.jpg')

# 리사이즈
resized = img.resize((800, 600))  # 정확한 크기
print(f"리사이즈: {resized.size}")

# 비율 유지 리사이즈 (thumbnail)
img_copy = img.copy()
img_copy.thumbnail((800, 800))  # 비율 유지, 원본 수정
print(f"썸네일: {img_copy.size}")

# 리사이즈 알고리즘
resized = img.resize((400, 300), Image.Resampling.LANCZOS)   # 최고 품질
resized = img.resize((400, 300), Image.Resampling.BILINEAR)  # 빠름
resized = img.resize((400, 300), Image.Resampling.NEAREST)   # 가장 빠름

# 크롭 (잘라내기)
# (left, upper, right, lower)
cropped = img.crop((100, 100, 500, 400))
print(f"크롭: {cropped.size}")  # (400, 300)

# 중앙 크롭
w, h = img.size
new_size = 300
left = (w - new_size) // 2
top = (h - new_size) // 2
center_crop = img.crop((left, top, left + new_size, top + new_size))
print(f"중앙 크롭: {center_crop.size}")


=== 회전, 뒤집기, 변환 ===

from PIL import Image

img = Image.open('photo.jpg')

# 회전
rotated = img.rotate(45)                      # 45도 반시계
rotated = img.rotate(45, expand=True)          # 크기 확장
rotated = img.rotate(45, fillcolor='white')    # 빈 공간 색상

# 뒤집기
flipped_h = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # 좌우
flipped_v = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)  # 상하
rotated_90 = img.transpose(Image.Transpose.ROTATE_90)       # 90도

# 모드 변환
gray = img.convert('L')       # 흑백
rgba = img.convert('RGBA')    # 투명도 추가
rgb = rgba.convert('RGB')     # 투명도 제거

print(f"흑백: {gray.mode}")    # L
print(f"RGBA: {rgba.mode}")   # RGBA


=== 필터 적용 ===

from PIL import Image, ImageFilter, ImageEnhance

img = Image.open('photo.jpg')

# --- ImageFilter (기본 필터) ---
blur = img.filter(ImageFilter.BLUR)               # 블러
gaussian = img.filter(ImageFilter.GaussianBlur(5)) # 가우시안 (반경 5)
sharpen = img.filter(ImageFilter.SHARPEN)          # 샤프닝
detail = img.filter(ImageFilter.DETAIL)            # 디테일 강조
edge = img.filter(ImageFilter.FIND_EDGES)          # 엣지 검출
contour = img.filter(ImageFilter.CONTOUR)          # 윤곽선
emboss = img.filter(ImageFilter.EMBOSS)            # 엠보싱

# 언샤프 마스크 (사진 보정에 많이 사용)
sharpened = img.filter(ImageFilter.UnsharpMask(
    radius=2,       # 블러 반경
    percent=150,    # 효과 강도
    threshold=3     # 임계값
))

# --- ImageEnhance (조정) ---
# 밝기
bright = ImageEnhance.Brightness(img).enhance(1.5)  # 1.0=원본, >1 밝게

# 대비
contrast = ImageEnhance.Contrast(img).enhance(1.3)

# 색상
color = ImageEnhance.Color(img).enhance(0.0)  # 0=흑백, 1=원본, 2=강조

# 선명도
sharp = ImageEnhance.Sharpness(img).enhance(2.0)

print("필터: BLUR, GaussianBlur, SHARPEN, FIND_EDGES, CONTOUR, EMBOSS")
print("보정: Brightness, Contrast, Color, Sharpness")


=== 텍스트 오버레이 ===

from PIL import Image, ImageDraw, ImageFont

# 새 이미지 생성 또는 기존 이미지 열기
img = Image.new('RGB', (600, 300), color='white')
draw = ImageDraw.Draw(img)

# 기본 폰트 (시스템 폰트)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except:
    font = ImageFont.load_default()
    font_small = font

# 텍스트 그리기
draw.text((50, 50), 'Hello, Pillow!', fill='black', font=font)
draw.text((50, 120), 'Image Processing', fill='blue', font=font_small)

# 텍스트 크기 측정 (Pillow 10+)
bbox = draw.textbbox((0, 0), 'Hello', font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
print(f"텍스트 크기: {text_width} x {text_height}")

# 중앙 정렬 텍스트
img_w, img_h = img.size
bbox = draw.textbbox((0, 0), 'Centered', font=font)
tw = bbox[2] - bbox[0]
x = (img_w - tw) // 2
draw.text((x, 200), 'Centered', fill='red', font=font)

# 도형 그리기
draw.rectangle([400, 50, 550, 150], outline='green', width=3)
draw.ellipse([400, 160, 550, 260], fill='yellow', outline='black')
draw.line([(0, 0), (600, 300)], fill='gray', width=2)

img.save('text_overlay.png')


=== 이미지 합성 ===

from PIL import Image

# 이미지 합성 (paste)
background = Image.new('RGB', (800, 600), 'white')
foreground = Image.open('logo.png').resize((100, 100))

# RGBA면 투명도 마스크로 사용
if foreground.mode == 'RGBA':
    background.paste(foreground, (50, 50), foreground)  # 3번째: 마스크
else:
    background.paste(foreground, (50, 50))

# 블렌딩 (알파 합성)
img1 = Image.open('img1.jpg').resize((400, 300))
img2 = Image.open('img2.jpg').resize((400, 300))
blended = Image.blend(img1, img2, alpha=0.5)  # 50:50 합성

# 일괄 처리
import os
def batch_resize(input_dir, output_dir, size=(800, 600)):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(os.path.join(input_dir, filename))
            img.thumbnail(size)
            img.save(os.path.join(output_dir, filename))
    print(f"일괄 리사이즈 완료: {output_dir}")


=== 주요 클래스/모듈 정리 ===
Image: open(), new(), save(), resize(), crop(), rotate()
ImageFilter: BLUR, SHARPEN, FIND_EDGES, GaussianBlur()
ImageEnhance: Brightness, Contrast, Color, Sharpness
ImageDraw: text(), rectangle(), ellipse(), line()
ImageFont: truetype(), load_default()
````

**풀이 요점**
- 스크립트 자체는 문자열을 찍기만 하므로, 배울 내용은 문자열 속 Pillow 호출의 꼴이다.
- 새 이미지를 돌려주는 호출(`resize` · `crop` · `rotate` · `filter`)과 제자리에서 바꾸는 호출(`thumbnail` · `paste` · `ImageDraw`)을 구분해 읽는다.
- `crop` 상자와 중앙 크롭 · 가운데 정렬은 모두 왼쪽 위 원점 좌표와 `(전체 − 대상) // 2` 로 풀린다.
- 모드가 저장과 합성을 가른다 — RGBA 로고는 마스크로, JPEG 저장 전에는 `convert('RGB')`.
- `batch_resize` 는 파일마다 새로 연 객체라 `copy()` 없이 `thumbnail()` 을 바로 불러도 된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
