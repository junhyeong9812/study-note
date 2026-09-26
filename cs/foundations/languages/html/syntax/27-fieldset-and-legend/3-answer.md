# html/syntax/27 — `fieldset`/`legend` 와 그룹 비활성화 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 `fieldset`·「Enabling and disabling form controls」·「Constructing the entry list」·`click()` 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 퍼짐 격자다** — 칸마다 네 물음을 한 줄에 놓았고, **반쯤 막힌 줄이 하나도 없다**(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 열 줄은 넷 다 막히고 네 줄은 넷 다 산다 — 첫 `legend` 안(`lg1`)과 첫 자식 아닌 첫 `legend` 안(`lg4`)만 예외 · 필수 빈 칸이 있어도 제출된다 · 퍼진 칸 35 / 53

**출력**

명세 열 파일 —

```javascript
// html25b-27-spec.js
// 명세 열 — 「A form control is disabled if … a descendant of a fieldset element whose disabled attribute is
// specified, and the element is not a descendant of that fieldset element's first legend element child」로 채웠다.
// true = 명세상 disabled. a·span 은 폼 컨트롤이 아니라 false.
const 명세상비활성 = {
  lg1: false,
  lg2: true,
  i1: true,
  rq: true,
  c1: true,
  s1: true,
  t1: true,
  b1: true,
  lg3: true,
  i2: true,
  a1: false,
  sp: false,
  lg4: false,
  o1: false,
};
```

```text
$ python3 html25b-form.py 시도 html25b-27-spread.html | sed -n '/^\[보냄\]$/,/^$/p'
[보냄]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「lg1=%EC%B2%AB+%EB%B2%94%EB%A1%80+%EC%95%88&lg4=%EC%B2%AB+%EC%9E%90%EC%8B%9D+%EC%95%84%EB%8B%8C+%EB%B2%94%EB%A1%80+%EC%95%88&o1=%EB%B0%94%EA%B9%A5+%EC%9E%85%EB%A0%A5&%EB%B3%B4%EB%83%84=1」
          필드  lg1=「첫 범례 안」 · lg4=「첫 자식 아닌 범례 안」 · o1=「바깥 입력」 · 보냄=「1」

(exit 0)
```

```text
$ python3 html25b-form.py 시도 html25b-27-spread.html | sed -n '/^칸 /,$p'
칸                                :disabled focus()  클릭     실림     명세     명세와
첫 legend 안의 input              —        감       받음     실림     아님     같다
둘째 legend 안의 input            매치      안 감    안 받음  —       disabled 같다
input                             매치      안 감    안 받음  —       disabled 같다
required 인데 빈 input            매치      안 감    안 받음  —       disabled 같다
checkbox                          매치      안 감    안 받음  —       disabled 같다
select                            매치      안 감    안 받음  —       disabled 같다
textarea                          매치      안 감    안 받음  —       disabled 같다
button (제출 단추)                매치      안 감    안 받음  (부적용) disabled 같다
안쪽 fieldset 의 legend 안 input  매치      안 감    안 받음  —       disabled 같다
안쪽 fieldset 의 input            매치      안 감    안 받음  —       disabled 같다
a[href]                           —        감       받음     (부적용) 아님     같다
span[tabindex]                    —        감       받음     (부적용) 아님     같다
첫 자식이 아닌 첫 legend 안 input —        감       받음     실림     아님     같다
fieldset 밖 input                 —        감       받음     실림     아님     같다

fieldset 자신의 :disabled — 바깥=true · 안쪽=true · 뒤범례=true
퍼진 칸 = 35 / 53  (disabled 처럼 군 칸 — :disabled 매치 · 포커스 안 감 · 클릭 안 받음 · 안 실림)
명세 열과 갈린 행 = 0 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **막힌 열 줄** — `lg2`(둘째 `legend`) · `i1` · `rq` · `c1` · `s1` · `t1` · `b1` · `lg3`(안쪽 `fieldset` 의 `legend`) · `i2` — `:disabled` 매치 · 포커스 안 감 · 클릭 안 받음 · 안 실림(`b1` 은 실림 부적용).
- ★★★ **산 네 줄** — `lg1` · `lg4` · `a[href]` · `span[tabindex]` + 밖의 `o1`. 반쯤 막힌 줄은 **없다.**
- ★★ **제출은 일어났다** — 서버가 받은 필드는 **`lg1`·`lg4`·`o1`·`보냄`**. `rq`(필수 · 빈 값)는 **검증에서 빠져** 제출을 막지 않았다.
- **세 `fieldset` 자신** — 바깥 `true` · **안쪽 `true`**(속성 없음) · 뒤범례 `true`.
- **퍼진 칸 = 35 / 53** · **명세 열과 갈린 행 = 0 / 14**.

### 2. `legend` 자식이 있으면 그 첫째 · 감싸면 사라진다 · `aria-label` > `legend` > `title` · `div` 는 `radiogroup` 을 붙여야 묶음 — 6 / 9

**출력**

```text
$ python3 html25b-form.py page html25b-27-name.html
id  무엇을                                역할        이름              nameFrom
f1  legend 가 첫 자식                     group       "배송 방법"       relatedElement
f2  legend 앞에 div                       group       "배송 방법"       relatedElement
f3  legend 가 div 안(자식 아님)           group       ""                (없음)
f4  legend 둘                             group       "첫 범례"         relatedElement
f5  aria-label + legend                   group       "에어리아 이름"   attribute
f6  title 만                              group       "제목 이름"       title
f7  이름 없음                             group       ""                (없음)
f8  div role=radiogroup + aria-labelledby radiogroup  "배송 방법"       relatedElement
f9  그냥 div                              generic     ""                (없음)

이름이 있는 묶음 = 6 / 9
(exit 0)
```

**왜 그런가**

- **`f1`·`f2`·`f4`** — `group` · 첫 `legend` 자식(`f2` 는 `div` 뒤여도 · `f4` 는 둘 중 첫째) · `relatedElement`.
- **`f3`** — `legend` 가 `div` 안(자식 아님) → 이름 `""`.
- **`f5`** — `aria-label` · **`f6`** — `title` · **`f7`** — 빈 이름.
- **`f8`** — `radiogroup` · `aria-labelledby` 로 `"배송 방법"` · **`f9`** — `generic` · `""`.
- **이름이 있는 묶음 = 6 / 9.**

### 3. 자기 `disabled` · 또는 `disabled` 인 `fieldset` 의 자손이면서 그 첫 `legend` 자식 안이 아님 — 안쪽 `fieldset` 은 「비활성 fieldset」 정의의 둘째 줄

- 명세 — 「폼 컨트롤이 disabled 인 조건: ① `button`·`input`·`select`·`textarea`·폼 연관 사용자 정의 요소이고 **자기 `disabled` 가 있다** · ② **`disabled` 가 지정된 `fieldset` 의 자손**이고 **그 `fieldset` 의 첫 `legend` 자식의 자손이 아니다**」.
- **안쪽 `fieldset`** — 「비활성 fieldset」 = 「`disabled` 속성이 있다」 **또는** 「`disabled` 가 지정된 다른 `fieldset` 의 자손이고 그 첫 `legend` 자식의 자손이 아니다」. 둘째 줄에 걸렸다(A1 의 「안쪽=true」).

### 4. 「**그** `fieldset` 의 첫 `legend` **자식**」의 자손 — 자식 중 `legend` 로 첫째면 되고 첫 자식일 필요는 없다 · 안쪽의 `legend` 는 바깥의 것이 아니다

- **첫 `legend` 자식** — `fieldset` 의 **자식** 가운데 `legend` 인 것 중 첫째. `div` 가 앞에 있어도 된다(A1 의 `lg4`) — 「첫 자식」이 아니다.
- **안쪽 `fieldset` 의 첫 `legend`** — 조건의 「그 `fieldset`」은 **`disabled` 가 지정된 바깥 `fieldset`** 이다. 안쪽 `legend` 는 바깥의 첫 `legend` 자식이 아니므로 예외가 아니다(A1 의 `lg3`).

### 5. 항목 목록 거름망의 「field is disabled」 · 비활성 칸은 제약 검증에서 제외

- **제출** — 「항목 목록 만들기」가 칸을 건너뛰는 조건에 **「필드가 disabled 다」** 가 있다([24번](../24-input-types-choice-special/2-summary.md)의 거름망).
- **검증** — 비활성 칸은 **제약 검증에서 제외**(barred)된다. 그래서 `rq` 는 `valueMissing` 을 낼 기회가 없고, [21번](../21-form-submission-model/2-summary.md)이 잰 「검증 → `invalid` → 멈춤」이 **이 칸에서는 안 돈다.**

### 6. 「disabled 인 폼 컨트롤은 사용자 상호작용 작업의 `click` 을 디스패치하지 않게 해야 한다」 · `click()` 은 첫 줄에서 돌아간다

- 명세 — 「disabled 인 폼 컨트롤은 **사용자 상호작용 작업 원천**에 들어온 `click` 이벤트가 **그 요소에 디스패치되지 않게** 해야 한다」 — A1 의 「안 받음」.
- **`click()`** — 명세의 단계 첫 줄 — 「이 요소가 **disabled 인 폼 컨트롤이면 돌아간다**」. 이 판은 `click()` 을 비활성 칸에 따로 던지지 않았다 — 문장만 적는다.

### 7. `a[href]`·`span[tabindex]` — 폼 컨트롤이 아니라서

- `disabled` 는 **폼 컨트롤**(`button`·`input`·`select`·`textarea`·폼 연관 사용자 정의 요소)의 상태다. 링크와 `tabindex` 요소는 그 목록에 없어 **`fieldset` 의 퍼짐이 닿지 않는다**(A1 — 포커스·클릭 둘 다 됐다).

### 8. 감싸면 이름도 예외도 사라진다 · `role="radiogroup"` + `aria-labelledby`

- **`div` 로 감싼 `legend`** — `fieldset` 의 **자식이 아니다.** 이름 계산(HTML-AAM 「`legend` **자식**」)에서도, 비활성 예외(「첫 `legend` **자식**」)에서도 빠진다(A2 의 `f3`).
- **`fieldset` 없이** — `<div role="radiogroup" aria-labelledby="…">`(A2 의 `f8`).

### 9. 갈린 행 0 / 14 · 어긋난 줄 없음 · 트리의 `group` 이름까지(읽는 소리는 못 잰 것)

- **명세 열과 갈린 행은 0 / 14**, 네 물음이 **서로 어긋난 줄도 없다**(A1).
- **스크린리더** — 이 판이 보인 것은 **`group` 과 그 이름 `"배송 방법"`** 까지다. 보조 기술이 그것을 묶음에 들어갈 때 읽는지는 **못 잰 것**이다.

### 10. 정본 경계

- **`disabled` 대 `readonly`** — 목록의 **30번 주제** · **`:disabled` 선택자** — [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) · **칸 하나의 이름** — [25번](../25-label-association/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [25번](../25-label-association/3-answer.md)의 `html25b-form.py`·`html25b-cdp.py` 그대로다.\
★ **퍼짐 격자** — 표 종류 「종합」. 칸마다 **새 페이지에서 진짜로 한 번 누르고**(`click` 리스너가 불렸나를 `뒤` 로 받는다), 마지막 시도가 **보냄**을 누른다. 하네스가 모든 시도의 결과와 **서버가 받은 필드 목록**을 새 페이지의 `__종합` 에 넘기면, 페이지가 `:disabled` 와 `focus()` 를 그 자리에서 묻고 네 물음을 한 줄로 놓는다.\
★ **「명세」 열은 따로 둔 파일**(`html25b-27-spec.js`) — 질문 파일에 소스를 실어도 답이 안 새게 했다.

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다(재대조는 25번 `## 실행 검증`).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **열네 칸 × 네 물음 · 보냄** | 3 | 동작 방식 (1) · A1 |
| **묶음 아홉의 이름** | 3 | 동작 방식 (2) · A2 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목** — 이 주제에서 명세와 갈린 칸이 없어 **다시 찍을 구현 항목이 없다.** 트리의 역할 이름(`group`·`radiogroup`·`generic`)만 Chrome 의 이름이다.

**안 돌려 본 것** — ① **Tab 키 순회.** ② **비활성 칸에 스크립트 `click()`** — 명세 문장만. ③ **떠 있는 `legend`**(렌더된 `legend` 조건). ④ **`inert`** 와의 비교.

**못 잰 것** — ① **스크린리더의 묶음 읽기.** ② **비활성 칸의 모양**(demo 로 사람이 본다).

**부적용인 창** — **창 ③ · ④ · ⑥** — **잴 것이 없다.**

## 용어 풀이

- **비활성 fieldset** — `disabled` 가 있거나, 비활성 fieldset 안(그 첫 `legend` 밖)의 `fieldset`.
- **첫 `legend` 자식** — 자식 `legend` 중 첫째.
- **제약 검증에서 제외** — 검증 대상이 아닌 것. 비활성 칸이 여기 든다.
- **`group` · `radiogroup`** — 묶음 역할. 앞은 `fieldset`, 뒤는 라디오 전용.
