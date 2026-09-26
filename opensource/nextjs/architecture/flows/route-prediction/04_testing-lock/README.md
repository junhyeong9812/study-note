# 04 테스트 잠금

상위: [가져온 적 없는 라우트 트리를 예측하기까지](../README.md)

Instant Navigation Testing API 는 "캐시가 따뜻한 사용자가 링크를 누른 순간 보는 화면" 을 테스트가 붙잡아 검사하게 해 준다. 방법은 쿠키 하나다. 쿠키가 있으면 서버는 **셸만** 그리고, 클라이언트는 내비게이션의 **동적 데이터 쓰기를 멈춰 세운다.** 쿠키를 지우면 둘 다 풀린다. 이 장치는 예측과 같은 디렉터리(`segment-cache/`)에 살고, 프로덕션 빌드에서는 **모듈이 통째로 빈 껍데기로 바뀐다.**

## 위치

`packages/next` / `src/client/components/segment-cache` / `navigation-testing-lock.ts` L114-L290 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/navigation-testing-lock.ts#L114-L290))

## 실제 코드

잠금을 잡는 함수다. 잠금이 쥐는 것이 여기서 다 보인다.

```ts
// navigation-testing-lock.ts L210-L236
function acquireLock(): void {
  if (lockState !== null) {
    return
  }
  let resolveReleased: () => void
  const released = new Promise<void>((r) => {
    resolveReleased = r
  })
  let resolveCurrentNavigation: () => void
  const currentNavigation = new Promise<void>((r) => {
    resolveCurrentNavigation = r
  })
  lockState = {
    released,
    resolveReleased: resolveReleased!,
    fetch: window.fetch,
    activePrefetches: new Set(),
    segmentCacheMap: createCacheMap(),
    currentNavigation,
    resolveCurrentNavigation: resolveCurrentNavigation!,
  }

  // Install the fetch blocker. We only intercept `window.fetch` for the
  // duration of the lock so that — outside of a testing scope — user-
  // installed overrides of `window.fetch` are untouched.
  window.fetch = globalFetchOverride
}
```

서버는 같은 쿠키로 "이 요청은 테스트 렌더인가" 를 정한다.

```ts
// app-page-runtime.ts L448-L453
    const isInstantNavigationTest =
      exposeTestingApi &&
      typeof req.headers.cookie === 'string' &&
      req.headers.cookie.includes(NEXT_INSTANT_TEST_COOKIE + '=') &&
      (!isRSCRequestHeader(req.headers[RSC_HEADER]) ||
        req.headers[NEXT_ROUTER_PREFETCH_HEADER] === '1')
```

```text
 ★★★ 잠금 하나가 **다섯 가지**를 쥔다 (NavigationLockState L114-154 — 필드 일곱 중 resolve 함수 둘을 뺀 것)

   released            잠금이 풀릴 때 resolve. 막아 둔 사용자 fetch 가 이것을 기다린다
   fetch               잠그기 전의 window.fetch. 풀 때 되돌린다
   activePrefetches    아직 안 끝난 "잠긴 내비게이션용 프리페치" — 풀 때 강제로 resolve
   segmentCacheMap     **이 잠금만의 빈 세그먼트 캐시** (L227 createCacheMap())
                         주석 L134-137 - "It starts empty, so each instant() navigation observes
                         only data fetched under the lock — a "clean read" — and never matches
                         a stale entry left in the shared cache"
   currentNavigation   지금 잠긴 내비게이션의 동적 데이터 문. 새 잠긴 내비게이션이 오면
                       **이전 것을 열고** 새 문을 단다 (beginLockedNavigation L276-290)

 L235  window.fetch = globalFetchOverride
 => 잠금 중에는 **앱 코드의 fetch 도 멈춘다** (L379 `currentLock.released.then(...)`).
    Next.js 내부 요청은 segment-cache/fetch.ts 를 거쳐 잠그기 전 fetch 로 나간다 —
    그 모듈을 쓰는 곳은 cache.ts · fetch-server-response.ts · server-action-reducer.ts · offline.ts 넷 (grep)
 ★ 개발 서버의 `/__nextjs_` 요청(오류 오버레이 · 소스맵)은 막지 않는다 (L365-373, `__NEXT_DEV_SERVER` 일 때)

 서버 쪽 APPRT L448-453
   쿠키가 있고 (문서 요청이거나 `next-router-prefetch: 1` 요청)이면 테스트 렌더
   주석 L446-447 - "Regular RSC navigation requests proceed normally even during a locked
     scope; blocking happens on the client side."
 => 프리페치와 첫 문서는 서버가 셸만 주고, 내비게이션의 동적 요청은 **정상 응답을 받은 뒤
    클라이언트가 쓰기를 미룬다** (PPRNAV L1848-1850)
```

## 동작 흐름

```text
 어느 모듈이 실리는가 — 빌드가 두 번 가른다

 define-env.ts L396-397
   __NEXT_EXPOSE_TESTING_API = dev || experimental.exposeTestingApiInProductionBuild === true
   => require(...) 로 부르는 자리는 열 곳이다. 그중 여덟(SCNAV L90 · L323, PPRNAV L2347 · L2365 · L2380,
      scheduler.ts L333 · L681, app-globals.ts L16)은 이 플래그의 if 안에 있고,
      SCNAV L1234 · L1273 은 플래그 갈래에서만 불리는 ensurePrefetchThenNavigate 안에 있다
 create-compiler-aliases.ts L183-198   (isClient 일 때만 — L151)
   !dev && exposeTestingApiInProductionBuild !== true 면
     navigation-testing-lock.js → navigation-testing-lock.disabled 로 **별칭**
 crates/next-core/src/next_import_map.rs L600-621   Turbopack 의 같은 별칭 (`if !expose_testing_api`)

 ★★ 플래그와 별칭이 **같은 조건**을 두 번 쓴다
   segment-cache/fetch.ts L1 은 `import { getPreLockFetch } from './navigation-testing-lock'` 를
   **정적으로** 한다. 호출은 L17 플래그 안이지만 import 는 남는다
 ※ 그래서 플래그만으로는 모듈이 번들에서 빠지지 않고, 별칭이 그 자리를 채우는 것으로 보인다.
   번들 결과를 열어 확인하지는 않았다

 navigation-testing-lock.disabled.ts (68줄)
   export 함수 **열한 개** — 진짜 모듈과 같은 수다 (grep -c "^export function" 둘 다 11)
   주석 L11-12 - "Every export mirrors the real module's signature and returns the value the
     real implementation produces when no lock is held."
   => null · false · 빈 함수. shouldRestrictNavigationToShell 도 false (L63-68)

 [프리페치] [03](../../segment-cache/03_navigate/README.md)이 "어느 쪽이 언제 쓰이는지는 확인하지 않았다" 고 남긴 답이 이것이다 —
   개발 서버와 `exposeTestingApiInProductionBuild: true` 빌드는 진짜, 그 밖의 프로덕션 브라우저 번들은 .disabled
```

```text
 쿠키 상태 넷 — parseCookieValue  NTLOCK L35-49

   ''                              empty
   JSON 배열이고 길이 3 이상         [2] 가 null 이면 mpa, 아니면 spa     (Next.js 가 쓴 값)
   그 밖 전부                        pending                             (외부가 쓴 값)
 쓰는 쪽
   @next/playwright instant()  [0, "p<난수>"]            next-playwright/src/index.ts L106   잠금 시작
   NTLOCK L411                 [1, "c<난수>", null]       MPA 첫 로드를 잡았다
   NTLOCK L475                 [1, "c<난수>", {from, to}] SPA 내비게이션을 잡았다
   NTLOCK L314                 [0, "c<난수>"]             뒤로/앞으로 뒤 다시 pending
   외부가 쿠키를 지운다                                   잠금 끝
 주석 L8-11 - 외부는 [0] 을 써서 시작하고 쿠키를 지워 끝낸다. 값으로 누가 썼는지 가른다
```

```text
 한 번의 잠금 — 시작에서 끝까지

 잡기 (셋 중 먼저 오는 것)
   NTLOCK L418-433  CookieStore 'change' 에서 pending 을 보면 acquireLock
   NTLOCK L481-513  isNavigationLocked — lockState 가 없으면 document.cookie 를 **동기로** 읽어 잡는다
                     (쿠키 설정과 change 이벤트 사이의 틈, 주석 L486-490)
   NTLOCK L394-411  MPA 첫 로드 — 서버가 심은 self.__next_instant_test 가 있으면 잡고 [1,…,null] 을 쓴다
     (app-globals.ts L12-18 이 페이지 초기화 때 startListeningForInstantNavigationCookie 를 부른다)

 잠긴 채 링크를 누르면 — SCNAV navigate L88-110
 L91   isNavigationLocked() 이면
 L96     navigationLock = beginLockedNavigation()     이전 잠긴 내비게이션의 문을 열고 새 문
 L97     => return ensurePrefetchThenNavigate(...)    (SCNAV L1210-1278) — **언제나 Promise**
 L1235     beginNavigationLockPrefetch()
 L1236     schedulePrefetchTask(...)   작업이 잠금의 segmentCacheMap 에 묶인다 (scheduler.ts L330-337)
 L1245     await 프리페치 완료           scheduler.ts L670-687 가 작업이 끝날 때 resolve
 L1253     navigateImpl(..., prefetchTask.segmentCacheMap)
             SCNAV L320-329  shouldRestrictNavigationToShell 이면 restrictToShell
               → SCCACHE L568-574  세그먼트를 **셸 varyPath** 로만 찾는다
                 (잠김 + 라우트가 partial prefetching + 이 링크가 speculative 프리페치를 안 했을 때 — NTLOCK L544-552)
             ... spawnDynamicRequests → fetchMissingDynamicData
 PPRNAV L1848    `__NEXT_EXPOSE_TESTING_API && navigationLock !== null` 이면 **await navigationLock**
                 → 응답은 받았지만 CacheNode 에 쓰지 않는다. 화면은 프리페치 상태에 머문다
                 ※ 이 게이트는 fetchMissingDynamicData 에만 있다 — 라우트 캐시가 비어
                   navigateToUnknownRoute 로 가면 전체 seed 를 받고 잠금을 기다리지 않는다
                   (SCNAV L470-540). 실행해 확인하지는 않았다
 L1271     MPA 가 아니면 updateCapturedSPAToTree(from, to)

 잠긴 채 다른 라우터 일을 하면
   refresh-reducer.ts L69 · server-action-reducer.ts L502 · server-patch-reducer.ts L52
     getCurrentNavigationLock() (PPRNAV L2344-2351) — **지금 잠긴 내비게이션의 문**에 같이 묶인다
   restore-reducer.ts L102 · L112   뒤로/앞으로는 null 로 **묶지 않고**, 잠금을 새 pending 으로 되돌린다

 풀기 — 외부가 쿠키를 지운다 (NTLOCK L439-462)
 L447  releaseLock   window.fetch 복원 → 남은 프리페치 강제 resolve → 현재 문 resolve → released resolve
 L458  쿠키를 한 번 더 지운다 (주석 L448-456 — 틈새에 되살아난 쿠키)
 L460  refreshOnInstantNavigationUnlock (use-action-queue.ts L23-31)
         라우터가 있으면 ACTION_REFRESH { bypassCacheInvalidation: true }, 없으면 location.reload()
```

```text
 ★★ 서버는 이 쿠키로 **PPR 경로를 강제로 연다** — APPRT L433-476

 L433-435  exposeTestingApi = routeModule.isDev === true || exposeTestingApiInProductionBuild === true
 L462      isRoutePPREnabled = (couldSupportPPR || isInstantNavigationTest) && ...
           주석 L458-461 - "enable the PPR prerender path even without Cache Components.
             In dev mode without CC, static pages need this path to produce buffered segment data"
 L471-473  매니페스트에 PARTIALLY_STATIC 이 없어도 (테스트 렌더 && (exposeTestingApi || testProxy)) 면 연다
 L475-476  isDebugStaticShell = (디버그 쿼리 || 테스트 렌더) && isRoutePPREnabled
 => [PPR 내비게이션] README 가 "PPR 은 cacheComponents 로만" 이라 적은 설정 관계 밖에서,
    **테스트 렌더 한 요청**에 한해 PPR 셸 경로가 돈다
 couldSupportPPR 는 L324 `checkIsAppPPREnabled(nextConfig.experimental.ppr)` — v16.3.6 에서
   experimental.ppr 은 cacheComponents 일 때만 참이다 ([PPR 내비게이션] README 의 설정 관계)
 => CC 를 끈 기본 앱에서도 **테스트 렌더면** L462 의 앞 조건이 참이 된다

 셸이 비어 있을 때 (L1961-2006)
   개발    Error 를 던진다 → catch(L2192-2197)가 Set-Cookie 로 쿠키를 지운다
   프로덕션 쿠키를 지우는 <script> 가 든 복구 문서를 보낸다
   주석 L1967-1971 - 그러지 않으면 "every reload would render the same blank shell and leave
     the user stuck"

 첫 문서의 하이드레이션 원천
   server/app-render/instant-test-bootstrap.ts L23-33
     쿠키가 있으면 self.__next_instant_test = fetch(location.pathname + '?_rsc=…',
       { RSC: 1, next-router-prefetch: 1, next-router-segment-prefetch: '/_full' })
   app-render.tsx L3362 · L8337 — renderOpts.experimental.exposeTestingApi 면 bootstrapScriptContent 에 붙인다
   => client/app-index.tsx L43-48 이 이 Promise 를 정적 RSC 원천으로 쓰고, NTLOCK L394 가 이것을 보고 잠근다
 ※ base-server.ts L2317-2345 에도 같은 쿠키를 보는 `hasInstantTestCookie` 가 있다. 이 경로가
   APPRT 와 어떻게 나뉘는지는 읽지 않았다
```

## 결과가 쓰이는 곳

```text
 NavigationLock (currentNavigation 의 스냅숏 Promise)
      --> PPRNAV L1848 fetchMissingDynamicData — 동적 데이터 쓰기 직전에 기다린다
          ([PPR 내비게이션] [04]가 "L1848 테스트 API 의 잠금" 이라 한 줄)

 segmentCacheMap (잠금 전용)
      --> 잠금 중에 예약된 프리페치 작업과 그 작업이 이끄는 내비게이션이 **공유 캐시 대신** 쓴다
          (scheduler.ts L330-337 · SCNAV L1265)
      ★ 예측의 트라이([01][02])와 라우트 캐시는 잠금이 따로 두지 않는다 — 잠금 전에 배운 패턴은
        잠금 중에도 쓰인다 (NTLOCK 안에 knownRoute · routeCacheMap 참조 0건)

 restrictToShell
      --> [PPR 내비게이션] [01][02]의 트리 짓기 함수들이 인자로 받아 SCCACHE L563 까지 내려보낸다

 쿠키의 captured 값 (from/to 트리)
      --> 외부 도구(Navigation Inspector 패널 · `@next/playwright`)가 읽는다. 읽는 쪽은 범위 밖
```

## 다루지 않는 것

`@next/playwright` 의 `instant()`(next-playwright/src/index.ts 216줄) 본문과 쿠키 도메인 결정, 개발 도구의 Navigation Inspector 패널(`next-devtools/dev-overlay/components/instant-navs/`), `app-index.tsx` 가 `self.__next_instant_test` 로 하이드레이션하는 과정, `subtreeHasSpeculativePrefetch`(scheduler.ts)의 판정, 스케줄러가 잠긴 프리페치를 "끝났다" 고 보는 조건(`blockTaskOnPendingResponse`), APPRT 의 나머지 테스트 분기(L1272 · L1300-1303 · L1581 `allowEmptyStaticShell`)와 `use-cache-wrapper.ts` L414 의 쿠키 사용, 개발 중 `instant` 설정을 검증하는 장치([instant 검증](../../instant-validation/README.md) — 이 잠금과는 다른 코드다)는 이 문서의 범위 밖이다.
