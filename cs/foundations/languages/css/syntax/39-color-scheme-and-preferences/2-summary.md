# css/syntax/39 — 사용자 선호와 다크 모드: `prefers-color-scheme`·`color-scheme` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Media Queries Level 5](https://drafts.csswg.org/mediaqueries-5/) 의 「User Preference Media Features」 절 · [CSS Color Adjustment Module Level 1](https://drafts.csswg.org/css-color-adjust-1/) 의 「`color-scheme`」·「System Colors 의 사용」 · [CSS Color Level 5](https://drafts.csswg.org/css-color-5/) 의 `light-dark()`. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle`·`matchMedia` 로 읽거나, **스크린샷을 찍어 픽셀을 표본한 것**이다. **선호를 바꾸는 플래그는 여러 개를 던져 보고 되는 것만 썼다** — 아래 「환경 확인」이 그 기록이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. `prefers-color-scheme` 은 Baseline **widely**(2020-01-15 → 2022-07-15) · `color-scheme` 은 **widely**(2022-02-03 → 2024-08-03) · `light-dark()` 는 **newly**(2024-05-13, 아직 widely 아님) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 환경 확인 — 선호를 어떻게 바꿨나

이 주제는 **환경을 바꿔 가며 재는 것이 본체**라 측정 수단부터 밝힌다. **플래그를 던져 보고 되는 것만 썼다.**

```text
실측 — 같은 문서에 플래그만 바꿔 여섯 번 띄우고 matchMedia 를 읽었다

  플래그                                        prefers-color-scheme: dark    비고
  ------------------------------------------    --------------------------    ------
  (없음)                                         false                         기본은 light
  --force-dark-mode                              false                         ★ 안 먹는다
  --force-prefers-color-scheme=dark              false                         ★ 안 먹는다
  --enable-features=WebContentsForceDark         false                         ★ 안 먹는다
  --blink-settings=preferredColorScheme=0        true                          ★ 이것만 먹었다
  --blink-settings=preferredColorScheme=1        false                         light
  --blink-settings=preferredColorScheme=2        false (light 도 false)         ★ 제3의 상태

  --force-prefers-reduced-motion                 (reduce) = true               ★ 먹는다
  --force-prefers-contrast=more                  (more)   = false              ★ 안 먹는다
```

- **`--force-dark-mode` 는 이 목적에 안 먹는다.** 이름 때문에 가장 먼저 시도하게 되는데, 그것은 **브라우저가 페이지 색을 강제로 뒤집는 기능**이지 `prefers-color-scheme` 을 바꾸는 것이 아니다.
- **`--blink-settings=preferredColorScheme=0` 이 dark, `=1` 이 light** 였다. 값이 0 이 dark 인 것은 직관과 반대다.
- ★ **`=2` 에서는 dark 도 light 도 둘 다 거짓**이었다. 「둘 중 하나는 참」이라는 가정이 깨지는 상태가 실제로 있다.
- 선호 자체를 못 바꾸는 항목(`prefers-contrast`)은 **바꾸지 못했다고 적고 뜻만** 쓴다. 이 문서는 그렇게 했다.

## 한눈에 — 쉽게 말하면

**둘은 이름이 닮았을 뿐 서로 다른 기계다. `prefers-color-scheme` 은 묻고, `color-scheme` 은 시킨다.**

식당에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 손님에게 「매운 것 괜찮으세요?」 묻기 | `@media (prefers-color-scheme: dark)` — **읽기만** 한다 |
| 그 답에 맞춰 **내가** 요리를 바꾼다 | 내 CSS 로 색을 다시 칠하는 것 |
| 주방에 「이 테이블은 매운 코스」라고 **알리기** | `color-scheme: dark` — **브라우저에게 시킨다** |
| 주방이 알아서 바꾸는 것 | **UA 가 그리는 것** — 스크롤바·폼 컨트롤·페이지 바탕 |
| 「손님 답에 맞춰 주세요」 | `color-scheme: light dark` |
| 답에 따라 둘 중 하나를 고르는 소스 | `light-dark(밝을때, 어두울때)` |

- **미디어 쿼리는 아무것도 안 바꾼다.** 조건일 뿐이다 — 내가 그 안에 색을 쓰지 않으면 화면은 그대로다.
- **`color-scheme` 은 선언 하나로 화면이 바뀐다.** 내가 색을 하나도 안 썼는데도.

```text
   실측 — 저자 CSS 에 색을 한 글자도 안 쓰고 두 가지만 바꿔 봤다

   (A) 선호만 dark 로            (B) :root { color-scheme: dark }
   +---------------------------+  +---------------------------+
   | 페이지 바탕  (255,255,255)|  | 페이지 바탕  (18,18,18)   |
   | 스크롤바 트랙 (252,252,252)|  | 스크롤바 트랙 (44,44,44)  |
   | input 배경   (255,255,255)|  | input 배경   (59,59,59)   |
   +---------------------------+  +---------------------------+
     아무것도 안 바뀐다              UA 가 그리는 것이 전부 바뀐다
```

실무에서 이게 터지는 자리는 **「미디어 쿼리로 다크 모드를 다 짰는데 폼 입력칸만 하얗게 남는」** 때다.\
입력칸은 **내 CSS 가 그리는 게 아니라 브라우저가 그리는 것**이라, `color-scheme` 을 선언하기 전에는 안 바뀐다.

> **사용자 선호 미디어 기능(user preference media feature)** — OS·브라우저 설정을 읽는 미디어 기능. `prefers-*`·`forced-colors` 가 이 부류다.\
> 예: `@media (prefers-color-scheme: dark)` 는 「사용자가 어두운 테마를 골랐나」를 묻는다.

> **UA 스타일(user agent style)** — 브라우저가 기본으로 그리는 것. 폼 컨트롤·스크롤바·페이지 바탕.\
> 예: `<input>` 의 흰 배경은 내 CSS 에 없다 — 브라우저가 그린 것이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`prefers-color-scheme` 과 `color-scheme` 은 각각 무엇을 바꾸는가.** 하나만 쓰면 무엇이 안 바뀌는가.
2. **`light-dark()` 는 무엇을 보고 고르는가.** 사용자 선호인가, 선언된 색 구성표인가.
3. **다크 모드를 「색을 뒤집는 것」으로 하면 무엇이 깨지는가.**

## 동작 방식

### (1) ★ 미디어 쿼리는 읽기만 한다 — 화면은 안 바뀐다

**언제 쓰나** — 다크 모드를 처음 짤 때. **여기서 갈라야 나머지가 읽힌다.**

```text
실측 — 저자 CSS 가 아예 없는 문서를 선호만 바꿔 띄우고 스크린샷 픽셀을 표본했다

  --blink-settings=preferredColorScheme=0 (dark)
    matchMedia("(prefers-color-scheme: dark)").matches = true
    페이지 바탕 픽셀 (280,110) = (255, 255, 255)        ★ 그대로 하얗다
```

```text
   @media (prefers-color-scheme: dark) { … }

        브라우저 -> "사용자가 어두운 쪽을 골랐다"  (참/거짓)
                          |
                          v
        내가 쓴 선언들이 켜진다  <- 내가 안 쓰면 아무 일도 안 일어난다
```

그림 해설 (한 단계씩):

- 이것은 **[38번 주제](../38-media-queries/2-summary.md)의 미디어 기능 하나**일 뿐이다. 문법도 논리도 거기와 똑같다.
- 다른 점은 **재는 대상**이다 — 뷰포트가 아니라 **사람의 설정**을 읽는다.
- **화면을 바꾸는 것은 전적으로 내가 그 안에 쓴 선언**이다.

비용 — 없음. 대신 **UA 가 그리는 것은 여기로 못 바꾼다**(아래 (2)).

### (2) ★★ `color-scheme` 은 UA 가 그리는 것을 바꾼다

**언제 쓰나** — 폼 컨트롤·스크롤바·페이지 바탕이 다크 모드에서 안 바뀔 때. **이 주제의 과녁이다.**

```text
실측 — 저자 CSS 에 색을 한 글자도 안 쓰고 color-scheme 만 갈랐다

  항목                           color-scheme: light     color-scheme: dark
  ----------------------------   ---------------------   ---------------------
  <input> 배경                   rgb(255, 255, 255)      rgb(59, 59, 59)
  <input> 글자색                 rgb(0, 0, 0)            rgb(255, 255, 255)
  <input> 테두리색               rgb(118, 118, 118)      rgb(133, 133, 133)
  <button> 배경                  rgb(239, 239, 239)      rgb(107, 107, 107)
  <button> 글자색                rgb(0, 0, 0)            rgb(255, 255, 255)
  시스템 색 Canvas               rgb(255, 255, 255)      rgb(18, 18, 18)
  시스템 색 CanvasText           rgb(0, 0, 0)            rgb(255, 255, 255)
```

루트에 걸면 **페이지 바탕과 스크롤바까지** 바뀐다. 스크린샷 픽셀로 잰 것이다.

```text
실측 — :root { color-scheme: X } 만 다른 문서 세 장을 찍어 같은 좌표를 표본했다
       (내용은 2000px 짜리 흰 div 하나 — 세로 스크롤바가 생긴다)

  색 구성표    페이지 바탕     스크롤바 트랙    스크롤바 막대   본문 div
  ----------   -------------   --------------   -------------   -------------
  normal       (255,255,255)   (252,252,252)    (139,139,139)   (255,255,255)
  light        (255,255,255)   (252,252,252)    (139,139,139)   (255,255,255)
  dark         (18,18,18)      (44,44,44)       (159,159,159)   (255,255,255)
                ^^^^^^^^^^^     ^^^^^^^^^^^                      ^^^^^^^^^^^
                UA 가 그린 것이 바뀌었다                          내가 칠한 것은 그대로
```

```text
   누가 그리나로 갈린다

   +-------------------------------------------+
   |  내가 그리는 것        UA 가 그리는 것      |
   |  -------------------   -------------------|
   |  background / color    페이지 바탕(canvas)|
   |  border / box-shadow   스크롤바           |
   |  내 컴포넌트 전부      폼 컨트롤 기본 모습 |
   |  ^ @media 로 바꾼다    ^ color-scheme 으로 |
   |                          바꾼다            |
   +-------------------------------------------+
```

그림 해설 (한 단계씩):

- **`color-scheme` 은 미디어 쿼리가 아니다.** 조건이 아니라 **상속되는 보통 CSS 속성**이다.
- 값은 `normal`(기본) · `light` · `dark` · `light dark`(둘 다 지원한다고 알림) · `only light` 등이다.
- 실측에서 **`only light` 는 계산값이 `light only` 로 정규화**됐다. 내가 쓴 순서와 다르다.
- ★ **`.dark` 안의 `<p>` 글자색은 안 바뀌었다**(실측: `rgb(0, 0, 0)`). `color` 는 루트에서 **이미 상속돼 내려온 값**이라 그대로다.\
  곧 **서브트리에 `color-scheme: dark` 만 걸면 「어두운 입력칸이 하얀 바닥에 놓이는」 어중간한 상태**가 된다.

비용 — **선언하면 되돌리기가 번거롭다.** 특정 컴포넌트만 밝게 두려면 그 자리에 `color-scheme: light` 를 다시 건다.

### (3) 둘을 함께 쓰는 정석

**언제 쓰나** — 다크 모드를 실제로 짤 때.

```text
   1) 브라우저에게 알린다 (UA 가 그리는 것)
      :root { color-scheme: light dark; }

   2) 내가 그리는 것을 고른다  — 둘 중 하나
      (a) 미디어 쿼리로            (b) light-dark() 로
      :root { --bg: #fff }         :root { --bg: light-dark(#fff, #111) }
      @media (prefers-color-scheme: dark) {
        :root { --bg: #111 }
      }

   3) 사용자가 직접 고를 수 있게 하려면 루트에 토글을 건다
      html[data-theme="dark"] { color-scheme: dark; --bg: #111 }
```

```text
실측 — color-scheme: light dark 는 선호를 따라간다

  선언                      선호 light          선호 dark
  ----------------------    ----------------    ----------------
  :root { color-scheme: light dark }
    페이지 바탕              (255,255,255)       (18,18,18)
  .ld { color-scheme: light dark;
        color: light-dark(#b91c1c, #15803d) }
                             rgb(185,28,28)      rgb(21,128,61)
```

그림 해설 (한 단계씩):

- `light dark` 는 「**둘 다 그릴 줄 안다, 사용자 설정을 따라 달라**」는 선언이다.
- 이것이 있어야 **UA 가 사용자의 선호를 실제로 반영**한다. 없으면(기본 `normal`) 언제나 light 처럼 그린다.
- 3번 단계의 토글에서 `color-scheme` 을 같이 바꿔 주지 않으면 **스크롤바와 입력칸만 예전 테마로 남는다.**

비용 — 선언 한 줄. 안 쓰는 쪽이 더 비싸다.

### (4) ★ `light-dark()` 가 보는 것은 선호가 아니라 「쓰이는 색 구성표」다

**언제 쓰나** — `light-dark()` 를 처음 쓸 때. **가장 헷갈리는 자리다.**

```text
실측 — 같은 선언을 color-scheme 만 바꿔 가며 두 선호에서 읽었다
       color: light-dark(#b91c1c, #15803d)      (빨강, 초록)

  color-scheme     선호 light          선호 dark
  --------------   ----------------    ----------------
  normal (기본)    rgb(185, 28, 28)    rgb(185, 28, 28)   ★ 선호가 dark 인데 빨강
  light only       rgb(185, 28, 28)    rgb(185, 28, 28)
  light dark       rgb(185, 28, 28)    rgb(21, 128, 61)   선호를 따라갔다
```

```text
   light-dark() 가 묻는 것

   "이 요소에 쓰이는 색 구성표(used color-scheme)가 dark 인가?"
                                ^^^^^^^^^^^^^^^^^^^^
                   = color-scheme 속성 + 사용자 선호를 합쳐 정해진 결과

   "사용자가 dark 를 골랐나?" 가 아니다.
   color-scheme 이 normal 이면 사용자가 무엇을 골랐든 언제나 밝은 쪽이 나온다
```

그림 해설 (한 단계씩):

- ★ **`color-scheme` 없이 `light-dark()` 만 쓰면 아무 일도 안 일어난다.** 이것이 실측에서 확인된 첫째 함정이다.
- `light-dark()` 는 **`@media` 블록을 하나 줄여 주는 도구**이지 미디어 쿼리의 대체품이 아니다.
- 상속되므로 **루트에 `color-scheme: light dark` 한 번만** 걸면 문서 전체에서 쓸 수 있다.
- Baseline **newly**(2024-05-13) 다 — 아직 widely 가 아니므로, 아주 넓게 받아야 하면 미디어 쿼리 쪽이 안전하다.

비용 — 두 값을 한 줄에 몰아 쓰므로 **테마가 셋 이상이면 안 맞는다.** 그때는 커스텀 속성으로 돌아간다.

### (5) ★ 다크 모드는 「색을 뒤집는 것」이 아니다

**언제 쓰나** — `filter: invert(1)` 한 줄로 끝내고 싶을 때. **안 된다는 것을 실측으로 본다.**

```text
실측 — 같은 내용을 두 장 그리고 아래쪽에만 filter: invert(1) hue-rotate(180deg) 를 걸었다
       스크린샷의 같은 좌표를 표본했다

  표본 지점        그대로           뒤집은 것
  -------------    --------------   --------------
  판 바탕          (255,255,255)    (0,0,0)          <- 의도한 것
  이미지 픽셀      (40, 80, 220)    (132,172,255)    <- ★ 사진까지 뒤집혔다
  카드 앞면        (255,255,255)    (0,0,0)          <- 의도한 것
  카드 그림자      (228,228,228)    (27, 27, 27)     <- ★ 바탕(0)보다 밝다
```

```text
   그림자가 뒤집히면 "빛무리" 가 된다

   그대로                              뒤집은 것
   판 (255)                            판 (0)
     카드 (255)                          카드 (0)
     그림자 (228)  < 카드보다 어둡다      그림자 (27)  > 판보다 밝다
   => 카드가 판 위에 떠 보인다          => 검은 카드가 검은 판에 묻히고
                                          테두리에 회색 후광만 남는다
```

그림 해설 (한 단계씩):

- **이미지·동영상·로고가 같이 뒤집힌다.** 사진의 파랑(`40,80,220`)이 연한 하늘색(`132,172,255`)이 됐다.
- **그림자의 방향이 뒤집힌다.** 밝기 순서가 역전되어 「아래로 지는 그림자」가 「위로 뜨는 후광」이 된다.
- 여기에 더해 **대비비(contrast ratio)가 보존되지 않는다.** 밝은 배경에서 충분하던 대비가 어두운 배경에서 눈부심이 되거나 흐려진다.
- 그래서 실무의 정석은 **색을 뒤집는 것이 아니라 팔레트를 두 벌 두는 것**이다. 토큰을 `--bg`·`--fg`·`--surface` 로 뽑고 두 벌을 따로 정한다.

비용 — 팔레트가 두 벌이 된다. 대신 이미지·그림자·대비를 각각 따로 정할 수 있다.

### (6) 다른 선호 기능들 — 존재와 뜻까지만

**언제 쓰나** — 접근성 요구를 받았을 때. **자세한 것은 이 주제가 아니다.**

```text
실측 — 이 환경에서 읽은 값 (사람의 브라우저와 다를 수 있다)

  (prefers-reduced-motion: reduce)        false     --force-prefers-reduced-motion 으로 true 로 바꿀 수 있었다
  (prefers-reduced-motion: no-preference) true
  (prefers-contrast: more)                false     ★ 바꾸는 플래그를 못 찾았다
  (prefers-contrast: no-preference)       true
  (forced-colors: active)                 false     ★ 바꾸는 수단이 없었다
  (forced-colors: none)                   true
  (prefers-reduced-transparency: reduce)  false
  (prefers-reduced-data: reduce)          false
  (inverted-colors: inverted)             false
```

| 기능 | 뜻 | 정본 |
|---|---|---|
| `prefers-reduced-motion` | 움직임을 줄여 달라는 설정. 전정기관 장애·주의력 문제 등 | [목록의 **60번 주제**](../60-prefers-reduced-motion/)(모션 접근성) |
| `prefers-contrast` | 대비를 더/덜 원한다는 설정 | ★ **정본 없음** — 아래 참조 |
| `forced-colors` | OS 가 색을 강제로 제한하는 모드(고대비 테마). **내 색 선언이 대부분 무시된다** | ★ **정본 없음** — 아래 참조 |
| `prefers-reduced-transparency` | 반투명을 줄여 달라는 설정 | — |
| `inverted-colors` | OS 차원에서 색을 반전시켜 보고 있음 | — |

★ **`prefers-contrast`·`forced-colors` 는 이 60주제 목록에 정본이 없다.**
60번의 축은 **모션 하나**이고(목록이 그렇게 정했다), 이 둘은 **색·대비 쪽**이라 성격이 다르다.
여기서 뜻과 이 환경에서 **바꾸지 못했다는 사실**까지만 적고, 깊이 다루는 것은 **다음 라운드의 몫**으로 남긴다.
★ **정본이 없다는 것을 적어 두는 편이 엉뚱한 곳을 가리키는 것보다 낫다** — 독자가 찾아가 헛걸음하지 않는다.

그림 해설 (한 단계씩):

- `forced-colors` 는 다른 선호와 **성질이 다르다** — 묻기만 하는 게 아니라 **브라우저가 실제로 내 색을 갈아치운다.**\
  그 모드에서는 `color`·`background-color` 가 대부분 무시되므로, **테두리·아이콘을 색으로만 구별하는 UI 가 통째로 사라진다.**
- ★ **모션 접근성의 정본은 [목록의 60번 주제](../60-prefers-reduced-motion/)다.** 여기서는 **존재와 뜻까지만** 쓴다.\
  demo 블록 안에 `prefers-reduced-motion` 을 넣지 않는 것도 같은 이유다([render-rules.md](../../../../../../reference/render-rules.md)).

비용 — 없음.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
:root { color-scheme: light dark; }                 /* 둘 다 그릴 줄 안다고 알린다 */
:root { --bg: light-dark(#ffffff, #111111); }       /* 쓰이는 색 구성표에 따라 고른다 */

@media (prefers-color-scheme: dark) { :root { --accent: #8ab4f8 } }

.keep-light { color-scheme: light; }                /* 이 서브트리만 밝게 */
```

```js
matchMedia("(prefers-color-scheme: dark)").matches   // 선호를 읽는다
getComputedStyle(el).colorScheme                     // 선언된 색 구성표
```

### 금지 사례 — 던져서 확인한 것

```css
:root { color-scheme: dark; }
/* 그런데 내 --bg 는 그대로 흰색 -> 바탕만 어둡고 카드가 하얗게 남는다 */

.pane { color-scheme: dark; }
/* 서브트리에만 걸면 글자색은 안 바뀐다 — 실측: .pane 안의 <p> 가 rgb(0, 0, 0) 그대로 */

:root { --bg: light-dark(#fff, #111); }
/* color-scheme 선언이 없으면 선호가 dark 여도 언제나 #fff 다 (실측) */

html { filter: invert(1); }
/* 사진·그림자·대비가 전부 깨진다 (실측) */
```

### 어디서 헷갈리나

- **`prefers-color-scheme` 은 미디어 기능, `color-scheme` 은 속성**이다. 하나는 조건이고 하나는 선언이다.
- **`color-scheme` 은 상속된다.** 루트에 한 번 걸면 문서 전체에 내려간다.
- **`light-dark()` 는 `color-scheme` 이 있어야 동작한다.** 선호만으로는 안 고른다.
- **`only light` 의 계산값은 `light only`** 다(실측). 직렬화 순서가 뒤집힌다.
- **`color-scheme` 은 내 `background-color` 를 안 바꾼다.** 내가 칠한 것은 내 책임이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. 미디어 쿼리만 쓰고 폼 컨트롤이 하얗게 남는다

실측에서 **선호만 dark 로 바꿨을 때 페이지 바탕도 입력칸도 하나도 안 바뀌었다.**\
입력칸·스크롤바·페이지 바탕은 **UA 가 그리는 것**이라 `color-scheme` 없이는 못 바꾼다.\
증상이 「거의 다 됐는데 몇 군데만 이상함」이라 원인을 엉뚱한 데서 찾게 된다.

### 2. `color-scheme` 만 쓰고 내 색이 안 따라온다

반대 사고다. `:root { color-scheme: dark }` 만 걸면 **바탕은 어두워지는데 내가 칠한 카드는 그대로 하얗다.**\
실측에서 `color-scheme: dark` 아래의 본문 div(내가 흰색으로 칠한 것)는 `(255,255,255)` 그대로였다.

### 3. 서브트리에만 `color-scheme` 을 걸고 다 된 줄 안다

실측에서 `.dark { color-scheme: dark }` 안의 `<p>` 글자색이 **`rgb(0, 0, 0)` 그대로**였다.\
`color` 는 루트에서 이미 상속돼 내려온 값이라 안 바뀐다. **어두운 입력칸이 하얀 바닥 위에 놓인다.**

### 4. `light-dark()` 를 선호 질의로 착각한다

실측에서 `color-scheme` 이 기본(`normal`)일 때 **선호가 dark 인데도 밝은 쪽 값**이 나왔다.\
`light-dark()` 는 **「쓰이는 색 구성표」** 를 본다. `color-scheme: light dark` 를 먼저 선언해야 동작한다.

### 5. `--force-dark-mode` 로 테스트하고 「선호를 바꿨다」고 적는다

실측에서 **`--force-dark-mode` 는 `prefers-color-scheme` 을 안 바꿨다**(`matches = false`).\
이름이 그럴듯해서 가장 먼저 쓰게 되는데, 그건 **브라우저가 색을 강제로 뒤집는 별개 기능**이다.\
반드시 **`matchMedia(...).matches` 를 읽어 확인**하고, 바뀐 것을 본 뒤에 측정을 시작한다.

### 6. 「둘 중 하나는 참」이라고 가정한다

실측에서 `--blink-settings=preferredColorScheme=2` 로 띄우면 **`dark` 도 `light` 도 둘 다 거짓**이었다.\
`@media (prefers-color-scheme: light) { … }` 만 써 두면 **아무 스타일도 안 걸리는 상태**가 생길 수 있다.\
**기본값은 미디어 쿼리 밖에 두고, 블록 안에는 차이만** 담는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `prefers-color-scheme` 이 조건일 뿐 화면을 안 바꾸는 것 | **명세**(mediaqueries-5) |
| `color-scheme` 이 UA 가 그리는 것을 바꾸는 것 | **명세**(css-color-adjust-1 「`color-scheme`」) |
| `color-scheme` 이 상속되는 속성인 것 | **명세**(같은 절) |
| `light-dark()` 가 **쓰이는 색 구성표**를 보는 것 | **명세**(css-color-5 「`light-dark()`」) |
| `light dark` 가 사용자 선호를 따르는 것 | **명세**(css-color-adjust-1) |
| `forced-colors` 에서 색 선언이 무시되는 것 | **명세**(css-color-adjust-1 「Forced Color Mode」) |
| **`rgb(18, 18, 18)`·`rgb(59, 59, 59)` 같은 구체적 색값** | **관찰**(Chrome 151). UA 스타일의 색은 구현이 정한다 |
| **스크롤바 트랙 `(44,44,44)`·막대 `(159,159,159)`** | **관찰**(Chrome 151 · 이 OS). 스크롤바는 플랫폼마다 다르다 |
| `only light` 의 계산값이 `light only` 인 것 | **관찰**(Chrome 151 직렬화) |
| **`--blink-settings=preferredColorScheme` 의 값 대응(0=dark)** | **관찰**(Chrome 151 의 내부 플래그). 공개 API 가 아니다 |
| 이 환경의 선호값(`reduced-motion: false` 등) | **환경**. 사람의 브라우저 값이 아니다 |
| Baseline — `color-scheme` widely · `light-dark()` newly | **2차 집계**(`api.webstatus.dev`) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 다크 모드를 지원한다 | `color-scheme: light dark` **+** 내 팔레트 두 벌 | 둘 중 하나만 |
| 폼·스크롤바가 안 따라온다 | `color-scheme` | 미디어 쿼리 안에서 입력칸 색을 손으로 칠하기 |
| 값 하나만 둘로 갈린다 | `light-dark()` | `@media` 블록을 통째로 하나 더 |
| 테마가 셋 이상이다 | 커스텀 속성 + `data-theme` | `light-dark()` |
| 사용자가 직접 고른 테마가 있다 | 루트에 `color-scheme` 도 같이 토글 | 색만 토글 |
| 급하게 어둡게만 하고 싶다 | 팔레트 두 벌 | `filter: invert(1)` |
| 모션·대비 접근성 | [목록의 **60번 주제**](../60-prefers-reduced-motion/) | 이 주제에서 처리 |

판단 규칙 두 줄.

- **「이 색을 누가 그리나」를 먼저 묻는다.** 내가 그리면 미디어 쿼리·`light-dark()`, 브라우저가 그리면 `color-scheme`.
- **기본값은 언제나 미디어 쿼리 밖에** 둔다. 선호가 「둘 다 아님」인 상태가 실제로 있다.

## demo — 저자 색 없이 브라우저가 다시 그린다

```html demo
<div class="pane light"><p>color-scheme: light</p><input value="입력칸"><button>버튼</button></div>
<div class="pane dark"><p>color-scheme: dark</p><input value="입력칸"><button>버튼</button></div>
<style>
  .pane { padding: 10px; font: 14px system-ui; }
  .light { color-scheme: light; }
  .dark  { color-scheme: dark; }
</style>
```

> **보이는 것** — 아래 판의 **입력칸과 버튼만** 어두운 회색 바탕에 흰 글씨로 바뀐다. 이 블록에는 색 선언이 **한 글자도 없다** — 바뀐 것은 전부 브라우저가 그리는 부분이다. 반대로 **두 문단의 글자색과 두 판의 배경은 똑같다**(둘 다 검정 글씨 · 투명 배경). 서브트리에 건 `color-scheme` 은 이미 상속돼 내려온 `color` 를 되돌리지 않기 때문이다.\
> **바꿔 볼 것** — `.dark` 의 `color-scheme: dark` 를 지우면 → **두 판이 완전히 똑같아진다** · 같은 선언을 `:root` 에 걸면 → **페이지 바탕과 스크롤바까지 어두워진다**

*(Chrome 151 headless 실측: `input` 배경 `rgb(255, 255, 255)` → `rgb(59, 59, 59)` · `input` 글자색 `rgb(0, 0, 0)` → `rgb(255, 255, 255)` · `button` 배경 `rgb(239, 239, 239)` → `rgb(107, 107, 107)` · 두 `<p>` 의 `color` 는 **둘 다** `rgb(0, 0, 0)` · 두 `.pane` 의 `background-color` 는 **둘 다** `rgba(0, 0, 0, 0)`. `:root` 판은 스크린샷 픽셀로 페이지 바탕 `(255,255,255)` → `(18,18,18)`, 스크롤바 트랙 `(252,252,252)` → `(44,44,44)`.)*

## 핵심 문장

- **`prefers-color-scheme` 은 묻고, `color-scheme` 은 시킨다.** 앞엣것은 조건이고 뒤엣것은 상속되는 속성이다.
- **미디어 쿼리만으로는 폼 컨트롤·스크롤바·페이지 바탕이 안 바뀐다.** 실측에서 선호만 dark 로 바꿨을 때 **아무 픽셀도 안 움직였다.**
- **`color-scheme: dark` 는 저자 CSS 없이 화면을 바꾼다.** 입력칸 배경이 `(255,255,255)` 에서 `(59,59,59)` 로, 스크롤바 트랙이 `(252,252,252)` 에서 `(44,44,44)` 로 갔다.
- **`light-dark()` 가 보는 것은 선호가 아니라 「쓰이는 색 구성표」** 다. `color-scheme` 없이 쓰면 **언제나 밝은 쪽**이 나온다(실측).
- **다크 모드는 색 뒤집기가 아니다.** 실측에서 사진 픽셀이 같이 뒤집혔고, 그림자가 바탕보다 밝아져 **후광**이 됐다.
- **선호가 「둘 다 아님」인 상태가 있다.** 기본값은 미디어 쿼리 밖에 둔다.
- **테스트 플래그를 믿지 말고 `matchMedia` 로 확인한다.** `--force-dark-mode` 는 `prefers-color-scheme` 을 안 바꿨다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 39번)
- [`../38-media-queries/2-summary.md`](../38-media-queries/2-summary.md) — **미디어 쿼리 문법의 정본.**\
  `and`/`not`/쉼표·경계값·명시도 이야기는 거기, 여기는 **`prefers-*` 기능이 무엇을 재고 `color-scheme` 과 어떻게 갈리나**만.
- [`../40-container-and-style-queries/2-summary.md`](../40-container-and-style-queries/2-summary.md) — 조상 상자를 재는 쪽. `@container style(--theme: dark)` 로 **테마를 조상에서 읽는** 방법이 거기 있다.
- [`../03-inheritance-and-global-keywords/2-summary.md`](../03-inheritance-and-global-keywords/2-summary.md) — 상속의 정본.\
  `color-scheme` 이 상속되는 것과 `color` 가 **이미 내려와 버린 것**이 여기서 갈린다.
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — UA 스타일이 **출처 사다리의 맨 아래**에 있다는 것. `color-scheme` 이 바꾸는 것이 바로 그 층이다.
- [`../41-supports-feature-queries/2-summary.md`](../41-supports-feature-queries/2-summary.md) — `CSS.supports('color', 'light-dark(red,blue)')` 로 지원을 묻는 방법.
- [목록의 **42번 주제**](../42-color-notation-and-spaces/)(색 표기와 색 공간) — 팔레트를 두 벌 만들 때의 색 선택. `oklch` 로 명도만 바꾸는 방법이 거기.
- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(모션·접근성) — **`prefers-reduced-motion`·`prefers-contrast`·`forced-colors` 의 정본.**\
  여기는 **존재와 뜻까지만** 쓴다.
- [`../../../../../../reference/render-rules.md`](../../../../../../reference/render-rules.md) — demo 블록 규칙. 모션 선호를 demo 안에 안 넣는 근거.

## 용어 풀이

- **`prefers-color-scheme`** — 사용자가 밝은/어두운 테마 중 무엇을 골랐는지 묻는 미디어 기능. **조건일 뿐이다.**
- **`color-scheme`** — 이 서브트리를 어느 색 구성표로 그릴지 브라우저에게 알리는 **상속되는 속성**.
- **쓰이는 색 구성표(used color-scheme)** — `color-scheme` 선언과 사용자 선호를 합쳐 요소마다 정해진 결과. `light-dark()` 가 보는 것.
- **UA 스타일(user agent style)** — 브라우저가 기본으로 그리는 것. 폼 컨트롤·스크롤바·페이지 바탕.
- **시스템 색(system color)** — `Canvas`·`CanvasText`·`ButtonFace` 같은 키워드. 쓰이는 색 구성표에 따라 값이 달라진다.
- **`light-dark()`** — 두 값 중 하나를 쓰이는 색 구성표에 따라 고르는 함수. Baseline **newly**.
- **`forced-colors`** — OS 의 강제 색 모드. 묻기만 하는 게 아니라 **내 색 선언을 실제로 갈아치운다.**
- **`prefers-reduced-motion`** — 움직임을 줄여 달라는 설정. 정본은 [목록의 **60번 주제**](../60-prefers-reduced-motion/).
- **대비비(contrast ratio)** — 두 색의 밝기 차이 비율. 뒤집기로는 보존되지 않는다.

## 더 들어가면

- **`color-scheme` 은 메타 태그로도 줄 수 있다** — `<meta name="color-scheme" content="light dark">`.
  실측: `content="dark"` 는 선호가 light 여도 페이지 바탕이 `(18,18,18)` 이었고, `content="light dark"` 는
  선호를 따라 `(255,255,255)` ↔ `(18,18,18)` 로 갈렸다 — **CSS 한 줄 없이 속성 선언과 같은 효과**다.
  ★ 다만 **`getComputedStyle(root).colorScheme` 은 그때도 `normal`** 이었다. 메타는 UA 에게 알릴 뿐
  CSS 속성값을 만들지 않는다 — **진단할 때 속성만 읽으면 못 본다.**
  CSS 파일이 도착하기 전에 첫 페인트가 이뤄지는 점 때문에 흰 화면 번쩍임을 줄이는 용도로 쓰이는데,
  **번쩍임 자체는 이 환경에서 못 쟀다**(첫 페인트 시점을 잡을 수단이 없었다).
- **사용자가 고른 테마를 저장하는 패턴**에서는 루트의 `color-scheme` 과 팔레트를 **같은 곳에서** 토글해야 한다. 실측이 보여 주듯 둘은 서로를 안 따라간다.
- **`forced-colors` 는 「무시된다」가 무섭다.** 색만으로 상태를 구별한 UI(빨간 테두리 = 오류)가 그 모드에서 **완전히 사라진다.** 아이콘·글자를 함께 쓰는 설계가 필요하고, 그 이야기는 [목록의 **60번 주제**](../60-prefers-reduced-motion/)다.
- **선호는 OS 가 정하고 브라우저가 옮긴다.** 그래서 같은 기계에서도 브라우저마다 답이 다를 수 있고, 헤드리스 자동화에서는 **기본값이 언제나 light** 였다(실측). 스냅샷 테스트를 짤 때 이것을 모르면 「우리 다크 모드는 테스트된 적이 없다」가 된다.
