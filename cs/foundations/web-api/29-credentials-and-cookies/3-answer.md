# web-api/29 — 자격 증명과 `credentials`: 쿠키가 실리는 조건·와일드카드 금지 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버 두 대(A·B)는 같은 기계의 로컬 서버이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 credentials mode · includeCredentials · CORS check · CORS protocol and credentials 절로 접지했다. **쿠키 속성(`SameSite`·`Secure`)과 서드파티 쿠키는 이 판의 관찰**이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 쿠키 통 · 격자 24칸 · 콘솔 · 서버 로그 · 프리플라이트 | ★ **판·설정에 매인 칸** — 사이트 밖 `include` 네 칸의 `none=1`(서드파티 쿠키 정책) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 진짜 등록 도메인 · https |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `lax`·`none`·`plain` 셋 — `nosec` 은 안 남는다

**출력**

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '1,2p'
B 를 127.0.0.1 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
B 를 localhost 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
(exit 0)
```

**왜 그런가**

- **`SameSite=None` 에 `Secure` 가 없는 `nosec` 은 저장되지 않았다** — 예외도 경고도 페이지에 없다.
- ★ **`Secure` 인 `none` 은 http 인데도 저장됐다** — 두 이름 모두. Chrome 이 루프백 주소를 안전한 곳으로 친다는 관찰이다(쿠키 명세는 열지 않았다).

### 2. 실린 칸 8 / 24 · 읽힌 칸 14 / 24 · 받았는데 못 읽은 칸 6 / 24

**출력**

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '3,28p'
받는 쪽     credentials  B 의 응답          B 가 받은 쿠키            페이지
같은 사이트 omit         허용 없음          (쿠키 없음)               catch TypeError
같은 사이트 omit         ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 omit         ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 omit         ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  허용 없음          (쿠키 없음)               catch TypeError
같은 사이트 same-origin  ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 include      허용 없음          lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: *            lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: 출처         lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: 출처 + ACAC  lax=1 none=1 plain=1      읽음 lax=1 none=1 plain=1
사이트 밖   omit         허용 없음          (쿠키 없음)               catch TypeError
사이트 밖   omit         ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   omit         ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   omit         ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  허용 없음          (쿠키 없음)               catch TypeError
사이트 밖   same-origin  ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   include      허용 없음          none=1                    catch TypeError
사이트 밖   include      ACAO: *            none=1                    catch TypeError
사이트 밖   include      ACAO: 출처         none=1                    catch TypeError
사이트 밖   include      ACAO: 출처 + ACAC  none=1                    읽음 none=1
쿠키가 서버에 간 칸 = 8 / 24 · 페이지가 읽은 칸 = 14 / 24 · 서버는 쿠키를 받았는데 페이지는 못 읽은 칸 = 6 / 24
(exit 0)
```

**왜 그런가**

- ★★★ **쿠키는 `include` 에만 실렸다** — 기본 `same-origin` 은 다른 출처에 안 싣는다(명세의 includeCredentials).
- ★★★ **`include` 여덟 칸 중 읽힌 것은 「출처 + ACAC」 둘뿐** — 허용 없음·`*`·출처만은 **쿠키가 서버에 갔는데 페이지는 `catch`** 다.
- ★★ **받는 쪽마다 실린 쿠키가 다르다** — 같은 사이트(`127.0.0.1:<B>`)는 **`lax none plain`**, 사이트 밖(`localhost:<B>`)은 **`none` 하나.** 안 적은 `plain` 은 `Lax` 처럼 굴었다(관찰).

### 3. 세 문구 — 칸이 근거이고 문구는 확인용

**출력**

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '/^--- 콘솔/,/^--- 서버/{/^--- 서버/!p}'
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k0&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k4&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k8&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k9&acao=star' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k10&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k12&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k16&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k20&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k21&acao=star' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k22&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
(exit 0)
```

- ① **허용 없음** → 「No 'Access-Control-Allow-Origin' header is present …」 ② **`include` + `*`** → 「… must not be the wildcard '*' when the request's credentials mode is 'include'.」 ③ **`include` + 출처(ACAC 없음)** → 「The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' …」.
- ★ **근거는 칸(응답 헤더)이다** — 문구는 Chrome 의 글자다(가이드 규칙 27). 이 판에서는 문구가 칸과 맞았다.

### 4. 사이트 밖 `include` 네 칸만 바뀐다

**출력**

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html compare
그대로 사이트 밖   include      허용 없음          none=1                    catch TypeError
막음   사이트 밖   include      허용 없음          (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: *            none=1                    catch TypeError
막음   사이트 밖   include      ACAO: *            (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: 출처         none=1                    catch TypeError
막음   사이트 밖   include      ACAO: 출처         (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: 출처 + ACAC  none=1                    읽음 none=1
막음   사이트 밖   include      ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
서드파티 쿠키를 막자 바뀐 칸 = 4 / 24
(exit 0)
```

- ★★ **바뀐 칸 4 / 24 — 전부 사이트 밖 · `include`.** 막으면 `none=1` 도 안 실린다. 같은 사이트 칸은 그대로다.
- ★★ **기본 판에서는 서드파티 쿠키가 실렸다** — 이 네 칸이 **판·설정에 매인 칸**이다.
- ★ **「출처 + ACAC」 칸은 막아도 읽힌다** — 쿠키만 빠진다. CORS 통과와 쿠키 실림은 따로다.

### 5. OPTIONS 에는 쿠키가 없다 · ACAC 가 없으면 GET 이 안 간다

**출력**

```text
$ python3 wa28b-net.py cookie wa28b-29-preflight.html
B 를 127.0.0.1 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
B 를 localhost 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
가. 두 답 모두 ACAO: 출처 + ACAC: true → 읽음 lax=1 none=1 plain=1
나. 두 답 모두 ACAO: 출처 (ACAC 없음) → catch TypeError
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=p2&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /c29?id=p1&acao=origin&acac=1  Cookie=(쿠키 없음)
B GET /c29?id=p1&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B OPTIONS /c29?id=p2&acao=origin  Cookie=(쿠키 없음)
(exit 0)
```

- ★★ **OPTIONS 두 줄 모두 `Cookie=(쿠키 없음)`** — 명세 「CORS-preflight request never includes credentials」.
- ★★ **나는 GET 이 서버에 안 왔다** — 프리플라이트 답에도 `Allow-Credentials: true` 가 필요하다. 쿠키째 요청이 안 갔다(28편 (4)와 같은 모양).

### 6. `include` 가 아닐 때만 `*` 로 성공하고, 아니면 출처가 같아야 한다

- Fetch 의 CORS check — ① `Access-Control-Allow-Origin` 이 없으면 실패 ② **credentials mode 가 `include` 가 아니고 값이 `*` 면 성공** ③ 값이 **요청 출처의 직렬화와 같지 않으면 실패** ④ `include` 가 아니면 성공 ⑤ `Access-Control-Allow-Credentials` 가 **`true` 면 성공**, 아니면 실패.
- 그래서 **`include` + `*`** 는 ②를 못 타고 ③에서 `*` ≠ 출처로 실패한다. **`omit`·`same-origin`** 은 ②에서 끝난다. 명세의 허용·불허 조합 표도 같은 것을 적는다.

### 7. 포트만 다르면 같은 사이트다 — 로컬은 교차 사이트를 흉내 내지 못한다

- **`127.0.0.1:<A>` 와 `127.0.0.1:<B>` 는 다른 출처지만 같은 사이트**로 다뤄졌다 — 그래서 `Lax` 도 실렸다(격자 문항 2). **호스트 이름이 다른 `localhost:<B>`** 에서야 사이트 밖이 됐다.
- ★ 그래서 **「로컬에서 포트만 바꿔 API 를 띄운」 구성은 배포의 교차 사이트(다른 등록 도메인)를 흉내 내지 못한다** — `Lax` 쿠키와 서드파티 쿠키 정책이 **다르게** 걸린다.

### 8. 서버는 쿠키째 받았다 — 브라우저는 처리를 막지 않는다

- **`k9`(같은 사이트 · `include` · `*`) 줄에 `Cookie=lax=1 none=1 plain=1`** — 페이지는 `catch` 였다(2-summary 의 (4)).
- 상태를 바꾸는 엔드포인트였다면 **그 일은 일어났다.** 브라우저가 대신 막아 주는 것은 **응답을 보여 주는 것**과 **`Lax` 쿠키를 사이트 밖에 싣는 것** · **거부된 프리플라이트 뒤의 본 요청**뿐이다. **단순 요청의 처리 자체는 막지 않는다** — 서버의 `Origin` 검사·토큰이 필요하다(방어 설계는 [`../../security/`](../../security/) 의 몫 — 절은 아직 없다).

### 9. 다른 주제와 잇기

- **25편 문항 5** — `Cookie: evil=1` 은 **예외 없이 지워지고 쿠키 통의 `jar=1` 이 갔다.** 쿠키는 **헤더로 넣는 것이 아니다.** 스크립트가 고를 수 있는 것은 **싣나 안 싣나(`credentials`)** 뿐이고, 무엇이 실리는지는 쿠키 통과 쿠키 속성이 정한다 — 이 편의 격자가 그 「싣나」의 칸들이다.
- **도구가 못 보는 것** — ① **진짜 다른 등록 도메인**(루프백의 `127.0.0.1` 대 `localhost` 로 흉내 냈다) ② **https**(전부 http — `Secure` 가 통한 것은 루프백이라서일 수 있다).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B — IPv4·IPv6). **엔진은 Chrome 하나다.**

★ **하네스** — [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1). `cookie` 모드는 먼저 B 를 두 이름으로 **직접** 열어 쿠키를 받게 한 뒤 A 에서 페이지를 연다. `compare` 는 같은 쿠키 통으로 두 탭을 돌려 갈린 줄만 찍는다.\
★ **「실렸나」는 서버에게 묻는다**(`/note`) — 페이지는 나가는 `Cookie` 를 못 본다.

```sh
# wa28b-29-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa28b-net.py cookie wa28b-29-grid.html
python3 wa28b-net.py cookie wa28b-29-grid.html compare
python3 wa28b-net.py cookie wa28b-29-preflight.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 쿠키 통 준비 | 캡처 3판 | 동작 방식 (1) · A1 |
| 쿠키 실림 격자 + 콘솔 + 서버 로그 | 캡처 3판 | 동작 방식 (2)\~(4) · A2 · A3 · A8 |
| 서드파티 쿠키 차단 대조 | 캡처 3판 | 동작 방식 (5) · A4 |
| 프리플라이트 + `include` | 캡처 3판 | 동작 방식 (6) · A5 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 기본 프로필의 서드파티 쿠키 | 실림 | 브라우저 정책 — 판마다 바뀔 수 있다 |
| http 루프백의 `Secure` 쿠키 | 저장·전송됨 | Chrome 의 「안전한 곳」 판정 |
| `SameSite` 안 적음 | `Lax` 처럼 | 쿠키 명세 초안·구현의 기본값 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `Strict`·`Partitioned`·HttpOnly. ③ 다른 출처 응답의 `Set-Cookie` 저장.
