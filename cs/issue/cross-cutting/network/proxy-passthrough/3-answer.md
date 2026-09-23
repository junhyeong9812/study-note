# cs/issue/network/proxy-passthrough — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

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

6. **소비자에 따라 갈리는 이유.** 판단 기준은 **"이 응답을 누가, 무엇을 위해 소비하는가"**다. 화면을 그리는 **페이지(SSR)**는 봉투 속 `data`를 꺼내 렌더링해야 하니 **연다**. 반면 **프록시(`/api/*`)**는 브라우저의 JS가 상태코드·본문을 그대로 받아 자기가 분기할 것이므로, 프록시가 미리 열어 가공하면 오히려 정보(상태코드·오류 코드)를 뭉갠다 → **원형 전달**. 같은 backend 응답이라도 "사람이 볼 화면용"과 "기계가 소비할 API용"은 처리가 다르다.

7. **연결 — 같은 뿌리 + allowlist는 다른 층.** 그렇다, 같은 뿌리다. 프록시가 상류 200을 받아 이미 클라이언트로 흘리기 시작했다면, "한 번 나간 헤더/상태는 불변"이라 사후에 못 바꾼다 — 이건 [http-streaming-status-locked](../http-streaming-status-locked/)의 상태 잠김과 정확히 같은 원리(*상태코드는 응답의 맨 앞에서 한 번만 결정된다*)다. 그래서 스트림 상황에선 프록시가 상태를 재구성할 여지조차 없으니 원형 보존이 유일한 선택이 된다. **allowlist는 상충하지 않는다** — 그것은 *응답* 보존이 아니라 *요청* 위생이고, 브라우저가 보낸 쿼리를 상류로 넘기기 전에 정한 키(`q`, `topic`, `size`, 복수 `doc_kind`)만 골라 재조립해 **주입 면적을 줄이는** 것이다. 응답 본문·상태를 뭉개는 것과는 층이 다르다.
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
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) headers.set("set-cookie", setCookie);              // 상류 → 브라우저
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
    proxy_pass http://api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```
무엇이 깨졌나: 프록시가 hop-by-hop 헤더(Upgrade)를 기본으로 버리고, 이름 해석·경로 매칭 규칙이 원형 전달을 방해했다.\
같은 구조: 다른 compose 네트워크의 upstream은 네트워크 편입 또는 호스트 게이트웨이 이름으로 · 다른 경로로 프록시한 페이지의 상대 경로 정적 리소스 404 → 정적 확장자 location에서 원래 요청 URI로 프록시.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

위 변형들은 "원형 보존"(스트림·status·쿠키·헤더를 그대로 왕복)이다. 같은 원리의 후반부 — **전달받은 헤더는 신뢰 홉 기준으로만 믿는다** — 와 **명시적으로 덧붙여 전파해야 하는 헤더**에 대해 다른 방안들이 쓰였다.

### 방안 1 — BFF가 클라이언트 IP를 릴레이 + 신뢰 관문 2중
```ts
// BFF: 엣지가 넘긴 실제 IP를 상류로 릴레이 (안 넘기면 상류는 도커 브리지 게이트웨이 IP만 봄)
headers["X-Real-IP"] = clientIpFrom(request);
headers["X-Proxy-Secret"] = PROXY_SECRET;
```
```kotlin
fun resolve(req: HttpServletRequest): String {
    val remote = req.remoteAddr
    if (!isTrusted(remote)) return remote                         // ① 출발지가 내부 컨테이너 대역인가
    if (!hasValidSecret(req)) return remote                       // ② 공유 비밀 상수시간 비교
    return sanitize(req.getHeader("X-Real-IP")) ?: sanitize(firstForwardedFor(req)) ?: remote
}
```
잔여 리스크(수용·기록): LAN에서 BFF 포트를 직접 호출하면 위조 헤더가 세탁될 수 있다. 엣지 강화 옵션은 XFF를 이어붙이기 대신 `$remote_addr`로 덮어쓰기.

### 방안 2 — XFF는 신뢰 홉 수만큼 오른쪽에서
```ts
// 문제: const ip = xff.split(",")[0].trim();   // 왼쪽은 클라이언트가 보낸 값 그대로 → 위조·키 폭증
const parts = xff.split(",").map(s => s.trim());
const candidate = parts[Math.max(0, parts.length - TRUSTED_PROXY_HOPS)];
return candidate && isIpLiteral(candidate) ? candidate : null;   // 형식·길이 검증, 실패 시 추측 없이 미부착
```
같은 구조: 레이트리밋이 XFF가 **없으면 통째로 건너뛰는** 분기 → 프록시를 우회한 직접 접속은 무제한 · 선행 콤마로 빈 키. 계획: 신뢰 프록시 IP에서 온 요청만 XFF(가장 오른쪽 신뢰 홉), 그 외엔 소켓 주소, 스킵 분기 제거 + 직접 접속은 네트워크 레벨 차단.

### 방안 3 — XFF는 신뢰 프록시 뒤에서만 + 키 상수시간 비교
```java
http.addFilterAfter(rateLimitFilter, ApiKeyFilter.class);        // 키 게이트 뒤에서 레이트리밋
String ip = props.trustedProxy() ? firstXff(req) : req.getRemoteAddr();
boolean ok = MessageDigest.isEqual(given.getBytes(UTF_8), expected.getBytes(UTF_8));   // 조기 종료 없음
```

### 방안 4 — 상관 ID는 진입 서버가 발행하고 모든 구간에 헤더로 전파
```ts
// 중계 구간 하나가 빠지면 한 요청의 로그 사슬이 끊긴다
headers: { "Content-Type": "application/json", "X-Sync-Secret": secret,
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
| 1. 릴레이 + 신뢰 관문 2중 | 중간 BFF가 있고 상류가 BFF를 식별할 수 있다 | 공유 비밀 관리·대역 설정 | BFF 포트 직접 호출 시 세탁(잔여 리스크) | 엣지 → BFF → API 다단 구조 |
| 2. 오른쪽에서 신뢰 홉 수 | 신뢰 프록시 홉 수가 고정·알려져 있다 | 설정 1개 + IP 검증 | 홉 수가 바뀌면 틀린 IP 채택 | 단일 엣지 뒤 서비스, 레이트리밋 키 |
| 3. 신뢰 프록시 플래그 + 상수시간 비교 | 배포 환경이 프록시 유무를 안다 | 플래그·필터 순서 | 플래그 오설정 시 위조 허용 | 키 기반 API + 레이트리밋 |
| 4. 상관 ID 전파 | 모든 구간을 코드로 통제한다 | 구간마다 헤더 1줄 | 구간 하나 누락 = 추적 단절 | 여러 서버를 거치는 요청의 관측 |
| 5. prefix 헤더 + 재해석 | 프록시가 경로를 변형한다 | 헤더 1줄·resolver | 앱이 헤더를 안 읽으면 여전히 404 | 경로 기반 라우팅 뒤 앱 |

**결론**: 원형 보존은 "받은 것을 그대로 넘긴다"이고, 이 방안들은 그 반대편 — "무엇을 믿고, 무엇을 덧붙이나" — 이다.\
클라이언트 식별 헤더는 **신뢰 경계를 코드로 명시**해야 한다: 홉 수가 고정이면 2, 프록시 유무만 알면 3, BFF가 끼면 1.\
관측·라우팅용 헤더(상관 ID·prefix)는 프록시가 **자동으로 만들어 주지 않으므로** 모든 구간에서 명시적으로 덧붙인다(4·5).
