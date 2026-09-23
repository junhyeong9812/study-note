# css/syntax/44 — 배경과 대체 요소 맞춤 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 질문 → 서머리 → 여기 순서다.
> 번호는 [1-question.md](1-question.md)와 1:1 이다. **출력을 먼저, 해설은 그 뒤.**
> 모든 계산값은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이고, 모든 좌표·RGB 는 **스크린샷 PNG 의 픽셀을 파이썬으로 읽어 뽑은 값**이다.

### 1. 단축이 푸는 아홉 가지

**출력**

```text
background-image       url("data:image/gif;base64,...")
background-position-x  right 10px
background-position-y  bottom 20px
background-size        40px 30px
background-repeat      no-repeat
background-origin      content-box
background-clip        padding-box
background-attachment  initial            ★ 안 적었는데 들어갔다
background-color       rgb(238, 238, 238)
```

**내가 적지 않았는데 값이 들어간 것은 `background-attachment` 이고, `initial` 로 들어갔다.**

**왜 그런가**

- **단축은 자기가 푸는 롱핸드를 전부 재설정한다.** 안 적은 것은 `initial` 이다. 「건드리지 않는다」가 아니라 **「초기값으로 되돌린다」** 다.
- 그래서 앞에서 `background-attachment: fixed` 를 적어 놨어도 이 한 줄이 그것을 지운다.
- **`position` 과 `size` 는 `/` 가 가른다.** `/` 를 빼면 `40px 30px` 이 위치로 읽힌다.
- **상자 값이 둘이면 앞이 `origin`, 뒤가 `clip`** 이다.

### 2. 상자 값을 하나만 적으면

**출력**

```text
선언                                 background-origin   background-clip
-----------------------------------  ------------------  ---------------
background: padding-box red          padding-box         padding-box   ★ 둘 다
background: border-box padding-box red   border-box      padding-box
```

**`clip` 만 바꾸려면 롱핸드를 쓴다.**

```css
.a { background-color: red; background-clip: padding-box; }   /* origin 은 안 건드린다 */
```

**왜 그런가**

- 단축 문법이 **상자 값 하나를 `origin` 과 `clip` 둘 다에 넣도록** 정의돼 있다. 대개 둘을 맞추고 싶어 하기 때문이다.
- 그래서 **단축에서는 둘을 독립으로 다룰 수 없다.** 둘을 다르게 하려면 **두 값을 다 적거나** 롱핸드를 쓴다.

### 3. 배경 레이어 둘이 겹치면 누가 보이나

**출력**

```text
x=50    rgb(220,  38,  38)   빨강    ← 두 레이어가 겹치는 구간. 첫째(빨강)가 이겼다 ★
x=130   rgb( 37,  99, 235)   파랑    ← 둘째만 있는 구간
x=190   rgb(255, 255, 255)   흰색    ← 둘 다 투명. 페이지 바탕
```

**`background-color: yellow` 를 더하면 — x = 190 구간만 노랑이 된다.**

```text
  실측 (background-color: yellow 를 더한 뒤)
  x=50   rgb(220,  38,  38)   빨강 그대로
  x=130  rgb( 37,  99, 235)   파랑 그대로
  x=190  rgb(255, 255,   0)   노랑 ★
  x=210  rgb(255, 255,   0)   노랑
```

**왜 그런가**

```text
  소스에 적은 순서 = 위에서 아래로

    첫째 레이어 (빨강)    ────── 가장 위
    둘째 레이어 (파랑)    ──────
    background-color      ────── 가장 아래. 레이어가 아니라 바닥 한 장
```

- **먼저 쓴 것이 위다.** `z-index` 와 직관이 반대다.
- `background-color` 는 **모든 이미지 레이어 아래**에 깔린다. 그래서 두 레이어가 다 투명한 구간에서만 보인다.
- `background-color` 는 **쉼표로 여러 개 못 적는다** — 언제나 하나다.

### 4. `origin` 과 `clip` 을 하나씩 바꾸면

**출력**

```text
바꾼 것                        타일의 시작 좌표        칠해진 구간
-----------------------------  ---------------------  ----------------
origin: border-box → content-box   (0,0) → (30,30) ★   0..239 → 0..239  (안 변함)
clip:   border-box → content-box   (30,30) 그대로      0..239 → 30..209 ★
```

**`origin` 은 타일의 시작 좌표만, `clip` 은 칠해진 구간만 바꾼다. 서로의 일을 전혀 안 건드린다.**

**왜 그런가**

```text
  상자 (내용 180×70, 패딩 20, 테두리 10  → 전체 240×130)

   0    10        30                     209      229  239
   ├────┼─────────┼──────────────────────┼─────────┼────┤
   │border│ padding│       content        │ padding │border│

  origin = 이미지의 (0,0) 을 어느 모서리에 맞추나
      border-box  → (0, 0)
      padding-box → (10, 10)
      content-box → (30, 30)

  clip = 어디까지 칠하나
      border-box  → 0..239
      padding-box → 10..229
      content-box → 30..209
```

- 실측으로 **네 조합을 교차 확인**했다 — `origin` 셋을 돌렸을 때 칠 구간이 셋 다 `0..239` 였고, `clip` 셋을 돌렸을 때 타일 시작점이 안 움직였다.
- ★ **주의** — `origin: border-box` 인데 `clip: content-box` 로 하면 **타일이 칠 영역 밖에 놓여 아예 안 보인다.** (문서의 demo 를 이 조합으로 짰다가 점이 사라져서 고쳤다.)
- `background-attachment: fixed` 이면 **`origin` 은 무시된다** — 위치 영역이 뷰포트가 되기 때문이다.

### 5. `space` 와 `round`

**출력**

```text
값        타일 개수    주황 점의 중심 간격      background-size 계산값
--------  -----------  ---------------------  ----------------------
space         3        65, 65                 50px 50px
round         4        45, 45, 45             50px 50px   ★ 안 바뀐다
(비교) repeat-x  4     50, 50, 46.5           50px 50px
```

**`round` 로 줄어든 크기는 `getComputedStyle().backgroundSize` 로 읽을 수 없다.** 실측에서 `space`·`round` 둘 다 선언값 `50px 50px` 그대로였다.

**왜 그런가**

```text
  180px 안에 50px 타일을  →  180 / 50 = 3.6

  space  :  버림해서 3개.  남는 30px 를 두 틈에 15px 씩 뿌린다
            [50] 15 [50] 15 [50]        중심 간격 65
            ★ 타일 크기를 절대 안 바꾼다

  round  :  반올림해서 4개.  180/4 = 45 로 타일을 줄인다
            [45][45][45][45]            중심 간격 45
            ★ 개수를 맞추려고 크기를 바꾼다
```

- **줄어든 45px 는 사용값**이다. 계산값 단계에는 내가 적은 `50px` 이 그대로 있다 — [04번](../04-value-processing-stages/2-summary.md)에서 본 구조와 같다.
- 그래서 **이 차이는 픽셀을 재야만 보인다.** 계산값만 읽으면 세 값이 전부 같아 보인다.

### 6. 같은 `cover` 인데 결과가 다르다

**출력** (y = 60 가로줄)

```text
                       x=5      x=55     x=65     x=115
---------------------  -------  -------  -------  -------
<img> object-fit       파랑     파랑     빨강     빨강     ← 가운데 기준으로 좌우를 잘랐다
<div> background-size  파랑     파랑     파랑     파랑     ← 왼쪽에 붙이고 오른쪽을 잘랐다

실측 RGB — 파랑 rgb(37, 99, 235) · 빨강 rgb(220, 38, 38)
```

**왜 다른가 — 기본 정렬이 다르다.**

```text
  object-position   기본값  50% 50%   (가운데)
  background-position 기본값 0% 0%     (왼쪽 위)   ★

  16×8 (2:1) 이미지를 120×120 칸에 cover 로 넣으면 240×120 이 된다.
  240 중에서 120 만 보인다 — 어느 120 을 보여 주느냐가 갈린다.

  object-fit: cover        [····|■■■■■■■■■■■■|····]   가운데 120
  background-size: cover   [■■■■■■■■■■■■|········]    왼쪽 120
```

- **규칙(`cover`) 은 같다.** 다른 것은 **자른 뒤 어디를 보여 주느냐**다.
- `.bg` 에 `background-position: center` 를 더하면 **두 칸이 같아진다.**
- **`<img>` 상자 자체의 크기는 `object-fit` 이 안 바꾼다** — 다섯 값 전부 `getBoundingClientRect()` 가 `120x120` 이었다.

### 7. `background-clip: text` 만 주면

**출력**

```text
선언                                  흰색 아닌 픽셀   글자 속 픽셀
------------------------------------  --------------  ------------------
clip: text  (color 기본)                 2,718        rgb(  0,  0,  0)   검정
clip: text + color: transparent          2,718        rgb(209, 35, 86)   그라디언트 ★
(비교) clip 기본값                       21,600        rgb(  0,  0,  0)
```

**글자는 검정이다.** 그라디언트를 보려면 **`color: transparent`** 를 같이 적는다.

**왜 그런가**

```text
  clip: text 가 한 일           글자가 한 일
  ┌──────────────────┐          ┌──────────────────┐
  │ 배경을 글자 모양으로│  →      │ 그 위에 color 로  │
  │ 잘랐다             │          │ 다시 칠했다      │
  └──────────────────┘          └──────────────────┘
       칠해진 픽셀 2,718 개            같은 자리를 덮는다
```

- **첫 줄과 둘째 줄의 칠해진 픽셀 수가 2,718 로 똑같다** — 칠 영역은 이미 글자 모양으로 잘려 있고, 달라진 것은 **그 위를 덮는 글자색**뿐이라는 증거다.
- Chrome 151 에서 `-webkit-background-clip` 은 **같은 속성의 별칭**이다(둘 다 계산값 `text`). 하지만 **Baseline 이 `limited`** 라 접두사를 같이 적는 편이 안전하다.
- 글자를 `transparent` 로 만들면 **배경 이미지가 안 뜨는 환경에서 글자가 사라진다.** `@supports` 로 감싸는 편이 좋다.

### 8. `background: red` 한 줄의 부작용

**단축이 `background-image` 를 `initial`(= `none`)로 되돌렸기 때문이다.**

```css
/* 고치는 법 — 롱핸드로 색만 바꾼다 */
.card.on { background-color: red; }
```

- 단축의 값어치는 「여러 개를 한 줄에」인데, **그 대가가 「안 적은 것은 초기화」** 다.
- 미디어 쿼리·상태 클래스처럼 **한 조각만 덮어쓰는 자리에서는 언제나 롱핸드**를 쓴다.
- 같은 함정이 `font`·`border`·`grid` 같은 다른 단축에도 그대로 있다.

### 9. `object-fit` 을 `<div>` 에 주면

**진단 3창으로는 안 잡힌다.**

```text
  창 1  cssRules[j].style.cssText   "object-fit: cover;"    ← 담겼다
  창 2  querySelectorAll('div')     1                       ← 잡았다
  창 3  getComputedStyle(el).objectFit  "cover"             ← 이겼다

  세 창이 전부 정상인데 화면에는 아무 변화가 없다.
```

- **`object-fit` 은 대체 요소의 「내용물」을 배치하는 속성**이다. `<div>` 에는 배치할 내용물이 없다.
- 이것은 **「버려졌나」가 아니라 「적용될 대상이 없나」** 라는 제4의 상태다. 진단 3창이 못 보는 자리다.
- 잡는 법은 **「이 속성이 어느 요소 종류에 적용되나」를 확인하는 것**뿐이다. 명세의 `Applies to:` 칸이 그 답이다.

### 10. `background-attachment: fixed` 가 바꾸는 것

**출력**

```text
값       x=2                  x=50                 x=98
-------  -------------------  -------------------  -------------------
scroll   rgb(220, 30,  76)    rgb(130, 64, 154)    rgb( 40,  98, 232)   ← 다 변했다
local    rgb(220, 30,  76)    rgb(130, 64, 154)    rgb( 39,  98, 232)   ← scroll 과 같다
fixed    rgb(223, 29,  73)    rgb(200, 38,  93)    rgb(177,  47, 113)   ★ 거의 안 변했다
```

**`fixed` 는 위치 영역이 요소의 상자가 아니라 뷰포트가 된다.**

```text
  scroll — 위치 영역 = 요소 상자(100px)      fixed — 위치 영역 = 뷰포트
  [■■■■■■■■■■] 100px 안에서                  [■■■■■■■■■■■■■■■■■■■■■■■■] 뷰포트 폭
   그라디언트가 처음부터 끝까지               [■■■] ← 요소는 이 앞부분만 보여 준다
```

- 그래서 **100px 상자 안에서는 그라디언트의 앞쪽 한 조각만** 보이고 색이 거의 안 변한다.
- `fixed` 는 **`background-origin` 을 무시한다.**
- ★ **`scroll` 과 `local` 은 이 실험으로 구분할 수 없다** — 한 장면 스크린샷에서는 픽셀이 1 단위 차이로 같았다. **요소 안을 실제로 스크롤해야** 갈린다. 「못 잰 것」이지 「같다」가 아니다.

### 11. `background-position: right 10px bottom 10px` 의 계산값

**출력**

```text
선언                                         계산값
-------------------------------------------  ----------------------------------
background-position: right 10px bottom 10px  calc(100% - 10px) calc(100% - 10px)
background-position: right bottom            100% 100%
background-position: 100% 100%               100% 100%
background-position: 10px 10px               10px 10px
```

**`100% 100%` 가 「영역 폭만큼 민다」가 아닌 이유**

```text
  % 의 뜻 — 「이미지의 그 지점」이 「영역의 그 지점」에 온다

   0%                  50%                  100%
   ┌────────────────────────────────────────┐ 영역
   │                                        │
   └────────────────────────────────────────┘
   ■■■                                  ■■■
   이미지 왼쪽 끝이                     이미지 오른쪽 끝이
   영역 왼쪽 끝에                       영역 오른쪽 끝에

  만약 「영역 폭만큼 민다」였으면 100% 에서 이미지가 완전히 밖으로 나갔을 것이다.
```

- 실측 좌표가 이것을 확인한다 — 20px 타일을 200px 영역에 `100% 100%` 로 놓으니 **x 185..194**(오른쪽 끝에 붙음)였다.
- 네 값 구문은 **가장자리 키워드 + 거리**를 한 쌍으로 읽는다. `right 10px` = 「오른쪽에서 10px 안으로」.
- `10px 10px` 은 기본 기준이 `left top` 이라 **왼쪽·위에서** 10px 이다.

### 12. 썸네일은 `<img>` 인가 배경인가

**기준은 「그 이미지가 내용인가 장식인가」** 다.

| | `<img>` + `object-fit` | `background-image` |
|---|---|---|
| 대체 텍스트 | `alt` 로 준다 | **줄 수 없다** |
| 스크린 리더 | 읽는다 | 무시한다 |
| 이미지 로딩 실패 | `alt` 가 보인다 | 아무것도 없다 |
| 인쇄 | 기본으로 나온다 | 기본 설정에서 빠질 수 있다 |
| 반응형 소스 | `srcset`·`<picture>` | `image-set()` 로 제한적으로 |
| 기본 정렬 | 가운데(`50% 50%`) | 왼쪽 위(`0% 0%`) |

- **카드의 썸네일은 내용**이다 — 무엇에 대한 카드인지를 그 그림이 말한다. `<img>` 로 한다.
- **무늬·그라디언트·장식 아이콘은 장식**이다 — 배경으로 한다. 스크린 리더가 읽으면 오히려 방해다.
- 화면만 보면 둘을 같게 만들 수 있으므로 **화면으로는 이 판단을 할 수 없다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| `background` 단축이 푸는 롱핸드 | `--dump-dom` 으로 `cssRules` 10개 규칙 회수 | 1 | 1·2번 표 |
| 레이어 순서·`background-color` 자리 | `--screenshot` → 픽셀 | 2 | 3번 표 |
| `origin` 대 `clip` 교차 실험 | 여섯 상자를 찍어 **주황 점의 상자**와 **칠해진 구간**을 좌표로 뽑았다 | 2 | 4번 표 |
| `space`/`round`/`repeat-x` | 타일 중심 간격을 픽셀에서 계산 | 2 | 5번 표 |
| `object-fit` 5값 대 `background-size` 5값 | 같은 이미지·같은 칸을 열 개 찍어 그림이 놓인 칸을 좌표로 뽑았다 | 1 | 6번 표 |
| `background-clip: text` | 흰색 아닌 픽셀 수를 셌다 | 1 | 7번 표 |
| `background-attachment` 3값 | 픽셀 | 1 | 10번 표 |
| `background-position` 4형태 | 계산값 + 타일 좌표 | 1 | 11번 표 |
| Baseline 조회 | `webstatus.dev` API | 1 | 머리말 |
| demo 블록 3개 | 완성된 문서에서 다시 뽑아 재렌더 + 픽셀 대조 | 2 | 1차에서 **거짓 1건**을 잡았다(아래) |

★ **demo 재실행에서 잡힌 거짓 1건** — 「`origin: border-box` + `clip: content-box`」 조합으로 짠 셋째 상자에서 **주황 점이 칠 영역 밖이라 아예 안 보였는데**, 「보이는 것」에는 「점은 첫째와 같은 자리」라고 적혀 있었다. **화면을 눈으로 봐도 「점이 없네」 정도로만 보여 잡기 어려운 종류**였다. 조합을 `origin: content-box + clip: content-box` 로 바꿔 둘째와 짝이 되게 고쳤다.

**픽셀을 읽은 방법** — [42번의 같은 절](../42-color-notation-and-spaces/3-answer.md)과 같다. 이 주제에서는 **색 하나가 아니라 「어디까지 칠해졌나」** 를 재야 해서 한 겹 더 썼다.

```python
# 칠해진 가로 구간 — 한 행을 훑어 흰색이 아닌 첫 x 와 마지막 x
row = [im.getpixel((x, y)) for x in range(0, W)]
nz  = [x for x, p in enumerate(row) if p != (255, 255, 255)]
print(nz[0], nz[-1])

# 타일(주황 점)의 상자 — 색 범위로 걸러 min/max
xs = [x for y in range(top, top+H) for x in range(0, W)
      if (lambda p: p[0] > 180 and 90 < p[1] < 190 and p[2] < 90)(im.getpixel((x, y)))]
print(min(xs), max(xs))
```

**구현에 달린 항목 — 버전이 오르면 다시 찍을 것**

| 항목 | 왜 |
|---|---|
| 네 값 위치의 계산값이 `calc(100% - 10px)` 인 것 | CSSOM 직렬화 형식 |
| `round` 로 줄어든 크기가 계산값에 안 보이는 것 | 사용값 단계라 그렇다. 직렬화 정책이 바뀔 수 있다 |
| `-webkit-background-clip` 이 같은 속성의 별칭인 것 | Chrome 의 구현. **다른 엔진은 확인하지 못했다** |
| `background-clip: text` 를 쓸 수 있는가 | Baseline `limited` |
| `background-attachment` 의 지원 | Baseline `limited`. **모바일 동작은 확인하지 못했다** |
| `scroll` 과 `local` 의 차이 | **못 잰 것** — 한 장면 스크린샷으로는 측정 방법이 성립하지 않는다 |
