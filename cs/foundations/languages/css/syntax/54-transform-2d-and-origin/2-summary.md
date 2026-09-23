# css/syntax/54 — `transform` 2D·`transform-origin`·개별 변환 속성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Transforms Level 1](https://drafts.csswg.org/css-transforms-1/) (함수 목록·`transform-origin`·인라인 요소 제외·쌓임 맥락과 포함 블록) · [CSS Transforms Level 2](https://drafts.csswg.org/css-transforms-2/) (개별 변환 속성과 합성 순서). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 본문 실험 **9벌**을 **Google Chrome 151.0.7922.173** headless 에 CDP 로 붙여 돌렸다.\
> ★ 이 주제는 **계산값만으로는 아무것도 못 읽는다** — 계산값이 전부 `matrix(…)` 로 나오기 때문이다. 그래서 **`getBoundingClientRect()` 좌표**를 같이 재고, 필요하면 스크린샷 픽셀을 읽었다.\
> **엔진은 Chrome 하나다** — 크로스 브라우저는 Baseline 으로만 접지했다.
> **버전** — CSS 에 언어 버전은 없다. 2D transforms 는 Baseline **widely**(newly 2015-09-30 → widely 2018-03-30), 개별 변환 속성(`translate`/`rotate`/`scale`)은 **widely**(newly 2022-08-05 → widely 2025-02-05) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`transform` 은 「다 그려 놓은 그림을 오려서 옮겨 붙이는 것」이다.**

레이아웃은 이미 끝났다. 자리도 크기도 다 정해졌다.\
그 **결과물만** 옮기고 돌리고 늘인다 — **주변은 아무것도 모른다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 다 그려 놓은 그림 | 레이아웃이 끝난 박스 |
| 오려서 옮겨 붙인다 | `transform: translate(…)` |
| 돌려 붙인다 / 늘여 붙인다 | `rotate(…)` / `scale(…)` |
| **압정을 어디에 꽂고 돌리나** | `transform-origin` |
| 종이의 원래 자리는 비어 있지 않다 | **레이아웃은 안 바뀐다** — 형제는 제자리 |
| 붙이는 순서가 결과를 바꾼다 | **함수 목록은 순서가 뜻을 갖는다** |

- **옮겨 붙여도 주변은 안 움직인다.** 이것이 `transform` 이 싼 이유이자([56번](../56-rendering-pipeline-and-will-change/2-summary.md)) 실수의 근원이다.
- **순서가 결과를 바꾼다.** `translate` 후 `rotate` 와 그 반대는 **완전히 다른 자리**에 간다((2)).
- **계산값은 전부 `matrix(…)`** 로 뭉개진다 — 무슨 함수를 썼는지 되읽을 수 없다((8)).

```text
  transform 을 준 요소                주변에서 보는 그림

  +--------+                          +--------+
  |   B    |  ← 원래 자리(레이아웃)     | (비어  |   ← 자리는 그대로 잡혀 있다
  +--------+                          |  있지  |
       ↓ translateX(60) scale(1.5)    |  않다) |
     +-----------+                    +--------+
     |     B     |  ← 그려지는 자리     A [여기] C  ← 형제는 꿈쩍도 안 한다
     +-----------+
```

*(Chrome 151 실측 — 인라인 블록 셋 중 가운데에만 `translateX(60px) scale(1.5)` 를 줬다. 대조군은 변환 없음:)*

```text
             대조군                     가운데에 transform
  A   rect left=0    80x40           rect left=0    80x40
  B   rect left=80   80x40           rect left=120  120x60   ← 옮겨지고 커졌다
  C   rect left=160  80x40           rect left=160  80x40    ← 제자리 ★
```

★ **C 가 안 움직인다.** 그리고 B 자신의 `offsetLeft`·`offsetWidth` 는 **변환 전 값**(80·80)을 그대로 돌려준다 — 뒤에서 다시 본다((1)).

> **레이아웃(layout)** — 어느 상자가 어디에 얼마만 한 크기로 놓이는지 정하는 단계.\
> 예: 인라인 블록 셋이 가로로 `0, 80, 160` 에 놓이는 것을 정하는 일.

> **변환 행렬(matrix)** — 이동·회전·확대·기울임을 한 덩어리로 표현한 여섯 수.\
> 예: `matrix(1, 0, 0, 1, 30, 0)` 은 「가로로 30px 옮김」과 같다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `translateX(100px) rotate(45deg)` 와 `rotate(45deg) translateX(100px)` 는 **어디가 다르고 좌표로 얼마나 다른가.**
2. 개별 속성(`translate`/`rotate`/`scale`)을 `transform` 과 섞으면 **어떤 순서로 합쳐지는가** — 선언 순서를 따르는가.
3. `transform` 하나를 줬을 뿐인데 **딸려 오는 것들**은 무엇인가 — 무엇을 만들고 무엇을 안 만드는가.

## 동작 방식

### (1) 레이아웃은 그대로다 — 두 API 가 다른 답을 준다

**언제 쓰나** — 「변환했는데 왜 겹치지」·「스크롤바가 왜 안 생기지」를 볼 때.

```text
레이아웃 단계            변환 단계
  상자의 자리·크기 결정  →  그 결과를 옮겨 그린다
        |                        |
        v                        v
  offsetLeft / offsetWidth   getBoundingClientRect()
  = 변환 전 값               = 변환 후 값
```

*(Chrome 151 실측 — 가운데 요소에 `translateX(60px) scale(1.5)`:)*

```text
             rect (변환 후)            offset* (변환 전)
  B   left=120  top=50  120x60      offsetLeft=80  offsetTop=60  80x40
```

그림 해설 (한 단계씩):

- **`offsetWidth` 는 80, `getBoundingClientRect().width` 는 120** — 같은 요소에 두 답이 나온다.
- ★ 이것이 이 주제의 「계산값만 보면 안 되는」 자리다. **선언을 읽는 창과 결과를 재는 창을 늘 함께 둔다.**
- 문서 크기도 변환을 반영하지 않았다 — 변환으로 밖에 나간 부분 때문에 **스크롤바가 자동으로 생기지 않는다**(실측: 상자가 오른쪽으로 삐져나가도 `scrollWidth` 가 창 폭 그대로였다).

비용 — 레이아웃을 안 돌리므로 **싸다.** 얼마나 싼지는 [56번](../56-rendering-pipeline-and-will-change/2-summary.md)에 실측 표가 있다.

### (2) ★ 함수 순서가 결과를 바꾼다 — 좌표로 잰다

**언제 쓰나** — 「같은 함수를 썼는데 자리가 다르다」를 만날 때. **이 주제에서 가장 자주 나는 사고다.**

```text
translateX(100px) rotate(45deg)        rotate(45deg) translateX(100px)

  ① 먼저 오른쪽으로 100 민다             ① 먼저 제자리에서 45도 돈다
  ② 그 자리에서 45도 돈다                ② '돌아간 좌표계'에서 100 민다
                                          -> 오른쪽 아래 대각선으로 간다
```

*(Chrome 151 실측 — `left:100px; top:100px; 80x40` 상자 둘. 기준(변환 없음)은 중심 (140, 120):)*

```text
             rect.left  rect.top   폭x높이        중심
  기준       100.00     100.00     80.0 x 40.0    (140.00, 120.00)
  translate→rotate  197.57  77.57  84.85 x 84.85  (240.00, 120.00)
  rotate→translate  168.28 148.28  84.85 x 84.85  (210.71, 190.71)
```

그림 해설 (한 단계씩):

- **중심이 (240, 120) 대 (210.71, 190.71)** — 가로로 29.29px, **세로로 70.71px** 차이다. 같은 두 함수인데 완전히 다른 자리다.
- 70.71 은 `100 × sin45°` 다 — 회전한 좌표계에서 민 것이 아래로 내려간 만큼이다.
- **외접 상자 크기는 같다**(84.85 × 84.85). 크기만 보면 같아 보인다 — **좌표를 봐야 갈린다.**

```html demo
<div class="stage"><b class="tr">1</b><b class="rt">2</b></div>
<style>
  .stage { position: relative; width: 420px; height: 200px; background: #f1f5f9; }
  .stage b { position: absolute; left: 60px; top: 60px; width: 80px; height: 40px;
             color: #fff; font: 14px/40px system-ui; text-align: center; }
  .tr { background: #1d4ed8; transform: translateX(120px) rotate(45deg); }
  .rt { background: #b91c1c; transform: rotate(45deg) translateX(120px); }
</style>
```

> **보이는 것** — 같은 자리에서 출발한 두 상자가 **서로 다른 곳에 놓인다.** 파랑(`translate` → `rotate`)은 **오른쪽으로 곧게** 가서 45도 기울어 있고, 빨강(`rotate` → `translate`)은 **오른쪽 아래 대각선**으로 내려가 있다. 기울기는 둘 다 같다.\
> **바꿔 볼 것** — 둘 다 `rotate(45deg)` → `rotate(90deg)`(빨강이 더 아래로 내려간다) · `translateX(120px)` → `translateY(120px)`(이번엔 파랑이 아래로, 빨강이 왼쪽 아래로 간다)

*(Chrome 151 headless 실측 — 두 상자의 `getBoundingClientRect()`:)*

```text
  .tr (translate -> rotate)   left=177.6  top= 37.6   84.9 x 84.9
  .rt (rotate -> translate)   left=142.4  top=122.4   84.9 x 84.9
```

- **세로로 84.8px 차이**가 난다. 눈으로도 바로 보인다.

비용 — 없다. 다만 **순서를 바꿔도 화면이 비슷해 보이는 경우가 있어**(작은 각도·작은 이동) 좌표를 재지 않으면 못 잡는다.

### (3) `transform-origin` — 압정을 어디에 꽂나

**언제 쓰나** — 회전·확대가 「엉뚱한 데를 중심으로」 돌 때.

```text
기본값은 50% 50% — 상자 한가운데다.

  transform-origin: 50% 50%      0 0                right bottom
     +--------+                +--------+         +--------+
     |   ×    |                ×        |         |        |
     +--------+                +--------+         +-------×+
     가운데를 꽂고 돈다          왼쪽 위를 꽂고 돈다  오른쪽 아래를 꽂고 돈다
```

*(Chrome 151 실측 — `left:100 top:100` 의 `80×40` 상자에 `rotate(90deg)`:)*

```text
  origin 선언        계산값           rect.left  rect.top  폭x높이
  (기본)             40px 20px        120.0      80.0      40 x 80
  0 0                0px 0px           60.0     100.0      40 x 80
  right bottom       80px 40px        180.0      60.0      40 x 80
```

- **계산값은 언제나 길이 두 개**로 정규화된다 — `50% 50%` 는 `40px 20px`(상자가 80×40 이므로), `top right` 는 `200px 0px`(상자가 200×80 일 때).
- **폭·높이는 셋 다 같다**(40 × 80). 달라지는 것은 **어디에 놓이나**뿐이다.

```html demo
<div class="stage"><b class="c"></b><b class="tl"></b><b class="br"></b></div>
<style>
  .stage { position: relative; width: 420px; height: 190px; background: #f1f5f9; }
  .stage b { position: absolute; left: 140px; top: 70px; width: 120px; height: 40px;
             opacity: .6; transform: rotate(35deg); }
  .c  { background: #1d4ed8; }
  .tl { background: #b91c1c; transform-origin: left top; }
  .br { background: #16a34a; transform-origin: right bottom; }
</style>
```

> **보이는 것** — 똑같이 35도 기울어진 막대 셋이 **서로 다른 자리에** 놓여 부채처럼 어긋나 있다. 파랑(기본 = 가운데)이 가운데, 빨강(`left top`)이 **왼쪽 아래로**, 초록(`right bottom`)이 **오른쪽 위로** 밀려 있다. 기울기는 셋 다 같다.\
> **바꿔 볼 것** — `rotate(35deg)` → `scale(1.6)`(압정 자리에서 사방으로 커진다 — 빨강은 오른쪽 아래로만, 초록은 왼쪽 위로만 자란다) · `left top` → `50% 0`(위쪽 가운데)

*(Chrome 151 headless 실측 — 세 막대의 `getBoundingClientRect()`:)*

```text
  .c  (기본 = 50% 50%)   left=139.4  top= 39.2   121.2 x 101.6
  .tl (left top)         left=117.1  top= 70.0   121.2 x 101.6
  .br (right bottom)     left=161.7  top=  8.4   121.2 x 101.6
```

- **외접 상자 크기가 셋 다 같다**(121.2 × 101.6) — **좌표만 갈린다.**

### (4) ★ 개별 속성은 순서가 **고정**돼 있다

**언제 쓰나** — `translate`/`rotate`/`scale` 을 따로 쓸 때. 애니메이션에서 특히 쓸모 있다.

CSS Transforms Level 2 는 세 속성을 따로 둔다. 그리고 **합성 순서를 명세가 못 박는다.**

```text
  최종 변환 = translate  ×  rotate  ×  scale  ×  transform
                 ↑ 선언 순서와 무관하다 ★
```

*(Chrome 151 실측 — `left:100 top:100` 의 `80×40` 상자. 넷 다 같은 자리에 놓였다:)*

```text
  선언                                              rect.left  rect.top
  translate: 100px; rotate: 45deg;                  197.57     77.57
  rotate: 45deg; translate: 100px;    (순서 거꾸로) 197.57     77.57   ★ 같다
  translate: 100px; transform: rotate(45deg);       197.57     77.57   ★ 같다
  transform: translateX(100px) rotate(45deg);       197.57     77.57   ★ 같다
```

그림 해설 (한 단계씩):

- **선언 순서를 거꾸로 써도 결과가 같다.** 개별 속성은 CSS 의 다른 단축·롱핸드와 달리 **「쓴 순서」가 뜻을 갖지 않는다.**
- **개별 속성이 `transform` 보다 먼저** 적용된다 — 셋째 줄이 넷째 줄과 같다는 것이 그 증거다.

**`rotate` 와 `scale` 의 앞뒤도 확인했다** — 균등 확대는 회전과 교환되므로 **비균등 확대**로 갈랐다.

*(Chrome 151 실측 — `left:200 top:150` 의 `80×40` 상자:)*

```text
  rotate: 45deg; scale: 3 1;                 left=141.01  top= 71.01  197.99 x 197.99
  transform: rotate(45deg) scale(3, 1);      left=141.01  top= 71.01  197.99 x 197.99  ★ 같다
  transform: scale(3, 1) rotate(45deg);      left=112.72  top=127.57  254.56 x  84.85     다르다
```

- 개별 속성 조합은 **`rotate` 다음 `scale`** 과 같다. 명세의 순서가 그대로 관찰된다.

```html demo
<div class="stage"><b class="ind"></b><b class="fn"></b><b class="rev"></b></div>
<style>
  .stage { position: relative; width: 460px; height: 220px; background: #f1f5f9; }
  .stage b { position: absolute; left: 60px; top: 70px; width: 90px; height: 40px; }
  .ind { background: #1d4ed8; rotate: 40deg; translate: 130px; }
  .fn  { outline: 3px dashed #fff; outline-offset: -7px;
         transform: translateX(130px) rotate(40deg); }
  .rev { background: #16a34a; transform: rotate(40deg) translateX(130px); }
</style>
```

> **보이는 것** — 파란 막대 하나와 초록 막대 하나가 보인다. 파란 막대 **위에 흰 점선 테두리가 정확히 겹쳐** 있다 — 그 점선이 `transform: translateX(130px) rotate(40deg)` 를 준 세 번째 상자이고, **선언 순서를 거꾸로 쓴 개별 속성(`rotate` 먼저, `translate` 나중)과 한 픽셀도 안 어긋난다.** 초록은 함수 순서를 뒤집은 것이라 **왼쪽 아래**에 따로 떨어져 있다.\
> **바꿔 볼 것** — `.ind` 의 두 줄을 `translate: 130px; rotate: 40deg;` 로(**아무것도 안 바뀐다** — 순서가 뜻이 없다) · `.ind` 에 `transform: scale(1.4)` 를 더해 보기(개별 속성이 먼저 적용되고 그 뒤에 확대된다)

*(Chrome 151 headless 실측 — 세 상자의 `getBoundingClientRect()`:)*

```text
  .ind (rotate: 40deg; translate: 130px)          left=187.67  top= 45.75   94.66 x 88.49
  .fn  (transform: translateX(130px) rotate(40deg)) left=187.67  top= 45.75   94.66 x 88.49
  .rev (transform: rotate(40deg) translateX(130px)) left=157.26  top=129.32   94.66 x 88.49
```

- `.ind` 와 `.fn` 이 **소수점까지 같다.** 그리고 `.ind` 의 **`transform` 계산값은 `none`** 이다 — 개별 속성은 `transform` 에 합쳐져 보이지 않는다((8)).

비용 — 없다. 오히려 **애니메이션에서 싸다** — `translate` 만 키프레임에 넣으면 `rotate` 를 안 건드려도 된다. `transform` 한 덩어리로 쓰면 함수 목록 전체를 다시 적어야 한다.

### (5) `%` 는 자기 상자 기준이다

**언제 쓰나** — 「가운데 정렬」 관용구 `translate(-50%, -50%)` 를 쓸 때.

*(Chrome 151 실측 — `translateX(50%)` 를 준 `80px` 상자를 폭이 다른 부모 둘에 넣었다:)*

```text
  부모 폭    자기 폭    rect.left    계산값
  500px      80px       40.0         matrix(1, 0, 0, 1, 40, 0)
  200px      80px       40.0         matrix(1, 0, 0, 1, 40, 0)
```

- **부모 폭이 2.5배 달라도 결과가 같다.** 40px = **자기 폭 80px 의 50%** 다.
- 길이·백분율의 기준 전반은 [33번 주제](../33-length-units/2-summary.md)가 정본이다. 여기서는 **`transform` 의 `%` 가 참조 상자(기본은 자기 테두리 상자)를 본다**는 것만 짚는다.
- 그래서 `position: absolute; left: 50%; transform: translateX(-50%)` 가 **부모 기준 50% → 자기 기준 -50%** 로 정확히 상쇄되어 가운데 정렬이 된다.

```text
  left: 50%              transform: translateX(-50%)
  (부모 폭의 50%)   →     (자기 폭의 50%를 되돌린다)
       = 가운데 정렬
```

### (6) ★ 인라인 요소에는 안 먹는다 — 계산값은 멀쩡한데

**언제 쓰나** — `<span>` 에 `transform` 을 주고 「왜 안 움직이지」 할 때.

명세는 변환 대상을 「**변환 가능한 요소**」로 제한한다 — **비대체 인라인 상자는 거기 들지 않는다.**

*(Chrome 151 실측 — 같은 `translateX(60px) scale(2)` 를 넷에 줬다:)*

```text
  요소                    display        계산된 transform          rect
  span (변환 없음)        inline         none                      left=22.73  29.45 x 24.00
  span (변환 줌)          inline         matrix(2,0,0,2,60,0) ★    left=22.73  29.45 x 24.00  ← 같다
  span + inline-block     inline-block   matrix(2,0,0,2,60,0)      left=56.01 106.91 x 44.78  ← 먹었다
  img (대체 요소)         inline         matrix(2,0,0,2,60,0)      left=78.73  16.00 x 16.00  ← 먹었다 (8px -> 16px)
```

그림 해설 (한 단계씩):

- ★★ **계산값에는 `matrix(2,0,0,2,60,0)` 이 버젓이 들어 있는데 화면은 안 움직인다.**\
  진단 3창이 전부 정상인데 결과만 다른 **제4의 상태**다 — `getBoundingClientRect()` 로만 잡힌다.
- **`display: inline-block` 이나 `block` 으로 바꾸면 먹는다.** `display` 의 안/바깥 값은 [16번 주제](../16-display-inner-outer/2-summary.md)가 정본이다.
- **`<img>` 는 인라인인데도 먹는다** — 대체 요소(replaced element)라 변환 가능한 요소에 들기 때문이다(폭이 8px → 16px 로 커졌다).

> **대체 요소(replaced element)** — 내용을 CSS 가 아니라 외부 자원이 채우는 요소.\
> 예: `<img>`·`<video>`·`<canvas>`. 인라인이어도 자기 상자를 갖는다.

### (7) `transform` 에 딸려 오는 것 — 둘은 만들고 하나는 안 만든다

**언제 쓰나** — 「`transform` 하나 줬는데 `z-index` 가 이상해졌다」·「`fixed` 가 갇혔다」를 볼 때.

```text
  transform: translateZ(0) 하나를 주면

   ① 쌓임 맥락을 만든다          → 정본은 22번
   ② fixed·absolute 자손의        → 정본은 21번
      포함 블록을 가로챈다
   ③ BFC 는?                      → 만들지 않는다 (아래 실측)
```

- ①②는 **[22번](../22-stacking-context-and-z-index/2-summary.md)과 [21번](../21-position-and-containing-block/2-summary.md)이 정본**이다. 거기에 픽셀·좌표 실측 표가 있다 — 여기서 다시 쓰지 않는다.\
  ★ 두 목록은 **겹치지만 같지 않다**(`opacity` 가 갈리는 자리). 그 대조표도 21번에 있다.
- ③은 **던져서 확인했다.**

*(Chrome 151 실측 — 같은 상자 셋에 float 자식을 넣고 감싸는지 봤다. float 은 60px, 테두리 2px × 2:)*

```text
  상자에 준 선언              상자 높이     float 을 감쌌나
  (없음)                      24.0px        아니다
  transform: translateZ(0)    24.0px        ★ 아니다 — BFC 가 아니다
  display: flow-root          64.0px        감쌌다 (60 + 4)
```

- **`transform` 은 BFC 를 만들지 않는다.** 쌓임 맥락과 포함 블록은 만드는데 BFC 는 아니다 — **셋이 서로 다른 축**이다.
- BFC 의 정본은 [17번 주제](../17-block-formatting-context/2-summary.md)다.

> **BFC(블록 서식 맥락)** — float 을 감싸고 마진 상쇄를 끊는 독립된 레이아웃 영역.\
> 예: `display: flow-root` 가 만든다. 쌓임 맥락과는 **다른 것**이다.

비용 — 이 셋은 **부작용이지 목적이 아니다.** `transform` 을 성능 힌트로만 쓰면(`translateZ(0)`) 위 둘이 조용히 딸려 온다.

### (8) 계산값은 `matrix(…)` 하나로 뭉개진다

**언제 쓰나** — JS 로 「지금 몇 도 돌아 있나」를 알아내려 할 때.

*(Chrome 151 실측 — 함수별 계산값:)*

```text
  선언                                  계산값
  translateX(30px)                      matrix(1, 0, 0, 1, 30, 0)
  rotate(30deg)                         matrix(0.866025, 0.5, -0.5, 0.866025, 0, 0)
  scale(2, .5)                          matrix(2, 0, 0, 0.5, 0, 0)
  skewX(20deg)                          matrix(1, 0, 0.36397, 1, 0, 0)
  translateX(30px) rotate(30deg) scale(2, .5)
                                        matrix(1.73205, 1, -0.25, 0.433013, 30, 0)
```

```text
  matrix(a, b, c, d, e, f) 의 뜻

        | a  c  e |        a,d  가로·세로 배율 성분
        | b  d  f |        b,c  기울임·회전 성분
        | 0  0  1 |        e,f  이동량 (px)
```

- **함수 이름이 사라진다.** `rotate(30deg)` 였는지 `matrix(...)` 로 직접 썼는지 되읽을 수 없다.
- 개별 속성(`translate`/`rotate`/`scale`)은 **각자 자기 계산값을 따로 갖는다** — `getComputedStyle(el).rotate` 가 `"45deg"` 를 돌려준다. 그래서 JS 로 읽을 거면 개별 속성 쪽이 낫다.
- ★ **계산값이 있다고 화면에 먹은 것은 아니다**((6)의 인라인 요소). **계산값은 「무엇이 선언됐나」를 말하지 「무엇이 일어나나」를 말하지 않는다.**

## 형태 — 어디서 헷갈리나

### 함수 목록과 개별 속성 — 같은 일을 하는 두 길

```css
/* ① 함수 목록 — 순서가 뜻을 갖는다 */
transform: translateX(100px) rotate(45deg) scale(1.2);

/* ② 개별 속성 — 순서가 뜻을 갖지 않는다 (명세가 순서를 고정) */
translate: 100px;
rotate: 45deg;
scale: 1.2;

/* ③ 섞으면 — 개별 속성이 먼저, transform 이 나중 */
translate: 100px;
transform: rotate(45deg);        /* = transform: translateX(100px) rotate(45deg) */
```

### 자주 쓰는 함수

```css
transform: translate(40px, 10px);   /* 이동. 한 값만 쓰면 Y 는 0 */
transform: translateX(50%);         /* % 는 자기 상자 기준 */
transform: rotate(45deg);           /* 회전. deg·rad·turn */
transform: scale(2);                /* 균등 확대. scale(2, .5) 는 비균등 */
transform: skewX(20deg);            /* 기울임 */
transform: matrix(a, b, c, d, e, f);/* 직접 행렬 */
transform-origin: 50% 50%;          /* 초기값 */
```

### 헷갈리는 자리 넷

```css
/* ① 순서를 바꾸면 다른 자리에 간다 */
transform: translateX(100px) rotate(45deg);   /* 오른쪽으로 곧게 */
transform: rotate(45deg) translateX(100px);   /* 오른쪽 아래 대각선 */

/* ② % 는 부모가 아니라 자기 상자다 */
transform: translateX(-50%);

/* ③ 인라인에는 안 먹는다 — 에러도 경고도 없다 */
span { transform: rotate(10deg); }            /* display 를 바꿔야 한다 */

/* ④ 여러 번 선언하면 뒤엣것이 앞엣것을 통째로 덮는다 (누적되지 않는다) */
.a { transform: translateX(50px); }
.a { transform: rotate(10deg); }              /* translateX 는 사라진다 */
```

## 어디서 틀리나

이 주제의 값어치가 여기 몰려 있다. **넷 다 에러도 경고도 없다.**

### 1. 함수 순서를 아무렇게나 쓴다

(2)가 그것이다. 중심이 **세로로 70.71px** 어긋났다.\
관용구로 외울 것: **「멀리 보낸 다음 돌린다」와 「돌린 다음 멀리 보낸다」는 다른 그림이다.**\
시계 바늘·부채꼴을 만들 때는 **`rotate` 를 먼저** 쓰는 쪽이 맞다.

### 2. `transform` 을 두 번 선언하고 누적을 기대한다

```css
.a { transform: translateX(50px); }
.a:hover { transform: rotate(10deg); }   /* 호버하면 이동이 사라진다 */
```

- `transform` 은 **한 속성**이라 뒤엣것이 앞엣것을 통째로 덮는다.
- 처방 둘 — ① 호버 쪽에 `translateX(50px) rotate(10deg)` 를 전부 다시 적는다 · ② **개별 속성**으로 나눈다(`translate` 는 그대로 두고 `rotate` 만 바꾼다). ②가 훨씬 안전하다((4)).

### 3. 인라인 요소에 준다

(6)이 그것이다. **계산값에는 `matrix(…)` 가 들어 있는데 화면은 안 움직인다.**\
`getComputedStyle` 만 보면 「먹었네」로 오해한다 — `getBoundingClientRect()` 를 같이 재야 잡힌다.\
`display: inline-block` 으로 바꾸면 된다([16번](../16-display-inner-outer/2-summary.md)).

### 4. `%` 를 부모 기준으로 안다

`translateX(50%)` 는 **자기 폭의 50%** 다. 부모 폭을 2.5배로 바꿔도 값이 안 변한다(실측: 둘 다 40px).\
`left: 50%`(부모 기준)와 **기준이 다르다**는 것이 가운데 정렬 관용구의 핵심이다.

### 5. 성능 힌트로 `translateZ(0)` 을 뿌린다

**쌓임 맥락과 포함 블록이 딸려 온다**((7)).\
조상에 `transform` 하나가 생기면 **그 안의 `position: fixed` 자손이 그 조상 안에 갇힌다** — 정본은 [21번](../21-position-and-containing-block/2-summary.md), 거기에 실측 좌표가 있다.\
합성 레이어를 띄우려는 의도라면 [`will-change`](../56-rendering-pipeline-and-will-change/2-summary.md) 쪽이 뜻이 분명하다 — 다만 **그쪽도 같은 부작용을 갖는다.**

### 6. `transform` 이 BFC 도 만들 것이라 짐작한다

**안 만든다**((7) 실측: float 을 못 감쌌다).\
「쌓임 맥락 = BFC」로 뭉뚱그리면 여기서 틀린다. 셋은 서로 다른 축이다 — [17번](../17-block-formatting-context/2-summary.md)·[22번](../22-stacking-context-and-z-index/2-summary.md)·[21번](../21-position-and-containing-block/2-summary.md).

### 7. 변환한 요소가 밖으로 나가도 스크롤바가 생기길 기대한다

**레이아웃이 안 바뀌므로** 문서 크기도 안 바뀐다(실측: `scrollWidth` 가 창 폭 그대로).\
넘친 부분은 조상의 `overflow` 가 처리할 뿐이다([23번](../23-overflow-and-scroll-containers/2-summary.md)).

### 8. `getComputedStyle().transform` 으로 각도를 읽으려 한다

**`matrix(…)` 여섯 수로만 나온다**((8)). 각도를 되계산할 수는 있지만 **부호·주기가 모호해진다.**\
각도를 읽을 거면 **개별 속성**(`rotate`)을 쓴다 — 계산값이 `"45deg"` 로 그대로 나온다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| 함수 목록은 **왼쪽부터 차례로** 적용된다(순서가 뜻을 갖는다) | **명세**(css-transforms-1 — 변환 함수 합성) |
| 개별 속성의 합성 순서가 **`translate` → `rotate` → `scale` → `transform`** 인 것 | **명세**(css-transforms-2 — 개별 변환 속성) |
| `transform-origin` 의 초기값이 **`50% 50%`** 인 것 | **명세** |
| `transform` 의 `%` 가 **참조 상자(기본 테두리 상자)** 기준인 것 | **명세** |
| **비대체 인라인 상자에는 적용되지 않는 것** | **명세**(변환 가능한 요소의 정의) |
| `transform` 이 **쌓임 맥락**과 **`fixed`·`absolute` 포함 블록**을 만드는 것 | **명세** — 실측 표는 [22번](../22-stacking-context-and-z-index/2-summary.md)·[21번](../21-position-and-containing-block/2-summary.md) |
| **BFC 는 안 만드는 것** | ★ **이 브라우저의 관찰.** 명세가 「만들지 않는다」를 명시하는 자리는 확인하지 않았다 — 만드는 것들의 목록에 없을 뿐이다 |
| 계산값이 **`matrix(…)` 로 직렬화**되는 것 | ★ **직렬화 형식** — 관찰이다. 소수 자릿수(`0.866025`)는 더 그렇다 |
| `offsetWidth` 가 **변환 전** 값을 주는 것 | ★ **관찰**(CSSOM View 의 정의까지는 확인하지 않았다) |
| 좌표의 소수점(`197.57`·`84.85`) | ★ 삼각함수 결과다. **자릿수는 흔들릴 수 있다 — 결론은 「몇 px 차이냐」에 세운다** |

★ **흔들리는 칸 / 안 흔들리는 칸**

```text
  안 흔들린다   순서를 바꾸면 자리가 바뀐다 / 개별 속성은 선언 순서와 무관하다
                인라인에는 안 먹는다 / 형제가 안 움직인다 / BFC 를 안 만든다
  흔들린다      좌표의 소수 둘째 자리 · matrix 성분의 소수 자릿수
```

## 언제 쓰고 언제 안 쓰나

| 상황 | `transform` | 다른 것 |
|---|---|---|
| 움직이는 효과(이동·확대·회전) | **쓴다** — 가장 싸다([56번](../56-rendering-pipeline-and-will-change/2-summary.md)) | |
| 실제 배치를 바꿔야 한다(형제가 따라와야 한다) | **못 쓴다** | `margin`·flex·grid |
| 가운데 정렬 | **쓴다**(`left:50%` + `translateX(-50%)`) | `place-items: center`(레이아웃으로 되면 그쪽) |
| 애니메이션에서 회전과 이동을 **따로** 제어 | 함수 목록은 불편하다 | **개별 속성**(`translate`/`rotate`/`scale`) |
| JS 로 현재 각도를 읽어야 한다 | 계산값이 `matrix` 라 불편하다 | **개별 속성** |
| 인라인 텍스트 조각을 기울이기 | 그대로는 안 된다 | `display: inline-block` 먼저 |
| 3D·원근 | 여기까지가 2D | 3D 는 [55번](../55-3d-transforms/2-summary.md) |

판단 규칙 두 줄.

- **「보이는 것만 움직이면 되는가」를 먼저 묻는다.** 그렇다면 `transform` 이고, 형제가 따라와야 하면 레이아웃 속성이다.
- **애니메이션할 거면 개별 속성을 기본으로 쓴다** — 덮어쓰기 사고가 사라진다.

## 핵심 문장

- `transform` 은 **레이아웃이 끝난 결과를 옮겨 그리는 것**이다 — 형제는 안 움직이고 문서 크기도 안 바뀐다.
- **같은 요소에 두 API 가 다른 답을 준다** — `offsetWidth` 는 변환 전, `getBoundingClientRect()` 는 변환 후.
- **함수 목록은 왼쪽부터 적용되고 순서가 결과를 바꾼다** — `translate`→`rotate` 와 그 반대의 중심이 세로로 70.71px 어긋났다(실측).
- **개별 속성은 선언 순서와 무관하다** — 명세가 `translate` → `rotate` → `scale` → `transform` 으로 고정한다(실측: 소수점까지 같다).
- `transform-origin` 의 초기값은 **`50% 50%`** 이고, 계산값은 **언제나 길이 둘**로 정규화된다.
- **`%` 는 자기 상자 기준**이다 — 부모 폭을 바꿔도 값이 안 변한다.
- ★ **비대체 인라인 요소에는 안 먹는다.** 그런데 **계산값에는 `matrix(…)` 가 들어 있다** — 좌표로만 잡힌다.
- `transform` 은 **쌓임 맥락과 `fixed` 포함 블록은 만들고 BFC 는 안 만든다**(실측).
- **계산값은 `matrix(…)` 로 뭉개져 함수 이름이 사라진다** — 각도를 읽으려면 개별 속성을 쓴다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 54번) · 「버전·지원 기준」의 Baseline 표
- [21번 주제 — `position` 과 포함 블록](../21-position-and-containing-block/2-summary.md) — ★ **`transform` 이 `fixed` 의 포함 블록을 가로채는 것의 정본.** 거기에 여섯 선언의 실측 좌표표가 있다. **여기는 「그런 일이 생긴다」까지만.**
- [22번 주제 — 쌓임 맥락과 `z-index`](../22-stacking-context-and-z-index/2-summary.md) — ★ **`transform` 이 쌓임 맥락을 만드는 것의 정본.** 픽셀 실측표가 거기 있다. **두 목록의 대조표도 21번에 있다.**
- [17번 주제 — 블록 서식 맥락](../17-block-formatting-context/2-summary.md) — BFC 의 정본. **여기는 「`transform` 은 BFC 를 안 만든다」는 한 줄만.**
- [16번 주제 — `display` 의 안/바깥](../16-display-inner-outer/2-summary.md) — 인라인 상자가 무엇인지의 정본. **여기는 「인라인에는 변환이 안 먹는다」만.**
- [33번 주제 — 길이 단위](../33-length-units/2-summary.md) — ★ **`%` 가 무엇을 기준으로 재는지의 정본.** 여기는 **`transform` 의 `%` 가 자기 상자라는 한 자리**만.
- [23번 주제 — `overflow` 와 스크롤 컨테이너](../23-overflow-and-scroll-containers/2-summary.md) — 변환으로 삐져나간 것을 누가 자르나
- [53번 주제 — `@keyframes` 와 `animation`](../53-keyframes-and-animation/2-summary.md) — **그쪽은 「시간을 따라 어떻게 가나」, 여기는 「무엇이 어디로 가나」.**
- [55번 주제 — 3D 변환](../55-3d-transforms/2-summary.md) — `perspective`·`transform-style`·`backface-visibility`. **여기는 2D 까지.**
- [56번 주제 — 렌더링 파이프라인](../56-rendering-pipeline-and-will-change/2-summary.md) — ★ **「`transform` 이 왜 싼가」의 정본.** 실측 표가 거기 있다.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **`transform`** — 레이아웃이 끝난 상자를 옮기고 돌리고 늘이는 속성. 레이아웃은 안 바뀐다.
- **변환 함수(transform function)** — `translate`·`rotate`·`scale`·`skew`·`matrix` 등. 목록에 쓰면 **왼쪽부터** 적용된다.
- **개별 변환 속성(individual transform properties)** — `translate`·`rotate`·`scale`. 선언 순서와 무관하게 **명세가 정한 순서**로 합쳐진다.
- **`transform-origin`** — 변환의 기준점(압정 자리). 초기값 `50% 50%`. 계산값은 길이 둘.
- **변환 행렬(matrix)** — `matrix(a, b, c, d, e, f)`. `a`·`d` 는 배율, `b`·`c` 는 기울임·회전, `e`·`f` 는 이동량.
- **참조 상자(reference box)** — `%` 가 무엇을 기준으로 재는지 정하는 상자. 기본은 자기 **테두리 상자**.
- **변환 가능한 요소(transformable element)** — 변환이 적용되는 요소. **비대체 인라인 상자는 들지 않는다.**
- **대체 요소(replaced element)** — 내용을 외부 자원이 채우는 요소(`<img>` 등). 인라인이어도 변환이 먹는다.
- **쌓임 맥락(stacking context)** — 누가 위에 그려지나를 정하는 독립 영역. `transform` 이 만든다(정본 22번).
- **포함 블록(containing block)** — `absolute`·`fixed` 가 기준으로 삼는 상자. `transform` 이 가로챈다(정본 21번).
- **BFC(블록 서식 맥락)** — float 을 감싸고 마진 상쇄를 끊는 영역. **`transform` 은 안 만든다**(정본 17번).

---

## 더 들어가면

- **`transform-box`**(Baseline newly, 2024-04-16)는 `%` 와 `transform-origin` 이 보는 참조 상자를 바꾼다 — SVG 에서 특히 뜻이 있다. 이 문서에서는 **돌려 보지 않았다.**
- `rotate()` 의 각도 단위는 `deg` 말고 `rad`·`grad`·`turn` 도 된다(`0.125turn` = `45deg`).
- `scale(0)` 은 상자를 한 점으로 만들지만 **레이아웃 자리는 그대로**다 — 「숨기기」로 쓰면 그 자리에 구멍이 남는다.
- `matrix()` 로 직접 쓰면 **보간이 달라질 수 있다** — 두 `matrix` 사이는 행렬 분해 후 보간이고, 같은 함수 목록끼리는 함수별로 보간된다([52번](../52-transition/2-summary.md)의 「같은 함수 목록일 때」가 그 뜻이다).
- 3D 함수(`rotateY`·`translateZ`·`perspective()`)를 하나라도 쓰면 계산값이 **`matrix3d(…)` 열여섯 수**로 바뀐다 — [55번](../55-3d-transforms/2-summary.md)에서 다룬다.
- 이 문서의 모든 좌표는 `getBoundingClientRect()` 값이다. **변환된 요소의 rect 는 회전한 도형의 외접 상자**이지 도형 자체가 아니다 — 45도 돌린 `80×40` 상자의 rect 가 `84.85×84.85` 로 나오는 이유가 그것이다.
