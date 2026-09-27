# css/syntax/49 — `clip-path` 와 `mask` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다. ★ **답을 픽셀 값·좌표로 적어라** — 「잘린다」는 답이 아니다.
> 잘렸는지는 **그 자리가 페이지 배경색으로 돌아왔는지**로 판정한다.
> ★ 이 주제에서 `getComputedStyle` 은 **거짓 안심**을 준다. 계산값이 멀쩡한데 요소가 통째로 사라지는 경우가 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 잘린 자리에 무엇이 보이나 (예측)

```css
/* 페이지 배경 #ffcc00, 상자 #1d4ed8 120x120 */
.a { clip-path: inset(20px); }
.b { clip-path: circle(45px at 60px 60px); }
.c { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
```

- `.a` 의 왼쪽 위 모서리 픽셀은 무엇인가 — 투명인가, 상자색인가, 페이지 배경색인가?
- 세 상자의 `getBoundingClientRect().width` 는 잘리기 전과 후에 달라지는가?
- 도형 밖 좌표에 `document.elementFromPoint()` 를 던지면 무엇이 나오는가?
- 옆 요소는 잘린 만큼 당겨지는가?

### 2. 어느 상자를 자르나 (예측)

```css
/* border 10px + padding 20px + content 80px 인 상자 */
.p { clip-path: inset(0); }
.q { clip-path: inset(0) padding-box; }
.r { clip-path: inset(0) content-box; }
```

- `.p` 에서 테두리 자리의 픽셀은 테두리색인가 페이지 배경색인가?
- `.q` 는?
- `.r` 에서 패딩 자리는?
- `getComputedStyle().clipPath` 가 `.p`·`.q`·`.r` 에서 각각 무엇을 돌려주는가 — `.p` 에 `border-box` 를 명시하면 어떻게 직렬화되는가?

### 3. `overflow: hidden` 과 무엇이 다른가 (예측)

```css
.a { overflow: hidden; }            /* 둘 다 box-shadow: 0 0 0 12px red */
.b { clip-path: inset(0); }         /* 둘 다 삐져나온 자식이 있다 */
```

- 삐져나온 자식은 두 판에서 각각 잘리는가?
- **자기 `box-shadow`** 는 두 판에서 각각 어떻게 되는가?
- 둘 중 스크롤 컨테이너를 만드는 것은 어느 쪽인가?
- 둘 중 BFC 를 만드는 것은 어느 쪽인가?

### 4. `clip-path` 가 무엇을 건드리나 — 던져서 확인 (예측)

```css
.wrap { clip-path: inset(0); }
.up   { position: absolute; z-index: 9999; }   /* .wrap 의 자식 */
.over { position: absolute; z-index: 1; }      /* .wrap 의 형제 */
.fx   { position: fixed; left: 0; top: 0; }    /* .wrap 의 자식 */
```

- `.up` 과 `.over` 가 겹치는 자리는 무슨 색인가 — 쌓임 맥락이 생겼는가?
- `.fx` 의 좌표는 `(0,0)` 인가 `.wrap` 의 모서리인가?
- `.fx.offsetParent` 는 무엇인가?
- 이 결과는 [47번](../47-filter-and-backdrop-filter/2-summary.md)의 `filter` 와 같은가 다른가?

### 5. 같은 이미지, 정반대 결과 (예측)

**알파가 전부 255 이고 색만 검정 → 흰색으로 변하는** PNG 를 마스크로 쓴다.

```css
.a { mask-image: url(그PNG); mask-mode: alpha; }
.b { mask-image: url(그PNG); mask-mode: luminance; }
.c { mask-image: url(그PNG); }                      /* 기본값 */
```

- `.a` 의 왼쪽 끝·오른쪽 끝 픽셀은 각각 무엇인가?
- `.b` 는?
- `.c` 는 `.a` 와 같은가 `.b` 와 같은가 — `mask-mode` 의 기본값 이름은?
- 그 기본값이 **휘도**가 되는 경우는 언제인가?

### 6. 페이드 아웃이 안 된다 (예측)

```css
.a { mask-image: linear-gradient(to right, #000, #fff); }
.b { mask-image: linear-gradient(to right, #000, transparent); }
```

- `.a` 의 오른쪽 끝 픽셀은 무엇인가?
- `.b` 의 오른쪽 끝은?
- `.a` 를 의도대로 만들려면 어느 선언 한 줄을 더하면 되는가?
- 왜 `#fff` 가 「보이게 하는 흰색」으로 안 읽히는가?

### 7. `-webkit-mask-` 는 아직 필요한가 (경계)

```css
.c { -webkit-mask-image: linear-gradient(#000, transparent); }
.d { mask-image: linear-gradient(#000, transparent); -webkit-mask-image: none; }
```

- `.c` 의 규칙은 `cssRules` 에 어떤 텍스트로 남는가?
- `.d` 의 계산된 `mask-image` 는 무엇인가 — 왜 그런가?
- 지금 무접두사만 써도 되는 근거는 무엇인가(Baseline 값으로 답하라)?
- 「호환을 위해 둘 다 쓰자」가 왜 위험한가?

### 8. 단축 `mask` 의 함정 (경계)

```css
.a { mask-mode: luminance; mask: linear-gradient(#000, #fff); }
.b { mask: linear-gradient(#000, #fff); mask-mode: luminance; }
```

- `.a` 의 계산된 `mask-mode` 는 무엇인가?
- `.b` 는?
- 두 규칙이 `cssRules` 에 각각 어떻게 직렬화되는가?
- 같은 성격의 함정을 가진 다른 단축 속성을 하나 대라.

### 9. 계산값이 멀쩡한데 안 보인다 (왜)

```css
.x { clip-path: polygon(50%, 100% 100%); mask-mode: alpha-zz; mask-image: url(#nope); }
```

- 「진단 3창」에서 셋 중 무엇이 살아남는가?
- 살아남은 선언의 계산값은 무엇인가?
- 그 요소는 화면에 보이는가 — 안 보인다면 그 자리의 픽셀은 무엇인가?
- 이것을 무엇이라 부르고, 실무에서 이 상태를 피하려면 무엇을 해야 하는가?

### 10. 다른 주제로 잇기 (연결)

- `inset()` 의 `round` 키워드는 어느 주제의 문법을 그대로 재사용하는가?
- `mask-size`·`mask-repeat`·`mask-position` 은 어느 주제의 축과 짝인가?
- `mask-composite` 가 합치는 것은 색인가 알파인가 — 색을 합치는 쪽은 몇 번 주제인가?
- `clip-path` 가 만드는 쌓임 맥락은 [48번](../48-blend-modes-and-isolation/2-summary.md)에서 무엇으로 쓰이는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
