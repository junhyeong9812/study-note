# web-api/30 — 요청 본문 만들기: `FormData`·`URLSearchParams`·JSON 과 `Content-Type` 자동 설정 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 같은 기계의 로컬 서버 A 이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 extract a body · Request 생성자, [WHATWG HTML](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html) 의 create an entry · constructing the entry list · multipart/form-data 인코딩 알고리즘으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 격자 14칸 · 원문 · 바이트 수 · 파일 칸 · 폼 대 `fetch` · 파이썬 | ★ **boundary 뒤 16자 · `requests` 의 32자** — 요청마다 새로 만든다. **하네스가 출력 전에 가렸다** |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 서버 프레임워크의 관용 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 깨진 본문 1 / 7 — `FormData` 하나

**출력**

```text
$ python3 wa28b-net.py page wa28b-30-grid.html | sed -n '1,16p'
본문             직접 쓴 Content-Type                서버가 받은 Content-Type                                    서버 파싱
FormData         (안 씀)                             multipart/form-data; boundary=----WebKitFormBoundary<16자>  칸 2개 · a=1 · b=한
FormData         multipart/form-data                 multipart/form-data                                         boundary 가 Content-Type 에 없다 — 가를 수 없다
URLSearchParams  (안 씀)                             application/x-www-form-urlencoded;charset=UTF-8             칸 [["a", "1"], ["b", "한"]]
URLSearchParams  application/x-www-form-urlencoded   application/x-www-form-urlencoded                           칸 [["a", "1"], ["b", "한"]]
문자열           (안 씀)                             text/plain;charset=UTF-8                                    글 「a=1」
문자열           text/plain                          text/plain                                                  글 「a=1」
Blob(type 있음)  (안 씀)                             application/json                                            JSON {"a": 1}
Blob(type 있음)  application/json                    application/json                                            JSON {"a": 1}
Blob(type 없음)  (안 씀)                             (없음)                                                      (Content-Type 으로 고를 파서 없음)
Blob(type 없음)  application/json                    application/json                                            JSON {"a": 1}
JSON.stringify   (안 씀)                             text/plain;charset=UTF-8                                    글 「{"a":1}」
JSON.stringify   application/json                    application/json                                            JSON {"a": 1}
ArrayBuffer      (안 씀)                             (없음)                                                      (Content-Type 으로 고를 파서 없음)
ArrayBuffer      application/json                    application/json                                            JSON {"a": 1}
직접 써서 서버가 받은 Content-Type 이 바뀐 본문 = 6 / 7 · 직접 써서 서버 파싱이 깨진 본문 = 1 / 7
(exit 0)
```

**왜 그런가**

- **안 씀** — `FormData` → `multipart/form-data; boundary=…` · `URLSearchParams` → `…urlencoded;charset=UTF-8` · 문자열과 **`JSON.stringify` → `text/plain;charset=UTF-8`** · `type` 있는 `Blob` → 그 값 · **타입 없는 `Blob`·`ArrayBuffer` → 없음.**
- ★★★ **「씀」으로 파싱이 깨지는 것은 `FormData` 하나** — boundary 가 빠진다. 나머지 여섯 중 다섯은 받은 값만 바뀌었다(charset 이 빠지거나 없던 것이 생김) — `JSON.stringify`·타입 없는 `Blob`·`ArrayBuffer` 세 칸은 **쓰니까 비로소 JSON 으로 읽혔다.**

### 2. 원문은 같다 — `Content-Type` 에서 boundary 만 빠졌다

**출력**

```text
$ python3 wa28b-net.py page wa28b-30-twice.html
보냈다 — 둘
--- 서버 로그 ---
A POST /echo?id=f1&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n1\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 1개 · a=1
A POST /echo?id=f2&raw=1  Content-Type=multipart/form-data · 본문 133바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n1\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → boundary 가 Content-Type 에 없다 — 가를 수 없다
(exit 0)
```

**왜 그런가**

- ★★★ **두 원문이 한 글자도 같다(133바이트)** — 본문은 여전히 boundary 로 쌌다. **직접 쓴 쪽의 `Content-Type` 은 `multipart/form-data` 뿐**이라 서버는 **가를 수 없다.**
- 브라우저 쪽에는 **예외도 경고도 없다** — 요청은 `200` 이다.

### 3. `Blob` 은 `File` 이 된다 — 이름 없으면 `blob`

**출력**

```text
$ python3 wa28b-net.py page wa28b-30-file.html
FormData.get → a:string · b:File(name=blob, type="") · c:File(name=r.csv, type="text/csv") · d:File(name=n.txt, type="text/plain") · e:File(name=m.bin, type="")
--- 서버 로그 ---
A POST /echo?id=f3&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 692바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n글\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="b"; filename="blob"\r\nContent-Type: application/octet-stream\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="c"; filename="r.csv"\r\nContent-Type: text/csv\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="d"; filename="n.txt"\r\nContent-Type: text/plain\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="e"; filename="m.bin"\r\nContent-Type: application/octet-stream\r\n\r\nx\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 5개 · a=글 · b[filename=blob][application/octet-stream]=<1바이트> · c[filename=r.csv][text/csv]=x · d[filename=n.txt][text/plain]=x · e[filename=m.bin][application/octet-stream]=<1바이트>
(exit 0)
```

**왜 그런가**

- **`f.get("b")` 는 `File(name=blob, type="")`** — 명세의 create an entry(`File` 이 아닌 `Blob` → 이름 `"blob"` 인 `File`).
- **파일 칸의 `Content-Type` 은 `type`**, 비었으면 **`application/octet-stream`**(이 판의 관찰). **문자열 칸에는 `Content-Type` 줄이 없다**(명세).

### 4. boundary 만 가리면 한 글자도 같다

**출력**

```text
$ python3 wa28b-net.py form wa28b-30-form.html wa28b-30-note.txt
fetch 로 보냈다 — 이제 폼 제출
폼 제출 뒤 주소 = http://127.0.0.1:<A>/echo?id=form&raw=1
두 원문(경계 뒤 16자를 가린 것)이 한 글자도 같나 = True
--- 서버 로그 ---
A POST /echo?id=fetch&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 392바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="title"\r\n\r\n메모\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="ok"\r\n\r\nyes\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="f"; filename="wa28b-30-note.txt"\r\nContent-Type: text/plain\r\n\r\n메모 파일\n\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 3개 · title=메모 · ok=yes · f[filename=wa28b-30-note.txt][text/plain]=메모 파일
A POST /echo?id=form&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 392바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="title"\r\n\r\n메모\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="ok"\r\n\r\nyes\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="f"; filename="wa28b-30-note.txt"\r\nContent-Type: text/plain\r\n\r\n메모 파일\n\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 3개 · title=메모 · ok=yes · f[filename=wa28b-30-note.txt][text/plain]=메모 파일
(exit 0)
```

**왜 그런가**

- ★★★ **`True` — 392바이트 두 원문이 같다.** `new FormData(form)` 은 폼 제출과 **같은 entry list · 같은 인코딩**이다(XHR 의 `FormData(form)` 생성자가 constructing the entry list 를 부른다).
- **체크 안 된 `no` 는 둘 다 없다** · 파일 칸은 `filename="wa28b-30-note.txt"` · `text/plain` · 내용의 `\n` 그대로.

### 5. `urllib` 는 폼 타입을 붙이고, `requests` 도 직접 쓰면 깨진다

**출력**

```text
$ python3 wa28b-net.py py
urlopen(urlencode 한 바이트) → status 200 · 보낸 Content-Type = application/x-www-form-urlencoded
urlopen(JSON 바이트) → status 200 · 보낸 Content-Type = application/x-www-form-urlencoded
urlopen(JSON 바이트 + Content-Type 지정) → status 200 · 보낸 Content-Type = application/json
requests.post(files= 만) → status 200 · 보낸 Content-Type = multipart/form-data; boundary=<32자>
requests.post(files= + Content-Type: multipart/form-data 지정) → status 200 · 보낸 Content-Type = multipart/form-data
--- 서버 로그 ---
A POST /echo?id=py  Content-Type=application/x-www-form-urlencoded · 본문 15바이트
    서버 파싱 → 칸 [["a", "1"], ["b", "한"]]
A POST /echo?id=py  Content-Type=application/x-www-form-urlencoded · 본문 8바이트
    서버 파싱 → 칸 [["{\"a\": 1}", ""]]
A POST /echo?id=py  Content-Type=application/json · 본문 8바이트
    서버 파싱 → JSON {"a": 1}
A POST /echo?id=py  Content-Type=multipart/form-data; boundary=<32자> · 본문 248바이트
    서버 파싱 → 칸 2개 · a=1 · f[filename=n.txt][text/plain]=x
A POST /echo?id=py  Content-Type=multipart/form-data · 본문 248바이트
    서버 파싱 → boundary 가 Content-Type 에 없다 — 가를 수 없다
(exit 0)
```

**왜 그런가**

- ★★ **`urllib` 는 JSON 바이트에도 `application/x-www-form-urlencoded`** — 서버가 JSON 을 폼으로 읽었다(`{"a": 1}` 이 **이름**). 브라우저의 자동 값과 다르다.
- ★★ **`requests` 도 `Content-Type: multipart/form-data` 를 직접 주면 boundary 가 빠져 서버가 못 가른다** — 같은 사고가 언어를 안 가린다.

### 6. 「있으면 안 붙인다」 + 「boundary 는 본문을 만드는 쪽만 안다」

- **Fetch 의 extract a body** 는 `FormData` 의 타입을 **`multipart/form-data; boundary=` + 인코딩 알고리즘이 만든 boundary** 로 정한다. **Request 생성자**는 그 타입을 **headers 에 `Content-Type` 이 없을 때만** 붙인다.
- 직접 쓰면 두 번째 문장 때문에 자동 값이 안 붙는다 — 그런데 **본문은 extract a body 가 그대로 인코딩한다**(boundary 로). 그래서 **본문은 멀쩡하고 송장만 틀린** 요청이 된다. 그 boundary 는 **요청마다 새로 만들어지므로** 스크립트가 미리 알 수 없다.

### 7. 「브라우저가 붙일 줄 아는 값이면 맡기고, 모르는 값이면 쓴다」

- **`FormData`** — 브라우저가 **boundary 까지** 안다 → **맡긴다.** **JSON** — 브라우저는 그것이 문자열인 줄만 안다(`text/plain`) → **쓴다.**
- **타입 없는 `Blob`·`ArrayBuffer`** — 브라우저가 **아무것도 안 붙인다** → **쓴다**((1)에서 쓰니까 JSON 으로 읽혔다).

### 8. 클라이언트가 정해 원문에 적어 보낸다

- **`filename` 은 원문의 `Content-Disposition` 에 클라이언트가 적은 글자**다 — `Blob` 이면 `"blob"`, `File` 이면 그 `name`((3)), 폼이면 사용자가 고른 파일 이름((4)). 파이썬 `requests` 도 제 마음대로 적는다((5) — `n.txt`).
- 그래서 서버는 **신뢰할 수 없는 입력**으로 다룬다 — 경로로 쓰지 않는다. (명세는 `"`·줄바꿈을 `%22`·`%0A` 로 바꾸는 것까지만 정한다.)

### 9. 다른 주제와 잇기

- **28편 문항 1** — `JSON.stringify` 만 넘긴 `POST` 는 `text/plain;charset=UTF-8` 이라 **「`POST` · `text/plain` · 헤더 없음」 — OPTIONS 가 안 붙는 칸**이다. 서버가 `Content-Type` 을 안 보고 JSON 으로 파싱하면 **프리플라이트 없는 다른 출처 JSON 요청**을 받는다 — 그리고 25편처럼 **처리된 뒤 읽기만** 막힌다.
- **도구가 못 보는 것** — ① **서버 프레임워크의 관용**(파서를 직접 짰다 — boundary 를 짐작하는 파서가 있는지는 모른다) ② **업로드 진행률 · 큰 파일**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A) · `urllib.request` · 서드파티 `requests`(대비). **엔진은 Chrome 하나다.**

★ **하네스** — [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1). `/echo` 는 받은 `Content-Type`·원문·**직접 짠 multipart 파서**의 결과를 적고, **boundary 는 로그에 적기 전에 가린다.** `form` 모드는 파일 입력에 CDP `DOM.setFileInputFiles` 로 파일을 넣고, `fetch` 뒤에 폼을 `requestSubmit()` 시킨다.

```sh
# wa28b-30-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa28b-net.py page wa28b-30-grid.html
python3 wa28b-net.py page wa28b-30-twice.html
python3 wa28b-net.py page wa28b-30-file.html
python3 wa28b-net.py form wa28b-30-form.html wa28b-30-note.txt
python3 wa28b-net.py py
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 자동 `Content-Type` 격자 | 캡처 3판 | 동작 방식 (1) · A1 · A7 |
| 같은 `FormData` 두 번 | 캡처 3판 | 동작 방식 (2) · A2 · A6 |
| 파일 칸 | 캡처 3판 | 동작 방식 (3) · A3 · A8 |
| 폼 대 `fetch` | 캡처 3판 | 동작 방식 (4) · A4 |
| 파이썬 대비 | 캡처 3판 | 동작 방식 (5) · A5 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| boundary 의 모양 | `----WebKitFormBoundary` + 16자 | Chrome 의 글자 |
| 빈 `type` 파일 칸 | `application/octet-stream` | 이 판의 관찰 |
| `urllib` 의 기본 `Content-Type` | `application/x-www-form-urlencoded` | 라이브러리 설계 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `text/plain` 폼 인코딩 · 비 UTF-8 폼. ③ `filename` 에 `"`·줄바꿈.
