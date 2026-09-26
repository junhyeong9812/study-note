# web-api/31 — `Blob`·`File`·`FileReader` 와 오브젝트 URL: 미리보기·업로드·저장 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 같은 기계의 로컬 서버(A·B)이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [W3C File API](https://w3c.github.io/FileAPI/) 의 `File`·`slice`·read operation·blob URL store·Lifetime of blob URLs·`revokeObjectURL`·접근 제한, [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 `blob` 스킴으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** **메모리는 재지 않았다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 들여다보기 · 미리보기 · 이벤트 순서 · 올리기 · 풀기 전·뒤 · 수명 표 · 내려받기 | ★ **판에 매일 수 있는 칸** — 떠난 뒤의 `then`(bfcache 에 들어갔기 때문) |
| 캡처를 세 판 돌려 **한 글자도 같았다** · UUID 는 찍지 않고 글자 수만 | **못 잰 것** — 메모리 · `slice` 의 복사 여부 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `File` 은 `Blob` 이다 — `slice` 는 `Blob` 을 준다

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '1,2p'
가. File — instanceof File=true · instanceof Blob=true · name=wa28b-31-dot.png · size=73 · type=image/png
   f.slice(0, 8) → Blob size=8 · 바이트 = 89 50 4e 47 0d 0a 1a 0a
(exit 0)
```

**왜 그런가**

- **`instanceof File`·`instanceof Blob` 둘 다 `true`** — 명세의 `interface File : Blob`.
- **`f.slice(0, 8)` 은 `Blob`(size 8)** 이고 바이트는 PNG 서명이다. `name` 이 없는 새 `Blob` 이다. **복사하는지는 재지 않았다.**

### 2. `blob:` + 출처 + 36자 · `readyState=1` 이 먼저

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '3,6p'
나. createObjectURL → 「blob:」 + 이 문서의 출처 + 「/」 로 시작하나=true · 그 뒤 글자 수=36
   <img src=그 URL> → load · 3×2
다. readAsDataURL → (readAsDataURL 이 돌아옴 · readyState=1) → loadstart → progress → load → loadend · 결과 앞부분 = data:image/png;base64, · 길이 122
   <img src=데이터 URL> → load · 3×2
(exit 0)
```

**왜 그런가**

- **오브젝트 URL 은 `blob:<이 문서의 출처>/<UUID 36자>`**(명세의 generate a new blob URL) — `<img>` 가 3×2 로 읽었다.
- ★★ **`readAsDataURL` 이 돌아온 직후 `readyState=1`, 그 뒤에 `loadstart → progress → load → loadend`** — `loadstart` 는 태스크로 큐에 들어간다(명세). 73바이트에도 `progress` 가 한 번 났다(구현 관찰 — 명세는 「대략 50ms 마다」).
- **결과는 `data:image/png;base64,` 로 시작하는 122글자** — 바이트를 글자로 바꾼 사본이다.

### 3. multipart(`filename`·`image/png`) 와 `image/png` 73바이트

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^--- 서버/,$p'
--- 서버 로그 ---
A POST /echo?id=u1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 259바이트
    서버 파싱 → 칸 1개 · f[filename=wa28b-31-dot.png][image/png]=<73바이트>
A POST /echo?id=u2&save=up.png  Content-Type=image/png · 본문 73바이트
    서버 파싱 → (Content-Type 으로 고를 파서 없음)
(exit 0)
```

**왜 그런가**

- **`FormData` 쪽** — 파일 칸 `filename=wa28b-31-dot.png`(`File.name`) · `image/png`(`File.type`) · 값 73바이트.
- **`body: f` 쪽** — `Content-Type=image/png` · 73바이트 — 본문이 파일 바이트 그 자체다. 서버가 받아 저장한 바이트는 **원본과 같았다**(A6 의 둘째 줄).

### 4. 풀면 `TypeError` · `<img>` 는 `error` · 잘못 풀어도 조용하다

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '8,11p'
마. 풀기 전 fetch(URL) → then · status 200 · 73바이트
   revokeObjectURL 뒤 fetch(URL) → catch · TypeError 「Failed to fetch」
   revokeObjectURL 뒤 <img src=URL> → error 이벤트
   같은 URL 을 또 풀기 · 없는 URL 풀기 · blob 아닌 글자 풀기 → 예외 없음
(exit 0)
```

**왜 그런가**

- **풀기 전 `status 200 · 73바이트` → 푼 뒤 `TypeError 「Failed to fetch」`**, `<img>` 는 `error`. 명세 — 풀린 뒤의 역참조는 network error(Fetch 의 `blob` 스킴: 항목이 null 이면).
- ★ **또 풀기 · 없는 URL · `blob` 아닌 글자 → 예외 없음** — 명세의 「조용히 끝난다」. 풀렸는지는 읽어 봐야 안다.

### 5. 같은 출처는 읽고, 다른 출처는 못 읽고, 떠나도 읽히고, 닫으면 끊긴다

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^다른 탭(같은/,/떠난 뒤, 다른 탭(A) → catch/p'
다른 탭(같은 출처 A) → then · status 200 · 73바이트
다른 탭(다른 출처 B) → catch · TypeError 「Failed to fetch」
첫 탭이 다른 문서로 떠난 뒤, 다른 탭(A) → then · status 200 · 73바이트
첫 탭에서 뒤로 → 스크립트 상태(window.__남긴URL)가 남아 있나 = True
첫 탭을 닫은 뒤, 다른 탭(A) → catch · TypeError 「Failed to fetch」
넷째 탭(unload 리스너를 단 문서)이 만든 URL — 떠나기 전, 다른 탭(A) → then · status 200 · 1바이트
                                             떠난 뒤, 다른 탭(A) → catch · TypeError 「Failed to fetch」
(exit 0)
```

**왜 그런가**

- ① **같은 출처 A 의 다른 탭 → 읽힌다**(blob URL store 는 브라우저에 하나). ② **다른 출처 B → `TypeError`**(storage key 접근 제한).
- ★★★ ③ **첫 탭이 떠난 뒤에도 읽힌다** — 그리고 **뒤로 가니 스크립트 상태가 남아 있었다**(`True`) — 떠난 문서가 **bfcache 에 들어가 파괴되지 않았다.** ④ **닫은 뒤 → `TypeError`**.
- ★★ ⑤ **unload 리스너를 단 문서의 URL 은 떠나기 전 읽히고 떠난 뒤 `TypeError`** — bfcache 에 못 들어가 떠나는 순간 파괴됐다(24편 (4)).

### 6. 이름은 `download` 그대로 · 73바이트 · 같은 바이트

**출력**

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^내려받기/p;/^서버가/p'
내려받기 → 제안된 이름 wa28b-31-saved.png · 떨어진 파일 73바이트 · 원본과 바이트가 같나 = True
서버가 body: file 로 받아 저장한 바이트가 원본과 같나 = True
(exit 0)
```

- **제안된 이름 `wa28b-31-saved.png`**(`download` 속성) · **73바이트** · **원본과 바이트가 같다.** 서버를 안 거친다.

### 7. 문서가 파괴될 때 지운다 — bfcache 는 파괴가 아니다

- File API 의 **Lifetime of blob URLs** — **unloading document cleanup steps** 에서 **그 문서의 환경이 만든 항목**을 장부에서 지운다. 즉 URL 은 **만든 문서의 수명**에 묶인다.
- **③은 떠난 문서가 bfcache 에 들어갔다** — 뒤로 가니 같은 스크립트 상태가 되살아났으므로 **파괴되지 않았다.** 그래서 URL 도 살아 있었다. **⑤는 `unload` 리스너 때문에 bfcache 에 못 들어가** 떠나는 순간 파괴됐고 URL 도 끊겼다. **가른 것은 「떠났나」가 아니라 「파괴됐나」다**(bfcache 절의 명세 문장은 열지 않았다 — 관찰로 적는다).

### 8. 관찰한 것은 「URL 이 아직 읽힌다」까지

- **관찰한 것** — 풀지 않은 URL 은 **만든 문서가 파괴될 때까지**(bfcache 에 있는 동안까지) **같은 출처의 어느 문서에서든 읽혔다.** 명세의 blob URL entry 는 **객체를 들고 있다** — 그러니 그 `Blob` 은 **URL 로 닿을 수 있는 상태**로 남는다. 단일 페이지 앱에서 미리보기를 바꿀 때마다 새 URL 을 만들면 **읽히는 URL 이 그만큼 쌓인다.**
- **관찰하지 않은 것** — **얼마나 자리를 차지하나 · 실제로 해제되나.** 이 편은 「메모리가 샌다」를 주장하지 않는다(가이드 규칙 4). 힙·GC 원리는 [`../../memory-management/`](../../memory-management/README.md) 의 몫이다.

### 9. 이벤트 대 프라미스 · 번호표 대 사본

- **`FileReader` 와 `blob.text()` 는 같은 `"가나"`** 를 줬다(2-summary 의 (1) 바). `FileReader` 는 **이벤트**(`readyState` · `load`), `text()` 는 **프라미스** — 새 코드는 프라미스 쪽이 짧다.
- **오브젝트 URL 은 번호표**(풀어야 끊긴다 · **다른 출처는 못 읽는다**), **데이터 URL 은 바이트를 글자로 바꾼 사본**(73바이트 → 122글자 · 문자열이라 옮길 수 있다). **다른 출처에 넘겨야 하면 사본(데이터 URL)이나 바이트**다.

### 10. 다른 주제와 잇기

- **30편 문항 3** — 이름 없이 넣은 `Blob` 은 **`filename="blob"`** · `application/octet-stream` 이었다. 이 편의 `fd.append("f", f)` 는 **`File` 이라 `filename="wa28b-31-dot.png"`** · `image/png` — **`File.name`·`File.type` 이 그대로** 원문에 적혔다.
- **도구가 못 보는 것** — ① **메모리**(풀지 않은 URL 이 얼마나 붙드나 — 재지 않았다) ② **`Blob.slice` 가 복사하나**(새 `Blob` 과 바이트까지만 봤다).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B). **엔진은 Chrome 하나다.**

★ **하네스** — [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1). `blob` 모드는 파일 입력에 CDP `DOM.setFileInputFiles` 로 PNG 를 넣고 `__끝()` → `Browser.setDownloadBehavior` 로 내려받기 → 다른 탭 둘 · 첫 탭을 떠나게 하고 뒤로 · 닫기 · unload 리스너를 단 넷째 탭 순으로 돈다.\
★ **파일** — `wa28b-31-dot.png` 는 파이썬 `zlib` 으로 만든 73바이트 PNG(3×2 빨강)다.

```sh
# wa28b-31-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 들여다보기 · 미리보기 · 풀기 전·뒤 | 캡처 3판 | 동작 방식 (1)·(3) · A1 · A2 · A4 · A9 |
| 올리기 둘 | 캡처 3판 | 동작 방식 (2) · A3 |
| 내려받기 | 캡처 3판 | 동작 방식 (4) · A6 |
| URL 수명 표 | 캡처 3판 | 동작 방식 (5) · A5 · A7 · A8 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 떠난 문서의 URL | 읽힘(bfcache) | bfcache 에 들어가느냐는 구현·조건 |
| 작은 파일의 `progress` | 한 번 남 | 명세 문장은 「대략 50ms 마다」 |
| `<a download>` 저장 | 이름·바이트 그대로 | CDP 로 허용한 내려받기 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 워커가 만든 URL · `MediaSource`. ③ 최상위 문서로 `blob:` 열기.
