# css/syntax/39 — 사용자 선호와 다크 모드: `prefers-color-scheme`·`color-scheme` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 읽거나 스크린샷 픽셀을 표본한 것**이다.\
> **선호를 바꾼 수단은 `--blink-settings=preferredColorScheme=0`(dark) / `=1`(light)** 이다 — 다른 플래그는 안 먹었다(A5).\
> 규칙은 [CSS Color Adjustment 1](https://drafts.csswg.org/css-color-adjust-1/) · [Media Queries 5](https://drafts.csswg.org/mediaqueries-5/) · [CSS Color 5](https://drafts.csswg.org/css-color-5/) 로 접지했다.\
> **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 선호만 바꾸면 화면이 바뀌는가

**출력** (Chrome 151 headless · `--blink-settings=preferredColorScheme=0`)

```text
matchMedia("(prefers-color-scheme: dark)").matches = true
스크린샷 픽셀 (280,110) = (255, 255, 255)          ★ 바탕은 그대로 하얗다
```

**페이지 바탕**

- **흰색**(`(255, 255, 255)`). 선호를 바꿔도 **아무것도 안 바뀐다.**

**`matches`**

- **`true`** 다. 선호는 분명히 바뀌었다.

**둘이 갈리는 이유**

- **미디어 쿼리는 조건일 뿐 아무것도 그리지 않는다.** 내가 그 안에 선언을 쓰지 않으면 화면은 그대로다.\
  「선호를 읽는 것」과 「브라우저가 그리는 것을 바꾸는 것」은 **다른 기계**이고, 뒤엣것은 `color-scheme` 이다.

### 2. `color-scheme` 이 바꾸는 것

**출력** (Chrome 151 headless)

```text
  항목                  color-scheme: light     color-scheme: dark
  -------------------   ---------------------   ---------------------
  input background      rgb(255, 255, 255)      rgb(59, 59, 59)
  input color           rgb(0, 0, 0)            rgb(255, 255, 255)
  input border-top      rgb(118, 118, 118)      rgb(133, 133, 133)
  button background     rgb(239, 239, 239)      rgb(107, 107, 107)
  button color          rgb(0, 0, 0)            rgb(255, 255, 255)
```

**두 `<input>`**

- light 쪽 **`rgb(255, 255, 255)`** · dark 쪽 **`rgb(59, 59, 59)`**.

**두 `<button>`**

- light 쪽 **`rgb(239, 239, 239)`** · dark 쪽 **`rgb(107, 107, 107)`**.

**색 선언의 개수**

- **0개.** 이 블록에는 `color` 도 `background` 도 한 글자도 없다.\
  바뀐 것은 전부 **UA 가 그리는 부분**이다.

**`:root` 에 걸면**

```text
실측 — :root { color-scheme: X } 만 다른 문서 세 장의 스크린샷 픽셀

  색 구성표    페이지 바탕     스크롤바 트랙    스크롤바 막대
  normal       (255,255,255)   (252,252,252)    (139,139,139)
  light        (255,255,255)   (252,252,252)    (139,139,139)
  dark         (18,18,18)      (44,44,44)       (159,159,159)
```

- **페이지 바탕(canvas)과 스크롤바**가 추가로 바뀐다.
- 시스템 색도 같이 뒤집힌다 — `Canvas` 가 `rgb(255,255,255)` → `rgb(18,18,18)`, `CanvasText` 가 `rgb(0,0,0)` → `rgb(255,255,255)`.

### 3. 서브트리에만 걸었을 때 안 바뀌는 것

**출력** (Chrome 151 headless)

```text
.c  color-scheme      = dark
.c  background-color  = rgba(0, 0, 0, 0)       투명 그대로
.cp color             = rgb(0, 0, 0)           ★ 검정 그대로
```

**`<p>` 의 `color`**

- **`rgb(0, 0, 0)`** — 안 바뀐다.

**`.dark` 의 `background-color`**

- **`rgba(0, 0, 0, 0)`** — 투명 그대로다. `color-scheme` 은 **내 배경을 안 칠한다.**

**어중간한 상태**

```text
   흰 페이지 바탕
   +-------------------------------------------+
   |  검정 글자 (안 바뀜)                        |
   |  +--------------------+                    |
   |  | 어두운 입력칸      |  <- 여기만 바뀌었다 |
   |  +--------------------+                    |
   +-------------------------------------------+
   => "폼만 다크" 인 상태. 눈에는 고장처럼 보인다
```

**왜 `color` 는 안 따라오나**

- `color` 는 **루트에서 이미 상속돼 내려온 값**이다. 서브트리에서 `color-scheme` 을 바꿔도 **이미 정해진 상속값을 되돌리지 않는다.**
- `color-scheme` 이 바꾸는 것은 **① UA 가 그리는 것**과 **② 그 서브트리에서 새로 계산되는 시스템 색·`light-dark()`** 뿐이다.
- 상속의 정본은 [03번 주제](../03-inheritance-and-global-keywords/2-summary.md)다.

### 4. `light-dark()` 는 무엇을 보는가

**출력** (Chrome 151 headless — 질문의 코드 그대로, 선호를 바꿔 두 번)

```text
                          선호 light          선호 dark
  .a (color-scheme 없음)   rgb(185, 28, 28)    rgb(185, 28, 28)    ★ 안 바뀐다
  .b (light dark)          rgb(185, 28, 28)    rgb(21, 128, 61)    선호를 따라간다
```

**선호가 dark 일 때**

- `.a` **빨강**(`rgb(185, 28, 28)`) — 선호가 dark 인데도 **밝은 쪽**이 나왔다.
- `.b` **초록**(`rgb(21, 128, 61)`).

**선호가 light 일 때**

- **둘 다 빨강**이다.

**명세 용어**

- **쓰이는 색 구성표**(used color-scheme). 「사용자 선호」가 아니라 **`color-scheme` 선언과 선호를 합쳐 요소마다 정해진 결과**다.\
  `color-scheme` 이 기본값 `normal` 이면 쓰이는 색 구성표는 **언제나 light** 이고, 그래서 `.a` 가 안 바뀐다.

**`only light`**

```text
실측
  .only { color-scheme: only light; color: light-dark(#b91c1c, #15803d) }
     선호 light -> rgb(185, 28, 28)      선호 dark -> rgb(185, 28, 28)
  계산값은 "light only" 로 직렬화된다     ★ 내가 쓴 순서와 뒤집힌다
```

- **언제나 밝은 쪽**이 나온다. `only` 는 「사용자 선호를 따르지 말고 이것만 써라」는 뜻이다.

### 5. 선호를 바꾸는 방법

**출력** (Chrome 151 headless — 같은 문서에 플래그만 바꿔 여섯 번)

```text
  플래그                                        (prefers-color-scheme: dark)
  ------------------------------------------    ----------------------------
  (없음)                                         false
  --force-dark-mode                              false      ★ 안 먹는다
  --force-prefers-color-scheme=dark              false      ★ 안 먹는다
  --enable-features=WebContentsForceDark         false      ★ 안 먹는다
  --blink-settings=preferredColorScheme=0        true       ★ 먹었다
  --blink-settings=preferredColorScheme=1        false
  --blink-settings=preferredColorScheme=2        false (light 도 false)

  --force-prefers-reduced-motion                 (reduce) = true    ★ 먹는다
  --force-prefers-contrast=more                  (more)   = false   ★ 안 먹는다
```

**`--force-dark-mode`**

- **참이 되지 않는다.** 그것은 **브라우저가 페이지 색을 강제로 뒤집는 기능**이지 선호를 바꾸는 것이 아니다.

**실제로 먹은 수단**

- **`--blink-settings=preferredColorScheme=N`** 이다. Blink 내부 설정을 직접 건드리는 플래그다.

**dark 에 해당하는 값**

- **`0` 이 dark, `1` 이 light** 다. 직관과 반대이므로 **던져서 확인해야** 한다.

**확인할 것**

- **`matchMedia("(prefers-color-scheme: dark)").matches`** 를 읽는다.\
  플래그 이름만 보고 「바꿨다」고 적으면 안 된다 — 실측에서 **세 개가 조용히 아무 일도 안 했다.**

### 6. 둘 다 거짓인 상태

**출력** (Chrome 151 headless · `--blink-settings=preferredColorScheme=2`)

```text
matchMedia("(prefers-color-scheme: dark)").matches  = false
matchMedia("(prefers-color-scheme: light)").matches = false
```

**그런 상태가 있는가**

- **있다.** 실측에서 dark 도 light 도 둘 다 거짓인 상태를 만들 수 있었다.

**`light` 블록만 써 둔 페이지**

- **아무 스타일도 안 걸린다.** 미디어 쿼리 밖에 기본값이 없으면 **색이 전혀 지정되지 않은 화면**이 된다.

**기본값의 자리**

```text
   나쁜 배치                                 좋은 배치
   @media (prefers-color-scheme: light) {     :root { --bg: #fff }          <- 기본은 밖에
     :root { --bg: #fff }                     @media (prefers-color-scheme: dark) {
   }                                            :root { --bg: #111 }        <- 차이만 안에
   @media (prefers-color-scheme: dark) {      }
     :root { --bg: #111 }
   }
   -> 둘 다 거짓이면 --bg 가 없다             -> 어떤 상태에서도 --bg 가 있다
```

### 7. 색을 뒤집으면 무엇이 깨지나

**출력** (Chrome 151 headless — 같은 내용을 두 장 그리고 아래쪽에만 `filter: invert(1) hue-rotate(180deg)`)

```text
  표본 지점        그대로           뒤집은 것
  -------------    --------------   --------------
  판 바탕          (255,255,255)    (0,0,0)
  이미지 픽셀      (40, 80, 220)    (132,172,255)
  카드 앞면        (255,255,255)    (0,0,0)
  카드 그림자      (228,228,228)    (27, 27, 27)
```

**사진**

- **같이 뒤집힌다.** 파란 픽셀(`40,80,220`)이 연한 하늘색(`132,172,255`)이 됐다.\
  `hue-rotate(180deg)` 를 곁들여도 **원래 색으로 돌아오지 않는다.**

**`box-shadow`**

- **밝기 순서가 역전된다.** 그림자 `(228,228,228)` → `(27,27,27)` 인데, 뒤집힌 판 바탕이 `(0,0,0)` 이라 **그림자가 바탕보다 밝다.**

**시각적으로 무엇으로 읽히나**

```text
   그대로                              뒤집은 것
   판 (255)                            판 (0)
     카드 (255)                          카드 (0)
     그림자 (228) < 카드보다 어둡다       그림자 (27) > 판보다 밝다
   => 카드가 떠 보인다                  => 카드가 판에 묻히고 후광만 남는다
```

- **그림자가 「빛무리」로 읽힌다.** 깊이 단서가 반대로 뒤집히는 것이다.

**대비비**

- **보존되지 않는다.** 밝은 배경에서 적정하던 대비가 어두운 배경에서는 눈부심이 되거나 흐려진다.\
  그래서 실무의 정석은 뒤집기가 아니라 **팔레트를 두 벌 두는 것**이다.

### 8. 정석 배치

**루트에 먼저 선언할 것**

```css
:root { color-scheme: light dark; }
```

- 이것이 없으면 **UA 가 그리는 것이 사용자 선호를 따르지 않는다**(실측: 기본 `normal` 은 언제나 light 처럼 그린다).

**내 색을 두 벌로 만드는 방법**

```text
   (a) 미디어 쿼리 + 커스텀 속성           (b) light-dark()
   :root { --bg: #fff }                   :root { color-scheme: light dark;
   @media (prefers-color-scheme: dark) {          --bg: light-dark(#fff, #111) }
     :root { --bg: #111 }
   }
   언제 쓰나                               언제 쓰나
   - 테마가 셋 이상                        - 값 하나만 둘로 갈릴 때
   - 넓은 지원이 필요할 때                 - 선언을 짧게 유지할 때
   - 두 테마의 구조가 다를 때              (Baseline newly 인 것을 감수)
```

**토글에서 같이 바꿀 것**

- **`color-scheme` 자체**다. 색 토큰만 토글하면 **스크롤바와 폼 컨트롤만 예전 테마로 남는다.**

```css
html[data-theme="dark"] { color-scheme: dark; --bg: #111; }
```

**첫 페인트의 흰 화면**

```text
실측 — <meta name="color-scheme" content="X"> 만 두고 CSS 를 안 썼다

  content="dark",       선호 light  -> 페이지 바탕 (18,18,18)
  content="light dark", 선호 light  -> (255,255,255)
  content="light dark", 선호 dark   -> (18,18,18)
  ★ 그때도 getComputedStyle(root).colorScheme 은 "normal" 이었다
```

- **메타 태그로 같은 것을 선언한다.** CSS 파일이 도착하기 전에 첫 페인트가 이뤄지기 때문이다.
- ★ **번쩍임 자체는 이 환경에서 못 쟀다**(첫 페인트 시점을 잡을 수단이 없었다). **메타가 색 구성표를 실제로 바꾼다는 것까지만** 실측했다.
- ★ 메타는 **CSS 속성값을 만들지 않는다** — `colorScheme` 을 읽어 진단하면 **안 걸린다.**

### 9. 다른 선호 기능들

**출력** (Chrome 151 headless — 이 환경의 값. 사람의 브라우저와 다르다)

```text
  (prefers-reduced-motion: reduce)        false   (--force-prefers-reduced-motion 으로 true 로 만들 수 있었다)
  (prefers-contrast: more)                false   (바꾸는 플래그를 못 찾았다)
  (forced-colors: active)                 false   (바꾸는 수단이 없었다)
  (prefers-reduced-transparency: reduce)  false
  (inverted-colors: inverted)             false
```

**각각의 뜻**

| 기능 | 뜻 |
|---|---|
| `prefers-reduced-motion` | 움직임을 줄여 달라는 설정(전정기관 장애·멀미 등) |
| `prefers-contrast` | 대비를 더/덜 원한다는 설정 |
| `forced-colors` | OS 가 색을 강제로 제한하는 모드(고대비 테마) |

**성질이 다른 하나**

- **`forced-colors`** 다. 다른 둘은 **묻기만** 하지만, 이것은 **브라우저가 실제로 내 색 선언을 갈아치운다.**\
  곧 「조건」이 아니라 「이미 벌어진 일을 알려 주는 신호」다.

**빨간 테두리 UI**

- **사라진다.** 그 모드에서는 `border-color` 가 시스템 색으로 대체되므로 **오류 표시와 정상 상태가 같은 색**이 된다.\
  색 말고 **아이콘·글자**로도 상태를 알려야 한다.

**정본**

- 정본은 [목록의 **60번 주제**](../60-prefers-reduced-motion/)(모션·접근성)다. 여기서는 **존재와 뜻까지만** 썼다.

### 10. 다른 주제와 잇기

**38번의 어느 규칙인가**

- **미디어 쿼리 문법 전부**다. `and`/`not`/쉼표·조건이 거짓일 때 규칙이 `cssRules` 에 남는 것·명시도에 영향이 없는 것이 그대로 적용된다.\
  다른 것은 **재는 대상**뿐이다 — 뷰포트가 아니라 사람의 설정.

**출처 사다리의 어디인가**

```text
   캐스케이드 출처 사다리 (01번 정본, normal 기준)
     작성자(author)   <- 내 CSS
     사용자(user)
     UA               <- ★ color-scheme 이 바꾸는 층
```

- `color-scheme` 은 **UA 스타일이 무엇을 그릴지**를 바꾼다. 내 선언과 경쟁하는 게 아니라 **맨 아래 층의 내용을 갈아 끼운다.**

**`color` 가 안 따라오는 이유**

- **상속은 「값을 내려보내는 것」이지 「부모를 다시 보는 것」이 아니다**([03번 주제](../03-inheritance-and-global-keywords/2-summary.md)).\
  루트에서 이미 검정으로 정해져 내려온 `color` 는 중간에서 색 구성표가 바뀌어도 **다시 계산되지 않는다.**\
  같은 서브트리에서 `color: CanvasText` 처럼 **시스템 색으로 다시 선언**하면 그때는 따라온다.

**조상의 테마를 자손이 읽으려면**

- **스타일 쿼리**다 — `@container style(--theme: dark) { … }`([40번 주제](../40-container-and-style-queries/2-summary.md)).\
  실측에서 조상이 `--theme: dark` 를 갖고 있으면 자손 규칙이 켜졌고, **`container-type` 선언이 없어도** 동작했다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**선호를 바꾼 수단** — `--blink-settings=preferredColorScheme=0`(dark) / `=1`(light) / `=2`(둘 다 거짓).
**먼저 `--force-dark-mode`·`--force-prefers-color-scheme=dark`·`--enable-features=WebContentsForceDark` 를 던져 봤고 셋 다 안 먹었다.**
`--force-prefers-reduced-motion` 은 먹었고 `--force-prefers-contrast=more` 는 안 먹었다. 전부 `matchMedia` 로 확인한 뒤 측정했다.

```bash
# 계산값 하네스 (37~41 공유)
google-chrome --headless --disable-gpu --no-sandbox \
  --blink-settings=preferredColorScheme=0 --window-size=800,400 --dump-dom "$D/index.html"

# 픽셀 하네스 — UA 가 그리는 것은 계산값에 안 나오므로 스크린샷을 찍어 표본한다
google-chrome --headless --disable-gpu --no-sandbox \
  --screenshot=/tmp/o.png --window-size=200,120 /tmp/doc.html
python3 -c "from PIL import Image; im=Image.open('/tmp/o.png').convert('RGB'); print(im.getpixel((180,90)))"
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 플래그 6종 던지기 + `matchMedia` 12종 | 6 | 환경 확인 · A5 · A9 |
| `--blink-settings=preferredColorScheme` 0/1/2 | 3 | 환경 확인 · A5 · A6 |
| `color-scheme` light/dark 의 폼 컨트롤·시스템 색 10항목 | 1 | 동작 방식 (2) · demo · A2 |
| `:root { color-scheme: normal/light/dark }` 픽셀 3장 | 3 | 동작 방식 (2) · A2 |
| 스크롤바 색 3장(넘치는 문서) + 스크롤바 폭 | 4 | 동작 방식 (2) · A2 |
| 선호만 dark 로 바꾼 무저자 문서 픽셀 | 1 | 동작 방식 (1) · A1 |
| `color-scheme: light dark` 를 두 선호에서 (픽셀 + 계산값) | 4 | 동작 방식 (3) · A4 |
| `light-dark()` × `normal`/`only light`/`light dark` × 두 선호 | 2 | 동작 방식 (4) · A4 |
| 서브트리 `color-scheme` 의 `color`·`background-color` | 2 | 동작 방식 (2) · A3 |
| `filter: invert(1) hue-rotate(180deg)` 픽셀 5지점 | 2 | 동작 방식 (5) · A7 |
| `<meta name="color-scheme">` 2종 × 두 선호 (픽셀 + 계산값) | 4 | A8 · 더 들어가면 |
| demo 1개 — 값 6항목 | 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 — `.dark` 의 `color-scheme` 제거 | 1 | demo |
| demo 의 「바꿔 볼 것」 — 같은 선언을 `:root` 에 (픽셀) | 3 | demo · A2 |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| UA 폼 컨트롤 색 | `input` `(59,59,59)` · `button` `(107,107,107)` | UA 스타일의 색은 구현·플랫폼이 정한다 |
| 페이지 바탕 dark | `(18, 18, 18)` | 〃 |
| 스크롤바 트랙·막대 | `(44,44,44)` · `(159,159,159)` | 스크롤바는 OS 위젯이라 더 잘 바뀐다 |
| `only light` 의 계산값 | `light only` | CSSOM 직렬화 세부 |
| `--blink-settings=preferredColorScheme` 의 값 대응 | `0` = dark | **공개 API 가 아니다.** 버전이 오르면 다시 던져 봐야 한다 |
| 메타 태그가 `colorScheme` 계산값을 안 만드는 것 | `normal` | 관찰 |
| Baseline | `color-scheme` widely 2024-08-03 · `light-dark()` newly 2024-05-13 | 2차 집계(`api.webstatus.dev`) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② 실제 OS 고대비 테마에서의 `forced-colors`(바꿀 수단이 없다 — 본문에서 값을 주장하지 않고 **뜻만** 썼다).

**못 잰 것** — ① `prefers-contrast`·`forced-colors` 를 참으로 만드는 것. 플래그를 던져 봤으나 값이 안 바뀌었고, 그래서 **그 모드의 실제 렌더 결과는 하나도 싣지 않았다.** ② 첫 페인트의 흰 화면 번쩍임. 메타 태그가 색 구성표를 바꾼다는 것까지만 쟀다(A8).

## 용어 풀이

- **`prefers-color-scheme`** — 사용자가 고른 테마를 묻는 미디어 기능. **조건일 뿐 아무것도 안 바꾼다.**
- **`color-scheme`** — 이 서브트리를 어느 색 구성표로 그릴지 UA 에게 알리는 **상속되는 속성**.
- **쓰이는 색 구성표(used color-scheme)** — `color-scheme` 선언과 선호를 합쳐 정해진 결과. `light-dark()` 가 보는 것.
- **UA 스타일** — 브라우저가 기본으로 그리는 것. 폼 컨트롤·스크롤바·페이지 바탕.
- **시스템 색** — `Canvas`·`CanvasText`·`ButtonFace` 등. 쓰이는 색 구성표에 따라 값이 달라진다.
- **`light-dark()`** — 두 값 중 하나를 쓰이는 색 구성표로 고르는 함수. Baseline **newly**.
- **`only`** — 「사용자 선호를 따르지 말고 이것만」이라는 `color-scheme` 의 한정자. 계산값은 `light only` 꼴.
- **`forced-colors`** — OS 의 강제 색 모드. 묻기만 하는 게 아니라 **내 색 선언을 갈아치운다.**
- **대비비(contrast ratio)** — 두 색의 밝기 차이 비율. 색을 뒤집어도 보존되지 않는다.
- **`--blink-settings`** — Blink 내부 설정을 직접 주는 Chrome 플래그. 공개 API 가 아니다.
