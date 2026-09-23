# css/syntax/55 — 3D 변환: `perspective`·`transform-style`·`backface-visibility` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Transforms Level 2](https://drafts.csswg.org/css-transforms-2/) (3D 함수·`perspective`·`transform-style`·`backface-visibility`·**평탄화 조건**). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 본문 실험 **7벌**을 **Google Chrome 151.0.7922.173** headless 에 CDP 로 붙여 돌렸다.\
> ★ 평탄화 실험은 **`getComputedStyle(el).transformStyle` 로는 판정할 수 없었다** — 평평해진 경우에도 계속 `preserve-3d` 를 돌려준다((5)). 그래서 **손자의 `getBoundingClientRect()` 크기**를 판정 기준으로 썼고, 앞뒤 관계는 **스크린샷 픽셀**로 읽었다.\
> **엔진은 Chrome 하나다** — 크로스 브라우저는 Baseline 으로만 접지했다.
> **버전** — CSS 에 언어 버전은 없다. 3D transforms 는 Baseline **widely**(newly 2022-03-14 → widely 2024-09-14) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**3D 변환은 「납작한 무대에 깊이를 주고, 관객을 어디에 앉힐지 정하는 것」이다.**

[54번](../54-transform-2d-and-origin/2-summary.md)의 2D 변환은 종이 위에서만 논다.\
`rotateY(45deg)` 를 줘도 **원근이 없으면 그냥 가로로 찌그러질 뿐**이다.\
깊이가 보이려면 **관객이 어디에 얼마나 가까이 앉았는지**를 따로 말해 줘야 한다 — 그게 `perspective` 다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 무대를 깊이 방향으로 돌린다 | `rotateX`·`rotateY`·`translateZ` |
| **관객이 무대에서 얼마나 떨어져 앉았나** | `perspective`(작을수록 가깝다 = 왜곡이 세다) |
| 관객이 무대의 어느 쪽에 앉았나 | `perspective-origin` |
| 무대 위 소품들이 **각자 입체로 서 있나, 사진 한 장으로 눌렸나** | `transform-style: preserve-3d` / `flat` |
| 소품의 **뒷면이 보이나** | `backface-visibility` |
| 관객에게 가까운 것이 앞에 보인다 | z 위치 정렬 — **`z-index` 와 별개다** |

- **`perspective` 가 없으면 3D 가 안 보인다.** 함수는 먹었는데 그냥 납작해질 뿐이다.
- **`preserve-3d` 는 아주 쉽게 깨진다.** `overflow: hidden` 하나면 손자가 사진 한 장으로 눌린다((5)).
- ★★ **깨졌는데 계산값은 `preserve-3d` 라고 답한다.** 이 주제에서 가장 당황스러운 자리다.

```text
  perspective 없이 rotateY(50deg)        perspective: 400px 안에서 rotateY(50deg)

    +------+                                 +-----+
    |      |   그냥 가로로 좁아진다             |      \
    |      |   (양 변이 평행)                  |       \    가까운 쪽이 크고
    |      |                                  |       /    먼 쪽이 작다
    +------+                                 +-----+       (양 변이 안 평행)
```

실무에서 터지는 자리는 **카드 뒤집기**다.\
`rotateY(180deg)` 는 되는데 **뒷면이 안 보이거나, 앞뒤가 동시에 보이거나, 아예 납작하다** — 원인이 세 속성에 흩어져 있다.

> **원근(perspective)** — 먼 것이 작게 보이도록 만드는 투영. 값은 **관객과 무대 사이의 거리**다.\
> 예: `perspective: 400px` 은 「400px 떨어져서 본다」. 값이 작을수록 가까이 앉은 것이라 왜곡이 세다.

> **평탄화(flattening)** — 자식들의 3D 위치를 무시하고 부모 평면에 **사진 한 장으로 눌러 버리는** 것.\
> 예: `transform-style: flat`(초기값)이 그렇다. 눌린 뒤에는 손자의 `translateZ` 가 아무 뜻도 없다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `perspective` 를 **부모에 주는 것**과 `transform: perspective()` 로 **자기에게 주는 것**은 무엇이 다른가.
2. **무엇이 `preserve-3d` 를 깨뜨리는가** — 그리고 깨졌는지를 어떻게 판정하는가.
3. 3D 공간에서 **누가 앞에 보이는가** — `z-index` 로 바꿀 수 있는가.

## 동작 방식

### (1) 2D 와 무엇이 다른가 — z 축이 생긴다

**언제 쓰나** — 3D 함수를 처음 쓸 때. **선행은 [54번](../54-transform-2d-and-origin/2-summary.md)이다** — 함수 순서·`transform-origin`·부작용은 거기가 정본이고, 여기서는 z 축만 더한다.

```text
  2D 좌표계                   3D 좌표계

   y                            y
   ↑                            ↑   z (화면 밖 = 나에게 가까운 쪽)
   |                            |  ↗
   +---→ x                      +---→ x

  transform: matrix(6수)       transform: matrix3d(16수)
```

- 3D 함수를 **하나라도** 쓰면 계산값이 `matrix3d(…)` **열여섯 수**로 바뀐다.
- 새로 생기는 것: `rotateX`·`rotateY`·`rotateZ`·`translateZ`·`translate3d`·`scaleZ`·`perspective()`.
- **함수 목록의 순서 규칙은 2D 와 같다** — 왼쪽부터 적용된다([54번](../54-transform-2d-and-origin/2-summary.md)).

### (2) ★ `perspective` 를 부모에 주기 대 자기에게 주기

**언제 쓰나** — 「왜 여러 카드가 제각각 이상하게 보이지」를 고칠 때.

```text
  부모에 perspective: 400px               자기 transform: perspective(400px)

  +-- 부모 --------------------+          +-- 부모 --------------------+
  |         ·(소실점)          |          |   ·(소실점)   ·(소실점)    |
  |  [A]      [B]      [C]    |          |  [A]          [B]          |
  +---------------------------+          +---------------------------+
   소실점이 '하나'다                        요소마다 소실점이 '따로'다
   -> 셋이 한 공간에 있는 것처럼            -> 셋이 각자 따로 노는 것처럼
```

*(Chrome 151 실측 — 부모 `300×120` 안의 `120×80` 상자에 `rotateY(50deg)`. 상자는 부모 안에서 왼쪽에 치우쳐 있다:)*

```text
  경우                                      rect(부모 기준)            계산값
  ① perspective 없음, rotateY(50deg)        left=72.43 top=21.00       matrix3d(…, 0, 0, 0, 1)
                                            77.13 x 80.00              ← 그냥 좁아졌다
  ② 부모 perspective: 400px                 left=62.23 top=15.81       ① 과 같은 matrix3d ★
                                            87.48 x 90.39
  ③ 자기 transform: perspective(400px) …    left=67.43 top=15.81       matrix3d(…, 0.00191511, …)
                                            78.17 x 90.39              ← 행렬에 원근이 박혔다
  ④ 둘 다                                   left=54.96 top= 9.06
                                            91.14 x 103.87             ← 두 번 걸린다
```

그림 해설 (한 단계씩):

- ①과 ②의 **계산값이 완전히 같다.** 원근이 **부모에 있기 때문**이다 — 요소 자신의 `transform` 에는 흔적이 없다.\
  ★ **계산값만 보면 ①과 ②를 구분할 수 없다.** 좌표를 재야 갈린다(77.13 대 87.48).
- ③은 **행렬에 원근 성분이 들어간다**(`0.00191511 = 1/400 × …`). 자기 상자 중심이 소실점이 된다.
- ②와 ③의 **높이는 같은데**(90.39) **폭이 다르다**(87.48 대 78.17).\
  이 상자는 부모 안에서 **가로로만 치우쳐 있어서** 그렇다 — 부모 원근의 소실점은 부모 중앙이고, 자기 원근의 소실점은 자기 중앙이다.
- ④는 원근이 두 번 걸려 가장 크게 왜곡된다. **실수로 둘 다 주면 이렇게 된다.**

```html demo
<div class="scene par"><b>부모에 perspective</b></div>
<div class="scene slf"><b>자기 perspective()</b></div>
<style>
  .scene { position: relative; width: 330px; height: 120px; margin: 8px;
           border: 1px solid #cbd5e1; }
  .par { perspective: 400px; }
  .scene b { position: absolute; left: 30px; top: 20px; width: 140px; height: 80px;
             background: #1d4ed8; color: #fff; font: 13px/80px system-ui; text-align: center; }
  .par b { transform: rotateY(50deg); }
  .slf b { transform: perspective(400px) rotateY(50deg); }
</style>
```

> **보이는 것** — 파란 상자 둘 다 오른쪽으로 좁아지는 **사다리꼴**이 된다(왼쪽 변이 길고 오른쪽 변이 짧다). 위(부모에 원근)가 **아래(자기 원근)보다 가로로 더 넓다** — 소실점이 부모 한가운데, 즉 상자보다 오른쪽에 있기 때문이다. 세로 높이는 둘이 같다.\
> **바꿔 볼 것** — `.par` 의 `perspective: 400px` → `150px`(훨씬 심하게 왜곡된다) · `.slf b` 의 `perspective(400px)` 를 빼기(**사다리꼴이 사라지고 그냥 좁은 직사각형**이 된다 — 원근이 없으면 3D 가 안 보인다) · `.par` 에 `perspective-origin: 0 50%` 추가(소실점이 왼쪽으로 가서 왜곡 방향이 뒤집힌다)

*(Chrome 151 headless 실측 — 상자의 `getBoundingClientRect()`(부모 기준):)*

```text
  .par b (부모에 perspective)   left=38.98  top=14.81   109.38 x 92.38
  .slf b (자기 perspective())   left=49.04  top=14.81    91.64 x 92.38
```

★ **이 demo 를 처음 쓸 때 실제로 함정에 걸렸다.** `.scene b` 에 `transform: rotateY(50deg)` 를 쓰고 `.self { transform: perspective(400px) … }` 로 덮으려 했는데, **`.scene b`(0,1,1) 가 `.self`(0,1,0) 보다 명시도가 높아** 그 선언이 통째로 무시됐다. 화면으로는 「둘이 비슷하다」로 보였고 **좌표를 재고서야** 잡혔다 — [52번](../52-transition/2-summary.md)에서 난 사고와 같은 유형이다.

비용 — `perspective` 는 **쌓임 맥락을 만든다**(정본 [22번](../22-stacking-context-and-z-index/2-summary.md)) 그리고 **`fixed` 자손의 포함 블록을 가로챈다**(정본 [21번](../21-position-and-containing-block/2-summary.md)).

### (3) `perspective-origin` — 관객이 어디에 앉았나

**언제 쓰나** — 왜곡 방향이 기대와 반대일 때.

```text
  perspective-origin: 50% 50%    0 0             100% 100%
      ·(부모 한가운데)          ·(왼쪽 위)                 ·(오른쪽 아래)
```

*(Chrome 151 실측 — 부모 `300×120`, 상자 `120×80` 에 `rotateY(50deg)`, `perspective: 300px`:)*

```text
  origin 선언     계산값            rect(부모 기준)        폭 x 높이
  (기본)          151px 61px        left=58.22 top=13.76   91.54 x  94.47
  0 0             0px 0px           left=85.54 top=18.21   44.16 x 101.06
  100% 100%       302px 122px       left=30.90 top= 2.73  138.92 x 101.06
```

- **소실점 위치 하나로 폭이 44 에서 139 까지 갈린다** — 세 배 넘게 차이가 난다.
- 계산값은 `transform-origin` 처럼 **길이 둘**로 정규화된다.
- `perspective-origin` 은 **`perspective` 를 준 요소(부모)에** 쓴다. 자식에 써 봐야 그 자식의 자손에게만 뜻이 있다.

### (4) ★ `transform-style: preserve-3d` — 손자가 평평해진다

**언제 쓰나** — 3D 로 짠 구조가 **중간 한 층에서** 무너질 때. 카드 뒤집기가 안 되는 이유의 대부분이다.

```text
  transform-style: flat (초기값)          transform-style: preserve-3d

  부모를 rotateY(45deg)                   부모를 rotateY(45deg)
       ↓                                       ↓
  자식들을 '부모 평면에' 그린다            자식들이 '3D 공간에' 그대로 선다
       ↓                                       ↓
  사진 한 장을 45도 돌린 것              손자의 rotateY(-45deg) 가
       ↓                                  부모의 회전을 되돌려 정면이 된다
  손자의 rotateY(-45deg) 는
  '납작한 사진 위에서' 돌 뿐이다
```

*(Chrome 151 실측 — 부모 `rotateY(45deg)`, 손자 `rotateY(-45deg)`, 부모에 `perspective: 400px`:)*

```text
  중간 요소의 선언                손자 rect
  (없음 = flat)                   left=84.71  47.61 x 68.24
  transform-style: preserve-3d    left=66.76  86.09 x 64.57   ← 정면을 되찾았다
```

- `preserve-3d` 쪽에서 손자 폭이 **86.09px**(원래 80px 에 원근이 더해진 값)로 **거의 정면**이 됐다.
- `flat` 쪽은 **47.61px** — 납작한 사진 위에서 한 번 더 돌았으니 더 좁아진다.

```html demo
<div class="scene"><div class="mid"><i></i></div></div>
<div class="scene"><div class="mid keep"><i></i></div></div>
<div class="scene"><div class="mid keep clip"><i></i></div></div>
<style>
  .scene { position: relative; width: 280px; height: 130px; margin: 8px;
           perspective: 400px; border: 1px solid #cbd5e1; }
  .mid { position: absolute; left: 40px; top: 20px; width: 200px; height: 90px;
         background: #e2e8f0; transform: rotateY(45deg); }
  .keep { transform-style: preserve-3d; }
  .clip { overflow: hidden; }
  .mid i { position: absolute; left: 20px; top: 15px; width: 80px; height: 60px;
           display: block; background: #16a34a; transform: rotateY(-45deg) translateZ(40px); }
</style>
```

> **보이는 것** — 회색 판 셋이 똑같이 오른쪽으로 좁아지는 사다리꼴로 기울어 있고, 그 위에 초록 상자가 하나씩 있다. **가운데 판의 초록만 넓고 정면을 향한다**(`preserve-3d`). 위와 **아래**의 초록은 회색 판에 눌려 **좁게 찌그러져** 있다 — 아래 판은 `preserve-3d` 를 선언했는데도 그렇다. `overflow: hidden` 한 줄이 그것을 깨뜨렸기 때문이다.\
> **바꿔 볼 것** — 셋째 줄의 `clip` 을 빼기(가운데와 똑같아진다) · `clip` 의 `overflow: hidden` → `opacity: .99`(**똑같이 깨진다**) · `overflow: hidden` → `contain: paint`(**안 깨진다** — 자르는데도 평탄화는 안 일어난다)

*(Chrome 151 headless 실측 — 손자의 `getBoundingClientRect()`(무대 기준)와 `transform-style` 계산값:)*

```text
  판 1 (선언 없음)              계산값 flat          손자 left=58.66  51.90 x 72.35
  판 2 (preserve-3d)            계산값 preserve-3d   손자 left=58.66  96.47 x 72.35
  판 3 (preserve-3d + overflow) 계산값 preserve-3d ★ 손자 left=58.66  51.90 x 72.35
                                                      ↑ 판 1 과 같은 값 = 평평해졌다
```

★ **판 3 의 계산값은 `preserve-3d` 인데 결과는 판 1 과 똑같다.** 계산값으로는 판정할 수 없다.

### (5) ★★ 무엇이 `preserve-3d` 를 깨뜨리나 — 던져서 만든 목록

**언제 쓰나** — 「분명 `preserve-3d` 를 줬는데 안 된다」를 만날 때.

명세는 평탄화를 일으키는 조건을 열거한다. **어느 선언이 거기 드는지는 던져 봐야** 안다.

*(Chrome 151 실측 — 중간 요소에 `transform-style: preserve-3d` 를 준 채 아래 선언을 하나씩 얹고, **손자의 rect 폭**으로 판정했다. 기준 96.47px · 평탄화되면 53.20px:)*

| 얹은 선언 | 계산된 `transform-style` | 손자 폭 | 판정 |
|---|---|---|---|
| (없음 — 기준) | `preserve-3d` | 96.47 | 3D 유지 |
| `overflow: hidden` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `overflow: auto` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `overflow: scroll` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `overflow: clip` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `overflow-x: hidden` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `overflow: visible` | `preserve-3d` | 96.47 | 3D 유지 |
| `opacity: 0.99` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `opacity: 1` | `preserve-3d` | 96.47 | 3D 유지 |
| `filter: blur(0px)` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `filter: opacity(1)` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `filter: none` | `preserve-3d` | 96.47 | 3D 유지 |
| `backdrop-filter: blur(0px)` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `clip-path: inset(0)` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `clip-path: none` | `preserve-3d` | 96.47 | 3D 유지 |
| `mask-image: linear-gradient(#000,#000)` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `mix-blend-mode: multiply` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `mix-blend-mode: normal` | `preserve-3d` | 96.47 | 3D 유지 |
| `isolation: isolate` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `will-change: opacity` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `will-change: filter` | `preserve-3d` | **53.20** | ★ 평탄화 |
| `will-change: transform` | `preserve-3d` | 96.47 | 3D 유지 |
| `contain: paint` / `layout` / `content` / `strict` / `size` | `preserve-3d` | 96.47 | 3D 유지 |
| `content-visibility: auto` | `preserve-3d` | 96.47 | 3D 유지 |
| `container-type: inline-size` / `size` | `preserve-3d` | 96.47 | 3D 유지 |
| `backface-visibility: hidden` | `preserve-3d` | 96.47 | 3D 유지 |
| `position: relative` / `fixed` · `z-index: 1` | `preserve-3d` | 96.47 | 3D 유지 |
| `border-radius` · `box-shadow` · `outline` · `text-shadow` · `background` | `preserve-3d` | 96.47 | 3D 유지 |

그림 해설 (한 단계씩):

- ★★ **`getComputedStyle().transformStyle` 은 34벌 전부에서 `preserve-3d` 를 돌려줬다.** 깨진 경우에도 그렇다.\
  **계산값은 「무엇이 선언됐나」를 말하지 「무엇이 일어나나」를 말하지 않는다** — 이 주제의 대표 사례다.
- **깨뜨리는 것들의 공통점**: 전부 **「안쪽을 한 장의 이미지로 합성해야 하는」 선언**이다.\
  `opacity`·`filter`·`mask`·`clip-path`·`mix-blend-mode`·`isolation`·`overflow` 가 그렇다 — [47번](../47-filter-and-backdrop-filter/2-summary.md)이 필터에서 같은 뿌리를 설명한다.
- ★ **`opacity: 1` 과 `opacity: 0.99` 가 갈린다.** [22번](../22-stacking-context-and-z-index/2-summary.md)의 쌓임 맥락과 **같은 경계**다.
- ★ **`will-change: transform` 은 안 깨뜨리는데 `will-change: opacity` 는 깨뜨린다.**\
  힌트를 준 속성이 평탄화를 일으키는 속성이면 **미리 그 효과가 적용된다**는 뜻이다.
- ★ **`contain: paint` 는 안 깨뜨린다.** 자르기는 하는데 평탄화는 안 일어났다 — `overflow: hidden` 과 **결과가 다르다.**
- `perspective: 500px` 을 얹으면 손자 폭이 **98.37px** 로 바뀌지만 **평탄화가 아니다** — 평탄화 값인 53.20 이 아니라 기준값 96.47 근처이고, 원근이 한 겹 더 걸린 것이다(높이도 72.35 → 83.78 로 같이 커졌다).

비용 — `preserve-3d` 를 쓰는 층에는 **위 목록의 선언을 하나도 못 쓴다.** 3D 구조가 깊어질수록 제약이 커진다.

### (6) `backface-visibility` — 카드 뒤집기

**언제 쓰나** — 앞면과 뒷면이 다른 카드를 만들 때.

```text
  구조

  .scene   perspective: 600px          ← 관객 자리
    .card  transform-style: preserve-3d ← 이게 없으면 뒤집기가 아예 안 된다
           :hover 시 rotateY(180deg)
      .f   backface-visibility: hidden                 ← 앞면
      .b   backface-visibility: hidden
           transform: rotateY(180deg)                  ← 뒷면 (미리 뒤집어 둔다)
```

```html demo
<div class="scene"><div class="card"><i class="f">앞</i><i class="b">뒤</i></div></div>
<style>
  .scene { width: 170px; height: 100px; margin: 10px; perspective: 600px; }
  .card { position: relative; width: 170px; height: 100px; transform-style: preserve-3d;
          transition: transform .8s ease; }
  .scene:hover .card { transform: rotateY(180deg); }
  .card i { position: absolute; inset: 0; display: block; backface-visibility: hidden;
            font: 15px/100px system-ui; text-align: center; color: #fff; }
  .f { background: #1d4ed8; }
  .b { background: #b91c1c; transform: rotateY(180deg); }
</style>
```

> **보이는 것** — 처음에는 「앞」이라고 쓰인 **파란 카드**가 보인다. 마우스를 올리면 0.8초에 걸쳐 세로축을 중심으로 돌아가고, 절반을 지나는 순간 **「뒤」라고 쓰인 빨간 카드**로 바뀐다. 도는 동안 **두 면이 동시에 보이는 순간은 없다.** 마우스를 떼면 같은 시간으로 되돌아온다.\
> **바꿔 볼 것** — `.card i` 의 `backface-visibility: hidden` 을 빼기(**뒷면이 좌우 반전된 채 앞면 위에 겹쳐 보인다**) · `.card` 의 `transform-style: preserve-3d` 를 빼기(**끝까지 파란 앞면만 보인다** — 아래 실측) · `perspective: 600px` → `200px`(도는 동안 훨씬 입체적으로 휜다)

*(Chrome 151 headless 실측 — 마우스를 올리기 전과 1.2초 뒤의 스크린샷 픽셀:)*

```text
  올리기 전     카드 자리의 색 = 파랑 (#1d4ed8) · transform: none
  1.2초 뒤      카드 자리의 색 = 빨강 (#b91c1c)
                transform = matrix3d(-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1)
```

*(같은 구조에서 `transform-style` 만 바꿔 정지 상태로 찍은 대조 실측 — 카드를 `rotateY(180deg)` 로 고정했다:)*

```text
  .card transform-style: preserve-3d   화면 색 = 빨강 (뒷면이 보인다)  ← 뒤집기가 된다
  .card transform-style: flat          화면 색 = 파랑 (앞면이 보인다)  ← 뒤집기가 안 된다
```

- **`flat` 이면 두 면이 카드 평면에 눌려 버려**, 카드 자체를 180도 돌려도 **`.b` 의 뒷면만 숨겨지고 `.f` 는 계속 앞을 향한다.**
- `backface-visibility` 는 **그 요소 자신의 뒷면**을 숨기는 속성이다. **부모가 `preserve-3d` 가 아니면 판정 기준 자체가 달라진다.**

### (7) z 축 정렬은 `z-index` 와 별개다

**언제 쓰나** — 3D 공간에서 `z-index` 로 앞뒤를 바꾸려 할 때.

*(Chrome 151 실측 — `perspective: 800px` 무대 안에서 빨강은 `translateZ(0)`, 파랑은 `translateZ(-100px)`. 둘이 겹치는 지점의 **스크린샷 픽셀**을 읽었다:)*

```text
  무대                                        겹친 자리 픽셀        누가 위인가
  ① preserve-3d, z-index 없음                 (220, 38, 38)        빨강 (z 가 앞)
  ② preserve-3d, 파랑에 z-index: 99           (220, 38, 38) ★      빨강 — z-index 가 졌다
  ③ transform-style: flat, 파랑에 z-index: 99 ( 37, 99, 235)       파랑 — z-index 가 이겼다
```

그림 해설 (한 단계씩):

- ★ **`preserve-3d` 안에서는 `z-index: 99` 가 z 위치를 못 이긴다.** 3D 공간에서는 **깊이가 순서를 정한다.**
- ③처럼 **평탄화되는 순간** 그 공간은 다시 평면이 되고, 거기서는 `z-index` 가 이긴다.
- 그래서 「`z-index` 가 안 먹는다」의 원인이 **조상의 `preserve-3d`** 일 수 있다. 쌓임 맥락 자체의 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md)이다.

## 형태 — 어디서 헷갈리나

### 세 속성이 각각 어디에 붙는가

```css
.scene {                 /* 관객 자리 — 3D 로 보여 줄 것들의 '부모'에 */
  perspective: 600px;
  perspective-origin: 50% 50%;   /* 초기값 */
}
.card {                  /* 입체를 유지할 '중간 층'에 */
  transform-style: preserve-3d;  /* 초기값은 flat */
  transform: rotateY(180deg);
}
.card > .face {          /* 뒷면을 숨길 '그 요소 자신'에 */
  backface-visibility: hidden;   /* 초기값은 visible */
}
```

### 3D 함수

```css
transform: rotateX(45deg);          /* 가로축 중심 — 앞으로 눕는다 */
transform: rotateY(45deg);          /* 세로축 중심 — 옆으로 돈다 */
transform: rotateZ(45deg);          /* = rotate(45deg), 2D 와 같다 */
transform: translateZ(80px);        /* 나에게 가까이 */
transform: translate3d(x, y, z);
transform: perspective(400px) rotateY(45deg);   /* 자기에게만 주는 원근 */
```

### 헷갈리는 자리 넷

```css
/* ① perspective 없이 3D 함수만 쓰면 — 그냥 납작해진다 */
.x { transform: rotateY(50deg); }

/* ② perspective() 는 '함수 목록의 맨 앞'에 와야 한다 */
transform: rotateY(45deg) perspective(400px);   /* 원근이 거의 안 걸린다 */
transform: perspective(400px) rotateY(45deg);   /* 이쪽 */

/* ③ preserve-3d 를 준 요소에 overflow/opacity/filter 를 같이 주면 깨진다 */
.card { transform-style: preserve-3d; overflow: hidden; }   /* 평탄화 */

/* ④ backface-visibility 는 부모가 아니라 '면' 에 준다 */
.card { backface-visibility: hidden; }    /* 카드 자체의 뒷면만 숨는다 */
.card > i { backface-visibility: hidden; }/* 각 면의 뒷면을 숨긴다 — 이쪽 */
```

## 어디서 틀리나

이 주제의 값어치가 여기 몰려 있다. **전부 에러도 경고도 없다.**

### 1. `perspective` 없이 3D 를 기대한다

`rotateY(50deg)` 만 주면 **그냥 가로로 좁아진다**(실측: 140px → 77.13px, 양 변이 평행).\
원근이 걸리면 사다리꼴이 된다(87.48px, 양 변이 안 평행).\
**어디에 줄지**는 (2) — 여러 요소를 한 공간에 놓으려면 **부모에** 준다.

### 2. `perspective()` 를 함수 목록 뒤에 쓴다

```css
transform: rotateY(45deg) perspective(400px);   /* 회전한 뒤에 원근이 걸린다 */
```

함수는 **왼쪽부터** 적용되므로([54번](../54-transform-2d-and-origin/2-summary.md)) 원근을 맨 앞에 둬야 한다.

### 3. `preserve-3d` 를 준 층에 `overflow: hidden` 을 같이 준다

(5)가 그것이다. **`overflow-x: hidden` 하나로도 깨진다.**\
★★ **계산값은 끝까지 `preserve-3d` 라고 답한다** — 자르기가 필요하면 `overflow` 를 바깥 층으로 옮기거나 `contain: paint` 를 쓴다(실측: `contain: paint` 는 안 깨뜨렸다).

### 4. `opacity` 로 페이드하면서 3D 를 유지하려 한다

`opacity: 0.99` 하나로 깨진다. **`opacity: 1` 은 안 깨뜨린다** — 경계가 「1 미만이냐」다([22번](../22-stacking-context-and-z-index/2-summary.md)의 쌓임 맥락과 같은 경계).\
페이드가 필요하면 **평탄화돼도 되는 층**에서 한다.

### 5. `will-change` 를 성능 힌트로만 본다

**`will-change: opacity` 가 3D 를 깨뜨린다**(실측). `will-change: transform` 은 안 깨뜨린다.\
「곧 바뀐다」고 알려 준 것뿐인데 **그 속성의 부작용이 미리 적용된다.**\
같은 성질을 [21번](../21-position-and-containing-block/2-summary.md)이 포함 블록에서, [22번](../22-stacking-context-and-z-index/2-summary.md)이 쌓임 맥락에서 실측해 뒀다.

### 6. 카드 뒤집기에서 `preserve-3d` 를 빠뜨린다

**끝까지 앞면만 보인다**(실측: `flat` 이면 화면 색이 계속 파랑).\
에러도 없고 회전은 일어나므로 「`backface-visibility` 가 이상한가」로 시간을 쓴다.

### 7. `backface-visibility` 를 부모에 준다

숨겨지는 것은 **그 요소 자신의 뒷면**이다. 각 면에 줘야 한다.\
부모(카드)에 주면 **카드 전체가 뒤돌았을 때 통째로 사라진다.**

### 8. 3D 공간에서 `z-index` 로 앞뒤를 바꾸려 한다

**안 바뀐다**((7) 실측: `z-index: 99` 가 `translateZ` 에 졌다).\
앞뒤를 바꾸려면 **`translateZ` 값을 바꾼다.**

### 9. 「계산값이 `preserve-3d` 니까 살아 있다」고 읽는다

이 주제에서 가장 나쁜 함정이다. 34벌 전부에서 계산값이 `preserve-3d` 였다.\
**판정은 손자의 `getBoundingClientRect()` 크기나 스크린샷 픽셀로** 한다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| `perspective` 가 **자손**에게 적용되고 `perspective()` 는 **자기**에게만 적용되는 것 | **명세**(css-transforms-2) |
| `transform-style` 의 초기값이 `flat` 인 것 | **명세** |
| `backface-visibility` 의 초기값이 `visible` 인 것 | **명세** |
| **평탄화를 일으키는 조건이 있다**는 것 자체 | **명세**(css-transforms-2 — grouping property 류가 평탄화를 강제한다) |
| **어느 선언이 그 목록에 드는지**(위 34벌 표) | ★ **이 브라우저에서 던져 본 결과다.** 명세의 열거와 한 줄씩 대조하지는 않았다 — `contain: paint` 와 `container-type` 이 특히 그렇다 |
| `getComputedStyle().transformStyle` 이 **평탄화돼도 `preserve-3d`** 를 주는 것 | ★ **관찰**. 계산값과 사용값이 갈리는 자리다 |
| 3D 공간에서 **`z-index` 가 z 위치를 못 이기는 것** | ★ **픽셀 관찰**. 명세의 3D 렌더링 맥락 정렬 규칙과 한 줄씩 대조하지는 않았다 |
| `perspective` 가 **쌓임 맥락·포함 블록**을 만드는 것 | **명세** — 실측 표는 [22번](../22-stacking-context-and-z-index/2-summary.md)·[21번](../21-position-and-containing-block/2-summary.md) |
| 좌표의 소수점(`96.47`·`53.20`) | ★ **한 판의 값**. 결론은 「기준값과 같냐 다르냐」에만 세웠다 |

★ **흔들리는 칸 / 안 흔들리는 칸**

```text
  안 흔들린다   깨졌나 안 깨졌나 (손자 폭이 기준값과 같은가)
                계산값이 언제나 preserve-3d 라는 것
                겹친 자리의 색 (빨강이냐 파랑이냐)
  흔들린다      좌표의 소수 둘째 자리 · matrix3d 성분의 자릿수
```

## 언제 쓰고 언제 안 쓰나

| 상황 | 3D 변환 | 다른 것 |
|---|---|---|
| 카드 뒤집기 | **쓴다**(`preserve-3d` + `backface-visibility`) | |
| 살짝 기울어진 입체 느낌 | **쓴다**(부모에 큰 `perspective`) | |
| 캐러셀·큐브 | **쓴다**(`translateZ` + `rotateY`) | 무겁다 — 항목 수를 제한한다 |
| 요소를 그냥 옮기고 돌리기 | 과하다 | 2D([54번](../54-transform-2d-and-origin/2-summary.md)) |
| 안쪽을 잘라야 하는 카드 | **못 쓴다**(`overflow` 가 평탄화한다) | `overflow` 를 바깥 층으로 · `contain: paint` |
| 페이드와 3D 를 같이 | **못 쓴다**(`opacity` 가 평탄화한다) | 층을 나눈다 |
| 깊이 순서를 `z-index` 로 제어 | **못 한다** | `translateZ` 값을 바꾼다 |

판단 규칙 두 줄.

- **3D 는 층 구조를 먼저 그린다** — 관객(`perspective`) / 입체를 유지할 층(`preserve-3d`) / 면(`backface-visibility`). 셋이 다른 요소다.
- **입체를 유지할 층에는 아무것도 더 얹지 않는다.** `overflow`·`opacity`·`filter`·`mask`·`isolation` 이 전부 깨뜨린다.

## 핵심 문장

- 3D 함수는 **`perspective` 가 없으면 그냥 납작해진다** — 함수는 먹었는데 입체가 안 보인다.
- **부모에 준 `perspective` 는 소실점이 하나**(부모 중앙)이고, **`perspective()` 는 요소마다 따로**다. 계산값으로는 ①과 ②가 구분되지 않는다.
- `perspective-origin` 하나로 같은 회전의 폭이 **44px 에서 139px 까지** 갈렸다(실측).
- **`transform-style: preserve-3d` 는 아주 쉽게 깨진다** — `overflow`(`visible` 아닌 전부) · `opacity` 1 미만 · `filter` · `backdrop-filter` · `clip-path` · `mask-image` · `mix-blend-mode` · `isolation` · `will-change: opacity|filter`.
- ★★ **깨져도 `getComputedStyle().transformStyle` 은 `preserve-3d` 를 돌려준다** — 판정은 좌표나 픽셀로 한다.
- **`contain: paint` 와 `will-change: transform` 은 안 깨뜨렸다**(실측) — `overflow: hidden`·`will-change: opacity` 와 갈린다.
- 카드 뒤집기는 **`preserve-3d` 가 없으면 앞면만 계속 보인다**(실측).
- **3D 공간에서는 `z-index` 가 z 위치를 못 이긴다** — 평탄화되는 순간 다시 `z-index` 가 이긴다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 55번) · 「버전·지원 기준」의 Baseline 표
- [54번 주제 — `transform` 2D](../54-transform-2d-and-origin/2-summary.md) — ★ **함수 순서·`transform-origin`·`%` 기준·인라인 제외·계산값 직렬화는 거기가 정본이다.** 여기는 **z 축이 생긴 뒤에 달라지는 것**만.
- [22번 주제 — 쌓임 맥락과 `z-index`](../22-stacking-context-and-z-index/2-summary.md) — ★ **쌓임 맥락의 정본.** 여기는 「3D 공간에서는 `z-index` 가 진다」는 한 자리만. `opacity: 1` 과 `0.99` 가 갈리는 경계도 거기가 정본이다.
- [21번 주제 — `position` 과 포함 블록](../21-position-and-containing-block/2-summary.md) — ★ **`perspective`·`will-change` 가 `fixed` 의 포함 블록을 가로채는 것의 정본.**
- [47번 주제 — `filter`·`backdrop-filter`](../47-filter-and-backdrop-filter/2-summary.md) — ★ **「보정을 걸려면 안쪽을 한 장으로 눌러야 한다」는 뿌리가 거기 있다.** 평탄화 목록이 필터·마스크·혼합으로 가득한 이유가 같은 뿌리다.
- [53번 주제 — `@keyframes` 와 `animation`](../53-keyframes-and-animation/2-summary.md) — 카드 뒤집기를 반복·왕복으로 만들 때
- [52번 주제 — `transition`](../52-transition/2-summary.md) — 이 문서의 카드 뒤집기 demo 가 쓰는 전환의 정본
- [56번 주제 — 렌더링 파이프라인](../56-rendering-pipeline-and-will-change/2-summary.md) — `will-change` 의 본래 목적과 비용
- [23번 주제 — `overflow` 와 스크롤 컨테이너](../23-overflow-and-scroll-containers/2-summary.md) — `overflow` 의 정본. 여기는 「그것이 3D 를 깨뜨린다」만.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **원근(perspective)** — 먼 것을 작게 보이게 하는 투영. 값은 **관객과 무대 사이 거리**이고, 작을수록 왜곡이 세다.
- **`perspective`(속성)** — **자손**에게 원근을 건다. 소실점이 그 요소 안에 하나 생긴다.
- **`perspective()`(함수)** — **자기 자신**에게만 원근을 건다. 함수 목록의 **맨 앞**에 와야 한다.
- **`perspective-origin`** — 소실점의 자리. 초기값 `50% 50%`, 계산값은 길이 둘.
- **`transform-style`** — `flat`(초기값) / `preserve-3d`. 자식들을 평면에 누를지, 3D 공간에 세울지.
- **평탄화(flattening)** — 자식의 3D 위치를 무시하고 부모 평면에 눌러 그리는 것. **여러 선언이 이것을 강제한다.**
- **`backface-visibility`** — `visible`(초기값) / `hidden`. **그 요소 자신의 뒷면**을 그릴지.
- **소실점(vanishing point)** — 원근 투영에서 모든 깊이 방향 선이 모이는 점. `perspective-origin` 이 정한다.
- **`matrix3d(…)`** — 3D 변환 행렬. 열여섯 수. 3D 함수를 하나라도 쓰면 계산값이 이 형태가 된다.
- **z 위치** — `translateZ` 로 정하는 깊이. 3D 공간에서는 **이것이 앞뒤를 정하고 `z-index` 는 진다.**

---

## 더 들어가면

- `perspective` 의 값으로 `none`(초기값)을 주면 **평행 투영**이 된다 — 원근 없는 3D 다.
- `rotate3d(x, y, z, angle)` 로 임의 축 회전을 쓸 수 있다. 개별 속성 `rotate` 도 `rotate: 1 1 0 45deg` 형태를 받는다([54번](../54-transform-2d-and-origin/2-summary.md)).
- `translateZ(N)` 은 **`perspective` 안에서만 크기 변화로 보인다.** 원근이 없으면 앞뒤 순서만 바뀌고 크기는 그대로다.
- 3D 로 짠 구조는 **합성 레이어를 많이 만든다.** 비용과 `will-change` 의 대가는 [56번](../56-rendering-pipeline-and-will-change/2-summary.md)에서 다룬다.
- 평탄화 목록을 외우는 대신 **한 문장으로 기억하는 편이 낫다** — 「**안쪽을 한 장의 이미지로 합성해야 하는 선언은 전부 3D 를 깨뜨린다**」. 실측 결과가 그 문장과 어긋난 것은 `contain: paint` 하나였다(자르는데도 안 깨뜨렸다).
- 모션이 큰 3D 연출은 전정기관에 민감한 사용자에게 특히 문제가 된다 — 정본은 [목록의 **60번 주제**](../60-prefers-reduced-motion/)다. 이 문서의 demo 에는 일부러 넣지 않았다.
