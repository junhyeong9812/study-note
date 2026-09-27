# html/syntax/35 — 반응형 이미지: `srcset`/`sizes` 의 두 서술자(`w`·`x`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★★★ **명세의 「Images」 절(선택 규칙)은 이 배치의 사본에 없다** — 선택에 관한 명세층은 전부 **판정 보류**이고, 사본에 있는 것은 **렌더링 절의 `sizes=auto` 규칙**뿐이다. 「비교 열」은 명세가 아니다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤ 의 「받은 파일」이다** — 칸마다 새 탭 · 캐시 끔 · CDP 로 뷰포트·DPR.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 320 → `a400`/`a800` · 800 → `a400`/`a800` · 1400 → `a800`/`a1600`(dpr 1 / 2) · 비교 열과 갈린 칸 0 / 6 · 한 칸에 하나

**출력**

비교 열 파일 —

```javascript
// html33b-35-rule.js
// 비교 열 — 흔히 설명되는 「밀도가 dpr 이상인 후보 가운데 가장 작은 것 · 없으면 가장 큰 것」.
// ★ 명세가 아니다. 이 배치의 명세 사본에는 이미지 소스 선택 절이 없다 — 이 열은 「그 설명대로면」의 기준일 뿐이다.
function 비교열(후보, 슬롯, dpr) {
  const 됨 = 후보.filter(([, w]) => w / 슬롯 >= dpr);
  return (됨.length ? 됨[0] : 후보[후보.length - 1])[0];
}
```

```text
$ python3 html33b-run.py 격자 html33b-35-grid.html
뷰포트 · dpr    슬롯 폭  밀도(400w · 800w · 1600w)   서버가 받은 파일  currentSrc  naturalWidth  비교 열
320 · dpr 1     320      1.25 · 2.5 · 5              a400.png          a400.png    320           a400.png
320 · dpr 2     320      1.25 · 2.5 · 5              a800.png          a800.png    320           a800.png
800 · dpr 1     400      1 · 2 · 4                   a400.png          a400.png    400           a400.png
800 · dpr 2     400      1 · 2 · 4                   a800.png          a800.png    400           a800.png
1400 · dpr 1    700      0.57 · 1.14 · 2.29          a800.png          a800.png    699           a800.png
1400 · dpr 2    700      0.57 · 1.14 · 2.29          a1600.png         a1600.png   699           a1600.png
(밀도 = 후보 폭 ÷ 슬롯 폭 · 비교 열 = 밀도가 dpr 이상인 후보 가운데 가장 작은 것 — 명세가 아니다)
받은 파일의 가짓수 = 3
비교 열과 갈린 칸 = 0 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **슬롯** — 600 이하면 `100vw`(320), 넘으면 `50vw`(400 · 700). **밀도 = 파일 폭 ÷ 슬롯**이고, 이 판은 **밀도가 DPR 이상인 가장 작은 후보**를 받았다.
- ★★★ **받은 파일은 칸마다 하나** — `src` 를 따로 받지 않았다.
- ★★ **`naturalWidth`** — 파일 폭 ÷ 밀도 = **슬롯 폭**(320 · 400 · 699). 1400 칸의 **699** 는 `800 ÷ (800/700)` 의 소수 끝이 버려진 값으로 읽힌다(관찰).

### 2. `sizes` 없음 → `a1600`(100vw) · `100px` + CSS 800 → `a400` 을 800×400 으로 · `100px` 만 → `a400` 100×50 · `533px` → dpr 1 `a800` / dpr 2 `a1600` · 갈린 칸 0 / 8

**출력**

```text
$ python3 html33b-run.py 격자 html33b-35-sizes.html
[1000 · dpr 1]
  img                                 서버가 받은 파일    상자        naturalWidth  비교 열(슬롯 = sizes)
  n1 sizes 없음                       a1600.png           1000×500    1000          a1600.png (1000)
  n2 sizes=100px · CSS width:800px    a400.png            800×400     100           a400.png (100)
  n3 sizes=100px · CSS 폭 없음        a400.png            100×50      100           a400.png (100)
  n4 sizes=533px                      a800.png            533×266.5   533           a800.png (533)
[1000 · dpr 2]
  img                                 서버가 받은 파일    상자        naturalWidth  비교 열(슬롯 = sizes)
  n1 sizes 없음                       a1600.png           1000×500    1000          a1600.png (1000)
  n2 sizes=100px · CSS width:800px    a400.png            800×400     100           a400.png (100)
  n3 sizes=100px · CSS 폭 없음        a400.png            100×50      100           a400.png (100)
  n4 sizes=533px                      a1600.png           533×266.5   533           a1600.png (533)
비교 열과 갈린 칸 = 0 / 8
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`sizes` 없음 = 100vw** — `n1` 의 `naturalWidth` 1000.
- ★★★ **`sizes` 가 CSS 와 다르면 `sizes`** — `n2` 는 슬롯 100 으로 계산돼 `a400.png`(밀도 4)를 받고 **CSS 800px 로 늘렸다**(`naturalWidth` 100). DPR 2 에서도 같다.
- ★★ **CSS 폭이 없으면 슬롯 폭으로 그려진다** — `n3` 100×50 · `n4` 533×266.5.

### 3. `1x`/`2x` → dpr 1 `d200` · 2·3 `d400` · 상자 늘 200×100 / 섞은 둘은 콘솔 0 건으로 동작 / 한 후보에 `800w 2x` → 그 후보만 버려지고 콘솔 두 줄(두 번) · `currentSrc` 는 `a400.png`

**출력**

```text
$ python3 html33b-run.py 격자 html33b-35-x.html
img                               dpr 1 받은 파일 · 상자        dpr 2 받은 파일 · 상자        dpr 3 받은 파일 · 상자
x1 1x · 2x                        d200.png · 200×100            d400.png · 200×100            d400.png · 200×100
x2 400w · 2x (sizes=200px)        a400.png · 200×100            a400.png · 200×100            a400.png · 200×100
x3 1x · 800w (sizes=200px)        a400.png · 400×200            a800.png · 200×100            a800.png · 200×100
콘솔 기록(세 칸 합쳐 서로 다른 것) —
  0 건
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html33b-run.py 격자 html33b-35-drop.html
  서버    받음  i/a400.png?k=x4
  서버    풀어 줌
  서버    표지  끝
currentSrc = a400.png?k=x4
콘솔 기록 —
  Failed parsing 'srcset' attribute value since it has multiple 'x' descriptors or a mix of 'x' and 'w'/'h' descriptors.
  Dropped srcset candidate "i/a800.png?k=x4"
  Failed parsing 'srcset' attribute value since it has multiple 'x' descriptors or a mix of 'x' and 'w'/'h' descriptors.
  Dropped srcset candidate "i/a800.png?k=x4"
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`x` 는 DPR 로만** — `x1` 상자는 늘 200×100(밀도로 나눈 자연 폭).
- ★★★ **후보끼리 섞기는 동작했다** — `x3` 은 `1x`(밀도 1) 와 `800w`(800 ÷ 200 = 4) 가 한 목록에서 경쟁해 dpr 1 에 `a400`(상자 400×200), 2·3 에 `a800`(200×100). `x2` 는 두 후보가 **같은 밀도 2** 라 늘 `a400`.
- ★★★ **한 후보에 둘** — 「Failed parsing 'srcset' … a mix of 'x' and 'w'/'h' descriptors」 · 「Dropped srcset candidate "i/a800.png?k=x4"」. 남은 `a400.png 1x` 가 쓰였다.

### 4. 줄인 칸 — `a1600` 하나로 끝(다시 안 받음) · 늘린 칸 — `a400` 뒤에 `a1600` 을 새로(둘)

**출력**

```text
$ python3 html33b-run.py 격자 html33b-35-resize.html
[1400·dpr 2 → 320·dpr 1]
  서버    받음  i/a1600.png
  서버    풀어 줌
  서버    표지  처음 · 1400 · dpr 2 · currentSrc a1600.png
  서버    표지  바꾼 뒤 · 320 · dpr 1 · currentSrc a1600.png
  서버    표지  끝
  받은 이미지 수 = 1
[320·dpr 1 → 1400·dpr 2]
  서버    받음  i/a400.png
  서버    풀어 줌
  서버    표지  처음 · 320 · dpr 1 · currentSrc a400.png
  서버    받음  i/a1600.png
  서버    표지  바꾼 뒤 · 1400 · dpr 2 · currentSrc a1600.png
  서버    표지  끝
  받은 이미지 수 = 2
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **줄이면 유지 · 늘리면 다시** — 두 칸의 기다림은 같다(두 틀 × 2 + 새 그림의 `load`). 늘린 칸이 **그 기다림 안에 새 요청을 보였으니** 줄인 칸의 「안 받음」은 기다림 탓이 아니다.
- ★★ **명세층은 판정 보류**(A9).

### 5. `lazy`+`auto` → `a400` · `auto` 만 → `a1600` · `lazy`+`"auto, 100vw"` → `a400` · `lazy`+`auto`(폭 없음) → `a400` · 넷 다 `contain: size` · `300px 150px` · 상자 200×150 셋 · 300×150 하나

**출력**

```text
$ python3 html33b-run.py 격자 html33b-35-auto.html
img                                         받은 파일   상자      contain · contain-intrinsic-size
u1 lazy · sizes=auto · CSS 200px            a400.png    200×150   size · 300px 150px
u2 (eager) · sizes=auto · CSS 200px         a1600.png   200×150   size · 300px 150px
u3 lazy · sizes="auto, 100vw" · CSS 200px   a400.png    200×150   size · 300px 150px
u4 lazy · sizes=auto · CSS 폭 없음          a400.png    300×150   size · 300px 150px
(비교 — 슬롯 200 이면 a400.png · 슬롯 300 이면 a400.png · 슬롯 1400(100vw) 이면 a1600.png)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`auto` 는 `lazy` 와 함께일 때만 레이아웃 폭** — `u2`(eager)는 100vw 로 떨어져 `a1600.png`.
- ★★★ **`contain: size` · `contain-intrinsic-size: 300px 150px`** — 렌더링 절의 규칙 그대로(명세 판별 — 맞다). 폭이 없으면 **300×150**, 폭 200 이면 높이는 **150** 에 붙는다.

### 6. 요청이 레이아웃보다 먼저 나갈 수 있어서 — 그때는 CSS 폭을 모른다 · `sizes` 는 그 전에 주는 약속

- [34번](../34-img-alt-size-and-loading/2-summary.md) (2) — `eager` 그림은 **`DOMContentLoaded` 전에** 요청됐다. 그 시점에 레이아웃은 없다.
- 그래서 약속이 틀리면 **틀린 파일**을 받는다(A2 `n2`). `sizes=auto` 는 **`lazy` 로 요청을 레이아웃 뒤로 미룰 때만** 그 약속을 레이아웃에 맡긴다(A5).

### 7. `x` — 크기 고정(로고·아이콘) · `w` + `sizes` — 폭이 바뀌는 그림 / 후보끼리 섞기 — 각자 밀도로 바뀌어 경쟁(동작) · 한 후보에 둘 — 그 후보만 버려짐

- A3 이 둘 다의 근거다. 명세가 섞기를 작성자에게 금지하는지는 **사본이 없어 판정 보류.**

### 8. 밀도로 나눈 자연 폭 — 받은 파일 폭 ÷ 밀도(= 대개 슬롯 폭) · 속성이 없으면 **그 폭으로 그려진다**

- A1 — `a800.png` 이 400(800 칸) · 699(1400 칸). A2 — `a400.png` 이 100(`sizes="100px"`).
- `width`/`height` 속성·CSS 폭이 없으면 그림은 **그 자연 폭으로** 놓인다(A2 `n3`).

### 9. 줄이면 그대로 · 늘리면 다시 받음 / 적을 수 없다 — 선택 절이 사본에 없다

- 이 판이 말할 수 있는 것은 「**이 판의 Chrome 이 그렇게 했다**」까지다. 「UA 재량이다」도 이 배치가 **문장으로 확인한 말이 아니다.**

### 10. `sizes` 기본값 — 명세(판정 보류) · 이 판 100vw / `contain: size` — 명세(판별 — 맞다) / 줄인 뒤 — 구현 / 섞은 목록 — 구현(적합성은 판정 보류) / 같은 밀도 — 관찰

- 이 배치가 **판정할 수 있는 것은 `sizes=auto` 의 렌더링 규칙 하나**다 — 사본에 있는 유일한 문장이다.

### 11. 정본 경계

- **자리 예약 · 지연 로딩** — [34번](../34-img-alt-size-and-loading/2-summary.md).
- **좁은 화면에 다른 자르기 · 포맷 대체** — [36번 주제](../36-picture-art-direction-and-format/2-summary.md)(`picture`).
- **`video` 의 `source` 고르기** — 목록의 **37번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 칸마다 **새 탭 · `Network.setCacheDisabled(true)` · `Emulation.setDeviceMetricsOverride`(폭 · 높이 800 · DPR · `mobile: false`)**. **엔진은 이것 하나다.** 하네스는 [33번](../33-output-progress-meter/3-answer.md)의 `html33b-run.py` 다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

★ **창을 바꾸는 칸** — `뒤단계` 의 `["크기", 폭, 높이, dpr]` 로 **`load` 뒤에** 같은 탭의 뷰포트를 다시 건다. 페이지는 두 틀 × 2 를 넘기고, 그사이 그림이 **다시 오고 있으면** 그 `load` 까지 기다린 뒤 표지를 보낸다. 「뒤늦게 온 요청 = 0」이 끝 표지 뒤의 요청 수다.\
★ **파일 이름** — 크기만 적었다(`a400` = 폭 400). 파일은 캡처가 매번 새로 만든다(34번의 「예시 데이터」).

**흔들림 확인** — 캡처 세 판의 재대조는 [33번](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **여섯 칸** | 3 | 동작 방식 (1) · A1 |
| **`sizes` 넷 × 두 칸** | 3 | 동작 방식 (2) · A2 |
| **`x`·섞기 9 칸 · 한 후보에 둘** | 3 | 동작 방식 (3) · A3 |
| **창을 바꾼 두 방향** | 3 | 동작 방식 (4) · A4 |
| **`sizes=auto` 넷** | 3 | 동작 방식 (5) · A5 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 후보를 고르는 기준 | 밀도 ≥ DPR 인 가장 작은 것(14 칸) | 명세 절이 사본에 없다 · 네트워크 조건을 안 바꿨다 |
| 창을 줄인 뒤 | 다시 안 받는다 | 구현의 선택 |
| 한 후보의 서술자 둘 | 버리고 콘솔 두 줄(두 번) | 콘솔 문구는 판에 매인다 |

**안 돌려 본 것** — ① **`h` 서술자.** ② **네트워크 절약 모드·느린 연결.** ③ **`sizes` 의 미디어 조건을 여러 개 겹친 목록.**

**못 잰 것** — ① **그 선택이 명세가 허용하는 범위인가**(사본 없음). ② **흐리게 보이나**(픽셀).

**부적용인 창** — **창 ① · ③ · ④ · ⑥ · ⑦**.

## 용어 풀이

- **비교 열** — 「밀도 ≥ DPR 인 가장 작은 후보」를 옮긴 기준선. 명세가 아니다.
- **슬롯 폭** — `sizes` 가 알려 준 자리의 폭.
- **밀도** — 파일 폭 ÷ 슬롯 폭(`w`) 또는 적힌 값(`x`).
