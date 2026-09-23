# css/syntax/36 — 사용자 정의 속성: 선언·`var()`·대체값·상속 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다. ★ **답을 「창」별로 나눠 적어라** —
> ① `cssRules` 에 담겼나 ② 변수의 **계산값**은 무엇인가 ③ **쓰는 쪽 속성**의 계산값은 무엇인가.
> 「안 먹는다」는 답이 아니다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 오타가 난 변수는 어디서 죽는가 (예측)

```css
#p  { color: green; }
#a  { --x: redd; color: var(--x); background-color: #fde68a; }
```

- `#a` 규칙의 `cssRules` 속성 목록에는 무엇이 들어 있는가?
- `getComputedStyle(#a).getPropertyValue('--x')` 는 무엇을 돌려주는가?
- `getComputedStyle(#a).color` 는 무엇인가? 그 값은 `initial` 과 같은가 `unset` 과 같은가?
- `background-color` 는 어떻게 되는가?
- 같은 오타를 **보통 속성**(`color: redd`)에 냈을 때와 무엇이 다른가?

### 2. 앞선 선언으로 돌아가는가 (예측)

```css
#p { color: green; }
#d { --x: redd; color: red; color: var(--x); }
```

- `#d` 의 계산된 `color` 는 red 인가, green 인가, 검정인가?
- 이 결과가 「점진적 향상」에 시사하는 바는 무엇인가?

### 3. ★ 대체값은 언제 쓰이나 (예측)

```css
#b { color: var(--nope); }
#c { color: var(--nope, green); }
#d { --x: redd;   color: var(--x, green); }
#k { --empty: ;   color: var(--empty, teal); }
```

- 네 경우 중 **대체값이 실제로 쓰인 것**은 어느 것인가?
- `#k` 가 결정적인 근거인 이유는 무엇인가?
- 「대체값을 넣어 두면 오타가 막힌다」는 왜 틀린가?

### 4. 대체값 안의 쉼표 (경계)

```css
.g { border: var(--brd, 1px solid red); }
.f { font-family: var(--ff, "Courier New", monospace); }
.h { color: var(--p, var(--q, teal)); }
```

- 셋 다 동작하는가? `var()` 의 인자를 자르는 규칙은 무엇인가?
- `var(--ff, "Courier New", monospace)` 에서 대체값은 정확히 무엇인가?

### 5. ★ 순환 참조를 던져 본다 (예측)

```css
#p   { color: green; }
#cyc { --a: var(--b); --b: var(--a); color: var(--a); }
#f   { --a: var(--b); --b: var(--a); color: var(--a, purple); }
#s   { --s: var(--s); color: var(--s, navy); }
```

- 세 경우의 `--a`(또는 `--s`) 계산값은 무엇인가?
- 세 경우의 `color` 는 각각 무엇인가?
- 대체값이 있는 쪽과 없는 쪽이 갈리는 이유를 「**보장된 무효**」라는 낱말로 설명할 수 있는가?

### 6. ★ 대소문자를 가리는가 (예측)

```css
#e { --X: blue; color: var(--x, orange); }
```

- `#e` 의 계산된 `color` 는 무엇인가?
- 보통 속성 이름(`COLOR`)과 무엇이 다른가?
- `--ws:    hello   world   ;` 를 선언하면 계산값은 정확히 어떤 문자열인가?

### 7. ★ 무엇이 상속되는가 — 토큰인가 값인가 (예측)

```css
#tp { font-size: 20px; text-indent: 2em; --len: 2em; }
#tc { font-size: 40px; width: var(--len); }   /* #tp 의 자식 */
```

- `#tp` 와 `#tc` 의 계산된 `text-indent` 는 각각 몇 px 인가?
- `#tp` 와 `#tc` 의 계산된 `--len` 은 각각 무엇인가?
- `#tc` 의 계산된 `width` 는 몇 px 인가? 왜 그 숫자인가?
- `--a: 10px; --b: var(--a); --c: calc(var(--b) * 3)` 에서 `--c` 의 **계산값 문자열**은 무엇인가?

### 8. ★ 두 조상이 같은 변수를 선언하면 (예측)

```css
.far  { --tone: red; }
#near { --tone: blue; }      /* .far 의 자식 */
#leaf { color: var(--tone); }  /* #near 의 자식 */

#hi    { --tone2: red; }      /* ID 선택자 */
.lo    { --tone2: blue; }     /* #hi 의 자식, 클래스 선택자 */
#leaf2 { color: var(--tone2); }
```

- 두 경우의 `color` 는 각각 무엇인가?
- 두 번째 경우에서 **명시도가 높은 `#hi` 가 지는** 이유는 무엇인가?
- 이 성질이 실무에서 무엇을 가능하게 하는가?

### 9. `:root` 관행의 한계 (경계)

- `:root` 에 변수를 두면 문서 전체가 읽는 이유는 무엇인가? 특별한 기능인가?
- `@media (min-width: var(--bp, 100px))` 는 동작하는가? 규칙 자체는 `cssRules` 에 담기는가?
- `--prop: color; var(--prop): red` 는 어떻게 되는가?

### 10. 이름 규칙과 JS (경계)

- `--: 1px` · `--1: red` · `--가나: blue` · `-x: red` 중 커스텀 속성으로 인정되는 것은?
- JS 로 쓸 때 `el.style.setProperty('--j','120px')` 와 `el.style['--j']='120px'` 중 무엇이 통하는가?
- `getComputedStyle(el).getPropertyValue('--j')` 와 `el.style.getPropertyValue('--j')` 는 무엇이 다른가?

### 11. ★ 애니메이션 (예측)

```css
@keyframes k { from { --w: 0px } to { --w: 200px } }
#an { --w: 0px; animation: k 10s linear forwards; width: var(--w); }
```

- 2초·4초·6초·9초 시점의 `width` 는 각각 몇 px 인가?
- 「안 움직인다」가 정확한 서술인가? 아니라면 정확한 서술은?
- 같은 조건으로 보통 `width` 를 애니메이션하면 5초 시점에 무엇이 나오는가?
- 이것을 푸는 기능은 무엇이고 목록의 몇 번 주제인가?

### 12. 다른 주제로 잇기 (연결)

- 보통 속성의 무효 값이 **선언째 버려지는** 규칙의 정본은 몇 번 주제인가?
- **`unset` 이 무엇인가**의 정본은 몇 번 주제인가?
- **명시도가 같은 요소의 선언끼리만 겨룬다**는 규칙의 정본은 몇 번 주제인가?
- 커스텀 속성이 **CSS 에 들어온 경위**는 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
