# network/34-http-caching — HTTP 캐시: Cache-Control·ETag·조건부 요청·Vary·휴리스틱 신선도 — 정리 (힌트)

## 해결하는 문제

같은 로고 이미지를 방문자마다 원 서버가 다시 보낸다고 하자.\
대역폭이 낭비되고, 원 서버가 불필요하게 바빠지고, 사용자는 왕복 시간만큼 기다린다.\
HTTP 캐시는 "이미 받은 응답을 저장해 두고, 조건이 맞으면 원 서버에 묻지 않고 다시 쓰는" 규칙이다.

쉬운 예: 사내 문서를 복사해 책상에 둔다.\
복사본에 "이 날짜까지 유효" 도장이 있으면 그냥 본다.\
날짜가 지났으면 원본 담당자에게 "아직 이 판이 최신인가요?"만 묻는다. 같다고 하면 복사본을 계속 쓴다.

똑같은 구조다.\
유효 기간 도장 = `Cache-Control: max-age`, "아직 최신인가요?" = 조건부 요청(`If-None-Match`), "같다" = `304 Not Modified`.

실무 예:
- CDN이 정적 파일을 대신 내보내 원 서버 트래픽을 줄인다.
- 배포했는데 사용자 브라우저가 옛 JS를 계속 쓴다. 캐시 규칙을 잘못 정한 결과다.
- 로그인 사용자 전용 응답을 CDN이 저장해 다른 사용자에게 내보낸다. 개인정보 사고다.

## 동작·원리

### 1. 캐시는 어디에 있나 — 전용 vs 공유

```text
  Browser                      CDN / 리버스 프록시                Origin
  +-------------+              +------------------+              +--------+
  | private     |  <-------->  | shared cache     |  <-------->  | 원 서버 |
  | cache       |              | (여러 사용자 공용) |              |        |
  +-------------+              +------------------+              +--------+
   한 사용자 전용                  모든 사용자가 같은 저장본을 받는다
```

- *전용 캐시(private cache)*: 한 사용자만 쓰는 캐시다. 브라우저 캐시가 대표다.
- *공유 캐시(shared cache)*: 여러 사용자의 요청에 같은 저장본을 쓴다. CDN·프록시가 대표다.
- 사고는 대부분 공유 캐시에서 난다. 한 사람의 응답이 모두에게 퍼지기 때문이다.

### 2. 저장해도 되나 — 저장 조건

RFC 9111 §3을 줄인 것이다. 아래를 **모두** 만족해야 저장할 수 있다.

```text
  [ ] 캐시가 이해하는 메서드 (보통 GET·HEAD)
  [ ] 최종 상태 코드 (1xx 아님)
  [ ] 응답에 no-store 없음
  [ ] 공유 캐시라면: private 없음
  [ ] 공유 캐시라면: 요청에 Authorization 없음 (또는 public·s-maxage·must-revalidate로 허용)
  [ ] 그리고 다음 중 하나 이상
        public / (전용 캐시면) private / Expires / max-age / (공유면) s-maxage
        / 휴리스틱 캐시 가능 상태 코드
```

- 마지막 줄이 중요하다. **명시 헤더가 없어도** 200·301·404 같은 코드는 저장될 수 있다(휴리스틱, 아래 4).
- `Set-Cookie`가 붙어 있어도 캐시를 막지 않는다(RFC 9111 §7.3). 막고 싶으면 `Cache-Control`을 직접 준다.

### 3. 신선한가 — 나이와 수명

```text
   원 서버가 생성                        수명(freshness_lifetime) 끝
   |<------------- fresh --------------->|<------------ stale ------------->
   |                                    |
   0s                                   max-age                       시간 →
               ^
               current_age (Age 헤더 + 캐시에 머문 시간)

   fresh  = freshness_lifetime > current_age   -> 원 서버에 안 묻고 바로 씀
   stale  = 그 반대                             -> 보통 검증(아래 5) 후 씀
```

(RFC 9111 §4.2)

수명은 다음 순서로 **처음 맞는 것**을 쓴다(§4.2.1).

```text
  1. (공유 캐시) s-maxage
  2. max-age
  3. Expires - Date
  4. 없으면 -> 휴리스틱 수명
```

- *Age 헤더*: 캐시가 "이 응답이 원 서버에서 나온 지 몇 초 됐는지" 추정해 붙이는 값이다(§5.1). 검증 없이 저장본을 내보낼 때 캐시는 `Age`를 붙여야 한다(MUST, §4).
- 수명 계산에 원 서버의 `Date`를 쓰는 이유는 캐시와 원 서버의 시계 차이를 줄이기 위해서다(§4.2.1).

### 4. 휴리스틱 신선도 — 헤더가 없을 때 캐시가 스스로 정하는 수명

```text
  응답: 200 OK
        Last-Modified: (100일 전)          <- 수명 헤더 없음
                    |
                    v
  캐시: "지난 100일 동안 안 바뀌었으니 당분간 안 바뀌겠지"
        휴리스틱 수명 = (지금 - Last-Modified) x 비율
        RFC가 드는 흔한 비율 = 10%  ->  약 10일 (예시)
```

- 캐시는 명시 수명이 없을 때 휴리스틱 수명을 붙여도 된다(MAY, RFC 9111 §4.2.2).
- 명시 수명이 있으면 휴리스틱을 쓰면 안 된다(MUST NOT).
- 대상은 "휴리스틱 캐시 가능" 상태 코드다. RFC 9110 §15.1은 200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414, 501을 든다.
- RFC는 구체 알고리즘을 정하지 않는다. `Last-Modified` 이후 경과 시간의 일정 비율을 권하고, 흔한 값으로 10%를 든다.
- 쿼리(`?`)가 있는 URL도 휴리스틱 캐시될 수 있다. 예전 규격은 금지했지만 실제로는 널리 지켜지지 않았다(§4.2.2 Note).
- 결론: **캐시되면 안 되는 응답에는 반드시 명시 헤더를 준다.** 헤더가 없으면 "캐시하지 마"가 아니라 "캐시가 알아서"다.

### 5. 검증 — 조건부 요청과 304

```text
  (1) 첫 요청
  Client ---- GET /app.js ----------------------------------> Origin
         <--- 200  ETag: "v42"  Cache-Control: no-cache  [본문 300KB]

  (2) 다시 쓸 때 (no-cache라 매번 확인)
  Client ---- GET /app.js   If-None-Match: "v42" ----------> Origin
         <--- 304 Not Modified   ETag: "v42"   [본문 없음]
         -> 저장본을 그대로 사용

  (3) 바뀌었으면
         <--- 200  ETag: "v43"  [새 본문]
```

- *검증자(validator)*: 표현이 바뀌었는지 비교하는 값이다. `ETag`와 `Last-Modified`가 있다(RFC 9110 §8.8).
  - `ETag` + `If-None-Match`: 태그가 일치하면 304(GET·HEAD) 또는 412(그 밖의 메서드)(§13.1.2).
  - `Last-Modified` + `If-Modified-Since`: 시각 비교다. 초 단위라 1초 안의 변경을 놓칠 수 있다.
- *강한 검증자 vs 약한 검증자*: 강한 것은 내용이 바이트 단위로 바뀌면 반드시 바뀐다. 약한 것(`W/"..."`)은 의미상 같으면 같은 값을 유지할 수 있다(§8.8.1). `If-None-Match`는 약한 비교를 쓴다(MUST, §13.1.2).
- 304 응답에는 200이었다면 보냈을 `ETag`·`Cache-Control`·`Expires`·`Vary` 등을 반드시 담는다(MUST, §15.4.5). 본문은 없다.
- 검증은 본문 전송은 아끼지만 **왕복 한 번은 든다**. 그래서 오래 안 바뀌는 파일은 검증조차 없는 긴 `max-age`가 낫다.

### 6. 캐시 키와 Vary — "같은 요청"의 정의

```text
  기본 캐시 키 = (메서드, 대상 URI)

  응답에 Vary: Accept-Encoding 이 있으면
  보조 키 = 요청의 Accept-Encoding 값

  GET /api/list  Accept-Encoding: gzip   ---> 저장본 A (gzip)
  GET /api/list  Accept-Encoding: br     ---> 저장본 B (br)
  GET /api/list  (Accept-Encoding 없음)   ---> 저장본 C (무압축)
```

- 캐시는 저장본의 `Vary`가 지명한 요청 헤더가 모두 일치할 때만 검증 없이 재사용한다(MUST NOT otherwise, RFC 9111 §4.1).
- `Vary: *`는 항상 불일치다. 사실상 매번 원 서버로 간다.
- *내용 협상(content negotiation)*: 같은 URL이 요청 헤더(`Accept-Encoding`, `Accept-Language` 등)에 따라 다른 표현을 돌려주는 것이다. 이때 서버는 `Vary`로 "어떤 요청 헤더가 결과를 바꿨는지" 알리는 것이 권고다(SHOULD, RFC 9110 §12.5.5).
- `Vary`에 값 종류가 많은 헤더(`User-Agent`, `Cookie`)를 넣으면 저장본이 쪼개져 적중률이 떨어진다.

### 7. Cache-Control 지시어 정리

```text
  응답 지시어            뜻                                                  근거
  max-age=N             N초 동안 신선                                        RFC 9111 §5.2.2.1
  s-maxage=N            공유 캐시에서만 max-age를 덮어씀 + stale이면 검증 필수    §5.2.2.10
  no-cache              저장은 해도 됨. 쓸 때마다 원 서버 검증 필수               §5.2.2.4
  no-store              저장 자체 금지 (전용·공유 모두)                          §5.2.2.5
  private               공유 캐시 저장 금지. 브라우저 캐시는 가능                  §5.2.2.7
  public                원래 금지되는 경우(예: Authorization 요청)에도 저장 허용     §5.2.2.9
  must-revalidate       stale이면 검증 전 재사용 금지. 원 서버 불통이면 오류(504 권장) §5.2.2.2
  immutable             신선한 동안에는 새로 고침해도 조건부 요청을 보내지 말 것       RFC 8246 §2
  stale-while-revalidate=N  stale 된 뒤 N초 동안은 저장본을 주고 뒤에서 갱신 가능    RFC 5861 §3
  stale-if-error=N      오류 시 stale 저장본을 줄 수 있음                         RFC 5861 §4
```

- **`no-cache` ≠ "캐시하지 마라"**. 저장은 하되 매번 확인하라는 뜻이다. 저장 자체를 막는 것은 `no-store`다.
- `no-store`도 프라이버시를 보장하지 않는다. 악의적 캐시는 무시할 수 있다(§5.2.2.5).
- 지시어가 충돌하면(예: `max-age`와 `no-cache` 동시) 가장 제한적인 것을 따르는 것이 권장이다(§4.2.1).

### 8. 무효화 — 쓰기가 지나가면 지운다

```text
  Client -- POST /orders/42/cancel --> [캐시] --> Origin
                                         |      <-- 200
                                         +-- /orders/42/cancel 저장본 무효화 (MUST)
                                         +-- Location·Content-Location URI도 무효화 가능 (MAY)
```

- 안전하지 않은 메서드에 비오류(2xx·3xx) 응답이 오면 캐시는 대상 URI를 무효화해야 한다(MUST, RFC 9111 §4.4).
- 이 무효화는 **요청이 지나간 캐시에만** 일어난다. 다른 경로의 CDN 노드나 다른 사용자 브라우저는 모른다.
- 그래서 전역 무효화가 필요하면 CDN의 purge API나 "URL 자체를 바꾸기"(파일명 해시)를 쓴다.

## 쓰이는 자료구조·알고리즘

- **캐시 키 해시 테이블** — (메서드, URI)를 해시해 저장본을 찾는다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **보조 키 목록(Vary)** — 한 기본 키 아래 여러 변형(variant)을 두고, 요청 헤더를 정규화해 비교한다. 여러 개가 맞으면 가장 최근(`Date` 기준)을 고른다(RFC 9111 §4.1).
- **LRU 축출** — 저장 공간이 차면 오래 안 쓴 항목부터 버린다. 신선도와 별개로 공간 때문에 사라질 수 있다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **나이·수명 계산** — `Age`, `Date`, 요청·응답 시각으로 `current_age`를 구하고 수명과 비교한다(RFC 9111 §4.2.3). 시계 차이를 보정하는 산술이다.
- **요청 합치기(collapsing)** — 캐시 미스 때 같은 키의 동시 요청을 하나로 묶어 원 서버에 한 번만 보낸다(RFC 9111 §4). 캐시 스탬피드 방어와 같은 생각이다. [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)
- **ETag 생성 = 내용 해시** — 본문 해시(예: SHA-256 앞부분)나 버전 번호로 만든다. 서버가 여러 대면 모든 서버가 같은 방식으로 만들어야 한다.

## 적용 — 풀어나가는 법

### 1. 자원 종류별로 정책을 나눈다

```text
  자원                          Cache-Control                            검증자
  파일명에 해시 든 정적 파일       public, max-age=31536000, immutable      (거의 불필요)
    app.3f9a1c.js
  HTML 진입 페이지               no-cache                                  ETag
  공개 API 목록 (CDN 허용)        public, max-age=60, s-maxage=300          ETag
  로그인 사용자 전용 API           private, no-cache  또는  no-store         ETag(선택)
  민감 정보 (계좌·토큰)            no-store                                  -
```

- 핵심 생각: **바뀌는 것은 짧게 확인하고, 안 바뀌는 것은 URL을 바꿔서 갱신한다.**
- HTML은 매번 확인(`no-cache`)하고, HTML이 가리키는 JS·CSS 파일명에 해시를 넣는다. 배포하면 HTML만 새로 받고 새 파일명을 따라간다.

### 2. 헤더를 눈으로 확인한다

```bash
# 응답 헤더: Cache-Control, ETag, Last-Modified, Age, Vary 확인
curl -sI https://cdn.example.com/app.3f9a1c.js

# 조건부 요청 -> 304가 오는지
curl -sI -H 'If-None-Match: "v42"' https://api.example.com/list

# 압축별 변형이 분리되는지 (Vary: Accept-Encoding)
curl -sI -H 'Accept-Encoding: gzip' https://api.example.com/list
curl -sI -H 'Accept-Encoding: identity' https://api.example.com/list

# 두 번 요청해 Age가 늘어나면 공유 캐시가 내보낸 것
curl -sI https://cdn.example.com/logo.png | grep -i '^age'
```

- CDN마다 적중 여부를 알려 주는 헤더(예: `X-Cache`, `CF-Cache-Status`)가 있다. 이름·값은 업체 문서를 따른다.
- 브라우저 개발자 도구 Network 탭의 "(disk cache)", "304" 표시도 같은 정보를 준다.

### 3. 코드에서

Java(Spring MVC) — 수명과 ETag를 붙이고, 조건부 요청이면 304로 끝낸다.

```java
@GetMapping("/products/{id}")
public ResponseEntity<Product> get(@PathVariable long id, WebRequest req) {
    Product p = service.find(id);
    String etag = "\"" + p.version() + "\"";
    if (req.checkNotModified(etag)) {
        return null;                       // 프레임워크가 304를 보낸다
    }
    return ResponseEntity.ok()
        .cacheControl(CacheControl.maxAge(Duration.ofSeconds(60)).cachePublic())
        .eTag(etag)
        .body(p);
}
```

Node — 사용자별 응답은 공유 캐시에 남지 않게 한다.

```js
app.get('/me', (req, res) => {
  res.set('Cache-Control', 'private, no-store');
  res.json(loadProfile(req.user.id));
});
```

### 4. CDN 앞에서 점검할 순서

1. 사용자마다 다른 응답(쿠키·토큰으로 달라지는 응답)에 `private` 또는 `no-store`가 있는가.
2. 내용 협상하는 응답에 올바른 `Vary`가 있는가(`Accept-Encoding` 등).
3. 수명 헤더가 **없는** 200 응답이 있는가. 있다면 휴리스틱 캐시 대상이다.
4. 배포 산출물 파일명에 해시가 들어가는가.

## 장애 시나리오와 대처

### 1. 다른 사용자의 응답을 캐시가 돌려준다 — 개인정보 노출

- **현상**: 사용자 A가 마이페이지에서 사용자 B의 이름·주소를 본다.
- **보이는 형태**
  - 문제 응답에 `Age: 37` 같은 값이 있다. 원 서버가 아니라 캐시가 내보냈다는 뜻이다.
  - CDN 적중 헤더가 HIT이다.
  - 응답 헤더에 `Cache-Control`이 없거나 `public, max-age=...`다. `Vary`에 사용자 식별 헤더가 없다.
- **원인**
  - 캐시 키는 기본적으로 (메서드, URI)다. `/me`는 모든 사용자에게 같은 URI다.
  - 응답이 쿠키로 달라지는데 캐시에는 그 사실을 알리지 않았다(`private` 없음, `Vary`에 `Cookie` 없음).
  - `Set-Cookie`가 있어도 캐시를 막지 않는다(RFC 9111 §7.3). `Authorization` 요청은 공유 캐시가 기본으로 막지만(§3.5), 쿠키 인증은 그 보호를 받지 못한다.
- **대처**
  - 즉시: CDN에서 해당 경로를 purge하고, 캐시 제외 규칙을 건다.
  - 근본: 사용자별 응답에 `Cache-Control: private`(또는 `no-store`)를 준다.
  - `Vary: Cookie`도 이론상 막지만, 쿠키 값마다 저장본이 생겨 적중률이 무너진다. 개인 응답은 공유 캐시에 두지 않는 쪽이 맞다.

### 2. 배포했는데 사용자에게 옛 화면이 계속 보인다 — 휴리스틱 캐싱

- **현상**: 배포 후 일부 사용자만 옛 JS·HTML을 받는다. 강력 새로 고침하면 고쳐진다.
- **보이는 형태**
  - 브라우저 Network 탭에 "(disk cache)" 또는 "(memory cache)"로 표시된다. 서버에는 요청 로그가 없다.
  - 응답 헤더에 `Cache-Control`·`Expires`가 없고 `Last-Modified`만 있다.
- **원인**: 명시 수명이 없으니 캐시가 휴리스틱 수명을 붙였다(RFC 9111 §4.2.2). 오래전에 수정된 파일일수록 수명이 길어진다(흔한 비율 10%).
- **대처**
  - HTML에는 `Cache-Control: no-cache`를 준다.
  - 정적 파일은 파일명에 내용 해시를 넣고 긴 `max-age`와 `immutable`을 준다.
  - 이미 퍼진 휴리스틱 캐시는 서버에서 지울 수 없다. HTML이 새 파일명을 가리키게 바꾸는 것이 가장 빠른 복구다.

### 3. `no-cache`를 "저장 금지"로 오해한다

- **현상 A**: 보안 점검에서 "계좌 조회 응답이 브라우저 디스크 캐시에 남는다"는 지적을 받는다.
- **현상 B**: 반대로 모든 응답에 `no-store`를 붙여 정적 파일까지 매번 전부 다시 받는다. 페이지가 느리다.
- **보이는 형태**: A는 응답에 `Cache-Control: no-cache`만 있다. B는 정적 파일에도 `no-store`가 있고 304가 전혀 없다.
- **원인**: `no-cache`는 "저장은 하되 매번 검증"이다(§5.2.2.4). 저장을 막는 것은 `no-store`다(§5.2.2.5).
- **대처**: 민감 응답은 `no-store`, 자주 바뀌지만 공개인 응답은 `no-cache` + ETag, 불변 파일은 긴 `max-age`로 나눈다.

### 4. `Vary`를 잘못 다뤄 압축 응답이 엉뚱한 클라이언트로 가거나, 적중률이 무너진다

- **현상 A**: 오래된 클라이언트·스크립트가 깨진 바이트를 받는다.
- **현상 B**: CDN 적중률이 갑자기 한 자릿수로 떨어진다.
- **보이는 형태**
  - A: gzip으로 압축된 본문(`Content-Encoding: gzip`)이 `Accept-Encoding` 없는 요청에 온다. 응답에 `Vary: Accept-Encoding`이 없다.
  - B: 응답에 `Vary: User-Agent`나 `Vary: Cookie`가 있다.
- **원인**
  - A: 압축 여부로 표현이 달라지는데 `Vary`로 알리지 않았다. 캐시는 첫 저장본(gzip)을 모두에게 준다.
  - B: 값 종류가 수천 가지인 헤더를 보조 키로 넣어 저장본이 잘게 쪼개졌다.
- **대처**
  - 압축하는 응답에는 `Vary: Accept-Encoding`을 둔다. 세부는 39번(content-encoding)에서 다룬다.
  - 값 종류가 많은 헤더는 `Vary`에 넣지 말고, 필요하면 CDN에서 정규화(예: 기기 유형 3가지로 묶기)한다.

### 5. 서버마다 ETag가 달라 304가 거의 안 나온다

- **현상**: 조건부 요청을 보내는데도 200과 전체 본문이 계속 온다. 원 서버 트래픽이 줄지 않는다.
- **보이는 형태**: 같은 파일을 여러 번 요청하면 ETag 값이 번갈아 바뀐다. 로드밸런서 뒤 서버 수만큼 다른 값이 보인다.
- **원인**: ETag를 서버 로컬 정보(파일 수정 시각·파일 시스템 정보 등)로 만들었다. 배포 시각이 서버마다 달라 같은 내용인데 태그가 다르다(예시).
- **대처**: ETag를 내용 해시나 버전 번호처럼 서버와 무관한 값으로 만든다. 확인은 `curl -sI`를 여러 번 보내 ETag를 비교한다.

## 핵심 문장

- 캐시는 저장 조건(§3)을 통과한 응답을 (메서드, URI) + `Vary` 보조 키로 저장하고, 수명 안이면 원 서버에 묻지 않고 재사용한다.
- 수명은 `s-maxage` → `max-age` → `Expires - Date` 순으로 정하고, 모두 없으면 캐시가 휴리스틱 수명을 붙일 수 있다. 헤더가 없다고 캐시되지 않는 것이 아니다.
- `no-cache`는 "매번 검증", `no-store`는 "저장 금지", `private`는 "공유 캐시 금지"다.
- 조건부 요청(`If-None-Match` → 304)은 본문 전송을 아끼지만 왕복은 든다. 불변 파일은 파일명 해시 + 긴 `max-age` + `immutable`이 낫다.
- 쿠키로 달라지는 응답은 캐시 키에 드러나지 않는다. `private`나 `no-store`를 주지 않으면 공유 캐시가 다른 사용자에게 내보낸다.

## 관련 주제·근거

- 선행
  - `33-http-semantics` — [33-http-semantics](../33-http-semantics/2-summary.md)
- 후속
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) — `Accept-Encoding`과 `Vary`
  - [41-range-requests-and-resume](../41-range-requests-and-resume/2-summary.md) — `If-Range`·206
  - [47-cdn-and-edge](../47-cdn-and-edge/2-summary.md) — CDN 캐시 계층·무효화
  - [web-platform/07-service-workers-and-offline](../../web-platform/07-service-workers-and-offline/2-summary.md) — 서비스 워커 캐시 고착.
  - [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md) — 캐시 만료 순간의 몰림
- RFC 9111 HTTP Caching <https://www.rfc-editor.org/rfc/rfc9111>
  - §3 저장 조건 · §3.5 Authorization 요청 · §4 저장본 재사용 조건·요청 합치기 · §4.1 Vary와 캐시 키
  - §4.2 신선도 · §4.2.1 수명 계산 순서 · §4.2.2 휴리스틱 신선도(10%) · §4.2.3 Age 계산 · §4.2.4 stale 제공
  - §4.3 검증 · §4.4 무효화 · §5.1 Age · §5.2.2 응답 지시어 · §7.3 민감 정보 캐싱(Set-Cookie)
- RFC 9110 HTTP Semantics <https://www.rfc-editor.org/rfc/rfc9110>
  - §8.8 검증자(강·약) · §12.5.5 Vary · §13.1.2 If-None-Match · §15.1 휴리스틱 캐시 가능 코드 · §15.4.5 304
- RFC 8246 `immutable` <https://www.rfc-editor.org/rfc/rfc8246>
- RFC 5861 `stale-while-revalidate`·`stale-if-error` <https://www.rfc-editor.org/rfc/rfc5861>
- MDN "HTTP caching" <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching>
- Spring Framework `CacheControl`·`WebRequest.checkNotModified` <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-caching.html>
- Grigorik, 『High Performance Browser Networking』 "Optimizing Application Delivery" 장(캐시 활용) <https://hpbn.co/optimizing-application-delivery/>
