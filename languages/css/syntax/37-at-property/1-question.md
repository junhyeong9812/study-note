# css/syntax/37 — `@property`: 타입 등록·초기값·상속 여부 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 「등록 전후에 무엇이 달라지나」를 **값으로 맞히는 것**이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 등록하면 애니메이션이 된다 (예측)

```html
<div class="u">u</div>
<div class="r">r</div>
<style>
  @property --rw { syntax: "<length>"; inherits: false; initial-value: 0px; }
  @keyframes u { from { --uw: 0px }  to { --uw: 200px } }
  @keyframes r { from { --rw: 0px }  to { --rw: 200px } }
  .u { --uw: 0px; width: var(--uw); animation: u 10s linear -5s paused; }
  .r { --rw: 0px; width: var(--rw); animation: r 10s linear -5s paused; }
</style>
```

- 진행률 50% 에서 멈춘 두 막대의 `width` 는 각각 얼마인가?
- 같은 실험을 25% 와 75% 에서 하면 두 막대는 각각 어떻게 되는가?
- 등록 안 한 쪽의 값이 바뀌는 지점은 진행률 몇 퍼센트인가?
- 그 동작을 명세 용어로 무엇이라 부르는가?

### 2. 전환은 애니메이션과 같은 방식으로 실패하는가 (경계)

- 등록 안 한 커스텀 속성에 `transition: --uw 1s linear` 를 걸고 값을 바꾸면 중간에 무엇이 보이는가?
- 그 결과가 1번의 애니메이션 결과와 다른 이유는 무엇인가?
- 「계단이라도 움직인다」와 「순간이동한다」 중 어느 쪽이 애니메이션이고 어느 쪽이 전환인가?

### 3. 칸 하나를 빼면 (예측)

```css
@property --a { syntax: "<length>"; inherits: false; }
@property --b { syntax: "*";        inherits: false; }
@property --c { syntax: "<lengthzz>"; inherits: false; initial-value: 1px; }
```

- 이 셋 중 실제로 등록되는 것은 무엇인가?
- 등록되지 않은 것은 어디로 갔는가 — 선언만 버려지는가, 규칙 전체가 버려지는가?
- 그 사실을 화면이 아니라 무엇으로 확인하는가?
- `syntax: "*"` 만 `initial-value` 를 면제받는 이유는 무엇인가?

### 4. 무효한 값이 떨어지는 자리 (예측)

```html
<p class="p1">A</p>
<p class="p2">B</p>
<style>
  @property --len { syntax: "<length>"; inherits: false; initial-value: 10px; }
  .p1 { --plain: redd; color: var(--plain); }
  .p2 { --len: redd;   width: var(--len);  }
</style>
```

- `getComputedStyle(.p1)['--plain']` 과 `getComputedStyle(.p2)['--len']` 은 각각 무엇인가?
- `.p1` 의 `color` 와 `.p2` 의 `width` 는 각각 무엇인가?
- 둘 중 어느 쪽이 IACVT 이고 어느 쪽이 아닌가?
- 등록이 「디자인 토큰의 방화벽」이라 불리는 이유를 이 결과로 설명할 수 있는가?

### 5. 상속 칸 (예측)

```html
<div class="par"><div class="kid">kid</div></div>
<style>
  @property --i { syntax: "<color>"; inherits: true;  initial-value: #b91c1c; }
  @property --n { syntax: "<color>"; inherits: false; initial-value: #b91c1c; }
  .par { --i: #15803d; --n: #15803d; }
</style>
```

- `.kid` 에서 읽은 `--i` 와 `--n` 은 각각 무슨 색인가?
- 등록하지 않은 커스텀 속성은 상속을 타는가 안 타는가?
- 그래서 `inherits: false` 는 「있던 기능을 끄는 것」인가 「없던 기능을 얻는 것」인가?

### 6. 계산값의 모양이 바뀐다 (경계)

- `#b91c1c` 로 준 값을 등록한 뒤 `getComputedStyle` 로 읽으면 어떤 문자열이 나오는가?
- 등록하지 않았을 때는 무엇이 나오는가?
- 이 차이만으로 등록 여부를 판별할 수 있는가?

### 7. at-rule 과 JS API 의 실패 방식 (연결)

- `@property` 에서 `initial-value` 를 빼면 무엇이 일어나고, `CSS.registerProperty` 에서 빼면 무엇이 일어나는가?
- 같은 이름을 두 번 등록하면 각각 어떻게 되는가?
- 진단할 때 JS API 쪽을 먼저 던져 보라고 하는 이유는 무엇인가?
- 그런데 실제 코드에서는 왜 `@property` 쪽을 쓰는가?

### 8. 등록은 언제부터 효력이 있는가 (예측)

- 이미 진행 중인 애니메이션이 있는 상태에서 `CSS.registerProperty` 를 호출하면 그 애니메이션은 어떻게 되는가?
- 등록을 취소할 수 있는가?
- 라이브러리와 이름이 부딪히면 무슨 일이 일어나는가?

### 9. `syntax` 문자열 (경계)

- `"<length> | auto"` 로 등록한 속성에서 `auto` 와 `10px` 사이의 애니메이션은 보간되는가?
- `"*"` 로 등록하면 애니메이션이 되는가?
- 목록 타입(`"<color>#"`)은 무엇을 구분자로 쓰는가?

### 10. 다른 주제와 잇기 (연결)

- `@property` 규칙이 칸 하나 때문에 통째로 사라지는 것은 07번의 어느 규칙인가?
- 등록은 값 처리 네 단계(04번) 중 어느 단계에 무엇을 끼워 넣는 것인가?
- 「등록 안 한 커스텀 속성에 `transition` 이 안 걸린다」는 52번의 어느 문장과 같은 이야기인가?
- 컨테이너 스타일 쿼리(40번)에서 등록한 속성을 질의할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
