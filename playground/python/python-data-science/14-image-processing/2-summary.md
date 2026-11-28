# python/python-data-science/14 — 이미지 처리 (Pillow) — 정리 (힌트)

> 출처 — study-site 항목 `python/image-processing`(항목 데이터 `data/python/data-science.json`) · 정답 코드 study-practice `python/python-data-science/reference/image-processing.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Pillow 는 「사진관 작업대」다.**
원본 사진을 작업대에 올린다.
재단기로 자르고, 확대·축소기로 크기를 바꾸고, 렌즈를 대어 흐리게 하거나 또렷하게 만든다.
펜으로 글자를 쓰고, 다른 사진을 겹쳐 붙인다.
작업 대부분은 원본을 그대로 두고 **새 인화본**을 돌려준다.
몇몇 작업(썸네일 만들기 · 붙이기 · 펜으로 그리기)은 작업대 위의 그 사진 자체를 바꾼다.
Pillow 의 `Image` 객체도 똑같은 구조다.

> **Pillow** — 파이썬에서 이미지를 열고 고치고 저장하는 라이브러리로, 옛 이름 PIL 을 이어받아 `from PIL import ...` 로 불러온다.\
> 예: `pip install Pillow` 로 설치하고 `from PIL import Image` 로 쓴다.

| 비유 | 실체 |
|---|---|
| 원본 사진 | `Image.open()` 이 돌려준 `Image` 객체 |
| 새 인화본 | `resize()` · `crop()` · `rotate()` · `filter()` · `convert()` 가 돌려준 새 `Image` |
| 원본을 직접 깎는 작업 | `thumbnail()` · `paste()` · `ImageDraw` 로 그리기 |
| 복사본 뜨기 | `copy()` |
| 렌즈 | `ImageFilter` 의 필터 |
| 밝기·대비 손잡이 | `ImageEnhance` 의 `enhance(배율)` |
| 펜 | `ImageDraw.Draw(img)` |
| 인화해서 봉투에 넣기 | `save('파일이름.확장자')` |

```text
 Image.open('photo.jpg')
        │
        ▼
   [ img 원본 ] ──resize / crop / rotate / filter / convert──▶ [ 새 Image ]   (img 는 그대로)
        │
        └──copy()──▶ [ 사본 ] ──thumbnail()──▶ [ 사본 자체가 작아짐 ]
                                                   │
                                                   ▼
                                           save('out.jpg')
```

## 이 주제가 답하려는 질문

1. 이미지를 열어 크기·색 구성을 어떻게 알고, 어떤 형식으로 저장하나?
2. 크기와 영역은 어떻게 바꾸나 — `resize` · `thumbnail` · `crop` 은 무엇이 다른가?
3. 회전 · 뒤집기 · 색 모드 변환 · 필터 · 보정은 어떻게 하나?
4. 이미지 위에 글자와 도형을 그리고, 이미지끼리 합치려면 어떻게 하나?

## 동작 방식

### (1) 열기 · 정보 · 저장

**언제 쓰나** — 파일에서 이미지를 불러와 크기와 색 구성을 확인하고, 다른 형식이나 품질로 저장할 때.

```text
Image.open('photo.jpg')             → 파일을 읽어 Image 객체 img 를 만든다
img.size                            → (가로, 세로)
img.mode                            → 'RGB' / 'RGBA' / 'L'
img.format                          → 'JPEG' / 'PNG'
img.info                            → EXIF 같은 메타데이터
img.save('output.png')              → 확장자를 보고 PNG 로 저장
img.save('output.jpg', quality=85)  → JPEG, 품질 85
img.save('output.webp', quality=80) → WebP, 품질 80
```

- `open()` 이 파일을 `Image` 객체로 바꾼다.
- `size` 는 (가로, 세로) 순서의 튜플이다.
- `mode` 는 픽셀이 어떤 채널로 이루어졌는지 알려 준다.
- `format` 은 원래 파일 형식, `info` 는 사진에 딸린 부가 정보다.
- `save()` 는 확장자로 형식을 고르고, `quality` 로 JPEG · WebP 의 압축 품질을 정한다.

> **모드** — 픽셀 하나를 어떤 채널로 담는지 나타내는 문자열이다.\
> 예: `'RGB'` 는 빨강·초록·파랑, `'RGBA'` 는 거기에 투명도(알파), `'L'` 은 밝기 하나(흑백)다.

> **EXIF** — 사진 파일에 함께 저장되는 촬영 정보(카메라 · 날짜 등)다.\
> 예: `img.info` 에서 들여다볼 수 있다.

### (2) `resize` 와 `thumbnail`

**언제 쓰나** — 정해진 크기로 맞출 때는 `resize`, 비율을 지키며 「이 상자 안에 들어가게」 줄일 때는 `thumbnail`.

```text
원본 1600 × 1200 (가로:세로 = 4:3)

img.resize((800, 600))   → 새 Image 800 × 600       (원본 그대로)
img.resize((800, 800))   → 새 Image 800 × 800       (4:3 이 1:1 로 찌그러짐)

c = img.copy()
c.thumbnail((800, 800))  → c 자체가 800 × 600 으로 바뀜 (img 는 1600 × 1200 그대로)
   배율 = min(800/1600, 800/1200) = min(0.5, 0.67) = 0.5
```

- `resize((가로, 세로))` 는 주어진 크기를 **정확히** 맞추고 새 이미지를 돌려준다.
- 원본과 비율이 다른 크기를 주면 그림이 늘어나거나 눌린다.
- `thumbnail((가로, 세로))` 는 그 크기를 「최대 상자」로 보고, 비율을 유지한 채 상자 안에 들어가도록 줄인다.
- 가로·세로 배율 가운데 작은 쪽을 고르므로 한 변은 상자에 딱 맞고 다른 변은 상자보다 작다.
- `thumbnail` 은 새 이미지를 돌려주지 않고 **호출한 객체 자체를 바꾼다** — 그래서 예제는 먼저 `copy()` 로 사본을 뜬다.

`resize` 의 두 번째 인자로 리샘플링 방법을 고른다.

| 리샘플링 | 원본의 설명 |
|---|---|
| `Image.Resampling.LANCZOS` | 최고 품질 |
| `Image.Resampling.BILINEAR` | 빠름 |
| `Image.Resampling.NEAREST` | 가장 빠름 |

> **리샘플링** — 크기를 바꿀 때 새 픽셀의 색을 원래 픽셀들로부터 계산하는 방법이다.\
> 예: `NEAREST` 는 가장 가까운 픽셀 하나를 그대로 가져다 쓴다.

### (3) `crop` 과 중앙 크롭

**언제 쓰나** — 이미지의 일부 직사각형만 떼어 낼 때.

```text
좌표: 왼쪽 위가 (0, 0), x 는 오른쪽으로, y 는 아래로 커진다

img.crop((100, 100, 500, 400))
          left upper right lower
결과 크기 = (right - left, lower - upper) = (400, 300)

중앙 크롭 (한 변 new_size)
left = (w - new_size) // 2
top  = (h - new_size) // 2
box  = (left, top, left + new_size, top + new_size)
```

- `crop()` 은 상자 `(left, upper, right, lower)` 를 받아 그 안만 담은 새 이미지를 돌려준다.
- 상자의 네 값은 크기가 아니라 **좌표**라서, 결과 크기는 오른쪽 − 왼쪽, 아래 − 위로 나온다.
- 중앙 크롭은 「남는 여백을 반으로 나눈 값」을 왼쪽·위 좌표로 쓴다.
- `//` 는 정수 나눗셈이라 좌표가 정수로 떨어진다.

> **크롭 상자** — 잘라 낼 영역을 `(left, upper, right, lower)` 네 좌표로 적은 튜플이다.\
> 예: `(0, 0, 100, 50)` 은 왼쪽 위에서 가로 100, 세로 50 만큼이다.

### (4) 회전 · 뒤집기 · 모드 변환

**언제 쓰나** — 사진 방향을 바로잡거나, 흑백으로 만들거나, 투명도를 붙이거나 뗄 때.

```text
img.rotate(45)                    → 반시계 45도, 캔버스 크기는 원본 그대로 → 모서리가 잘리고 빈 곳이 생김
img.rotate(45, expand=True)       → 돌린 그림이 다 들어가도록 캔버스를 넓힘
img.rotate(45, fillcolor='white') → 빈 곳을 흰색으로 채움

img.transpose(Image.Transpose.FLIP_LEFT_RIGHT) → 좌우 뒤집기
img.transpose(Image.Transpose.FLIP_TOP_BOTTOM) → 상하 뒤집기
img.transpose(Image.Transpose.ROTATE_90)       → 90도 회전

img.convert('L')     → 흑백      (mode 'L')
img.convert('RGBA')  → 투명도 추가 (mode 'RGBA')
rgba.convert('RGB')  → 투명도 제거 (mode 'RGB')
```

- `rotate()` 의 양수 각도는 반시계 방향이다.
- `expand` 없이 돌리면 결과 크기가 원본과 같아서, 바깥으로 나간 모서리는 잘리고 안쪽 빈 곳은 채움색으로 메워진다.
- `transpose()` 는 뒤집기와 90도 단위 회전을 한다.
- `convert(모드)` 는 지정한 모드의 새 이미지를 돌려준다.

### (5) 필터와 보정

**언제 쓰나** — 흐리게 · 또렷하게 · 윤곽만 뽑기(필터), 밝기 · 대비 · 채도 · 선명도 손잡이 돌리기(보정).

```text
img.filter(ImageFilter.BLUR)             → 새 Image (흐림)
img.filter(ImageFilter.GaussianBlur(5))  → 새 Image (반경 5 가우시안 흐림)
ImageEnhance.Brightness(img).enhance(1.5) → 새 Image (더 밝음)
                                   └─ 배율: 1.0 = 원본, 1 보다 크면 강하게
```

| `ImageFilter` | 하는 일 |
|---|---|
| `BLUR` | 블러 |
| `GaussianBlur(반경)` | 가우시안 블러 |
| `SHARPEN` | 샤프닝 |
| `DETAIL` | 디테일 강조 |
| `FIND_EDGES` | 엣지 검출 |
| `CONTOUR` | 윤곽선 |
| `EMBOSS` | 엠보싱 |
| `UnsharpMask(radius, percent, threshold)` | 사진 보정에 많이 쓰는 언샤프 마스크 — 블러 반경 · 효과 강도 · 임계값 |

| `ImageEnhance` | 예제의 배율 | 뜻 |
|---|---|---|
| `Brightness` | `1.5` | 1.0 이 원본, 1 보다 크면 밝게 |
| `Contrast` | `1.3` | 대비를 높임 |
| `Color` | `0.0` | 0 은 흑백, 1 은 원본, 2 는 색 강조 |
| `Sharpness` | `2.0` | 선명하게 |

- `filter()` 는 필터 상수나 필터 객체를 받아 새 이미지를 돌려준다.
- `ImageEnhance.X(img)` 로 손잡이를 만들고 `.enhance(배율)` 로 결과를 얻는다.
- 배율 1.0 은 「원본 그대로」라는 기준점이다.

> **언샤프 마스크** — 흐린 사본과 원본의 차이를 키워 경계를 또렷하게 하는 보정이다.\
> 예: `ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)`.

### (6) 글자와 도형 그리기

**언제 쓰나** — 워터마크 · 캡션 · 표시용 상자를 이미지 위에 직접 그릴 때.

```text
img  = Image.new('RGB', (600, 300), color='white')   → 흰 캔버스
draw = ImageDraw.Draw(img)                           → img 위에 그리는 펜
font = ImageFont.truetype(경로, 36)  (실패하면 load_default())

draw.text((50, 50), 'Hello, Pillow!', fill='black', font=font)  → img 가 바뀜

bbox = draw.textbbox((0, 0), 'Centered', font=font)  → (left, top, right, bottom)
tw   = bbox[2] - bbox[0]                              → 글자 너비
x    = (600 - tw) // 2                                → 가운데 정렬 x
```

- `Image.new(모드, 크기, color)` 는 빈 캔버스를 만든다.
- `ImageDraw.Draw(img)` 로 만든 펜은 `img` **자체**에 그린다 — 새 이미지를 돌려주지 않는다.
- `ImageFont.truetype(경로, 크기)` 로 글꼴 파일을 읽고, 경로가 없으면 `except` 에서 `load_default()` 로 넘어간다.
- `textbbox()` 는 글자가 차지할 상자를 돌려주고, 오른쪽 − 왼쪽이 너비, 아래 − 위가 높이다.
- 가운데 정렬은 중앙 크롭과 같은 꼴 `(전체 − 대상) // 2` 이다.
- 도형은 `rectangle([x0, y0, x1, y1])` · `ellipse([x0, y0, x1, y1])`(그 상자에 맞는 타원) · `line([(x, y), (x, y)])` 이고, `outline` · `fill` · `width` 로 선 · 채움 · 굵기를 정한다.

> **바운딩 박스** — 글자나 도형을 빈틈없이 감싸는 가장 작은 직사각형의 좌표다.\
> 예: `bbox[2] - bbox[0]` 이 그 상자의 너비다.

### (7) 합성 — `paste` · `blend` · 일괄 처리

**언제 쓰나** — 로고를 배경에 얹거나, 두 사진을 반투명하게 섞거나, 폴더 안 사진을 한꺼번에 줄일 때.

```text
background.paste(fg, (50, 50), fg)     → background 자체가 바뀜
                          └ 3번째 인자 = 마스크 (fg 가 RGBA 면 그 투명도를 마스크로)

Image.blend(img1, img2, alpha=0.5)    → 새 Image, 50:50 섞음
   (두 이미지의 크기와 모드가 같아야 한다 → 예제는 둘 다 resize((400, 300)))

batch_resize(input_dir, output_dir):
   폴더 만들기(exist_ok=True) → 파일마다 확장자 검사 → open → thumbnail → save
```

- `paste(이미지, 위치, 마스크)` 는 배경 이미지에 직접 붙인다.
- 마스크를 주면 마스크가 투명한 곳은 배경이 남고, 마스크가 없으면 붙이는 네모 전체가 배경을 덮어쓴다.
- 그래서 예제는 `foreground.mode == 'RGBA'` 일 때만 자기 자신을 마스크로 넘긴다.
- `Image.blend()` 는 `alpha` 비율로 두 이미지를 섞은 새 이미지를 돌려준다 — `alpha=0.5` 는 반반이다.
- 일괄 처리 함수는 `filename.lower().endswith(('.png', '.jpg', '.jpeg'))` 로 대소문자와 상관없이 이미지 파일만 고른다.
- 여기서는 파일마다 새로 연 객체라 원본 객체가 바뀌어도 상관없으므로 `copy()` 없이 `thumbnail()` 을 바로 쓴다.

> **마스크** — 어느 픽셀을 얼마나 붙일지 정하는 흑백(또는 알파) 이미지다.\
> 예: RGBA 로고의 투명한 부분은 마스크가 0 이라 배경이 그대로 보인다.

## 문법 — 형태와 규칙

```python
from PIL import Image, ImageFilter, ImageDraw

img = Image.new('RGB', (400, 200), 'white')   # 빈 캔버스
draw = ImageDraw.Draw(img)                    # img 에 직접 그린다
draw.rectangle([20, 20, 120, 80], outline='black', width=2)

small = img.copy()                            # 사본을 떠서
small.thumbnail((200, 200))                   # 사본만 줄인다 (200 x 100)

part = img.crop((0, 0, 200, 100))             # 새 이미지 200 x 100
soft = img.filter(ImageFilter.GaussianBlur(2))
img.convert('RGB').save('out.jpg', quality=85)
```

- 크기는 언제나 `(가로, 세로)` 튜플이다.
- 좌표는 왼쪽 위가 `(0, 0)` 이고 `crop` 상자는 `(left, upper, right, lower)` 다.
- 새 이미지를 **돌려주는** 것: `resize` · `crop` · `rotate` · `transpose` · `convert` · `filter` · `enhance` · `Image.blend` · `copy`.
- 객체를 **제자리에서 바꾸는** 것: `thumbnail` · `paste` · `ImageDraw` 의 그리기 메서드.
- `Image.Resampling.*` · `Image.Transpose.*` 는 상수 묶음으로 쓴다.
- JPEG 로 저장할 이미지는 `RGB`(또는 `L`) 모드여야 한다.

| 모듈 / 클래스 | 예제에 나온 것 |
|---|---|
| `Image` | `open()` · `new()` · `save()` · `resize()` · `crop()` · `rotate()` · `thumbnail()` · `transpose()` · `convert()` · `paste()` · `blend()` · `copy()` |
| `ImageFilter` | `BLUR` · `SHARPEN` · `FIND_EDGES` · `GaussianBlur()` · `UnsharpMask()` 등 |
| `ImageEnhance` | `Brightness` · `Contrast` · `Color` · `Sharpness` |
| `ImageDraw` | `text()` · `textbbox()` · `rectangle()` · `ellipse()` · `line()` |
| `ImageFont` | `truetype()` · `load_default()` |

## 어디서 틀리나

### 1. `thumbnail()` 이 원본을 바꿔 버린다
`thumbnail()` 은 호출한 객체 자체를 줄인다.
원본을 다른 작업에 다시 쓸 계획이면 `img.copy()` 로 사본을 만든 뒤 사본에 부른다.
원본의 팁대로 `copy()` 후 쓰는 것이 안전하다.

### 2. RGBA 이미지를 JPEG 로 저장하면 에러가 난다
JPEG 는 투명도 채널을 담지 못한다.
PNG 에서 읽은 RGBA 이미지를 `.jpg` 로 저장하려면 먼저 `convert('RGB')` 로 투명도를 떼어 낸다.

### 3. `resize()` 에 비율이 다른 크기를 주면 찌그러진다
`resize()` 는 주어진 크기를 정확히 맞출 뿐 비율을 지켜 주지 않는다.
비율을 지키려면 `thumbnail()` 을 쓰거나 비율을 계산해서 넘긴다.

### 4. 리샘플링은 품질과 속도의 맞바꿈이다
원본의 팁은 `LANCZOS` 가 품질이 가장 좋다고 한다.
`NEAREST` 는 가장 빠르지만 거칠다.
많은 사진을 빨리 처리해야 하면 `BILINEAR` · `NEAREST` 를 고려한다.

### 5. `rotate()` 기본값은 캔버스를 넓히지 않는다
45도처럼 90도 단위가 아닌 각도로 돌리면 모서리가 잘린다.
전부 보이게 하려면 `expand=True`, 빈 곳의 색을 정하려면 `fillcolor` 를 준다.

### 6. `paste()` 에 마스크를 빼면 투명한 부분까지 덮는다
RGBA 로고를 마스크 없이 붙이면 네모 전체가 배경을 덮어쓴다.
세 번째 인자로 로고 자신을 넘겨야 투명한 곳에 배경이 남는다.

### 7. `Image.blend()` 는 크기와 모드가 같아야 한다
크기가 다른 두 이미지는 섞을 수 없어 에러가 난다.
예제가 두 이미지를 모두 `resize((400, 300))` 하는 까닭이다.

### 8. 글꼴 경로는 운영체제마다 다르다
예제의 `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` 는 리눅스에서 쓰는 경로다.
그 파일이 없으면 `except` 로 넘어가 `load_default()` 를 쓴다.
`except:` 는 어떤 예외든 다 삼키므로 글꼴 말고 다른 문제까지 가려질 수 있다.

### 9. 원본의 팁 「with문은 지원하지 않는다」
원본의 주장 → `Image` 는 `with` 문을 지원하지 않으므로 직접 `close()` 하거나 그냥 두면 된다.
왜 의심스러운가 → Pillow 의 `Image` 객체는 `with Image.open(...) as im:` 꼴로 쓰는 예가 널리 쓰인다 (확인 필요).
열어 둔 파일을 확실히 닫고 싶으면 `close()` 나 `with` 를 쓰는 편이 낫다.

### 10. 원본 주석 「텍스트 크기 측정 (Pillow 10+)」
원본의 주장 → `textbbox()` 는 Pillow 10 이상의 기능이다.
왜 의심스러운가 → `textbbox()` 는 그보다 이른 버전부터 있었고, 10 에서 일어난 일은 옛 `textsize()` 가 없어진 것으로 알려져 있다 (확인 필요).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `thumbnail()` 이 객체를 제자리에서 바꾼다 | Pillow 라이브러리의 API 동작 |
| `LANCZOS` 가 품질이 가장 좋다 | Pillow 문서와 일반적 평가 — 이미지와 용도에 따라 다를 수 있다 (확인 필요) |
| RGBA 를 JPEG 로 저장하면 에러 | JPEG 형식의 한계 + Pillow 의 JPEG 저장기 |
| `Image` 는 `with` 를 지원하지 않는다 | 원본의 주장 — 현재 Pillow 와 맞지 않을 수 있다 (확인 필요) |
| `Image.Resampling` · `Image.Transpose` 상수 묶음 | Pillow 특정 버전 이후의 API (확인 필요) |
| `textbbox()` 는 Pillow 10+ | 원본 주석 — 버전 범위가 의심스럽다 (확인 필요) |
| DejaVu 글꼴 경로 | 운영체제와 설치된 글꼴 |
| `//` 가 정수 몫을 낸다 · `try/except` 흐름 | 파이썬 언어 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 정확히 800×600 이 필요하다 | `resize((800, 600))` | `thumbnail()` |
| 비율을 지키며 상자 안에 맞춘다 | `copy()` + `thumbnail()` | 비율이 다른 `resize()` |
| 정사각형 대표 이미지를 만든다 | 중앙 크롭 공식 + `crop()` | 비율이 다른 `resize()` |
| 사진을 기울어진 채 전부 보이게 돌린다 | `rotate(각도, expand=True)` | 기본 `rotate()` |
| 좌우 대칭 사진을 만든다 | `transpose(FLIP_LEFT_RIGHT)` | `rotate(180)` |
| 투명 로고를 얹는다 | `paste(로고, 위치, 로고)` | 마스크 없는 `paste()` |
| 투명 PNG 를 JPEG 로 저장한다 | `convert('RGB')` 후 `save()` | RGBA 그대로 `save('*.jpg')` |
| 글자를 가운데 놓는다 | `textbbox()` 로 너비를 재고 `(전체 − 너비) // 2` | 글자 수로 너비 어림 |

## 핵심 문장

1. **대부분의 작업은 새 `Image` 를 돌려주지만, `thumbnail` · `paste` · `ImageDraw` 는 그 객체를 직접 바꾼다.**
2. **`resize` 는 크기를 정확히 맞추고, `thumbnail` 은 비율을 지키며 상자 안에 들어가게 줄인다.**
3. **`crop` 상자는 크기가 아니라 `(left, upper, right, lower)` 좌표이며, 가운데 맞추기는 `(전체 − 대상) // 2` 한 공식이다.**
4. **모드가 저장 형식과 합성을 가른다 — JPEG 는 RGB, 투명 합성은 RGBA 마스크.**
5. **필터는 `img.filter(...)`, 보정은 `ImageEnhance.X(img).enhance(배율)` 이며 배율 1.0 이 원본이다.**

## 관련 자료

- `regex-advanced` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [sklearn-preprocessing](../09-sklearn-preprocessing/2-summary.md)
- [plotly-interactive](../12-plotly-interactive/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/data-science.json` 의 `image-processing`

## 용어 풀이

- **Pillow / PIL** — 파이썬 이미지 처리 라이브러리와 그 옛 이름; 모듈 이름은 지금도 `PIL` 이다.
- **`Image` 객체** — 열거나 만든 이미지 한 장을 담은 객체다.
- **모드** — 픽셀의 채널 구성(`RGB` · `RGBA` · `L`)이다.
- **알파(투명도)** — RGBA 의 A, 픽셀이 얼마나 비치는지 나타내는 채널이다.
- **EXIF** — 사진 파일에 딸린 촬영 정보다.
- **리샘플링** — 크기를 바꿀 때 새 픽셀 색을 계산하는 방법이다.
- **썸네일** — 비율을 유지해 줄인 작은 이미지다.
- **크롭 상자** — 잘라 낼 영역의 `(left, upper, right, lower)` 좌표다.
- **`transpose`** — 뒤집기와 90도 단위 회전이다.
- **필터** — 픽셀 주변을 보고 흐림 · 선명 · 윤곽 같은 효과를 내는 처리다.
- **언샤프 마스크** — 흐린 사본과의 차이를 키워 경계를 또렷하게 하는 보정이다.
- **보정 배율** — `enhance()` 에 넘기는 값으로 1.0 이 원본이다.
- **바운딩 박스** — 대상을 감싸는 가장 작은 직사각형 좌표다.
- **마스크** — 붙일 때 픽셀마다 얼마나 반영할지 정하는 이미지다.
- **블렌딩** — 두 이미지를 비율대로 섞는 합성이다.
- **제자리 변경** — 새 객체를 만들지 않고 그 객체 자체를 바꾸는 동작이다.

## 더 들어가면

- `thumbnail()` 은 새 이미지가 아니라 `None` 을 돌려준다 — `small = img.thumbnail(...)` 처럼 받으면 `small` 이 `None` 이 된다 (확인 필요).
- `thumbnail()` 은 줄이기만 하고, 원본이 상자보다 작으면 키우지 않는다 (확인 필요).
- `Image.new()` 로 만들었거나 변환으로 얻은 이미지는 `format` 이 `None` 이다 (확인 필요).
- `Image.open()` 은 파일 머리만 먼저 읽고 픽셀은 실제로 필요할 때 읽는 지연 로딩을 한다 (확인 필요).
- 휴대폰 사진은 EXIF 의 방향 정보 때문에 열면 누워 보일 수 있으며 `ImageOps.exif_transpose()` 로 바로잡는다 (확인 필요).
- 중앙 크롭과 리사이즈를 한 번에 하는 `ImageOps.fit()` 이 있다 (확인 필요).
- `numpy.array(img)` 로 픽셀을 배열로 바꿔 수치 계산과 이어 붙일 수 있다 (확인 필요).
