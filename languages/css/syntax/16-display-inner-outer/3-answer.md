# css/syntax/16 — `display` 의 내부/외부 값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 계산값과 치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getComputedStyle`·`getBoundingClientRect()` 로 읽은 값**이다.\
> 접근성 트리는 같은 Chrome 에 `--force-renderer-accessibility` 를 켜고 CDP `Accessibility.getFullAXTree` 로 덤프한 것이다.\
> 규칙은 [CSS Display Module Level 3](https://drafts.csswg.org/css-display-3/) 과 [CSS Containment Level 2](https://drafts.csswg.org/css-contain-2/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `display` 한 낱말은 무엇 둘을 정하는가

**`display: inline-block` 이 정하는 둘**

- **바깥 = `inline`** — 줄 안에 글자처럼 끼어든다.
- **안 = `flow-root`** — 자식은 보통 흐름으로 쌓되 **독립된 흐름을 연다.**
- 그래서 이름의 "inline" 은 바깥, "block" 은 안쪽 성격을 가리킨 것이고, 정확한 두 값 표기는 **`inline flow-root`** 다.

**`display: block` 을 풀면**

- **`block flow`** — 바깥 `block`, 안 `flow`.

**`display: flow-root` 를 풀면**

- **`block flow-root`** — 바깥 `block`, 안 `flow-root`.

**공유하는 값**

- **안쪽 값 `flow-root`** 다.

```text
                안쪽 값
           flow          flow-root
  바깥 block |  block      |  flow-root    |
       inline| inline      | inline-block  |
                              ^^^^^^^^^^
                     이 열이 「독립된 흐름」을 여는 값들
```

- 그래서 **"`inline-block` 은 마진이 안 샌다"와 "`flow-root` 는 마진이 안 샌다"가 같은 사실**이다. 정본은 [17번](../17-block-formatting-context/2-summary.md).

### 2. 이 선언들은 파싱되는가

**실행 결과** (Chrome 151 headless — 대조군으로 `display: inline-flex` 를 먼저 깔고 덮어썼다)

```text
display: block flow          -> block
display: inline flow-root    -> inline-block
display: flow                -> block
display: flow block          -> block
(대조군 그대로면 inline-flex 가 남는다 — 넷 다 아니었다)
```

**버려지는 것이 있는가**

- **없다. 넷 다 유효하다.** 넷 다 계산값이 대조군 `inline-flex` 에서 바뀌었다.

**각각의 계산값**

- `.a` → **`block`** · `.b` → **`inline-block`** · `.c` → **`block`** · `.d` → **`block`**
- 두 값으로 썼는데 한 낱말이 돌아오는 것은 **버려진 것이 아니라 옛 이름으로 접힌 것**이다.

**안쪽 값만 썼을 때 바깥은**

- **`block`** 으로 채워진다. `display: flow` 의 계산값이 `block` 이었다.
- 반대로 바깥만 쓰면 안쪽은 `flow` 로 채워진다(`display: block` = `block flow`).

**순서를 뒤집으면**

- **결과가 같다.** `flow block` → `block`, `flow-root block` → `flow-root`, `ruby block` → `block ruby` 로 전부 정순과 같았다.
- 두 값은 **순서가 아니라 종류로** 구분된다 — 바깥 값 목록과 안쪽 값 목록이 겹치지 않기 때문이다.

### 3. 이 선언들은 버려지는가

**실행 결과** (Chrome 151 headless — 대조군 `inline-flex`)

```text
display: block block          -> inline-flex   (대조군 그대로 = 버려짐)
display: flex flow            -> inline-flex   (버려짐)
display: inline-block flow    -> inline-flex   (버려짐)
display: block table-row      -> inline-flex   (버려짐)
비교용: display: blorp        -> inline-flex   (당연히 버려짐)
비교용: display: run-in       -> inline-flex   (Chrome 이 모르는 값)
```

**유효한 것이 있는가**

- **없다. 넷 다 버려진다.**
  - `block block` — **바깥 값이 둘**이다.
  - `flex flow` — `flex` 자체가 바깥+안쪽을 다 정하는 값이라 **안쪽 값이 둘**이 된다.
  - `inline-block flow` — **옛 한 낱말 표기와 두 값 문법을 섞을 수 없다.**
  - `block table-row` — `table-row` 는 **표 내부 전용 값**이라 바깥 값을 붙일 수 없다.

**버려졌다는 것을 어떻게 확인하나**

- **`getComputedStyle` 만으로는 안 된다.** `<div>` 에 `display: blorp` 를 주면 계산값이 `block` 인데, 이건 "`blorp` 가 `block` 으로 해석됐다"가 아니라 **선언이 버려지고 `<div>` 의 기본값이 남은 것**이다.
- 방법: **다른 값을 먼저 깔아 대조군을 만든다.**

```text
  .t { display: inline-flex; }     <- 대조군
  .t { display: <시험할 값>; }

  계산값이 inline-flex 면  -> 버려졌다
  그 밖의 값이면           -> 받아들여졌다
```

**에러나 경고가 나오는가**

- **안 나온다.** CSS 는 에러가 없는 언어다 — 모르는 값을 만나면 **그 선언 하나만 조용히 버리고** 규칙의 나머지는 그대로 적용한다.
- 정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(오류 복구).

### 4. 두 값이 그대로 남는 경우

**실행 결과** (Chrome 151 headless)

```text
display: block ruby                 -> block ruby
display: inline ruby                -> ruby
display: inline flow list-item      -> inline list-item
display: block flow list-item       -> list-item
display: block flow-root list-item  -> flow-root list-item
display: inline flow-root list-item -> inline flow-root list-item
```

**`display: block ruby` 의 계산값**

- **`block ruby`** — **두 값이 그대로 남는다.**

**`display: inline flow list-item` 의 계산값**

- **`inline list-item`** — 역시 접히지 않고 남는다(`flow` 만 생략됐다).

**접히는 것과 남는 것의 기준**

- **그 조합에 붙은 옛 한 낱말 이름이 있으면 접힌다.** `block flow` → `block`, `inline flow-root` → `inline-block`.
- **없으면 남는다.** `ruby` 라는 옛 이름은 `inline ruby` 를 뜻하므로 `block ruby` 에는 쓸 이름이 없다. `list-item` 도 `block flow list-item` 만 옛 이름을 갖는다.

**이것이 증거가 되는 이유**

- 만약 두 값 문법이 **파싱되지 않았다면** `block ruby` 도 대조군 값(`inline-flex`)으로 남았어야 한다.
- 실제로는 **선언이 받아들여졌고, 접을 이름이 없어서 두 값이 그대로 직렬화됐다.**\
  즉 브라우저가 **바깥과 안쪽을 따로 들고 있다**는 뜻이다. "한 낱말로 돌려주니 두 값을 모르는 것"이라는 해석을 **반증**한다.

### 5. 인라인 상자에 `width` 를 주면

**실행 결과** (Chrome 151 headless — 두 요소 모두 패딩 8px 좌우, 테두리 2px 좌우)

```text
.a (inline flow)      계산 display=inline        rect.width = 88.64   getComputedStyle().width = 120px
.b (inline flow-root) 계산 display=inline-block  rect.width = 140     getComputedStyle().width = 120px
```

**`.a` 는 120px 을 반영하는가**

- **아니다.** `rect.width` 가 **88.64** — 글자 폭 그대로다. 선언한 120px 은 레이아웃에 쓰이지 않았다.

**`.b` 는**

- **반영한다.** `rect.width` 가 **140** = 선언한 120 + 좌우 패딩 16 + 좌우 테두리 4.

**두 결과가 갈리는 이유**

- **바깥 값이 `inline` 인 것은 둘이 같다.** 갈린 것은 **안쪽 값**이다.
- 안쪽이 `flow` 인 인라인 상자는 **줄 안에서 글자들과 함께 흐르는 조각**이라 자기 치수를 가질 수 없다.
- 안쪽이 `flow-root` 면 **독립된 흐름을 여는 하나의 덩어리**가 되어, 줄 안에 놓이면서도 치수를 가질 수 있다.
- 이것이 **`inline-block` 이 존재하는 이유** 전부다.

**`.a` 의 `getComputedStyle().width`**

- **`120px` 을 돌려준다.** 레이아웃이 안 썼는데도 계산값에는 남아 있다.
- ★ **"계산값에 있다"와 "적용됐다"는 다른 이야기다.** 적용 여부는 `getBoundingClientRect()` 로 재야 안다.

### 6. `display: contents` 는 무엇을 없애는가

**실행 결과** (Chrome 151 headless — flex 컨테이너 안의 래퍼)

```text
보통 래퍼          rect 63.2 x 98    B: y=15   C: y=51   (B·C 가 세로로 쌓인다)
display: contents  rect 0 x 0        B: y=116  C: y=116  (B·C 의 y 가 같다 = 가로로 나란)
                                     B: x=48.52  C: x=95.72
래퍼에 background/padding/border 를 크게 줘도  rect 0 x 0, 자식 좌표 변화 없음
```

**래퍼의 `getBoundingClientRect()`**

- **0×0** 이고 x·y 도 0 이다. **상자가 존재하지 않는다.**

**`B` 와 `C` 는**

- **flex 컨테이너의 직계 자식처럼 다뤄져 flex 항목이 된다.** 실측에서 y 가 같고 x 가 다른 — 가로로 나란한 배치였다.
- 보통 래퍼일 때는 **래퍼 하나만 flex 항목**이고 `B`·`C` 는 그 안에서 세로로 쌓였다.

**`background`·`border`·`padding` 은**

- **전부 화면에서 사라진다.** 실측에서 배경을 초록, 패딩 40px, 테두리 10px 로 크게 줘도 **자식 좌표가 한 픽셀도 안 움직였다.**
- 없어진 것이 아니라 **그릴 상자가 없는** 것이다.

**접근성 트리에서도 사라지는가**

- **아니다. 남았다.** `aria-label` 을 준 `display: contents` 요소가 AX 트리에 `exposed generic` 으로 나왔고 자식도 정상 노출됐다.
- ★ **레이아웃 상자가 없다는 것과 접근성 트리에 없다는 것은 다른 이야기다.**

### 7. 숨기는 세 가지 — 레이아웃

**실행 결과** (Chrome 151 headless)

```text
height: 30px 를 준 경우
  display: none              rect 0 x 0          자리 없음
  visibility: hidden         rect 780 x 32       자리 있음, 아무것도 안 그려짐
  content-visibility: hidden rect 780 x 32       자리 있음, 배경·테두리는 그려짐

height 선언을 지운 경우
  display: none              rect 0 x 0
  visibility: hidden         rect 780 x 21       (글자 높이만큼)
  content-visibility: hidden rect 780 x 2        (테두리 1px 두 겹만)
```

**자리를 차지하는 것**

- **`visibility: hidden` 과 `content-visibility: hidden` 둘.** `display: none` 은 상자를 아예 만들지 않는다.

**자기 배경과 테두리가 그려지는 것**

- **`content-visibility: hidden` 하나뿐이다.**
- 스크린샷으로 확인했다 — 붉은 배경과 회색 테두리가 그대로 보이고 **그 안의 글자만 사라졌다.**
- `visibility: hidden` 은 **완전히 흰 빈칸**이다(배경도 테두리도 안 그려진다).

**`height` 를 지우면**

- `display: none` — 그대로 **0**(원래 상자가 없다).
- `visibility: hidden` — **21**. 안쪽 글자를 정상으로 레이아웃하기 때문이다.
- `content-visibility: hidden` — **2**. 안쪽을 **레이아웃조차 하지 않아** 내용 높이가 0 이 되고 테두리만 남는다.
- 그래서 `content-visibility` 를 쓸 때는 `contain-intrinsic-size` 로 **"대략 이만하다"를 미리 알려 줘야** 스크롤바가 널뛰지 않는다. 성능 쪽 정본은 [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/).

### 8. 숨기는 세 가지 — 접근성 트리

**실행 결과** (Chrome 151 headless + `--force-renderer-accessibility` · CDP `Accessibility.getFullAXTree`)

```text
A-보임         exposed paragraph  + StaticText("보임 알파")
B-none         트리에 아예 없음
C-visibility   트리에 아예 없음
D-contentvis   exposed paragraph  — 그런데 자식 StaticText 가 없다
E-보임         exposed paragraph  + StaticText("보임 오메가")
F-contents     exposed generic    (display: contents 인데 남아 있다)
G-자식         exposed paragraph  + StaticText — 정상
```

**`display: none` 요소**

- **남지 않는다.** 노드 자체가 트리에 없다.

**`visibility: hidden` 요소**

- **남지 않는다.** `display: none` 과 똑같이 트리에서 통째로 빠졌다.

**`content-visibility: hidden` 요소와 그 안의 글자**

- **요소 자신은 남고, 안의 글자는 빠진다.** 실측에서 `aria-label` 이 붙은 그 `<p>` 는 `exposed` 였는데 **자식 텍스트 노드가 없었다.**
- (`aria-label` 없이 같은 실험을 하면 그 요소는 이름도 내용도 없어 `IGNORED / uninteresting` 이 된다 — **이름이 있을 때 노출된다**는 것이 정확한 서술이다.)

**"화면에서 사라진다" = "보조 기술이 못 읽는다"인가**

- **아니다.** 셋 중 어느 것도 "접근성용 도구"가 아니고, 레이아웃·페인트·접근성이 각각 따로 움직인다.
- **읽히되 안 보이게** 하려면 시각적 숨김(클립) 기법을 쓴다 — `display`/`visibility` 로는 못 한다.
- **보이되 안 읽히게** 하려면 `aria-hidden` 을 쓴다 — `display` 로는 못 한다.

### 9. 왜 마진이 새는가

**안쪽 값으로 설명하면**

- `display: block` = **`block flow`** 이고, `flow` 는 **바깥과 이어진 하나의 흐름**이다.
- 같은 흐름 안에 있으면 자식의 위 마진과 부모의 위 마진이 **맞닿아 하나로 합쳐진다.** 그 결과가 "부모 밖으로 샜다"로 보인다.
- 즉 새는 것이 **버그가 아니라 `flow` 의 정의**다. 정본은 [18번](../18-margin-collapsing/2-summary.md).

**막으려면 안쪽 값을**

- **`flow-root`** 로 바꾼다. 그러면 자기 안에서 흐름이 새로 시작되어 마진이 바깥과 만나지 않는다.

**옛 한 낱말 이름**

- **`flow-root`** 다(= `block flow-root`). 바깥이 `block` 인 경우의 옛 이름이 그대로 `flow-root` 다.
- 바깥이 `inline` 이면 같은 안쪽 값의 옛 이름이 **`inline-block`** 이다.

**서식 문맥의 정본**

- [17번 주제](../17-block-formatting-context/2-summary.md)(서식 문맥 — 생성 조건과 효과)다.

### 10. 다른 주제와 잇기

**실행 결과** (Chrome 151 headless — flex/grid 컨테이너의 자식에 준 `display`)

```text
flex 자식에 display: inline        -> 계산값 block
flex 자식에 display: inline-block  -> 계산값 block
flex 자식에 display: inline-flex   -> 계산값 flex
flex 자식에 display: contents      -> 계산값 contents (그대로)
grid 자식에 display: inline        -> 계산값 block
대조: 보통 흐름의 span, display: inline -> 계산값 inline
```

**`display: flex` 를 풀면**

- **`block flex`** — 바깥 `block`, 안 `flex`.
- flex 의 **주축·교차축과 정렬은 [24번 주제](../24-flexbox-axes/2-summary.md)가 정본**이다. 이 문서는 `display` 값의 구조까지만 다룬다.

**`none` ↔ `block` 을 전환에 못 태웠던 이유**

- `display` 의 값은 **키워드**라 시작값과 끝값 사이에 중간값이 없다 — 보간이 성립하지 않는다(보간 가능성의 정본은 [52번 주제](../52-transition/2-summary.md)).
- 게다가 `none` 인 동안에는 **상자 자체가 없어** 애니메이션할 대상이 없다.
- 이 문제를 푸는 `@starting-style` 과 이산 전환은 [목록의 **57번 주제**](../57-starting-style-and-entry-exit-transitions/)다.

**flex 컨테이너의 자식에 `display: inline` 을 주면**

- **`block` 으로 끌어올려진다**(블록화, blockification). 실측에서 계산값이 `block` 이었다.
- `inline-block` 도 `block` 이 되고 `inline-flex` 는 `flex` 가 된다 — **바깥 값만 `block` 으로 바뀌고 안쪽 값은 유지**된다.
- "flex 안에서는 `display` 가 안 먹는다"로 보이는 증상의 정체가 이것이다. 단 `contents` 는 그대로 남았다.

**`content-visibility` 의 Baseline**

- **newly**(2025-09-15, 아직 widely 아님 — 목록 README 의 지원 표).
- 실무에서 뜻하는 바: **오래된 브라우저에서는 이 선언이 통째로 버려져 그냥 보인다.**\
  숨김의 *수단*으로 쓰면 안 되고, **렌더 비용을 아끼는 최적화**로만 써야 안전하다는 뜻이다.

## 용어 풀이

- **외부 display 타입** — 이 상자가 부모의 흐름에 어떻게 참여하나. `block` 또는 `inline`.
- **내부 display 타입** — 이 상자가 자식을 어떻게 배치하나. `flow`·`flow-root`·`flex`·`grid`·`table` 등.
- **`flow`** — 바깥 흐름과 **이어진** 보통 흐름. 마진이 새는 것이 이 값의 정의다.
- **`flow-root`** — 배치는 `flow` 와 같지만 **독립된 흐름을 연다.** `inline-block` 과 같은 안쪽 값.
- **접힘(직렬화)** — 두 값 조합에 옛 한 낱말 이름이 있으면 계산값이 그 이름으로 돌아오는 것. `block flow` → `block`.
- **대조군 판정** — 다른 값을 먼저 깔고 시험 선언으로 덮어, 계산값이 바뀌었는지로 유효/무효를 가리는 방법.
- **`display: contents`** — 상자를 만들지 않고 자식만 남긴다. 배경·테두리·패딩이 사라지지만 접근성 트리에는 남았다.
- **블록화(blockification)** — flex/grid 컨테이너의 자식에서 바깥 값이 자동으로 `block` 으로 올라가는 것.
- **접근성 트리** — 보조 기술이 읽는 트리. 화면에 보이는 것과 일대일이 아니다.
- **`contain-intrinsic-size`** — `content-visibility` 로 안쪽을 건너뛴 상자에 "대략 이만하다"를 알려 주는 속성.
- **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것. 키워드에는 중간값이 없다([52번](../52-transition/2-summary.md)).

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 두 값 문법 파싱 | Chrome 151.0.7922.173 headless · 대조군 `inline-flex` 를 깔고 40여 값을 덮어 `getComputedStyle().display` 판독 | **파싱된다.** 계산값은 옛 이름으로 접힘 |
| 접힘의 예외 | `block ruby`·`inline flow list-item`·`block flow-root list-item` | 두 값 그대로 남음 |
| 무효 조합 | `block block`·`flex flow`·`inline-block flow`·`block table-row`·`run-in` | 전부 대조군 값이 남음 = 버려짐 |
| 순서·생략 | `flow block`·`flow`·`flow-root block` | 순서 무관 · 바깥 생략 시 `block` |
| 인라인의 `width` | `inline flow` 대 `inline flow-root` | 88.64 대 140 — 앞엣것은 무시 |
| `display: contents` | flex 컨테이너 안 래퍼의 rect·자식 좌표 | rect 0×0 · 자식이 flex 항목이 됨 |
| 숨김 3종 레이아웃 | rect 측정 + 스크린샷 | 0×0 / 780×32(안 그려짐) / 780×32(배경·테두리 그려짐) |
| 숨김 3종 높이 붕괴 | `height` 선언 제거 후 재측정 | 0 / 21 / 2 |
| 숨김 3종 접근성 | `--force-renderer-accessibility` + CDP `Accessibility.getFullAXTree` | none·visibility 는 트리에 없음 · content-visibility 는 요소만 남음 |
| 블록화 | flex/grid 자식의 계산값 | `inline`·`inline-block` → `block` · `inline-flex` → `flex` |
| demo 3개 | 각 블록을 `<!doctype>`·`<body>` 래퍼에 넣어 렌더 + 스크린샷 | 「보이는 것」 3건 모두 화면과 일치 |

**구현 의존 항목** — **계산값 직렬화 형태**(어떤 조합이 접히고 어떤 것이 남는가)와 **`display: contents` 의 접근성 트리 노출**은 Chrome 151 에서 관찰한 것이다. 버전이 오르면 이 두 칸을 다시 찍는다.\
`content-visibility` 는 Baseline **newly** 라 **더 오래된 브라우저에서는 선언 자체가 버려진다.**\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**
