# css/syntax/49 — `clip-path` 와 `mask` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 색은 Google Chrome 151.0.7922.173 headless 로 렌더한 스크린샷 PNG 를 파이썬 표준 라이브러리(`zlib`)로 디코드해 그 좌표의 `(r,g,b)` 를 읽은 값**이고,
> **좌표·계산값은 `getBoundingClientRect()`·`offsetParent`·`getComputedStyle()`·`document.elementFromPoint()` 로 읽은 값**이다.\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [CSS Masking 1](https://drafts.csswg.org/css-masking-1/)·[CSS Shapes 1](https://drafts.csswg.org/css-shapes-1/#basic-shape-functions) 으로 접지했다.\
> ★ 렌더는 `--disable-gpu` **소프트웨어 렌더링**이다. 정확한 픽셀 값을 「보장」으로 읽지 마라.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 잘린 자리에 무엇이 보이나

**실행 결과** (Chrome 151 headless — 페이지 `#ffcc00` = `(255,204,0)`, 상자 `#1d4ed8` = `(29,78,216)`)

```text
함수                               도형 안         도형 밖
inset(20px)                       (29,78,216)   (255,204,0)
circle(45px at 60px 60px)         (29,78,216)   (255,204,0)
ellipse(50px 25px at 60px 60px)   (29,78,216)   (255,204,0)
polygon(50% 0, 100% 100%, 0 100%) (29,78,216)   (255,204,0)
path('M 0 0 L 120 0 L 120 60 Z')  (29,78,216)   (255,204,0)

rect 는 다섯 판 모두 120x120 으로 동일

elementFromPoint(원 안)  -> DIV#b
elementFromPoint(원 밖)  -> HTML          ★ 상자가 아니라 그 아래 요소가 나온다
```

**모서리 픽셀**

- **페이지 배경색 `(255,204,0)`** 이다. 「투명해진」 것이 아니라 **그 요소가 그려지지 않은** 것이라 뒤에 있던 것이 그대로 나온다.

**`rect.width`**

- **안 달라진다.** 다섯 판 모두 120×120 이었다.

**`elementFromPoint`**

- **그 아래 요소**가 나온다. 클리핑은 **히트 테스트에도 적용**되므로 잘린 밖은 이벤트를 안 받는다.
- demo 에서도 원 밖 좌표에 던지니 `.s1` 이 아니라 부모 `.page` 가 나왔다.

**옆 요소**

- **안 당겨진다.** 레이아웃 치수가 그대로이므로 잘린 자리가 차지하던 공간은 남는다.

### 2. 어느 상자를 자르나

**실행 결과** (Chrome 151 headless — border 10px + padding 20px + content 80px)

```text
선언                    테두리 자리      패딩 자리       내용 자리
inset(0)               (148,163,184)  (29,78,216)   (29,78,216)
inset(0) padding-box   (255,204,0)    (29,78,216)   (29,78,216)
inset(0) content-box   (255,204,0)    (255,204,0)   (29,78,216)

계산값
inset(0)               "inset(0px)"
inset(0) border-box    "inset(0px)"                 ★ border-box 가 사라진다
inset(0) padding-box   "inset(0px) padding-box"
inset(0) content-box   "inset(0px) content-box"
circle(40px) margin-box "circle(40px) margin-box"
```

**`.p` 의 테두리 자리**

- **테두리색 `(148,163,184)`** 이다. 기본 참조 상자가 `border-box` 라 테두리까지 남는다.

**`.q`**

- **페이지 배경색 `(255,204,0)`** 이다. `padding-box` 로 자르면 테두리가 잘려 나간다.

**`.r` 의 패딩 자리**

- **페이지 배경색**이다. `content-box` 는 테두리와 패딩을 둘 다 잘라낸다.

**계산값**

- `.p` 는 `"inset(0px)"`, `.q` 는 `"inset(0px) padding-box"`, `.r` 은 `"inset(0px) content-box"` 다.
- ★ `border-box` 를 **명시해도 계산값에서 사라진다.** 기본값이라 직렬화에서 생략된다 — 곧 **계산값만 봐서는 명시했는지 알 수 없다.**

### 3. `overflow: hidden` 과 무엇이 다른가

**실행 결과** (Chrome 151 headless)

```text
                      삐져나온 자식 자리     자기 box-shadow 자리   본체
overflow: hidden      (220, 38, 38)        (220, 38, 38)        (29,78,216)
clip-path: inset(0)   (255,204,  0)        (255,204,  0)        (29,78,216)

BFC 실험 — 자식에게 margin-top: 40px 을 주고 부모 높이를 잰다
(아무것도 없음)         부모 높이 20   마진이 새어 나갔다
overflow: hidden       부모 높이 60   갇혔다 = BFC
clip-path: inset(-999px) 부모 높이 20   새어 나갔다 = BFC 아님
```

**삐져나온 자식**

- **두 판 모두 잘린다.**
- `overflow` 판에서 그 자리에 보이는 `(220,38,38)` 은 자식이 아니라 **그 아래 빨간 그림자**다.

**자기 `box-shadow`**

- `overflow: hidden` 은 **남긴다**(`(220,38,38)`).
- `clip-path` 는 **자른다**(`(255,204,0)` 페이지 배경). 요소 자신이 클리핑 대상이기 때문이다.

**스크롤 컨테이너**

- **`overflow` 쪽**이다. `clip-path` 는 스크롤 컨테이너를 안 만든다.

**BFC**

- **`overflow` 쪽**이다. 실측에서 `overflow: hidden` 판만 자식 마진이 갇혀 부모 높이가 60 이 됐고, `clip-path` 판은 20 이었다(마진이 새어 나갔다).
- BFC 의 정본은 [17번](../17-block-formatting-context/2-summary.md)이다.

### 4. `clip-path` 가 무엇을 건드리나 — 던져서 확인

**실행 결과** (Chrome 151 headless)

```text
실험 1 — 쌓임 맥락
wrap 의 선언             겹침 픽셀        판정
(없음)                   (220, 38, 38)   z-index:9999 자식이 이김
clip-path: inset(0)      ( 37, 99,235)   형제가 위 — 쌓임 맥락이 생겼다

실험 2 — fixed 자손의 포함 블록
wrap 의 선언             host 좌표     fixed 자식      offsetParent
(없음)                   ( 20,200)    (0, 0)         null
clip-path: inset(0)      (220,200)    (0, 0)         null      ★ 안 바뀐다
```

**겹치는 자리**

- **파랑 `(37,99,235)`** 이다. `z-index: 9999` 가 갇혔으므로 **쌓임 맥락이 생겼다.**

**`.fx` 의 좌표**

- **`(0,0)`** — 뷰포트 기준 그대로다.

**`offsetParent`**

- **`null`** 이다. 포함 블록이 안 바뀌었다.

**`filter` 와 같은가**

- ★ **다르다.** [47번](../47-filter-and-backdrop-filter/2-summary.md) 실측에서 `filter: brightness(1)` 은 `fixed` 자식을 `(400,90)` 으로 끌어가고 `offsetParent` 를 `host` 로 바꿨다.

```text
                      쌓임 맥락   fixed 포함 블록
  filter               O           O
  clip-path            O           X      ★ 여기서 갈린다
```

- **추측했으면 틀렸을 자리**다. 둘 다 「합성 단계의 부작용」처럼 보이지만 포함 블록 축은 다르다.

### 5. 같은 이미지, 정반대 결과

**실행 결과** (Chrome 151 headless — 알파가 전부 255, 색만 검정→흰색인 16×4 PNG)

```text
mask-mode       왼쪽 끝          중간            오른쪽 끝
alpha           (29, 78,216)   (29, 78,216)   (29, 78,216)
luminance       (255,255,255)  (129,156,233)  (29, 78,216)
match-source    (29, 78,216)   (29, 78,216)   (29, 78,216)
```

**`.a`(alpha)**

- 왼쪽·오른쪽 **둘 다 `(29,78,216)`** — 전부 보인다. 이미지의 **알파가 전 영역 255** 이기 때문이다.

**`.b`(luminance)**

- 왼쪽 `(255,255,255)`(완전히 사라짐) → 오른쪽 `(29,78,216)`(원색). **밝기를 읽었다.**

**`.c`(기본값)**

- **`.a` 와 같다.** 기본값 이름은 **`match-source`** 다.

**기본값이 휘도가 되는 경우**

- 마스크가 **SVG 의 `<mask>` 요소를 참조**할 때다. 이미지(PNG·그라디언트 포함)면 알파다.
- 그래서 **포토샵·SVG 습관(검정=숨김)과 CSS 기본값이 어긋난다.**

### 6. 페이드 아웃이 안 된다

**실행 결과** (Chrome 151 headless — 다섯 지점을 왼쪽부터)

```text
마스크                                      다섯 지점
linear-gradient(to right,#000,#fff)         (29,78,216) 다섯 번 — 전부 원색
같은 것 + mask-mode: luminance               (249,250,254) → … → (33,81,217)
linear-gradient(to right,#000,transparent)  (35,83,217) → … → (250,251,254)
linear-gradient(to right,transparent,#000)  (249,250,254) → … → (34,82,217)
```

**`.a` 의 오른쪽 끝**

- **`(29,78,216)`** — 원색 그대로다. **아무 일도 안 일어났다.**

**`.b` 의 오른쪽 끝**

- **`(250,251,254)`** — 거의 배경색이다. 사라졌다.

**`.a` 를 의도대로 만들려면**

- **`mask-mode: luminance;`** 한 줄을 더한다. 그러면 왼쪽부터 사라진다(위 표 두 번째 줄).

**왜 `#fff` 가 안 읽히나**

- `mask-mode` 의 기본값 `match-source` 는 **그라디언트도 이미지로 보고 알파를 읽는다.**
- `#000` 도 `#fff` 도 **알파는 1** 이다. 마스크가 전 영역 1 이 되어 전부 보인다.
- 고치는 법은 두 가지 — **색 대신 알파를 쓰거나**(`transparent`), **모드를 휘도로 바꾸거나**.

### 7. `-webkit-mask-` 는 아직 필요한가

**실행 결과** (Chrome 151 headless — 「진단 3창」의 창 1·3)

```text
던진 것                                          cssRules 에 남은 것
.c { -webkit-mask-image: linear-gradient(…) }    .c { mask-image: linear-gradient(…); }
.d { mask-image: linear-gradient(…);             .d { mask-image: none; }
     -webkit-mask-image: none }
계산값: .d 의 maskImage = none · webkitMaskImage = none
```

**`.c` 의 규칙 텍스트**

- **`mask-image`** 로 바뀌어 남는다. 접두사가 사라진다.

**`.d` 의 계산값**

- **`none`** 이다. `-webkit-mask-image` 가 **같은 속성의 별칭**이라 **나중에 쓴 쪽이 이겼다.**

**무접두사만 써도 되는 근거**

- webstatus.dev 조회(2026-09-23) — `masks`(Masks)가 **Baseline widely**, low 2023-12-07 / high 2026-06-07.
- 브라우저별로 Chrome 120(2023-12-05)·Firefox 53(2017-04-19)·Safari 15.4(2022-03-14).

**「둘 다 쓰자」가 위험한 이유**

- 별칭이므로 **순서가 캐스케이드를 결정한다.** 접두사판을 뒤에 쓰면 무접두사판이 조용히 덮인다.
- 에러도 경고도 없다. 실측의 `.d` 가 정확히 그 사고였다.
- ★ 다만 이 판정은 **Chrome 151 의 관찰**이다. 아주 오래된 Safari 를 지원해야 한다면 사정이 다를 수 있다.

### 8. 단축 `mask` 의 함정

**실행 결과** (Chrome 151 headless)

```text
.a { mask-mode: luminance; mask: linear-gradient(#000,#fff) }
   cssRules: .a { mask: linear-gradient(rgb(0,0,0), rgb(255,255,255)); }
   계산값 mask-mode = match-source          ★ 지워졌다

.b { mask: linear-gradient(#000,#fff); mask-mode: luminance }
   cssRules: .b { mask: linear-gradient(rgb(0,0,0), rgb(255,255,255)) luminance; }
   계산값 mask-mode = luminance             ○
```

**`.a` 의 `mask-mode`**

- **`match-source`** 다. 단축이 앞의 선언을 초깃값으로 되돌렸다.

**`.b`**

- **`luminance`** 다.

**직렬화**

- `.a` 는 **하나의 `mask:` 선언**으로 합쳐지고, `.b` 는 `mask: … luminance` 로 모드까지 포함해 합쳐진다.
- 곧 **단축과 하위 속성이 한 규칙에 있으면 하나로 합쳐 다시 쓴다.**

**같은 성격의 단축**

- **`background`** 다. `background: red` 한 줄이 `background-image`·`background-position` 등을 전부 초깃값으로 되돌린다([목록의 **44번 주제**](../44-backgrounds-and-object-fit/)).
- `border`·`font`·`flex` 도 같은 성격이다.

### 9. 계산값이 멀쩡한데 안 보인다

**실행 결과** (Chrome 151 headless — 「진단 3창」)

```text
입력  .x { clip-path: polygon(50%, 100% 100%); mask-mode: alpha-zz; mask-image: url(#nope); }

창 1  cssRules[0] = .x { mask-image: url("#nope"); }    앞의 둘은 사라졌다
창 2  querySelectorAll('.x').length = 1                 잡혔다
창 3  clip-path = none · mask-mode = match-source · mask-image = url("#nope")

화면  그 요소 자리의 픽셀 = (255,204,0) = 페이지 배경     ★ 통째로 사라졌다
대조  마스크 없는 판 = (29,78,216) · 깨진 data URI 판 = (255,204,0)
```

**살아남는 것**

- **`mask-image: url(#nope)` 하나**다. 문법상 유효한 URL 이라 파서가 받는다.
- `clip-path: polygon(50%, 100% 100%)` 은 좌표가 한 쌍이 아니라 무효, `mask-mode: alpha-zz` 는 값 이름이 틀려 무효다.

**계산값**

- `url("#nope")` 를 **그대로 돌려준다.** 참조가 안 풀린다는 사실은 계산값에 안 나타난다.

**화면**

- **안 보인다.** 그 자리의 픽셀이 페이지 배경 `(255,204,0)` 이었다.
- 깨진 `data:` URI 를 마스크로 줘도 같았다 — 「마스크 없음」이 아니라 「**전부 가리는 마스크**」처럼 동작했다.

**이름과 대책**

- **제4의 상태**다 — 「진단 3창」을 전부 통과하는데 화면이 다른 경우.
- 대책은 **깨진 참조를 남기지 않는 것**이다. 마스크를 지울 때는 `mask-image: none` 으로 지운다.
- ★ 이 동작은 **Chrome 151 에서 관찰한 것**이다. 「마스크 없음으로 취급」하는 구현이 있을 수 있으므로 더더욱 남기면 안 된다.

### 10. 다른 주제로 잇기

**`inset()` 의 `round`**

- **`border-radius` 문법**을 그대로 재사용한다. 정본은 [46번](../46-borders-radius-outline-shadow/2-summary.md)이다.
- 실측에서 `inset(10px 30px round 18px)` 의 모서리 픽셀이 `(255,204,0)` 배경이었고, `round 18px` 를 지우니 `(29,78,216)` 상자색이 되어 각졌다.

**`mask-size`·`mask-repeat`·`mask-position`**

- **배경 속성**의 같은 축과 짝이다. 정본은 [목록의 **44번 주제**](../44-backgrounds-and-object-fit/)다. 값 문법이 그대로 같다.

**`mask-composite`**

- **알파**를 합친다. 색을 합치는 쪽은 [48번](../48-blend-modes-and-isolation/2-summary.md)(`mix-blend-mode`·`background-blend-mode`)이다.
- 실측: `intersect` 로 두 그라디언트를 합치니 양 끝 `(243,245,253)`·`(245,247,253)`(거의 배경), 가운데 `(41,88,218)`(거의 원색)이 됐다.

**`clip-path` 가 만드는 쌓임 맥락**

- [48번](../48-blend-modes-and-isolation/2-summary.md)에서 **격리**로 쓰인다. 쌓임 맥락을 만드는 선언은 전부 자손의 `mix-blend-mode` 를 그 자리에서 끊는다.

## 용어 풀이

- **`clip-path`** — 요소를 도형 안쪽만 남기고 잘라내는 선언. 이분법이고 레이아웃 치수는 안 바꾼다.
- **도형 함수(basic shape)** — `inset()`·`circle()`·`ellipse()`·`polygon()`·`path()`.\
  예: `polygon(50% 0, 100% 100%, 0 100%)` 은 위를 향한 삼각형이다.
- **`<geometry-box>`** — 도형의 기준 상자. 기본은 `border-box` 이고, 명시해도 계산값에서 생략된다.
- **알파(alpha)** — 픽셀의 불투명도. `transparent` 는 0, `#fff` 는 1 이다 — 마스크에서 갈리는 것은 색이 아니라 이 값이다.
- **휘도(luminance)** — 픽셀의 밝기. `mask-mode: luminance` 가 읽는 값. 검정이 0, 흰색이 최대다.
- **`mask-mode`** — 알파를 읽을지 휘도를 읽을지. 기본 `match-source` 는 이미지면 알파, SVG `<mask>` 참조면 휘도다.
- **`mask-composite`** — 마스크 레이어들의 알파를 합치는 규칙. `add`(기본)·`subtract`·`intersect`·`exclude`.
- **히트 테스트(hit testing)** — 어느 좌표를 눌렀을 때 어느 요소가 잡히는지 정하는 계산.\
  예: `document.elementFromPoint(x, y)`. `clip-path` 로 잘린 밖에서는 그 아래 요소가 나온다.
- **BFC(블록 서식 맥락)** — 마진 상쇄·부동 겹침을 그 안에 가두는 독립 구역. `overflow: hidden` 은 만들고 `clip-path` 는 안 만든다. 정본은 [17번](../17-block-formatting-context/2-summary.md).
- **제4의 상태** — 「진단 3창」을 전부 통과하는데 화면이 다른 상태. 여기서는 **깨진 마스크 참조**다.
- **진단 3창** — `cssRules` → `querySelectorAll` → `getComputedStyle`. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 도형 함수 다섯 | 노란 페이지 위 파란 상자 여섯 판을 렌더해 안팎 픽셀 | 도형 밖이 전부 `(255,204,0)` 페이지 배경 |
| 잘려도 치수가 그대로인 것 | `getBoundingClientRect()` | 다섯 판 모두 120×120 |
| 잘린 밖의 이벤트 | `document.elementFromPoint()` | 도형 밖에서 `HTML`(또는 부모)이 나옴 |
| `<geometry-box>` | border 10 + padding 20 상자 셋의 테두리·패딩 픽셀 | 기본 `border-box` · `padding-box` · `content-box` 가 각각 다르게 잘림 |
| 같은 것의 계산값 | `getComputedStyle().clipPath` | `border-box` 는 **생략돼 직렬화**됨 |
| `overflow` 와의 차이 | 그림자 있는 상자 + 삐져나온 자식, 두 판 | 자기 그림자가 `(220,38,38)` 대 `(255,204,0)` |
| BFC 를 만드나 | 자식 `margin-top:40px` 로 부모 높이 측정 | `overflow` 60 · `clip-path` 20 (**BFC 아님**) |
| 쌓임 맥락을 만드나 | `z-index:9999` 자식과 형제의 겹침 픽셀 | `(220,38,38)` → `(37,99,235)` (**만든다**) |
| `fixed` 포함 블록 | `rect`·`offsetParent` 두 판 | 둘 다 `(0,0)`·`null` (**안 가로챈다**) |
| 알파 마스크 대 휘도 마스크 | 알파 255·휘도 그라디언트인 PNG(data URI) 한 장으로 세 판 | `alpha` 전부 보임 · `luminance` 왼쪽 사라짐 |
| 삼각형 PNG 로 재확인 | 같은 이미지, 두 모드 | `alpha` 는 삼각형 · `luminance` 는 거의 전부 사라짐 |
| 그라디언트 마스크 | 네 판을 다섯 지점씩 | `#000→#fff` 는 **무변화** · `transparent` 판만 페이드 |
| `mask-composite: intersect` | 두 겹 그라디언트 한 판 | 양 끝 배경 · 가운데 원색 |
| `-webkit-mask-` | 두 규칙을 던져 `cssRules` 대조 | **별칭** — 접두사가 무접두사로 직렬화되고 순서로 덮임 |
| 단축 `mask` 의 리셋 | 순서를 바꾼 두 규칙 | 앞의 `mask-mode` 가 `match-source` 로 되돌아감 |
| 깨진 마스크 참조 | `url(#nope)`·깨진 data URI 두 판 | 계산값 정상인데 **픽셀이 페이지 배경** |
| 무효 값 | 「진단 3창」 | `polygon(50%, …)`·`alpha-zz` 가 `cssRules` 에서 사라짐 |
| demo 4개 | 각 블록을 `<!doctype>`·`<body>` 래퍼에 넣어 렌더 + 픽셀 대조 | 「보이는 것」·「바꿔 볼 것」 단언 전부 화면과 일치 |

**구현 의존 항목** — ①깨진 참조 마스크에서 **요소가 통째로 사라지는** 것 ②`-webkit-mask-*` 가 **별칭**이라 순서로 덮이는 것 ③`clip-path` 가 포함 블록을 안 가로채는 것(명세의 포함 블록 목록까지 대조하지는 않았다) ④각 픽셀의 정확한 값과 경계 안티앨리어싱 — `--disable-gpu` **소프트웨어 렌더링** 결과다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.** 크로스 브라우저는 Baseline 데이터로만 접지했다(webstatus.dev 조회 2026-09-23: `clip-path` widely 2021-01-21/2023-07-21 · `masks` widely 2023-12-07/2026-06-07).
