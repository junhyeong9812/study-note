# html/syntax/24 — `<input>` 타입 지도 ③ 선택·특수: `checkbox`/`radio`/`file`/`color`/`hidden`/`submit`/`image` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「Constructing the entry list」·「The input element」 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤ 다** — 「안 실린다」는 서버가 받은 필드 목록에서 **찾아보고 없었다**로만 선다(A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `on` 둘 · `#000000` 둘 · `hidden` 은 `none` · 그림 단추만 `form.elements` 에서 빠진다(21 대 22)

**출력**

```text
$ python3 html21b-form.py page html21b-24-sent.html
태그·type       name       .value          .checked 역할
input·checkbox  c1         "예"            true     checkbox
input·checkbox  c2         "예"            false    checkbox
input·checkbox  c3         "on"            true     checkbox
input·radio     r1         "가"            false    radio
input·radio     r1         "나"            true     radio
input·radio     r2         "가"            false    radio
input·radio     r2         "나"            false    radio
input·radio     r3         "on"            true     radio
input·file      f1         ""              —       button
input·hidden    h1         "숨김"          —       none
input·hidden    _charset_  "아무 값"       —       none
input·color     k1         "#000000"       —       ColorWell
input·color     k2         "#ff0000"       —       ColorWell
input·color     k3         "#abcdef"       —       ColorWell
input·color     k4         "#000000"       —       ColorWell
input·text      x1         "비활성"        —       textbox
input·text      x2         "읽기 전용"     —       textbox
input·text      (없음)     "이름 없음"     —       textbox
button·button   b0         "보통 단추"     —       button
button·submit   s          "1"             —       button
button·submit   s          "2"             —       button
input·image     img        ""              —       button

form.elements 의 개수 = 21 · 폼 안의 input·button 개수 = 22
form.elements 에 없는 것 = input·image
(exit 0)
```

**왜 그런가**

- **`c3`·`r3`(`value` 없음) 의 `.value` 는 `"on"`** · **`k1`(값 없음)·`k4`(`아님`)는 `"#000000"`**, `k2` 는 `"#ff0000"`, `k3` 은 `"#abcdef"` · **`r1` 은 `나` 쪽이 `true`**, `r2` 는 둘 다 `false`.
- **역할** — `checkbox` · `radio` · 파일 `button` · `hidden` 은 `none` · 색 `ColorWell` · `text` 는 `textbox` · 단추·그림 단추 `button`.
- ★★ **`form.elements` 21 · 폼 안의 `input`·`button` 22 — 빠진 것은 `input·image`** — 명세 「역사적 이유로 그림 단추는 뺀다」.

### 2. 체크 안 된 `c2`·고르지 않은 `r2`·`disabled`·`name` 없음·`type=button` 은 언제나 없다 — 13 · 13 · 14 · 12 / 20

**출력**

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '26,$p'
칸                                (1)   (2)   (3)   (4)
checkbox 체크됨 (value=예)        실림  실림  실림  실림
checkbox 체크 안 됨               —    —    —    —
checkbox 체크됨 (value 없음)      실림  실림  실림  실림
radio 그룹 r1 (나 체크)           실림  실림  실림  실림
radio 그룹 r2 (아무것도 안 고름)  —    —    —    —
radio r3 (value 없음)             실림  실림  실림  실림
file (고른 파일 없음)             실림  실림  실림  실림
hidden                            실림  실림  실림  실림
hidden name=_charset_             실림  실림  실림  실림
color (값 없음)                   실림  실림  실림  실림
color value=red                   실림  실림  실림  실림
color value=#ABCDEF               실림  실림  실림  실림
color value=아님                  실림  실림  실림  실림
text disabled                     —    —    —    —
text readonly                     실림  실림  실림  실림
text (name 없음)                  —    —    —    —
button type=button                —    —    —    —
제출 단추 s                       실림  실림  —    —
image 단추의 img.x                —    —    실림  —
image 단추의 img.y                —    —    실림  —
(1) 보냄 1 클릭 — 실린 칸 = 13 / 20
(2) 보냄 2 클릭 — 실린 칸 = 13 / 20
(3) 그림 단추 (7, 5) 클릭 — 실린 칸 = 14 / 20
(4) requestSubmit() · 제출자 없음 — 실린 칸 = 12 / 20
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '1,6p'
[보냄 1 클릭]
  페이지  click(보냄1 · detail=1) → submit(submitter=보냄1)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&s=1」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · s=「1」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '7,24p'
[보냄 2 클릭]
  페이지  click(보냄2 · detail=1) → submit(submitter=보냄2)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&s=2」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · s=「2」
[그림 단추 (7, 5) 클릭]
  페이지  click(그림 · detail=1) → submit(submitter=그림)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&img.x=7&img.y=5」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · img.x=「7」 · img.y=「5」
[requestSubmit() · 제출자 없음]
  페이지  submit(submitter=null)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」
(exit 0)
```

**왜 그런가**

- ★★★ **언제나 「—」 = `c2`(체크 안 됨) · `r2`(아무것도 안 고름) · `x1`(`disabled`) · 이름 없는 칸 · `b0`(`type=button`)** — 본문에 **`c2=` 도 `r2=` 도 없다.** 「빈 값으로 실린다」가 아니라 **항목이 안 생겼다.**
- ★★★ **`s` 는 누른 단추만** — `보냄 1` → `s=1`, `보냄 2` → `s=2`, 그림 단추·`requestSubmit()` → 없음. **그림 단추는 `img.x=7 · img.y=5`**.
- **값** — `c3=on` · `r3=on` · **`_charset_=UTF-8`**(속성 `아무 값` 무시) · `k2=#ff0000` · `k4=#000000` · **`f1=`**(고른 파일 없음 — urlencoded 에서는 빈 값) · `x2=읽기 전용`(`readonly` 는 실린다).
- **실린 칸** — `13 / 20` · `13 / 20` · `14 / 20` · `12 / 20`.

### 3. 부분 셋 — `f1` 은 `filename=""` · `application/octet-stream`

**출력**

```text
$ python3 html21b-form.py 시도 html21b-24-file.html
[multipart · 파일 안 고름]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 3개 · 경계로 갈라 필드만 적는다)
          필드  f1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · c1=「예」 · s=「멀티」
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **부분 3개 = `f1` · `c1` · `s`** — `c2` 는 multipart 에서도 없다.
- ★★ **`f1` 은 `filename=「」` · 부분 `Content-Type: application/octet-stream` · 값 빈 것** — 명세 「고른 파일이 없으면 **이름이 빈 `File`**, 형식 `application/octet-stream`, 빈 본문」.

### 4. 처음엔 넷이 켜져 있다 — 폼이 다르면 따로, `form` 속성이면 그 폼으로

**출력**

```text
$ python3 html21b-form.py 시도 html21b-24-radio.html
[처음 상태]
  페이지  (기록 없음)
  뒤      갑1 · 을1 · 밖1 · 대1 · 두2
  서버    (받은 요청 없음)
[을2 클릭]
  페이지  click(을2 · detail=1)
  뒤      갑1 · 을2 · 밖1 · 대1 · 두2
  서버    (받은 요청 없음)
[밖갑 클릭]
  페이지  click(밖갑 · detail=1)
  뒤      을1 · 밖1 · 밖갑 · 대1 · 두2
  서버    (받은 요청 없음)
[밖2 클릭]
  페이지  click(밖2 · detail=1)
  뒤      갑1 · 을1 · 밖2 · 대1 · 두2
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **처음 = `갑1 · 을1 · 밖1 · 대1 · 두2`** — `name="r"` 인 셋이 **동시에** 켜져 있다(폼 `갑` · 폼 `을` · 폼 없음 — **세 그룹**). `대1` 은 이름이 `R` 이라 네 번째 그룹. `두1`·`두2` 는 둘 다 `checked` 속성인데 **`두2` 만** 켜졌다.
- **`을2` 뒤** — `을1` 만 꺼짐. **`밖갑` 뒤** — ★ **`갑1` 이 꺼짐**(트리에서는 폼 밖, `form="갑"`). **`밖2` 뒤** — `밖1` 만 꺼짐.

### 5. `datalist` 안 · `disabled` · 제출자 아닌 단추 · 체크 안 된 체크박스 · 체크 안 된 라디오 — `readonly` 는 없다

- 명세 — 「다음 중 하나라도 참이면 **건너뛴다**: 칸에 **`datalist` 조상**이 있다 · 칸이 **비활성**이다 · 칸이 **단추인데 제출자가 아니다** · **체크박스인데 체크 상태가 거짓** · **라디오인데 체크 상태가 거짓**」. 그 뒤에 따로 「**`name` 이 없거나 빈 문자열이면** 건너뛴다」가 있고, 그림 단추는 **제출자가 아니면** 건너뛴다.
- **`readonly` 는 목록에 없다** → **실린다**(A2 의 `x2`). `disabled` 와 제출에서 정반대다.

### 6. 문자열 `"on"` — 서버는 무엇을 골랐는지 모른다

- 명세 — 「`value` 속성이 **있으면 그 값, 없으면 문자열 `"on"`**」(A2 의 `c3=on` · `r3=on`).
- 라디오 그룹의 칸마다 `value` 가 없으면 **어느 칸을 골라도 `on`** 이 간다 — 서버는 **골랐다는 것만** 알고 **무엇을** 골랐는지 모른다. 체크박스 하나라면 「켜졌다」만 알면 되지만, 라디오는 `value` 가 **필수에 가깝다.**

### 7. 제출자일 때만 — `이름.x`·`이름.y` 에 누른 좌표 · 이름이 없으면 `x`·`y`

- 명세 — 「그림 단추면: **제출자가 아니면 건너뛴다.** `name` 이 있고 비지 않았으면 이름 = 그 값 + `.`, 아니면 빈 문자열. `이름x`·`이름y` 두 항목에 **선택된 좌표**를 넣는다」. A2 — `img.x=7 · img.y=5`, 누른 자리가 요소 왼쪽 위에서 (7, 5) 였다.
- **`name` 이 없으면 항목 이름이 그냥 `x`·`y`** 다 — 명세의 문장에서 읽은 것이고 **이 판이 던지지 않았다.**

### 8. 같은 폼 소유자(또는 둘 다 없음) · 같은 트리 · 비지 않은 같은 이름 — `form` 속성을 가진 라디오는 그 폼의 그룹에 든다

- 명세 — 라디오 `a` 의 그룹에는 다음을 **모두** 만족하는 라디오 `b` 가 든다: 「`b` 가 라디오 상태 · **`a` 와 `b` 의 폼 소유자가 같거나 둘 다 없다** · **같은 트리**에 있다 · 둘 다 `name` 이 있고 **비지 않았고 같다**」.
- **트리 위치가 폼 밖이어도 `form` 속성이 폼 소유자를 정하면** 그 폼의 그룹이다 — A4 의 **`밖갑` 을 누르자 `갑1` 이 꺼졌다.** [21번](../21-form-submission-model/3-answer.md) A4 의 「`form` 속성이 트리를 이긴다」와 같은 축이다.

### 9. 불투명 검정 · 빈 값은 없다 · 이름 빈 `File` · `_charset_`

- **색** — 「색 칸의 색 갱신」 — 값을 **CSS 색으로 파싱**하고 **실패하면 불투명 검정**(A1·A2 의 `k4` → `#000000`). 명세 — 「이 상태에서는 **언제나 색이 골라져 있고** 사용자가 값을 **빈 문자열로 둘 방법이 없다**」.
- **파일** — 고른 것이 없으면 **이름이 빈 `File`(`application/octet-stream`, 빈 본문)** 하나(A3). urlencoded 에서는 `f1=`(A2).
- **`hidden`** — 이름이 **`_charset_`**(대소문자 무시)면 **인코딩 이름**(A2 — `UTF-8`).

### 10. 갈린 칸은 없었다 · `file`·`color` 는 「대응 역할 없음」, `hidden` 은 「대응 없음」 — CDP 는 `button`·`ColorWell`·`none` · 「—」 는 스무 칸을 선언하고 찾은 결과다

- **이 주제에서 명세와 갈린 칸은 없었다** — 거름망·`on`·좌표·`_charset_`·빈 파일·색·라디오 그룹·`elements` 가 전부 명세 문장 그대로였다. ([21번](../21-form-submission-model/3-answer.md)·[23번](../23-input-types-number-date/3-answer.md)과 대조되는 점이다.)
- **HTML-AAM** — `file`·`color` 는 **「대응하는 역할 없음」**(계산된 역할 `html-input-file`·`html-input-color`), `hidden` 은 **「대응 없음(Not mapped)」**. **CDP** — `button` · `ColorWell` · `none`(A1). 앞의 둘은 Chrome 의 이름이다.
- **「—」 의 근거** — 페이지가 `__칸목록` 에 **필드 이름 스무 개를 먼저 선언**하고, 하네스가 시도마다 **서버가 받은 필드 이름 목록에서 찾아** 칸을 채웠다(A2 의 격자). 「안 물어본 것」은 격자에 행 자체가 없다 — **스무 행이 전부 물은 것**이다.

### 11. 정본 경계

- **`disabled`·`readonly` 의 포커스·검증** — 목록의 **30번 주제**. 여기는 제출에 실리나까지(A2).
- **리스너 안의 `checked`** — [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)의 (4)·(8).
- **라디오 그룹의 이름** — 목록의 **27번 주제**(`fieldset`·`legend`) · **실제 파일 업로드** — 목록의 **31번 주제** · **`select` 다중 선택** — 목록의 **26번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [21번](../21-form-submission-model/3-answer.md)의 `html21b-form.py`·`html21b-cdp.py` 그대로다.\
★ **「실린」 격자** — 페이지가 `window.__표 = "실린"` 과 `window.__칸목록 = [[표시, 필드 이름], …]` 을 두면, 하네스가 시도마다 **서버가 파싱한 필드 이름 목록**(`INFO` 의 다섯째 칸)에서 찾아 「실림 / —」을 찍고 시도별 「실린 칸 N / M」을 센다. **그림 단추는 `clickat`**(요소 왼쪽 위에서 7, 5)로, 좌표는 매번 `getBoundingClientRect` 에서 계산한다.
★ **라디오** — 시도의 `뒤` 식(`찍기()`)을 **이동이 없을 때만** 평가해 켜진 라디오를 찍는다. 시도마다 페이지를 새로 열므로 앞 시도의 클릭이 남지 않는다.

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다. 이 주제의 블록은 **세 판이 한 글자도 같았다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **스무 칸의 값·역할 · `form.elements`** | 3 | 동작 방식 (1) · A1 |
| **네 제출 × 스무 칸의 실림** | 3 | 동작 방식 (1) · A2 |
| **multipart 빈 파일 칸** | 3 | 동작 방식 (2) · A3 |
| **라디오 여덟 × 네 시도** | 3 | 동작 방식 (3) · A4 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `file`·`color` 의 CDP 역할 | `button` · `ColorWell` | HTML-AAM 은 대응 역할 없음 |
| `color` 가 `red` 를 받는 것 | `#ff0000` | 명세의 현재 판 규칙 — 옛 판 엔진에서는 다를 수 있다(확인 안 함) |

**안 돌려 본 것** — ① **실제 파일을 고른 업로드**(`DOM.setFileInputFiles`). ② **`name` 없는 그림 단추** — A7 은 명세의 문장이다. ③ **키보드 화살표로 라디오 그룹을 도는 것.** ④ **`datalist` 안의 칸.**

**못 잰 것** — ① **파일·색 선택 창.** ② **스크린리더의 라디오 그룹 읽기.**

**부적용인 창** — **창 ③ · ④ · ⑥.** — **잴 것이 없다.**

## 용어 풀이

- **항목 목록** — 제출할 `이름·값` 쌍. 거름망을 통과한 칸만 든다.
- **체크 상태** — `.checked`. `checked` 속성은 초기값이다.
- **라디오 단추 그룹** — 같은 폼 소유자 · 같은 트리 · 같은 이름.
- **선택된 좌표** — 그림 단추를 누른 자리.
- **`_charset_`** — 인코딩 이름을 보내는 `hidden` 의 특수 이름.
