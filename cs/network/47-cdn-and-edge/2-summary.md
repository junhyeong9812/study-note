# network/47-cdn-and-edge — CDN 캐시 계층·원점 보호·무효화 — 정리 (힌트)

## 해결하는 문제

서버가 서울 한 곳에 있다고 하자.\
상파울루 사용자는 요청마다 지구 반대편까지 왕복한다.\
사용자가 늘면 같은 이미지를 서버가 수백만 번 다시 보낸다.\
트래픽이 한꺼번에 몰리면 서버(**원점**, origin)가 버티지 못한다.

CDN(Content Delivery Network)은 사용자 가까운 곳에 **공유 캐시 서버(엣지)** 를 여러 곳에 둔다.\
엣지가 응답을 저장해 두고 대신 준다.\
원점은 엣지가 모르는 것만 답한다.

  - *원점(origin)*: CDN 뒤에 있는 원본 서버다. 캐시에 없는 것을 최종적으로 답한다.
  - *엣지(edge)*: 사용자 가까이 있는 CDN 서버다. PoP(Point of Presence)라고도 부른다.

쉬운 예: 본사 창고 하나에서 전국에 배송하면 느리고 창고가 붐빈다.\
동네마다 편의점에 인기 상품을 미리 놓아 두면, 대부분은 편의점에서 끝난다.\
편의점에 없는 것만 지역 물류센터, 거기도 없으면 본사로 간다.

똑같은 구조다.\
편의점 = 엣지, 지역 물류센터 = 상위 계층 캐시(tier·shield), 본사 창고 = 원점.

실무 예:
- 정적 자원(JS·CSS·이미지)을 CDN에 두어 원점 트래픽과 지연을 줄인다.
- 스트리밍 세그먼트 전달(45번).
- 공개 API 응답을 짧게 캐시해 순간 폭주를 흡수한다.

## 동작·원리

### 1. 캐시 계층 — 뒤로 갈수록 비싸다

```text
  브라우저 캐시(private)
        | 미스
        v
  엣지 PoP (shared, 사용자 근처, 수백 곳)
        | 미스
        v
  상위 계층 / 지역 캐시 / origin shield (소수)
        | 미스
        v
  원점 서버
```

- 계층이 깊을수록 원점에 닿는 요청이 줄어든다.
- Cloudflare Tiered Cache: 하위 계층(보통 방문자에 가장 가까운 데이터센터)에 없으면 상위 계층에 묻는다. **상위 계층만 원점에 요청**한다. 원점 연결도 적은 수의 데이터센터로 모인다(Cloudflare 문서).
- CloudFront: 엣지 로케이션 → 지역 엣지 캐시(regional edge cache)를 거친다. Origin Shield를 켜면 그 앞에 한 층을 더 둔다. 모든 지역 캐시의 원점 요청이 Origin Shield를 지난다(AWS 문서).

  - *공유 캐시(shared cache)*: 여러 사용자의 응답을 저장하고 재사용하는 캐시다. CDN·리버스 프록시가 여기에 속한다. 브라우저 캐시는 *사설 캐시(private cache)* 다(RFC 9111 §1).

### 2. 캐시 키 — "같은 응답"을 판정하는 기준

```text
  요청: GET https://shop.example.com/products?id=7&utm_source=ad
        Cookie: session=abc
        Accept-Encoding: br

  캐시 키(기본, 개념)
    = method + scheme + host + path + query        (RFC 9111 §2: 최소 method + target URI)
    + Vary가 지목한 요청 헤더 값                    (RFC 9111 §4.1)
    + CDN 설정으로 넣고 뺀 것                        (쿠키·헤더·쿼리 일부)
```

- RFC 9111 §2: 캐시 키는 최소한 요청 메서드와 대상 URI로 구성된다. 흔한 캐시는 GET만 캐시하므로 사실상 URI만 쓴다.
- **Vary**: 응답이 어떤 요청 헤더에 따라 달라지는지 알린다. 캐시는 Vary가 지목한 요청 헤더가 모두 일치할 때만 저장본을 재사용할 수 있다(MUST NOT otherwise, §4.1).
- CDN 기본 키 예
  - Cloudflare: scheme + host + 쿼리 포함 URI, CORS용 `Origin` 헤더 등. **쿠키는 기본 키에 없다**(Cloudflare 문서).
  - nginx: `proxy_cache_key` 기본값 `$scheme$proxy_host$request_uri`(nginx 문서).

```text
  키에 너무 적게 넣으면  -> 다른 사람의 응답을 준다      (정확성 사고)
  키에 너무 많이 넣으면  -> 히트율이 0에 가까워진다      (효율 사고: utm_*, 쿠키 전체)
```

### 3. 신선도 — 얼마나 오래 재사용하나

```text
  Cache-Control: public, max-age=60, s-maxage=600, stale-while-revalidate=30, stale-if-error=86400
                          ^ 브라우저      ^ 공유 캐시(CDN)  ^ 만료 후 30초간 옛것 주며 뒤에서 갱신
                                                                              ^ 원점 오류 시 옛것 허용
```

- `s-maxage`: 공유 캐시에서는 `max-age`·`Expires`보다 우선한다(RFC 9111 §5.2.2.10).
- `private`: 공유 캐시는 저장하면 안 된다(MUST NOT, §5.2.2.7). 브라우저는 저장할 수 있다.
- `no-store`: 어떤 캐시도 저장하지 않는다.
- `stale-while-revalidate`·`stale-if-error`: RFC 5861의 확장이다. 만료 뒤에도 정해진 초 동안 옛 응답을 줄 수 있다(MAY).
- `CDN-Cache-Control`: CDN만 보는 전용 헤더다. 브라우저용 `Cache-Control`과 따로 줄 수 있다(RFC 9213).
- 명시적 만료가 없으면 캐시가 휴리스틱으로 정할 수 있다(MAY, §4.2.2). `Last-Modified` 이후 경과 시간의 10% 정도가 흔한 설정이라고 RFC가 예로 든다.

### 4. 원점 보호 — 미스가 몰릴 때

```text
  같은 객체 미스 1000건 동시 도착
     요청 병합 없음:  엣지 --1000건--> 원점        (스탬피드)
     요청 병합 있음:  엣지 --1건-----> 원점, 나머지 999건은 기다렸다가 같은 응답
```

- **요청 병합(request collapsing)**: 같은 캐시 키의 동시 미스를 원점 요청 하나로 합친다.
  - nginx `proxy_cache_lock on`: 새 캐시 항목은 한 번에 한 요청만 원점에 보낸다. 나머지는 캐시에 응답이 생기거나 락 타임아웃까지 기다린다(nginx 문서).
  - CloudFront Origin Shield: 캐시에 없는 같은 객체 요청을 합쳐, 원점에는 한 요청만 갈 수도 있다(AWS 문서).
- **계층 캐시 / shield**: 원점 앞 계층을 하나로 모아, 엣지 수와 상관없이 원점 미스를 줄인다.
- **stale 응답**: 원점이 느리거나 죽었을 때 옛 응답을 준다(`stale-while-revalidate`, `stale-if-error`).

### 5. 무효화 — 바뀐 것을 어떻게 내리나

```text
  방법                     동작                                  비용·위험
  TTL 만료 기다리기          아무것도 안 함                          반영이 TTL만큼 늦음
  버전 붙은 URL(해시 파일명)  app.3f9a1c.js -> app.7b20de.js         가장 안전. HTML만 짧게 캐시
  URL 퍼지                  특정 URL 삭제                           URL 목록을 빠짐없이 알아야
  태그 퍼지(Surrogate-Key)   태그로 묶인 객체 전부 삭제                태그 설계 필요
  소프트 퍼지                삭제 대신 "stale" 표시                   원점 폭주 완화
  전체 퍼지                  전부 삭제                               원점에 스탬피드
```

- Fastly `Surrogate-Key` 헤더는 응답에 태그를 붙인다. 그 키로 퍼지하면 연결된 객체가 모두 퍼지된다(Fastly 문서). 소프트 퍼지는 삭제 대신 "outdated"로 표시한다.
- RFC 9111 §4.4: 캐시는 unsafe 메서드(POST·PUT·DELETE)의 오류 아닌 응답(2xx·3xx)을 보면 그 대상 URI를 무효화해야 한다(MUST). 하지만 그 요청이 **지나간 캐시만** 무효화된다. 다른 엣지는 모른다. 그래서 CDN 무효화는 퍼지 API로 따로 한다.

### 6. 사용자는 어떻게 엣지에 닿나

```text
  www.example.com  --CNAME-->  example.cdn-provider.net  --DNS 응답-->  가까운 엣지 IP
                                            또는 같은 IP를 여러 PoP가 광고(애니캐스트)
```

- CDN마다 방식이 다르다. DNS 응답으로 가까운 엣지를 고르거나, 같은 IP를 여러 곳에서 BGP로 광고해 라우팅이 가까운 곳으로 보내게 한다(애니캐스트).
- 이 경로는 27번(DNS)·13번(BGP)에서 다룬다.

## 쓰이는 자료구조·알고리즘

- **계층 캐시(hierarchical cache)** — 각 층이 아래 층의 미스를 흡수한다. 전체 히트율 = 1 − (각 층 미스율의 곱)에 가깝다(층이 독립이라는 가정의 근사).
- **캐시 키 해시 → 해시 테이블 조회** — 키 문자열을 해시해 저장본을 찾는다. [05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **LRU 계열 축출** — 저장 공간이 차면 덜 쓰인 객체를 내보낸다. [10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **일관 해싱** — PoP 안의 여러 캐시 서버에 키를 나눠, 같은 객체가 한 서버에 모이게 한다. 서버가 빠져도 이동하는 키가 적다. 이 기법은 원래 웹 캐시의 핫스팟 문제를 풀려고 나왔다(Karger 외, STOC 1997). [31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
- **single-flight(요청 병합)** — 키별 진행 중 요청 표(맵 + 대기열)로 중복 미스를 합친다. [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md).
- **태그 → 객체 역색인** — 태그 퍼지를 위해 "태그 → 객체 키 집합"을 유지한다.

## 적용 — 풀어나가는 법

### 1. 응답을 네 부류로 나눈다

```text
  부류                          예                       정책(예시)
  불변 정적 자원                 app.3f9a1c.js, 이미지       public, max-age=31536000, immutable
  진입점 HTML                    index.html                 짧게 또는 no-cache(매번 재검증)
  공개 API                       /api/products              s-maxage=60, stale-while-revalidate
  개인화·인증 응답               /api/me, /account           private 또는 no-store
```

Spring MVC에서 헤더를 명시한다.

```java
@GetMapping("/api/products")
ResponseEntity<List<Product>> products() {
    return ResponseEntity.ok()
        .cacheControl(CacheControl.maxAge(Duration.ofSeconds(30))
            .sMaxAge(Duration.ofSeconds(300))              // CDN은 5분
            .staleWhileRevalidate(Duration.ofSeconds(60))
            .cachePublic())
        .body(productService.list());
}

@GetMapping("/api/me")
ResponseEntity<User> me(Principal p) {
    return ResponseEntity.ok()
        .cacheControl(CacheControl.noStore())             // 공유 캐시에 절대 남기지 않음
        .body(userService.find(p.getName()));
}
```

### 2. 캐시 키를 명시적으로 설계한다

- 넣을 것: 응답을 실제로 바꾸는 입력만. 예: `id`, 언어(`Accept-Language`를 정규화한 값), 압축 방식.
- 뺄 것: 추적용 쿼리(`utm_*`), 응답과 무관한 쿠키.
- 개인화 응답은 키에 사용자 식별자를 넣기보다 **캐시하지 않는** 쪽이 안전하다.

### 3. 헤더로 캐시 동작을 확인한다

```bash
# 두 번 요청해 상태 변화를 본다: MISS -> HIT, Age 증가
for i in 1 2; do
  curl -s -o /dev/null -D - https://www.example.com/app.js \
    | grep -i -E '^(cache-control|age|vary|cf-cache-status|x-cache|set-cookie)'
  echo ---
done

# 쿠키를 바꿔도 같은 본문이 오면, 쿠키가 키에 없다는 뜻이다 (개인화 페이지라면 사고)
curl -s -b 'session=A' https://www.example.com/account | sha256sum
curl -s -b 'session=B' https://www.example.com/account | sha256sum
```

- Cloudflare `cf-cache-status` 값 예: `HIT`, `MISS`, `EXPIRED`(만료돼 원점에서 받음), `STALE`, `UPDATING`(뒤에서 갱신 중), `BYPASS`(원점 응답이 캐시 불가), `DYNAMIC`(캐시 대상 아님)(Cloudflare 문서).
- `Age`: 응답이 원점에서 생성(또는 재검증)된 뒤 지난 시간의 추정치(초)다(RFC 9111 §5.1).
  - 이 캐시에 저장된 시각이 기준이 아니다. 상위 캐시(shield)에 머문 시간과 전송 지연도 들어간다(§4.2.3). 그래서 엣지에 방금 들어온 응답도 `Age`가 클 수 있다.

### 4. 배포와 무효화를 묶는다

```text
  1. 정적 자원은 해시 파일명으로 빌드한다 (새 이름 = 새 캐시 키, 퍼지 불필요)
  2. 새 자원을 먼저 올린다
  3. HTML을 배포한다 (짧은 TTL 또는 no-cache)
  4. 필요하면 HTML·API만 URL/태그 퍼지 (전체 퍼지는 피한다)
```

## 장애 시나리오와 대처

### 1. 캐시 키에 쿠키·쿼리 누락 → 개인화 페이지 교차 노출

- **현상**: 사용자 A가 로그인했는데 B의 이름·주문 내역이 보인다는 신고가 들어온다.
- **보이는 형태**
  - 문제 응답에 `cf-cache-status: HIT` 같은 캐시 히트 표시와 `Age > 0`이 있다.
  - 쿠키를 바꿔 요청해도 같은 본문 해시가 나온다.
  - 원점 응답에 `Cache-Control: private`/`no-store`가 없다.
- **원인**
  - CDN 규칙(예: "모든 것을 캐시")이 개인화 경로까지 캐시했다. 캐시 키에는 쿠키가 없다.
  - RFC 9111 §7.3: `Set-Cookie`가 있어도 캐시는 막히지 않는다. 캐시 가능한 응답은 `Set-Cookie`가 있어도 재사용될 수 있다. 원점이 `Cache-Control`로 막아야 한다.
  - 일부 CDN·프록시는 `Set-Cookie` 응답을 기본적으로 캐시하지 않는다(Cloudflare 기본 동작, nginx 문서). 이 기본값에 기대면, 규칙 하나로 깨진다.
- **대처**
  - 즉시: 해당 경로 퍼지 + CDN 규칙에서 개인화 경로 제외.
  - 원점: 개인화 응답에 `Cache-Control: private` 또는 `no-store`를 항상 붙인다.
  - 사고 규모를 로그로 추적한다(어느 응답이 누구에게 나갔나).

### 2. 퍼지 누락 → 배포했는데 옛 화면·옛 데이터

- **현상**: 배포 후 일부 사용자에게 옛 화면이 보인다. 새 JS가 옛 HTML과 섞여 깨지기도 한다.
- **보이는 형태**
  - HTML 응답의 `Age`가 배포 시각보다 오래됐다.
  - HTML이 가리키는 자원 이름이 옛 해시다. 또는 같은 이름의 JS가 PoP마다 다르다.
- **원인**
  - HTML에 긴 TTL을 주고 퍼지를 빠뜨렸다.
  - 파일명을 버전 없이 쓰면서(`app.js`) 일부 URL만 퍼지했다.
- **대처**
  - 정적 자원은 해시 파일명 + 긴 TTL, HTML은 짧은 TTL로 역할을 나눈다.
  - 배포 파이프라인에 퍼지 단계를 넣는다. 태그 퍼지로 "이 배포에 속한 것"을 한 번에 내린다.

### 3. 전체 퍼지 또는 동시 만료 → 원점 스탬피드

- **현상**: "전체 퍼지" 직후 원점 CPU·DB 부하가 급등하고 5xx가 난다.
- **보이는 형태**
  - CDN 미스율 급등, 원점 요청 수 급등.
  - 원점 5xx → CDN이 사용자에게 502/504를 준다.
- **원인**: 모든 엣지가 동시에 비었다. 인기 객체마다 엣지 수만큼 원점 요청이 몰린다.
- **대처**
  - 전체 퍼지 대신 URL·태그 퍼지. 가능하면 소프트 퍼지(stale 표시)로 옛것을 주며 갱신한다.
  - 요청 병합(`proxy_cache_lock`, Origin Shield)과 계층 캐시를 켠다.
  - `stale-while-revalidate`·`stale-if-error`로 원점 부담을 뒤로 미룬다.

### 4. 웹 캐시 속임(web cache deception)

- **현상**: 공격자가 피해자에게 `https://site/account/profile/x.css` 같은 링크를 누르게 한다. 그 뒤 같은 URL로 피해자의 계정 페이지를 받아 간다.
- **보이는 형태**: 확장자가 정적 자원인 URL에 HTML 계정 페이지가 캐시 HIT로 나간다.
- **원인**
  - 캐시는 "`.css`로 끝나니 정적 자원"으로 보고 캐시한다.
  - 원점은 경로 뒤를 무시하고 계정 페이지를 준다. 두 해석의 차이다(PortSwigger).
- **대처**
  - 동적 응답에 `Cache-Control: no-store`·`private`를 붙이고, CDN이 이를 존중하게 설정한다.
  - 확장자와 `Content-Type`이 다르면 캐시하지 않는 CDN 보호 기능을 켠다.
  - 원점이 알 수 없는 경로 접미사를 404로 거절하게 한다.

### 5. 추적 쿼리·헤더가 키에 들어가 히트율 붕괴

- **현상**: 마케팅 캠페인을 시작하자 원점 트래픽이 몇 배가 된다.
- **보이는 형태**: 같은 페이지 URL에 `utm_source=...`가 제각각 붙고, 전부 MISS다.
- **원인**: 캐시 키에 쿼리 전체가 들어간다. 추적 값이 다를 때마다 다른 객체가 된다.
- **대처**: 캐시 키에서 추적 파라미터를 뺀다. 쿼리 정렬·정규화 규칙을 둔다.

## 핵심 문장

- CDN은 사용자 가까운 공유 캐시(엣지)와 상위 계층·origin shield로 원점 요청을 줄인다. 계층이 깊을수록 원점 미스가 모인다.
- 캐시 키는 최소 메서드 + URI에 Vary가 지목한 요청 헤더를 더한 것이다. 쿠키는 기본 키에 없으므로, 개인화 응답은 원점이 `private`/`no-store`로 막아야 한다.
- `Set-Cookie`는 캐시를 막지 않는다(RFC 9111 §7.3). CDN 기본값이 막아 주는 것에 기대면 규칙 하나로 교차 노출 사고가 난다.
- 무효화의 기본은 버전 붙은 URL이다. 퍼지는 URL·태그 단위로 하고, 전체 퍼지는 원점 스탬피드를 부른다.
- 원점 보호는 요청 병합, 계층 캐시, stale 응답(`stale-while-revalidate`, `stale-if-error`) 세 가지로 한다.

## 관련 주제·근거

- 선행
  - [34-http-caching](../34-http-caching/2-summary.md) — `Cache-Control`·`ETag`·`Vary`
  - [46 로드밸런서·프록시](../46-load-balancers-and-proxies/2-summary.md) — 원고 [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md) (「CDN / 엣지」 절 포함)
- 후속·연결
  - [45-adaptive-media-streaming](../45-adaptive-media-streaming/2-summary.md) — 세그먼트 전달
  - [systems/server-design/04-caching.md](../../systems/server-design/04-caching.md) — 캐시 계층·스탬피드
  - [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md) — 요청 병합
  - [issue/cross-cutting/network/http-cache-policy](../../../issue/cross-cutting/network/http-cache-policy/2-summary.md)
- RFC 9111 HTTP Caching <https://www.rfc-editor.org/rfc/rfc9111>
  - §2 캐시 키 · §4.1 Vary · §4.2.2 휴리스틱 신선도 · §4.4 무효화 · §5.1 Age · §5.2.2.7 private · §5.2.2.10 s-maxage · §7.1 캐시 오염 · §7.3 민감 정보 캐시(`Set-Cookie`)
- RFC 5861 stale-while-revalidate·stale-if-error <https://www.rfc-editor.org/rfc/rfc5861>
- RFC 9213 Targeted HTTP Cache Control(`CDN-Cache-Control`) <https://www.rfc-editor.org/rfc/rfc9213>
- Cloudflare 문서: Cache keys · Tiered Cache · Default cache behavior · Cache responses(`cf-cache-status`) <https://developers.cloudflare.com/cache/>
- AWS CloudFront "Use Amazon CloudFront Origin Shield" <https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html>
- Fastly "Working with surrogate keys" <https://www.fastly.com/documentation/guides/full-site-delivery/purging/working-with-surrogate-keys/>
- nginx `ngx_http_proxy_module`(`proxy_cache_key`, `proxy_cache_lock`, `Set-Cookie` 응답 미캐시) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
- PortSwigger Web Security Academy "Web cache deception" <https://portswigger.net/web-security/web-cache-deception>
- Karger 외, "Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web", STOC 1997
