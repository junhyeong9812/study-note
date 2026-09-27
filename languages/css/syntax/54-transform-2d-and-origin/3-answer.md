# css/syntax/54 — `transform` 2D·`transform-origin`·개별 변환 속성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 좌표는 Google Chrome 151.0.7922.173 headless 에서 실제로 측정한 것**이다.\
> ★ 이 주제는 계산값이 전부 `matrix(…)` 로 나와 **계산값만으로는 아무것도 못 읽는다** — 그래서 `getBoundingClientRect()` 좌표를 같이 쟀고, 필요하면 스크린샷 픽셀을 읽었다.\
> 규칙은 [CSS Transforms Level 1](https://drafts.csswg.org/css-transforms-1/) 과 [Level 2](https://drafts.csswg.org/css-transforms-2/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 형제는 따라 움직이는가

**출력** (Chrome 151 — 인라인 블록 셋, 가운데에만 변환)

```text
             대조군 (변환 없음)              가운데에 transform
  A   rect left=0    top=10  80x40      rect left=0    top=60  80x40
  B   rect left=80   top=10  80x40      rect left=120  top=50  120x60
  C   rect left=160  top=10  80x40      rect left=160  top=60  80x40   ★ 제자리

  변환한 B 의 두 API
     offsetLeft=80  offsetTop=60  offsetWidth=80  offsetHeight=40     <- 변환 전
     rect.left=120  rect.top=50   rect.width=120  rect.height=60      <- 변환 후

  문서 크기: scrollWidth=900 (창 폭 그대로) · scrollHeight=700
```

**세 번째 상자**

- **같다**(둘 다 160). 변환은 **레이아웃이 끝난 뒤** 그리기만 바꾸므로 형제가 알 수 없다.

**`offsetWidth` 대 `rect.width`**

- **80px 대 120px.** 같은 요소에 두 답이 나온다.

**왜 다른가**

```text
  스타일 → 레이아웃 → 페인트 → 합성
              ↑            ↑
       offsetWidth 가   rect 가 보는 자리
       보는 자리        (변환이 얹힌 뒤)
```

- 변환은 레이아웃 **다음** 단계의 일이다. `offset*` 은 레이아웃 결과를, `getBoundingClientRect()` 는 화면에 그려지는 자리를 답한다.
- 파이프라인 단계의 정본은 [56번](../56-rendering-pipeline-and-will-change/2-summary.md)이다.

**스크롤바**

- **안 생긴다.** 실측에서 상자가 삐져나가도 `scrollWidth` 가 창 폭 그대로였다.\
  넘친 부분은 조상의 `overflow` 가 처리할 뿐이다([23번](../23-overflow-and-scroll-containers/2-summary.md)).

### 2. 두 상자는 어디에 놓이는가

**출력** (Chrome 151 — `left:100 top:100` 의 `80×40` 상자)

```text
                      rect.left  rect.top   폭 x 높이       중심
  기준(변환 없음)      100.00     100.00     80.0 x 40.0     (140.00, 120.00)
  translateX → rotate  197.57      77.57     84.85 x 84.85   (240.00, 120.00)
  rotate → translateX  168.28     148.28     84.85 x 84.85   (210.71, 190.71)
```

**두 중심**

- **(240.00, 120.00)** 과 **(210.71, 190.71)**.

**세로 차이와 그 출처**

- **70.71px** 이다. `100 × sin45° = 70.71` — **회전한 좌표계에서 100px 을 민 것**이 아래로 내려간 만큼이다.

```text
  translateX → rotate                rotate → translateX

  ① 오른쪽으로 100                    ① 제자리에서 45도 회전
       □──────────→ □                     ↘ 좌표축이 같이 돌아간다
  ② 그 자리에서 회전                  ② 돌아간 x 축을 따라 100
       ◇                                     ↘ 오른쪽 아래로 간다
  세로 위치 그대로 (120)              세로가 70.71 내려감 (190.71)
```

**크기**

- **같다**(84.85 × 84.85). 회전 각도가 같으므로 외접 상자도 같다.

**크기만으로 구분 못 하는 이유**

- `getBoundingClientRect()` 는 **회전한 도형의 외접 상자**를 준다. 도형의 모양·크기는 회전 각도만으로 정해지고, **이동은 위치에만 들어간다.**
- 그래서 **좌표를 재야** 갈린다.

**시계 바늘 모양**

- **`rotate` 를 먼저** 쓴다. `rotate(Ndeg) translateY(-80px)` 처럼 하면 중심에서 각도별로 뻗어 나간다.

### 3. 압정을 옮기면

**출력** (Chrome 151 — `left:100 top:100` 의 `80×40` 상자에 `rotate(90deg)`)

```text
  origin 선언     계산값         rect.left  rect.top   폭 x 높이
  (안 적음)       40px 20px      120.0       80.0       40 x 80
  0 0             0px 0px         60.0      100.0       40 x 80
  right bottom    80px 40px      180.0       60.0       40 x 80
```

**안 적었을 때의 계산값**

- **`40px 20px`** 이다. 초기값은 `50% 50%` 이고, 상자가 80×40 이므로 길이로 정규화되면 40px·20px 이 된다.

**세 경우의 좌표**

- 위 표대로 `left` 가 **120 → 60 → 180**, `top` 이 **80 → 100 → 60** 으로 갈린다.

**크기**

- **셋 다 같다**(40 × 80). `transform-origin` 은 **어디에 놓이나만** 바꾼다.

**200×80 상자에 `top right`**

- **`200px 0px`** 로 나온다(실측). 가로는 오른쪽 끝(200px), 세로는 위쪽 끝(0px).

> **`transform-origin`** — 변환의 압정 자리. 키워드로 써도 **계산값은 언제나 길이 둘**로 정규화된다.

### 4. 선언 순서를 거꾸로 쓰면

**출력** (Chrome 151 — `left:100 top:100` 의 `80×40` 상자)

```text
  선언                                           rect.left  rect.top   계산값
  translate: 100px; rotate: 45deg;               197.57     77.57      transform="none"
  rotate: 45deg; translate: 100px;               197.57     77.57      transform="none"
  translate: 100px; transform: rotate(45deg);    197.57     77.57      transform="matrix(…, 0, 0)"
  transform: translateX(100px) rotate(45deg);    197.57     77.57      transform="matrix(…, 100, 0)"
```

**넷의 `left`**

- **넷 다 197.57px** 이다. 소수점까지 같다.

**`.p1` 과 `.p2` 가 같은 이유**

- 개별 속성은 **선언 순서가 뜻을 갖지 않는다.** 명세가 합성 순서를 미리 정해 두었기 때문이다.

**`.p3` = `.p4` 에서 알 수 있는 것**

- **개별 속성이 `transform` 보다 먼저** 적용된다. `translate: 100px` + `transform: rotate(45deg)` 가 `translateX(100px) rotate(45deg)` 와 같다는 뜻이다.

**`.p3` 의 계산값**

- **`matrix(0.707107, 0.707107, -0.707107, 0.707107, 0, 0)`** — `rotate(45deg)` 만 들어 있다.\
  ★ **이동 성분(`e`, `f`)이 0 이다.** `translate` 는 `transform` 계산값에 **안 섞인다** — 자기 속성에 따로 남는다(`getComputedStyle(el).translate === "100px"`).

**합성 순서**

```text
  최종 변환 = translate  ×  rotate  ×  scale  ×  transform
```

*(비균등 확대로 `rotate`/`scale` 의 앞뒤도 확인했다 — `rotate: 45deg; scale: 3 1` 이 `transform: rotate(45deg) scale(3,1)` 과 같은 `left=141.01 top=71.01 197.99×197.99` 였고, 순서를 뒤집은 `scale(3,1) rotate(45deg)` 는 `left=112.72 top=127.57 254.56×84.85` 로 달랐다.)*

### 5. `%` 는 무엇의 절반인가

**출력** (Chrome 151 — `translateX(50%)` 를 준 80px 상자)

```text
  부모 폭    자기 폭    rect.left    계산값
  500px      80px       40.0         matrix(1, 0, 0, 1, 40, 0)
  200px      80px       40.0         matrix(1, 0, 0, 1, 40, 0)
```

**두 상자**

- **같다. 둘 다 40px** 이다.

**무엇의 50% 인가**

- **자기 상자(기본은 테두리 상자)의 50%** 다. 80px 의 절반이 40px.

**가운데 정렬이 되는 이유**

```text
  left: 50%                    transform: translateX(-50%)
  = 부모 폭의 50% 만큼 오른쪽     = 자기 폭의 50% 만큼 왼쪽
        ↓                              ↓
  상자의 '왼쪽 모서리'가 가운데   상자의 '가운데'가 가운데
```

- **두 `50%` 의 기준이 다르다**는 것이 이 관용구의 전부다. 같은 기준이었으면 상쇄되지 않는다.

**정본**

- [33번 주제 — 길이 단위](../33-length-units/2-summary.md)다. 「이 수치가 무엇의 몇 %인가」의 정본이 거기다.

### 6. 왜 `<span>` 은 안 움직이는가

**출력** (Chrome 151 — 같은 `translateX(60px) scale(2)` 를 넷에)

```text
  요소                 display        계산된 transform        rect
  span (변환 없음)     inline         none                    left=22.73  29.45 x 24.00
  span (변환 줌)       inline         matrix(2,0,0,2,60,0)    left=22.73  29.45 x 24.00
  span + inline-block  inline-block   matrix(2,0,0,2,60,0)    left=56.01 106.91 x 44.78
  img (대체 요소)      inline         matrix(2,0,0,2,60,0)    left=78.73  16.00 x 16.00
```

**계산값**

- **`matrix(2, 0, 0, 2, 60, 0)`** — 멀쩡히 들어 있다.

**`getBoundingClientRect()`**

- **변환 없는 `<span>` 과 완전히 같다**(left 22.73 · 29.45 × 24.00). 아무 일도 안 일어났다.

**어디서 잡히나**

- ★★ **진단 3창 어디에서도 안 잡힌다.** 규칙도 담겼고 선택자도 잡혔고 계산값도 나온다.\
  틀린 것은 값이 아니라 「**이 요소가 변환 가능한 요소가 아니다**」라는 사실이다.\
  **`getBoundingClientRect()` 를 같이 재야** 보인다 — [계산값 단계 이후에서 갈리는 유형](../11-is-where-not/2-summary.md)과 같은 성격이다.

**`display: inline-block` 으로 바꾸면**

- **먹는다.** 폭이 29.45 → 106.91 로 커지고 위치도 옮겨졌다.

**`<img>` 가 움직이는 이유**

- **대체 요소**라서다. 명세의 「변환 가능한 요소」에는 비대체 인라인 상자만 빠져 있고, `<img>` 같은 대체 요소는 인라인이어도 들어간다.
- 실측에서 8px 짜리 이미지가 **16px** 로 커졌다 — `scale(2)` 가 먹은 것이다.

### 7. `transform` 하나에 딸려 오는 것

**만드는 것 둘**

- ① **쌓임 맥락** — 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md).
- ② **`fixed`·`absolute` 자손의 포함 블록** — 정본은 [21번](../21-position-and-containing-block/2-summary.md).

**`position: fixed` 자식이 있으면**

- **그 자식이 뷰포트가 아니라 `.wrap` 을 기준으로 놓인다.** 화면에 고정되지 않고 `.wrap` 안에 갇힌다.
- 정본은 [21번](../21-position-and-containing-block/2-summary.md) — 거기에 `transform`·`filter`·`will-change` 등 여섯 선언의 실측 좌표표가 있다.

**안 만드는 것**

- **BFC** 다.

**출력** (Chrome 151 — float 60px 자식, 테두리 2px × 2)

```text
  상자에 준 선언              상자 높이     float 을 감쌌나
  (없음)                      24.0px        아니다
  transform: translateZ(0)    24.0px        아니다  ★
  display: flow-root          64.0px        감쌌다 (60 + 4)
```

**float 자식이 있을 때 높이**

- **24.0px** — 감싸지 못한다. `flow-root` 와 비교하면 40px 차이가 난다.

**세 축이 다르다는 확인**

- 쌓임 맥락·포함 블록은 **21·22 에서 픽셀과 좌표로** 확인돼 있고, BFC 는 **이 문서에서 float 감싸기로** 확인했다.\
  같은 선언이 **둘은 만들고 하나는 안 만든다** — 그래서 셋을 한 덩어리로 외우면 안 된다.

### 8. 계산값에서 각도를 읽을 수 있는가

**출력** (Chrome 151)

```text
  translateX(30px)                              matrix(1, 0, 0, 1, 30, 0)
  rotate(30deg)                                 matrix(0.866025, 0.5, -0.5, 0.866025, 0, 0)
  scale(2, .5)                                  matrix(2, 0, 0, 0.5, 0, 0)
  skewX(20deg)                                  matrix(1, 0, 0.36397, 1, 0, 0)
  translateX(30px) rotate(30deg) scale(2, .5)   matrix(1.73205, 1, -0.25, 0.433013, 30, 0)
```

**여섯 수의 뜻**

```text
  matrix(a, b, c, d, e, f)

        | a  c  e |        a, d   가로·세로 배율 성분
        | b  d  f |        b, c   기울임·회전 성분
        | 0  0  1 |        e, f   이동량 (px)
```

**되읽을 수 있는가**

- **없다.** `matrix(1.73205, 1, -0.25, 0.433013, 30, 0)` 하나만 보고 「`rotate(30deg)` 뒤에 `scale(2, .5)` 를 썼다」를 복원할 수 없다.\
  같은 행렬을 만드는 함수 조합이 여럿이기 때문이다.

**각도를 읽으려면**

- **개별 속성**을 쓴다. `getComputedStyle(el).rotate` 가 `"30deg"` 를 그대로 돌려준다(실측: 개별 속성으로 준 요소의 `transform` 은 `"none"` 이고 `rotate` 가 값을 갖는다).

### 9. 이 호버는 왜 이동을 잃는가

**어디에 있나**

- **원래 자리에서 10도만 돌아 있다.** `translateX(50px)` 이 통째로 사라진다.

**누적되지 않는 이유**

- `transform` 은 **하나의 속성**이다. 같은 속성의 두 선언은 캐스케이드에서 **한쪽만 이긴다** — 값이 합쳐지는 일은 없다.

```text
  .a       { transform: translateX(50px); }      <- 진다
  .a:hover { transform: rotate(10deg); }         <- 이긴다 (명시도가 높다)
            결과: rotate(10deg) 만 남는다
```

**방법 둘**

```css
/* ① 호버 쪽에 전부 다시 적는다 */
.a:hover { transform: translateX(50px) rotate(10deg); }

/* ② 개별 속성으로 나눈다 — 서로 안 덮는다 */
.a       { translate: 50px; }
.a:hover { rotate: 10deg; }
```

- ②가 훨씬 안전하다. 이동을 어디서 줬는지 몰라도 회전만 바꿀 수 있다.

**애니메이션에서 특히 잦은 이유**

- 키프레임마다 `transform` 을 적는데, **한 키프레임에서 함수 하나를 빠뜨리면 그 구간에서 그 변환이 사라진다.**\
  개별 속성을 쓰면 키프레임이 건드리지 않은 축은 그대로 남는다([53번](../53-keyframes-and-animation/2-summary.md)).

### 10. 다른 주제와 잇기

**`left` 대 `transform`**

- **다시 도는 파이프라인 단계가 다르다.** `left` 는 매 프레임 스타일 재계산·레이아웃·페인트가 돌고, `transform` 은 주 스레드 카운터가 **0** 이다(실측).
- 정본은 [56번 주제](../56-rendering-pipeline-and-will-change/2-summary.md)다.

**회전과 이동을 따로 제어**

- **개별 속성**(`translate`·`rotate`·`scale`)이다. 명세가 합성 순서를 고정하므로 각자 따로 애니메이션해도 결과가 예측 가능하다.

**`scale(0)` 으로 숨기면**

- **레이아웃 자리는 그대로 남는다.** 화면에서는 사라지는데 그 자리에 구멍이 생기고, 형제는 안 채워 준다.
- 자리까지 없애려면 `display: none` 이나 레이아웃 속성을 건드려야 한다.

**3D 함수를 쓰면**

- 계산값이 **`matrix3d(…)` 열여섯 수**로 바뀐다. 2D 함수만 있으면 `matrix(…)` 여섯 수다.
- 정본은 [55번 주제](../55-3d-transforms/2-summary.md)다.

## 실행 검증

| 무엇을 | 어떻게 | 결과가 있는 곳 |
|---|---|---|
| `demo` 블록 3개 | Chrome 151 headless, `getBoundingClientRect()` + 스크린샷 | 서머리 (2)·(3)·(4) |
| 형제가 안 움직이는 것 | 대조군 포함 6요소의 rect + `offset*` 4값 | 서머리 (1) / 문항 1 |
| 함수 순서 | `left:100 top:100` 상자 3벌, 중심 좌표까지 계산 | 서머리 (2) / 문항 2 |
| `transform-origin` 세 값 | 같은 상자 3벌 + 별도로 계산값 4벌(`25% 75%`·`10px 20px`·`top right` 포함) | 서머리 (3) / 문항 3 |
| 개별 속성 합성 순서 | 4벌(선언 순서 뒤집기 포함) + 비균등 `scale` 로 `rotate`/`scale` 앞뒤 3벌 | 서머리 (4) / 문항 4 |
| `%` 의 기준 | 부모 폭 500px·200px 대조 | 서머리 (5) / 문항 5 |
| 인라인에 안 먹는 것 | 변환 없는 대조군 포함 4요소(`inline`·`inline-block`·`img`) | 서머리 (6) / 문항 6 |
| BFC 를 만드나 | float 자식으로 3벌(`flow-root` 대조군 포함) | 서머리 (7) / 문항 7 |
| 계산값 직렬화 | 함수 5벌의 `transform` 계산값 | 서머리 (8) / 문항 8 |

**구현 의존 항목** — 다시 찍어야 하는 것

- **`matrix(…)` 의 소수 자릿수**(`0.866025`·`0.36397`) — 직렬화 형식이다.
- **좌표의 소수 둘째 자리**(`197.57`·`84.85`) — 삼각함수 결과라 흔들릴 수 있다. **결론은 「몇 px 차이냐」에 세웠다.**
- **`transform` 이 BFC 를 안 만드는 것** — 이 브라우저의 관찰이다. 명세가 부재를 명시하는 자리는 확인하지 않았다.

**못 잰 것**

- `transform-box` 세 값 — **돌려 보지 않았다.**
- **크로스 브라우저** — 엔진이 Chrome 하나뿐이다. Baseline 데이터로만 접지했다.

## 용어 풀이

- **`transform`** — 레이아웃이 끝난 상자를 옮기고 돌리고 늘이는 속성. **형제는 안 움직인다.**
- **변환 함수** — `translate`·`rotate`·`scale`·`skew`·`matrix`. 목록에 쓰면 **왼쪽부터** 적용된다.
- **개별 변환 속성** — `translate`·`rotate`·`scale`. 선언 순서와 무관하게 **`translate` → `rotate` → `scale` → `transform`** 순서로 합쳐진다.
- **`transform-origin`** — 변환의 기준점. 초기값 `50% 50%`, 계산값은 길이 둘.
- **`matrix(a, b, c, d, e, f)`** — 2D 변환 행렬. `a`·`d` 배율, `b`·`c` 기울임·회전, `e`·`f` 이동.
- **참조 상자(reference box)** — `%` 와 `transform-origin` 이 보는 상자. 기본은 자기 테두리 상자.
- **변환 가능한 요소** — 변환이 적용되는 요소. **비대체 인라인 상자는 빠진다.**
- **대체 요소(replaced element)** — 내용을 외부 자원이 채우는 요소(`<img>` 등). 인라인이어도 변환이 먹는다.
- **외접 상자** — `getBoundingClientRect()` 가 돌려주는, 회전한 도형을 감싸는 축 정렬 사각형.
- **쌓임 맥락 / 포함 블록 / BFC** — `transform` 은 앞의 둘은 만들고 **BFC 는 안 만든다.** 서로 다른 축이다.
