# cs/issue/network/http-cache-policy — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **max-age와 immutable.**\
   `max-age=N`은 "N초 동안은 캐시 사본을 신선하다고 봐도 된다"는 허락이다. 사용자가 새로고침하면 브라우저는 보통 조건부 요청(`If-None-Match` 등)으로 서버에 재검증을 보낸다.\
   `immutable`은 한 발 더 나가 "이 URL의 바이트는 **절대** 바뀌지 않는다"고 약속한다 — 만료 전에는 (일반) 새로고침에도 재검증을 생략할 수 있다(실제 처리는 브라우저마다 다르고, 캐시를 무시하는 강력 새로고침은 여전히 서버로 간다).\
   즉 immutable은 성능 힌트가 아니라 **URL과 바이트의 영구 대응에 대한 서버의 서약**이다.
   > **immutable** — 캐시된 응답이 유효 기간 동안 바뀌지 않으므로 재검증할 필요가 없다는 Cache-Control 확장.

2. **200일 때만.**\
   204는 본문이 없고 206은 범위 요청의 일부 바이트다. 여기에 7일 immutable이 붙으면 캐시가 "이 URL = 빈 본문/부분 본문"을 7일간 고정할 수 있다.\
   immutable이 약속하는 대상은 "이 URL의 완전한 정상 표현"이므로, 그 표현인 **200 OK 응답에만** 캐시 헤더를 부여한다.

3. **버전 없는 URL의 재적재.**\
   URL이 같으면 캐시는 바이트가 바뀐 줄 모른다. immutable 7일이면 이미 본 사용자는 **최대 7일** 옛 이미지를 본다.\
   콘텐츠 주소화 URL은 내용의 해시나 버전을 URL에 넣어 **내용이 바뀌면 URL이 바뀌게** 만든 것이다 — 그래야 "이 URL의 바이트는 안 바뀐다"가 참이 되고, immutable이 안전해진다.
   > **콘텐츠 주소화(content-addressed) URL** — 내용의 해시·버전이 경로에 들어가, 다른 내용이 같은 URL을 가질 수 없는 URL.

4. **배포와 클라이언트의 어긋남.**\
   해시 없는 정적 파일(`deploy.js`, `modal.css`)은 배포로 내용이 바뀌어도 URL이 같아서, 브라우저·프록시가 이전 응답을 재사용한다 → 서버는 새 버전인데 클라이언트는 구 로직으로 돈다(이 사건에선 새 완료 감지 로직이 적용되지 않아 "완료 확인 실패").\
   상태 엔드포인트가 캐시되면 폴링이 **옛 상태**를 보고 진행 판정이 멈추거나 틀린다.\
   두 경우 모두 서버 배포라는 사건이 클라이언트에 전달되지 않는 것이다.

5. **클라이언트 no-store vs 서버 정책.**\
   `fetch(url, { cache: 'no-store' })`는 **그 호출 하나**가 브라우저 HTTP 캐시를 쓰지 않게 할 뿐이다 — 다른 코드 경로, 다른 클라이언트, 중간 프록시는 여전히 캐시할 수 있다.\
   서버가 `Cache-Control: no-store`(또는 짧은 max-age + ETag 재검증)를 응답에 실으면 **그 응답을 받는 (규격을 따르는) 모든 캐시**가 따른다.\
   이 사건은 클라이언트 측 `no-store` + 하드 리프레시 안내로 막았고, 서버(리버스 프록시) 쪽 Cache-Control/ETag 정책은 후속 검토로 남겼다.

6. **리스크를 아는 예외.**\
   재적재가 드물고, 옛 이미지를 며칠 보는 비용이 작으며, 캐시로 얻는 부하 절감이 크다면 합리적이다.\
   정책 값이 **상수 한 곳**에 있어 되돌리기 쉽다는 점이 결정을 가볍게 만든다 — 틀렸다고 판명되면 한 줄 수정으로 복구된다(이미 배포된 캐시는 만료까지 남는다는 점은 감수).\
   중요한 것은 "모르고 쓴 immutable"이 아니라 **리스크를 기록한 결정**으로 남기는 것이다.

## 문제 구조 (추상화 코드)

### 변형 A — 상태코드와 URL 성질을 보지 않고 immutable 부여
① 문제 코드
```java
ResponseEntity<byte[]> imageProxy(String id) {
    ResponseEntity<byte[]> upstream = client.get("/images/" + id);   // URL에 버전 토큰 없음
    if (upstream.getStatusCode().is2xxSuccessful()) {                 // 204·206에도
        return ResponseEntity.status(upstream.getStatusCode())
            .header(CACHE_CONTROL, "max-age=604800, immutable")      // 7일
            .body(upstream.getBody());
    }
    // ...
}
```
② 고친 코드
```java
static final String IMG_CACHE_HEADER = "max-age=604800, immutable";   // 상수 1곳 — 되돌리기 쉬움

ResponseEntity<byte[]> imageProxy(String id) {
    ResponseEntity<byte[]> upstream = client.get("/images/" + id);
    BodyBuilder b = ResponseEntity.status(upstream.getStatusCode());
    if (upstream.getStatusCode().value() == 200) {                     // 정상 전체 응답만
        b.header(CACHE_CONTROL, IMG_CACHE_HEADER);
    }
    return b.body(upstream.getBody());
}
// 버전 없는 URL + immutable은 리스크 기록 후 유지 결정 (근본 해결 = URL에 버전 토큰)
```
무엇이 깨졌나: "성공"과 "영구 불변 표현"을 같은 것으로 보고, 바뀔 수 있는 URL에 불변 약속을 붙였다.\
같은 구조: 해시 없는 공개 CSS가 프록시에 캐시되면 스타일 수정이 반영되지 않을 수 있음 → 배포 후 강제 새로고침으로 확인.

### 변형 B — 해시 없는 스크립트·상태 API가 캐시돼 배포가 클라이언트에 안 닿음
① 문제 코드
```html
<script src="/static/deploy.js"></script>          <!-- 배포해도 같은 URL → 구버전 재사용 -->
<script type="module">                          <!-- 최상위 await는 모듈 스크립트에서만 -->
  const s = await (await fetch('/api/agent-status')).json();   // 상태도 캐시될 수 있음
</script>
```
② 고친 코드
```html
<script src="/static/deploy.js"></script>          <!-- 당장은 하드 리프레시 안내, 후속: 서버 캐시 정책 -->
<script type="module">
  const s = await (await fetch('/api/agent-status', { cache: 'no-store' })).json();
</script>
```
무엇이 깨졌나: 캐시 정책을 정하지 않은 자원이 브라우저 기본 휴리스틱에 맡겨져 서버 배포와 클라이언트 로직이 어긋났다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
