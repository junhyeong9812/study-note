# css/syntax/60 — `prefers-reduced-motion` 과 모션 접근성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Media Queries Level 5](https://drafts.csswg.org/mediaqueries-5/) §12.1 「`prefers-reduced-motion`」 · [WCAG 2.2](https://www.w3.org/TR/WCAG22/) 의 2.3.3 Animation from Interactions(AAA)·2.2.2 Pause, Stop, Hide(A). 열어서 확인한 것만 적었다.
> **실행 검증** — 같은 문서를 **선호를 끈 판과 켠 판 두 번** 띄워 값을 대조했다. 선호는 **`--force-prefers-reduced-motion`** 으로 켰고, **`matchMedia('(prefers-reduced-motion: reduce)').matches` 로 켜졌는지 먼저 확인한 뒤** 측정했다. 하네스와 **한 번 헛다리를 짚은 기록**은 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 151.0.7922.173 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — `prefers-reduced-motion` 은 Baseline **widely**(newly 2020-01-15 → widely 2022-07-15). 엔진별로는 Safari 2017-03 · Firefox 2018-10 · Chrome 2019-04 — **이 갈래에서 가장 오래된 기능**이다. `api.webstatus.dev` 를 2026-09-23 에 직접 조회했다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 이 주제의 자리 — 이 갈래의 마무리

52\~59 는 전부 **「어떻게 움직이나」** 였다. 이 주제만 **「움직이지 말아야 할 때」** 다.

```text
  52 transition        두 값 사이를 걸어간다
  53 animation         여러 지점을 들른다
  54·55 transform      옮기고 돌리고 기울인다
  56 파이프라인         그 움직임이 무엇을 다시 돌리나
  57 @starting-style   나타나고 사라지는 순간
  58 스크롤 연동         진행률을 스크롤에서 받는다
  59 뷰 전환            화면 전체를 갈아 끼운다
  ------------------------------------------------
  60 (여기)            ★ 그 전부를 누구에게는 하지 말아야 한다
```

★ **[render-rules.md](../../../../../../reference/render-rules.md) 가 「모션 접근성은 demo 안에 넣지 말고 이 주제로 링크하라」고 정했다.**\
그래서 다른 주제들이 여기를 가리키고 있고 — **`prefers-reduced-motion` 을 쓰는 demo 는 이 문서에만** 있다.

## 한눈에 — 쉽게 말하면

**「끄기」 스위치가 아니라 「바꾸기」 요청이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 식당에서 「덜 맵게 해 주세요」 | `prefers-reduced-motion: reduce` |
| **음식을 안 주는 것** | `* { animation: none !important }` — 요청을 오해한 것 |
| 고추를 빼고 **다른 방법으로 간을 맞추는 것** | 이동·확대를 없애고 **불투명도 전환으로 대체** |
| 「맵기에 대해 말한 적 없음」 | `no-preference` — **「맵게 해 달라」가 아니다** |
| 애초에 안 맵게 내고 원하면 더하기 | `@media (prefers-reduced-motion: no-preference)` 로 **켜는** 설계 |

명세의 정의를 그대로 옮긴다. 이것은 **「줄이라」가 아니라 「없애거나 바꾸라」는 요청**이고, 대상이 한정돼 있다.

> The prefers-reduced-motion media feature is used to detect if the user has requested the system minimize the amount of **non-essential** motion it uses.

> **reduce** — Indicates that user has notified the system that they prefer an interface that **removes or replaces** the types of motion-based animation that either trigger discomfort for those with **vestibular motion sensitivity**, or distraction for those with **attention deficits**.

```text
  이 요청이 말하는 것                       이 요청이 말하지 않는 것
  +------------------------------+         +------------------------------+
  | 비본질적인 움직임을 최소화    |         | 모든 애니메이션을 끄기        |
  | 불편을 주는 '종류'를          |         | 상태 변화 피드백까지 없애기   |
  |   없애거나 '대체'하라         |         | 자동재생 영상·GIF 멈추기      |
  +------------------------------+         +------------------------------+
```

> **전정계(vestibular system)** — 귓속의 균형 감각 기관. 눈으로 본 움직임과 몸이 느낀 움직임이 어긋나면 어지럼·메스꺼움이 난다.\
> 예: 스크롤할 때 배경이 다른 속도로 따라오는 시차 효과가 대표적인 자극원이다.

> **비본질적(non-essential) 움직임** — 없어도 정보가 전달되는 움직임.\
> 예: 화면을 가로지르는 슬라이드는 비본질적이고, 로딩 진행률 표시는 본질적일 수 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **무엇을 남기고 무엇을 없애나.** 「전부 끄기」가 왜 답이 아닌가?
2. 기본값을 **정적으로 두는 설계**가 왜 더 나은가?
3. 이 미디어 기능이 **못 막는 것**은 무엇인가?

## 환경 확인 — 선호를 어떻게 켰나

이 주제는 **환경을 바꿔 가며 재는 것이 본체**라 측정 수단부터 밝힌다.

```text
  실측 — 같은 문서를 두 번 띄우고 matchMedia 를 먼저 읽었다

    판          플래그                              (reduce)   (no-preference)
    ------      --------------------------------    --------   ---------------
    선호 끔     (없음)                               false      true
    선호 켬     --force-prefers-reduced-motion       true       false     ★ 먹었다
```

- **플래그가 먹었다.** [39번 주제](../39-color-scheme-and-preferences/2-summary.md)의 실측(그 편에서는 `--force-dark-mode` 류가 전부 안 먹었다)과 같은 결론이다.
- **CDP `Emulation.setEmulatedMedia`** 로도 켜졌고 **끌 수도 있었다** — 한 브라우저 안에서 앞뒤로 바꿀 수 있어 대조에 더 편하다.
- ★ **두 판을 같은 디버깅 포트로 돌리다가 한 번 틀린 결론을 냈다.** 앞 브라우저가 포트를 놓기 전에 뒤 브라우저가 붙어 **앞 판을 다시 잰 것**이다. 그때 「플래그가 안 먹는다」가 나왔다. 판마다 포트를 갈랐더니 위 표가 나왔다. **자세한 것은 [3-answer.md](3-answer.md) 의 실행 검증 절.**

## 동작 방식

### (1) ★ CSS 는 아무것도 자동으로 해 주지 않는다

**언제 쓰나** — 가장 먼저 확인할 것. **선호를 켜도 내 애니메이션은 그냥 돈다.**

실측 — 아무 대응도 안 한 요소(`#a`)를 두 판에서 읽었다.

```text
                     선호 끔                        선호 켬
  #a  animation-name    slide                          slide        ★ 그대로다
      animation-duration  1s                             1s
      실행 중인 애니메이션  1개                            1개
      transition-property transform                    transform
```

- **브라우저는 선호를 「알려만」 준다.** `prefers-color-scheme` 이 화면을 안 바꾸는 것과 같은 구조다(정본은 [39번 주제](../39-color-scheme-and-preferences/2-summary.md)).
- **미디어 쿼리를 내가 쓰지 않으면 아무 일도 안 일어난다.**
- 이 점이 중요한 이유는 **테스트에서 「켰는데 그대로다」를 보고 「플래그가 안 먹네」로 오해하기 딱 좋기 때문**이다.\
  먼저 `matchMedia` 를 읽어 **선호가 켜졌는지**와 **내 CSS 가 반응했는지**를 갈라야 한다.

비용 — 없음.

### (2) ★★ 전면 차단의 문제 — 상태 변화까지 죽는다

**언제 쓰나** — 인터넷에 돌아다니는 「한 줄 해결책」을 붙이기 전에.

```css
/* 널리 복사되는 형태 */
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

실측 — 이 형태(`#b`)와 「줄이기」 형태(`#c`)를 같은 판에서 읽었다.

```text
                       선호 끔                          선호 켬
  #b 전면 차단   animation  slide                        none
                 transition-property  transform          ★ none      <- 모든 전환이 죽었다
                 transition-duration  1s                 0s
  #c 줄이기      animation  slide                        none
                 transition-property  transform, opacity  ★ opacity   <- 페이드만 남았다
                 transition-duration  1s, 1s              0.2s
```

```text
  전면 차단                              줄이기
  +--------------------------+          +--------------------------+
  | 이동 없음                 |          | 이동 없음                 |
  | 확대 없음                 |          | 확대 없음                 |
  | ★ 색 전환도 없음          |          | 색·불투명도 전환은 남김   |
  | ★ 열림/닫힘 피드백 없음   |          | 0.2초 페이드로 알려 줌    |
  +--------------------------+          +--------------------------+
     "무슨 일이 일어났는지 모른다"          "달라졌다는 것은 안다"
```

그림 해설 (한 단계씩):

- **`transition-property` 가 `none` 이 됐다.** 이 요소의 **어떤 전환도** 안 걸린다.
- 그래서 **토글이 켜졌는지, 항목이 선택됐는지, 오류가 떴는지**가 한 프레임에 툭 바뀐다.\
  움직임은 장식이기만 한 게 아니라 **상태가 바뀌었다는 신호**이기도 하다.
- 명세가 요청한 것은 **「제거하거나 대체(removes or replaces)」** 다. 대체할 여지를 남겨 두라는 뜻이다.
- ★ **그래도 전면 차단이 전혀 쓸모없지는 않다** — 남의 코드·서드파티 위젯처럼 **손댈 수 없는 것**에 마지막 수단으로 쓰인다.\
  내 코드에 쓰는 기본값으로 삼지 않을 뿐이다.

비용 — 없음.

### (3) 무엇을 남기고 무엇을 없애나

**언제 쓰나** — 실제로 무엇을 고칠지 고를 때. **이 주제의 실무 본체다.**

```text
  없애거나 대체한다 (전정계를 자극한다)      남긴다 (정보를 나른다)
  ------------------------------------      ------------------------------
  큰 거리의 이동 (화면을 가로지르는 슬라이드)  불투명도 전환 (페이드 인/아웃)
  확대·축소 (scale)                          색 전환 (상태 표시)
  회전 (rotate) · 3D 원근                     아주 짧은 이동 (수 px 이내)
  시차(parallax)                             진행률 표시 (그 자체가 정보)
  자동 회전 캐러셀                            포커스 링 같은 즉시 피드백
  화면 전체 뷰 전환 (59번)
```

- 가르는 기준은 「**크게 움직이나**」와 「**없으면 정보가 사라지나**」 둘이다.
- **불투명도는 특별대우를 받는다** — 위치가 안 변해서 전정계를 자극하지 않으면서 **「달라졌다」는 신호는 남긴다.**
- 그래서 실무 형태는 대개 이 모양이 된다.

```css
.card { transition: opacity .25s linear; }        /* 기본: 페이드만 */
@media (prefers-reduced-motion: no-preference) {  /* 선호가 없을 때만 */
  .card { transition: opacity .25s linear, transform .5s ease; }
  .card:hover { transform: translateX(120px) scale(1.2); }
}
```

비용 — 선언이 두 벌이 된다. 대신 **기본 코드가 안전한 쪽**이 된다 — 다음 절.

### (4) ★ `no-preference` 로 켜는 쪽이 나은 이유

**언제 쓰나** — 두 형태 중 어느 쪽으로 쓸지 정할 때.

```text
  ① reduce 에서 '끄는' 설계                 ② no-preference 에서 '켜는' 설계

  .card { transform: … 움직임 }             .card { /* 정적 */ }
  @media (reduce) {                          @media (no-preference) {
     .card { transform: none }                  .card { transform: … 움직임 }
  }                                          }

  기본값 = 움직임                            기본값 = 정적
  빠뜨리면 = 움직인다 ★                      빠뜨리면 = 안 움직인다 ✓
```

그림 해설 (한 단계씩):

- **어느 쪽이 「빠뜨렸을 때」 안전한가**로 고른다. ② 는 **새 애니메이션을 추가하면서 미디어 쿼리를 깜빡해도** 정적인 채로 남는다.
- ★ **선호가 「둘 다 아님」인 상태는 없다.** 실측에서 `reduce` 와 `no-preference` 가 **언제나 서로 반대**였다.\
  (39번 주제의 `prefers-color-scheme` 은 **둘 다 거짓인 제3의 상태**가 있었다 — 여기는 다르다.)
- 그래도 ② 가 나은 이유는 **누락에 강해서**이지 값이 애매해서가 아니다.

실측 — `no-preference` 로 켜는 형태(`#d`):

```text
                 선호 끔          선호 켬
  #d  animation   slide            none      <- 기본이 정적이라 아무것도 안 해도 된다
```

비용 — 없음.

### (5) ★ 이 미디어 기능이 **못 막는 것**

**언제 쓰나** — 「`prefers-reduced-motion` 을 다 걸었는데 아직 어지럽다」는 신고를 받았을 때.

```text
  CSS 안              |  CSS 밖 (이 기능이 못 막는다)
  --------------------+----------------------------------------
  transition          |  <video autoplay>  자동재생 영상
  animation           |  애니메이션 GIF·APNG
  transform           |  <canvas>·WebGL 로 그리는 것
                      |  JS 가 직접 돌리는 requestAnimationFrame 루프
                      |  스크롤 연동 애니메이션(58번) ★ 아래 참고
                      |  scroll-behavior: smooth   ★ 실측으로 확인
```

- **자동재생 영상·GIF 는 CSS 가 닿지 않는다.** `matchMedia` 를 JS 로 읽어 `<video>` 를 `paused` 로 두거나\
  `<picture>` 로 정지 이미지를 내주는 식으로 **저자가 직접** 해야 한다.
- **스크롤 연동 애니메이션(58번)** 은 성질이 반쯤 다르다 — 움직임이 **사용자의 손가락에 묶여 있어** 예상 못 한 자동 움직임이 없다.\
  그래도 **시차·확대는 여전히 자극원**이므로 `@media (prefers-reduced-motion: reduce)` 에서 `animation-timeline: none` 으로 끄거나 연출을 바꾼다.

★ **`scroll-behavior: smooth` 는 던져서 확인했다.** 결과가 예상과 달랐다.

```text
  실측 — html { scroll-behavior: smooth } 를 두고 같은 문서를 두 판에서

    방법                              선호 끔                      선호 켬
    ------------------------------    -------------------------    -------------------------
    scrollTo({behavior:'smooth'})     0.7초에 걸쳐 이동            ★ 0.7초에 걸쳐 이동 (그대로)
    앵커 이동 (location.hash)          0.7초에 걸쳐 이동            ★ 0.7초에 걸쳐 이동 (그대로)
    scrollingElement.scrollTop = n     즉시 점프                    즉시 점프
```

- **선호를 켜도 부드러운 스크롤이 그대로 돌았다.** 브라우저가 알아서 꺼 주지 않는다.
- 고치는 것은 저자의 몫이고, 실제로 먹는다.

```css
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
```

```text
  이 한 줄을 넣고 다시 잰 앵커 이동
    선호 끔   0.7초에 걸쳐 이동
    선호 켬   ★ 7ms 에 이미 목적지 (즉시 점프)
```

비용 — 없음.

## demo — 이동은 없애고 페이드는 남긴다

★ **이 문서는 예외다.** 다른 주제들이 「모션 접근성은 60번으로」 링크해 두었으므로 **여기에는 `prefers-reduced-motion` 을 쓰는 demo 가 있어야 한다.**

```html demo
<div class="card">마우스를 올려 보세요</div>
<style>
  .card { width: 160px; padding: 10px; background: #1d4ed8; color: #fff;
          font: 14px system-ui; opacity: .55; transition: opacity .25s linear; }
  .card:hover { opacity: 1; }
  @media (prefers-reduced-motion: no-preference) {
    .card { transition: opacity .25s linear, transform .5s ease; }
    .card:hover { transform: translateX(120px) scale(1.2); }
  }
</style>
```

> **보이는 것** — **모션 선호가 꺼진 보통 상태**에서는 마우스를 올리면 상자가 0.25초에 걸쳐 또렷해지면서(0.55 → 1) 동시에 0.5초에 걸쳐 **오른쪽으로 120px 이동하고 1.2배로 커진다.**\
> **OS/브라우저에서 「동작 줄이기」를 켜면** 이동과 확대가 **통째로 사라지고** 또렷해지는 변화만 남는다 — **상태가 바뀐 것은 여전히 보인다.**\
> 움직임은 마우스를 올린 동안만 일어나고, 떼면 되돌아온다.\
> **바꿔 볼 것** — `(prefers-reduced-motion: no-preference)` → `(prefers-reduced-motion: reduce)` 로 바꾸면 **의미가 정확히 뒤집혀** 선호를 켠 사람만 움직인다 · `.card` 의 `transition` 을 `none` 으로 두면 → 선호를 켠 판에서 **상태가 바뀐 신호가 아예 없어진다**(전면 차단이 하는 일이 이것이다)

*(Chrome 151 headless 실측 — 같은 문서를 두 판에서 띄우고 CDP 로 실제 마우스를 올렸다. 선호는 `--force-prefers-reduced-motion` 으로 켰고 `matchMedia` 로 확인했다:)*

```text
  선호 끔 (reduce = false)                          선호 켬 (reduce = true)
  transition-property: opacity, transform           transition-property: opacity

   t=9ms    opacity 0.580  translateX   2.29px       t=15ms   opacity 0.580  transform none
   t=142ms  opacity 0.820  translateX  61.60px       t=149ms  opacity 0.820  transform none
   t=277ms  opacity 1      translateX 103.32px       t=282ms  opacity 1      transform none
   t=541ms  opacity 1      translateX 120px (1.2배)  t=549ms  opacity 1      transform none

  바꿔 볼 것 ① (no-preference -> reduce)
    선호 끔 판   끝값 transform none          <- 안 움직인다
    선호 켬 판   끝값 translateX 120px 1.2배   <- 움직인다  (의미가 뒤집혔다)
```

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
/* ① 값은 둘뿐이다 */
@media (prefers-reduced-motion: no-preference) { … }
@media (prefers-reduced-motion: reduce)        { … }

/* ② 불 대수 문맥 — 값을 생략하면 'reduce 인가'를 묻는다 */
@media (prefers-reduced-motion) { … }      /* = reduce */

/* ③ 다른 조건과 묶기 */
@media (prefers-reduced-motion: no-preference) and (min-width: 40rem) { … }
```

```js
// ④ CSS 밖의 것(영상·GIF·JS 루프)은 JS 로 읽어서 직접 막는다
if (matchMedia('(prefers-reduced-motion: reduce)').matches) video.pause();
```

### 금지 사례 — 던져서 확인한 것

```css
/* ✗ 전면 차단을 기본 해법으로 — 상태 변화 피드백까지 죽는다 (transition-property: none) */
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}

/* ✗ scroll-behavior 를 잊기 — 선호를 켜도 부드러운 스크롤은 그대로 돈다 (실측) */

/* ✗ no-preference 를 '움직임을 원한다'로 읽기 — '말한 적 없음'이다 */
```

### 어디서 헷갈리나

- **`no-preference` 는 「움직여 달라」가 아니다.** 「이 항목에 대해 말한 적이 없다」는 뜻이다.\
  그래서 **`no-preference` 에서 켜는 설계**는 「원하는 사람에게만 준다」가 아니라 「**모르는 사람에게는 기본 연출을 준다**」로 읽는다.
- **`reduce` 는 「0 으로 만들라」가 아니다.** 명세 문구가 `removes or replaces` 다.
- **미디어 쿼리는 요소를 안 고른다.** 조건일 뿐이므로 **안쪽 규칙의 명시도가 바깥과 같아야** 이긴다. 정본은 [38번 주제](../38-media-queries/2-summary.md).
- **OS 설정 이름이 제각각이다** — macOS 「동작 줄이기」, Windows 「Windows에서 애니메이션 표시」, Android 「애니메이션 제거」. **한 스위치에 다 묶여 있지도 않다.**

## 어디서 틀리나

### 1. ★★ `* { animation: none !important }` 를 붙이고 끝낸다

`transition-property` 가 `none` 이 되어 **상태 변화 피드백까지 사라진다**(동작 방식 (2)).\
손댈 수 없는 서드파티에 쓰는 마지막 수단이지 내 코드의 기본값이 아니다.

### 2. 선호를 켜 보고 「플래그가 안 먹는다」고 결론 낸다

CSS 는 자동으로 아무것도 안 한다(동작 방식 (1)). **`matchMedia` 를 먼저 읽어** 「선호가 켜졌나」와 「내 CSS 가 반응했나」를 갈라야 한다.

### 3. `scroll-behavior: smooth` 를 잊는다

선호를 켜도 **그대로 돈다**(실측). `@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto } }` 를 따로 넣는다.

### 4. 영상·GIF 를 CSS 로 막으려 한다

**닿지 않는다.** `matchMedia` 를 JS 로 읽어 `pause()` 하거나 정지 이미지를 내준다.

### 5. `reduce` 에서 「끄는」 설계만 쓴다

새 애니메이션을 추가하면서 미디어 쿼리를 깜빡하면 **그대로 움직인다.** `no-preference` 에서 켜는 쪽이 누락에 강하다.

### 6. 접근성 대응을 「기능 축소」로 본다

`reduce` 를 켠 사용자는 **콘텐츠가 덜 필요한 사람이 아니다.** 정보는 그대로 두고 **전달 수단만 바꾼다.**

### 7. WCAG 가 이 미디어 쿼리를 요구한다고 생각한다

WCAG 2.3.3 은 「**끌 수 있게 하라**」는 AAA 기준이고 **수단을 지정하지 않는다.**\
`prefers-reduced-motion` 은 그 요구를 만족시키는 **가장 싼 수단 중 하나**일 뿐이다 — 페이지 안의 토글도 유효한 수단이다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `reduce` 의 뜻이 **「removes or replaces」** 인 것 | **명세**(mediaqueries-5 §12.1, 위 인용) |
| 값이 `no-preference`/`reduce` 둘뿐인 것 | **명세** |
| **브라우저가 자동으로 안 꺼 주는 것** | **명세의 설계**(미디어 기능은 묻기만 한다) + Chrome 151 실측 |
| `scroll-behavior: smooth` 가 **안 꺼지는 것** | **Chrome 151 실측.** 명세가 끄라고 요구하지 않는다 |
| `reduce` 와 `no-preference` 가 **언제나 서로 반대**인 것 | **이 환경의 관찰**이다. 39번 주제에서 `prefers-color-scheme` 은 **둘 다 거짓**인 판이 있었다 |
| 어떤 OS 설정이 이 값을 켜는지 | **플랫폼마다 다르다.** 이름도 묶임도 제각각이다 |
| `--force-prefers-reduced-motion` 이 먹는 것 | **공개 API 가 아니다.** 버전이 오르면 다시 던져 봐야 한다 |
| 이 환경의 기본값이 `no-preference` 인 것 | **환경**. 사람의 브라우저 값이 아니다 |
| 전환 시각(±1프레임) | 측정 환경 |

## 언제 쓰고 언제 안 쓰나

| 움직임 | `reduce` 에서 | 왜 |
|---|---|---|
| 화면을 가로지르는 슬라이드 인 | **페이드로 대체** | 큰 이동이 전정계를 자극한다 |
| `scale`·`rotate` 강조 | **없앤다** | 〃 |
| 시차 배경 | **없앤다** | 대표적인 자극원 |
| 자동 회전 캐러셀 | **멈춘다**(WCAG 2.2.2 도 요구) | 자동 + 반복 + 큰 이동 |
| 뷰 전환(59번) | **크로스페이드만 남긴다** | 화면 전체가 움직인다 |
| 호버·포커스 색 전환 | **남긴다** | 위치가 안 변하고 정보를 나른다 |
| 0.2초 페이드 인/아웃 | **남긴다** | 대체 수단으로 쓰는 쪽이다 |
| 진행률 막대 | **남긴다** | 움직임 자체가 정보다 |
| 스크롤 연동(58번) | **연출에 따라** | 손가락에 묶여 있지만 시차·확대는 여전히 자극원 |

## 핵심 문장

- **`reduce` 는 「끄라」가 아니라 「없애거나 바꾸라」다.** 명세 문구가 `removes or replaces` 다.
- **대상이 한정돼 있다** — 전정계를 자극하거나 주의를 흩뜨리는 **종류의** 움직임이다.
- **브라우저는 아무것도 자동으로 안 해 준다.** 미디어 쿼리를 내가 써야 한다.
- **전면 차단은 상태 변화 피드백까지 죽인다.** 이동·확대는 없애고 **불투명도는 남긴다.**
- **`no-preference` 에서 켜는 쪽이 누락에 강하다.** 기본값이 정적이 된다.
- **영상·GIF·JS 루프·`scroll-behavior` 는 이 기능이 못 막는다.** 저자가 직접 걸러야 한다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 60번, 이 갈래의 마지막)
- [`../39-color-scheme-and-preferences/2-summary.md`](../39-color-scheme-and-preferences/2-summary.md) — **사용자 선호 일반의 정본.**\
  선호 미디어 기능이 **묻기만 한다**는 구조·`color-scheme` 과의 차이·선호를 바꾸는 플래그 실측은 **거기까지**,\
  여기는 **`prefers-reduced-motion` 한 축**만.\
  ★ `prefers-contrast`·`forced-colors` 는 **이 60주제 목록에 정본이 없다**(39번을 그렇게 고쳐 두었다) —
  이 주제의 축은 **모션 하나**이고 그 둘은 색·대비 쪽이라 성격이 다르다. **다음 라운드의 몫이다.**
- [`../38-media-queries/2-summary.md`](../38-media-queries/2-summary.md) — 미디어 쿼리 문법의 정본. `and`/`not`·불 대수 문맥·명시도는 거기.
- [`../52-transition/2-summary.md`](../52-transition/2-summary.md) — 전환의 정본. **대체 수단으로 남기는 불투명도 전환**이 거기서 온다.
- [목록의 **53번 주제**](../53-keyframes-and-animation/)(`@keyframes`·`animation`) — 없애는 대상의 대부분. `animation: none` 으로 끄는 형태.
- [목록의 **54번 주제**](../54-transform-2d-and-origin/)(`transform`) — `translate`·`scale`·`rotate` 가 자극원의 본체다.
- [`../57-starting-style-and-entry-exit-transitions/2-summary.md`](../57-starting-style-and-entry-exit-transitions/2-summary.md) — 진입·퇴장 연출. 이동을 빼고 페이드만 남기면 된다.
- [`../58-scroll-driven-animations/2-summary.md`](../58-scroll-driven-animations/2-summary.md) — **이 기능이 자동으로 못 막는 쪽.** 손가락에 묶여 있어도 시차·확대는 걸러야 한다.
- [`../59-view-transitions/2-summary.md`](../59-view-transitions/2-summary.md) — 화면 전체가 움직이는 연출. 특히 줄일 대상.
- [`../../../../../../reference/render-rules.md`](../../../../../../reference/render-rules.md) — **demo 블록 규칙.**\
  「모션 접근성은 demo 안에 넣지 말고 이 주제로 링크하라」가 거기 있고, **그래서 이 문서가 그 예외다.**
- [`../../../../../engineering/development-standards/quality-standards/`](../../../../../engineering/development-standards/quality-standards/) — ISO 25010 의 포용성(inclusivity) 항목.\
  품질 모델의 어휘는 거기, 여기는 **구체 표면과 대체 모션 설계**.

## 용어 풀이

- **`prefers-reduced-motion`** — 사용자가 「비본질적인 움직임을 최소화」해 달라고 시스템에 알렸는지 묻는 미디어 기능. **조건일 뿐이다.**
- **`reduce`** — 불편·주의 산만을 유발하는 종류의 움직임을 **없애거나 대체**해 달라는 값.
- **`no-preference`** — 이 항목에 대해 **말한 적이 없다**는 값. 「움직여 달라」가 아니다.
- **전정계(vestibular system)** — 귓속의 균형 감각 기관. 본 것과 느낀 것이 어긋나면 어지럼이 난다.
- **비본질적(non-essential) 움직임** — 없어도 정보가 전달되는 움직임.
- **전면 차단** — `* { animation: none !important }` 식으로 모든 움직임을 끄는 패턴. 상태 변화 피드백까지 죽는다.
- **WCAG 2.3.3 Animation from Interactions** — 상호작용으로 생기는 모션 애니메이션을 **끌 수 있어야 한다**는 AAA 기준.
- **WCAG 2.2.2 Pause, Stop, Hide** — 움직이거나 깜빡이거나 자동 갱신되는 정보에 대한 A 기준.
- **`scroll-behavior: smooth`** — 스크롤 이동을 부드럽게 만드는 속성. **선호를 켜도 자동으로 안 꺼진다.**
- **`matchMedia()`** — 미디어 쿼리를 JS 로 읽는 함수. CSS 가 못 닿는 영상·GIF·JS 루프를 거를 때 쓴다.

## 더 들어가면

- **페이지 안에 토글을 두는 것**도 WCAG 2.3.3 을 만족시키는 유효한 수단이다. OS 설정을 못 바꾸는 사용자(공용 PC 등)를 위해 둘을 같이 두는 사이트가 있다.
- `prefers-reduced-motion` 은 **사용자를 식별하는 신호로 쓰일 수 있다**(핑거프린팅). 그래서 브라우저가 값을 제한하는 모드가 있을 수 있다 — **이 환경에서는 확인하지 않았다.**
- 같은 가족의 다른 선호로 **`prefers-reduced-transparency`**(Baseline limited, 2026-09-23 조회 기준 Chromium 계열만)와 `prefers-reduced-data` 가 있다. **이 문서에서 값을 재지 않았다.**
- 애니메이션을 **완전히 없애는 대신 지속을 0.01초로 만드는** 관용구(`animation-duration: 0.01ms !important`)가 있다. `animationend` 이벤트에 로직이 걸린 코드를 안 깨뜨리려는 꼼수다 — **의도를 알고 쓰면 유용하지만 전면 차단의 변형**이라는 점은 같다.
