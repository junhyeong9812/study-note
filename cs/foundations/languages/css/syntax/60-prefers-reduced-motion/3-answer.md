# css/syntax/60 — `prefers-reduced-motion` 과 모션 접근성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 같은 문서를 두 판 띄워 측정한 것**이다.\
> 선호는 **`--force-prefers-reduced-motion`** 으로 켰고, 매 판 **`matchMedia` 로 켜졌는지 먼저 확인한 뒤** 값을 읽었다.\
> 규칙은 [Media Queries Level 5](https://drafts.csswg.org/mediaqueries-5/) §12.1 과 [WCAG 2.2](https://www.w3.org/TR/WCAG22/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 선호를 켜면 이 애니메이션은 멈추는가

**출력** (Chrome 151 headless — 같은 문서, 플래그만 다름)

```text
                            선호 끔 (reduce=false)      선호 켬 (reduce=true)
  #a  animationName             slide                       slide          ★ 그대로
      animationDuration         1s                          1s
      getAnimations().length    1                           1
      transitionProperty        transform                   transform
```

**`animationName`**

- **`slide` 그대로**다. 아무것도 안 바뀐다.

**실행 중인 애니메이션 개수**

- **1개**다. 계속 돌고 있다.

**브라우저가 하는 일**

- **알려 주기만 한다.** 미디어 기능은 **조건**이지 명령이 아니다.\
  `prefers-color-scheme` 이 화면을 안 바꾸는 것과 같은 구조다([39번 주제](../39-color-scheme-and-preferences/2-summary.md)).

**무엇이라 오해하기 쉬운가**

- **「플래그가 안 먹네」** 로 오해한다. 실제로는 플래그가 먹었고 **내 CSS 가 아무 대응을 안 한 것**이다.
- 그래서 **`matchMedia('(prefers-reduced-motion: reduce)').matches` 를 먼저 읽어** 두 가지를 갈라야 한다.

### 2. `reduce` 는 정확히 무엇을 요청하는가

**명세가 쓰는 문장**

> The prefers-reduced-motion media feature is used to detect if the user has requested the system minimize the amount of **non-essential** motion it uses.

- 붙어 있는 형용사는 **`non-essential`**(비본질적)이다. **「모든 모션」이 아니다.**

**`reduce` 설명의 동사 둘**

> **reduce** — Indicates that user has notified the system that they prefer an interface that **removes or replaces** the types of motion-based animation that either trigger discomfort for those with vestibular motion sensitivity, or distraction for those with attention deficits.

- **`removes`(없앤다)** 와 **`replaces`(대체한다)** 다.

**어떤 사람에게 무엇을 일으키나**

- **전정계(vestibular) 민감성**이 있는 사람에게는 **불편(discomfort)** 을,
- **주의력 결핍**이 있는 사람에게는 **주의 산만(distraction)** 을 일으키는 움직임이다.

**왜 오역인가**

```text
  요청                              흔한 구현
  +------------------------------+  +------------------------------+
  | 비본질적인 것을 최소화        |  | 전부 끈다                    |
  | 불편을 주는 '종류'를          |  | 종류를 안 가린다             |
  |   없애거나 '대체'하라         |  | 대체를 안 한다               |
  +------------------------------+  +------------------------------+
```

- **`replaces` 라는 단어가 「무언가는 남겨 두라」는 뜻**이다. 전부 끄면 대체할 것이 없다.

### 3. 전면 차단은 무엇을 죽이는가

**출력**

```text
                            선호 끔                  선호 켬
  #b  animationName            slide                   none
      transitionProperty       transform             ★ none
      transitionDuration       1s                      0s
      getAnimations().length   1                       0

  (대조) #c '줄이기' 형태
      transitionProperty       transform, opacity    ★ opacity
      transitionDuration       1s, 1s                  0.2s
```

**`transition-property` 의 계산값**

- **`none`** 이 된다. 이 요소에 **어떤 전환도 안 걸린다.**

**사용자가 잃는 것**

- **상태가 바뀌었다는 신호**다. 토글이 켜졌는지, 항목이 선택됐는지, 오류가 떴는지가 **한 프레임에 툭** 바뀐다.
- 움직임은 장식이기만 한 것이 아니라 **피드백**이기도 하다.

**그래도 쓸모 있는 경우**

- **손댈 수 없는 코드**에 걸 때다 — 서드파티 위젯·임베드·레거시 번들.
- **마지막 수단**이지 내 코드의 기본값이 아니다.

### 4. 무엇을 남기고 무엇을 없애나

```text
  없애거나 대체한다                         남긴다
  ------------------------------------      ------------------------------
  큰 거리의 이동 (화면을 가로지르는 슬라이드)  불투명도 전환 (페이드 인/아웃)
  확대·축소 (scale)                          색 전환 (상태 표시)
  회전 (rotate) · 3D 원근                     아주 짧은 이동 (수 px 이내)
  시차(parallax) · 자동 회전 캐러셀           진행률 표시 (그 자체가 정보)
  화면 전체 뷰 전환 (59번)                    포커스 링 같은 즉시 피드백
```

**가르는 기준 둘**

1. **크게 움직이나** — 위치가 크게 변하면 전정계를 자극한다.
2. **없으면 정보가 사라지나** — 사라지면 본질적(essential)이다.

**불투명도의 특별대우**

- **위치가 안 변한다** — 전정계를 자극하지 않는다.
- **그런데 「달라졌다」는 신호는 남는다** — 대체 수단으로 쓸 수 있는 거의 유일한 축이다.

### 5. 두 형태 중 어느 쪽이 나은가

**깜빡했을 때**

```text
  ① reduce 에서 끄는 설계        기본값 = 움직임   ->  빠뜨리면 그냥 움직인다 ★
  ② no-preference 에서 켜는 설계  기본값 = 정적     ->  빠뜨리면 안 움직인다  ✓
```

- **② 가 낫다.** 이유는 **누락에 강해서**다 — 새 애니메이션을 추가하면서 미디어 쿼리를 잊어도 안전한 쪽으로 떨어진다.

**출력** (`no-preference` 에서 켜는 형태 `#d`)

```text
                     선호 끔          선호 켬
  #d  animationName    slide            none
```

**`no-preference` 의 뜻**

- **「움직여 달라」가 아니다.** 「**이 항목에 대해 말한 적이 없다**」는 뜻이다.
- 그래서 ② 는 「원하는 사람에게만 준다」가 아니라 「**모르는 사람에게는 기본 연출을 준다**」로 읽는다.

**둘 다 아님 상태**

- **없었다.** 실측에서 `reduce` 와 `no-preference` 가 **언제나 서로 반대**였다.

```text
  선호 끔   reduce=false   no-preference=true
  선호 켬   reduce=true    no-preference=false
```

- ★ **39번 주제의 `prefers-color-scheme` 은 달랐다** — `--blink-settings=preferredColorScheme=2` 에서 **dark 도 light 도 둘 다 거짓**인 제3의 상태가 있었다.\
  **여기서는 그런 판을 못 만들었다.** 다만 이것은 **이 환경의 관찰**이지 보장이 아니다.

### 6. `scroll-behavior: smooth` 는 꺼지는가

**출력** (`html { scroll-behavior: smooth }` · 0 에서 1500 으로 이동)

```text
  방법                              선호 끔                          선호 켬
  ------------------------------    -----------------------------    -----------------------------
  scrollTo({behavior:'smooth'})     11ms:2 → 311ms:1281 → 911ms:1500  17ms:2 → 300ms:1248 → 900ms:1500
  앵커 이동 (location.hash)          17ms:2 → 300ms:1248 → 900ms:1500  17ms:2 → 300ms:1248 → 900ms:1500
  scrollingElement.scrollTop = n     17ms:1500 (즉시)                  17ms:1500 (즉시)
```

**앵커 링크 이동**

- **선호를 켜도 부드럽게 간다.** 약 0.7초가 걸렸고 **두 판이 구별되지 않았다.**

**`scrollTo({ behavior: 'smooth' })`**

- **역시 그대로**다. 브라우저가 알아서 꺼 주지 않는다.

**고치는 법과 그 효과**

```css
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
```

```text
  이 한 줄을 넣고 다시 잰 앵커 이동
    선호 끔   15ms:2 → 298ms:1248 → 915ms:1500   (부드럽게)
    선호 켬   ★ 7ms:1500                          (즉시 점프)
```

- **먹는다.** 7ms 에 이미 목적지였다.

### 7. 이 기능이 못 막는 것

```text
  CSS 안              |  CSS 밖 (이 미디어 쿼리가 닿지 않는다)
  --------------------+----------------------------------------
  transition          |  <video autoplay>  자동재생 영상
  animation           |  애니메이션 GIF·APNG
  transform           |  <canvas>·WebGL·requestAnimationFrame 루프
                      |  scroll-behavior: smooth  ★ 실측으로 확인 (A6)
```

- 스크롤 연동 애니메이션(58번)은 **CSS 안에 있지만 자동으로 안 꺼진다** — 저자가 `animation-timeline: none` 등으로 직접 꺼야 한다.

**자동재생 영상**

```js
if (matchMedia('(prefers-reduced-motion: reduce)').matches) video.pause();
```

- 또는 `<picture>` 로 **정지 이미지를 내준다.** CSS 로는 방법이 없다.

**스크롤 연동은 안전한가**

- **절반만 안전하다.** 움직임이 **사용자의 손가락에 묶여 있어** 예상 못 한 자동 움직임이 없다 — 이 점은 안전하다.
- 하지만 **시차·확대·회전은 여전히 전정계를 자극한다.** 그리고 **선호가 켜져도 그대로 돈다.**
- 그래서 `@media (prefers-reduced-motion: reduce)` 에서 **연출을 바꾸거나 타임라인을 끈다.** 정본은 [58번 주제](../58-scroll-driven-animations/2-summary.md).

### 8. WCAG 는 무엇을 요구하는가

**2.3.3 Animation from Interactions**

> Motion animation triggered by interaction can be disabled, unless the animation is essential to the functionality or the information being conveyed.

- 등급은 **AAA** 다.

**이 미디어 쿼리를 지정하는가**

- **아니다.** 「끌 수 있어야 한다」만 요구하고 **수단을 지정하지 않는다.**

**다른 수단**

- **페이지 안의 토글**이 대표적이다. OS 설정을 못 바꾸는 환경(공용 PC·관리 단말)을 위해 둘을 같이 두는 사이트가 있다.
- `prefers-reduced-motion` 은 **가장 싼 수단 중 하나**일 뿐이다.

**2.2.2 Pause, Stop, Hide**

> For moving, blinking, scrolling, or auto-updating information, all of the following are true:

- **움직이거나 깜빡이거나 스크롤되거나 자동 갱신되는 정보**에 대한 기준이고, 등급은 **A**(가장 낮은 단계, 즉 **필수**)다.
- 자동 회전 캐러셀이 여기 걸린다 — **선호와 무관하게** 멈출 수단이 있어야 한다.

### 9. 측정은 어떻게 하는가

**켜는 수단 둘**

```text
  ① 명령줄 플래그   --force-prefers-reduced-motion
       -> reduce=true / no-preference=false 로 바뀌었다
  ② CDP            Emulation.setEmulatedMedia
       features: [{ name: "prefers-reduced-motion", value: "reduce" }]
       -> 켜졌고, value 를 "no-preference" 로 다시 던져 끌 수도 있었다
```

**시작 전에 확인할 것**

- **`matchMedia('(prefers-reduced-motion: reduce)').matches`** 를 먼저 읽는다.\
  이걸 안 하면 「내 CSS 가 반응 안 함」과 「선호가 안 켜짐」이 **같은 화면으로 보인다.**

**조용히 틀린 결론이 나오는 함정**

- ★ **두 판을 같은 디버깅 포트로 돌리는 것**이다.

```text
  판 ①  chrome --remote-debugging-port=9334  (플래그 없음)  -> 측정 -> 종료 요청
  판 ②  chrome --remote-debugging-port=9334  (플래그 있음)
         ↑ 앞 브라우저가 아직 포트를 쥐고 있으면
           /json 조회가 '앞 브라우저'에 붙는다
        -> 두 판이 같은 값을 낸다 -> "플래그가 안 먹는다"라는 틀린 결론
```

- 실제로 이 사고를 냈다. 판마다 **포트를 갈랐더니** 곧바로 `reduce=true` 가 나왔다.
- **두 판 비교 실험에서는 「두 판이 정말 다른 브라우저인가」를 먼저 증명해야 한다** — 여기서는 `matchMedia` 값이 서로 다르다는 것이 그 증명이다.

### 10. 다른 주제와 잇기

**선호 일반의 정본**

- [39번 주제](../39-color-scheme-and-preferences/2-summary.md)다. 선호 미디어 기능이 **묻기만 한다**는 구조와 선호를 바꾸는 플래그 실측이 거기 있다.
- **이 주제는 `prefers-reduced-motion` 한 축**만 다룬다.
- ⚠️ 39번 표가 `prefers-contrast`·`forced-colors` 의 정본도 여기로 가리키고 있으나, **목록 README 가 정한 이 주제의 축은 모션 하나**다. 그 둘은 이 배치에서 아직 정본이 없다.

**뷰 전환(59번)을 `reduce` 에서**

- **크로스페이드만 남긴다.** `::view-transition-group(<이름>)` 의 크기·위치 애니메이션을 끄고 `old`/`new` 의 불투명도만 둔다.
- 화면 전체가 한꺼번에 움직이는 부류라 **특히 줄일 대상**이다.

**진입·퇴장 전환(57번)을 `reduce` 에서**

- **이동·확대를 빼고 불투명도만 남긴다.** `@starting-style { opacity: 0 }` 은 그대로 두고 `transform` 만 없앤다.
- `display … allow-discrete` 는 **그대로 둔다** — 그건 움직임이 아니라 **타이밍 확보**다.

**다른 주제의 demo 에 안 넣는 이유**

- [render-rules.md](../../../../../../reference/render-rules.md) 가 **「하나만 보여 준다」가 깨진다**는 이유로 그렇게 정했다.
- 그래서 다른 주제들은 **여기로 링크**하고, **`prefers-reduced-motion` 을 쓰는 demo 는 이 문서에만** 있다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--headless=new`). **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**선호를 켠 수단** — **`--force-prefers-reduced-motion` 이 먹었다.** 매 판 `matchMedia` 로 확인한 뒤 측정했다.

```text
  판          플래그                              (reduce)   (no-preference)
  선호 끔     (없음)                               false      true
  선호 켬     --force-prefers-reduced-motion       true       false

  CDP 로도 확인 — Emulation.setEmulatedMedia
    value "reduce"         -> reduce=true  / no-preference=false
    value "no-preference"  -> reduce=false / no-preference=true   (되돌릴 수 있다)
```

```bash
# 두 판을 '다른 포트'로 띄운다 — 같은 포트를 재사용하면 앞 판에 다시 붙는다 (A9)
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --remote-allow-origins=* --remote-debugging-port=9440 --window-size=900,500 about:blank
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --remote-allow-origins=* --remote-debugging-port=9441 --window-size=900,500 \
  --force-prefers-reduced-motion about:blank
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 플래그 4종 + CDP 던져 보기 (`matchMedia` 확인) | 8 | 환경 확인 · A9 |
| 네 형태(`#a` 무대응 · `#b` 전면차단 · `#c` 줄이기 · `#d` no-preference) × 두 판 | 2 | 동작 방식 (1)·(2)·(4) · A1 · A3 · A5 |
| `scroll-behavior` 4경로 × 두 판 | 2 | 동작 방식 (5) · A6 |
| `@media (reduce){html{scroll-behavior:auto}}` 추가 후 재측정 × 두 판 | 2 | 동작 방식 (5) · A6 |
| demo × 두 판 (CDP 실제 마우스 이동 + rAF 샘플) | 2 | demo · A4 |
| demo 「바꿔 볼 것」 ① `no-preference` → `reduce` × 두 판 | 2 | demo |
| 명세 원문 확인(mediaqueries-5 §12.1) | 1 | 한눈에 · A2 |
| WCAG 2.3.3 · 2.2.2 원문 확인 | 1 | A8 |
| Baseline 조회 | 1 | 머리말 |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `--force-prefers-reduced-motion` 이 먹는 것 | reduce=true | **공개 API 가 아니다.** 버전이 오르면 다시 던져 봐야 한다 |
| `reduce`/`no-preference` 가 **언제나 서로 반대**인 것 | 두 판 모두 반대 | **관찰**이다. 39번 주제에서는 둘 다 거짓인 판이 있었다 |
| `scroll-behavior: smooth` 가 **안 꺼지는 것** | 두 판 동일 | 명세가 끄라고 요구하지 않는다 — 구현 선택 |
| 부드러운 스크롤이 걸린 시간 | 약 0.7초 | 구현이 정하는 값 |
| `scrollingElement.scrollTop = n` 이 **즉시 점프**한 것 | 17ms:1500 | 관찰. 본문에서 규칙으로 주장하지 않았다 |
| 이 환경의 기본값 | `no-preference` | **환경.** 사람의 브라우저 값이 아니다 |
| Baseline | widely (2022-07-15) | 2026-09-23 조회. `api.webstatus.dev` 는 **2차 집계**다 |

**한 번 틀린 결론을 낸 것** — 첫 판에서 **두 브라우저를 같은 디버깅 포트(9334)로** 띄웠다. 앞 브라우저가 포트를 놓기 전에 뒤 브라우저의 `/json` 조회가 **앞 브라우저에 붙어**, 두 판이 같은 값을 냈다. 그 결과 「`--force-prefers-reduced-motion` 이 안 먹는다」는 **틀린 결론**을 한 번 적었다. 판마다 포트를 갈랐더니 곧바로 `reduce=true` 가 나왔다. **틀린 값을 지우지 않고 A9 에 함정으로 남겼다.**

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② 실제 OS 의 「동작 줄이기」 설정(이 환경에 데스크톱 설정이 없다 — 플래그와 CDP 로 대신했다). ③ `prefers-reduced-transparency`·`prefers-reduced-data`(「더 들어가면」에 **존재만** 적었고 값을 주장하지 않았다).

**못 잰 것** — **「이 정도 움직임이면 전정계를 자극한다」는 경계**다. 이것은 픽셀로 재는 값이 아니라 사람에 대한 판정이라 **측정 방법 자체가 이 환경에 없다.** 그래서 본문의 「무엇을 남기고 무엇을 없애나」 표는 **명세 문구(`vestibular motion sensitivity` · `non-essential`)에서 유도한 분류**이지 실측이 아니다 — 그 사실을 여기에 남긴다.

## 용어 풀이

- **`prefers-reduced-motion`** — 비본질적 움직임을 최소화해 달라고 사용자가 알렸는지 묻는 미디어 기능. **조건일 뿐이다.**
- **`reduce`** — 불편·주의 산만을 유발하는 **종류의** 움직임을 **없애거나 대체**해 달라는 값.
- **`no-preference`** — 이 항목에 대해 **말한 적이 없다**는 값.
- **전정계(vestibular system)** — 귓속의 균형 감각 기관. 본 것과 느낀 것이 어긋나면 어지럼이 난다.
- **비본질적(non-essential) 움직임** — 없어도 정보가 전달되는 움직임.
- **전면 차단** — `* { animation: none !important }` 식 패턴. `transition-property` 까지 `none` 으로 만든다.
- **WCAG 2.3.3 Animation from Interactions** — 상호작용으로 생기는 모션을 **끌 수 있어야 한다**는 **AAA** 기준. 수단은 지정하지 않는다.
- **WCAG 2.2.2 Pause, Stop, Hide** — 움직이거나 깜빡이거나 자동 갱신되는 정보에 대한 **A**(필수) 기준.
- **`scroll-behavior: smooth`** — 스크롤 이동을 부드럽게 하는 속성. **선호를 켜도 자동으로 안 꺼진다.**
- **`matchMedia()`** — 미디어 쿼리를 JS 로 읽는 함수. CSS 가 못 닿는 영상·GIF·JS 루프를 거를 때 쓴다.
- **`Emulation.setEmulatedMedia`** — CDP 로 미디어 기능 값을 강제하는 명령. 한 브라우저 안에서 켜고 끌 수 있다.
