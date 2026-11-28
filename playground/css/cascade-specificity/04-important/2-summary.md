# css/cascade-specificity/04 — !important — 정리 (힌트)

> 출처 — study-site 항목 `css/important`(항목 데이터 `data/css/cascade-specificity.json`) · 정답 코드 study-practice `css/cascade-specificity/reference/important.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`!important` 는 「줄 서기에서 쓰는 긴급 통행증」이다.**
평소에는 직급(명시도)이 높은 사람이 먼저 들어간다.
그런데 긴급 통행증을 든 사람은 직급과 상관없이 먼저 들어간다.
긴급 통행증을 든 사람이 둘이면 다시 직급을 따진다.
통행증을 아무나 쓰기 시작하면 줄이 엉망이 되고, 누가 왜 먼저 들어갔는지 아무도 모르게 된다.
CSS 선언도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 줄 서는 사람 | 같은 요소의 같은 속성을 두고 겨루는 선언 |
| 직급 | 선택자의 명시도 |
| 긴급 통행증 | 선언 끝의 `!important` |
| 통행증끼리 다시 직급 비교 | `!important` 끼리는 명시도로 다시 겨룸 |
| 줄이 엉망이 됨 | 유지보수가 어려워짐 |

```text
  일반 선언들            !important 선언들
 ┌───────────────┐     ┌──────────────────┐
 │ 명시도로 겨룸   │  <  │ 명시도로 겨룸       │
 └───────────────┘     └──────────────────┘
   (아래 칸)               (위 칸 — 언제나 먼저)
```

## 이 주제가 답하려는 질문

1. `!important` 가 붙은 선언은 명시도가 더 높은 일반 선언과 겨루면 어떻게 되나?
2. `!important` 끼리 부딪히면 무엇으로 승부를 가르나?
3. `!important` 는 규칙 전체에 걸리나, 선언 하나에만 걸리나?
4. 언제 써도 되고, 언제 쓰면 안 되나?

## 동작 방식

### (1) `!important` 는 일반 선언을 명시도와 상관없이 이긴다

**언제 쓰나** — 명시도가 낮은 선택자의 값이 높은 선택자의 값을 꼭 이겨야 할 때 쓴다.

```text
입력 코드                                  무엇이 일어나나                        결과
#high-spec { color: red; }        ─┐
   (ID — 명시도 1,0,0, 일반)        │      color 를 두고 두 선언이 겨룸
.styled { color: #3b82f6           ├──▶  .styled 쪽만 !important        ──▶  color = #3b82f6
          !important; }            │      → 명시도 비교 전에 이미 승부
   (클래스 — 명시도 0,1,0)          ─┘
```

- 같은 요소에 ID 규칙과 클래스 규칙이 모두 `color` 를 선언한다.
- 평소라면 명시도가 높은 ID 쪽 빨강이 이긴다.
- 그러나 클래스 쪽 선언에 `!important` 가 있으므로, 명시도를 따지기 전에 `!important` 쪽이 이긴다.
- 그래서 글자색은 파랑(`#3b82f6`)이 된다.

> **명시도(specificity)** — 같은 요소에 여러 규칙이 부딪힐 때 선택자의 구성(ID · 클래스 · 태그의 개수)으로 매기는 우선순위 점수다.\
> 예: `#high-spec` 는 1,0,0, `.styled` 는 0,1,0, `.imp-demo p` 는 0,1,1 이다.

### (2) `!important` 는 선언 하나에만 걸린다

**언제 쓰나** — 한 규칙 안에서 꼭 이겨야 하는 속성 하나만 골라 강제할 때 쓴다.

```text
입력 코드                              무엇이 일어나나                       결과
#high-spec { color: red;                color   → .styled 의 !important 가 이김   color      = #3b82f6
             font-size: 18px; }         font-size → 겨루는 선언이 없음            font-size  = 18px
.styled { color: #3b82f6 !important;    font-weight → 겨루는 선언이 없음          font-weight = 700
          font-weight: 700; }
```

- 승부는 규칙 단위가 아니라 **속성 하나하나** 단위로 난다.
- `#high-spec` 규칙은 `color` 에서 졌지만, `font-size: 18px` 은 겨룰 상대가 없으므로 그대로 적용된다.
- `.styled` 의 `font-weight: 700` 은 `!important` 가 없는 일반 선언이지만, 역시 겨룰 상대가 없어 적용된다.
- 즉 `!important` 를 붙인 것은 `color` 선언 하나뿐이고, 그 규칙의 다른 선언은 보통 선언 그대로다.

### (3) `!important` 끼리 부딪히면 다시 명시도로 겨룬다

**언제 쓰나** — 이미 `!important` 로 강제된 값을 또 덮어야 할 때 이 규칙을 알아야 한다.

```text
입력 코드                                    무엇이 일어나나                             결과
#a  { color: red  !important; }   ─┐       둘 다 !important → 같은 칸에서 겨룸
.b  { color: blue !important; }   ─┴──▶  명시도 비교: 1,0,0 > 0,1,0            ──▶  color = red
```

- 둘 다 `!important` 이므로 `!important` 라는 우위는 서로 상쇄된다.
- 그다음에는 일반 선언과 똑같이 명시도로 겨룬다.
- 명시도까지 같으면 스타일시트에서 **나중에 나온** 선언이 이긴다(캐스케이드의 마지막 판정 기준인 선언 순서).
- 그래서 `!important` 로 강제된 값은 **다른 `!important`** 로만 덮을 수 있다 — 일반 선언으로는 명시도를 아무리 높여도 이길 수 없다.

> **캐스케이드(cascade)** — 한 요소의 한 속성에 여러 선언이 해당될 때 어느 값을 쓸지 정하는 판정 절차다.\
> 예: `!important` 여부 → 명시도 → 선언 순서 차례로 따진다.

### (4) 남용하면 왜 지옥이 되나

```text
1단계  .btn { color: blue !important; }           ← 급해서 붙임
2단계  .btn-danger { color: red; }                 ← 안 먹힘
3단계  .btn-danger { color: red !important; }      ← 또 붙임
4단계  #page .btn { color: green !important; }    ← 또 붙임 …
```

- 일반 선언으로는 `!important` 를 덮지 못하므로, 덮으려는 쪽도 `!important` 를 붙이게 된다.
- 그러면 `!important` 끼리 다시 명시도 싸움이 벌어져, 원래 피하려던 문제가 한 칸 위에서 되풀이된다.
- 어느 값이 왜 이기는지 추적하기 어려워져 디버깅이 힘들어진다.

```html demo
<p id="high-spec" class="styled">ID 선택자 vs .styled !important</p>
<style>
  #high-spec { color: red; font-size: 18px; }
  .styled { color: #3b82f6 !important; font-weight: 700; }
</style>
```

> **보이는 것** — 18px 크기의 굵은 파란 글자 한 줄 (코드에서 읽은 것 — 렌더 실측 아님)

## 문법 — 형태와 규칙

```css
/* 최소 예제 */
#title  { color: red; font-size: 18px; }       /* ID — 1,0,0 */
.accent { color: blue !important; }            /* 클래스 — 0,1,0, 그러나 color 는 이김 */
.hidden { display: none !important; }          /* 유틸리티 클래스 — 정당한 사용 */
```

- 꼴은 `property: value !important;` 다 — 값 뒤, 세미콜론 앞에 둔다.
- 선언 하나에만 붙는다. 같은 규칙의 다른 선언에는 영향이 없다.
- `!important` 선언은 일반 선언을 명시도와 상관없이 이긴다.
- `!important` 선언끼리는 명시도로, 그것도 같으면 선언 순서로 겨룬다.
- 일반 선언으로는 `!important` 선언을 덮을 수 없다.

| 상황 | 승자 |
|---|---|
| 일반 vs 일반 | 명시도 높은 쪽 → 같으면 나중 쪽 |
| 일반(명시도 높음) vs `!important`(명시도 낮음) | `!important` 쪽 |
| `!important` vs `!important` | 명시도 높은 쪽 → 같으면 나중 쪽 |

## 어디서 틀리나

### 1. 「`!important` 는 규칙 전체를 이기게 한다」

아니다.
선언 하나에만 걸린다.
`.styled` 규칙에서 `color` 만 `!important` 이고 `font-weight` 는 일반 선언이다.
ID 규칙의 `font-size` 도 졌다고 사라지지 않는다 — 겨룰 상대가 없으면 그대로 적용된다.

### 2. 「`!important` 를 붙이면 무조건 이긴다」

다른 `!important` 가 있으면 다시 명시도 싸움이다.
`#a { color: red !important }` 와 `.b { color: blue !important }` 가 부딪히면 ID 쪽이 이긴다.

### 3. 명시도를 높여서 `!important` 를 덮으려 한다

일반 선언은 선택자를 아무리 길게 써도 `!important` 를 못 이긴다.
덮으려면 `!important` 를 붙이고 명시도로 이겨야 한다 — 그래서 「`!important` 는 다른 `!important` 로만 덮을 수 있다」.

### 4. 정당한 사용과 남용을 가르지 않는다 (원본 팁)

정당한 사용은 두 가지다.

- **유틸리티 클래스** — `.hidden { display: none !important }` 처럼 「붙이면 반드시 그렇게 되어야 하는」 한 가지 일만 하는 클래스.
- **서드파티 CSS 오버라이드** — 고칠 수 없는 외부 스타일시트의 값을 덮어야 할 때.

그 밖의 경우에 `!important` 가 필요해 보인다면, 문제는 명시도 구조에 있다.
선택자 설계를 고치는 것이 올바른 해결책이다.

### 5. 명시도 표기가 두 가지로 섞여 있다

원본 예제의 문단 글은 ID 를 `(0,1,0,0)` 네 자리로 적고, 정답 코드 주석은 `1,0,0` 세 자리로 적는다.
네 자리 표기는 맨 앞에 칸 하나를 더 둔 꼴이고, 세 자리 표기는 ID · 클래스 · 태그만 센다.
같은 ID 하나를 가리키므로 모순은 아니지만, 비교할 때는 한 가지 표기로 맞춰야 한다.

> **유틸리티 클래스(utility class)** — 한 가지 스타일 일만 하도록 만든 작은 클래스다.\
> 예: `.hidden` 은 요소를 숨기는 일만 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `!important` 선언은 일반 선언을 명시도와 상관없이 이긴다 | CSS 캐스케이드 명세 |
| `!important` 끼리는 명시도 → 선언 순서로 겨룬다 | CSS 캐스케이드 명세 |
| 승부는 선언(속성) 단위로 난다 | CSS 캐스케이드 명세 |
| `!important` 남용이 유지보수를 어렵게 한다 | 명세가 아니라 실무 관행상의 판단 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 붙이면 무조건 숨겨야 하는 `.hidden` | `display: none !important` | 명시도에 기대는 일반 선언 |
| 고칠 수 없는 외부 CSS 값을 덮기 | `!important` | 외부 파일 직접 수정 |
| 내 코드에서 규칙이 안 먹힘 | 선택자 구조 정리 · 명시도 조정 | `!important` 로 땜질 |
| 이미 `!important` 로 강제된 내 값을 바꾸기 | 원래 `!important` 를 걷어내기 | `!important` 를 하나 더 얹기 |

## 핵심 문장

1. **`!important` 선언은 명시도와 상관없이 일반 선언을 이긴다.**
2. **`!important` 는 선언 하나에만 걸린다** — 같은 규칙의 다른 선언은 평범하다.
3. **`!important` 끼리는 다시 명시도(그다음 선언 순서)로 겨룬다** — 그래서 `!important` 는 `!important` 로만 덮인다.
4. **정당한 사용은 유틸리티 클래스와 서드파티 CSS 오버라이드뿐이다** — 그 밖에는 명시도 구조를 고친다.

## 관련 자료

- [specificity-calculation](../01-specificity-calculation/2-summary.md)
- [cascade-order](../02-cascade-order/2-summary.md)
- `layer` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/cascade-specificity.json` 의 `important`

## 용어 풀이

- **`!important`** — 선언 끝에 붙여 그 선언을 일반 선언보다 앞세우는 표시.
- **선언(declaration)** — `color: red` 처럼 속성 하나와 값 하나의 짝.
- **규칙(rule)** — 선택자 하나와 중괄호 안 선언 묶음.
- **명시도(specificity)** — ID · 클래스 · 태그 개수로 매기는 선택자의 우선순위 점수.
- **캐스케이드(cascade)** — 여러 선언 가운데 적용할 값을 고르는 판정 절차.
- **선언 순서** — 명시도까지 같을 때 나중에 나온 선언이 이기는 마지막 판정 기준.
- **유틸리티 클래스** — 한 가지 스타일 일만 하는 작은 클래스.
- **서드파티 CSS** — 내가 쓰지 않은 외부 라이브러리 · 위젯의 스타일시트.
- **오버라이드(override)** — 이미 적용된 값을 다른 선언으로 덮어쓰는 것.

## 더 들어가면

- 캐스케이드는 명시도보다 먼저 「출처(origin)」를 본다 — 브라우저 기본 · 사용자 · 작성자 스타일시트이며, `!important` 가 붙으면 이 출처들의 우선순위가 뒤집힌다고 알려져 있다 (확인 필요).
- 인라인 `style` 속성의 일반 선언도 스타일시트의 `!important` 선언을 이기지 못한다 (확인 필요).
- 네 자리 명시도 표기의 맨 앞 칸은 인라인 스타일을 세는 칸으로 쓰이는 경우가 많다 (확인 필요).
- `@layer` 를 쓰면 `!important` 선언의 층 순서가 일반 선언과 반대로 매겨진다고 한다 (확인 필요).
- 개발자 도구의 스타일 패널에서 진 선언은 줄이 그어져 보이므로, 어느 `!important` 가 이겼는지 추적할 때 쓸 수 있다 (확인 필요).
