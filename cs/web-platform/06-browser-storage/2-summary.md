# web-platform/06-browser-storage — 브라우저 저장소: 쿠키·localStorage·IndexedDB·쿼터·축출 — 정리 (힌트)

## 해결하는 문제

HTTP는 요청마다 따로다. 페이지를 새로 열면 메모리의 JS 변수는 사라진다. 그래도 남겨야 하는 것이 있다.

```text
  남겨야 하는 것                      누가 읽나            어디에 두나(대표)
  ─────────────────────────────     ──────────────     ─────────────────────
  로그인 세션 식별자                  서버               쿠키 (HttpOnly)
  화면 설정(테마·언어)                 페이지 스크립트      localStorage
  오프라인 편집 중인 문서·대량 목록      페이지 스크립트      IndexedDB
  오프라인용 응답 사본                 서비스 워커         Cache Storage (07번)
```

- 저장소마다 **누가 읽을 수 있나, 동기인가, 얼마나 담나, 언제 지워지나**가 다르다. 이 넷을 틀리게 고르면 보안 사고·화면 멈춤·데이터 유실이 난다.

쉬운 예: 집의 보관 장소다.
- 지갑(쿠키): 작고, 나갈 때마다 자동으로 들고 간다(요청마다 서버로 간다).
- 현관 메모판(localStorage): 바로 보이고 바로 적지만, 집에 들어온 누구나 읽는다.
- 창고(IndexedDB): 크고 정리돼 있지만 꺼내는 데 절차가 있다(비동기·트랜잭션).
- 집주인(브라우저)은 공간이 모자라면 오래 안 쓴 집의 창고를 통째로 비운다.

똑같은 구조다.\
"현관 메모판에 금고 비밀번호를 붙이지 마라"가 "localStorage에 토큰을 두지 마라"다.

실무 예:
- 액세스 토큰을 localStorage에 뒀다가, 서드 파티 스크립트 하나가 변조돼 토큰이 통째로 빠져나갔다.
- 대량 목록을 localStorage에 `JSON.stringify`로 저장하다 `QuotaExceededError`가 났고, 예외 처리가 없어 앱 초기화가 멈췄다.
- Safari에서 일주일 안 들어온 사용자의 오프라인 데이터가 사라졌다.

## 동작·원리

### 1. 네 저장소 한눈에

```text
               쿠키                 localStorage          IndexedDB              Cache Storage
  범위         도메인·경로(포트 무관)   출처                  출처                   출처
  API          document.cookie /    동기 문자열 키-값       비동기, 트랜잭션,         비동기, Request→Response
               Set-Cookie 헤더                            구조적 복제 값, 인덱스
  서버 전송     요청마다 자동          안 감                  안 감                  안 감
  스크립트 읽기  HttpOnly면 불가       가능                   가능                   가능
  크기(실측·문서) 쿠키당 4096바이트 이상 Chrome: 약 5Mi 문자     출처 쿼터 공유           출처 쿼터 공유
               지원 권장(RFC 6265)   (아래 실험)
```

- *출처(origin)*: 스킴·호스트·포트 묶음. localStorage·IndexedDB는 기본적으로 출처마다 따로다.
  - 예외: Chrome 115+는 제3자 iframe 안의 저장소를 최상위 사이트별로도 나눈다(*저장소 분할*). 같은 출처라도 직접 방문과 남의 사이트 iframe 안은 다른 저장소다(Chrome for Developers "Storage partitioning").
- 쿠키는 **포트로 나뉘지 않는다**(RFC 6265 §8.5). 아래 실험 6에서 다른 포트 페이지가 같은 쿠키를 봤다.
- *구조적 복제(structured clone)*: 객체·배열·Date·Blob·Map 등을 복사해 저장하는 알고리즘. 함수·DOM 노드는 못 담는다.

### 2. 쿼터와 축출 — 저장소 묶음 단위

```text
  브라우저 전체 저장 공간
  ┌──────────────────────────────────────────────────────────┐
  │ 출처 A 버킷 [IndexedDB + Cache + OPFS ...]  ← 쿼터 한도 공유 │
  │ 출처 B 버킷 [ ... ]                                       │
  │ 출처 C 버킷 [ ... ]  (persist 허락됨 → 축출 제외)           │
  └──────────────────────────────────────────────────────────┘
  공간 압박 → 가장 오래 안 쓴(LRU) best-effort 출처부터 "통째로" 삭제
```

- WHATWG Storage 표준은 저장소를 *버킷(bucket)* 으로 묶는다. 버킷 모드는 *best-effort*(기본, 브라우저가 지울 수 있음)와 *persistent*(사용자·브라우저가 허락, 축출 대상 아님)다.
- MDN(2026-01 갱신) 기준
  - Chromium: 출처당 디스크의 최대 60%.
  - Firefox: best-effort는 디스크 10%와 10GiB 중 작은 값(같은 사이트 그룹 한도), persistent는 디스크 50%(최대 8TiB).
  - Safari(macOS 14+·iOS 17+): 브라우저 앱에서 출처당 디스크 약 60%.
  - 축출은 LRU, **출처 단위 전부 삭제**, persistent 출처는 제외.
  - 예외: Chromium 122+의 Storage Buckets API로 한 출처에 버킷을 여럿 만들면, 브라우저는 버킷을 따로 지울 수 있다(Chrome for Developers "Storage Buckets").
- `navigator.storage.estimate()`는 쿼터·사용량 *추정치*다. `navigator.storage.persist()`는 Firefox에서는 사용자에게 묻고, Chrome·Edge 등 대부분의 Chromium 계열과 Safari는 사용 이력으로 자동 판정한다(MDN).
- Safari ITP: 사용자 상호작용 없이 Safari 사용 7일이 지나면 스크립트가 쓴 저장소(IndexedDB·localStorage·sessionStorage·서비스 워커 등록·캐시 등)를 지운다. 홈 화면 웹 앱은 따로 센다(WebKit 블로그 2020-03-24). 서버가 설정한 쿠키는 이 삭제에서 제외된다(MDN).

### 3. localStorage — 동기 API의 대가

```text
  메인 스레드 ──[ 클릭 처리 ]──[ localStorage.setItem(4MiB) ≈ 42~54ms ]──[ 다음 프레임 ]──▶
                                    └ 이 동안 입력·렌더링 못 함
```

- HTML 표준의 Web Storage는 **동기** API다. 호출이 끝날 때까지 메인 스레드를 쥔다.
- 값은 문자열만. 객체는 `JSON.stringify`로 바꿔 넣고, 직렬화 비용도 메인 스레드에서 낸다.
- Chromium 소스의 `kPerStorageAreaQuota`는 10485760(10 MiB)이다(`third_party/blink/public/mojom/dom_storage/storage_area.mojom`, 현재 main). 렌더러 쪽 `StorageAreaMap`은 키와 값의 길이 × `sizeof(UChar)`(2바이트)로 사용량을 센다(`third_party/blink/renderer/modules/storage/storage_area_map.cc`의 `QuotaForString`). 그래서 약 5Mi 문자에서 막힌다. 실험에서 들어간 양도 약 5Mi 문자였다.
- 같은 출처의 다른 문서에는 `storage` 이벤트로 변경이 알려진다.
- *sessionStorage*: 같은 API, 범위가 출처 + 탭(최상위 브라우징 컨텍스트) 하나. 탭을 닫으면 사라진다.

### 4. IndexedDB — 비동기 트랜잭션 키-값 저장소

```text
  데이터베이스 "app" (버전 1)
   ├─ 객체 저장소 orders   keyPath=id      키 순서로 정렬 저장
   │     └─ 인덱스 byDate  (date → id)     범위 질의: IDBKeyRange.bound(a, b)
   └─ 객체 저장소 drafts
  트랜잭션: readonly / readwrite, 범위 = 저장소 목록
           요청 실패를 처리하지 않으면 abort → 전부 롤백
```

- *객체 저장소(object store)*: 테이블에 해당. 키로 정렬돼 저장된다.
- *키 순서*: W3C IndexedDB 표준의 키 비교는 타입 순서 Number < Date < String < Binary < Array, 같은 타입 안에서는 값 순서다. 실험 4의 정렬 결과가 이 순서다.
- 요청이 실패하면 `error` 이벤트가 난다. 핸들러가 `preventDefault()`를 부르지 않으면 트랜잭션이 abort된다(W3C IndexedDB §5.10 "fire an error event"). 부르면 트랜잭션은 계속된다.
- 트랜잭션은 **자동 커밋**이다. 대기 중인 요청이 없고 이벤트 루프로 돌아가면 커밋된다. 트랜잭션 도중 `await fetch(...)`를 끼우면 그 사이 트랜잭션이 끝나 `TransactionInactiveError`가 난다.
- 구현 저장 엔진(표준 밖)
  - Chromium: LevelDB(LSM 트리)와 파일 혼합 구현을 SQLite로 바꾸는 중이다. blink-dev 공지(2026-04-25): 148 DevTrial, 150 출시, **새 저장소부터** 적용, 기존 LevelDB 데이터 이전은 다음 단계. 그 앞 단계에서 시크릿 같은 메모리 컨텍스트에 먼저 적용했다.
  - Firefox·Safari(WebKit): SQLite 기반(WebKit `SQLiteIDBBackingStore`).
  - 이 노트 실험의 디스크 프로필(Playwright가 띄운 Chrome 151)에서는 `*.indexeddb.leveldb` 폴더가 생겼다(아래 실험 4b). 필드 트라이얼을 끈 실행이라 일반 사용자 프로필과 다를 수 있다 — 일반 프로필의 실제 백엔드는 [?].

### 5. 쿠키 — 서버를 위한 저장소

- `Set-Cookie` 속성이 접근 범위를 정한다.
  - *HttpOnly*: `document.cookie`로 못 읽는다. XSS가 쿠키 값을 직접 꺼내지 못한다(요청에 실어 보내는 것은 막지 못한다).
  - *Secure*: 보통 HTTPS에서만 전송. Chrome 151 실측에서는 `http://localhost`·`http://127.0.0.1`(루프백)에서도 저장·전송됐다. *SameSite*(`Strict`·`Lax`·`None`): 교차 사이트 요청에 실을지.
- RFC 6265 §6.1은 브라우저가 최소한 쿠키당 4096바이트, 도메인당 50개, 전체 3000개를 지원하라고 권한다. 실제 상한은 브라우저마다 다르다.
- 요청마다 실려 가므로 큰 쿠키는 그 도메인으로 가는 요청 헤더를 매번 키운다.

### 실험: 가시성·쿼터·동기 비용·IndexedDB 순서와 원자성

127.0.0.1 Node 서버가 `Set-Cookie: sid=secret; HttpOnly; SameSite=Lax`와 `theme=dark`를 준다. 페이지에서 각 저장소를 조작했다.

```js
// exp06-storage.js 핵심
// 2. 쿼터: 1Mi 문자 값을 계속 넣다가 예외가 나면 1Ki 문자로 남은 공간을 더 채운다
const chunk = 'a'.repeat(1024 * 1024);
try { for (; i < 100; i++) localStorage.setItem('k' + i, chunk); }
catch (e) { /* e.name, e.code, i 기록 후 'b'.repeat(1024)로 추가 채움 */ }
// 3. 동기 비용: 같은 크기 setItem을 3번, getItem 1번 시간 측정 (performance.now)
// 4. IndexedDB: 10000건 put 한 트랜잭션, byDate 인덱스 범위 질의, 키 타입 섞어 넣고 getAllKeys,
//    같은 트랜잭션에서 add('new1') 다음 이미 있는 키 add(10) → abort 여부와 new1 잔존 확인
```

(실험, headless Chrome 151.0.7922.173, Playwright 새 컨텍스트, 스로틀 없음, 2026-10-04 — 3회 실행)

```text
--- 1. 스크립트가 볼 수 있는 것 (XSS 가 실행하는 코드와 같은 권한)
document.cookie="theme=dark" | localStorage.access_token=eyJ...demo
브라우저 쿠키 저장소(CDP): sid httpOnly=true sameSite=Lax, theme httpOnly=false sameSite=Lax
--- 2. localStorage 쿼터: 1 MiB(문자) 단위로 채우기
QuotaExceededError (code 22) at key k4: stored 4 MiB chars + 1020 KiB chars; message=Failed to execute 'setItem' on 'Storage': Setting the value of 'k4' exceeded the quota.
같은 문자 수를 한글로: QuotaExceededError at k4 (4 MiB chars stored)
--- 3. localStorage 는 동기: 메인 스레드 점유 시간 (여러 번)
1MiB setItem=[13.4,14.4,15.0]ms getItem=0.3ms | 2MiB setItem=[24.4,24.8,24.5]ms getItem=0.5ms | 4MiB setItem=[53.4,48.1,44.8]ms getItem=1.0ms
--- 4. IndexedDB: 키 정렬 순서·범위 질의·트랜잭션 원자성
put 10000건 1 트랜잭션=1254ms | date=2026-10-03 범위 키 358개 앞 5개=2,30,58,86,114 | 키 정렬=[2,10,"Date(0)","a","b",[1]] | 충돌 트랜잭션=abort ConstraintError, new1 남았나=없음(롤백)
--- 5. navigator.storage
quota=7.00GiB usage=2677507B usageDetails={"indexedDB":2677507} persisted=false
persist() 요청: false
--- 6. 출처 경계: 다른 포트(=다른 출처)의 localStorage, 같은 호스트 쿠키
다른 포트 페이지: localStorage.mine=null document.cookie="theme=dark"
```

범위(집필 3회 + 사실 점검 재실행 2회): 4MiB `setItem` 42.1~54.3ms, 1MiB 10.6~15.0ms, IndexedDB 10000건 put 1254~1452ms, `quota` 6.00~7.00GiB. 쿼터 예외 지점·키 정렬·롤백·가시성 결과는 다섯 번 모두 같았다.

```text
--- 4b. 디스크 프로필(launchPersistentContext)에서 IndexedDB 쓰기 후 프로필 폴더
Default/IndexedDB/http_127.0.0.1_38067.indexeddb.leveldb/000003.log
Default/IndexedDB/http_127.0.0.1_38067.indexeddb.leveldb/CURRENT
Default/IndexedDB/http_127.0.0.1_38067.indexeddb.leveldb/MANIFEST-000001
...
SQLite 헤더: Default/WebStorage/QuotaManager
```

관찰과 해석:
- **HttpOnly 쿠키 `sid`는 스크립트에 안 보였고, localStorage 토큰은 그대로 보였다.** 페이지에서 도는 스크립트(XSS 포함)는 localStorage를 다 읽는다.
- 쿼터 예외는 약 5Mi 문자 지점에서 났다. 한글(UTF-8로 3바이트)도 같은 문자 수에서 막혔다. UTF-8 바이트가 아니라 UTF-16 코드 단위(2바이트)로 센다는 Chromium 소스(위 3절)와 맞는다.
- `setItem`은 크기에 거의 비례해 4MiB에서 42~54ms 메인 스레드를 쥐었다. 한 프레임(60Hz 기준 약 16.7ms)을 넘는다.
- IndexedDB 키 정렬은 숫자 → Date → 문자열 → 배열. 키 충돌 하나로 같은 트랜잭션의 앞선 `add`까지 롤백됐다.
- `quota`가 실행마다 6~7GiB로 달랐다. Playwright 새 컨텍스트는 디스크 프로필이 아닌 메모리 기반이라 MDN의 "디스크 60%"와 바로 비교할 수 없다. 산정 방식은 [?].
- 다른 포트 페이지는 localStorage를 못 봤지만(`null`) 쿠키 `theme`은 봤다. 출처 경계와 쿠키 경계가 다르다.

## 쓰이는 자료구조·알고리즘

- **키-값 저장소**: localStorage = 출처별 해시맵(문자열 → 문자열). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **정렬된 키 저장 + 범위 스캔**: IndexedDB 객체 저장소·인덱스. SQLite 백엔드는 B-트리, LevelDB 백엔드는 LSM 트리다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md) · [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md) · [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md) · [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)
- **트랜잭션 원자성**: 한 트랜잭션의 요청은 전부 반영되거나(커밋) 전부 취소된다(abort).
- **LRU 축출**: 출처 단위 마지막 사용 시각 기준. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- **스키마 버전 업그레이드**: `indexedDB.open(name, version)` → `onupgradeneeded`에서 마이그레이션. 다른 탭이 옛 버전 연결을 쥐고 있으면 `blocked`.

## 적용 — 풀어나가는 법

### 1. 무엇을 어디에 둘지 고른다

| 데이터 | 권장 위치 | 이유 |
|---|---|---|
| 세션 식별자·리프레시 토큰 | `HttpOnly; Secure; SameSite` 쿠키 (또는 BFF 서버 세션) | 스크립트가 값을 못 읽는다 |
| 짧은 수명 액세스 토큰 | 메모리(JS 변수) | 새로고침 시 쿠키 세션으로 재발급 |
| 테마·언어 같은 작은 설정 | localStorage | 작고 동기 읽기가 편하다 |
| 목록·초안·오프라인 데이터 | IndexedDB | 비동기·대용량·인덱스·트랜잭션 |
| 오프라인 응답 사본 | Cache Storage(07번) | Request→Response 그대로 |

- localStorage에 토큰을 두지 않는다. XSS 한 번으로 탈취된다(실험 1). 토큰 회전·저장 위치 설계는 security 17번(미작성, [security 영역 표](../../security/README.md)).

### 2. 쓰기 실패를 예상하고 짠다

```ts
function saveSetting(key: string, value: unknown): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    // QuotaExceededError, 또는 저장소가 막힌 환경(접근 시 SecurityError)
    console.warn('setting not saved', (e as DOMException).name);
    return false;   // 앱은 계속 돈다
  }
}
```

### 3. IndexedDB는 래퍼로, 트랜잭션 안에서 네트워크를 기다리지 않는다

```ts
// 1) 먼저 받고  2) 그다음 짧은 트랜잭션으로 쓴다
const items = await (await fetch('/api/items')).json();
const tx = db.transaction('items', 'readwrite');
for (const it of items) tx.objectStore('items').put(it);
await new Promise((res, rej) => { tx.oncomplete = res; tx.onabort = () => rej(tx.error); });
```

### 4. 중요한 데이터는 persist를 요청하고, 지워질 수 있다고 가정한다

```ts
if (navigator.storage?.persist && !(await navigator.storage.persisted())) {
  await navigator.storage.persist();      // 허락 여부는 브라우저 판단(실험에서 false)
}
const { usage, quota } = await navigator.storage.estimate();   // 추정치
```

- 서버가 원본, 브라우저 저장소는 사본이라는 전제로 동기화한다. 축출·ITP 삭제 뒤 서버에서 다시 채운다.

### 5. 진단

- DevTools Application 패널: Storage(사용량·쿼터 시뮬레이션·Clear site data), Cookies(HttpOnly·SameSite 열), Local Storage, IndexedDB.
- Performance 패널에서 `setItem`이 든 긴 태스크를 찾는다.

## 장애 시나리오와 대처

### 1. localStorage 토큰 탈취 (⚠ XSS 한 번에 탈취)

- **현상**: 계정 탈취 신고. 공격자가 다른 IP에서 유효한 토큰으로 API를 호출했다.
- **보이는 형태**: 서버 로그에 낯선 IP·User-Agent의 정상 인증 요청. 프론트엔드 로그에는 아무것도 없다.
- **원인**: 변조된 서드 파티 스크립트나 XSS가 `localStorage.getItem('access_token')`을 읽어 외부로 보냈다. 실험 1처럼 스크립트는 localStorage를 다 읽는다.
- **대처**: 토큰을 HttpOnly 쿠키·BFF 세션으로 옮긴다. CSP·SRI로 스크립트 공급망을 좁힌다. 이미 퍼진 토큰은 폐기·회전한다.

### 2. `QuotaExceededError`로 앱 초기화 중단 (⚠ 쿼터 초과)

- **현상**: 특정 사용자만 앱이 흰 화면.
- **보이는 형태**: 콘솔 `QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the value of '...' exceeded the quota.`
- **원인**: 캐시 목적으로 큰 JSON을 localStorage에 누적했다. Chrome에서는 약 5Mi 문자에서 막힌다(실험 2). 예외 처리가 없어 초기화 코드가 중단됐다.
- **대처**: 큰 데이터는 IndexedDB로. 쓰기마다 try/catch. 저장 키에 상한·만료를 둔다.

### 3. Safari에서 오프라인 데이터 소실 (⚠ ITP 7일 제한)

- **현상**: 한동안 안 쓴 iPhone 사용자의 오프라인 초안이 없어졌다.
- **보이는 형태**: IndexedDB가 비어 있고, 서비스 워커도 다시 설치된다. 오류 로그는 없다.
- **원인**: Safari의 7일 상한 — 사용자 상호작용 없이 Safari 사용 7일이 지나면 스크립트가 쓴 저장소를 지운다(WebKit 2020-03-24).
- **대처**: 초안은 서버에 자주 동기화한다. 홈 화면 웹 앱은 별도 집계라 영향이 다르다.

### 4. 저장 공간 압박으로 출처 통째 축출

- **현상**: 디스크가 거의 찬 기기에서 오프라인 앱 데이터 전체가 사라졌다.
- **보이는 형태**: `navigator.storage.persisted()`가 false였고, 다음 방문 때 IndexedDB·Cache가 모두 비어 있다.
- **원인**: best-effort 버킷은 공간 압박 시 삭제 대상이 되고, 지울 때는 버킷을 통째로 지운다(Storage 표준 §7.1 "Storage pressure"·버킷 삭제). 순서를 LRU(가장 오래 안 쓴 출처부터)로 하는 것은 MDN이 적은 브라우저 동작이다(표준은 "사용자 영향이 가장 적은 방식"만 권한다).
- **대처**: `persist()` 요청, 서버를 원본으로 두는 동기화 설계, 앱 시작 시 데이터 존재 확인 후 복구.

### 5. 저장 중 화면 끊김

- **현상**: "저장" 버튼을 누를 때마다 화면이 잠깐 멈춘다. INP가 나쁘다.
- **보이는 형태**: Performance 패널에 `setItem`·`JSON.stringify`가 든 수십 ms 태스크.
- **원인**: localStorage는 동기라 MiB 단위 값이면 메인 스레드를 수십 ms 쥔다(실험 3: 4MiB 42~54ms).
- **대처**: IndexedDB(비동기)로 옮기고, 직렬화가 큰 작업은 웹 워커로 넘긴다([16-long-tasks-and-web-workers](../16-long-tasks-and-web-workers/2-summary.md)).

## 핵심 문장

- 저장소는 누가 읽나·동기인가·얼마나 담나·언제 지워지나로 고른다. 세션 식별자는 HttpOnly 쿠키, 큰 데이터는 IndexedDB, 작은 설정만 localStorage에 둔다.
- localStorage는 같은 출처에서 도는 스크립트라면 누구든 읽는다. 토큰을 두면 XSS 한 번에 탈취된다.
- localStorage는 동기 API라 큰 값 쓰기가 메인 스레드를 막는다. Chrome 151 실측에서 4MiB 쓰기는 42~54ms, 약 5Mi 문자에서 `QuotaExceededError`가 났다.
- IndexedDB는 키가 정렬된 비동기 트랜잭션 저장소다. 처리하지 않은 요청 실패 하나로 트랜잭션 전체가 롤백된다.
- best-effort 저장소는 공간 압박 때 출처(버킷을 나눴다면 버킷) 단위로 통째 지워질 수 있고, Safari는 7일 무상호작용 시 지운다. 브라우저 저장소는 사본으로 다룬다.

## 관련 주제·근거

- 선행
  - [05-fetch-from-browser](../05-fetch-from-browser/2-summary.md) — credentials 모드와 쿠키 전송
  - security 11 `sessions-and-cookie-security` — 미작성, [security 영역 표](../../security/README.md)
- 후속·연결
  - [07-service-workers-and-offline](../07-service-workers-and-offline/2-summary.md) — Cache Storage와 오프라인
  - security 17 `refresh-token-rotation-and-revocation` — 미작성, [security 영역 표](../../security/README.md)
  - [16-long-tasks-and-web-workers](../16-long-tasks-and-web-workers/2-summary.md) — 메인 스레드 밖으로 직렬화·저장 넘기기
  - [03-event-loop](../03-event-loop/2-summary.md) — 동기 `setItem`이 막는 메인 스레드 태스크
  - [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md) · [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md) · [database/38-lsm-storage-engine](../../database/38-lsm-storage-engine/2-summary.md)
  - Web API 문법: [web-api/29 credentials·쿠키](../../../languages/web-api/29-credentials-and-cookies/2-summary.md)
- 표준·문서
  - WHATWG Storage Living Standard <https://storage.spec.whatwg.org/> — 버킷, best-effort·persistent, 쿼터, `navigator.storage`
  - WHATWG HTML "Web storage" 절 <https://html.spec.whatwg.org/multipage/webstorage.html> — localStorage·sessionStorage, 동기 API, `storage` 이벤트
  - W3C Indexed Database API 3.0 <https://w3c.github.io/IndexedDB/> — 키 비교 순서, 트랜잭션 수명·자동 커밋, §5.10 fire an error event(취소 안 하면 abort)
  - Chrome for Developers "Storage Buckets API" <https://developer.chrome.com/docs/web-platform/storage-buckets> — Chromium 122+, 버킷별 삭제 · "Storage partitioning" <https://developer.chrome.com/docs/privacy-sandbox/storage-partitioning> — Chrome 115+ 제3자 저장소 분할
  - MDN "Storage quotas and eviction criteria"(2026-01-05 갱신) <https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria> — 브라우저별 쿼터, LRU 출처 단위 축출, persist 동작, localStorage 5MiB
  - WebKit 블로그 "Full Third-Party Cookie Blocking and More"(2020-03-24) <https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/> — 스크립트 쓰기 저장소 7일 상한
  - blink-dev "Web-Facing Change PSA: IndexedDB: SQLite backend"(2026-04-25) <https://groups.google.com/a/chromium.org/g/blink-dev/c/jS0khnC5IWA> — 148 DevTrial·150 출시, 새 저장소부터
  - Chromium `third_party/blink/public/mojom/dom_storage/storage_area.mojom`(`kPerStorageAreaQuota = 10485760`), `third_party/blink/renderer/modules/storage/storage_area_map.cc`(`QuotaForString` = 길이 × `sizeof(UChar)`) — chromium.googlesource.com main
  - RFC 6265 §6.1 Limits, §8.5 Weak Confidentiality
- 실험 목록
  - `exp06-storage.js` — Node 20.19.6 + playwright-core 1.62.1, headless Chrome 151.0.7922.173, 127.0.0.1 Node 서버 2개. HttpOnly 쿠키 vs localStorage 가시성, localStorage 쿼터(ASCII·한글), `setItem` 동기 시간, IndexedDB 10000건 put·인덱스 범위·키 정렬·충돌 롤백, `navigator.storage.estimate/persist`, 다른 포트의 저장소·쿠키. 3회 실행.
  - `secure.js`(판정 때 추가) — 같은 환경, `Set-Cookie: s=1; Secure`를 `http://localhost`·`http://127.0.0.1`에서 받고 다음 요청에 실리는지 확인 → 둘 다 `cookie=s=1`.
  - `exp06-idbfiles.js` — 같은 환경에서 `launchPersistentContext`로 디스크 프로필을 만들고 IndexedDB 쓰기 후 프로필 파일 목록·SQLite 헤더 확인.
