# css/syntax/16 — `display` 의 내부/외부 값 — `block flow`·`inline flow-root`·`flow-root`·`contents`·`none` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Display Module Level 3](https://drafts.csswg.org/css-display-3/) (외부/내부 display 타입과 두 값 문법·`contents`·`none` 의 정본) · [CSS Containment Level 2](https://drafts.csswg.org/css-contain-2/) (`content-visibility`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 **두 값 문법을 포함한 `display` 값 40여 가지**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle(el).display` 와 `getBoundingClientRect()` 로 읽었다. 접근성 트리는 같은 Chrome 에 `--force-renderer-accessibility` 를 켜고 CDP 의 `Accessibility.getFullAXTree` 로 덤프해 확인했다.\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **버전** — `content-visibility` 는 Baseline **newly**(2025-09-15, 아직 widely 아님 — 목록 README 의 지원 표). 나머지는 오래 자리잡은 값이다.
> **여기서 다루지 않는 것** — 치수가 정해지는 규칙은 [15번](../15-box-model-and-box-sizing/2-summary.md), **`flow-root` 가 만드는 서식 문맥이 무엇을 가두는가**는 [17번](../17-block-formatting-context/2-summary.md), 마진 상쇄는 [18번](../18-margin-collapsing/2-summary.md)이다. **flex 의 축과 정렬은 [24번](../24-flexbox-axes/2-summary.md)이 정본**이고 여기서는 `display` 값으로만 언급한다. Grid 는 목록의 [**27**](../27-grid-track-sizing/)~[**29**](../29-grid-template-areas/)번 주제, 인라인 서식 문맥은 [목록의 **19번 주제**](../19-inline-formatting-context/)다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 동작은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`display` 는 한 값처럼 보이지만 질문 두 개에 동시에 답한다** — 「바깥에서 너는 어떻게 줄 서니」와 「안에 있는 애들은 어떻게 배치하니」.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물 하나 | 요소가 만드는 상자 |
| 이 건물이 **거리에 어떻게 서는가** — 한 줄을 통째로 쓰나, 옆 건물과 나란히 서나 | **외부 display** (`block` / `inline`) |
| 이 건물 **안을 어떻게 나누는가** — 층층이 쌓나, 한 줄로 늘어놓나, 격자로 나누나 | **내부 display** (`flow` / `flow-root` / `flex` / `grid` / `table`) |
| 건물을 허물고 **안에 있던 사람만 거리에 내놓는 것** | `display: contents` |
| 건물을 **지도에서 지우는 것** | `display: none` |

- 우리가 외우는 `block`·`inline-block`·`flex` 는 전부 **두 값을 한 낱말로 줄여 쓴 옛 표기**다.
- `inline-block` 이라는 이름이 "인라인인데 블록"이라는 **모순처럼 들리는 이유**가 이것이다 — 실제 뜻은 **바깥은 인라인, 안은 독립된 흐름**(`inline flow-root`)이다.
- **바깥 값과 안쪽 값은 서로 독립이다.** 그래서 네 조합이 전부 존재한다.

```text
                안을 어떻게 배치하나 (내부 display)
                flow            flow-root        flex           grid
              +---------------+---------------+--------------+--------------+
  바깥에   block | block         | flow-root     | flex         | grid         |
  어떻게        | (= block flow)| (= block      |(= block flex)|(= block grid)|
  서나          |               |   flow-root)  |              |              |
 (외부   -----+---------------+---------------+--------------+--------------+
 display) inline| inline       | inline-block  | inline-flex  | inline-grid  |
              | (= inline flow)| (= inline    |              |              |
              |                |   flow-root)  |              |              |
              +---------------+---------------+--------------+--------------+
                  한 낱말 이름은 이 표의 칸에 붙인 별명일 뿐이다
```

실무에서 이게 터지는 자리는 **"`display: block` 을 줬는데 마진이 밖으로 샌다"** 는 증상이다.\
`block` 의 안쪽은 `flow` 이고, `flow` 는 **바깥과 이어진 흐름**이라 새는 것이 정상이다. 안 새게 하려면 안쪽을 `flow-root` 로 바꿔야 한다([17번](../17-block-formatting-context/2-summary.md)).

> **외부 display 타입(outer display type)** — 이 상자가 **부모의 흐름 안에서 어떻게 참여하는가**. `block` 이면 한 줄을 통째로 쓰고, `inline` 이면 글자처럼 줄 안에 끼어든다.\
> 예: `<div>` 는 기본이 `block`, `<span>` 은 기본이 `inline` 이다.

> **내부 display 타입(inner display type)** — 이 상자가 **자기 자식들을 어떤 규칙으로 배치하는가**.\
> 예: `flow` 는 문단처럼 쌓고, `flex` 는 한 축으로 늘어놓고, `grid` 는 격자로 나눈다.

> **`flow-root`** — 내부 배치는 `flow` 와 똑같지만 **자기 안에서 독립된 흐름을 연다**는 뜻. `flow` 와 딱 이 한 가지만 다르다.\
> 예: 자식의 마진이 밖으로 새지 않고, 안의 `float` 를 끌어안는다([17번](../17-block-formatting-context/2-summary.md)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `display: inline-block` 이라는 **한 낱말이 무엇 둘을 동시에 정하는가.**
2. **이 브라우저가 두 값 문법을 실제로 파싱하는가** — 그리고 계산값으로 **무엇을 돌려주는가.**
3. 요소를 "안 보이게" 하는 세 가지(`none`·`visibility`·`content-visibility`)가 **레이아웃과 접근성 트리에서 각각 어떻게 다른가.**

## 동작 방식

### (1) 한 낱말 이름 ↔ 두 값 — 대응표

**언제 쓰나** — `display` 값을 읽을 때마다. 이 표가 이 주제의 좌표계다.

| 한 낱말 (옛 표기) | 두 값 | 바깥 | 안 |
|---|---|---|---|
| `block` | `block flow` | block | flow |
| `flow-root` | `block flow-root` | block | flow-root |
| `inline` | `inline flow` | inline | flow |
| `inline-block` | `inline flow-root` | inline | flow-root |
| `flex` | `block flex` | block | flex |
| `inline-flex` | `inline flex` | inline | flex |
| `grid` | `block grid` | block | grid |
| `inline-grid` | `inline grid` | inline | grid |
| `table` | `block table` | block | table |
| `inline-table` | `inline table` | inline | table |
| `list-item` | `block flow list-item` | block | flow (+ 표지자) |

- **`inline-block` 과 `flow-root` 는 같은 내부 값**(`flow-root`)을 갖는다. 바깥만 다르다.\
  그래서 "`inline-block` 은 마진이 안 샌다"와 "`flow-root` 는 마진이 안 샌다"가 **같은 사실**이다.
- `list-item` 만 세 낱말이다 — 바깥·안에 더해 **표지자(marker) 상자를 만든다**는 성질이 붙는다.
- 이 표를 외우는 것보다 **"바깥 하나 + 안 하나"라는 구조**를 붙드는 편이 낫다.

### (2) 이 Chrome 은 두 값 문법을 파싱하는가 — 실측

**언제 쓰나** — 명세를 읽고 `display: block flow-root` 라고 써도 되나 판단할 때. **이 주제의 급소다.**

★ **결론부터: Chrome 151 은 두 값 문법을 파싱한다.** 그리고 **계산값은 한 낱말 옛 표기로 되돌려 준다.**

판별 방법 — 기본값을 `inline-flex` 로 깔아 놓고 시험할 선언으로 덮었다.\
CSS 는 무효한 선언을 **조용히 버리는** 언어이므로, 계산값이 `inline-flex` 로 남아 있으면 **그 선언이 버려진 것**이다.

```text
  .t { display: inline-flex; }              <- 대조군
  .t { display: <시험할 값>; }              <- 덮어쓰기

  계산값이 inline-flex   -> 선언이 버려졌다 (무효)
  계산값이 그 밖의 것    -> 선언이 받아들여졌다 (유효)
```

*(Chrome 151 headless 실측 — `getComputedStyle(el).display` 가 돌려준 값 그대로다.)*

| 쓴 값 | 계산값 | 판정 |
|---|---|---|
| `block flow` | `block` | 유효 — 옛 표기로 접힌다 |
| `inline flow` | `inline` | 유효 |
| `block flow-root` | `flow-root` | 유효 |
| `inline flow-root` | **`inline-block`** | 유효 |
| `block flex` | `flex` | 유효 |
| `inline flex` | `inline-flex` | 유효 |
| `block grid` | `grid` | 유효 |
| `block table` | `table` | 유효 |
| `flow` (안쪽만) | `block` | **유효** — 바깥이 생략되면 `block` |
| `flow block` (순서 뒤집기) | `block` | **유효** — 순서는 상관없다 |
| `flow-root block` | `flow-root` | 유효 |
| `block ruby` | **`block ruby`** | 유효 — **두 값 그대로 남는다** |
| `inline flow list-item` | **`inline list-item`** | 유효 — 두 값으로 남는다 |
| `block flow-root list-item` | **`flow-root list-item`** | 유효 |
| `block block` | `inline-flex` | **무효** — 바깥 값 둘 |
| `block inline` | `inline-flex` | **무효** |
| `flex flow` | `inline-flex` | **무효** — 안쪽 값 둘 |
| `inline-block flow` | `inline-flex` | **무효** — 옛 표기와 섞을 수 없다 |
| `block table-row` | `inline-flex` | **무효** — 표 내부 값에는 바깥을 못 붙인다 |
| `run-in` | `inline-flex` | **무효** — Chrome 이 모르는 값 |
| `blorp` | `inline-flex` | **무효** (대조용 헛소리 값) |

그림 해설 (한 단계씩):

- **파싱은 된다.** 명세의 두 값 문법이 이 브라우저에서 "안 되는 문법"이 아니다.
- **계산값은 짧은 옛 이름으로 접힌다.** `block flow` 를 썼는데 DevTools 에서 `block` 이 보이는 것은 **버려진 것이 아니라 접힌 것**이다.
- **접을 옛 이름이 없으면 두 값이 그대로 남는다** — `block ruby`·`inline list-item`·`flow-root list-item` 이 그 경우다.\
  이것이 **"진짜로 파싱됐다"는 가장 강한 증거**다. 버려졌다면 대조군 값이 남았을 것이다.
- 그래서 **`getComputedStyle` 만으로 "지원 안 한다"고 판정하면 틀린다.** 대조군을 깔고 판정해야 한다.

비용 — 없다. 다만 **팀 코드에 두 값을 쓰면 DevTools·계산값과 소스가 달라 보인다.** 실무에서는 옛 표기를 쓰고, 두 값은 **읽는 법**으로 알아 두는 편이 낫다.

### (3) 바깥 값이 하는 일 — 줄을 통째로 쓰나, 줄 안에 끼나

**언제 쓰나** — `width` 가 안 먹거나 줄바꿈이 예상과 다를 때.

```html demo
<p>한 줄 안에서 —
  <span class="a">inline flow</span>
  <span class="b">inline flow-root</span>
  <span class="c">block flow</span>
</p>
<style>
  p { font: 14px system-ui; width: 360px; }
  span { background: #bfdbfe; border: 2px solid #64748b; padding: 4px 8px; }
  .a { display: inline flow; }
  .b { display: inline flow-root; width: 120px; }
  .c { display: block flow; width: 120px; }
</style>
```

> **보이는 것** — 앞의 두 상자는 **같은 줄에 나란히** 있고 세 번째만 **다음 줄로 내려가 왼쪽 끝에 붙는다.** 첫 상자(`inline flow`)는 `width` 선언이 없어 글자만큼만 넓고, 둘째(`inline flow-root`)는 `width: 120px` 이 먹어서 **글자보다 눈에 띄게 넓다.** 셋째도 `width: 120px` 이 먹었다.\
> **바꿔 볼 것** — `.a` 에 `width: 120px` 을 추가 → **아무 일도 일어나지 않는다**(바깥이 `inline` 이면 `width` 가 적용되지 않는다) · `.c` 의 `block` 을 `inline` 으로 바꿔 셋이 줄에 어떻게 놓이는지 보라

*(Chrome 151 headless 실측 — `.a` 는 계산값 `inline`, `rect.width` 88.64(글자 폭 그대로). `.b` 는 계산값 **`inline-block`**, `rect.width` 140(= 선언한 120 + 패딩 16 + 테두리 4). `.c` 는 계산값 `block`, `rect.width` 140 이고 `rect.y` 가 앞의 둘보다 32 아래다 — 줄이 바뀌었다.)*

- **바깥이 `inline` 이면 `width`/`height` 가 적용되지 않는다** — 단, **안쪽이 `flow` 일 때만** 그렇다.
- 안쪽이 `flow-root`(= `inline-block`)이면 **인라인으로 줄 안에 있으면서도 치수를 가질 수 있다.** 이것이 `inline-block` 의 존재 이유다.
- 인라인 상자가 줄 안에서 어떻게 정렬되고 왜 아래에 빈 공간이 생기는지는 [목록의 **19번 주제**](../19-inline-formatting-context/)가 정본이다.

### (4) 안쪽 값이 하는 일 — 자식을 어떤 규칙으로 놓나

**언제 쓰나** — 자식들의 배치 규칙을 고를 때.

```text
  같은 마크업, 부모의 내부 display 만 바꾼다

  flow          flow-root        flex            grid
  +--------+    +--------+       +--------+      +--------+
  | [ A  ] |    | [ A  ] |       |[A][B]  |      |[A]|[B] |
  | [ B  ] |    | [ B  ] |       |        |      |---|--- |
  +--------+    +--------+       +--------+      |[C]|[D] |
   위아래로      위아래로          한 축으로       +--------+
   쌓는다        쌓는다            늘어놓는다      격자로 나눈다
                 + 흐름이 독립
```

- `flow` 와 `flow-root` 는 **자식 배치가 완전히 같다.** 다른 것은 **흐름이 바깥과 이어져 있나**뿐이다.\
  그 차이가 무엇을 만드는지는 [17번](../17-block-formatting-context/2-summary.md)이 정본이다.
- `flex` 의 주축·교차축과 정렬은 [24번](../24-flexbox-axes/2-summary.md)이 정본이다. 여기서는 **`flex` 가 `block flex` 의 별명**이라는 것까지다.
- `grid` 는 목록의 [**27**](../27-grid-track-sizing/)~[**29**](../29-grid-template-areas/)번 주제, `table` 계열은 이 목록에서 **값으로만** 다룬다(README 의 「뺀 것」).

### (5) `display: contents` — 상자를 없애고 자식만 남긴다

**언제 쓰나** — 마크업 구조는 필요한데 **중간 래퍼가 레이아웃을 망칠 때.**

```html demo
<div class="bar">
  <div class="i">A</div>
  <div class="wrap"><div class="i">B</div><div class="i">C</div></div>
</div>
<div class="bar">
  <div class="i">A</div>
  <div class="wrap" style="display: contents"><div class="i">B</div><div class="i">C</div></div>
</div>
<style>
  .bar { display: flex; gap: 10px; width: 340px; border: 2px solid #64748b; margin-bottom: 12px; }
  .wrap { border: 3px solid #ef4444; padding: 10px; background: #fee2e2; }
  .i { background: #bfdbfe; padding: 8px 14px; font: 14px system-ui; }
</style>
```

> **보이는 것** — 위 줄에서는 **빨간 테두리 상자**가 보이고 그 안에서 `B` 와 `C` 가 **세로로 쌓인다**(래퍼가 flex 항목 하나이고, 그 안은 보통 흐름이라 위아래로 쌓인다). 아래 줄에서는 **빨간 테두리가 통째로 사라지고** `A` `B` `C` 셋이 **한 줄에 나란히** 놓인다.\
> **바꿔 볼 것** — `display: contents` 를 `display: block` 으로 → 위 줄과 똑같아진다 · `.wrap` 의 `background`·`padding` 을 바꿔 봐도 아래 줄에서는 **아무 변화가 없다**(그릴 상자가 없다)

*(Chrome 151 headless 실측 — 보통 래퍼: `rect` 63.2×98 이고 `B`·`C` 의 y 가 15 와 51 로 세로로 쌓였다. `display: contents` 래퍼: `rect` 가 **0×0**, `B`·`C` 의 y 가 둘 다 116 으로 같고 x 가 48.52 와 95.72 — **가로로 나란**하다.)*

- `display: contents` 는 그 요소의 **상자를 만들지 않는다.** 자식들이 **조부모의 직계 자식인 것처럼** 배치된다.
- 그래서 **배경·테두리·패딩·마진이 전부 사라진다.** 없어진 것이 아니라 **그릴 상자가 없는** 것이다.
- 실무 용도는 **flex/grid 컨테이너와 항목 사이에 낀 래퍼를 투명하게 만드는 것**이다.\
  "정렬이 손자에게 안 먹는다"([24번](../24-flexbox-axes/2-summary.md)의 사고)를 마크업을 안 바꾸고 푸는 길이다.
- ★ **주의** — 이것은 **레이아웃 상자만** 없애는 것이지 요소를 없애는 것이 아니다. 접근성 트리에는 남을 수 있다((7)의 실측).

### (6) 안 보이게 하는 세 가지 — 레이아웃에서

**언제 쓰나** — 토글·탭·접힘 UI 를 만들 때. **셋의 차이를 모르면 조용히 잘못된 것을 고른다.**

```html demo
<div class="b">① 앞 상자</div>
<div class="b x" style="display: none">display:none</div>
<div class="b x" style="visibility: hidden">visibility:hidden</div>
<div class="b x" style="content-visibility: hidden">content-visibility:hidden</div>
<div class="b">② 뒤 상자</div>
<style>
  .b { height: 30px; background: #bfdbfe; border: 1px solid #64748b; font: 13px system-ui; }
  .x { background: #fca5a5; }
</style>
```

> **보이는 것** — 파란 상자 둘 사이에 **빈 자리 둘과 붉은 상자 하나**가 있다. `display: none` 상자는 **자리까지 사라져** 아무 흔적이 없다. `visibility: hidden` 상자는 **완전히 흰 빈칸**만 남긴다(붉은 배경도 테두리도 안 그려진다). `content-visibility: hidden` 상자는 **붉은 배경과 테두리가 그대로 보이고 그 안의 글자만 사라진다.**\
> **바꿔 볼 것** — 세 상자의 `height: 30px` 을 지우면 → `visibility` 상자는 글자 높이만큼(21px) 남는데 `content-visibility` 상자는 **테두리 2px 만 남고 무너진다**(안을 재지 않으므로) · `contain-intrinsic-size: 0 30px` 을 더해 무너진 높이를 되돌려 보라

*(Chrome 151 headless 실측 — `display:none` 의 `rect` 는 **0×0** 이고 뒤 상자가 곧바로 이어진다. `visibility:hidden` 과 `content-visibility:hidden` 은 둘 다 `rect` 780×32 로 **자리를 그대로 차지한다.** `height` 선언을 빼고 다시 재니 `visibility:hidden` 은 21, `content-visibility:hidden` 은 **2**(테두리만) 였다 — 뒤엣것은 안쪽을 레이아웃하지 않기 때문이다.)*

| | 상자가 생기나 | 자리를 차지하나 | 배경·테두리가 그려지나 | 안의 내용이 그려지나 |
|---|---|---|---|---|
| `display: none` | **아니오** | 아니오 | 아니오 | 아니오 |
| `visibility: hidden` | 예 | **예** | 아니오 | 아니오 |
| `content-visibility: hidden` | 예 | **예** | **예** | 아니오 |

- `display: none` 은 **상자를 아예 안 만든다.** 자식이 아무리 많아도 레이아웃 비용이 0 이다.
- `visibility: hidden` 은 상자를 만들고 **칠하지만 않는다.** 자리는 그대로 남는다.
- `content-visibility: hidden` 은 상자를 만들고 **자기 배경·테두리는 칠하되 안쪽은 레이아웃도 페인트도 건너뛴다.**\
  그래서 **높이를 안 주면 테두리만 남고 무너진다** — 대신 `contain-intrinsic-size` 로 「대략 이만하다」를 알려 준다.

### (7) 안 보이게 하는 세 가지 — 접근성 트리에서

**언제 쓰나** — 스크린 리더 사용자에게 무엇이 읽히는지 판단할 때. **화면으로는 절대 알 수 없는 자리다.**

측정 방법 — Chrome 151 에 `--force-renderer-accessibility` 를 켜고 CDP `Accessibility.getFullAXTree` 를 덤프했다.\
구분이 되도록 각 요소에 서로 다른 `aria-label` 을 달았다.

```text
  덤프 결과 (요소 이름 | 트리에서의 상태)

  A-보임        | exposed paragraph  + 자식 StaticText("보임 알파")
  B-none        | 트리에 아예 없음
  C-visibility  | 트리에 아예 없음
  D-contentvis  | exposed paragraph  ... 그런데 자식 StaticText 가 없다
  E-보임        | exposed paragraph  + 자식 StaticText("보임 오메가")
  F-contents    | exposed generic    (display: contents 인데 트리에 남아 있다)
  G-자식        | exposed paragraph  + StaticText — 정상
```

- **`display: none` 과 `visibility: hidden` 은 접근성 트리에서 통째로 사라진다.** 스크린 리더가 읽을 것이 없다.
- **`content-visibility: hidden` 은 요소 자신은 트리에 남고 그 안의 내용만 사라진다.**\
  실측에서 `aria-label` 을 준 요소가 `exposed` 로 남았고 그 **자식 텍스트 노드는 없었다.**
- **`display: contents` 요소는 트리에 남았다** — 레이아웃 상자를 안 만드는 것과 접근성 트리에 나오는 것은 **다른 이야기**다.

★ **"화면에서 사라진다"와 "읽히지 않는다"는 다른 이야기다.** 세 값 중 어느 것도 "접근성용"이 아니며,\
**읽히기는 하되 안 보이게** 하고 싶으면 `display`/`visibility` 가 아니라 이른바 시각적 숨김(클립 기법)을 쓴다.\
반대로 **보이는데 읽히지 않게** 하려면 `aria-hidden` 을 쓴다 — `display` 로는 안 된다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.a { display: block; }              /* 옛 표기 — 실무에서 쓰는 형태 */
.b { display: block flow; }         /* 두 값 — 같은 뜻, 계산값은 block 으로 접힌다 */
.c { display: inline flow-root; }   /* = inline-block */
.d { display: flow-root; }          /* = block flow-root */
.e { display: contents; }           /* 상자를 안 만든다 */
.f { display: none; }               /* 상자도 자식도 없다 */
```

- **바깥을 생략하면 `block`**, **안을 생략하면 `flow`** 로 채워진다.\
  *(실측: `display: flow` 의 계산값이 `block`, `display: flow-root` 의 계산값이 `flow-root`(= `block flow-root`).)*
- **순서는 상관없다** — `flow block` 도 `block flow` 와 같은 결과였다.
- **옛 표기와 두 값을 섞을 수 없다** — `inline-block flow` 는 버려졌다.

### 금지 사례 — 버려지는 선언

```css
.a { display: block block; }       /* 바깥 값 둘 — 버려진다 */
.b { display: block inline; }      /* 역시 바깥 값 둘 */
.c { display: flex flow; }         /* 안쪽 값 둘 */
.d { display: block table-row; }   /* 표 내부 값에는 바깥을 못 붙인다 */
.e { display: run-in; }            /* Chrome 이 모르는 값 */
```

- 전부 **에러 메시지 없이 그 선언 하나만 버려진다.** 앞서 이긴 값이 그대로 남는다.
- 그래서 **"안 먹는다"와 "버려졌다"를 구분하려면 대조군을 깔아야 한다**((2)의 방법).
- 오류 복구의 정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)다.

## 구현 세부사항 대 언어 보장

- **"`display: block flow` 가 유효한 문법인가"는 명세가 정한다.** CSS Display Level 3 의 두 값 문법이 근거다.
- **"이 브라우저가 계산값으로 무엇을 돌려주나"는 구현이다.** Chrome 151 이 옛 표기로 접는 것은 **관찰**이지 보장이 아니다.\
  명세는 접을 옛 이름이 있으면 그것을 쓰라고 직렬화 규칙을 두고 있고 실측이 그것과 맞아떨어졌지만, **이 문서는 관찰한 값만 적는다.**
- **`display: contents` 가 접근성 트리에 남는 것도 관찰이다.** 과거 브라우저들이 이 자리에서 서로 달랐던 이력이 있으므로 **버전이 오르면 다시 찍어야 하는 칸**이다.
- `content-visibility` 는 Baseline **newly**(2025-09-15)다 — **오래된 브라우저에서는 선언 자체가 버려져 그냥 보인다.**

## 어디서 틀리나

### 1. `display` 를 "한 가지"로 외운다

`block`·`inline-block`·`flex` 를 **서로 무관한 값들**로 외우면 `inline-flex` 가 왜 존재하는지, `flow-root` 가 왜 `inline-block` 과 형제인지 설명이 안 된다.\
바른 기억: **바깥 하나 + 안 하나.**

### 2. `getComputedStyle` 만 보고 "미지원"이라 판정한다

`display: block flow` 를 쓰고 계산값 `block` 을 보면 "버려졌구나" 싶지만 **접힌 것**이다.\
**대조군을 깔고 판정해야** 갈린다((2)).

### 3. `display: contents` 로 요소를 "없앤다"고 생각한다

상자만 사라진다. **접근성 트리에는 남았다**((7) 실측). 배경·테두리를 준 요소에 `contents` 를 주면 **디자인이 조용히 사라진다.**

### 4. `visibility: hidden` 과 `content-visibility: hidden` 을 같은 것으로 본다

(6)의 demo 에서 **눈으로 바로 갈린다** — 뒤엣것은 **배경과 테두리가 그대로 보인다.**\
그리고 높이를 안 주면 **뒤엣것만 0 으로 무너진다.**

### 5. 인라인 요소에 `width` 를 준다

바깥이 `inline` 이고 안쪽이 `flow` 면 **`width` 가 적용되지 않는다.** 에러는 없다.\
치수를 주려면 안쪽을 `flow-root` 로(= `inline-block`) 바꾸거나 바깥을 `block` 으로 바꾼다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 값 | 왜 |
|---|---|---|
| 줄 안에 있으면서 치수를 갖고 싶다 | `inline-block`(= `inline flow-root`) | 바깥 inline + 안 flow-root |
| 마진이 새지 않는 블록이 필요하다 | `flow-root` | 부작용 없이 독립 흐름만 연다([17번](../17-block-formatting-context/2-summary.md)) |
| 중간 래퍼를 레이아웃에서 투명하게 | `contents` | 상자를 안 만든다. 단 배경·테두리도 사라진다 |
| 토글로 완전히 치우기 | `none` | 자리까지 사라지고 접근성 트리에서도 빠진다 |
| 자리를 남기고 숨기기 | `visibility: hidden` | 자리는 유지, 트리에서는 빠진다 |
| 화면 밖 긴 목록의 렌더 비용을 아끼기 | `content-visibility` | 안쪽 레이아웃·페인트를 건너뛴다(Baseline newly) |

판단 규칙 두 줄.

- **`display` 를 고르는 일은 "바깥"과 "안"을 따로 고르는 일이다.** 한 낱말 이름에 홀리지 않는다.
- **"숨기기"는 세 가지가 서로 다른 도구다.** 레이아웃·페인트·접근성 중 무엇을 끄고 싶은지 먼저 정한다.

## 핵심 문장

- `display` 는 **바깥(외부)과 안(내부) 두 가지**를 동시에 정한다. 한 낱말 이름은 그 조합에 붙인 별명이다.
- `block` = `block flow` · `inline-block` = `inline flow-root` · `flex` = `block flex` · `flow-root` = `block flow-root`.
- **Chrome 151 은 두 값 문법을 파싱한다.** 계산값은 옛 이름으로 접히고, **접을 이름이 없으면 두 값 그대로 남는다**(`block ruby`·`inline list-item`).
- **순서는 상관없고, 바깥을 생략하면 `block`, 안을 생략하면 `flow`** 다. 옛 표기와는 섞을 수 없다.
- `display: contents` 는 **상자만 없앤다** — 배경·테두리도 같이 사라지지만 접근성 트리에는 남았다(실측).
- `none` / `visibility: hidden` / `content-visibility: hidden` 은 **레이아웃에서도 접근성 트리에서도 셋 다 다르다.**\
  특히 `content-visibility: hidden` 은 **자기 배경·테두리는 그리고 안쪽만 건너뛴다.**

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 16번)
- [15번 주제](../15-box-model-and-box-sizing/2-summary.md)(박스 모델과 `box-sizing`) — **이 상자의 치수가 정해지는 규칙**은 거기. 여기는 **그 상자가 어떤 종류인가**다
- [17번 주제](../17-block-formatting-context/2-summary.md)(서식 문맥) — **`flow-root` 가 연 독립 흐름이 무엇을 가두는가**는 거기. 여기는 **`flow` 와 `flow-root` 가 `display` 의 내부 값으로 갈린다**는 것까지다
- [18번 주제](../18-margin-collapsing/2-summary.md)(마진 상쇄) — `flow` 안에서 마진이 합쳐지는 규칙은 거기
- [24번 주제](../24-flexbox-axes/2-summary.md)(Flexbox 축·정렬) — **flex 컨테이너가 어떻게 배치하는가는 거기가 정본**이다. 여기는 `flex` 가 `block flex` 의 별명이라는 것까지
- [목록의 **19번 주제**](../19-inline-formatting-context/)(인라인 서식 문맥) — 인라인 상자가 줄 안에서 정렬되는 규칙과 이미지 아래 빈 공간
- 목록의 [**27**](../27-grid-track-sizing/)~[**29**](../29-grid-template-areas/)번 주제(Grid) — `grid` 의 내부 배치 규칙
- [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(오류 복구) — 무효한 `display` 선언이 **조용히 버려지는** 규칙
- [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)(렌더링 파이프라인·`contain`·`content-visibility`) — `content-visibility` 의 **성능 쪽 정본**
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **외부 display 타입(outer display type)** — 이 상자가 부모의 흐름에 어떻게 참여하나. `block`(한 줄 차지) 또는 `inline`(줄 안에 끼어듦).
- **내부 display 타입(inner display type)** — 이 상자가 자식을 어떻게 배치하나. `flow`·`flow-root`·`flex`·`grid`·`table` 등.
- **`flow`** — 문단처럼 쌓는 보통 흐름. **바깥 흐름과 이어져 있다.**
- **`flow-root`** — `flow` 와 배치는 같지만 **자기 안에서 독립된 흐름을 연다.** 정본은 [17번](../17-block-formatting-context/2-summary.md).
- **`inline-block`** — `inline flow-root` 의 옛 이름. 줄 안에 있으면서 치수를 가질 수 있다.
- **`display: contents`** — 상자를 만들지 않고 자식만 남긴다. 배경·테두리·패딩·마진이 사라진다.
- **`display: none`** — 상자를 아예 만들지 않는다. 자리도 접근성 트리에서의 존재도 없다.
- **`visibility: hidden`** — 상자는 만들되 칠하지 않는다. 자리는 남고 접근성 트리에서는 빠진다.
- **`content-visibility: hidden`** — 상자와 그 배경·테두리는 그리되 **안쪽의 레이아웃·페인트를 건너뛴다.** Baseline newly(2025-09-15).
- **접근성 트리(accessibility tree)** — 보조 기술이 읽는, DOM 과 별개인 트리. 화면에 보이는 것과 일대일이 아니다.\
  예: `content-visibility: hidden` 요소는 화면에 상자가 보이지만 그 안의 글자는 트리에 없었다.
- **계산값(computed value)** — `getComputedStyle` 이 돌려주는 값. 선언한 문자열과 다를 수 있다(두 값이 옛 이름으로 접힌다).

---

## 더 들어가면

- **`display: list-item`** 은 세 낱말 값이다(`block flow list-item`). 바깥·안에 더해 **표지자 상자**를 만든다.\
  실측에서 `inline flow list-item` 의 계산값이 `inline list-item`, `block flow-root list-item` 이 `flow-root list-item` 으로 **두 값이 그대로 남았다** — 접을 옛 이름이 없기 때문이다.
- **`display` 는 전환·애니메이션의 대상으로 오래 쓸 수 없었다.** `none` ↔ `block` 사이에 중간값이 없기 때문이다.\
  그 문제를 푸는 `@starting-style` 과 `transition-behavior: allow-discrete` 는 [목록의 **57번 주제**](../57-starting-style-and-entry-exit-transitions/)다.
- **블록화(blockification)** — flex/grid 컨테이너의 자식은 `display: inline` 을 줘도 **자동으로 블록 수준으로 끌어올려진다.**\
  `inline-block` 을 줘도 `block` 이 된다. "flex 안에서는 `display` 가 안 먹는다"로 보이는 증상의 정체다.
- **`display: contents` 와 표(`table`)** — 표의 행·셀에 `contents` 를 주면 표 구조가 깨진다.\
  표 레이아웃은 **부모-자식 관계 자체가 규칙**이라 중간을 없애면 성립하지 않는다. 이 목록은 표 레이아웃을 다루지 않는다(README 의 「뺀 것」).
