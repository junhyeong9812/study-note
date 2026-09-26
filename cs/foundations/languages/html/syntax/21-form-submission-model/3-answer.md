# html/syntax/21 — `<form>` 의 제출 모델: `action`/`method`/`enctype`·제출을 일으키는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였고 사람이 옮겨 적지 않았다. 하네스는 맨 아래 `## 실행 검증` 절에 있다(22\~24번이 같은 하네스를 쓴다).\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「Form submission」 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤(서버 요청 로그)다** — 폼이 무엇을 보냈는지는 서버가 받은 줄로만 안다(A1\~A5).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. GET 셋은 질의에 urlencoded 로 — `enctype` 을 무시한다 · POST 셋은 본문에 셋 다른 모양으로

**출력**

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '50,$p'
시도                          메서드  질의  본문          Content-Type                        「GET · urlencoded(기본)」과 갈린 칸
GET · urlencoded(기본)        GET     있음  없음          (없음)                              (기준)
GET · multipart/form-data     GET     있음  없음          (없음)                              0 / 4
GET · text/plain              GET     있음  없음          (없음)                              0 / 4
POST · urlencoded(기본)       POST    없음  퍼센트 인코딩 application/x-www-form-urlencoded   4 / 4
POST · multipart/form-data    POST    없음  multipart     multipart/form-data                 4 / 4
POST · text/plain             POST    없음  글자 그대로   text/plain                          4 / 4
method=put                    GET     있음  없음          (없음)                              0 / 4
action 없음 · POST            POST    없음  퍼센트 인코딩 application/x-www-form-urlencoded   4 / 4
본문에 실린 시도 = 4 / 8
갈린 칸 = 16 / 28
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '19,36p'
[POST · urlencoded(기본)]
  페이지  click(b4 · detail=1) → submit(submitter=b4)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd」
          필드  q=「한 글」 · s=「a&b=c+d」
[POST · multipart/form-data]
  페이지  click(b5 · detail=1) → submit(submitter=b5)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 2개 · 경계로 갈라 필드만 적는다)
          필드  q=「한 글」 · s=「a&b=c+d」
[POST · text/plain]
  페이지  click(b6 · detail=1) → submit(submitter=b6)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=한 글\r\ns=a&b=c+d\r\n」
          필드  q=「한 글」 · s=「a&b=c+d」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '37,48p'
[method=put]
  페이지  click(b7 · detail=1) → submit(submitter=b7)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80
          본문  (없음)
          필드  q=「한 글」
[action 없음 · POST]
  페이지  click(b8 · detail=1) → submit(submitter=b8)
  서버    A POST /html21b-21-grid.html  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
(exit 0)
```

**왜 그런가**

- ★★★ **GET 셋은 `질의 있음 · 본문 없음 · Content-Type 없음`** 이고 셋이 **한 글자도 같다** — `enctype` 을 무시했다(갈린 칸 0 / 4 · 0 / 4). **POST 셋은 `질의 없음 · 본문 있음`** 이고 본문 모양과 `Content-Type` 이 `enctype` 대로 갈렸다.
- ★★★ **`text/plain` 의 본문은 `q=한 글\r\ns=a&b=c+d\r\n`** — 인코딩이 없다. `s` 는 `a&b=c+d` **그대로**다. urlencoded 에서는 `s=a%26b%3Dc%2Bd` 였다.
- **`method=put` 은 GET**(무효 기본값), **`action` 없음은 `POST /html21b-21-grid.html`**(폼 문서의 URL).
- 본문에 실린 시도 **4 / 8**, 기준과 갈린 칸 **16 / 28**.

### 2. 서버가 받은 시도 9 / 16 — `submit()` 만 검증을 건너뛰고, Enter 는 단추와 칸 수로 갈린다

**출력**

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '77,$p'
시도                                    submit  invalid  서버가 받은 요청  「가 · 제출 단추 클릭」과 갈린 칸
가 · 제출 단추 클릭                     났다    —       1번               (기준)
가 · 칸에서 Enter                       났다    —       1번               0 / 3
가 · form.submit()                      —      —       1번               1 / 3
가 · form.requestSubmit()               났다    —       1번               0 / 3
가빈 · 제출 단추 클릭                   —      났다     0번               3 / 3
가빈 · 칸에서 Enter                     —      났다     0번               3 / 3
가빈 · form.submit()                    —      —       1번               1 / 3
가빈 · form.requestSubmit()             —      났다     0번               3 / 3
나 · 단추 없음 · 칸 하나 · Enter        났다    —       1번               0 / 3
나빈 · 단추 없음 · 칸 하나 · Enter      —      났다     0번               3 / 3
다 · 단추 없음 · 칸 둘 · Enter          —      —       0번               2 / 3
라 · 단추 없음 · 칸+체크박스 · Enter    났다    —       1번               0 / 3
마 · disabled 단추 · Enter              —      —       0번               2 / 3
바 · type=button 클릭                   —      —       0번               2 / 3
바 · type=button · Enter                났다    —       1번               0 / 3
사 · type=zzz 클릭                      났다    —       1번               0 / 3
서버가 받은 시도 = 9 / 16
갈린 칸 = 20 / 45
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '1,24p'
[가 · 제출 단추 클릭]
  페이지  click(가단추 · detail=1) → submit(submitter=가단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · 칸에서 Enter]
  페이지  click(가단추 · detail=0) → submit(submitter=가단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · form.submit()]
  페이지  (기록 없음)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · form.requestSubmit()]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '25,39p'
[가빈 · 제출 단추 클릭]
  페이지  click(가빈단추 · detail=1) → invalid(q)
  서버    (받은 요청 없음)
[가빈 · 칸에서 Enter]
  페이지  click(가빈단추 · detail=0) → invalid(q)
  서버    (받은 요청 없음)
[가빈 · form.submit()]
  페이지  (기록 없음)
  서버    A GET /r
          질의  q=
          본문  (없음)
          필드  q=「」
[가빈 · form.requestSubmit()]
  페이지  invalid(q)
  서버    (받은 요청 없음)
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '40,75p'
[나 · 단추 없음 · 칸 하나 · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[나빈 · 단추 없음 · 칸 하나 · Enter]
  페이지  invalid(q)
  서버    (받은 요청 없음)
[다 · 단추 없음 · 칸 둘 · Enter]
  페이지  (기록 없음)
  서버    (받은 요청 없음)
[라 · 단추 없음 · 칸+체크박스 · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1&c=on
          본문  (없음)
          필드  q=「1」 · c=「on」
[마 · disabled 단추 · Enter]
  페이지  (기록 없음)
  서버    (받은 요청 없음)
[바 · type=button 클릭]
  페이지  click(바단추 · detail=1)
  서버    (받은 요청 없음)
[바 · type=button · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[사 · type=zzz 클릭]
  페이지  click(사단추 · detail=1) → submit(submitter=사단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
(exit 0)
```

**왜 그런가**

- ★★★ **칸에서 Enter 는 `click(가단추 · detail=0)` → `submit(submitter=가단추)`** — 암묵 제출은 **기본 단추에 `click` 을 쏜다**(명세). 키보드라 클릭 수(`detail`)가 0 이다.
- ★★★ **`가빈 · form.submit()` 은 `q=「」` 를 보냈다** — `required` 인데 빈 값이다. 페이지 기록이 **비어 있다** — `submit` 이벤트도 `invalid` 도 없었다. 나머지 무효 시도는 전부 **`invalid(q)` 만 남기고 요청 0**.
- ★★ **`라` 의 질의는 `q=1&c=on`** — 체크박스는 암묵 제출을 막는 칸이 아니라 Enter 가 보냈고, 체크된 체크박스(`value` 없음)는 `on` 으로 실렸다([24번](../24-input-types-choice-special/3-answer.md)).
- ★★ **`다`(칸 둘 · 단추 없음) · `마`(`disabled` 단추) · `바` 의 클릭** 셋은 요청 0. **`바` 의 Enter · `사` 의 클릭**은 제출했다.

### 3. 덮기는 메서드·경로를 바꾼다 — 그런데 단추가 메서드를 바꾼 두 칸에서 본문 모양이 명세와 갈렸다

**출력**

```text
$ python3 html21b-form.py 시도 html21b-21-override.html | sed -n '1,30p'
[겟폼 · 폼의 설정]
  페이지  click(기본 · detail=1) → submit(submitter=기본)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80
          본문  (없음)
          필드  q=「한 글」
[겟폼 · button formaction·formmethod]
  페이지  click(덮음 · detail=1) → submit(submitter=덮음)
  서버    A POST /r2  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
[겟폼 · input formaction·formmethod]
  페이지  click(입력덮음 · detail=1) → submit(submitter=입력덮음)
  서버    A POST /r3  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
[겟폼 · formmethod=post formenctype=text/plain]
  페이지  click(글자 · detail=1) → submit(submitter=글자)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「%ED%95%9C+%EA%B8%80」
[겟폼 · requestSubmit(#덮음)]
  페이지  submit(submitter=덮음)
  서버    A POST /r2  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-override.html | sed -n '31,$p'
[포스트폼 · 폼의 설정]
  페이지  click(글자2 · detail=1) → submit(submitter=글자2)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=한 글\r\n」
          필드  q=「한 글」
[포스트폼 · formmethod=""]
  페이지  click(빈덮음 · detail=1) → submit(submitter=빈덮음)
  서버    A GET /r
          질의  q=%C3%AD%E2%80%A2%C5%93%20%C3%AA%C2%B8%E2%82%AC
          본문  (없음)
          필드  q=「í•œ ê¸€」
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`#덮음` → `POST /r2` urlencoded · `#입력덮음` → `POST /r3` urlencoded · `requestSubmit(#덮음)` → `POST /r2`** — 명세의 「요소의 method 는 **`formmethod` 가 있으면 그 상태**」 그대로다.
- ★★★ **`겟폼 · formmethod=post formenctype=text/plain` 의 본문은 `q=%ED%95%9C+%EA%B8%80`** — `Content-Type: text/plain` 인데 **urlencoded 모양**이다. 명세의 제출 알고리즘은 「**제출자 요소의** enctype」으로 `text/plain` 칸을 골라 「text/plain 인코딩 알고리즘」(= `q=한 글\r\n`)을 돌리라고 한다 — **갈렸다.**
- ★★★ **`포스트폼 · formmethod=""` 는 `GET /r` 인데 질의가 `q=%C3%AD%E2%80%A2%C5%93%20%C3%AA%C2%B8%E2%82%AC`** — 서버가 디코딩하면 `「í•œ ê¸€」`. GET 이면 명세는 **urlencoded 직렬화기**(`q=%ED%95%9C+%EA%B8%80`)다 — **갈렸다.** `formmethod=""` 가 GET 이 된 것 자체는 명세(무효 기본값 GET)대로다.
- ★ 두 갈림은 **「단추가 메서드를 바꾼」 자리에서만** 났다. 폼 자체가 정한 조합은 (1) 의 여섯 칸도 `포스트폼 · 폼의 설정` 도 명세와 같았다.

### 4. `form` 속성이 트리를 이기고, 표 안의 빈 `form` 도 제출되며, 안쪽 `form` 은 사라진다

**출력**

```text
$ python3 html21b-form.py page html21b-21-owner.html
id      name          부모      input.form
i1      안            form#갑   form#갑
i2      form속성      body      form#갑
i3      그냥밖        body      null
i4      을안인데갑    form#을   form#갑
i5      없는폼        body      null
i6      표안          td        form#병
병단추  (없음)        td        form#병
i7      중첩          form#겉   form#겉

form 개수 = 4 · id = 갑 · 을 · 병 · 겉
form#병 의 자식 수 = 0 · form#병.elements.length = 2
form#갑.elements = i1 · 갑단추 · i2 · i4
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-owner.html
[갑의 단추]
  페이지  click(갑단추 · detail=1) → submit(submitter=갑단추)
  서버    A GET /r
          질의  %EC%95%88=1&form%EC%86%8D%EC%84%B1=2&%EC%9D%84%EC%95%88%EC%9D%B8%EB%8D%B0%EA%B0%91=4
          본문  (없음)
          필드  안=「1」 · form속성=「2」 · 을안인데갑=「4」
[표 안의 form 병의 단추]
  페이지  click(병단추 · detail=1) → submit(submitter=병단추)
  서버    A GET /r3
          질의  %ED%91%9C%EC%95%88=6
          본문  (없음)
          필드  표안=「6」
[form 안의 form 의 단추]
  페이지  click(속단추 · detail=1) → submit(submitter=속단추)
  서버    A GET /r4
          질의  %EC%A4%91%EC%B2%A9=7
          본문  (없음)
          필드  중첩=「7」
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`i2`(`body`)·`i4`(`form#을` 의 자식)의 `input.form` 은 `form#갑`** — `form` 속성이 있으면 **그 id 의 폼**이 소유자다. 갑의 제출에 **`안`·`form속성`·`을안인데갑`** 셋이 실렸다. `i3`·`i5` 는 `null` 이라 어디에도 안 실린다.
- ★★★ **`form#병` 은 자식 0 · `elements.length = 2`**, 그 단추가 **`GET /r3` 로 `표안=6`** 을 보냈다 — 파서의 form 요소 포인터로 이어진 소유가 제출까지 간다([17번](../17-table-structure/3-answer.md) A2).
- ★★★ **`document.forms.length = 4`**(`속` 없음) — `속단추` 는 **겉의 `/r4`** 로 보냈다([05번](../05-content-categories-and-models/3-answer.md)).

### 5. 브라우저는 막고, `curl` 은 그대로 닿는다 — 서버가 받은 본문은 `novalidate` 와 한 글자도 같다

**출력**

```text
$ python3 html21b-form.py 시도 html21b-21-guard.html
[검증 있음]
  페이지  click(막음단추 · detail=1) → invalid(addr) → invalid(age)
  서버    (받은 요청 없음)
[novalidate]
  페이지  click(안막음단추 · detail=1) → submit(submitter=안막음단추)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html21b-form.py curl
보낸 명령  curl -s -o /dev/null -w '%{http_code}' --data 'addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5' http://127.0.0.1:<A>/r
  응답 코드 200 · curl exit 0
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
(exit 0)
```

**왜 그런가**

- **`검증 있음`** — `invalid(addr) → invalid(age)`, 요청 0. **`novalidate`** — 그대로 보냈다.
- ★★★ **`curl` 의 필드는 `addr=「아무 글자」 · age=「-5」`** — 응답 코드 200. 본문 줄이 `novalidate` 블록과 **같다.** 명세 — 「**서버는 클라이언트 쪽 검증에 기대면 안 된다.** 적대적 사용자가 일부러 건너뛸 수 있다 … 제약 검증 기능은 **사용자 경험을 좋게 하려는 것**이지 보안 장치가 아니다」.

### 6. 넷 다 역할 `form` — `name` 은 이름이 안 되고 `aria-label`·`title` 은 된다

**출력**

```text
$ python3 html21b-form.py ax html21b-21-ax.html
RootWebArea    이름='21 폼의 역할'
  form           이름=''
    textbox        이름='이름 없는 폼의 칸'
      generic        이름=''
  form           이름=''
    textbox        이름='name 속성만 있는 폼의 칸'
      generic        이름=''
  form           이름='검색 조건'
    textbox        이름='aria-label 폼의 칸'
      generic        이름=''
  form           이름='툴팁 제목'
    textbox        이름='title 폼의 칸'
      generic        이름=''
(exit 0)
```

**왜 그런가**

- **역할은 넷 다 `form`**, 이름은 `''` · `''` · `'검색 조건'` · `'툴팁 제목'`. **`name` 속성은 접근 가능한 이름이 되지 않았다**(`이름=''`).
- ★ HTML-AAM 의 「이름 없는 `form` 은 랜드마크로 노출하지 않는다」는 **이 트리로는 안 보인다** — A11.

### 7. GET 은 「Mutate action URL」 — urlencoded 직렬화기뿐이다

- 명세의 표에서 `http`/`https` + GET 은 **「Mutate action URL」** 이고, 그 단계는 「항목 목록을 이름·값 쌍으로 바꾸고 **`application/x-www-form-urlencoded` 직렬화기**를 돌려 **질의로 둔다**」가 전부다. `enctype` 을 읽는 줄이 **없다.** 「Submit as entity body」(POST) 쪽만 `enctype` 으로 갈린다.
- 그래서 **파일은 안 간다** — (1) 에서 GET · multipart 의 질의가 urlencoded 와 같았다. 파일 칸은 urlencoded 에서 **파일 이름**만 남는다([24번](../24-input-types-choice-special/3-answer.md)의 빈 파일 칸이 `f1=` 였다).

### 8. `submit()` 은 「`submit()` 에서 온 것이 아니면」 덩어리 전체를 건너뛴다 — `requestSubmit()` 을 쓴다

- 명세의 제출 알고리즘 — 「**submitted from submit() method 가 거짓이면**: … 제약을 대화형으로 검증하고 결과가 부정이면 돌아간다 … `submit` 이벤트를 쏘고 취소됐으면 돌아간다」. `submit()` 은 이 플래그를 **참**으로 넘겨 **검증과 `submit` 이벤트를 통째로** 건너뛴다(A2 의 `가빈 · form.submit()`).
- **`form.requestSubmit(단추?)`** — (2) 에서 무효 폼은 `invalid(q)` 로 멈췄고, 유효 폼은 `submit(submitter=null)` 을 냈다. 인자로 단추를 주면 그 단추의 `formaction` 등도 쓴다((3)).

### 9. 로그인 폼은 Enter 가 아무것도 안 한다 — 체크박스와 `type=button` 은 셈에 안 든다

- **아이디(`text`) + 비밀번호(`password`)** 는 **암묵 제출을 막는 칸 둘**이다. 제출 단추가 없으면 명세 — 「막는 칸이 **둘 이상**이면 돌아간다」 — 로 **아무 일도 없다**((2) 의 `다` 와 같은 꼴).
- **체크박스는 막는 칸이 아니다**(목록에 없다 — (2) 의 `라` 가 보냈다). **`type="button"` 은 제출 단추가 아니다** — 그래서 그 폼은 「단추 없는 폼」 갈래로 가서 **칸 하나면 보낸다**(`바`).
- **기본 단추가 `disabled` 면 아무 일도 없다** — 명세의 조건이 「기본 단추에 활성화 동작이 있고 **비활성이 아니면** click」이고, 단추가 **있으므로** 「단추 없음」 갈래도 안 탄다(`마`).

### 10. 갈림은 (3) 의 두 줄 — 판별은 「DOM 조작 작업 원천」 문장과 `beforeunload` 관찰 위에 섰다

- ★★★ **Chrome 이 명세와 갈린 자리** — (3) 의 ① 폼 GET + 단추 `formmethod=post formenctype=text/plain` → 본문이 urlencoded 모양, ② 폼 POST·`text/plain` + 단추 `formmethod=""` → GET 질의의 한글이 깨지고 공백이 `%20`. 갈린 문장은 제출 알고리즘의 「**제출자 요소의** method / enctype 을 쓴다」와 「text/plain 인코딩 알고리즘」·「Mutate action URL = urlencoded 직렬화기」다.
- **판별 근거** — 명세의 「plan to navigate」 — 「폼 요소에 대해 **DOM 조작 작업 원천**에 요소 작업을 넣는다」. 하네스가 같은 원천에 `details` 의 `toggle` 작업을 뒤에 넣으면, 그 작업이 돌 때 **먼저 들어간 이동 작업은 이미 돌았다.** ★ **관찰인 것** — ① Chrome 이 폼 제출 작업과 `toggle` 작업을 **같은 줄에 순서대로** 넣는다는 것, ② 그 이동 작업 안에서 **`beforeunload` 가 난다**는 것. 그 전제가 틀려 **「안 갔다」로 적은 뒤 요청이 뒤늦게 오면** 다음 시도가 페이지를 열 때 잡히게 짰고, (2) 의 격자 끝줄이 **`뒤늦게 온 요청 = 0`** 이다(16시도 중 7시도가 「안 갔다」).
- **`invalid` 창이 못 보는 것** — **검증이 돌았는데 통과한** 경우. 그래서 무효 폼을 따로 뒀다(제5의 상태 — 「검증이 돌았나」를 `invalid` 로 물었다).

### 11. 둘 다 못 한다 — 랜드마크는 제3의 상태, 서버 쪽은 (5) 의 두 블록이 근거다

- **증명하지 못했다.** CDP 트리는 넷 다 역할 `form` 을 준다(A6). 「랜드마크로 노출하지 않는다」는 **플랫폼 접근성 API 층**의 일이고 이 판에는 그 층을 읽는 도구가 없다 — **제3의 상태(못 잰 것)** 다. 「잴 것이 없다」가 아니다 — 층은 존재한다.
- **알 수 없다** — (5) 의 **`novalidate` 블록과 `curl` 블록의 「본문」 줄이 한 글자도 같다.** 요청에 「검증을 거쳤다」를 담는 칸이 없다.

### 12. 정본 경계

- **트리 쪽** — `form` 안의 `form`: [05번 주제](../05-content-categories-and-models/2-summary.md) · 표 안의 `form`: [17번 주제](../17-table-structure/2-summary.md). 여기는 **그 트리가 제출에 어떻게 번지나**부터.
- **이벤트 사슬** — [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)의 (8). 여기는 **폼 모양에 따라 Enter 가 무엇을 하나**.
- **`FormData`** — 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **30번**. **`button` 의 `type`·`form` 속성** — 목록의 **32번 주제**. **검증 상태·`novalidate`** — 목록의 **29번 주제**.
- **HTTP 연혁** — [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md) 의 HTTP/1.0 절(`POST` 추가). ★ **본문 형식 절은 없다**(`urlencoded`·`multipart`·`질의` 로 `grep` — 0줄).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★ **서버는 하네스 프로세스 안의 스레드 하나(A)** 다. 포트는 0 으로 열어 **운영체제가 고르고**, 로그에는 서버 이름만 적는다. 파일은 이 주제의 소스 폴더에서 내주고, `/r` 로 시작하는 경로는 받은 것을 적은 뒤 「받음」 한 장을 돌려준다.

**하네스 — 16번 판의 서버와 17번 판의 CDP 연결을 이었다.**
① [16번 주제](../16-links/3-answer.md)의 `html13b-link.py` 에서 **「프로세스 안의 서버」** 를 가져와 **POST 본문·질의·`Content-Type`** 을 적게 넓혔다. ★ **multipart 는 경계로 갈라 필드 목록만** 적는다(경계 문자열이 실행마다 바뀌므로 흔들리는 칸을 아예 안 만든다). ★ **필드 값은 디코딩해 「」 안에**, 인코딩된 원문은 「질의」·「본문」 줄에 둔다.
② [17번 주제](../17-table-structure/3-answer.md)의 `html17b-cdp.py`(포트 0 + `DevToolsActivePort` · `loadEventFired` · `page` 모드 · 창 ⑦)에서 **폼에 안 쓰는 부품**(픽셀·글꼴·하이픈·내부 덤프)을 걷어 내고, **환경 변수를 넘기는 자리**를 하나 더했다(23번의 로케일).
③ ★★ **「제출이 났나」를 시간 상수 없이 가른다** — 처음에는 CDP 의 `Page.frameRequestedNavigation` 이 **동작 명령의 응답보다 먼저 오는지**로 가르려 했다. `requestSubmit()` 을 `Runtime.evaluate` 로 부른 판은 먼저 왔지만, **진짜 마우스 클릭 판은 응답 뒤에 왔다** — 그대로 썼으면 여덟 시도 **전부 「안 받았다」** 로 적혔다(탐색 판, 캡처로 남기지 않았다). 그래서 명세의 「DOM 조작 작업 원천」 문장에 기대 **같은 원천의 `toggle` 작업을 울타리로** 세웠다(A10).
④ ★ **CDP 의 진짜 입력** — 클릭은 `Input.dispatchMouseEvent`, Enter 는 `Input.dispatchKeyEvent`(`keyDown` 에 `text: "\r"`), 글자 입력은 `Input.insertText`.
★ **Chrome 정리** — 하네스는 **자기 프로필 경로**로 띄운 **자기 프로세스**만 끝낸다(`proc.terminate()`).

```python
# html21b-form.py
#!/usr/bin/env python3
"""21~24 폼 — 창 ⑤(서버 요청 로그)를 본체로 쓰는 실행기.

사용: html21b-form.py [--lang=xx-YY] 시도 <페이지> | page <페이지> | ax <페이지> | curl
     html21b-form.py 로케일 <페이지> <로케일1> <로케일2>
  · 서버 하나(A)를 이 프로세스 안에 띄운다. 포트는 0 — 운영체제가 고른다(출력에는 서버 이름 A 만 적는다).
  · 서버 로그는 「서버 · 메서드 · 경로 · Content-Type · 질의 · 본문 · 필드」만 적는다. 시각·포트는 안 적는다.
    ★ multipart 의 경계(boundary) 문자열은 실행마다 바뀐다 — 싣지 않고 경계로 본문을 갈라 **필드 목록만** 적는다.
    ★ 필드 값은 디코딩해서 「」 안에 적는다. 퍼센트 인코딩된 원문은 「본문」·「질의」 줄에 그대로 둔다.
  · 시도 — 페이지의 window.__시도 = [{이름, 단계: [...]}, ...] 를 하나씩 돈다.
    시도마다 페이지를 새로 열고 → sessionStorage 를 비우고 → 단계를 실행한 뒤
    (시도에 「뒤」 식이 있고 이동이 없었으면 그 식을 평가해 「뒤」 줄로 찍는다)
    ★ 「제출이 일어났나」는 동작 명령의 응답보다 먼저 도착하는 Page.frameRequestedNavigation 으로 가른다
      (시간 상수 없음). 일어났으면 새 문서의 loadEventFired 를 기다린다.
    페이지 쪽 기록(click·submit·invalid)은 html21b-rec.js 가 sessionStorage 에 적어 둔다 —
    같은 출처로 이동해도 같은 탭이면 남는다.
  단계 꼴:
    ["js", 식]                     페이지 안에서 평가한다
    ["click", 선택자]              그 요소 한가운데를 진짜 마우스로 누른다
    ["clickat", 선택자, dx, dy]    그 요소 왼쪽 위에서 (dx, dy) 떨어진 점을 누른다
    ["enter", 선택자]              그 요소에 포커스를 두고 진짜 Enter 를 누른다
    ["type", 선택자, 글자]         그 요소에 포커스를 두고 글자를 입력한다(Input.insertText)
    ["key", 선택자, key, code, 가상키코드]  그 요소에 포커스를 두고 글자 없는 키(화살표 등)를 누르고 뗀다
  · --lang=xx-YY — Chrome 을 그 로케일로 띄운다(23편 — 환경 변수 LANGUAGE). 이때 로그에 Accept-Language 를 함께 적는다.
"""
import http.server, importlib.util, json, os, shutil, subprocess, sys, threading, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html21b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)

LOG = []
INFO = []          # 요청마다 격자용 요약 — (메서드, 질의 있나, 본문 종류, Content-Type)
LOCK = threading.Lock()
LANG = None
RESULT = '<!DOCTYPE html><meta charset="utf-8"><link rel="icon" href="data:,"><title>받음</title><p>받음</p>'.encode()


def 값(s):
    return "「" + s.replace("\r", "\\r").replace("\n", "\\n") + "」"


def 필드_urlencoded(raw):
    return [(k, v) for k, v in urllib.parse.parse_qsl(raw, keep_blank_values=True)]


def 적기(label, method, path, headers, body):
    out = []
    ct = headers.get("Content-Type")
    u = urllib.parse.urlsplit(path)
    head = f"{label} {method} {u.path}"
    if ct:
        if ct.startswith("multipart/form-data"):
            head += "  Content-Type=multipart/form-data; boundary=(경계)"
        else:
            head += f"  Content-Type={ct}"
    out.append(head)
    if LANG:
        out.append(f"  Accept-Language  {headers.get('Accept-Language', '(없음)')}")
    out.append(f"  질의  {u.query if u.query else '(없음)'}")
    fields = 필드_urlencoded(u.query) if u.query else []
    if method == "POST":
        if ct and ct.startswith("multipart/form-data"):
            b = ct.split("boundary=", 1)[1].encode()
            parts = body.split(b"--" + b)[1:-1]
            out.append(f"  본문  (multipart — 부분 {len(parts)}개 · 경계로 갈라 필드만 적는다)")
            fields = []
            for p in parts:
                h, _, v = p[2:].partition(b"\r\n\r\n")
                v = v[:-2] if v.endswith(b"\r\n") else v
                hs = h.decode().split("\r\n")
                disp = next(x for x in hs if x.lower().startswith("content-disposition"))
                name = disp.split('name="', 1)[1].split('"', 1)[0]
                extra = []
                if 'filename="' in disp:
                    extra.append("filename=" + 값(disp.split('filename="', 1)[1].split('"', 1)[0]))
                for x in hs:
                    if x.lower().startswith("content-type"):
                        extra.append("부분 " + x)
                fields.append((name, v.decode() + ("" if not extra else "\0" + " · ".join(extra))))
        else:
            text = body.decode()
            out.append(f"  본문  {값(text) if text else '(빈 본문)'}")
            if ct == "text/plain":
                fields = [tuple(line.split("=", 1)) for line in text.split("\r\n") if line]
            else:
                fields = 필드_urlencoded(text)
    else:
        out.append("  본문  (없음)")
    shown = []
    for k, v in fields:
        v, _, extra = v.partition("\0")
        shown.append(f"{k}={값(v)}" + (f" ({extra})" if extra else ""))
    out.append("  필드  " + (" · ".join(shown) if shown else "(없음)"))
    kind = "없음" if method != "POST" else ("multipart" if ct and ct.startswith("multipart")
                                             else "글자 그대로" if ct == "text/plain" else "퍼센트 인코딩")
    info = (method, "있음" if u.query else "없음", kind,
            "multipart/form-data" if ct and ct.startswith("multipart") else (ct or "(없음)"),
            [k for k, _ in fields], u.path)
    return out, info


def server(label):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def 기록(self, method, body=b""):
            if not self.path.endswith(".js"):
                lines, info = 적기(label, method, self.path, self.headers, body)
                with LOCK:
                    LOG.extend(lines)
                    INFO.append(info)

        def 받음(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(RESULT)))
            self.end_headers()
            self.wfile.write(RESULT)

        def do_GET(self):
            self.기록("GET")
            if self.path.startswith("/r"):
                return self.받음()
            return super().do_GET()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            self.기록("POST", self.rfile.read(n))
            return self.받음()

        def log_message(self, *a):
            pass

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def take_log():
    with LOCK:
        out = LOG[:]
        LOG.clear()
        INFO.clear()
    return out


def take_info():
    with LOCK:
        return INFO[:]


def center(c, sid, sel, off=None):
    at = "[r.x + r.width / 2, r.y + r.height / 2]" if off is None else \
         "[r.x + %s, r.y + %s]" % (json.dumps(off[0]), json.dumps(off[1]))
    xy = cdp.evaluate(c, sid, "(() => { const r = document.querySelector(" + json.dumps(sel)
                      + ").getBoundingClientRect(); return " + at + "; })()")
    if not isinstance(xy, list):
        raise RuntimeError("좌표를 못 얻었다: " + sel + " " + str(xy))
    return xy


def focus(c, sid, sel):
    r = cdp.evaluate(c, sid, "(() => { const e = document.querySelector(" + json.dumps(sel)
                     + "); e.focus(); return document.activeElement === e; })()")
    if r is not True:
        raise RuntimeError("포커스를 못 줬다: " + sel)


def 단계(c, sid, st):
    kind = st[0]
    if kind == "js":
        v = cdp.evaluate(c, sid, st[1])
        if isinstance(v, str) and v.startswith("«예외"):
            raise RuntimeError(st[1] + " -> " + v)
    elif kind in ("click", "clickat"):
        x, y = center(c, sid, st[1], st[2:4] if kind == "clickat" else None)
        c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
        for t in ("mousePressed", "mouseReleased"):
            c.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                   "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)
    elif kind == "enter":
        focus(c, sid, st[1])
        for t in ("keyDown", "keyUp"):
            prm = {"type": t, "key": "Enter", "code": "Enter",
                   "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13}
            if t == "keyDown":
                prm["text"] = "\r"
            c.send("Input.dispatchKeyEvent", prm, sid)
    elif kind == "key":
        focus(c, sid, st[1])
        for t in ("keyDown", "keyUp"):
            c.send("Input.dispatchKeyEvent", {"type": t, "key": st[2], "code": st[3],
                   "windowsVirtualKeyCode": st[4], "nativeVirtualKeyCode": st[4]}, sid)
    elif kind == "type":
        focus(c, sid, st[1])
        c.send("Input.insertText", {"text": st[2]}, sid)
    else:
        raise RuntimeError("모르는 단계: " + kind)


FENCE = """new Promise(r => { const d = document.createElement('details');
  d.addEventListener('toggle', () => r(sessionStorage.getItem('떠남') || '안 떠남'), { once: true });
  document.body.append(d); d.open = true; })"""


def 울타리(c, sid):
    """제출이 계획됐나 — 폼 제출의 이동은 DOM 조작 작업 원천의 작업으로 뒤로 미뤄진다.
    같은 작업 원천에 details 의 toggle 작업을 하나 더 넣고, 그것이 돌 때 beforeunload 가 이미 났나를 본다."""
    r = c.send("Runtime.evaluate", {"expression": FENCE, "awaitPromise": True, "returnByValue": True}, sid)
    v = r.get("result", {}).get("value")
    return v == "1" or "exceptionDetails" in r


def goto(c, sid, url):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)


def 너비(s):
    return sum(2 if ord(ch) > 0x1100 else 1 for ch in s)


def 칸(s, w):
    return s + " " * max(w - 너비(s), 1)


def 시도(c, sid, base, page):
    goto(c, sid, base + page)
    trials = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__시도)"))
    kind = cdp.evaluate(c, sid, "window.__표 || ''")
    names = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸목록 || [])"))
    rows = []
    late = 0
    for t in trials:
        goto(c, sid, base + page)
        cdp.evaluate(c, sid, "sessionStorage.clear(); 1")
        # ★ 앞 시도가 「안 갔다」로 적혔는데 요청이 뒤늦게 왔다면 여기서 잡힌다(이 페이지를 연 요청은 뺀다)
        late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
        take_log()
        for st in t["단계"]:
            단계(c, sid, st)
        went = 울타리(c, sid)
        if went:
            c.wait("Page.loadEventFired", sid)
        rec = json.loads(cdp.evaluate(c, sid, "sessionStorage.getItem('기록') || '[]'"))
        after = cdp.evaluate(c, sid, t["뒤"]) if t.get("뒤") and not went else None
        info = take_info()
        log = take_log()
        print(f"[{t['이름']}]")
        print("  페이지  " + (" → ".join(rec) if rec else "(기록 없음)"))
        if after is not None:
            print("  뒤      " + str(after))
        for line in log:
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        if not log:
            print("  서버    (받은 요청 없음)")
        rows.append((t["이름"], "났다" if any(r.startswith("submit") for r in rec) else "—",
                     "났다" if any(r.startswith("invalid") for r in rec) else "—",
                     str(len(info)) + "번", info))
    if kind == "제출":
        print()
        print(칸("시도", 40) + 칸("submit", 8) + 칸("invalid", 9) + "서버가 받은 요청  「" + rows[0][0] + "」과 갈린 칸")
        hit = total = 0
        for r in rows:
            d = sum(1 for i in (1, 2, 3) if r[i] != rows[0][i])
            if r is not rows[0]:
                hit += d
                total += 3
            print(칸(r[0], 40) + 칸(r[1], 8) + 칸(r[2], 9) + 칸(r[3], 18) + ("(기준)" if r is rows[0] else f"{d} / 3"))
        print(f"서버가 받은 시도 = {sum(1 for r in rows if r[4])} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "싣기":
        print()
        print(칸("시도", 30) + 칸("메서드", 8) + 칸("질의", 6) + 칸("본문", 14) + 칸("Content-Type", 36) + "「" + rows[0][0] + "」과 갈린 칸")
        base_i = rows[0][4][0]
        hit = total = 0
        for r in rows:
            m, q, b, ct = r[4][0][:4]
            d = sum(1 for x, y in zip((m, q, b, ct), base_i[:4]) if x != y)
            if r is not rows[0]:
                hit += d
                total += 4
            print(칸(r[0], 30) + 칸(m, 8) + 칸(q, 6) + 칸(b, 14) + 칸(ct, 36) + ("(기준)" if r is rows[0] else f"{d} / 4"))
        print(f"본문에 실린 시도 = {sum(1 for r in rows if r[4][0][2] != '없음')} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "실린":
        print()
        print((칸("칸", 34) + "".join(칸(f"({k + 1})", 6) for k in range(len(rows)))).rstrip())
        for label, field in names:
            print((칸(label, 34) + "".join(칸("실림" if r[4] and field in r[4][0][4] else "—", 6) for r in rows)).rstrip())
        for k, r in enumerate(rows):
            n = sum(1 for _, field in names if r[4] and field in r[4][0][4])
            print(f"({k + 1}) {r[0]} — 실린 칸 = {n} / {len(names)}")
    goto(c, sid, base + page)
    late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
    take_log()
    print(f"뒤늦게 온 요청 = {late}")
    return rows


def 화면글자(c, sid, sel):
    """창 ⑦ — 그 입력 칸 아래 StaticText 를 트리 순서로 이어 붙인다(선택도구 단추는 뺀다). 화면에 그려진 글자다."""
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": sel}, sid)["nodeId"]
    be = cdp.backend(c, sid, nid)
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    top = next(n for n in nodes if n.get("backendDOMNodeId") == be)
    out = []

    def walk(n):
        role = cdp.val(n, "role")
        if role == "button":
            return
        if role == "StaticText":
            out.append(cdp.val(n, "name"))
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch])
    walk(top)
    return "".join(out)


def 로케일(page, langs):
    """같은 페이지를 로케일마다 새 브라우저로 열어 — 준비 단계(입력) → 화면 글자 → 제출 → 서버 필드."""
    global LANG
    got = {}
    for lang in langs:
        LANG = lang
        env = {**os.environ, "LANGUAGE": lang.replace("-", "_")}
        a = server("A")
        base = f"http://127.0.0.1:{a.server_address[1]}/"
        proc, c = cdp.start((), env)
        try:
            tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
            sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
            for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable"):
                c.send(m, sid=sid)
            goto(c, sid, base + page)
            nav = cdp.evaluate(c, sid, "navigator.language")
            for st in json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__준비 || [])")):
                단계(c, sid, st)
            ids = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸)"))
            screen = {i: 화면글자(c, sid, "#" + i) for i in ids}
            take_log()
            단계(c, sid, ["click", cdp.evaluate(c, sid, "window.__보냄")])
            if 울타리(c, sid):
                c.wait("Page.loadEventFired", sid)
            info = take_info()
            log = take_log()
        finally:
            proc.terminate()
            proc.wait()
            shutil.rmtree(cdp.PROF, ignore_errors=True)
            a.shutdown()
        body = next(l for l in log if l.strip().startswith("본문"))
        fields = dict(urllib.parse.parse_qsl(body.split("「", 1)[1].rsplit("」", 1)[0], keep_blank_values=True))
        al = next(l for l in log if "Accept-Language" in l).split()[-1]
        got[lang] = (nav, al, screen, fields, body.strip(), len(info))
    L1, L2 = langs
    for lang in langs:
        nav, al, _, _, body, n = got[lang]
        print(f"[{lang}]  navigator.language = {nav} · 요청 {n}번")
        print(f"  Accept-Language  {al}")
        print(f"  {body}")
    print()
    ids = list(got[L1][2])
    print(칸("칸", 5) + 칸(f"화면({L1})", 26) + 칸(f"화면({L2})", 26) + 칸(f"서버({L1})", 20) + f"서버({L2})")
    ds = dv = 0
    for i in ids:
        s1, s2 = got[L1][2][i], got[L2][2][i]
        v1, v2 = got[L1][3].get(i, "(없음)"), got[L2][3].get(i, "(없음)")
        ds += s1 != s2
        dv += v1 != v2
        print(칸(i, 5) + 칸(json.dumps(s1, ensure_ascii=False), 26) + 칸(json.dumps(s2, ensure_ascii=False), 26)
              + 칸(json.dumps(v1, ensure_ascii=False), 20) + json.dumps(v2, ensure_ascii=False))
    print(f"화면 글자가 갈린 칸 = {ds} / {len(ids)}")
    print(f"서버 값이 갈린 칸 = {dv} / {len(ids)}")


def main():
    global LANG
    args = sys.argv[1:]
    extra = []
    env = None
    if args and args[0].startswith("--lang="):
        # ★ 리눅스의 Chrome 은 --lang 플래그를 안 듣는다(실측) — 환경 변수 LANGUAGE 로 로케일을 준다
        LANG = args.pop(0).split("=", 1)[1]
        env = {**os.environ, "LANGUAGE": LANG.replace("-", "_")}
    mode = args[0]
    if mode == "로케일":
        로케일(args[1], args[2:4])
        return
    a = server("A")
    base = f"http://127.0.0.1:{a.server_address[1]}/"
    if mode == "curl":
        # 폼을 거치지 않고 같은 본문을 직접 보낸다 — 브라우저도, 검증도 없다
        body = "addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5"
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--data", body, base + "r"]
        print("보낸 명령  curl -s -o /dev/null -w '%{http_code}' --data '" + body + "' http://127.0.0.1:<A>/r")
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("  응답 코드 " + r.stdout + " · curl exit " + str(r.returncode))
        for line in take_log():
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        a.shutdown()
        return
    proc, c = cdp.start(extra, env)
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable"):
            c.send(m, sid=sid)
        if mode == "시도":
            시도(c, sid, base, args[1])
        elif mode == "page":
            goto(c, sid, base + args[1])
            targets = cdp.evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: cdp.ax_of(c, sid, sel) for k, sel in json.loads(targets)}
            cdp.evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            take_log()
            print(cdp.evaluate(c, sid, "window.__끝()"))
        elif mode == "ax":
            goto(c, sid, base + args[1])
            cdp.dump_tree(c, sid)
        else:
            sys.exit("모드는 시도 | page | ax | curl")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(cdp.PROF, ignore_errors=True)
        a.shutdown()


if __name__ == "__main__":
    main()
```

```python
# html21b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙는 공용 부품 — html21b-form.py 가 불러 쓴다(17편 판에서 폼에 안 쓰는 부품을 걷어 냈다).

사용(단독):
  html21b-cdp.py ax   <url|파일>   접근성 트리 전체를 트리 순서로 찍는다
  html21b-cdp.py page <url|파일>   페이지의 window.__대상 = [[열쇠, 선택자], ...] 마다
                              접근성 노드(역할·이름·설명·무시 여부)를 받아 window.__AX 로 넣고
                              window.__끝() 이 돌려준 문자열을 찍는다(표 짜기·칸 세기는 페이지가 한다)

★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 묻는다.
★ CDP 포트와 프로필 경로는 실행마다 다르다 — 출력에는 안 들어간다.
★ start(extra, env) — 추가 플래그·환경 변수를 주면 그것으로 띄운다(23편의 로케일은 환경 변수 LANGUAGE).
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-html21b-{os.getpid()}")
# ★ 포트는 0 — Chrome 이 빈 포트를 고르고 프로필의 DevToolsActivePort 에 적는다.
#   고정 범위에서 무작위로 고르면 같은 기계의 다른 작업과 겹칠 수 있다(뒤 브라우저가 앞에 붙는다).
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--force-renderer-accessibility", "--remote-debugging-port=0",
         f"--user-data-dir={PROF}", "about:blank"]


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(method + " " + json.dumps(r["error"], ensure_ascii=False))
                return r.get("result", {})
            self.events.append(r)

    def post(self, method, params=None, sid=None):
        """응답을 안 기다리고 보낸다 — 디버거 대기 중인 새 창은 run 전까지 답을 안 한다."""
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))

    def wait(self, method, sid=None, pred=lambda p: True):
        """이미 받아 둔 이벤트부터 뒤지고, 없으면 올 때까지 막고 기다린다."""
        while True:
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid) \
                        and pred(e.get("params", {})):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start(extra=(), env=None):
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS[:-1] + list(extra) + FLAGS[-1:],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def open_page(c, url):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable"):
        c.send(m, sid=sid)
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)
    return sid


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def val(node, key):
    return (node.get(key) or {}).get("value", "")


def ax_of(c, sid, selector):
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": selector}, sid)["nodeId"]
    if not nid:
        return {"없음": True}
    nodes = c.send("Accessibility.getPartialAXTree",
                   {"nodeId": nid, "fetchRelatives": True}, sid)["nodes"]
    n = next(x for x in nodes if x.get("backendDOMNodeId") and
             x["backendDOMNodeId"] == backend(c, sid, nid))
    kids = [x for x in nodes if x.get("parentId") == n["nodeId"]]
    props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])}
    return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"),
            "무시": bool(n.get("ignored")), "속성": props,
            "표지": [val(x, "name") for x in kids if val(x, "role") == "ListMarker"]}


def backend(c, sid, nid):
    return c.send("DOM.describeNode", {"nodeId": nid}, sid)["node"]["backendNodeId"]


def dump_tree(c, sid):
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    SKIP = {"InlineTextBox"}

    def walk(n, d):
        role = val(n, "role")
        ignored = n.get("ignored")
        if role not in SKIP and not ignored:
            name = val(n, "name")
            props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])
                     if p["name"] == "level" or (p["name"] == "url" and role == "link")}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r} {extra}".rstrip())
            d += 1
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch], d)

    for n in nodes:
        if not n.get("parentId"):
            walk(n, 0)


def main():
    mode, url = sys.argv[1], sys.argv[2]
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    proc, c = start()
    try:
        sid = open_page(c, url)
        if mode == "ax":
            dump_tree(c, sid)
        elif mode == "page":
            targets = evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: ax_of(c, sid, s) for k, s in json.loads(targets)}
            evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            print(evaluate(c, sid, "window.__끝()"))
        else:
            sys.exit("모드는 ax | page")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

**캡처 조립기** — 이 배치(21\~24)가 공유한다. 블록마다 **한 번만 돌려 받아 둔 뒤** 자르는 필터를 건다(파이프를 하네스에 물리지 않는다 — 규칙 19-A).

```bash
# capture.sh
#!/usr/bin/env bash
# html21b 묶음(HTML 21~24 폼) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 출력 디렉토리를 첫머리에서 절대경로로 정규화한다(규칙 25).
# ★ set -o pipefail — 없으면 파이프 뒤 명령의 종료 코드가 기록된다.
# ★ 자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 — 전부 받아 둔 뒤 필터를 건다.
# ★ grep -c 를 블록의 마지막 명령으로 두지 않는다(0건이면 exit 1).
# ★ 표준 출력만 싣는다 — 표준 오류는 버린다(규칙 18).
# ★ 서버 포트는 운영체제가 고른다 — 출력에는 서버 이름 A 만 나온다. multipart 경계는 하네스가 지운다.
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

CH="google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800"
MARK="sed -n '/^--OUT\$/,/^OUT--\$/{//!p}'"

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

# 출력 블록 — 코드펜스째 뱉는다. 배너 = 실제로 던진 명령 + (있으면) 자르는 필터.
out_block() {  # out_block <블록이름> <열쇠> <명령> [필터]
  local name="$1" key="$2" cmd="$3" pipe="$4" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$cmd" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$cmd"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

form() {  # form <블록이름> <인자…> [-- 필터]
  local name="$1"; shift
  local args="" pipe=""
  while [ $# -gt 0 ]; do
    if [ "$1" = "--" ]; then pipe="$2"; break; fi
    args="$args $1"; shift
  done
  args="${args# }"
  out_block "$name" "form-${args// /_}" "python3 html21b-form.py $args" "$pipe"
}
dom() { out_block "$1" "dom-$2" "$CH --dump-dom $2 2>/dev/null" "$3"; }

# 소스 삽입용 블록 — 원고의 펜스 안에 들어가므로 펜스로 감싸지 않는다.
# 배너는 여기서만 찍는다(basename — 규칙 28). 원고에 손으로 쓰면 이중 배너가 된다.
src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_js()   { { printf '// %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version"

# ------------------------------------------------------------ 21 제출 모델
src_js   21-rec-src      html21b-rec.js
src_html 21-grid-src     html21b-21-grid.html
form     21-grid-get     시도 html21b-21-grid.html -- "sed -n '1,18p'"
form     21-grid-post    시도 html21b-21-grid.html -- "sed -n '19,36p'"
form     21-grid-odd     시도 html21b-21-grid.html -- "sed -n '37,48p'"
form     21-grid-table   시도 html21b-21-grid.html -- "sed -n '50,\$p'"
src_html 21-trigger-src  html21b-21-trigger.html
form     21-trigger-ga   시도 html21b-21-trigger.html -- "sed -n '1,24p'"
form     21-trigger-bin  시도 html21b-21-trigger.html -- "sed -n '25,39p'"
form     21-trigger-rest 시도 html21b-21-trigger.html -- "sed -n '40,75p'"
form     21-trigger-table 시도 html21b-21-trigger.html -- "sed -n '77,\$p'"
src_html 21-override-src html21b-21-override.html
form     21-override-get 시도 html21b-21-override.html -- "sed -n '1,30p'"
form     21-override-post 시도 html21b-21-override.html -- "sed -n '31,\$p'"
src_html 21-owner-src    html21b-21-owner.html
form     21-owner-page   page html21b-21-owner.html
form     21-owner-out    시도 html21b-21-owner.html
src_html 21-guard-src    html21b-21-guard.html
form     21-guard-out    시도 html21b-21-guard.html
form     21-curl-out     curl
src_html 21-ax-src       html21b-21-ax.html
form     21-ax-out       ax html21b-21-ax.html

# ------------------------------------------------------------ 22 텍스트 계열
src_html 22-types-src    html21b-22-types.html
form     22-types-page   --lang=ko-KR page html21b-22-types.html
form     22-types-de     --lang=de-DE page html21b-22-types.html -- "sed -n '/^validationMessage/,/^\$/p'"
form     22-types-out    시도 html21b-22-types.html
src_html 22-dump-src     html21b-22-dump.html
dom      22-dump-dom     html21b-22-dump.html
src_html 22-demo-src     html21b-22-demo.html
src_html 22-democheck-src html21b-22-democheck.html
dom      22-democheck-out html21b-22-democheck.html "$MARK"

# ------------------------------------------------------------ 23 숫자·날짜
src_html 23-locale-src   html21b-23-locale.html
form     23-locale-out   로케일 html21b-23-locale.html ko-KR de-DE
form     23-locale-ax    --lang=ko-KR ax html21b-23-locale.html -- "sed -n '1,17p'"
src_html 23-values-src   html21b-23-values.html
form     23-values-out   --lang=ko-KR page html21b-23-values.html
src_html 23-range-src    html21b-23-range.html
form     23-range-out    --lang=ko-KR page html21b-23-range.html
src_html 23-phone-src    html21b-23-phone.html
form     23-phone-out    시도 html21b-23-phone.html
src_html 23-lang-src     html21b-23-lang.html
out_block 23-lang-flag   lang-flag "$CH --lang=de-DE --dump-dom html21b-23-lang.html 2>/dev/null" "$MARK"
out_block 23-lang-env    lang-env "LANGUAGE=de_DE $CH --dump-dom html21b-23-lang.html 2>/dev/null" "$MARK"
src_html 23-demo-src     html21b-23-demo.html
src_html 23-democheck-src html21b-23-democheck.html
dom      23-democheck-out html21b-23-democheck.html "$MARK"

# ------------------------------------------------------------ 24 선택·특수
src_html 24-sent-src     html21b-24-sent.html
form     24-sent-page    page html21b-24-sent.html
form     24-sent-one     시도 html21b-24-sent.html -- "sed -n '1,6p'"
form     24-sent-rest    시도 html21b-24-sent.html -- "sed -n '7,24p'"
form     24-sent-table   시도 html21b-24-sent.html -- "sed -n '26,\$p'"
src_html 24-radio-src    html21b-24-radio.html
form     24-radio-out    시도 html21b-24-radio.html
src_html 24-file-src     html21b-24-file.html
form     24-file-out     시도 html21b-24-file.html
src_html 24-demo-src     html21b-24-demo.html
src_html 24-democheck-src html21b-24-democheck.html
dom      24-democheck-out html21b-24-democheck.html "$MARK"

# ------------------------------------------------------------ 하네스 (21-answer 실행 검증)
src_py   form-py         html21b-form.py
src_py   cdp-py          html21b-cdp.py
src_sh   capture-sh      ../capture.sh
```

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다(원본 · 재대조 두 판). 제출 격자·트리거 격자·덮기 블록 모두 **세 판이 한 글자도 같았다**(재대조 결과는 아래 표와 22\~24번의 「실행 검증」). 서버 포트·multipart 경계는 **출력에 안 나오므로** 정규화 규칙이 필요 없었다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`method` × `enctype` 여섯 칸 + `put`·`action` 없음** | 3 | 동작 방식 (1) · A1 |
| **제출 트리거 열여섯 시도 × `submit`·`invalid`·서버** + 갈린 칸 집계 | 3 | 동작 방식 (2) · A2 · A9 |
| **단추 덮기 일곱 시도** | 3 | 동작 방식 (3) · A3 · A10 |
| **폼 소유(`input.form`)와 세 단추의 제출** | 3 | 동작 방식 (4) · A4 |
| **검증 있음 / `novalidate` / `curl`** | 3 | 동작 방식 (5) · A5 |
| **`form` 넷의 접근성 트리** | 3 | 동작 방식 (6) · A6 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 폼 GET + 단추 POST·`text/plain` 의 본문 | **urlencoded 모양** | 명세와 갈린다 — 고쳐지면 바뀐다 |
| 폼 POST·`text/plain` + `formmethod=""` 의 질의 | **깨진 글자 · `%20`** | 명세와 갈린다 |
| 폼 제출 작업이 `toggle` 과 같은 줄에서 순서대로 돈다 | 그렇다 — `뒤늦게 온 요청 = 0` | **하네스 판별의 전제** — 판이 오르면 제일 먼저 확인 |
| 이름 없는 `form` 의 CDP 역할 | `form` | 플랫폼 층과 다를 수 있다 |

**안 돌려 본 것** — ① **`method="dialog"`**(목록의 **47번 주제**). ② **`mailto:`·`data:` 로의 제출** — 명세 표에 칸이 있지만 던지지 않았다. ③ **`accept-charset`·`target`·`formtarget`·`rel`**. ④ **한 조작 안의 이중 제출**(「계획된 이동」을 지우고 다시 넣는 것).

**못 잰 것** — ① **이름 없는 `form` 의 플랫폼 층 노출**(A11). ② **검증 실패 풍선 말** — 헤드리스에는 그 UI 가 없다. ③ **다른 엔진의 (3)** — 비교할 엔진이 없다.

**부적용인 창** — **창 ①(`--dump-dom`) · ③ · ④ · ⑥.** ①이 볼 파서 쪽은 05·17번이 이미 찍었고, 나머지는 제출과 무관하다 — **잴 것이 없다.**

## 용어 풀이

- **질의 / 본문** — GET 이 싣는 자리 / POST 가 싣는 자리.
- **`Content-Type`** — 본문의 형식을 알리는 헤더. GET 제출에는 없다.
- **제출자(submitter)** — 제출을 일으킨 단추. 암묵 제출이 단추 없는 폼에서 나면 `null`.
- **암묵 제출 · 막는 칸** — Enter 제출 · 단추 없는 폼에서 둘 이상이면 Enter 를 무효로 만드는 입력.
- **폼 소유자** — 입력이 속한 폼. `form` 속성 > 가장 가까운 조상.
- **계획된 이동(planned navigation)** — 폼마다 하나씩 두는, 뒤로 미룬 이동 작업.
- **DOM 조작 작업 원천** — 명세가 폼 제출 이동을 넣는 작업 줄. 하네스의 울타리가 여기에 섰다.
- **제5의 상태** — 같은 질문을 다른 창으로 물은 것. 이 주제에서는 「검증이 돌았나」를 `invalid` 이벤트로 물었다.
