# issue/network/proxy-passthrough — 정답

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **원형 보존 세 가지.** 투명 프록시(BFF)는 상류와 클라이언트 사이에서 **종단간 의미를 그대로 통과**시켜야 한다. (a) **스트림 타이밍** — 조각이 오는 대로 흘려야 함, 깨지면 타자 효과가 죽음(스트리밍 무효). (b) **상태코드** — 상류 status를 그대로 반환, 깨지면 오류의 의미가 사라져 클라이언트가 상태코드로 분기 못 함. (c) **상태성 헤더(쿠키)** — `set-cookie`/`cookie` 양방향 전달, 깨지면 세션이 안 서서 매 요청이 새 사용자. 셋은 각각 "속도·의미·정체성"을 담당한다.
   > **BFF(Backend For Frontend)** — 프론트가 백엔드를 직접 못 볼 때 그 사이에서 요청을 대신 중계하는 얇은 프록시 계층.

2. **버퍼링이 타자 효과를 죽이는 이유.** 스트리밍의 이점은 "응답이 완성되기 전에 **첫 조각을 빨리** 보내 사용자가 곧바로 글자가 늘어나는 걸 보게" 하는 것이다. 프록시가 버퍼링하면 조각들을 **다 모을 때까지 붙들었다가 한꺼번에** 내보내므로, 사용자 관점에선 "몇 초 멈춤 → 답 통째 등장"이 되어 스트리밍이 없던 것과 같아진다. nginx라면 `proxy_buffering off`로 끈다.

3. **양방향 쿠키 왕복.** 세션 쿠키는 상류(backend)가 발급한다. `set-cookie`(상류→브라우저)를 프록시가 안 내려주면 브라우저가 세션 쿠키를 **못 받고**, `cookie`(브라우저→상류)를 안 올려주면 브라우저가 가진 쿠키가 **상류에 안 닿는다**. 둘 중 하나만 넘겨도 왕복이 끊겨 상류 입장에선 매번 쿠키 없는 요청 = **"처음 온 사람"**이 되어 세션이 안 선다. 발급(내려보내기)과 제시(올려보내기) 둘 다 통과해야 상태가 유지된다.
   > **set-cookie / cookie** — 전자는 서버가 브라우저에 "저장해"라고 내리는 헤더, 후자는 브라우저가 서버로 도로 보내는 헤더. 세션은 이 둘의 왕복으로 성립.

4. **봉투를 열어 재포장하면 422가 어떻게 되나.** 프록시가 상류 봉투를 열어 `data`만 꺼내 자기가 다시 응답을 조립하면, 상류가 붙인 원래 상태코드를 **프록시가 새로 정하게 된다**. 이 과정에서 세밀한 코드가 뭉개진다 — 예: backend가 준 **422**(입력 오류)를 프록시가 "예외 났으니 500" 같은 거친 코드로 바꿔버린다. 클라이언트는 422였으면 "입력 고쳐 재시도", 500이면 "서버 장애"로 다르게 반응해야 하는데 그 구분이 사라진다. 그래서 프록시는 봉투·status를 **손대지 않고 원형 반환**(`status: upstream.status`)한다.

5. **버퍼링을 끄는 층.** 응답은 여러 층에서 모일 수 있다. **애플리케이션 프레임워크** — 상류 body를 `await response.json()`처럼 통째로 읽고 반환하면 그 자체가 버퍼링이다. 스트림을 살리려면 상류 body(readable stream)를 **읽지 말고 그대로 응답 body로 넘긴다**(`return Response(upstream.body, ...)`). **리버스 프록시(nginx)** — `proxy_buffering off`로 응답을 모으지 않게 한다. **`X-Accel-Buffering: no`** — 상류(애플리케이션)가 응답 헤더에 이걸 실으면 nginx에게 "이 응답만은 버퍼링하지 말라"고 지시하는 것으로, 프록시 설정을 못 건드릴 때 응답 단위로 버퍼링을 끄는 신호다.

6. **소비자에 따라 달라지는 이유.** 판단 기준은 **"이 응답을 누가, 무엇을 위해 소비하는가"**다. 화면을 그리는 **페이지(SSR)**는 봉투 속 `data`를 꺼내 렌더링해야 하니 **연다**. 반면 **프록시(`/api/*`)**는 브라우저의 JS가 상태코드·본문을 그대로 받아 자기가 분기할 것이므로, 프록시가 미리 열어 가공하면 오히려 정보(상태코드·오류 코드)를 뭉갠다 → **원형 전달**. 같은 backend 응답이라도 "사람이 볼 화면용"과 "기계가 소비할 API용"은 처리가 다르다.

7. **연결 — 겹치는 뿌리 + allowlist는 다른 층.** 스트리밍 중계에선 같은 원리다. 프록시가 상류 200을 받아 이미 클라이언트로 흘리기 시작했다면, "한 번 나간 헤더/상태는 불변"이라 사후에 못 바꾼다 — 이건 [http-streaming-status-locked](../http-streaming-status-locked/)의 상태 잠김과 같은 원리(*상태코드는 응답의 맨 앞에서 한 번만 결정된다*)다. 그래서 흘리기 시작한 뒤에 상류가 실패해도 프록시가 상태를 고칠 수 없고, 상류가 확정한 상태를 첫 바이트 전에 그대로 넘기는 것이 사실상 유일한 선택이 된다. 다만 버퍼링 프록시의 422→500 뭉개기는 "못 바꿔서"가 아니라 "바꾸면 정보가 사라져서" 금지하는 것이라, 원형 보존 규칙의 근거는 불변성 + 정보 보존 두 가지다. **allowlist는 상충하지 않는다** — 그것은 *응답* 보존이 아니라 *요청* 위생이고, 브라우저가 보낸 쿼리를 상류로 넘기기 전에 정한 키(`q`, `topic`, `size`, 복수 `doc_kind`)만 골라 재조립해 **주입 면적을 줄이는** 것이다. 응답 본문·상태를 뭉개는 것과는 층이 다르다.
   > **allowlist** — 허용할 값(여기선 쿼리 키)만 통과시키고 나머지는 버리는 방식.

## 문제 구조 (추상화 코드)

### 변형 A — 스트림·쿠키를 BFF가 끊음 (버퍼링 + 단방향 쿠키)
① 문제 코드
```ts
export async function POST(request: Request) {
  const upstream = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST", body: await request.text(),         // cookie 미전달 → 매 요청 새 세션
  });
  const body = await upstream.text();                    // 통째로 읽음 = 버퍼링 → 타자 효과 소멸
  return new Response(body);                             // set-cookie·status 유실
}
```
② 고친 코드
```ts
export async function POST(request: Request) {
  const upstream = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json",
               cookie: request.headers.get("cookie") ?? "" },       // 브라우저 → 상류
    body: await request.text(),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const headers = new Headers({ "Content-Type": "text/plain; charset=utf-8" });
  for (const c of upstream.headers.getSetCookie()) headers.append("set-cookie", c);   // 상류 → 브라우저
  // get("set-cookie")는 여러 Set-Cookie를 쉼표로 합쳐 돌려줘(Expires 속성의 쉼표와 뒤섞임) 쿠키가 깨질 수 있다
  return new Response(upstream.body, { status: upstream.status, headers });   // 스트림·status 그대로
}
```
무엇이 깨졌나: 프록시가 스트림 타이밍·상태성 헤더를 자기 편의대로 재구성했다.\
같은 구조: 인증이 필요한 BFF 경로가 쿠키를 포워딩하지 않는 서버 측 클라이언트를 써서 401 → 쿠키 포워딩 클라이언트로 교체(관련 함정: 다중 `Set-Cookie` 릴레이, 역할별 응답의 캐시 `Vary` 누락).

### 변형 B — BFF가 봉투를 열어 재포장하며 status를 뭉갬
① 문제 코드
```ts
const res = await fetch(`${BACKEND_URL}/api/search?${request.nextUrl.searchParams}`);  // 쿼리 통째 전달
const env = await res.json();
if (!env.success) return NextResponse.json({ error: env.error }, { status: 500 });      // 422 → 500
return NextResponse.json(env.data);
```
② 고친 코드
```ts
const upstream = new URLSearchParams();
for (const key of ["q", "topic", "size"]) {                        // 정한 키만 (요청 위생)
  const v = search.get(key); if (v) upstream.set(key, v);
}
for (const kind of search.getAll("doc_kind")) upstream.append("doc_kind", kind);
const res = await fetch(`${BACKEND_URL}/api/search?${upstream}`, { headers: { "X-Request-Id": requestId } });
return NextResponse.json(await res.json(), { status: res.status });  // 봉투·status 그대로
```
무엇이 깨졌나: 기계가 소비할 응답을 프록시가 해석해 상류의 오류 의미를 바꿨다.

### 변형 C — 업로드 스트림을 BFF가 버퍼링 없이 넘기기
① 문제 코드 (선택하지 않은 방법 — 설계 단계에서 피한 버퍼링 전달)
```ts
const form = await request.formData();                 // GB 업로드를 메모리에 통째로
return fetch(`${BASE}/upload`, { method: "POST", body: form });   // boundary 재생성·취소 미전파
```
② 고친 코드
```ts
export const runtime = "nodejs";                        // 엣지 런타임 아님
return fetch(`${BASE}/upload`, {
  method: "POST",
  headers: { "Content-Type": request.headers.get("content-type")! },   // multipart boundary 보존
  body: request.body,                                  // 스트림 그대로
  signal: request.signal,                              // 클라이언트 취소를 상류까지 전파
  redirect: "manual",                                  // 스트림 본문은 redirect 재전송 불가
  cache: "no-store",
  ...({ duplex: "half" } as Record<string, unknown>),  // 스트림 본문 필수 옵션 (표준 타입에 없음)
});
// 진행률: 브라우저 fetch엔 업로드 progress가 없음 → 클라이언트는 XMLHttpRequest.upload.onprogress
```
무엇이 깨질 수 있었나: 요청 방향의 스트림도 응답과 마찬가지로 프록시가 모으면 메모리·취소·경계가 깨진다(장애 기록이 아니라 설계 제약 기록).

### 변형 D — 리버스 프록시가 WebSocket·정적 경로·upstream 이름을 원형대로 못 넘김
① 문제 코드
```nginx
upstream api { server api-server:8080; }       # 기동 시 1회 해석: 없으면 기동 실패, recreate 후 옛 IP
location ~* \.(js|css)$ { root /static; }       # 정규식 location이 prefix보다 우선 → /app/_next/... 가로챔
location /ws/ { proxy_pass http://api; }        # Upgrade 헤더 미전달 → WS 연결 실패
```
② 고친 코드
```nginx
resolver 127.0.0.11 valid=10s;                  # 도커 내장 DNS 주기 재해석 (변수 upstream과 함께)
location ^~ /app { proxy_pass http://front; }   # ^~ = 정규식 검사 생략, prefix 우선
location /ws/ {
    set $api_upstream http://api-server:8080;   # 변수 proxy_pass여야 resolver가 요청 시 재해석
    proxy_pass $api_upstream;                   # (upstream 블록 안 server 이름은 기본적으로 기동 시 1회 해석)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```
무엇이 깨졌나: 프록시가 hop-by-hop 헤더(Upgrade)를 기본으로 버리고, 이름 해석·경로 매칭 규칙이 원형 전달을 방해했다.\
같은 구조: 다른 compose 네트워크의 upstream은 네트워크 편입 또는 호스트 게이트웨이 이름으로 · 다른 경로로 프록시한 페이지의 상대 경로 정적 리소스 404 → 정적 확장자 location에서 원래 요청 URI로 프록시.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

위 변형들은 "원형 보존"(스트림·status·쿠키·헤더를 그대로 왕복)이다. 같은 원리의 후반부 — **전달받은 헤더는 신뢰 홉 기준으로만 믿는다** — 와 **명시적으로 덧붙여 전파해야 하는 헤더**에 대해 다른 방안들이 쓰였다.

### 방안 1 — BFF가 클라이언트 IP를 릴레이 + 신뢰 관문 2중
```ts
// BFF: 엣지가 넘긴 실제 IP를 상류로 릴레이 (안 넘기면 상류는 도커 브리지 게이트웨이 IP만 봄)
headers["X-Client-IP"] = clientIpFrom(request);
headers["X-Shared-Key"] = SHARED_KEY;
```
```kotlin
fun resolve(req: HttpServletRequest): String {
    val remote = req.remoteAddr
    if (!isTrusted(remote)) return remote                         // ① 출발지가 내부 컨테이너 대역인가
    if (!hasValidSecret(req)) return remote                       // ② 공유 비밀 상수시간 비교
    return sanitize(req.getHeader("X-Client-IP")) ?: sanitize(firstForwardedFor(req)) ?: remote
}
```

### 방안 2 — XFF는 신뢰 홉 수만큼 오른쪽에서
```ts
// 문제: const ip = xff.split(",")[0].trim();   // 왼쪽은 클라이언트가 보낸 값 그대로 → 위조·키 폭증
const parts = xff.split(",").map(s => s.trim());
const candidate = parts[Math.max(0, parts.length - TRUSTED_HOPS)];
return candidate && isValidIp(candidate) ? candidate : null;   // 형식·길이 검증, 실패 시 추측 없이 미부착
```

### 방안 3 — XFF는 신뢰 프록시 뒤에서만 + 키 상수시간 비교
```java
http.addFilterAfter(rateLimiter, KeyAuthFilter.class);           // 키 게이트 뒤에서 레이트리밋
String ip = props.behindProxy() ? firstXff(req) : req.getRemoteAddr();   // 맨 왼쪽 XFF는 신뢰 프록시가 헤더를
                                                                   // 덮어쓸 때만 안전 — 덧붙이는 프록시면 방안 2처럼 오른쪽에서
boolean ok = MessageDigest.isEqual(given.getBytes(UTF_8), expected.getBytes(UTF_8));   // 조기 종료 없음
```

### 방안 4 — 상관 ID는 진입 서버가 발행하고 모든 구간에 헤더로 전파
```ts
// 중계 구간 하나가 빠지면 한 요청의 로그 사슬이 끊긴다
headers: { "Content-Type": "application/json", "X-Shared-Key": secret,
           "X-Request-Id": requestId },                           // 진입 서버 발행 id 전파
```
```kotlin
val id = acceptOrIssue(req.getHeader("X-Request-Id"))            // 형식이 틀리면 재발행
// 로그 한 줄 규약: <requestId>:<server>:<message> — 성공도 기록. CI 호출은 gh-<run id>로 같은 id 사용
```

### 방안 5 — 경로 prefix를 헤더로 전달 + upstream 이름 재해석
```nginx
location /svc/ {
    proxy_pass http://svc/;                         # prefix를 떼어 전달
    proxy_set_header X-Forwarded-Prefix /svc;       # 앱이 링크·라우트를 원래 prefix로 생성
}
# 컨테이너 recreate 후 옛 IP 캐시 → resolver 설정(근본 해결은 후속 과제로 기록)
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 릴레이 + 신뢰 관문 2중 | 중간 BFF가 있고 상류가 BFF를 식별할 수 있다 | 공유 비밀 관리·대역 설정 | 공유 비밀 유출·대역 오설정 시 위조 허용 | 엣지 → BFF → API 다단 구조 |
| 2. 오른쪽에서 신뢰 홉 수 | 신뢰 프록시 홉 수가 고정·알려져 있다 | 설정 1개 + IP 검증 | 홉 수가 바뀌면 틀린 IP 채택 | 단일 엣지 뒤 서비스, 레이트리밋 키 |
| 3. 신뢰 프록시 플래그 + 상수시간 비교 | 배포 환경이 프록시 유무를 안다 | 플래그·필터 순서 | 플래그 오설정 시 위조 허용 | 키 기반 API + 레이트리밋 |
| 4. 상관 ID 전파 | 모든 구간을 코드로 통제한다 | 구간마다 헤더 1줄 | 구간 하나 누락 = 추적 단절 | 여러 서버를 거치는 요청의 관측 |
| 5. prefix 헤더 + 재해석 | 프록시가 경로를 변형한다 | 헤더 1줄·resolver | 앱이 헤더를 안 읽으면 여전히 404 | 경로 기반 라우팅 뒤 앱 |

**결론**: 원형 보존은 "받은 것을 그대로 넘긴다"이고, 이 방안들은 그 반대편 — "무엇을 믿고, 무엇을 덧붙이나" — 이다.\
클라이언트 식별 헤더는 **신뢰 경계를 코드로 명시**해야 한다: 홉 수가 고정이면 2, 프록시 유무만 알면 3, BFF가 끼면 1.\
관측·라우팅용 헤더(상관 ID·prefix)는 프록시가 **자동으로 만들어 주지 않으므로** 모든 구간에서 명시적으로 덧붙인다(4·5).

## 방안 비교 — 로그인으로 보내는 이동 주소(Location)를 누가, 무엇을 기준으로 만드나

같은 원리(프록시 계층마다 헤더를 명시적으로 다뤄야 한다 — 방안 5 의 "앱이 바깥 경로를 알아야 링크가 맞다")가 리다이렉트의 `Location` 에서 나온 사례다.\
앱(Next.js 15.5, middleware 에서 세션 확인)은 리버스 프록시(nginx) 뒤에서 돌고, 세션이 없는 화면 요청을 `/login` 으로 보낸다.\
`Location` 은 응답 헤더라 프록시를 지나 브라우저까지 그대로 간다 — 앱이 아는 주소(내부 호스트·포트)로 만들면 그 주소가 바깥으로 샌다.

```
브라우저 ── https://공개출처/ ──▶ nginx ── http://내부:포트/ ──▶ 앱 middleware
                                                                     │ 세션 없음
         ◀── 307 Location: ? ──────────────────────────────────────┘
방안 6  요청 주소 기준 절대 주소   → 앱이 본 Host(내부 주소)가 Location 에 들어갈 수 있다
방안 7  상대 주소 "/login" 직접    → 단위 테스트 초록, 실제 서버 500 (프레임워크 어댑터가 다시 해석)
방안 8  설정된 공개 출처 기준 절대 주소 + 프록시가 경로만 남김 → 바깥에는 "/login"
```

### 방안 6 — 요청 주소를 기준으로 절대 주소를 만든다 (처음 형태)
```ts
const response = NextResponse.redirect(new URL("/login", request.nextUrl), 307);
// 주석의 가정: "같은 출처로의 이동은 프레임워크가 상대 Location 으로 바꿔 내보낸다"
```
리뷰어가 앱을 루프백 주소로 띄운 실행에서 `Location: http://localhost:<내부 포트>/login` 이 나왔다.\
운영 설정(모든 주소에 바인드)에서는 구현 쪽 실측이 `/login` 이었다 — 가정은 실행 설정에 따라서만 맞았다(잠재 결함).\
게다가 테스트는 요청 주소와 설정값을 같은 값으로 두어, 요청 호스트를 베끼는 구현도 통과했다.

### 방안 7 — 상대 주소 `/login` 을 직접 낸다 (리뷰 직후의 수정 방향)
```ts
return new NextResponse(null, { status: 307, headers: { Location: "/login" } });
```
단위 테스트 452개는 초록이었는데 실제 서버에서는 500 이 났다.\
Next 15.5 의 middleware 어댑터가 응답의 `Location` 을 기준 주소 없이 URL 로 다시 해석해 `ERR_INVALID_URL` 을 던졌다 — 단위 테스트는 middleware 함수만 부르고 어댑터를 거치지 않는다.\
상대 `Location` 은 HTTP 로는 허용되지만, 계층(프레임워크 어댑터·프록시)마다 받아들이는지가 다르다.

### 방안 8 — 설정된 공개 출처로 만들고, 프록시가 경로만 남긴다 (이 사례의 선택)
```ts
const configuredOrigin = readConfig().publicOrigin;           // 설정값 — 요청 Host 를 쓰지 않는다
if (!isValidOrigin(configuredOrigin)) {
  return new NextResponse("service unavailable", { status: 503 });   // 요청 주소로 대신하지 않는다
}
return NextResponse.redirect(new URL("/login", configuredOrigin), 307);
```
```nginx
# 앱이 낸 절대 Location 을 경로만 남긴 상대 주소로 바꾼다
proxy_redirect ~^https?://[^/]+(/.*)$ $1;
absolute_redirect off;        # 그 상대 주소를 nginx 가 다시 절대 주소(내부 포트 포함)로 만들지 않게
proxy_set_header X-Forwarded-Host "";
```
```ts
// 테스트: 요청 주소를 설정값과 다른 내부 주소로 둔다 — 요청 호스트를 베끼면 빨강
const request = makeRequest("http://localhost:8080/dashboard");    // 설정값과 다른 내부 주소
expect(response.headers.get("location")).toBe(`${PUBLIC_ORIGIN}/login`);
```
요청 주소 기준으로 되돌린 변형에서 38개가 빨강이 됐다.\
컨테이너 실측: `Host: evil.example.test` 로 보낸 요청이 500 이 아니라 307 과 설정된 공개 출처의 `/login` 을 받았다.\
시작 검사가 설정을 해석하지 못하면 서버가 아예 뜨지 않으므로, 위의 503 은 정상 구동에서 닿지 않는 두 번째 방어다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 6. 요청 주소 기준 | 앱이 보는 Host 가 바깥 Host 와 같다 | 없음 | 프록시 뒤에서 내부 주소가 새고, Host 위조가 Location 에 실린다 | 프록시 없이 직접 받는 앱 |
| 7. 상대 주소 직접 | 모든 계층이 상대 Location 을 받아들인다 | 없음 | 계층 하나가 다시 해석하면 500 — 단위 테스트는 못 본다 | 상대 Location 을 그대로 통과시키는 것을 실제 서버로 확인한 스택 |
| 8. 설정 출처 + 프록시 재작성 | 공개 출처를 설정으로 안다 | 설정 키 1개·형식 검사·프록시 설정 2줄 | 설정이 틀리면 엉뚱한 출처 — 시작 검사로 막는다 | 프록시 뒤의 앱, Host 를 믿을 수 없는 배치 |

**결론**: 리다이렉트 주소를 요청에서 얻은 값(Host·요청 URL)으로 만들지 않는다 — 프록시 뒤에서는 그 값이 바깥 주소가 아니고, 위조될 수도 있다.\
상대 주소가 가장 단순하지만 그것을 받아들이는지는 계층마다 다르므로, 단위 테스트가 아니라 실제 서버에서 확인한 뒤에만 쓴다(7).\
그 확인이 실패하는 스택에서는 설정된 공개 출처로 절대 주소를 만들고, 바깥에 내보낼 모양(상대 경로)은 프록시가 정한다(8).\
테스트는 요청 주소와 설정값을 다르게 두어야 "요청에서 베꼈다"를 가를 수 있다.

검증 기록: 2026-11-23 — 사건 기록·리뷰 기록·수정 전후 코드 대조·추상화. 리뷰어 실행(내부 주소가 든 Location), 구현 쪽 실측(상대 주소 → 500), 변형 실험(38 빨강), 컨테이너 확인(위조 Host → 설정 출처의 `/login`)은 사건 기록의 값이다.

## 방안 비교 — 원본 포트가 인터넷에서 직접 닿을 때: 클라이언트 IP 헤더를 어디서 믿나

같은 원리(전달받은 헤더는 신뢰 홉 기준으로만 믿는다 — 방안 1~3)에서, **신뢰 홉을 건너뛰는 길이 있는** 배치의 사례다.\
엣지 프록시(TLS 종단)는 `X-Real-IP` 에 실제 접속 주소를 넣어 집 서버의 원본 포트로 넘긴다. 앱은 이 IP 로 로그인 속도 제한과 시도 기록을 한다.\
처음 가정은 "원본 포트는 엣지에서만 닿는다"였는데, 착수 직후 확인에서 틀렸다 — 공유기 포트포워딩은 엣지 전용이 아니라 인터넷 어디서나 닿는다.\
그대로 두면 엣지를 거치지 않은 연결이 `X-Real-IP` 를 마음대로 넣어 IP 별 속도 제한을 피할 수 있다.

```
클라이언트 ──▶ 엣지 (X-Real-IP = 실제 주소) ──▶ 원본 포트 ──▶ 원본 nginx ──▶ 앱
공격자 ───────────────────────────────────────▶ 원본 포트 (X-Real-IP: 아무 값)
                                                     │
방안 9   원본 nginx 가 연결 출처로 거른다:  엣지 → 엣지가 넣은 헤더 / 사설 대역 → 실제 접속 주소 / 그 밖 → 444
         앱으로 가는 클라이언트 IP 헤더는 nginx 가 다시 쓴 한 값뿐
```

### 방안 9 — 원본 앞 프록시에서 연결 출처 허용 목록 + 헤더 재작성 (이 사례의 선택)
```nginx
geo $via_edge   { default 0; <엣지 주소> 1; }          # 저장소 밖 파일 — 없으면 설정 검사(nginx -t)가 실패
geo $is_internal { default 0; 127.0.0.0/8 1; 10.0.0.0/8 1; 172.16.0.0/12 1; 192.168.0.0/16 1; }
map "$via_edge:$is_internal" $allow_conn { "0:0" 0; default 1; }
map $via_edge $real_client { 1 $http_x_real_ip; default $remote_addr; }

server {
    if ($allow_conn = 0) { return 444; }         # 응답 없이 연결을 닫는다
    proxy_set_header X-Real-IP       $real_client;    # 엣지가 아닌 곳에서 온 X-Real-IP·XFF 는 버려진다
    proxy_set_header X-Forwarded-For $real_client;
    # ...
}
```
사설 대역을 받는 것은 같은 서버의 헬스 확인·감시·도커 브리지 연결 때문이다 — 그 연결은 실제 접속 주소를 IP 로 쓴다.\
실측: 바깥 도메인(엣지 경유)으로 보낸 로그인 시도의 기록된 주소가 요청자의 공인 주소였고(엣지 주소도 사설 주소도 아님), 클라이언트가 넣은 가짜 `X-Real-IP`·`X-Forwarded-For` 는 기록에 없었다.\
문서용 주소 대역의 도커 네트워크 실험에서는 엣지 주소의 헤더 전달, 그 밖 공인 주소의 끊김, 사설 대역의 실제 주소 사용을 확인했다.\
**한계**: 엣지가 아닌 제3의 바깥 기계에서 원본 포트로 직접 붙어 444 로 닫히는지는 시험하지 못했다(쓸 수 있는 바깥 기계가 엣지뿐) — 위 실측에서의 추론이다.

| 방안 | 판정 위치 | 직접 연결 처리 | 앱이 읽는 값 | 맞는 조건 |
|------|-----------|----------------|--------------|-----------|
| 1. 릴레이 + 신뢰 관문 2중 | 앱(접속 주소 대역 + 공유 비밀) | 헤더를 무시하고 접속 주소 사용 | 조건부로 헤더 또는 접속 주소 | 앱이 실제 접속 주소를 보는 다단 구조 |
| 2·3. XFF 오른쪽 · 신뢰 프록시 플래그 | 앱 | 설정에 따라 위조 허용 가능 | XFF 의 한 칸 | 앞단 구성이 고정되고 우회 길이 없을 때 |
| 9. 원본 프록시의 출처 허용 목록 + 재작성 | 원본 앞 프록시(연결 출처) | 연결을 닫는다(444) | 프록시가 다시 쓴 한 헤더 | 원본 포트가 신뢰 홉을 건너 직접 닿는 배치 |

**결론**: 클라이언트 IP 헤더는 그 헤더를 넣은 홉에서 온 연결일 때만 의미가 있다 — 판정에 필요한 것은 헤더가 아니라 **연결의 출처**다.\
앱이 프록시 뒤에 있으면 앱은 프록시 주소만 보므로 연결 출처를 판정할 수 없다. 그래서 출처를 볼 수 있는 첫 계층(원본 앞 프록시)에서 거르고, 앱에는 다시 쓴 값 하나만 넘긴다(9).\
앱이 실제 접속 주소를 직접 보는 구조라면 앱에서 같은 판정을 하는 방안 1 로 충분하다.\
신뢰 홉을 건너뛰는 길이 있는지는 가정하지 말고 착수 때 확인한다 — 이 사례에서 그 가정이 틀렸다.

검증 기록: 2026-11-23 — 사건 기록·설정 파일 대조·추상화(엣지 주소는 자리표시로 바꿨다). 가정이 틀린 것(착수 직후 확인), 도커 네트워크 실험, 공개 전 차단 조건으로 둔 실측(공인 주소 기록 · 가짜 헤더 미기록)과 그 한계는 사건 기록의 값이다.
