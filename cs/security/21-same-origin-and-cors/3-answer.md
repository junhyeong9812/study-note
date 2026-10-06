# security/21-same-origin-and-cors — 정답

## 정답

### 1. 출처와 SOP

- 출처 = `scheme + host + port` 세 요소(RFC 6454, `http`·`https` 같은 URL 기준. `data:` 등은 불투명 출처).
- 셋 다 다르다: `https://a.com`(scheme https, port 443) vs `https://a.com:8443`(port 다름) vs `http://a.com`(scheme·port 다름) — 서로 모두 다른 출처.
- SOP는 한 출처의 스크립트가 다른 출처의 리소스를 **읽는** 것을 기본 차단한다.

### 2. 읽기만 막는다

- 단순 요청에서 CORS가 막는 것은 **읽기**다. 요청 자체는 서버에 도착해 처리된다(쿠키는 `credentials: 'include'`이고 쿠키 정책이 허용할 때만 실린다. `fetch` 기본값은 `same-origin`).
- 서버는 정상으로 `200`과 본문을 만든다. 응답이 돌아오면 브라우저가 `ACAO`를 보고, 없으면 JS에 응답을 주지 않고 `TypeError`를 던진다. 그래서 서버 로그는 `200`, 브라우저는 에러.

### 3. CSRF와의 연결

- 단순 요청의 부수효과(상태 변경)는 응답 읽기와 무관하게 서버에서 일어난다. CSRF는 그 부수효과만 노리므로, 읽기만 막는 CORS로는 못 막는다.

### 4. credentials + 와일드카드

- 거부된다. 브라우저가 `TypeError`를 던진다(콘솔: "must not be the wildcard '*' when the request's credentials mode is 'include'").
- 올바른 설정: 정확한 출처를 `ACAO`로 돌려주고 `Access-Control-Allow-Credentials: true`, 그리고 `Vary: Origin`으로 캐시를 출처별 분리.

### 5. preflight

- 안전 목록 밖(`PUT`, `Content-Type: application/json`)이므로 브라우저가 먼저 `OPTIONS` preflight를 보낸다.
- 서버가 `OPTIONS`를 `405`로 답하면 preflight 실패 → 본 `PUT`은 **서버에 도착하지 않는다**(실험: OPTIONS 405에서 PUT 로그 없음). `ACAO`를 붙여도 상태가 2xx가 아니면 실패한다("It does not have HTTP ok status").

### 6. Origin 반사 + credentials

- 위험: 인증 쿠키가 교차 사이트 요청에 실리는 경우(`SameSite=None` 등), 어느 사이트든 인증된 응답을 읽을 수 있다. 실험에서 다른 사이트 `localhost:C`가 `secret-data`를 받았다.
- 고치는 법: 허용 목록과 **정확히** 비교해 일치할 때만 출처를 돌려준다. 와일드카드·정규식 접두 일치 금지(`bank.example.attacker.com` 통과 사고). 비인증 공개 API만 `*` 허용.

### 7. 사이트 vs 출처, 쓰기 vs 읽기

- SameSite(20번)는 **사이트**(scheme + 등록 가능 도메인, eTLD+1) 기준. SOP/CORS(21번)는 **출처**(scheme+host+port) 기준.
- SameSite/CSRF 방어는 **쓰기(부수효과)**를, SOP/CORS는 **읽기(응답 데이터)**를 막는다. 두 축이 다르다.

### 8. 읽기 차단 vs preflight 실패 구분

- 서버 로그에 요청이 **닿았고** Network에 본 요청 1개뿐이면 단순 요청의 읽기 차단이다(본 요청 처리됨, JS만 못 읽음).
  - 주의: preflight가 성공한 비단순 요청도 본 응답에 `ACAO`가 없으면 서버에 닿은 뒤 읽기에서 막힌다. 이때는 Network에 `OPTIONS`와 본 요청 2개가 보인다(preflight 캐시 적중이면 1개).
- 요청이 서버에 **안 닿았고** Network에 `OPTIONS`가 실패로 보이면 preflight 실패다. 콘솔에 "Response to preflight request doesn't pass access control check".
- 응답 헤더(`ACAO` 값·`ACAC`·`Allow-Methods/Headers`)와 Chrome 콘솔의 구체 사유를 함께 본다(JS `e.message`는 `Failed to fetch`로 뭉뚱그려진다).

### 9. no-cors

- 데이터를 읽을 수 **없다**. `no-cors`로 받은 응답은 opaque(타입 `opaque`, 상태 0, 본문 접근 불가)다.
- CORS를 끄는 게 아니라 응답 읽기를 포기하는 것이다. 요청은 나가지만(단순 요청 제약 안에서) 결과를 못 쓴다.
