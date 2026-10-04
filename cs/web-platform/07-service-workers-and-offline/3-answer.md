# web-platform/07-service-workers-and-offline — 정답

## 정답

### 1. 왜 서비스 워커인가

- HTTP 캐시는 서버 헤더와 브라우저 정책이 정한다. 앱 코드는 `fetch()`의 `cache` 옵션 정도만 고를 수 있고, 응답을 직접 골라 줄 수 없다. 네트워크가 끊기면 HTTP 캐시에 재사용 가능한 사본이 없는 한 내비게이션이 실패한다.
- 서비스 워커는 범위 안 요청을 `fetch` 이벤트로 가로채, 캐시에서 줄지 네트워크로 갈지 앱 코드가 정한다. 그래서 오프라인 페이지를 만들 수 있다.
- 새 책임: 옛 응답을 언제 버릴지(캐시 무효화), 새 워커로 언제 넘어갈지(갱신 흐름), 캐시 용량 관리. Cache Storage에는 만료가 없다.

### 2. 상태와 전이

```text
  parsed → installing → installed(waiting) ──▶ activating → activated
                │                 ▲  조건 ① 옛 워커가 제어하는 클라이언트 0개
                │                 │  조건 ② skipWaiting()
                └ install 실패 ───┴──────────▶ redundant (밀려난 옛 워커도 redundant)
```

- 기존 활성 워커가 없으면 대기 없이 바로 activating으로 간다.
- ①·② 모두 옛 워커에 처리 중인 이벤트가 없어야 넘어간다(표준 Try Activate).

### 3. 첫 방문 페이지

- `controller`는 `null`(실험 1: `controlled=false`). 페이지와 그 요청은 워커가 생기기 전에 이미 처리됐다.
- 새로고침 뒤에는 그 내비게이션부터 워커가 처리해 `controlled=true`(실험 2).
- `clients.claim()`을 쓰면 활성화 시 이미 열린 페이지도 넘겨받는다.

### 4. 배포·다운 결과

```text
cache-first   3 서버에 v2 배포 후 새로고침: APP=v1 ...
              4 서버 다운(오프라인) 새로고침: ok APP=v1 ...
network-first 3 서버에 v2 배포 후 새로고침: APP=v2 ...
              4 서버 다운(오프라인) 새로고침: ok APP=v2 ...
```

- cache-first: v1. 같은 URL을 캐시에서 꺼낸다. 다운이어도 v1로 열린다.
- network-first: v2. 다운이면 네트워크 실패 → 캐시 폴백으로 마지막에 받은 v2.

### 5. sw.js의 HTTP 캐시

- 못 보는 것이 아니다. `updateViaCache` 기본값 `imports`에서 메인 워커 스크립트 요청은 캐시 모드 `no-cache`라, `max-age`가 남아 있어도 서버에 재검증한다(`304`면 캐시 본문 재사용).
- 실험: 새로고침 뒤 0.5초 시점에는 `sw.js` 요청 0회, 3초 더 기다리자 1회 → 새 워커 `waiting=installed`. Chromium은 내비게이션 직후 바로 확인하지 않고 조금 미룬다(현재 main 소스 `ServiceWorkerContext::kUpdateDelay` = 1000ms, 다시 예약되면 타이머 재시작).

### 6. waiting 유지와 활성화

```text
6 한 번 더 새로고침(탭 1개 유지): APP=v1 ... waiting=installed
7 탭을 닫고 새로 열기      : APP=v2 ... waiting=-
```

- 새로고침으로는 안 된다. 새로고침 동안 옛 페이지와 새 페이지가 겹쳐 옛 워커의 클라이언트가 0이 되지 않는다.
- 탭을 닫으면 클라이언트가 0이 되어 활성화된다. 새 워커가 install 때 v2를 사전 캐시했으므로 v2가 뜬다.

### 7. skipWaiting + claim의 한 박자 늦음

```text
8 sw3(skipWaiting+claim) 배포 후 새로고침: APP=v2 ...
9 한 번 더 새로고침        : APP=v3 ...
```

- 8의 화면은 v2(옛 버전). 그 내비게이션은 갱신 확인보다 먼저 옛 워커(sw2)가 캐시로 처리했다. 확인은 내비게이션 뒤에 일어나고, 그때 sw3이 설치·즉시 활성화됐다.
- 9에서 sw3이 처리해 v3.

### 8. 전략 배정

- 해시 파일명 JS → cache-first(사전 캐시).
- HTML → network-first(시간 제한 + 캐시 폴백).
- 아바타 이미지(해시 없음) → stale-while-revalidate.
- 결제 API → network-only.
- 기준: **같은 URL의 내용이 바뀔 수 있으면 캐시를 먼저 믿지 않는다.**

### 9. addAll 실패로 설치 실패

```text
(실험) page addAll: TypeError: Failed to execute 'addAll' on 'Cache': Request failed
       cache t 항목 수=0
       sw state → redundant, registration.active=null
```

- 원인: 사전 캐시 목록에 404 URL이 있었다. `addAll`은 하나라도 실패하면 전체 거부, `install`의 `waitUntil`이 거부되어 워커가 `redundant`.
- 캐시에는 정상 URL(`/`)도 안 들어갔다(항목 0개).
- 대처: 사전 캐시 목록을 빌드 산출물에서 자동 생성하고, 배포 전 각 URL을 검증한다.

### 10. 일부 사용자만 옛 화면

- 확인: DevTools Network 탭에서 HTML·JS 응답이 `(ServiceWorker)`인지, 서버 접근 로그에 그 사용자의 HTML 요청이 오는지, Application → Service workers에 waiting 워커가 있는지. `chrome://serviceworker-internals`.
- 당장: 새 워커에서 옛 캐시 삭제 + 갱신 배너로 `skipWaiting`. 심하면 해제용 워커(`registration.unregister()`)나 `Clear-Site-Data: "cache", "storage"` 응답.
- 재발 방지: HTML은 network-first, 정적 자원은 해시 파일명 + cache-first, 캐시 이름에 버전, `sw.js`는 `Cache-Control: no-cache`.
