# css/syntax/55 — 3D 변환: `perspective`·`transform-style`·`backface-visibility` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 수치는 Google Chrome 151.0.7922.173 headless 에서 실제로 측정한 것**이다.\
> ★ 평탄화 판정은 **계산값으로 할 수 없었다** — 깨진 경우에도 `getComputedStyle().transformStyle` 이 `preserve-3d` 를 돌려준다.\
> 그래서 **손자의 `getBoundingClientRect()` 크기**로 판정했고, 앞뒤 관계는 **스크린샷 픽셀**로 읽었다.\
> 규칙은 [CSS Transforms Level 2](https://drafts.csswg.org/css-transforms-2/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 원근이 없으면 무엇이 보이는가

**출력** (Chrome 151 — `120×80` 상자에 `rotateY(50deg)`, 원근 없음 (부모 `300×120`))

```text
  rect(부모 기준)  left=72.43  top=21.00   77.13 x 80.00
  계산값           matrix3d(0.642788, 0, -0.766044, 0,
                            0, 1, 0, 0,
                            0.766044, 0, 0.642788, 0,
                            0, 0, 0, 1)
```

**폭**

- **작아진다**(120 → 77.13). 원근이 없으면 `rotateY(θ)` 는 **가로만 `cos θ` 배**로 줄이는 것과 같다 — `120 × cos50° = 77.13` 이 정확히 실측값이다.

**사다리꼴인가**

- **아니다. 그냥 좁아진 직사각형이다.** 높이가 80.00 으로 **원래 그대로**인 것이 증거다 — 원근이 있으면 가까운 쪽이 커져서 높이도 커진다(실측: 90.39).

**계산값의 형태**

- **`matrix3d(…)` 열여섯 수.** 3D 함수를 하나라도 쓰면 이렇게 바뀐다.
- 마지막 줄이 `0, 0, 0, 1` 이다 — **원근 성분이 없다.**

**사다리꼴로 만들려면**

- **`perspective` 를 더한다.** 부모에 `perspective: 400px` 을 주거나, 함수 목록 맨 앞에 `perspective(400px)` 을 쓴다.

### 2. 부모에 주기 대 자기에게 주기

**출력** (Chrome 151 — `120×80` 상자, 부모 `300×120` 안에서 `left:50 top:20`)

```text
  경우                                   rect(부모 기준)          폭 x 높이
  ① 원근 없음                            left=72.43 top=21.00     77.13 x  80.00
  ② 부모 perspective: 400px              left=62.23 top=15.81     87.48 x  90.39
  ③ 자기 perspective(400px)              left=67.43 top=15.81     78.17 x  90.39
  ④ 둘 다                                left=54.96 top= 9.06     91.14 x 103.87

  계산값
  ① matrix3d(0.642788, 0, -0.766044, 0, 0, 1, 0, 0, 0.766044, 0, 0.642788, 0, 0, 0, 0, 1)
  ② ① 과 완전히 같다 ★
  ③ matrix3d(0.642788, 0, -0.766044, 0.00191511, 0, 1, 0, 0, 0.766044, 0, 0.642788, -0.00160697, 0, 0, 0, 1)
```

**두 상자의 폭**

- **다르다** — ② 87.48px, ③ 78.17px.

**높이**

- **같다**(둘 다 90.39px). 이 상자는 부모 안에서 **세로로는 거의 가운데** 있고 **가로로만 치우쳐** 있기 때문이다.
- 부모 원근의 소실점은 **부모 중앙**(151, 61), 자기 원근의 소실점은 **자기 중앙**(110, 60) 이다. **세로가 거의 같고 가로만 41px 어긋난다** — 그래서 가로만 갈렸다.

**`.par b` 의 계산값**

- **원근 없는 경우와 완전히 같다.** 원근이 **부모에** 있으므로 이 요소의 `transform` 에는 흔적이 없다.

**계산값만으로 판정할 수 있나**

- ★ **없다.** ①과 ②가 계산값이 같다. **좌표를 재야** 갈린다.
- 반대로 ③은 행렬 안에 원근 성분(`0.00191511`)이 들어 있어 계산값으로도 보인다 — **두 방법이 남기는 흔적이 다르다.**

**한 공간에 있는 것처럼**

- **부모에 준다.** 소실점이 하나라 카드 여러 장이 같은 무대에 선 것처럼 보인다.\
  `perspective()` 를 각자에게 주면 **각자 자기 중심이 소실점**이라 제각각 논다.

### 3. 소실점을 옮기면

**출력** (Chrome 151 — 부모 `300×120`, 상자 `120×80` 에 `rotateY(50deg)`, `perspective: 300px`)

```text
  origin 선언     계산값          rect(부모 기준)         폭 x 높이
  (안 적음)       151px 61px      left=58.22 top=13.76     91.54 x  94.47
  0 0             0px 0px         left=85.54 top=18.21     44.16 x 101.06
  100% 100%       302px 122px     left=30.90 top= 2.73    138.92 x 101.06
```

**안 적었을 때의 계산값**

- **`151px 61px`** — 초기값 `50% 50%` 가 부모 상자(테두리 포함 302×122) 기준 길이로 정규화된 값이다.

**`0 0` 과 `100% 100%`**

- 폭이 **44.16px** 와 **138.92px** 로 갈린다. `left` 도 85.54 대 30.90 으로 반대쪽이다.

**몇 배**

- **약 3.15배**(138.92 / 44.16). 같은 회전인데 소실점 하나로 이만큼 갈린다.

**어디에 쓰나**

- **`perspective` 를 준 요소(부모)에** 쓴다. 소실점은 원근을 건 공간의 성질이기 때문이다.

### 4. 손자는 정면을 볼 수 있는가

**출력** (Chrome 151 — 부모 `rotateY(45deg)`, 손자 `rotateY(-45deg)`, 무대에 `perspective: 400px`)

```text
  중간 요소의 선언                계산된 transform-style   손자 rect
  (없음 = flat)                   flat                     left=84.71  47.61 x 68.24
  transform-style: preserve-3d    preserve-3d              left=66.76  86.09 x 64.57
```

**안 줬을 때**

- **작다**(47.61px). 원래 80px 인데 절반 가까이 찌그러졌다.

**`preserve-3d` 일 때**

- **86.09px** — 원래 80px 보다 오히려 크다. 손자의 `rotateY(-45deg)` 가 부모의 회전을 **되돌려 정면을 향하고**, 거기에 원근이 더해져 살짝 커진 것이다.

**`flat` 일 때 손자의 회전은 무엇을 하나**

```text
  preserve-3d                       flat

  부모가 3D 공간에서 45도 돌고       부모의 자식들을 '부모 평면 위에' 먼저 그린다
  손자가 그 공간에서 -45도 돈다       -> 손자의 -45도는 '그 납작한 종이 위에서' 도는 것
  => 서로 상쇄돼 정면                 -> 상쇄되지 않고 한 번 더 좁아진다
```

**초기값**

- **`flat`** 이다. 그래서 「아무것도 안 하면 3D 구조가 한 층에서 끊긴다」가 기본 동작이다.

### 5. 무엇이 `preserve-3d` 를 깨뜨리는가

**출력** (Chrome 151 — 34벌을 던졌다. 기준 손자 폭 96.47px · 평탄화되면 53.20px)

```text
  ★ 평탄화됨
     overflow: hidden / auto / scroll / clip / overflow-x: hidden
     opacity: 0.99
     filter: blur(0px) / filter: opacity(1)
     backdrop-filter: blur(0px)
     clip-path: inset(0)
     mask-image: linear-gradient(#000,#000)
     mix-blend-mode: multiply
     isolation: isolate
     will-change: opacity / will-change: filter / will-change: opacity, transform

  3D 유지
     overflow: visible · opacity: 1 · filter: none · clip-path: none
     mix-blend-mode: normal
     will-change: transform / will-change: perspective
     contain: paint / layout / content / strict / size
     content-visibility: auto · container-type: inline-size / size
     backface-visibility: hidden · position: relative / fixed · z-index: 1
     border-radius · box-shadow · outline · text-shadow · background

  ※ perspective: 500px 은 98.37 x 83.78 — 평탄화(53.20)가 아니라 원근이 한 겹 더 걸린 것이다.
```

**`overflow` 셋**

- **셋 다 깨뜨린다.** `overflow-x: hidden` 처럼 **한 축만** 줘도 깨진다. `overflow: visible` 만 안 깨뜨린다.

**`opacity`**

- **`0.99` 가 깨뜨리고 `1` 은 안 깨뜨린다.** 경계가 「1 미만이냐」다 — [22번](../22-stacking-context-and-z-index/2-summary.md)의 쌓임 맥락과 **같은 경계**다.

**`will-change`**

- **`opacity` 가 깨뜨리고 `transform` 은 안 깨뜨린다.**
- 한 문장: 「**그 속성이 평탄화를 일으키는 속성이면, 힌트만 줘도 그 효과가 미리 적용된다.**」\
  `will-change: transform` 이 안 깨뜨리는 것은 `transform` 자체가 평탄화를 안 일으키기 때문이다.

**`contain: paint`**

- **안 깨뜨린다**(96.47px 그대로). 자르기는 하는데 평탄화는 안 일어났다 — `overflow: hidden` 과 **결과가 다르다.**\
  ★ 「자르면 깨진다」로 외우면 여기서 틀린다.

**공통점**

- 「**안쪽을 한 장의 이미지로 합성해야 하는 선언**」이다.\
  투명도를 섞으려면, 필터를 걸려면, 마스크를 씌우려면, 혼합하려면 **먼저 안쪽을 평평하게 눌러야** 한다.\
  [47번](../47-filter-and-backdrop-filter/2-summary.md)이 필터에서 같은 뿌리를 설명한다.
- 실측에서 이 문장과 어긋난 것은 **`contain: paint` 하나**다.

**계산값으로 판정할 수 있나**

- ★★ **없다. 34벌 전부에서 `preserve-3d` 가 나왔다.**\
  판정은 **손자의 rect 크기**(기준값과 같냐)나 **스크린샷 픽셀**로 한다.

### 6. 카드 뒤집기의 부품

**출력** (Chrome 151 — 카드를 `rotateY(180deg)` 로 고정하고 스크린샷 픽셀을 읽었다)

```text
  .card transform-style: preserve-3d   화면 색 = 빨강 (#b91c1c)  -> 뒷면이 보인다
  .card transform-style: flat          화면 색 = 파랑 (#1d4ed8)  -> 앞면이 계속 보인다
```

*(demo 쪽 실측 — hover 전 파랑, 1.2초 뒤 빨강, `transform = matrix3d(-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1)`.)*

**`preserve-3d` 를 빼면**

- **계속 파란 앞면만 보인다.** 회전은 일어나는데 뒤집힌 것처럼 안 보인다.
- `flat` 이면 두 면이 카드 평면에 **먼저 눌려** 버리고, 그 평면 안에서 `.b` 만 뒷면을 향해 숨겨진다.

**`backface-visibility: hidden` 을 빼면**

- **두 면이 동시에 보인다.** 뒷면 쪽 글자가 **좌우로 뒤집힌 채** 앞면 위에 겹쳐 보인다.

**어디에 주나**

- **각 면(`.card i`)에** 준다.
- 부모(`.card`)에 주면 **카드 전체가 180도 돌았을 때 카드째 사라진다.** 숨겨지는 것은 「그 요소 자신의 뒷면」이기 때문이다.

**뒷면에 미리 `rotateY(180deg)` 를 주는 이유**

```text
  뒷면에 회전을 안 주면            뒷면에 rotateY(180deg) 를 주면

  .b 가 앞을 향해 있다              .b 가 뒤를 향해 있다
  -> backface 가 숨기지 않는다       -> 평소에는 숨는다
  -> 앞면과 겹쳐 보인다              -> 카드가 180도 돌면 앞을 향해 보이게 된다
```

- 두 면을 **같은 자리에 등을 맞대고 붙여 두는 것**이 카드 뒤집기의 구조다.

### 7. `z-index` 로 앞뒤를 바꿀 수 있는가

**출력** (Chrome 151 — 겹친 자리의 스크린샷 픽셀)

```text
  무대                                          겹친 자리 (132, y)    색
  ① preserve-3d, z-index 없음                   (220, 38, 38)        빨강 (translateZ 0)
  ② preserve-3d, 파랑에 z-index: 99             (220, 38, 38)        빨강 ★
  ③ transform-style: flat, 파랑에 z-index: 99   ( 37, 99, 235)       파랑
```

**겹친 자리의 색**

- **빨강**(`translateZ(0)` 쪽). 파랑은 `translateZ(-100px)` 으로 뒤에 있다.

**`z-index: 99` 의 효과**

- **없다.** 3D 렌더링 맥락 안에서는 **깊이가 순서를 정한다.**

**`flat` 으로 바꾸면**

- **파랑이 이긴다.** 평탄화되는 순간 그 공간은 다시 평면이 되고, 평면에서는 `z-index` 가 순서를 정한다.

**앞뒤를 바꾸려면**

- **`translateZ` 값을 바꾼다.** `z-index` 로는 못 한다.
- 이 성질 때문에 **「`z-index` 가 안 먹는다」의 원인이 조상의 `preserve-3d`** 일 수 있다. 쌓임 맥락 자체의 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md)이다.

### 8. 이 함수 목록은 왜 원근이 안 걸리는가

**걸리는가**

- **제대로 안 걸린다.**

**왜**

- 함수 목록은 **왼쪽부터** 적용된다([54번 주제](../54-transform-2d-and-origin/2-summary.md)가 정본이고, 거기에 좌표 실측이 있다).
- `rotateY(45deg) perspective(400px)` 은 「먼저 45도 돌린 다음, **돌아간 좌표계에서** 원근을 건다」는 뜻이 된다 — 원근이 관객 방향이 아니라 엉뚱한 축으로 걸린다.

**올바른 순서**

```css
transform: perspective(400px) rotateY(45deg);   /* 원근을 맨 앞에 */
```

- 여러 요소에 줄 거면 아예 **부모의 `perspective` 속성**을 쓰는 편이 낫다(2번).

### 9. 계산값을 믿으면 왜 틀리는가

**평탄화된 요소의 계산값**

- **`preserve-3d`** 를 돌려준다. 34벌 전부 그랬다.

**무엇으로 판정하나**

- **손자의 `getBoundingClientRect()` 크기**(기준값과 같은가) 또는 **스크린샷 픽셀**.

**[54번](../54-transform-2d-and-origin/2-summary.md)의 같은 구조**

- **비대체 인라인 요소의 `transform`** 이다. 계산값에 `matrix(2,0,0,2,60,0)` 이 버젓이 들어 있는데 rect 는 변환 없는 것과 한 픽셀도 안 다르다.

**한 문장**

- ★ 「**계산값은 무엇이 선언됐나를 말하지, 무엇이 일어나나를 말하지 않는다.**」\
  선언을 읽는 창(`getComputedStyle`)과 결과를 재는 창(`getBoundingClientRect`·픽셀)을 **늘 함께** 둔다.

### 10. 다른 주제와 잇기

**`perspective` 의 부작용 둘**

- ① **쌓임 맥락을 만든다** — 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md).
- ② **`fixed`·`absolute` 자손의 포함 블록을 가로챈다** — 정본은 [21번](../21-position-and-containing-block/2-summary.md).

**평탄화 목록과 쌓임 맥락 목록**

- **많이 겹치지만 같지 않다.**

```text
  둘 다        opacity < 1 · filter · backdrop-filter · clip-path · mask
               mix-blend-mode · isolation · will-change(그 속성들)
  평탄화만     overflow (visible 아닌 전부)          <- 쌓임 맥락은 안 만든다
  쌓임 맥락만  position + z-index · contain: paint   <- 평탄화는 안 시킨다 (실측)
```

- 목록이 서로 다른 이유는 **목적이 다르기 때문**이다. 쌓임 맥락은 「누가 위에 그려지나」, 평탄화는 「안쪽을 한 장으로 눌러야 하나」다.

**안쪽을 잘라야 하는 3D 카드**

- `overflow` 를 **`preserve-3d` 층이 아닌 바깥 층**으로 옮긴다.
- 또는 **`contain: paint`** 를 쓴다 — 실측에서 자르면서도 평탄화를 안 일으켰다.

**모션 접근성**

- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(`prefers-reduced-motion`)다. 3D 회전은 전정기관에 특히 부담이 크다.

## 실행 검증

| 무엇을 | 어떻게 | 결과가 있는 곳 |
|---|---|---|
| `demo` 블록 3개 | Chrome 151 headless, rect + 스크린샷 픽셀, 카드는 CDP 로 실제 `:hover` | 서머리 (2)·(4)·(6) |
| 원근 없는 3D | rect + `matrix3d` 계산값 | 서머리 (2) / 문항 1 |
| 부모 원근 대 자기 원근 | 4벌(없음·부모·자기·둘 다), rect + 계산값 대조 | 서머리 (2) / 문항 2 |
| `perspective-origin` | 3벌(기본·`0 0`·`100% 100%`) | 서머리 (3) / 문항 3 |
| `preserve-3d` 손자 평탄화 | 2벌 + demo 3판 | 서머리 (4) / 문항 4 |
| **평탄화를 깨뜨리는 선언** | ★ **34벌**을 하나씩 얹고 손자 rect 로 판정 + 계산값 병기 | 서머리 (5) / 문항 5 |
| `backface-visibility` | 정지 2벌(`preserve-3d`/`flat`) 스크린샷 픽셀 + demo 의 hover 전후 | 서머리 (6) / 문항 6 |
| z 축 대 `z-index` | 3벌, 겹친 좌표의 스크린샷 픽셀 | 서머리 (7) / 문항 7 |

**구현 의존 항목** — 다시 찍어야 하는 것

- **평탄화 목록 34벌** — 이 브라우저에서 던져 본 결과다. 명세의 열거와 한 줄씩 대조하지는 않았다. **`contain: paint`·`container-type`·`content-visibility` 가 특히 다시 찍을 자리**다.
- **`getComputedStyle().transformStyle` 이 평탄화 후에도 `preserve-3d` 를 주는 것** — 관찰이다.
- **3D 공간에서 `z-index` 가 지는 것** — 픽셀 관찰이다.
- 좌표의 소수 둘째 자리 — **결론은 「기준값과 같냐 다르냐」에만 세웠다.**

**못 잰 것**

- **합성 레이어의 수와 메모리** — 이 환경에서 CDP `LayerTree` 도메인이 **빈 목록을 돌려준다**(`--disable-gpu` 유무 모두). [56번](../56-rendering-pipeline-and-will-change/2-summary.md)에 같은 한계가 적혀 있다.
- **크로스 브라우저** — 엔진이 Chrome 하나뿐이다. Baseline 데이터로만 접지했다.

## 용어 풀이

- **원근(perspective)** — 먼 것을 작게 보이게 하는 투영. 값은 관객과 무대 사이 거리이고 **작을수록 왜곡이 세다.**
- **`perspective`(속성)** — **자손**에게 원근을 건다. 소실점이 그 요소 안에 하나.
- **`perspective()`(함수)** — **자기 자신**에게만. 함수 목록 **맨 앞**에 와야 한다.
- **`perspective-origin`** — 소실점 자리. 초기값 `50% 50%`, 계산값은 길이 둘.
- **소실점(vanishing point)** — 깊이 방향 선들이 모이는 점.
- **`transform-style`** — `flat`(초기값) / `preserve-3d`.
- **평탄화(flattening)** — 자식의 3D 위치를 무시하고 부모 평면에 눌러 그리는 것. **여러 선언이 강제한다.**
- **`backface-visibility`** — `visible`(초기값) / `hidden`. **그 요소 자신의 뒷면**을 그릴지.
- **`matrix3d(…)`** — 3D 변환 행렬 열여섯 수. 원근이 걸리면 네 번째 열에 작은 수가 생긴다.
- **z 위치** — `translateZ` 가 정하는 깊이. 3D 공간에서는 **이것이 앞뒤를 정하고 `z-index` 는 진다.**
- **3D 렌더링 맥락** — `preserve-3d` 가 만든, 자손들이 같은 3D 공간을 공유하는 영역.
