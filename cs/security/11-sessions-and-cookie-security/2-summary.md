# security/11-sessions-and-cookie-security — 세션 ID, 세션 고정, 쿠키 속성 — 정리 (힌트)

## 해결하는 문제

HTTP 요청은 서로 독립이다. 로그인(10번)에 성공해도 다음 요청은 그 사실을 모른다.

```text
  요청 1: POST /login (id, password)   → 200 "환영합니다"
  요청 2: GET  /orders                  → 서버: "누구세요?"   ← HTTP 자체는 기억하지 않는다
```

- 해법: 로그인 성공 때 서버가 **추측할 수 없는 번호표**를 주고, 브라우저가 매 요청에 그 번호표를 다시 보낸다.
  - *세션(session)*: 서버가 한 사용자의 로그인 상태를 여러 요청에 걸쳐 기억하는 단위.
  - *세션 ID*: 그 세션을 가리키는 무작위 문자열. 가진 사람이 곧 그 사용자로 취급된다(bearer).
  - *쿠키(cookie)*: 서버가 `Set-Cookie`로 맡기고 브라우저가 `Cookie` 헤더로 돌려주는 이름=값. 세션 ID를 나르는 가장 흔한 수단이다.

쉬운 예: 놀이공원 손목 밴드다.
- 입구에서 표를 확인(로그인)하면 밴드를 채워 준다(세션 ID 쿠키).
- 그 뒤로는 놀이기구마다 밴드만 본다. 밴드를 빼앗기면 남이 내 자격으로 탄다.
- 그래서 밴드는 위조할 수 없어야 하고(무작위성), 남의 손에 넘어가지 않게(쿠키 속성) 하고, 입장 순간 새것으로 바꿔야 한다(세션 고정 방지).

실무 예:
- 로그인은 됐는데 다음 요청에서 다시 로그인 화면으로 튕긴다 → 쿠키가 안 실린다(속성·도메인·SameSite).
- 외부 SSO에서 돌아오는 콜백에서만 "state 불일치"로 실패한다 → SameSite 기본값 변경의 영향.

## 동작·원리

### 1. 세션 한 바퀴

```text
  브라우저                                        서버                     세션 저장소 (해시 + TTL)
  ── POST /login ──────────────────────────────>  인증 성공
                                                  sid = CSPRNG 128비트 ──>  sid → {user: alice, created, lastSeen}
  <── Set-Cookie: __Host-sid=k3J...; Path=/;          TTL = 유휴 30분 (예시)
        Secure; HttpOnly; SameSite=Lax ─────────
  ── GET /orders  Cookie: __Host-sid=k3J... ───>  sid로 조회 ──────────────> 있으면 lastSeen 갱신, TTL 연장
                                                  없거나 만료 → 401 / 로그인으로
  ── POST /logout ─────────────────────────────>  저장소에서 삭제 ────────>  sid 제거
  <── Set-Cookie: __Host-sid=; Max-Age=0 ─────
```

- 세션 ID의 조건(OWASP Session Management Cheat Sheet)
  - 엔트로피 최소 **64비트**. 길이보다 예측 불가능성이 중요하다. 보통 CSPRNG로 128비트를 만든다(09번).
  - 값에 의미(사용자 ID, 시각)를 넣지 않는다. 의미 있는 정보는 서버 쪽 세션 객체에 둔다.
  - 기본 이름(`JSESSIONID`, `PHPSESSID`)은 기술 스택을 드러낸다. `id`처럼 일반적인 이름을 권한다.
- 만료는 두 종류다.
  - *유휴 만료(idle timeout)*: 마지막 요청 뒤 일정 시간. Spring Boot `server.servlet.session.timeout` 기본값은 `30m`이다.
  - *절대 만료(absolute timeout)*: 로그인 뒤 일정 시간이 지나면 활동과 상관없이 끝. 유휴 만료만 있으면 계속 쓰는 탈취 세션은 영원히 산다.
  - 클라이언트 쪽 만료(쿠키 `Max-Age`)만으로는 부족하다. 서버가 저장소에서 판정해야 한다(OWASP).

### 2. 세션 고정 — 로그인 전 번호표를 그대로 쓰면

```text
  공격자                          피해자 브라우저                       서버
  ① 사이트 방문 → sid=AAA 받음
  ② 피해자 브라우저에 sid=AAA를 심는다 (URL 파라미터로 세션을 받는 서버, 하위 도메인의 쿠키 설정 등)
                                  ③ sid=AAA로 로그인 ───────────────>  취약: AAA를 "alice 로그인됨"으로 승격
  ④ sid=AAA로 요청 ─────────────────────────────────────────────────>  alice로 처리됨
                                                                      고침: 로그인 순간 새 sid=BBB 발급, AAA 폐기
                                                                            → ④는 401
```

- *세션 고정(session fixation)*: 공격자가 미리 알고 있는 세션 ID를 피해자가 쓰게 만들어, 피해자의 로그인 결과를 가로채는 공격.
- 규칙: **권한 수준이 바뀔 때마다 세션 ID를 새로 발급**한다. 로그인, 비밀번호 변경, 역할 상승이 해당한다(OWASP).
- Spring Security는 기본으로 막는다. Servlet 3.1+ 기본 전략은 `changeSessionId`(컨테이너의 `HttpServletRequest#changeSessionId()`로 ID만 바꾸고 속성은 유지)다. `none`으로 끄면 취약해진다.

실험(로컬 Python 3 http.server + curl, 2026-10-07) — 로그인 전 세션을 공격자가 받아 두고, 피해자가 그 세션으로 로그인한 뒤 공격자가 같은 ID로 `/me`를 부른다. 단순화를 위해 세션 ID를 쿠키 대신 `X-Sid` 요청 헤더로 실었다:

```text
  fixed=0 공격자가 미리 받은 sid로 /me: user=alice [200] | 로그인 후 sid 같음? yes
  fixed=1 공격자가 미리 받은 sid로 /me: user=None [401] | 로그인 후 sid 같음? no
```

### 3. 쿠키 속성 — 어디로, 누구에게 보내나

```text
  Set-Cookie: __Host-sid=k3J...; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=1800
              │                  │       │       │         │             └ 브라우저 보관 기간(없으면 브라우저 세션 동안)
              │                  │       │       │         └ 다른 사이트에서 시작된 요청에 실을지
              │                  │       │       └ JS의 document.cookie에서 숨김
              │                  │       └ 안전한 연결(HTTPS 등)로만 전송
              │                  └ 이 경로 아래 요청에만
              └ __Host- 접두: Secure + Path=/ + Domain 없음 을 강제 (호스트에만 묶임)
```

- `Domain`
  - 생략하면 *host-only*: 쿠키를 준 호스트에만 간다.
  - `Domain=example.com`을 주면 모든 하위 도메인에도 간다. 하위 도메인 하나가 뚫리면 세션 쿠키를 읽거나 덮어쓸 수 있다.
- `HttpOnly`: 스크립트가 못 읽는다. XSS(19번)가 쿠키를 훔쳐 가는 것을 막지만, XSS가 그 페이지에서 요청을 대신 보내는 것까지는 막지 못한다.
- `Secure`: 평문 HTTP로 안 보낸다. "안전한 연결"의 정의는 브라우저에 맡겨져 있다. 6265bis 초안은 HTTPS와 `localhost`를 흔한 예로 든다.
- 쿠키는 **포트를 구분하지 않는다**(RFC 6265 §8.5). 같은 호스트의 다른 포트 서비스끼리 쿠키를 공유한다. 출처(origin)는 포트를 구분하므로 SOP와 쿠키의 경계가 다르다.
- 접두 `__Host-`·`__Secure-`(6265bis 초안 §4.1.3): 이름만 보고 속성을 보장받는다. OWASP는 세션 ID에 `__Host-`를 권한다.

### 4. SameSite — "같은 사이트"에서 시작된 요청인가

```text
  사이트(site) = 스킴 + 등록 가능 도메인(eTLD+1)      출처(origin) = 스킴 + 호스트 + 포트
  https://a.shop.example  와  https://b.shop.example   → 같은 사이트, 다른 출처
  http://127.0.0.1:18431  와  http://localhost:18432   → 다른 사이트(호스트가 다름)

                     같은 사이트 요청   다른 사이트에서 시작된 요청
                                       최상위 GET 이동   최상위 POST   img·iframe·fetch
  SameSite=Strict        보냄              안 보냄           안 보냄        안 보냄
  SameSite=Lax           보냄              보냄              안 보냄        안 보냄
  SameSite=None; Secure  보냄              보냄              보냄           보냄
  속성 없음(Chrome)      보냄              보냄              생성 2분 이내만  안 보냄
```

- 이 표는 SameSite 규칙만 보인다. `None`은 "SameSite 제한을 걸지 않는다"는 뜻이지 "반드시 실린다"는 뜻이 아니다.
  - 다른 출처로 가는 `fetch()`는 기본 `credentials`가 `same-origin`이라 쿠키를 싣지 않는다. `credentials: "include"`(+ CORS 허용)가 있어야 실린다(WHATWG Fetch).
  - 브라우저의 제3자 쿠키 차단 설정이 `None` 쿠키를 따로 막을 수 있다.

- RFC 6265bis-22 초안(2025-12, RFC 편집 대기 중)
  - 알 수 없는 값은 Lax와 같은 기본 강제 모드를 따른다.
  - *Lax-allowing-unsafe*: 속성을 지정하지 않은 쿠키에만, 최근에 만든 쿠키에 한해 최상위 POST 같은 "안전하지 않은" 메서드에도 보내는 호환 모드. "2분 이하가 합리적 한도"라고 적는다(UA 재량, MAY/SHOULD).
- Chrome의 *Lax-by-default*: 속성 없는 쿠키를 Lax로 취급한다. Chromium 공지는 2020-07-14에 Chrome 80 이상 안정판(그 무렵 나온 84 포함)에서 단계적 적용을 재개했고, 2020-08-11에 목표 대상을 Chrome 80 이상 안정판 사용자 100%로 올렸다(실제 적용 비율은 점진 증가)고 적는다. `SameSite=None`은 `Secure`가 함께 있어야 한다. "Lax + POST" 2분 예외는 임시 조치라고 명시한다.
  - 흔한 오해: "SameSite를 안 쓰면 예전처럼 다 보낸다" → Chrome에서는 Lax에 가깝게 동작한다. 브라우저마다 기본값이 다르므로 명시한다.

실험(Google Chrome 151.0.7922.173 headless + playwright-core 1.62.1, 로컬 Python 서버 2개, 2026-10-07) — app = `http://127.0.0.1:A`, 다른 사이트 = `http://localhost:B`. app이 다섯 쿠키를 심은 뒤, 다른 사이트 페이지에서 app으로 요청을 보내고 app 서버가 받은 `Cookie` 헤더를 기록했다:

```text
  app document.cookie = c_lax=1; c_strict=1; c_none=1; c_default=1          ← c_httponly 없음
  same-site-GET    GET  Cookie: c_lax=1; c_strict=1; c_none=1; c_default=1; c_httponly=1
  img-subresource  GET  Cookie: c_none=1
  iframe           GET  Cookie: c_none=1
  top-GET-link     GET  Cookie: c_lax=1; c_none=1; c_default=1; c_httponly=1
  top-POST-form    POST Cookie: c_none=1; c_default=1        ← 쿠키 나이 ~0초
  top-POST-form    POST Cookie: c_none=1                     ← 쿠키 나이 ~130초 (별도 실행)
```

- `HttpOnly` 쿠키는 `document.cookie`에 없지만 요청에는 실린다.
- 다른 사이트의 최상위 POST에 `SameSite=Lax`(c_lax)는 안 실린다. 외부 IdP가 콜백을 POST로 보내면 Lax 세션·state 쿠키가 빠지는 이유다(장애 1).
- 속성 없는 쿠키(c_default)는 생성 직후에는 POST에 실렸고 130초 뒤에는 안 실렸다. Chrome의 2분 예외가 지금(151)도 남아 있다. Playwright는 이 쿠키의 `sameSite`를 `Lax`로 보고했지만 실제 전송은 Lax와 달랐다.
- `Secure` 쿠키(c_none)가 `http://127.0.0.1`에서 저장·전송됐다. Chrome이 루프백 주소를 안전한 연결로 취급하기 때문이다. 운영 HTTPS 환경과 같다고 일반화하지 않는다.

## 쓰이는 자료구조·알고리즘

- **해시 맵 + TTL** — 세션 저장소는 `sid → 세션 객체` 조회가 핵심이다. 유휴 만료는 접근마다 TTL을 연장하는 키 만료로 구현한다(예: Redis 해시 + `EXPIRE`, Spring Session Data Redis). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **CSPRNG** — 세션 ID 생성. `java.security.SecureRandom` 128비트. 생일 경계로 충돌 확률을 어림한다([16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md)).
- **HMAC 서명 쿠키** — 서버 상태 없이 쿠키 값의 위·변조만 막을 때 `값.HMAC(키, 값)` 모양을 쓴다. 기밀성은 없다(05번).
- **공개 접미사 목록(Public Suffix List)** — "등록 가능 도메인"을 정하는 표. `co.kr`처럼 접미사가 두 칸인 경우를 알려 준다. SameSite의 사이트 판정과 `Domain` 속성 거부에 쓰인다.

## 적용 — 풀어나가는 법

### 1. 세션 쿠키를 안전하게 (Spring Boot 3)

취약 예:

```yaml
server:
  servlet:
    session:
      cookie:
        domain: example.com      # 모든 하위 도메인에 세션 쿠키가 간다
        secure: false
        http-only: false         # XSS가 document.cookie로 읽는다
```

고친 예:

```yaml
server:
  servlet:
    session:
      timeout: 30m               # 유휴 만료(Boot 기본값과 같음, 명시)
      cookie:
        name: __Host-sid         # Domain 없음 + Secure + Path=/ 와 함께
        path: /
        secure: true
        http-only: true
        same-site: lax
```

- 절대 만료는 프로퍼티가 없다. 로그인 시각을 세션에 저장하고 필터에서 검사한다.

```java
// 절대 만료: 로그인 후 8시간(예시)이면 활동과 무관하게 끝낸다
@Component
class AbsoluteTimeoutFilter extends OncePerRequestFilter {
    static final Duration MAX = Duration.ofHours(8);
    @Override protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        HttpSession s = req.getSession(false);
        if (s != null && s.getAttribute("loginAt") instanceof Instant at && at.plus(MAX).isBefore(Instant.now())) {
            s.invalidate();
            res.sendError(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
        chain.doFilter(req, res);
    }
}
```

### 2. 세션 고정 방지를 끄지 않는다

취약 예:

```java
http.sessionManagement(s -> s.sessionFixation(f -> f.none()));   // 로그인 전 ID가 그대로 로그인 세션이 된다
```

고친 예:

```java
http.sessionManagement(s -> s.sessionFixation(f -> f.changeSessionId()));   // Servlet 3.1+ 기본값과 같다
```

- 직접 로그인 처리를 짜면 성공 지점에서 `request.changeSessionId()`를 부른다. 권한 상승(관리자 모드 진입)에서도 같다.
- URL에 세션 ID를 싣지 않는다(`;jsessionid=`). 로그·Referer로 샌다. `server.servlet.session.tracking-modes: cookie`로 막는다.

### 3. 로그아웃은 서버에서 지운다

```java
// 클라이언트 쿠키만 지우면, 이미 복사된 sid는 서버에서 계속 유효하다
session.invalidate();                                              // 서버 저장소에서 제거
ResponseCookie c = ResponseCookie.from("__Host-sid", "").path("/").secure(true).httpOnly(true).maxAge(0).build();
response.addHeader(HttpHeaders.SET_COOKIE, c.toString());
```

- "모든 기기에서 로그아웃"은 사용자 ID로 세션을 찾을 색인이 필요하다(Spring Session의 `FindByIndexNameSessionRepository`). 비밀번호 변경 때 다른 세션을 모두 끊는 데 쓴다.

### 4. 쿠키가 안 실리는 이유를 진단한다

```text
  1) 응답에 Set-Cookie가 있나?            curl -si https://app.example/login | grep -i set-cookie
  2) 브라우저가 저장을 거부했나?           DevTools > Network > 응답의 Cookies 탭: "This Set-Cookie was blocked ..."
                                          (SameSite=None인데 Secure 없음, Domain 불일치, __Host- 조건 위반 등)
  3) 저장은 됐는데 요청에 안 실리나?       요청의 Cookies 탭 "This cookie was blocked because ..." 
                                          (SameSite 판정, Path 불일치, Secure인데 http)
  4) 사이트 판정은?                        요청이 시작된 페이지의 사이트(eTLD+1)와 대상 사이트 비교
```

## 장애 시나리오와 대처

### 1. 외부 SSO 콜백만 실패한다 — SameSite 기본값의 영향

- **현상**: 회사 SSO(외부 IdP)로 로그인하면 돌아오는 순간 "state 불일치"나 "세션 없음"으로 실패한다. 직접 로그인은 된다.
- **보이는 형태**
  - IdP가 `response_mode=form_post`로 콜백을 **다른 사이트에서 최상위 POST**로 보낸다.
  - 콜백 요청의 DevTools 쿠키 탭에 세션·state 쿠키가 "SameSite 때문에 차단"으로 표시된다. 서버 로그: `state mismatch` 또는 새 세션 생성.
  - 로그인 시작 직후 2분 안에 끝나면 성공하고, 오래 머물면 실패한다(속성 없는 쿠키의 Chrome 2분 예외 — 실험 참고).
- **원인**: Lax(또는 속성 없음 → Lax 취급) 쿠키는 다른 사이트에서 온 최상위 POST에 실리지 않는다.
- **대처**
  - 콜백 처리에 필요한 쿠키(state·nonce를 담은 임시 쿠키)만 `SameSite=None; Secure`로 두고 수명을 짧게 한다. 세션 쿠키 전체를 None으로 풀지 않는다.
    - 단, 이 방법은 인가 요청 상태(state·nonce)를 세션이 아니라 그 임시 쿠키에 저장하도록 구성한 경우에만 통한다. Spring Security 기본값(`HttpSessionOAuth2AuthorizationRequestRepository`)은 세션에 저장하므로, 콜백에 세션 쿠키가 빠지면 "세션 없음"이 그대로 남는다. 저장소를 쿠키 기반으로 바꾸거나 아래 쿼리 방식을 쓴다.
  - 또는 IdP 응답 방식을 쿼리(최상위 GET 이동)로 바꾼다. Lax 쿠키가 실린다.
  - 쿠키를 명시적으로 설정해 브라우저 기본값 변화에 의존하지 않는다.

### 2. 세션 고정 — 로그인 전후 세션 ID가 같다

- **현상**: 점검에서 "로그인 전 받은 세션 ID가 로그인 후에도 유효하다"는 지적.
- **보이는 형태**: 로그인 전 `Set-Cookie: sid=AAA`, 로그인 응답에 새 `Set-Cookie`가 없다. 로그인 전에 복사해 둔 AAA로 인증된 API가 `200`.
- **원인**: 로그인 성공 때 세션 ID를 갱신하지 않는다. 커스텀 로그인 처리, `sessionFixation().none()`, URL 세션 추적 허용.
- **대처**: 로그인·권한 변경 시 `changeSessionId()`. URL 세션 추적 끄기. 회귀 테스트로 "로그인 응답에 새 세션 쿠키가 있다"를 고정한다.

### 3. 하위 도메인 하나가 세션을 오염시킨다

- **현상**: 마케팅용 `promo.example.com`이 뚫린 뒤, 메인 서비스 사용자가 이상한 계정으로 로그인돼 있다.
- **보이는 형태**: 세션 쿠키가 `Domain=example.com`. 요청에 같은 이름 쿠키가 두 개 실린다(`Cookie: sid=...; sid=...`).
- **원인**: 하위 도메인은 상위 도메인 쿠키를 설정할 수 있다. 공격자가 자기 세션 ID를 심어 세션 고정을 하거나, 같은 이름 쿠키로 덮어쓴다.
- **대처**: 세션 쿠키는 host-only(`Domain` 생략)·`__Host-` 접두. 서로 다른 신뢰 수준의 서비스는 다른 등록 도메인으로 분리한다.

### 4. 로그아웃했는데 세션이 살아 있다

- **현상**: 공용 PC에서 로그아웃했는데, 그 세션 ID로 여전히 API가 된다.
- **보이는 형태**: 로그아웃 응답에 `Max-Age=0` 쿠키만 있고, 서버 저장소에 sid 키가 남아 있다(`redis-cli EXISTS ...` → 1).
- **원인**: 클라이언트 쿠키만 지우고 서버 세션을 무효화하지 않았다. 쿠키 값은 이미 복사됐을 수 있다.
- **대처**: `session.invalidate()`로 서버에서 지운다. 절대 만료를 둔다. 비밀번호 변경 시 그 사용자의 다른 세션도 끊는다.

### 5. 세션 저장소 장애 → 전원 로그아웃

- **현상**: 배포 직후 모든 사용자가 로그인 화면으로 튕긴다.
- **보이는 형태**: `401` 급증, 세션 저장소(Redis) 연결 오류 로그, 또는 인스턴스별 메모리 세션인데 로드 밸런서가 다른 인스턴스로 보냄.
- **원인**: 세션 상태가 한 인스턴스 메모리에만 있거나, 공유 저장소가 비었다(재시작·키 축출).
- **대처**: 공유 세션 저장소를 쓰고, 축출 정책이 세션 키를 지우지 않게 메모리를 잡는다. 저장소 장애 때 "검증 생략"으로 열지 않는다(fail-closed). 토큰 방식과의 비교는 12번.

## 핵심 문장

- 세션 ID는 가진 사람이 곧 사용자로 취급되는 번호표다. 64비트 이상의 엔트로피를 가진 무의미한 무작위 값이어야 한다.
- 권한 수준이 바뀌면(로그인 포함) 세션 ID를 새로 발급한다. 그래야 세션 고정이 막힌다.
- `HttpOnly`는 스크립트가 쿠키를 읽는 것을, `Secure`는 평문 전송을, `SameSite`는 설정값(Strict·Lax)에 따라 다른 사이트에서 시작된 요청에 실리는 것을 제한한다(`None`은 제한 없음).
- SameSite는 출처가 아니라 사이트(스킴 + 등록 가능 도메인)로 판정한다. Lax 쿠키는 다른 사이트에서 온 최상위 POST에 실리지 않는다.
- 쿠키는 포트를 구분하지 않고, `Domain`을 주면 하위 도메인까지 퍼진다. 세션 쿠키는 `__Host-` 접두로 호스트에 묶는다.
- 로그아웃과 만료는 서버 저장소에서 판정한다. 클라이언트 쿠키 삭제만으로는 끝나지 않는다.

## 관련 주제·근거

- 선행
  - [10-authentication-basics](../10-authentication-basics/2-summary.md) — 세션은 인증 결과를 들고 다니는 수단
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 메서드의 안전성(GET vs POST), 헤더
- 후속·연결
  - [12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md) — 서버 저장소 없는 자기 포함 토큰과의 비교
  - [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — 토큰 저장 위치·BFF
  - [19-xss-and-csp](../19-xss-and-csp/2-summary.md), [20-csrf-and-samesite](../20-csrf-and-samesite/2-summary.md), [21-same-origin-and-cors](../21-same-origin-and-cors/2-summary.md)
  - [web-platform/06-browser-storage](../../web-platform/06-browser-storage/2-summary.md) — 쿠키 vs Web Storage
  - [languages/web-api/29-credentials-and-cookies](../../../languages/web-api/29-credentials-and-cookies/2-summary.md) — fetch의 `credentials`와 쿠키
- 1차 출처
  - RFC 6265 HTTP State Management Mechanism — §8.5 쿠키는 포트를 구분하지 않음 <https://www.rfc-editor.org/rfc/rfc6265>
  - draft-ietf-httpbis-rfc6265bis-22 (2025-12-01, RFC 편집 대기) — §4.1.3 `__Secure-`·`__Host-`, SameSite 기본 강제 모드, §5.6.7.2 Lax-allowing-unsafe(2분), "secure" 연결은 UA 정의 <https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/>
  - Chromium "SameSite Updates" — 2020-07-14 Chrome 80+ 단계적 재개, 2020-08-11 목표 대상 100%, `None`은 `Secure` 필요, Lax+POST 2분 임시 조치 <https://www.chromium.org/updates/same-site/>
  - OWASP Session Management Cheat Sheet — 64비트 엔트로피, 권한 변경 시 ID 재발급, `__Host-`, 유휴·절대 만료 <https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html>
  - Spring Security Reference — Session Management(세션 고정: Servlet 3.1+ 기본 `changeSessionId`) <https://docs.spring.io/spring-security/reference/servlet/authentication/session-management.html>
  - Spring Boot Common Application Properties — `server.servlet.session.timeout` 기본 `30m`, `cookie.same-site`·`secure`·`http-only` <https://docs.spring.io/spring-boot/appendix/application-properties/index.html>
- 실험(2026-10-07)
  - 세션 고정: 로컬 Python 3 `http.server`, curl(세션 ID는 `X-Sid` 헤더로 단순화). 갱신 없음 → 공격자 sid로 `200 user=alice`, 갱신 → `401`
  - SameSite·HttpOnly·Secure: Google Chrome 151.0.7922.173 headless + playwright-core 1.62.1, `127.0.0.1` vs `localhost`(다른 사이트). 요청 종류별 전송 쿠키, 속성 없는 쿠키의 2분 예외(0초 전송·130초 미전송)
