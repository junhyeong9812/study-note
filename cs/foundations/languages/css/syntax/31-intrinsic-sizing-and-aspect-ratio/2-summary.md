# css/syntax/31 — 내재적 크기(`min-content`/`max-content`/`fit-content`)와 `aspect-ratio` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Box Sizing Level 3](https://drafts.csswg.org/css-sizing-3/) (내재적 크기 키워드·`min-width: auto`) · [CSS Box Sizing Level 4](https://drafts.csswg.org/css-sizing-4/) (`aspect-ratio`·`fit-content()`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 치수는 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 잰 값이다. 선언이 **담겼는지**는 `document.styleSheets[…].cssRules` 로 따로 확인했다(진단 3창의 첫째 창).\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 엔진 차이는 주장하지 않는다.
> **버전** — `min-content`/`max-content` 는 Baseline **widely**(newly 2020-01-15 → widely 2022-07-15) · `fit-content` **키워드**는 **widely**(2021-11-02 → 2024-05-02) · `aspect-ratio` 는 **widely**(2021-09-20 → 2024-03-20) · ★ **`fit-content()` 함수는 `width`/`height` 에서 Baseline `limited` 다**(아래 (5)에서 실측으로도 확인했다). 전부 `api.webstatus.dev` 조회값이다.
> **여기서 다루지 않는 것** — Grid 의 `fr`·`minmax()` 는 [목록의 **27번 주제**](../27-grid-track-sizing/)다. 여기서는 **내재적 크기 키워드**까지만 다룬다. 박스 모델과 `box-sizing` 은 [15번](../15-box-model-and-box-sizing/), flex 항목 크기 해결은 [25번](../25-flex-shorthand-and-sizing/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**「내용만큼」에는 두 가지 뜻이 있다 — 「최대한 쥐어짜서」와 「한 줄로 쭉 펴서」.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 빨랫줄에 널 옷가지 | 상자 안의 내용(글·이미지) |
| 옷을 최대한 접어 쌓았을 때 필요한 폭 | **`min-content`** — 더는 쪼갤 수 없는 조각의 크기 |
| 옷을 한 줄로 쭉 늘어놓았을 때 필요한 폭 | **`max-content`** — 줄바꿈 없이 전부 |
| 방이 좁으면 접고, 넓으면 늘어놓되 방보다 크게는 안 편다 | **`fit-content`** — 둘 사이에서 방 크기에 맞춘다 |
| 액자 비율을 고정하고 한 변만 재는 것 | **`aspect-ratio`** — 한 축이 정해지면 다른 축이 따라온다 |

- **`min-content` ≤ `fit-content` ≤ `max-content`.** 셋은 항상 이 순서다.
- `fit-content` 는 독립된 크기가 아니라 **공식**이다 — `min(max-content, max(min-content, 쓸 수 있는 공간))`.
- ★ **이 키워드들은 [25번](../25-flex-shorthand-and-sizing/)의 사고를 푸는 열쇠이기도 하다.** flex 항목의 `min-width: auto` 가 **`min-content` 로 풀리는** 것이 「본문이 컨테이너를 뚫는」 원인이었다.

```text
같은 글 "hi javascript ok" 를 담은 상자를 세 가지로 재면 (부모 400px)

min-content = 80.00                max-content = 128.02
+----------+                       +------------------+
|hi        |                       |hi javascript ok  |
|javascript|   <- 세 줄이 된다       +------------------+
|ok        |                        <- 한 줄로 쭉
+----------+

fit-content = 128.02  (부모가 400 이라 max-content 가 그대로 들어간다)
width: auto  = 400.00 (블록은 부모를 꽉 채운다 — 내재적 크기가 아니다)
```

실무에서 이게 터지는 자리는 **버튼·배지·툴팁**이다.\
「글자 길이만큼만 넓은 상자」를 만들려고 `width: auto` 를 썼는데 **블록이라 부모를 꽉 채운다.**\
답은 `width: fit-content` 이고, 그것이 `float`·`position: absolute`·`inline-block` 에서 `auto` 가 하던 일과 같다 — (6)이 그 정본이다.

> **내재적 크기(intrinsic size)** — 부모가 얼마나 넓은지와 **무관하게** 내용만으로 정해지는 크기.\
> 예: 글 상자의 `max-content` 는 부모가 100px 든 1000px 든 128.02px 로 같다.

> **외재적 크기(extrinsic size)** — 부모가 준 공간을 기준으로 정해지는 크기.\
> 예: 블록 상자의 `width: auto` 나 `width: 50%` 는 부모가 바뀌면 같이 바뀐다.

> **줄바꿈 기회(soft wrap opportunity)** — 글을 쪼갤 수 있는 자리. 공백·하이픈이 대표다.\
> 예: `white-space: pre` 면 줄바꿈 기회가 없어 `min-content` 와 `max-content` 가 **같아진다**.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 「내용만큼」의 두 가지 뜻은 **수치로 얼마나 다른가** — 그리고 무엇이 그 차이를 만드나.
2. `width: auto` 와 `width: fit-content` 는 **언제 갈리고 언제 같은가.**
3. `aspect-ratio` 는 어느 축을 기준으로 다른 축을 정하고, **언제 그 비율이 깨지나.**

## 동작 방식

### (1) 세 키워드를 같은 글로 재 본다

**언제 쓰나** — 「내용만큼」이라는 말이 나올 때마다. **어느 쪽 뜻인지 먼저 정해야 한다.**

`hi javascript ok` 를 담은 상자를 **부모 400px** 안에서 네 가지로 쟀다.

```text
선언                  폭        높이     무슨 일이 일어났나
width: min-content    80.00    72.00    세 줄로 접혔다 ("hi" / "javascript" / "ok")
width: max-content   128.02    24.00    한 줄로 쭉 폈다
width: fit-content   128.02    24.00    max-content 가 400 보다 작아 그대로 들어갔다
width: auto          400.00    24.00    블록이라 부모를 꽉 채웠다 (내재적 크기가 아니다)

낱말 폭을 따로 재 보면
  "hi"               =  16.02
  "javascript"       =  80.02     <- min-content(80.00)가 이 낱말과 맞는다
  "ok"               =  16.02
  "hi javascript ok" = 128.02     <- max-content 가 이것과 맞는다
```

*(Chrome 151 headless 실측 — 글꼴은 `16px monospace`. 낱말 폭은 `position: absolute; white-space: pre` 인 `<span>` 으로 따로 쟀다. `min-content` 80.00 과 낱말 폭 80.02 의 0.02 차이는 측정 방식이 다른 데서 온다 — 상자 쪽은 레이아웃 결과, 낱말 쪽은 인라인 상자의 폭이다.)*

```html demo
<div class="p"><div class="a">hi javascript ok</div></div>
<div class="p"><div class="b">hi javascript ok</div></div>
<div class="p"><div class="c">hi javascript ok</div></div>
<style>
  .p { width: 400px; background: #eee; margin-bottom: 6px; font: 16px monospace; }
  .p > div { background: #bfdbfe; outline: 1px solid #333; }
  .a { width: min-content; }    /* 가장 긴 낱말만큼 */
  .b { width: max-content; }    /* 줄바꿈 없이 전부 */
  .c { width: fit-content; }    /* 둘 사이에서 부모에 맞춰 */
</style>
```

> **보이는 것** — 위 상자는 **세로로 길쭉하고**(`hi` / `javascript` / `ok` 가 세 줄) 폭이 `javascript` 만큼이다. 가운데와 아래 상자는 **한 줄이고 폭이 똑같다** — 부모(400px)가 넉넉해서 `fit-content` 가 `max-content` 와 같아졌다.\
> **바꿔 볼 것** — `.p` 의 `width` 를 `80px` 로 줄이면 → **가운데(`max-content`)만 부모를 뚫고 나가고** `fit-content` 는 부모 안에서 접힌다 · `.c` 를 `width: auto` 로 → 부모를 꽉 채운다

*(Chrome 151 headless 실측 — 위 블록 그대로: 80.00×72.00 / 128.02×24.00 / 128.02×24.00. 부모를 80px 로 줄인 판에서 `fit-content` 는 80.00×48.00, `auto` 도 80.00×48.00 이었다.)*

그림 해설 (한 단계씩):

- `min-content` 는 **「더는 쪼갤 수 없는 조각 중 가장 큰 것」** 이다. 글에서는 대개 가장 긴 낱말.
- `max-content` 는 **「줄바꿈을 한 번도 안 했을 때」** 다.
- `fit-content` 는 둘 사이 값이고 **부모 크기에 달렸다** — 그래서 셋 중 **유일하게 외재적 요소가 섞인다.**
- `width: auto` 는 **블록에서 내재적 크기가 아니다.** 부모를 채운다. (6)에서 이 예외를 다룬다.

비용 — 내재적 크기는 **내용을 한 번 재야** 알 수 있다. 레이아웃 비용이 `auto` 보다 크고, 내용이 바뀌면 다시 재야 한다.

### (2) `fit-content` 는 크기가 아니라 공식이다

**언제 쓰나** — `fit-content` 가 어떤 값이 될지 예측할 때.

```text
fit-content = min( max-content , max( min-content , 쓸 수 있는 공간 ) )

  ①  쓸 수 있는 공간이 max-content 보다 크다  ->  max-content 가 된다
      부모 400, max-content 128.02           ->  128.02

  ②  쓸 수 있는 공간이 둘 사이에 있다          ->  쓸 수 있는 공간이 된다
      부모 80, min 80.00 ~ max 128.02        ->  80.00

  ③  쓸 수 있는 공간이 min-content 보다 작다   ->  min-content 가 된다 (뚫는다)
```

*(Chrome 151 headless 실측 — ①: 부모 400px 에서 `fit-content` = 128.02(높이 24, 한 줄). ②: 부모 80px 에서 `fit-content` = 80.00(높이 48, 두 줄).)*

```text
수직선으로 보면

  0        min-content(80)        max-content(128.02)
  |------------|----------------------|------------------->  쓸 수 있는 공간
               ↑          ↑           ↑
            부모가 좁으면   부모가 중간   부모가 넓으면
            min 으로 고정   부모 크기     max 로 고정
```

- 그래서 **`fit-content` 는 절대 `max-content` 보다 커지지 않는다.** 「내용보다 넓어지지 않는 상자」가 필요할 때 쓰는 값이다.
- 그리고 **`min-content` 보다 작아지지도 않는다** — 좁은 부모에서는 뚫는다. [25번](../25-flex-shorthand-and-sizing/)의 바닥과 같은 성질이다.

### (3) 무엇이 `min-content` 를 정하나 — 줄바꿈 기회

**언제 쓰나** — 「왜 이 상자가 이만큼 아래로는 안 줄어드나」를 따질 때.

```text
같은 길이의 글인데 min-content 가 다르다

"hi javascript ok"          min-content =  80.00   (가장 긴 낱말 "javascript")
"hi flex-basis ok"          min-content =  40.00   (하이픈에서 쪼개진다!)
<pre>GET /api/v1/users/12345/preferences</pre>
                            min-content = 280.02   (줄바꿈 기회가 없다)
                            max-content = 280.02   (둘이 같다)
```

*(Chrome 151 headless 실측 — `hi flex-basis ok` 의 `min-content` 상자는 폭 40.00 · 높이 96.00 으로 **네 줄**이 됐다. `"flex-"` 와 `"basis"` 의 폭을 따로 재니 각각 40.02 로 같았다. `<pre>` 판은 `min-content` 와 `max-content` 가 둘 다 280.02 였다.)*

```text
하이픈이 쪼개지는 자리

  "flex-basis"  ->  min-content 는 "flex-basis" 가 아니라
                    +-------+          +-------+
                    | flex- |   그리고  | basis |
                    +-------+          +-------+
                    둘 중 큰 것(40.02) 이다
```

- ★ **하이픈은 줄바꿈 기회다.** `flex-basis`·`e-mail` 같은 식별자가 든 글의 `min-content` 는 **생각보다 작다.**
- 반대로 `white-space: pre`(또는 `nowrap`)면 **줄바꿈 기회가 하나도 없어** `min-content` = `max-content` 가 된다.
- **이 등식이 「쪼갤 수 없다」의 신호**다. [25번](../25-flex-shorthand-and-sizing/)의 `<pre>` 사고를 진단하는 방법이기도 하다.

비용 — 없다. 다만 **줄바꿈 규칙은 언어와 속성에 달렸다**(`word-break`·`overflow-wrap`·`hyphens`). 그 정본은 [목록의 **51번 주제**](../51-text-wrapping-and-decoration/)다.

### (4) ★ 25번의 `min-width: auto` 가 여기서 풀린다

**언제 쓰나** — flex·grid 항목이 안 줄어들 때.

```text
[25번] flex 항목의 min-width 기본값 = auto
              ↓  (css-sizing-3 의 자동 최소 크기)
[31번] auto 는 대개 **min-content** 로 풀린다
              ↓
       그래서 항목은 min-content 아래로 못 내려간다
              ↓
       <pre> 처럼 min-content = max-content 인 내용이면
       **한 픽셀도 안 줄어들고 컨테이너를 뚫는다**
```

*(Chrome 151 headless 실측 — 같은 `<div>` 의 `getComputedStyle().minWidth`: flex 항목일 때 `auto`, grid 항목일 때 `auto`, 일반 블록 자식일 때 `0px`. `min-height` 도 같은 값이었다.)*

| 상자 | `min-width` 기본값 | 뜻 |
|---|---|---|
| 일반 블록 자식 | `0px` | 0 까지 줄어든다 |
| **flex 항목** | `auto` | 대개 `min-content` 가 바닥 |
| **grid 항목** | `auto` | 대개 `min-content` 가 바닥 |

- **`min-content` 가 무엇인지 모르면 25번의 사고를 못 고친다.** 두 주제가 이 한 줄로 이어진다.
- 고치는 법은 바닥을 내리는 것(`min-width: 0`) 또는 **내용의 `min-content` 를 줄이는 것**(`overflow-wrap: anywhere` 등)이다.

### (5) ★★ `fit-content` 키워드는 되고 `fit-content()` 함수는 안 된다

**언제 쓰나** — 「최대 150px 까지만 늘어나는 내용 크기 상자」를 만들려 할 때.

`fit-content(150px)` 는 「공식의 「쓸 수 있는 공간」 자리에 150px 를 넣어라」라는 뜻이다. **써 봤다.**

```text
진단 3창의 첫째 창 — 규칙이 담겼나

  #fc { }                        <- width: fit-content(150px)   버려졌다
  #mc { width: min-content; }    <- width: min-content          담겼다
  #zz { }                        <- width: bogus-content        버려졌다 (대조군)

둘째·셋째 창은 볼 필요가 없다 — 담기지도 않았다.
실제 렌더 폭도 400.00 으로 width: auto 와 같았다 (선언이 없는 것과 같다).
```

*(Chrome 151 headless 실측 — `cssRules` 로 규칙 본문을 읽은 결과. `fit-content(150px)` 는 **존재하지 않는 값 `bogus-content` 와 구분되지 않는다.** `fit-content(600px)`·`fit-content(50px)` 도 모두 400.00 으로 같았다.)*

- ★ **Baseline 데이터와도 일치한다** — `api.webstatus.dev` 조회에서 `fit-content()` 는 **`limited`**(newly 날짜 없음)이고, 키워드 `fit-content` 는 **`widely`**(2021-11-02 → 2024-05-02)다. 근거가 둘이다.
- ★★ **에러가 없는 언어의 전형**이다. 「쓸 수 있는데 안 먹네」가 아니라 **아예 안 담겼다.** 화면도 콘솔도 말해 주지 않고, `getComputedStyle` 로 보면 `400px` 라는 그럴듯한 숫자가 돌아온다.
- 같은 일을 지금 하려면 **`width: fit-content; max-width: 150px`** 로 나눠 쓴다.
- Grid 트랙에서의 `fit-content()` 는 **다른 자리**이고 지원 상황도 다르다 — [목록의 **27번 주제**](../27-grid-track-sizing/)가 정본이다.

### (6) `width: auto` 와 `fit-content` 가 갈리는 자리

**언제 쓰나** — 「글자 길이만큼만 넓은 상자」를 만들 때.

같은 글을 담은 상자를 **상자 종류만 바꿔** 쟀다.

```text
상자 종류                   width: auto 의 결과      fit-content 와 같은가
블록 (display: block)       400.00  (부모를 채운다)   ✗ 다르다
float: left                 128.02                  ✓ 같다
position: absolute          128.02                  ✓ 같다
display: inline-block       128.02                  ✓ 같다

(부모 400px, 그 글의 fit-content = 128.02)
```

*(Chrome 151 headless 실측 — 네 판을 같은 문서에서 같은 부모 안에 넣고 쟀다.)*

```text
왜 갈리나 — auto 의 뜻이 상자마다 다르다

  블록 상자            "남은 폭을 전부 채워라"   (채움 · fill-available 쪽)
  float/absolute/     "쥐어짜서 맞춰라"          (축소 맞춤 · shrink-to-fit)
  inline-block          = 바로 fit-content 공식
```

- **`width: auto` 는 하나의 규칙이 아니다.** 상자 종류가 뜻을 바꾼다.
- **`fit-content` 는 상자 종류와 무관하게 늘 축소 맞춤이다.** 그래서 블록에서 `float` 흉내를 내려고 `display: inline-block` 을 쓰던 관용구를 대체한다.
- flex·grid 항목의 크기는 또 다른 규칙이다 — [25번](../25-flex-shorthand-and-sizing/)과 [목록의 **27번 주제**](../27-grid-track-sizing/).

비용 — 축소 맞춤은 **내용을 두 번 재야** 한다(`min-content` 와 `max-content`). 블록의 `auto` 보다 비싸다.

### (7) `aspect-ratio` — 한 축을 주면 다른 축이 따라온다

**언제 쓰나** — 이미지 자리·비디오 자리·정사각 카드처럼 **비율이 정해진 상자**를 만들 때.

```text
선언                                   결과 (부모 400px)      w/h
aspect-ratio: 16/9;  width: 320px      320.00 × 180.00       1.778  ✓
aspect-ratio: 16/9;  height: 90px      160.00 ×  90.00       1.778  ✓
aspect-ratio: 16/9;  둘 다 auto (블록)   400.00 × 225.00       1.778  ✓
aspect-ratio: 16/9;  width:320 height:200
                                       320.00 × 200.00       1.600  ✗ 무시된다
aspect-ratio: auto (초기값)             400.00 ×  24.00       —      비율 없음
```

*(Chrome 151 headless 실측. 셋째 줄은 블록의 `width: auto` 가 400 으로 정해진 뒤 높이가 400 ÷ (16/9) = 225 로 따라온 것이다.)*

```text
어느 축이 기준인가

  width 만 있다   ──> width 를 기준으로 height 를 만든다
  height 만 있다  ──> height 를 기준으로 width 를 만든다
  둘 다 auto     ──> 그 상자의 평소 규칙으로 한 축이 먼저 정해지고, 나머지가 따라온다
                     (블록이면 width 가 먼저 — 부모를 채운다)
  둘 다 지정      ──> **aspect-ratio 는 무시된다**
```

```html demo
<div class="p"><div class="r">16 / 9</div></div>
<style>
  .p { width: 320px; background: #eee; font: 14px monospace; }
  .r { aspect-ratio: 16 / 9;      /* 폭만 정해도 높이가 따라온다 */
       background: #bfdbfe; outline: 1px solid #333; }
</style>
```

> **보이는 것** — 높이를 한 글자도 안 썼는데 상자가 **가로로 긴 직사각형**이 된다. 부모 폭 320px 에 맞춰 높이가 180px 로 잡힌다(글자 한 줄 높이가 아니다).\
> **바꿔 볼 것** — `16 / 9` → `1 / 1` → **정사각형**(320×320)이 된다 · `.r` 에 `width: 160px` 를 추가 → 폭이 절반이 되고 **높이도 90px 로 같이 줄어든다**

*(Chrome 151 headless 실측 — 이 블록 그대로: 320.00 × 180.00, w/h = 1.778(16/9 = 1.778). `1 / 1` 로 바꾼 판은 320.00 × 320.00.)*

### (8) ★ 내용이 넘치면 비율이 깨진다

**언제 쓰나** — 비율 상자에 텍스트를 넣을 때. **「가끔만 깨져서」 늦게 발견되는 자리다.**

`aspect-ratio: 1/1; width: 120px` 인 상자에 **내용 길이만 바꿔** 쟀다.

```text
내용                                 결과            w/h      깨졌나
짧은 내용                            120.00×120.00   1.000    ✓ 지켜짐
아주 긴 내용(여러 줄)                  120.00×168.00   0.714    ✗ 깨짐
  + min-height: 0                   120.00×120.00   1.000    ✓ 고쳐짐 (scrollHeight 168)
  + overflow: hidden                120.00×120.00   1.000    ✓ 고쳐짐 (scrollHeight 168)
  + overflow: auto                  120.00×120.00   1.000    ✓ 고쳐짐 (scrollHeight 192)
```

*(Chrome 151 headless 실측 — 네 고침 판 모두 `scrollHeight` 가 120 보다 크다. **내용은 여전히 넘치고 상자만 비율을 지킨 것**이다. `overflow: auto` 판의 192 는 가로 스크롤바 자리가 더해진 값이다.)*

```text
왜 깨지나

  aspect-ratio 로 정해지는 축(여기서는 높이)에는
  **내용 기반 최소 크기**가 걸려 있다.
  내용이 그보다 크면 상자가 늘어나고 비율이 진다.

  깨지기 전                        깨진 뒤
  +--------+  120                +--------+  120
  |        |                     |        |
  |  120   |                     |  168   |   <- 내용이 밀어 올렸다
  |        |                     |        |
  +--------+                     |        |
                                 +--------+
```

```html demo
<div class="card">짧음</div>
<div class="card">아주 긴 내용이 여러 줄로 늘어나서 상자의 높이를 넘어서면 상자가 어떻게 되는지 수치로 확인해 본다 이만큼 길게</div>
<style>
  .card { aspect-ratio: 1 / 1; width: 120px; font: 16px monospace;
          background: #bfdbfe; outline: 2px solid #c00; margin-bottom: 60px; }
</style>
```

> **보이는 것** — 위 상자는 **정사각형**인데, 아래 상자는 같은 선언인데도 **세로로 길쭉한 직사각형**이다. 글자가 상자 아래를 밀어 키운 것이다.\
> **바꿔 볼 것** — `.card` 에 `min-height: 0` 을 추가 → 아래 상자도 **정사각형이 되고 글자가 상자 밖으로 넘쳐 나온다** · `min-height: 0` 대신 `overflow: hidden` → 정사각형이 되고 **넘친 글자가 잘린다**

*(Chrome 151 headless 실측 — 위 블록 그대로: 짧은 쪽 120.00×120.00(w/h 1.000), 긴 쪽 120.00×168.00(w/h 0.714). `min-height: 0`을 더한 판은 둘 다 120.00×120.00 이고 긴 쪽의 `scrollHeight` 가 168 이었다.)*

- **고치는 법 셋은 결과가 같고 부작용이 다르다** — `min-height: 0`(넘쳐 보인다) · `overflow: hidden`(잘린다) · `overflow: auto`(스크롤된다).
- ★ **이것이 (4)의 `min-width: auto` 와 같은 뿌리다.** 「내용 기반 최소 크기가 지정한 크기를 이긴다」는 규칙 하나가 flex 에서는 가로로, 비율 상자에서는 세로로 나타난 것이다.
- `min-height` 를 **명시적으로 크게** 주면 그것도 비율을 이긴다 — *(실측: `aspect-ratio: 1/1; width: 120px; min-height: 200px` → 120.00 × 200.00, w/h 0.600.)*

비용 — 비율을 지키려면 **내용의 넘침을 받아들여야 한다.** 둘 다 가질 수는 없다.

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 이 절은 **어디서 헷갈리나**로 읽는다.

### 최소 형태

```css
.a { width: min-content; }    /* 쪼갤 수 있는 만큼 접었을 때 */
.b { width: max-content; }    /* 줄바꿈 없이 전부 */
.c { width: fit-content; }    /* 둘 사이에서 쓸 수 있는 공간에 맞춰 */

.d { aspect-ratio: 16 / 9; }  /* 슬래시 양옆에 숫자 — 16/9 도 같다 */
.e { aspect-ratio: 1.5; }     /* 하나만 쓰면 가로/세로 비 */
```

- 세 키워드는 `width`/`height` 말고 **`min-*`·`max-*`·`flex-basis`·`inline-size`** 에도 쓸 수 있다.
- `aspect-ratio` 의 초기값은 `auto` 다. `<img>` 처럼 원래 비율이 있는 요소에서는 `auto` 가 **그 원래 비율**을 뜻한다.

### 헷갈리는 자리 — 「내용만큼」이라는 말 넷

| 쓴 것 | 블록에서의 뜻 |
|---|---|
| `width: auto` | **부모를 채운다**(내재적 크기가 아니다) |
| `width: fit-content` | 축소 맞춤 — `min(max-content, max(min-content, 공간))` |
| `width: max-content` | 줄바꿈 없이 전부. **부모보다 커질 수 있다** |
| `width: min-content` | 쪼갤 수 있는 만큼 접었을 때 |

- `float`·`absolute`·`inline-block` 에서는 **첫 줄과 둘째 줄이 같은 결과**다((6)).
- `flex: 0 1 auto` 의 `auto` 는 또 다른 뜻이다 — **`width` 를 보고, `width` 도 `auto` 면 내용 크기**([25번](../25-flex-shorthand-and-sizing/)).

### 금지에 가까운 형태

```css
/* ① fit-content() 함수를 width 에 쓴다 — Chrome 151 에서 담기지도 않는다 */
.x { width: fit-content(150px); }        /* (5) — fit-content + max-width 로 나눠 써라 */

/* ② aspect-ratio 와 두 축을 다 지정한다 — 비율이 무시된다 */
.y { aspect-ratio: 16/9; width: 320px; height: 200px; }

/* ③ aspect-ratio 에 음수 — 버려진다. 단 0 은 유효하다(아래 실측) */
.w { aspect-ratio: -1; }
```

*(Chrome 151 headless 실측 — 진단 3창의 첫째 창(`cssRules`)으로 읽은 결과.\
`#a1 { aspect-ratio: 0 / 1; }` ← **담긴다** · `#a2 { }` ← `aspect-ratio: -1`(버려짐) · `#a3 { aspect-ratio: 16 / 9; }` · `#a4 { aspect-ratio: 1.5 / 1; }` ← **한 값을 써도 `/ 1` 이 붙어 저장된다** · `#a5 { }` ← `width: fit-content(150px)` · `#a6 { }` ← `width: bogus-content`.\
★ `fit-content(150px)` 와 **존재하지 않는 값 `bogus-content` 가 똑같이 빈 상자**로 나온다.\
★ ①의 `aspect-ratio: 0 / 1` 은 **담기고도 아무 일을 안 한다** — 그 상자는 120.00 × **24.00**(글 한 줄 높이)이었고 계산값은 `0 / 1` 로 남았다. **담기는 것과 먹는 것이 다르다**는 대조군이다.\
★ ②도 같은 성격이다 — 선언은 담기지만 레이아웃에서 무시되어 320.00 × 200.00 이 됐다.)*

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `min-content` ≤ `fit-content` ≤ `max-content` 와 `fit-content` 의 공식 | **명세** — css-sizing-3 §5 |
| 블록의 `width: auto` 는 채움, `float`/`absolute`/`inline-block` 은 축소 맞춤 | **명세** — CSS2 §10.3 + css-sizing-3 |
| flex·grid 항목의 `min-width`/`min-height` 초기값이 `auto` 이고 자동 최소 크기가 되는 것 | **명세** — css-flexbox-1 §4.5 · css-grid-2 · css-sizing-3 |
| 두 축을 다 지정하면 `aspect-ratio` 가 무시되는 것 | **명세** — css-sizing-4 |
| 비율로 정해지는 축에 **내용 기반 최소 크기**가 걸리는 것 | **명세** — css-sizing-4 (그래서 (8)이 「버그」가 아니다) |
| ★ **`fit-content()` 가 이 Chrome 에서 안 되는 것** | **구현** — Baseline `limited`. 명세(css-sizing-4)에는 있다. **명세를 읽은 것은 확인한 것이 아니다** |
| 하이픈이 줄바꿈 기회가 되는 것 | **명세**(css-text)지만 **어디서 쪼개지는지는 언어·설정에 달린다** |
| 모든 구체 픽셀값(80.00 · 128.02 · 168.00 …) | **이 머신의 Chrome 151 실측** — 글꼴과 글꼴 크기에 달렸다 |

## 어디서 틀리나

이 주제의 값어치는 대부분 여기 있다. 전부 **에러 없이 조용히 어긋난다.**

### 1. `width: auto` 로 「내용만큼」을 기대한다

블록에서 `auto` 는 **부모를 채운다**(400.00). 원한 것은 `fit-content`(128.02)다((6)).\
`float`·`inline-block` 에서는 우연히 맞아서 **상자 종류를 바꾼 순간 깨진다.**

### 2. `max-content` 를 「안전한 내용 크기」로 쓴다

`max-content` 는 **부모보다 커질 수 있다.** 긴 글이면 그대로 뚫는다.\
부모 안에 가두면서 내용만큼이려면 **`fit-content`** 다.

### 3. `fit-content(150px)` 를 쓴다

Chrome 151 에서 **선언이 담기지도 않는다**((5)). `getComputedStyle` 로 보면 `400px` 라는 그럴듯한 값이 돌아와 **안 쓴 것과 구분이 안 된다.**\
확인은 **`cssRules` 로 규칙 본문을 읽는 것**이다. `width: fit-content; max-width: 150px` 로 나눠 쓴다.

### 4. `min-content` 를 「가장 긴 낱말」로만 외운다

하이픈에서도 쪼개진다((3)). `hi flex-basis ok` 의 `min-content` 는 `flex-basis`(80.02)가 아니라 **`flex-`(40.02)** 다.\
반대로 `<pre>` 는 **한 줄 전체**다.

### 5. flex 항목이 안 줄어드는 것을 `flex-shrink` 문제로 본다

바닥은 `min-width: auto` → `min-content` 다((4)). [25번](../25-flex-shorthand-and-sizing/)의 사고가 **여기서 풀린다.**

### 6. `aspect-ratio` 를 「반드시 지켜지는 비율」로 믿는다

**내용이 넘치면 깨진다**((8)). 120×120 이어야 할 상자가 120×168 이 된다.\
게다가 **짧은 내용에서는 안 깨져서** 실서비스 데이터가 들어온 뒤에야 드러난다.

### 7. `aspect-ratio` 와 두 축을 다 지정한다

**비율이 조용히 무시된다.** 선언은 계산값에 남아 있어서 「썼는데 왜 안 되지」가 된다.

### 8. `min-height` 를 「최소한 이만큼」의 뜻으로만 쓴다

비율 상자에서는 `min-height` 가 **비율을 이긴다** — *(실측: `1/1; width:120; min-height:200` → 120×200.)*\
「비율을 지키되 최소 높이도」는 성립하지 않는다. 둘 중 하나를 골라야 한다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 쓸 것 | 왜 |
|---|---|---|
| 글자만큼만 넓은 배지·버튼 | `width: fit-content` | 블록의 `auto` 는 부모를 채운다 |
| 부모를 뚫어도 좋으니 한 줄로 | `width: max-content` | 툴팁·코드 한 줄 |
| 표 칸을 최대한 좁히기 | `width: min-content` | 쪼갤 수 있는 만큼 접는다 |
| 최대 폭이 있는 내용 크기 상자 | `fit-content` + `max-width` | **`fit-content()` 는 아직 못 쓴다**((5)) |
| 이미지 자리를 미리 잡아 레이아웃 이동 막기 | `aspect-ratio` | 로드 전에도 높이가 잡힌다 |
| 비율 상자에 **텍스트**를 담기 | `aspect-ratio` + `overflow` 처리 | 안 하면 (8)에서 깨진다 |
| 행과 열의 트랙 크기를 정하기 | **Grid**([목록의 **27번 주제**](../27-grid-track-sizing/)) | `fr`·`minmax()` 는 거기다 |

판단 규칙 두 줄.

- **「내용만큼」이라고 말했으면 곧바로 「접어서인가 펴서인가」를 되물어라.** 그 대답이 `min-content` 와 `max-content` 를 가른다.
- **`aspect-ratio` 를 쓰면 넘침 처리도 같이 정한다.** 안 정하면 비율이 깨지는 쪽으로 기본값이 잡힌다.

## 핵심 문장

- 「내용만큼」은 둘이다 — **`min-content`(접어서)와 `max-content`(펴서).** 항상 `min ≤ fit ≤ max`.
- **`fit-content` 는 크기가 아니라 공식**이다 — `min(max-content, max(min-content, 쓸 수 있는 공간))`.
- **블록의 `width: auto` 는 내재적 크기가 아니다.** `float`·`absolute`·`inline-block` 에서만 `fit-content` 와 같아진다.
- **`min-content` 를 정하는 것은 줄바꿈 기회**다. 하이픈에서도 쪼개지고, `white-space: pre` 면 `min-content` = `max-content` 가 된다.
- ★ **flex·grid 항목의 `min-width: auto` 가 `min-content` 로 풀린다** — [25번](../25-flex-shorthand-and-sizing/)의 사고가 여기서 풀린다.
- **`aspect-ratio` 는 한 축이 정해질 때만 일한다.** 두 축을 다 주면 무시되고, **내용이 넘치면 비율이 깨진다.**
- ★★ **`fit-content()` 함수는 이 Chrome 에서 선언이 담기지도 않는다.** Baseline 도 `limited` 다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 31번) · 「버전·지원 기준」의 Baseline 표
- [15번](../15-box-model-and-box-sizing/) — **`width` 가 어느 칸을 재는가는 거기 정본이다.** 여기는 **그 `width` 자리에 들어가는 값**이 무엇인가
- [25번](../25-flex-shorthand-and-sizing/) — **`min-width: auto` 사고의 현장이 거기이고, 그 `auto` 가 무엇으로 풀리는지가 여기다.** 상호 참조
- [04번](../04-value-processing-stages/) — `getComputedStyle` 이 내재적 키워드를 그대로 돌려주는지 픽셀로 돌려주는지
- [07번](../07-syntax-and-error-recovery/) — (5)의 `fit-content()` 처럼 **모르는 값이 조용히 버려지는** 규칙
- [목록의 **27번 주제**](../27-grid-track-sizing/)(Grid 트랙 정의) — **`fr`·`minmax()`·트랙에서의 `fit-content()` 는 거기다.** 여기는 **내재적 크기 키워드**까지만
- [목록의 **51번 주제**](../51-text-wrapping-and-decoration/)(텍스트 줄바꿈) — **어디서 쪼개지는가**의 정본(`word-break`·`overflow-wrap`·`hyphens`). (3)이 거기 기댄다
- [목록의 **44번 주제**](../44-backgrounds-and-object-fit/)(`object-fit`) — 대체 요소가 비율을 다루는 다른 표면
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **내재적 크기(intrinsic size)** — 부모 크기와 무관하게 **내용만으로** 정해지는 크기.
- **외재적 크기(extrinsic size)** — 부모가 준 공간을 기준으로 정해지는 크기. `width: auto`·`50%` 가 그것이다.
- **`min-content`** — 쪼갤 수 있는 만큼 다 쪼갰을 때의 크기. 글에서는 대개 가장 긴 조각.
- **`max-content`** — 줄바꿈을 한 번도 안 했을 때의 크기.
- **`fit-content`** — `min(max-content, max(min-content, 쓸 수 있는 공간))`. 셋 중 **유일하게 부모 크기가 섞인다.**
- **축소 맞춤(shrink-to-fit)** — `fit-content` 공식의 옛 이름. `float`·`absolute`·`inline-block` 의 `auto` 가 이것이다.
- **줄바꿈 기회(soft wrap opportunity)** — 글을 쪼갤 수 있는 자리. 공백·하이픈. `white-space: pre` 면 없다.
- **자동 최소 크기(automatic minimum size)** — flex·grid 항목의 `min-*: auto` 가 풀리는 값. 대개 `min-content`.
- **`aspect-ratio`** — 한 축이 정해지면 다른 축을 비율로 만든다. 두 축이 다 지정되면 무시된다.
- **내용 기반 최소 크기(content-based minimum size)** — 비율로 정해지는 축에 걸리는 바닥. (8)에서 비율을 깨는 범인.
- **진단 3창** — `cssRules`(담겼나) → `querySelectorAll`(잡혔나) → `getComputedStyle`(이겼나). (5)는 **첫째 창에서 이미 탈락**한 경우다.

---

## 더 들어가면

- **`stretch`(옛 이름 `-webkit-fill-available`)** 라는 키워드도 있다 — 「부모의 남은 공간을 채워라」. 블록의 `width: auto` 가 하던 일을 `float`·`absolute` 에서도 하게 해 준다. 내재적 크기 셋과 **짝을 이루는 외재적 키워드**로 읽으면 지도가 완성된다.
- **`contain-intrinsic-size`** 는 `content-visibility` 로 렌더를 건너뛴 요소에 「내재적 크기가 이만큼이라고 쳐라」를 알려 주는 속성이다(Baseline **widely**, 2023-09-18 → 2026-03-18). 내재적 크기를 **측정하지 않고 선언하는** 유일한 표면이다. 정본은 [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/).
- **`aspect-ratio: auto <ratio>`** 라고 두 값을 쓰면 「원래 비율이 있으면 그것을, 없으면 이 비율을」이라는 뜻이다. `<img>` 처럼 대체 요소에 대비책을 줄 때 쓴다.
- ★ **`min-content` 는 「가장 긴 낱말」이 아니라 「가장 큰 쪼갤 수 없는 조각」** 이다. 표·인라인 블록·이미지가 섞이면 낱말이 아닌 것이 최댓값이 될 수 있다. (3)의 하이픈 실측이 그 축소판이다.
- ★ **줄바꿈 속성 중 어떤 것은 `min-content` 를 실제로 줄이고 어떤 것은 안 줄인다.** 이름이 비슷해서 헷갈리는데, **실측으로 갈린다.**\
  *(Chrome 151 headless 실측 — 같은 글 `hi javascript ok` 를 `width: min-content` 상자에 넣고 한 줄씩 더했다.\
  기본 → **80.00**(높이 72) · `overflow-wrap: anywhere` → **8.02**(높이 336) · `word-break: break-word` → **8.02** · `word-break: break-all` → **8.02** · ★ **`overflow-wrap: break-word` → 80.00 — 줄지 않았다.**)*\
  즉 `anywhere` 는 **내재적 크기 계산에 반영되고** `break-word` 는 **넘칠 때만 쪼갠다.** 이름이 한 쌍처럼 생겼는데 성질이 반대다.\
  ★ 그래서 [25번](../25-flex-shorthand-and-sizing/)의 사고를 **`min-width: 0` 없이** 고칠 수 있다 —\
  *(실측: 컨테이너 300 · 사이드바 100 · 본문 `flex: 1` 에 긴 URL 한 줄을 넣으면 기본은 본문 폭 248.00 에 오른끝 348.00(뚫는다)인데, 본문에 `overflow-wrap: anywhere` 한 줄만 더하면 **200.00 · 오른끝 300.00** 이 된다. 대신 높이가 48 → 72 로 늘어난다.)*\
  정본은 [목록의 **51번 주제**](../51-text-wrapping-and-decoration/).
