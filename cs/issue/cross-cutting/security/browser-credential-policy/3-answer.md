# cs/issue/security/browser-credential-policy — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **쿠키는 요청을 만든 페이지가 누구든 브라우저가 붙인다.** 다른 사이트의 페이지가 우리 서버로 요청을 일으키면(링크 이동·폼 제출), 브라우저는 우리 도메인 쿠키를 자동 첨부하고 서버는 인증된 요청으로 본다.\
   Bearer 헤더는 스크립트가 직접 실어야 하는데, 다른 오리진의 스크립트는 우리 토큰을 읽을 수도 실을 수도 없으므로 CSRF가 성립하지 않는다.\
   즉 헤더를 못 쓰는 제약(EventSource) → 쿠키 인증 → CSRF 방어 필요의 연쇄다.
   > **CSRF(Cross-Site Request Forgery)** — 사용자의 브라우저가 자동으로 싣는 자격을 이용해, 다른 사이트가 사용자 몰래 요청을 보내게 하는 공격.

2. **Lax는 cross-site top-level GET에 쿠키를 보낸다.** 사용자가 다른 사이트의 링크를 눌러 우리 페이지로 이동하는 GET에는 쿠키가 실린다(그래야 로그인 상태로 도착한다).\
   그래서 GET 경로에 부작용이나 민감 응답이 있으면 Lax로는 막히지 않는다. Strict는 cross-site에서 시작한 요청에는 쿠키를 아예 싣지 않는다.\
   단 SameSite의 "site"는 등록 도메인(scheme 포함) 단위다 — 같은 사이트의 다른 서브도메인(오리진)에서 온 요청은 Strict여도 쿠키가 실리므로 Origin 허용목록 검사를 함께 둔다.\
   실제 교정은 쿠키를 `SameSite=Strict`로 바꾸고, 새로 추가할 상태 변경 경로는 GET이 아닌 POST로 두는 것을 불변식으로 명시한 것이다.
   > **SameSite** — 쿠키를 cross-site 요청에 실을지 정하는 속성. `Strict`(안 실음) · `Lax`(top-level GET만) · `None`(항상, Secure 필수).

3. **브라우저가 쿠키를 조용히 버린다.** `Secure` 쿠키는 보안 채널(HTTPS)에서만 저장·전송된다. HTTP 응답이 `Secure` 쿠키를 설정하면 최신 주요 브라우저는 저장하지 않는다(단 `http://localhost`는 보안 컨텍스트로 보고 허용하는 브라우저가 많아, 로컬에서는 재현되지 않을 수 있다).\
   서버 로그에는 로그인 성공·쿠키 발급이 찍히지만, 다음 요청에 쿠키가 없어 "로그인이 유지되지 않음"으로만 보인다. 앱 에러는 없다(개발자 도구의 쿠키 경고 정도).

4. **배포 채널이 HTTPS로 고정돼 있느냐의 차이다.** HTTPS 전용 배포에서는 `secure`를 환경 조건(예: 운영 모드일 때만)에 걸어두면, 조건이 빗나갈 때 평문 전송 쿠키가 생긴다 → **무조건 on**이 맞다.\
   HTTP로 도는 배포(내부 테스트 서버 등)가 실제로 있으면 무조건 on은 그 환경의 로그인을 깨뜨린다 → **명시 env 우선, 없으면 모드 기반 기본값**으로 제어하고, 그 환경은 평문 쿠키라는 트레이드오프를 인지한다.

5. **쿠키 jar는 브라우저의 것이다.** 서버에서 도는 fetch는 브라우저가 아니므로 사용자의 쿠키 저장소가 없다. BFF가 받은 요청의 쿠키를 **명시적으로 꺼내 헤더로 넘겨야** 백엔드가 사용자를 안다.\
   또 서버 측 fetch 응답을 캐시하는 프레임워크(예: 일부 버전의 Next.js App Router는 기본 캐시)에서는 사용자별 인증 응답이 다른 사용자의 요청에 재사용될 수 있다 → 인증이 얽힌 호출은 기본값에 기대지 말고 `cache: "no-store"`를 명시한다.
   > **BFF(Backend For Frontend)** — 브라우저와 백엔드 사이에서 프론트 전용으로 요청을 중계·조립하는 서버 층.

6. **httpOnly의 이점이 사라진다.** httpOnly는 "스크립트가 토큰을 읽지 못함"을 보장해 XSS의 토큰 탈취를 막는다. 같은 토큰을 응답 헤더로도 주면 스크립트가 거기서 읽을 수 있어 보장이 무너진다 → 헤더 토큰을 제거해 한 채널로만.\
   CORS의 `*` 금지도 같은 뿌리다 — credentials(쿠키)는 자동 첨부 자격이라, 그것을 "모든 출처"에 여는 것은 모든 사이트가 사용자 권한으로 응답을 읽게 하는 것이다. 그래서 스펙이 금지하고, 오리진은 화이트리스트로 좁힌다.\
   공통 원리: **자동으로 딸려 가는 자격은 노출 채널을 최소로 좁힌다.**
   > **CORS preflight** — 커스텀 헤더·비단순 메서드 요청 전에 브라우저가 OPTIONS로 허용 여부를 묻는 절차. 허용 헤더 목록에 없는 헤더는 막힌다.

## 문제 구조 (추상화 코드)

### 변형 A — 헤더를 못 쓰는 채널 → 쿠키 인증 → CSRF 노출
① 문제 코드
```ts
// SSE는 커스텀 헤더 불가 → 세션을 쿠키로
res.cookies.set("SESSION", token, { httpOnly: true, sameSite: "lax", secure: isProd });
// GET /private/... 가 cross-site top-level 이동으로도 쿠키를 받아 게이트 통과
```
② 고친 코드
```ts
res.cookies.set("SESSION", token, { httpOnly: true, sameSite: "strict", secure: true });
// 불변식: 상태 변경·민감 경로는 POST (+ Origin 허용목록), GET 금지
```
무엇이 깨졌나: 자동 첨부 자격을 쓰면서 cross-site 요청을 거르지 않았다.\
같은 리뷰의 곁가지: 세션 토큰은 DB에 **해시**로 저장(고엔트로피 토큰이라 빠른 해시로 충분, 비밀번호는 느린 해시), 유휴 만료 추가, 공개 계정 로그인은 연속 실패 시 점증 잠금(잠금 중에는 비싼 해시 비교를 실행하지 않아 CPU 소모 공격도 차단).

### 변형 B — `Secure` 쿠키를 HTTP 배포에서 발급
① 문제 코드
```ts
res.cookies.set("ACCESS", token, { httpOnly: true, secure: process.env.NODE_ENV === "production" });
// HTTP로 도는 운영형 배포 → Secure 쿠키가 버려져 로그인 유지 불가
```
② 고친 코드
```ts
const secure = process.env.COOKIE_SECURE != null
  ? process.env.COOKIE_SECURE === "true"              // 명시 우선
  : process.env.NODE_ENV === "production";            // 미설정 시 폴백
res.cookies.set("ACCESS", token, { httpOnly: true, secure, sameSite, path: "/" });
// HTTP 배포 환경만 false — 평문 전송 트레이드오프를 인지하고 끈다
```
무엇이 깨졌나: 쿠키의 전송 채널 요구(HTTPS)와 실제 배포 채널(HTTP)이 달랐다.

### 변형 C — 서버 측 fetch에 쿠키가 없다고 가정하지 않음 / 인증 응답 캐시
① 문제 코드
```ts
const r = await fetch(`${BACKEND}/me`);                        // 사용자 쿠키 없음, 캐시 가능
res.headers.set("X-Access-Token", token);                      // httpOnly 쿠키와 이중 노출
```
② 고친 코드
```ts
const r = await fetch(`${BACKEND}/me`, {
  headers: { cookie: (await cookies()).toString() },           // 명시 전달
  cache: "no-store",                                           // 사용자별 응답 캐시 금지
});
// 토큰은 httpOnly 쿠키로만 — 응답 헤더 토큰 제거
```
무엇이 깨졌나: 브라우저 전용 동작(쿠키 자동 첨부)을 서버 측 호출에 기대했고, 사용자별 응답을 공유 캐시 대상으로 두었다.

### 변형 D — 커스텀 헤더 preflight 차단
① 문제 코드
```java
cors.setAllowedHeaders(List.of("Content-Type", "Authorization"));   // API 키 헤더 누락 → preflight 실패
```
② 고친 코드
```java
cors.setAllowedOrigins(configuredOrigins);                           // credentials면 * 불가
cors.setAllowedHeaders(List.of("Content-Type", "Authorization", "X-Api-Key"));
cors.setAllowCredentials(true);
// 브라우저가 API 키를 알 필요가 없는 요청(파일 다운로드)은 BFF 스트리밍 프록시로 전달
```
무엇이 깨졌나: 브라우저가 보내는 헤더를 CORS 허용 목록이 몰랐다.\
곁가지: 메뉴 숨김 같은 프론트 게이팅은 UX일 뿐이고, 보안은 서버 인가가 한다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
