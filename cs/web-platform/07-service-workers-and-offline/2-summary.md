# web-platform/07-service-workers-and-offline — 서비스 워커 수명과 캐시 전략 — 정리 (힌트)

## 해결하는 문제

웹 페이지는 네트워크가 없으면 보통 열리지 않는다(HTTP 캐시에 재사용 가능한 사본이 있으면 열릴 수도 있다). HTTP 캐시의 동작은 서버 헤더와 브라우저가 정한다. 앱 코드는 `fetch()`의 `cache` 옵션으로 요청별 캐시 사용 방식 정도만 고를 수 있고, 응답을 직접 골라 만들어 줄 수는 없다.

```text
  서비스 워커 없음                         서비스 워커 있음
  ─────────────────                       ──────────────────────────────────
  페이지 ──▶ HTTP 캐시 ──▶ 네트워크          페이지 ──▶ [서비스 워커 fetch 핸들러] ──▶ Cache Storage
            (헤더가 정함)                                 │  (앱 코드가 정함)          └─▶ 네트워크
  오프라인이면 보통 "인터넷 연결 없음"         오프라인이어도 캐시에서 페이지를 줄 수 있다
```

- *서비스 워커(service worker)*: 페이지와 별도로 도는 이벤트 기반 워커. 자기 범위(scope) 안의 페이지가 내는 요청을 `fetch` 이벤트로 가로챈다.
  - *범위(scope)*: 기본은 워커 스크립트가 있는 경로. `/sw.js`면 사이트 전체.
- 앱이 "이 요청은 캐시 먼저, 저 요청은 네트워크 먼저"를 코드로 정할 수 있다.

쉬운 예: 회사 비서다.
- 사장(페이지)이 "그 서류 가져와"라고 하면 비서(서비스 워커)가 받는다.
- 비서는 서랍(캐시)에서 꺼내 줄지, 본사(서버)에 새로 받으러 갈지 스스로 정한다.
- 본사가 문을 닫아도 서랍에 사본이 있으면 일은 계속된다.

똑같은 구조다.\
대신 **서랍의 옛 서류를 계속 꺼내 주는 문제**가 생긴다. 이것이 "배포했는데 구 버전이 뜬다"다.

실무 예:
- 지하철에서도 열리는 뉴스·문서 앱(PWA).
- 새 버전을 배포했는데 일부 사용자는 며칠째 옛 화면을 본다. 캐시를 지우라고 안내해야 했다.

## 동작·원리

### 1. 등록과 수명

```text
  register('/sw.js')
       │ 스크립트 다운로드·파싱                         (상태: parsed)
       ▼
  install 이벤트 ── 사전 캐시(precache) ──▶ 실패하면 이 워커는 버려진다   (installing)
       │ 성공
       ▼
  기존 활성 워커가 있고, 그 워커가 제어하는 클라이언트가 남아 있나?
       ├─ 예 → 대기(waiting)                                       (installed)
       │        └ 그 클라이언트가 0이 되거나 skipWaiting() 하면 ↓
       └─ 아니오 ↓
  activate 이벤트 ── 옛 캐시 정리                                   (activating)
       ▼
  활성(active) ── fetch·push 등 이벤트 처리                          (activated)
  (새 버전에 밀려나거나 설치 실패하면 redundant)
```

- 상태 값은 W3C Service Workers 표준 §2.1의 `parsed`·`installing`·`installed`·`activating`·`activated`·`redundant`다.
- **처음 방문한 페이지는 제어되지 않는다.** 워커는 등록 뒤에 생기므로 그 페이지의 요청은 이미 나갔다. 다음 내비게이션부터 제어된다. `clients.claim()`을 쓰면 활성화 즉시 열린 페이지를 넘겨받는다(web.dev "The service worker lifecycle").
  - *클라이언트(client)*: 워커가 제어하는 창·탭·워커.
- 서비스 워커는 보안 컨텍스트(HTTPS, 또는 `localhost`·`127.0.0.1` 같은 잠재적 신뢰 출처)에서만 등록된다(표준 §6.1, W3C Secure Contexts).

### 2. 갱신 — 언제 새 워커를 알아채나

```text
  배포: sw.js 내용 변경
     │
  사용자가 범위 안 페이지로 이동 ──(브라우저가 잠시 뒤)──▶ sw.js 다시 받기
     │                                                      │ HTTP 캐시 신선도 무시·서버 재검증(updateViaCache 기본 'imports')
     ▼                                                      ▼
  기존 워커가 이 내비게이션을 처리                    바이트가 다르면 새 워커 install
  (= 이번 화면은 옛 캐시 기준)                        → 탭이 열려 있으면 waiting
```

- 갱신 확인 시점: 범위 안 내비게이션, `push`·`sync` 같은 기능 이벤트(24시간 안에 확인했으면 생략), 다른 URL로 `register()`할 때(web.dev).
- 비교: 새로 받은 워커 스크립트(가져온 스크립트 포함)가 **바이트 단위로 다르면** 갱신이다.
- `updateViaCache` 기본값은 `imports`다(표준 §2.3). 이때 메인 워커 스크립트 요청의 캐시 모드는 `no-cache`다(표준 Update 알고리즘). `max-age`가 남아 있어도 서버에 확인(재검증)한다는 뜻이다. 서버가 `304`를 주면 캐시된 본문을 다시 쓸 수 있다. 아래 실험 5에서 `Cache-Control: max-age=86400`을 준 `sw.js`도 서버에 요청이 갔다(검증자 헤더가 없는 서버라 본문을 다시 받았다).
- 마지막 확인이 86400초(24시간)보다 오래되면 등록이 *stale*로 간주된다(§2.3).
- **새로고침 한 번으로는 새 워커가 활성화되지 않는다.** 새로고침 동안 옛 페이지와 새 페이지가 겹쳐, 옛 워커가 제어하는 클라이언트가 0이 되지 않는다(web.dev). 실험 6이 이것이다.
- Chromium은 내비게이션 직후 바로 확인하지 않고 잠시 미룬다. 현재 main 소스에서 `ServiceWorkerVersion::ScheduleUpdate()`(`content/browser/service_worker/service_worker_version.cc`)는 `ServiceWorkerContext::kUpdateDelay`만큼 타이머를 걸고, 타이머가 돌고 있으면 `Reset()`으로 다시 건다. 그 값은 `base::Milliseconds(1000)`이다(`content/public/browser/service_worker_context.h`). Chromium 66판도 1초였다. 실험에서는 새로고침 0.5초 안에 요청 0회, 3.5초 안에 1회였다.

### 3. 캐시 전략

```text
  cache-first           network-first              stale-while-revalidate
  ────────────          ──────────────             ──────────────────────
  캐시 있음 → 캐시        네트워크 성공 → 응답+캐시 갱신   캐시를 즉시 응답
  없음 → 네트워크         실패 → 캐시                  뒤에서 네트워크로 캐시 갱신
  빠름·오프라인 강함      최신 우선·오프라인 폴백         빠름·한 번 늦게 최신
  ⚠ 갱신을 못 봄          ⚠ 느린 망에서 대기             ⚠ 이번 응답은 옛 것
```

- 그 밖에 cache-only, network-only가 있다(Workbox strategies 문서).
- 고르는 기준: **내용이 바뀔 수 있는 URL인가.**
  - 파일명에 해시가 든 자원(`app.3f9a.js`): 내용이 바뀌면 URL이 바뀐다 → cache-first가 안전하다.
  - HTML·API·해시 없는 `app.js`: 같은 URL에 새 내용 → network-first 또는 stale-while-revalidate.
- *Cache Storage*: `caches.open(name)`으로 여는 Request→Response 저장소. HTTP 캐시와 별개이고, **만료가 없다**. 앱이 지우기 전까지 남는다(출처 쿼터·축출 대상, 06번).

### 실험: cache-first vs network-first, 그리고 갱신 수명

127.0.0.1 Node 서버가 `/`(HTML), `/app.js`(`window.APP='v1'`), `/sw.js`를 준다. 서버 상태를 바꿔 "배포"(`app.js`를 v2로)와 "서버 다운"(소켓 끊기)을 흉내 냈다. 워커는 install에서 `/`와 `/app.js`를 사전 캐시한다.

```js
// exp07-sw.js가 내보내는 sw.js (전략 부분)
// cache-first
e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
// network-first
e.respondWith(fetch(e.request)
  .then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return r; })
  .catch(() => caches.match(e.request)));
// ⚠ 실험용으로 짧게 썼다: put을 기다리지 않아 저장 완료가 보장되지 않는다.
//   실서비스는 e.waitUntil(cache.put(...))로 저장을 워커 수명에 묶는다(표준 ExtendableEvent).
// activate: CACHE 이름이 아닌 캐시 삭제. sw3에서만 install에 skipWaiting(), activate에 clients.claim()
// sw.js 응답 헤더: Cache-Control: max-age=86400
```

(실험, headless Chrome 151.0.7922.173, Playwright 컨텍스트 전략별 새로 생성, 2026-10-04 — 집필 3회·사실 점검 재실행 2회 모두 같은 출력)

```text
=== cache-first
1 첫 방문(v1 배포)        : APP=v1 controlled=false active=activated waiting=-
2 새로고침                : APP=v1 controlled=true active=activated waiting=-
3 서버에 v2 배포 후 새로고침: APP=v1 controlled=true active=activated waiting=-
4 서버 다운(오프라인) 새로고침: ok APP=v1 controlled=true active=activated waiting=-
5 sw.js 를 sw2 로 바꿈(max-age=86400) 새로고침 +0.5s: sw.js 요청 0회, APP=v1 controlled=true active=activated waiting=-
5b 같은 페이지에서 3초 더 대기: sw.js 요청 1회, APP=v1 controlled=true active=activated waiting=installed
6 한 번 더 새로고침(탭 1개 유지): APP=v1 controlled=true active=activated waiting=installed
7 탭을 닫고 새로 열기      : APP=v2 controlled=true active=activated waiting=-
8 sw3(skipWaiting+claim) 배포 후 새로고침: APP=v2 controlled=true active=activated waiting=-
9 한 번 더 새로고침        : APP=v3 controlled=true active=activated waiting=-
=== network-first
1 첫 방문(v1 배포)        : APP=v1 controlled=false active=activated waiting=-
2 새로고침                : APP=v1 controlled=true active=activated waiting=-
3 서버에 v2 배포 후 새로고침: APP=v2 controlled=true active=activated waiting=-
4 서버 다운(오프라인) 새로고침: ok APP=v2 controlled=true active=activated waiting=-
```

관찰과 해석:
- 1→2: 첫 방문은 `controlled=false`. 다음 내비게이션부터 제어된다.
- 3: **cache-first는 서버가 v2인데도 v1을 줬다.** 같은 URL `/app.js`를 캐시에서 꺼냈기 때문이다. network-first는 v2.
- 4: 서버가 끊겨도 두 전략 모두 페이지가 열렸다. network-first는 실패 뒤 캐시로 폴백해 마지막으로 받은 v2를 줬다.
- 5·5b: `sw.js`에 `max-age=86400`을 줬어도 갱신 확인 요청이 서버에 갔다(`max-age` 무시·재검증). 다만 새로고침 직후가 아니라 0.5~3.5초 사이에 갔다.
- 6: 새 워커(sw2)는 `waiting`에 머물렀다. 새로고침으로는 활성화되지 않는다.
- 7: 탭을 닫고 새로 열자 sw2가 활성화됐다. sw2는 install 때 서버의 v2 `app.js`를 사전 캐시했으므로 v2가 떴다.
- 8→9: `skipWaiting`+`claim`을 넣은 sw3은 대기 없이 활성화됐다. 그래도 8의 화면은 v2다. 그 내비게이션은 갱신 확인 **전에** 옛 워커가 처리했다. 한 번 더 이동해야 v3이 보인다.

## 쓰이는 자료구조·알고리즘

- **캐시 저장소** = 이름 붙은 맵의 맵: `cacheName → (Request 키 → Response)`. `match`는 URL(+옵션에 따라 `Vary`)로 찾는다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **워커 수명 상태 기계**: parsed → installing → installed(waiting) → activating → activated → redundant. waiting → activating 전이 조건은 "기존 활성 워커 없음", 또는 "옛 워커에 처리 중 이벤트가 없고 + (제어 중 클라이언트 수 = 0 또는 `skipWaiting()`)"이다(표준 Try Activate).
- **버전 비교** = 바이트 단위 동등 비교. 파일명 해시(내용 주소화)와 짝을 이룬다.
- **캐시 무효화** = 캐시 이름에 버전을 넣고 activate에서 옛 이름 삭제. HTTP 캐시 무효화 원리는 [network/34-http-caching](../../network/34-http-caching/2-summary.md), CDN 쪽은 [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 자원 종류별 전략 표를 먼저 정한다

| 자원 | 전략 | 이유 |
|---|---|---|
| HTML(앱 셸 포함) | network-first(시간 제한 + 캐시 폴백) | 새 배포를 바로 반영 |
| 해시 파일명 JS·CSS·폰트 | cache-first(사전 캐시) | URL이 곧 버전 |
| 해시 없는 이미지·아바타 | stale-while-revalidate | 빠름, 한 박자 늦은 최신 |
| 인증·결제 API | network-only | 옛 응답을 주면 안 됨 |

### 2. 갱신 흐름을 설계한다 — "새 버전이 있습니다"

```js
// 페이지
const reg = await navigator.serviceWorker.register('/sw.js');
reg.addEventListener('updatefound', () => {
  const nw = reg.installing;
  nw.addEventListener('statechange', () => {
    if (nw.state === 'installed' && navigator.serviceWorker.controller) {
      showBanner('새 버전이 있습니다', () => nw.postMessage({ type: 'SKIP_WAITING' }));
    }
  });
});
navigator.serviceWorker.addEventListener('controllerchange', () => location.reload());

// sw.js
self.addEventListener('message', e => { if (e.data?.type === 'SKIP_WAITING') self.skipWaiting(); });
```

- 사용자가 동의할 때 `skipWaiting` → `controllerchange` → 새로고침. 작성 중인 폼이 날아가지 않게 한다.
- 무조건 `skipWaiting`은 옛 페이지가 새 워커의 캐시(옛 청크가 지워진)로 요청하는 혼합 상태를 만들 수 있다(09번 `ChunkLoadError`와 연결).

### 3. 배포 체크리스트

1. `sw.js`는 해시 없는 고정 URL. 서버에서 `Cache-Control: no-cache`(기본 `updateViaCache`가 메인 스크립트의 `max-age`를 무시하고 재검증해도, `importScripts`·모듈 의존은 다르다).
2. 캐시 이름에 빌드 버전. activate에서 옛 캐시 삭제.
3. HTML을 cache-first로 두지 않는다.
4. 비상 해제 수단을 미리 둔다: 아무것도 안 하는 워커 배포(`self.registration.unregister()`) 또는 응답 헤더 `Clear-Site-Data: "cache", "storage"`.

### 4. 진단

- DevTools Application → Service workers: 상태(activated·waiting), "Update on reload", "Bypass for network", skipWaiting 버튼.
- Application → Cache storage: 캐시 이름과 항목.
- Network 탭 Size 열의 `(ServiceWorker)` 표시.
- `chrome://serviceworker-internals`: 브라우저에 있는 등록 목록과 상태, 로그.

## 장애 시나리오와 대처

### 1. 배포해도 구 버전이 계속 뜸 (⚠ SW 캐시 고착)

- **현상**: 새 기능을 배포했는데 일부 사용자는 며칠째 옛 화면.
- **보이는 형태**: Network 탭에서 HTML·JS가 `(ServiceWorker)`로 응답. 서버 접근 로그에 그 사용자의 HTML 요청이 없다.
- **원인**: HTML이나 해시 없는 `app.js`를 cache-first로 줬다(실험 3). 새 워커를 배포해도 탭이 열려 있으면 waiting에 머문다(실험 6).
- **대처**: HTML은 network-first, 정적 자원은 해시 파일명 + cache-first. 갱신 배너 + `skipWaiting`. 급하면 해제용 워커나 `Clear-Site-Data`.

### 2. install 실패로 갱신이 영영 안 됨

- **현상**: 새 워커가 나타났다 사라진다(`redundant`). 옛 워커가 계속 제어한다.
- **보이는 형태**: Application 패널에 오류, 콘솔 `Uncaught (in promise) TypeError: Failed to execute 'addAll' on 'Cache': Request failed`.
- **원인**: 사전 캐시 목록에 404인 URL이 있었다. `cache.addAll`은 하나라도 실패하면 전체가 거부되고, `waitUntil`이 거부되면 설치가 실패한다.
  - 재현(실험, headless Chrome 151): 목록 `['/', '/missing.js']`(뒤는 404) → `TypeError: Failed to execute 'addAll' on 'Cache': Request failed`, 캐시 항목 0개(`/`도 안 들어감), 워커 상태 `redundant`, `registration.active=null`.
- **대처**: 빌드 도구가 사전 캐시 목록을 생성(Workbox precache manifest 등). 배포 전 목록 URL 검증.

### 3. 오프라인에서 흰 화면

- **현상**: 비행기 모드에서 앱이 "인터넷 연결 없음"을 보인다.
- **보이는 형태**: `controlled=false` 또는 내비게이션 요청이 워커 캐시에 없다.
- **원인**: 오프라인이 되기 전에 워커가 아직 활성화되지 않았다(install 중이거나 install 실패). 첫 방문 페이지 자체는 `controlled=false`지만(실험 1), 워커가 활성화됐다면 다음 내비게이션(오프라인 새로고침 포함)부터 제어된다(실험 2·4). 또는 HTML을 캐시하지 않았다. 또는 network-first에 시간 제한이 없어 끊긴 망(응답 없는 연결)에서 오래 기다렸다.
- **대처**: 앱 셸 HTML을 사전 캐시, 필요하면 `clients.claim()`. network-first에 시간 제한(예: `AbortSignal.timeout`)을 두고 넘으면 캐시.

### 4. 캐시가 계속 커져 쿼터 초과

- **현상**: 일정 시간 쓰면 오프라인 저장이 실패한다.
- **보이는 형태**: `cache.put`이 `QuotaExceededError`로 거부. Application → Storage 사용량 증가.
- **원인**: Cache Storage에는 만료가 없다. 런타임 캐시가 URL 쿼리마다 항목을 쌓았다.
- **대처**: 캐시별 항목 수·나이 상한(Workbox expiration 플러그인 등), 쿼리 정규화, activate에서 옛 캐시 삭제.

### 5. 인증·개인 데이터가 캐시에 남음

- **현상**: 로그아웃 뒤 다른 사용자가 같은 기기에서 이전 사용자의 화면 일부를 본다.
- **보이는 형태**: Cache storage에 `/api/me` 같은 응답.
- **원인**: 런타임 캐시가 인증 API까지 담았다.
- **대처**: 인증·개인 API는 network-only. 로그아웃 때 `caches.delete`.

## 핵심 문장

- 서비스 워커는 자기 범위 안 요청을 가로채는 프록시다. 캐시를 앱 코드가 정하므로 오프라인을 만들 수 있지만, 옛 응답을 계속 줄 위험도 앱 책임이 된다.
- 첫 방문 페이지는 제어되지 않는다. 새 워커는 옛 워커가 제어하는 탭이 모두 닫히거나 `skipWaiting()` 해야 활성화되고, 새로고침 한 번으로는 넘어가지 않는다.
- 갱신 확인은 바이트 비교이고 메인 워커 스크립트는 기본적으로 HTTP 캐시의 `max-age`를 무시하고 서버에 재검증한다. Chrome 151 실험에서 확인 요청은 내비게이션 뒤 0.5~3.5초 사이에 갔다.
- cache-first는 URL이 곧 버전인 자원(해시 파일명)에, HTML·API는 network-first나 stale-while-revalidate에 쓴다.
- Cache Storage에는 만료가 없다. 캐시 이름에 버전을 넣고 activate에서 옛 캐시를 지운다.

## 관련 주제·근거

- 선행
  - [06-browser-storage](../06-browser-storage/2-summary.md) — 쿼터·축출, Cache Storage도 출처 쿼터를 쓴다
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — HTTP 캐시(서비스 워커 아래 계층)
- 후속·연결
  - [05-fetch-from-browser](../05-fetch-from-browser/2-summary.md) — fetch 이벤트 안에서 다시 fetch
  - [09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md) — 해시 파일명·`ChunkLoadError`
  - [23 `web-symptom-index`](../23-web-symptom-index/2-summary.md)("배포가 반영 안 됨")
  - [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md) · [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md)
- 표준·문서
  - W3C Service Workers <https://w3c.github.io/ServiceWorker/> — §2.1 상태 값, §2.3 updateViaCache 기본 `imports`·stale(86400초), Update 알고리즘(메인 스크립트 캐시 모드 `no-cache`), Try Activate(활성화 조건), ExtendableEvent `waitUntil`, §6.1 Secure Context
  - WHATWG Fetch <https://fetch.spec.whatwg.org/> — request cache mode(`no-cache` = 재검증, 앱이 `fetch(…, { cache })`로 지정)
  - W3C Secure Contexts <https://w3c.github.io/webappsec-secure-contexts/> — 잠재적 신뢰 출처(루프백)
  - web.dev "The service worker lifecycle" <https://web.dev/articles/service-worker-lifecycle> — 갱신 시점, 바이트 비교, 새로고침으로 활성화 안 됨, skipWaiting·clients.claim
  - Chrome for Developers, Workbox "Caching strategies"·"Precaching"·"Handling service worker updates" <https://developer.chrome.com/docs/workbox/>
  - Chromium main `content/browser/service_worker/service_worker_version.cc`(`ScheduleUpdate`)·`content/public/browser/service_worker_context.h`(`kUpdateDelay = base::Milliseconds(1000)`) <https://chromium.googlesource.com/chromium/src/+/main/content/public/browser/service_worker_context.h>, 66판 비교 <https://chromium.googlesource.com/chromium/src/+/66.0.3359.158/content/browser/service_worker/service_worker_version.cc>
  - W3C Clear Site Data <https://w3c.github.io/webappsec-clear-site-data/>
- 실험 목록
  - `exp07-sw.js` — Node 20.19.6 + playwright-core 1.62.1, headless Chrome 151.0.7922.173, 127.0.0.1 Node 서버(상태 플래그로 배포·다운 흉내). cache-first·network-first의 배포 후·서버 다운 결과, `sw.js`(max-age=86400) 갱신 확인 시점, waiting 유지와 탭 닫기 후 활성화, skipWaiting+claim 후 한 번 늦은 반영. 3회 실행 출력 동일.
  - `exp07-addall.js` — 같은 환경. 404가 섞인 `cache.addAll`의 오류·부분 저장 여부와, install의 `waitUntil` 거부 시 워커 상태.
