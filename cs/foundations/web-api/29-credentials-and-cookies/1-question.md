# web-api/29 — 자격 증명과 `credentials`: 쿠키가 실리는 조건·와일드카드 금지 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 프리플라이트의 조건은 [28번 주제](../28-cors-simple-and-preflight/1-question.md), 헤더로 넣은 `Cookie` 가 지워지는 것은 [25번 주제](../25-fetch-request-response/1-question.md)의 문항 5가 물었다. 여기는 **다른 출처 요청에 쿠키가 언제 실리고, 실린 응답을 언제 읽나**를 묻는다. CSRF 방어 설계는 [`../../security/`](../../security/) 의 몫이다(절은 아직 없다).
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch 명세 문장이다. 쿠키 속성의 규칙은 **관찰로만** 다룬다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 쿠키 통 준비 (예측)

```js
// wa28b-29-q1.js
// 질문용 — 실행 대상 아님
// 서버 B 를 주소창으로 직접 연다 — http://127.0.0.1:<B>/setcookie 와 http://localhost:<B>/setcookie 두 번.
// 응답 헤더(둘 다 같다):
//   Set-Cookie: lax=1; Path=/; SameSite=Lax
//   Set-Cookie: none=1; Path=/; SameSite=None; Secure
//   Set-Cookie: nosec=1; Path=/; SameSite=None
//   Set-Cookie: plain=1; Path=/
document.cookie;   // 두 자리에서 각각 쿠키 통에 남은 이름은? (http 다 — https 가 아니다)
```

- 두 자리의 쿠키 통에 남는 이름은? 남지 않는 것이 있다면 왜인가?

### 2. 24칸 격자 (예측)

```js
// wa28b-29-q2.js
// 질문용 — 실행 대상 아님
// 페이지는 http://127.0.0.1:<A>. 받는 쪽 둘 — http://127.0.0.1:<B>(같은 사이트의 다른 출처) · http://localhost:<B>(사이트 밖)
// credentials 3 × B 의 응답 헤더 4(허용 없음 · ACAO: * · ACAO: 출처 · ACAO: 출처 + ACAC: true) — GET 한 번씩
const res = await fetch(받는쪽 + "/c29?…", { credentials });   // 그리고 await res.json()
// 24칸마다 ① B 가 받은 Cookie 헤더 ② 페이지가 본문을 읽었나(then) 아니면 catch 인가
// 쿠키가 서버에 간 칸 · 페이지가 읽은 칸 · 「서버는 받았는데 페이지는 못 읽은 칸」은 각각 몇 / 24 ?
```

- 쿠키가 실리는 칸과 읽히는 칸을 갈라라. 받는 쪽 둘에서 실리는 쿠키 이름은 같은가?

### 3. `catch` 로 간 칸의 이유 (예측)

```js
// wa28b-29-q3.js
// 질문용 — 실행 대상 아님
// 문항 2 의 격자에서 catch 로 간 칸들 — 콘솔(CDP Log 도메인)에 찍히는 CORS 이유는 몇 가지 문구로 갈리나?
//   credentials: 'include' + ACAO: *            → ?
//   credentials: 'include' + ACAO: 출처(ACAC 없음) → ?
//   허용 없음(어느 credentials 든)              → ?
```

- 세 경우의 콘솔 문구를 대라. 문구와 칸(응답 헤더) 중 무엇을 근거로 삼아야 하나?

### 4. 서드파티 쿠키를 막는 스위치 (예측)

```js
// wa28b-29-q4.js
// 질문용 — 실행 대상 아님
// 같은 24칸 격자를 두 탭에서 — 그대로 한 번, 그 탭에 서드파티 쿠키를 막는 스위치를 켜고 한 번
//   Network.setCookieControls({ enableThirdPartyCookieRestriction: true, … })
// 두 판이 갈리는 칸은 어느 것들이고 몇 칸인가? 기본 판(스위치를 안 켠 쪽)에서 서드파티 쿠키는 실렸나?
```

- 갈리는 칸과 그 수는? 「출처 + ACAC」 칸은 막은 판에서 읽히나?

### 5. 프리플라이트가 붙는 `include` (예측)

```js
// wa28b-29-q5.js
// 질문용 — 실행 대상 아님
// 같은 사이트의 B 에 credentials: 'include' + 커스텀 헤더 X-A — 프리플라이트가 붙는다
//   가. OPTIONS 답과 본 답 모두 ACAO: 출처 + ACAC: true
//   나. 두 답 모두 ACAO: 출처 (ACAC 없음)
await fetch(B + 길, { credentials: "include", headers: { "X-A": "1" } });
// B 의 서버 로그 — OPTIONS 에 실린 Cookie 는? 가·나 각각 GET 은 B 에 닿나?
```

- OPTIONS 의 `Cookie` 와 가·나의 GET 은?

### 6. `include` 일 때 CORS check 가 보는 것 (왜)

- Fetch 명세의 CORS check 는 어떤 순서로 무엇을 보나? 그 순서로 문항 2의 `ACAO: *` 칸들을 설명하라.

### 7. 「다른 출처」와 「사이트 밖」 (경계)

- `127.0.0.1:<A>` 에서 `127.0.0.1:<B>` 로 보낸 `include` 에 `SameSite=Lax` 쿠키가 실린 이유는? 이 로컬 구성이 배포 환경의 무엇을 흉내 내지 **못하나**?

### 8. `include` + `ACAO: *` 칸의 서버 쪽 (경계)

- `include` + `ACAO: *` 칸에서 서버 로그에는 무엇이 남았나? 그 엔드포인트가 상태를 바꾸는 것이었다면? 브라우저가 대신 막아 주지 **않는** 것은 무엇인가?

### 9. 다른 주제와 잇기 (연결)

- [25번 주제](../25-fetch-request-response/1-question.md)의 문항 5에서 `headers: { Cookie: "evil=1" }` 은 어떻게 됐나? 그것과 이 편의 `credentials` 는 어떻게 이어지나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
