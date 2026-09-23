# cs/issue/security/browser-credential-policy — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[쿠키 = 브라우저가 "자동으로" 싣는 자격]

  악성 사이트 페이지 ──(top-level GET / form POST)──▶ 우리 서버
                         └ 브라우저가 우리 쿠키를 자동 첨부 → 인증 통과 = CSRF
  Bearer 헤더 인증은 스크립트가 직접 실어야 함 → 다른 오리진은 못 실음 → CSRF 무관

  SameSite=Lax    : cross-site top-level GET 에는 쿠키 전송  → GET 부작용 경로 노출
  SameSite=Strict : cross-site 요청 전부 쿠키 미전송

[Secure 쿠키]
  HTTPS 응답의 Set-Cookie(Secure)  → 저장·전송
  HTTP 응답의 Set-Cookie(Secure)   → 브라우저가 조용히 버림 → "로그인이 안 유지됨"(에러 없음)

[BFF(서버 측 fetch)]
  브라우저 ──쿠키──▶ BFF ──(쿠키 jar 없음)──▶ 백엔드   ← 명시 전달 필요
  사용자별 응답 캐시 → 다른 요청에 stale 인증 섞임     ← no-store

[교정]
  쿠키 인증 → SameSite=Strict + 부작용은 POST
  Secure    → HTTPS 전용이면 무조건 on / HTTP 배포가 있으면 env로 명시 제어
  BFF       → 쿠키 명시 전달 + cache: no-store + 토큰은 httpOnly 쿠키 한 채널로만
  CORS      → credentials면 오리진 화이트리스트, 커스텀 헤더는 allowedHeaders에 등록
```

## 핵심 문장

- 쿠키는 브라우저가 **자동 첨부**한다 — 그래서 쿠키 인증은 CSRF 방어(SameSite·Origin 검사)가 필요하고, 헤더 인증은 필요 없다.
- `SameSite=Lax`는 cross-site **top-level GET**에 쿠키를 보낸다 → 부작용을 GET에 두지 않거나 Strict.
- `Secure` 쿠키는 **HTTPS에서만** 저장·전송된다. HTTP 배포에서는 에러 없이 버려진다.
- 서버→서버 호출에는 **쿠키 jar가 없다** → 명시 전달. 사용자별 인증 응답은 **캐시 금지**.
- httpOnly의 이점(JS 비노출)은 같은 토큰을 헤더로도 주는 순간 사라진다.
- credentials 요청에 `*` 오리진은 스펙상 금지 — 자동 첨부 자격을 모든 출처에 여는 것이기 때문이다.
