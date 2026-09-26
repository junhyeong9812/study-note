# html/syntax/26 — `select`/`option`/`optgroup`·`datalist`·`textarea` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 `select`·`option`·`datalist`·`textarea`·「Constructing the entry list」·파싱·직렬화 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤ 다** — 「안 실린다」는 열네 칸의 필드 이름을 먼저 선언하고 서버가 받은 목록에서 **찾아보고 없었다**로 선다(A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 단일은 안 골라도 0 번 · `multiple`·`size=3`·전부 `disabled` 는 -1 · `multiple` 의 `.value` 는 첫째 하나 · `datalist` 안의 칸은 `willValidate=false` 인데 `elements` 에 있다

**출력**

```text
$ python3 html25b-form.py page html25b-26-sent.html
name multiple·size  .value      selectedIndex selectedOptions
s1   —             "a"         0             ["a"]
s2   —             "b"         1             ["b"]
s3   multiple       ""          -1            []
s4   multiple       "a"         0             ["a","c"]
s5   —             "가 나"     0             ["가 나"]
s6   —             ""          0             [""]
s7   —             "b"         1             ["b"]
s8   — size=3      ""          -1            []
s9   —             ""          -1            []
s10  —             "긴 글자"   0             ["긴 글자"]

datalist 안의 input — willValidate=false · form.elements 에 있나=true
(exit 0)
```

**왜 그런가**

- **`s1` 0 · `s2` 1(첫 선택지가 `disabled`) · `s3` -1 · `s8` -1 · `s9` -1** — 명세가 첫 선택지를 고르는 것은 **`multiple` 없음 + 표시 크기 1** 일 때만이고, 비활성인 것은 건너뛴다(A5).
- **`s4`** — `.value` 는 **`"a"`**(첫째)인데 `selectedOptions` 는 **`["a","c"]`**.
- **`s5`** — `"가 나"`(공백 정리) · **`s6`** — `""` 인데 `selectedIndex` 0(골라져 있다) · **`s7`** — `"b"`(마지막 `selected`) · **`s10`** — `"긴 글자"`(`label` 이 아니다).
- **`datalist` 안의 `input`** — `willValidate=false` · `form.elements` 에 **있다.**

### 2. 실린 칸 11 / 14 — `s3`·`s8`·`s9` 만 없다 · `s4=a&s4=c` · 목록 밖 값도, `datalist` 안의 칸도 실린다 · 줄바꿈은 전부 `%0D%0A`

**출력**

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '1,6p'
[목록 밖 값을 치고 보냄 클릭]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「s1=a&s2=b&s4=a&s4=c&s5=%EA%B0%80+%EB%82%98&s6=&s7=b&s10=%EA%B8%B4+%EA%B8%80%EC%9E%90&d1=%EB%AA%A9%EB%A1%9D%EC%97%90+%EC%97%86%EB%8A%94+%EA%B3%B3&d2=%EB%AA%A9%EB%A1%9D+%EC%95%88%EC%9D%98+%EC%B9%B8&t1=%EC%B2%AB+%EC%A4%84%0D%0A%EB%91%98%EC%A7%B8+%EC%A4%84&t2=%EC%B2%AB%0D%0A%EB%91%98%0D%0A%EC%85%8B%0D%0A%EB%84%B7&b=%EB%B3%B4%EB%83%84」
          필드  s1=「a」 · s2=「b」 · s4=「a」 · s4=「c」 · s5=「가 나」 · s6=「」 · s7=「b」 · s10=「긴 글자」 · d1=「목록에 없는 곳」 · d2=「목록 안의 칸」 · t1=「첫 줄\r\n둘째 줄」 · t2=「첫\r\n둘\r\n셋\r\n넷」 · b=「보냄」
(exit 0)
```

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '7,12p'
[목록 밖 값을 치고 멀티 클릭]
  페이지  click(멀티 · detail=1) → submit(submitter=멀티)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 13개 · 경계로 갈라 필드만 적는다)
          필드  s1=「a」 · s2=「b」 · s4=「a」 · s4=「c」 · s5=「가 나」 · s6=「」 · s7=「b」 · s10=「긴 글자」 · d1=「목록에 없는 곳」 · d2=「목록 안의 칸」 · t1=「첫 줄\r\n둘째 줄」 · t2=「첫\r\n둘\r\n셋\r\n넷」 · b=「멀티」
(exit 0)
```

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '/^칸 /,$p'
칸                                (1)   (2)
select · 고른 것 없음             실림  실림
select · 첫 option 이 disabled    실림  실림
select multiple · 고른 것 없음    —    —
select multiple · 둘 고름         실림  실림
select · value 없는 option        실림  실림
select · value="" 고름            실림  실림
select · selected 둘              실림  실림
select size=3 · 고른 것 없음      —    —
select · option 전부 disabled     —    —
option label=짧게 · 글자=긴 글자  실림  실림
input list · 목록 밖 값           실림  실림
datalist 안의 input               실림  실림
textarea (자식 텍스트)            실림  실림
textarea (스크립트 값)            실림  실림
(1) 목록 밖 값을 치고 보냄 클릭 — 실린 칸 = 11 / 14
(2) 목록 밖 값을 치고 멀티 클릭 — 실린 칸 = 11 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **안 실린 셋은 `selectedIndex` 가 -1 인 셋**(A1)이다 — 고른 선택지가 없으면 항목이 안 생긴다. **`s3=` 조차 없다.**
- ★★ **`s4=a&s4=c`** — 고른 선택지마다 **같은 이름으로 한 항목씩**. multipart 에서도 부분이 둘이다(부분 **13개** = 필드 13).
- **`s5=가 나`** · **`s6=`**(빈 값 — 안 실린 것과 다르다) · **`s7=b`** · **`s10=긴 글자`**.
- ★★★ **`d1=목록에 없는 곳`** — `datalist` 는 제안일 뿐이다.
- ★★★ **`d2=목록 안의 칸`** — 명세는 **`datalist` 조상이 있으면 건너뛰라**고 하는데 이 판은 **두 인코딩 다 실었다**(A8).
- ★★ **`t1=첫+줄%0D%0A둘째+줄` · `t2=첫%0D%0A둘%0D%0A셋%0D%0A넷`** — CR 하나 · CRLF · LF 하나가 **전부 CRLF** 가 됐다. 명세의 「이름·값 쌍 목록으로 바꾸기」 단계다.

### 3. `value` 속성은 어디에도 없다 · 첫 LF 하나가 빠진다 · 자식 변경은 더러움 표시가 거짓일 때만 따라온다 · `reset` 이 되돌린다 · 직렬화는 자식 텍스트다

**출력**

```text
$ python3 html25b-form.py page html25b-26-textarea.html
── 파싱 직후
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="원래"  textContent="원래"  defaultValue="원래"  getAttribute('value')=null  textLength=2
  t4  .value="원래"  textContent="원래"  defaultValue="원래"  getAttribute('value')=null  textLength=2
  t5  .value=""  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=0
── 스크립트가 t3 자식 · t4 값→자식 · t5 값을 바꾼 뒤
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t4  .value="스크립트 값"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=6
  t5  .value="첫\n둘\n셋\n넷"  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=7
── form.reset() 뒤
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t4  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t5  .value=""  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=0
(exit 0)
```

```text
$ python3 html25b-form.py dom html25b-26-textarea.html | sed -n '/<form/,/<\/form>/p'
<form id="폼">
<textarea id="t1" value="속성 값">첫 줄
둘째 줄</textarea>
<textarea id="t2">
앞에 빈 줄</textarea>
<textarea id="t3">바뀐 자식</textarea>
<textarea id="t4">바뀐 자식</textarea>
<textarea id="t5"></textarea>
</form>
(exit 0)
```

**왜 그런가**

- **파싱 직후** — `t1` 의 `.value`·`textContent`·`defaultValue` 가 **셋 다 `"첫 줄\n둘째 줄"`**(첫 LF 가 빠졌다) · `getAttribute('value')` 만 `"속성 값"`. `t2` 는 **`"\n앞에 빈 줄"`**(LF 둘 중 하나만 빠졌다) · `textLength` 7.
- **스크립트 뒤** — `t3` 는 **`"바뀐 자식"`** 으로 따라왔다 · `t4` 는 `.value` 가 **`"스크립트 값"`** 이고 `textContent`·`defaultValue` 만 `"바뀐 자식"` · `t5` 는 `.value` 가 **`"첫\n둘\n셋\n넷"`**(CR 이 LF 로) · `textLength` **7** · `textContent` 는 `""`.
- **`reset()` 뒤** — `t4` 가 **`"바뀐 자식"`**, `t5` 가 **`""`**(자식 텍스트).
- **직렬화** — `t2` 는 **LF 하나** 뒤에 글자(다시 파싱하면 그 LF 가 또 빠진다) · `t4` 는 **`바뀐 자식`**(마지막에 `.value` 를 다시 썼는데도).

### 4. `combobox` → `MenuListPopup` → `group` · `listbox`(multiselectable) → `group` · 묶음 이름 = `label` · 선택지에 `disabled=True` · 이름은 `짧게` · `datalist` 는 트리에 없다

**출력**

```text
$ python3 html25b-form.py ax html25b-26-ax.html
RootWebArea    이름='26 트리'
  generic        이름=''
    LabelText      이름=''
      StaticText     이름='하나 '
      combobox       이름='하나 '
        MenuListPopup  이름=''
          group          이름='과일'
            option         이름='사과' selected=False
            option         이름='배' selected=True
          group          이름='채소'
            option         이름='무' disabled=True
    LabelText      이름=''
      StaticText     이름='여럿 '
      listbox        이름='여럿 ' multiselectable=True
        group          이름='과일'
          option         이름='사과' selected=True
          option         이름='배' selected=False
        option         이름='기타' selected=False
    LabelText      이름=''
      StaticText     이름='줄임 '
      combobox       이름='줄임 '
        MenuListPopup  이름=''
          option         이름='짧게' selected=True
    LabelText      이름=''
      StaticText     이름='도시 '
      combobox       이름='도시 '
        generic        이름=''
    LabelText      이름=''
      StaticText     이름='메모 '
      textbox        이름='메모 ' multiline=True
        generic        이름=''
(exit 0)
```

**왜 그런가**

- **단일** — `combobox "하나 "` → `MenuListPopup` → `group "과일"`·`group "채소"` → `option`. **`multiple`** — `listbox "여럿 "`(`multiselectable=True`) → `group "과일"` → `option` · 묶음 밖 `option "기타"`.
- **`채소`(disabled)** — 안의 `option "무"` 에 **`disabled=True`**.
- **`줄임`** — `option "짧게"`(`label` 이 트리 이름) — A2 에서 실린 값은 `긴 글자`.
- **`datalist`** — 트리에 **없다.** `도시` 칸은 `combobox`.

### 5. `multiple` 없음 + 표시 크기 1 + 선택 없음일 때만 · `size=3` 은 표시 크기가 3 · 「선택 안 함」은 `value=""` 첫 선택지

- 명세 — 「`multiple` 이 **없고**, 표시 크기가 **1** 이고, 선택된 것이 **하나도 없으면** 비활성이 아닌 **첫 선택지**를 선택됨으로 둔다」. 표시 크기는 `size` 속성이고, **`size=3` 이면 3** 이라 조건이 거짓이다(A1 의 `s8` -1).
- **「안 고름」을 알리려면** — 첫 선택지를 **`<option value="">고르세요</option>`** 로 둔다. 서버는 **`s=`**(빈 값)를 받는다(A2 의 `s6`). 단일 `select` 에서 「필드가 없다」로는 못 알린다.

### 6. `value` 없으면 HTML 인식 텍스트 내용 — 앞뒤 공백을 벗기고 연속 공백을 하나로 · `label` 은 트리 이름만

- 명세 — 값 = 「`value` 속성이 **있으면 그것**, 없으면 **HTML 인식 텍스트 내용**」 · 그 텍스트는 끝에 **「ASCII 공백 벗기고 합치기」** 를 거친다 — `  가   나  ` → `가 나`(A2).
- **`label`** — 명세의 `option` 의 라벨 = 「`label` 이 비어 있지 않으면 그 값, 아니면 텍스트」. **값은 안 바꾼다**(A2 `긴 글자`) · 트리 이름은 **`짧게`**(A4).

### 7. 원 값은 그대로 · API 값(`.value`·`textLength`·`maxlength`)은 LF · 값(제출)은 LF + `wrap` → 보낼 때 CRLF · 자식은 더러움 표시가 거짓일 때만 · 왕복하면 빈 첫 줄이 줄어든다

- **원 값** — 정규화 없음 · **API 값** — 줄바꿈을 **LF 로** · **값** — API 값에 `wrap="hard"` 면 줄 삽입(제출·그 밖의 처리). 보낼 때는 「이름·값 쌍 목록」 단계가 **CRLF** 로 바꾼다.
- **자식 텍스트가 바뀌면** — 명세의 「children changed steps」 — **더러움 표시가 거짓일 때만** 원 값을 자식 텍스트로(A3 의 `t3` 대 `t4`).
- **직렬화가 되살리지 않으면** — `innerHTML`·`--dump-dom` 을 다시 파싱할 때마다 **빈 첫 줄이 하나씩 사라진다**(A3 의 `t2`). 명세가 「역사적 이유로 왕복시키지 않는다」고 스스로 적은 자리다.

### 8. 「항목 목록에서 건너뛴다」·「제약 검증에서 제외」 — 이 판은 뒤엣것만 지켰다 · 제한할 수 없다(`select` + 서버 검증)

- **항목 목록** — 「필드에 **`datalist` 조상**이 있으면 건너뛴다」 — ★ **이 판은 실었다**(A2 의 `d2`). **제약 검증** — 「`datalist` 조상이 있으면 **제약 검증에서 제외**」 — 지켰다(A1 `willValidate=false`).
- **제한** — `list` 는 「제안」이다(A2 의 `d1`). 값을 닫힌 집합으로 묶으려면 `select`, 그리고 **어느 경우든 서버 검증**([21번](../21-form-submission-model/2-summary.md)의 `curl` — 브라우저를 안 거친 요청은 어떤 마크업도 못 막는다).

### 9. 갈린 칸은 하나 — `datalist` 안의 칸이 실린 것 · `MenuListPopup` 은 구현

- ★ **명세와 갈린 칸은 1 개** — A2 의 **`d2`**(urlencoded·multipart 두 제출에서 같은 모양). 나머지(선택 규칙·값·CRLF·`textarea` 의 세 정규화·파싱·직렬화)는 문장 그대로였다.
- **`combobox` → `MenuListPopup`** — HTML-AAM 은 단일 `select` 를 `combobox` 로 적을 뿐이다. 그 아래 층의 이름(`MenuListPopup`)은 **Chrome 의 구현**이다.

### 10. 페이지 밖 UI 다 · 글꼴 폭에 달린 구현 정의라 던지지 않았다

- **선택 창·자동완성 줄** — 헤드리스에서 **열지 않았다**. 트리에도 닫힌 상태의 `combobox` 까지만 있다 — 「못 잰 것」.
- **`wrap="hard"`** — 명세가 「**구현 정의** 알고리즘으로 각 줄이 글자 폭을 넘지 않게」라고만 적는다. 이 판은 **안 돌려 본 것**으로 둔다.

### 11. 정본 경계

- **격자 방식** — [24번](../24-input-types-choice-special/2-summary.md) · **첫 줄바꿈** — [04번](../04-whitespace-and-character-references/2-summary.md)의 (3).
- **필수 `select`** — 목록의 **29번 주제** · **`textarea` 의 `maxlength`** — [28번](../28-validation-attributes/2-summary.md)(사용자 편집 조건).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [25번](../25-label-association/3-answer.md)의 `html25b-form.py`·`html25b-cdp.py` 그대로다.\
★ **「실린」 격자** — [24번](../24-input-types-choice-special/3-answer.md)과 같다. 페이지가 `__칸목록` 에 **필드 이름 열넷을 먼저 선언**하고, 하네스가 시도마다 **서버가 파싱한 필드 이름 목록**에서 찾는다.\
★ **목록 밖 값** — `type` 단계(`Input.insertText`)로 **진짜 글자 입력**을 넣었다.\
★ **`dom` 모드** — `--dump-dom` 도 **같은 로컬 서버**에서 연 페이지로 받았다(`file://` 를 쓰지 않는다).

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다(결과는 25번 `## 실행 검증` 과 같은 재대조).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`select` 열 개의 상태** | 3 | 동작 방식 (1) · A1 |
| **두 인코딩 × 열네 칸** | 3 | 동작 방식 (1) · A2 |
| **`textarea` 다섯 × 세 시점 · 직렬화** | 3 | 동작 방식 (2) · A3 |
| **트리** | 3 | 동작 방식 (3) · A4 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| ★ **`datalist` 안의 칸** | **실린다**(두 인코딩) | 명세는 건너뛴다 — 판이 오르면 고쳐질 수 있다 |
| 단일 `select` 의 트리 층 | `combobox` → `MenuListPopup` | 구현의 이름 |
| 닫힌 `datalist` | 트리에 없다 | 구현 |

**안 돌려 본 것** — ① **`wrap="hard"`**. ② **선택 창을 연 뒤의 트리.** ③ **Customizable `<select>`**(`selectedcontent`). ④ **`select` 에 `required`** — 목록의 **29번 주제**.

**못 잰 것** — ① **선택 창·자동완성 UI.** ② **스크린리더의 묶음 읽기.**

**부적용인 창** — **창 ③ · ④ · ⑥** — **잴 것이 없다.**

## 용어 풀이

- **selectedness setting algorithm** — 선택이 없거나 여럿일 때 명세가 고쳐 두는 규칙.
- **표시 크기** — `size`, 없으면 `multiple` 4 · 아니면 1.
- **HTML 인식 텍스트 내용** — 공백을 벗기고 합친 `option` 의 글자.
- **원 값 · API 값 · 값** — `textarea` 의 세 정규화.
- **더러움 표시** — 값이 사용자·스크립트로 바뀌었다는 표시. 자식 변경이 값에 번지나를 정한다.
- **CRLF** — `\r\n`. 제출의 줄 끝.
