# 01 진입과 두 스토어

상위: [`'use cache'` 가 값을 돌려주기까지](../README.md)

`cache()` 가 처음 하는 일은 **자기가 어디서 불렸는지 알아내는 것**이다. 그 답이 `workUnitStore.type` 이고, 값이 **열한 가지**다. `'use cache: private'` 은 그중 셋에서만 허용된다.

## 위치

`packages/next` / `src/server/use-cache` / `use-cache-wrapper.ts` L1715-L2033 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/use-cache/use-cache-wrapper.ts#L1715-L2033))

## 실제 코드

스토어 둘을 확인하는데 **던지는 오류의 종류가 다르다**.

```ts
// use-cache-wrapper.ts L1724-L1736
  const workStore = workAsyncStorage.getStore()
  if (workStore === undefined) {
    throw new Error(
      '"use cache" cannot be used outside of App Router. Expected a WorkStore.'
    )
  }

  const workUnitStore = workUnitAsyncStorage.getStore()
  if (workUnitStore === undefined) {
    throw new InvariantError(
      '"use cache" cannot be used outside of App Router. Expected a WorkUnitStore.'
    )
  }
```

```text
 workStore 없음      => Error           (사용자 잘못 — App Router 밖에서 썼다)
 workUnitStore 없음  => InvariantError  (일어나면 안 되는 일)

 ★★ 문장은 같고 **마지막 단어와 클래스가 다르다** (L1727 `Expected a WorkStore.` ·
   L1734 `Expected a WorkUnitStore.`)
   workStore 는 App Router 렌더 전체에 하나, workUnitStore 는 렌더 단위마다 하나다.
   전자가 없으면 App Router 밖이고, 전자가 있는데 후자가 없으면 Next.js 버그다
```

## 동작 흐름

```text
 cache(kind, id, boundArgsLength, originalFn, args)   UCW L1715

 L1722  isPrivate = kind === 'private'
 L1724  workStore     = workAsyncStorage.getStore()      없으면 => throw Error
 L1731  workUnitStore = workUnitAsyncStorage.getStore()   없으면 => throw InvariantError

 L1747  switch (workUnitStore.type) — prerender 가 이미 중단됐나
 L1750    'prerender' · 'prerender-runtime' 이고 renderSignal.aborted 이면
 L1754      => return makeUntrackedHangingPromise(
                 renderSignal, workStore.route,
                 '"use cache" called after prerender ended')
 L1760    (중단이 아니면 그 자리에서 break)
 L1762-1770  그 밖 아홉 값 => L1771 break     L1773  default: workUnitStore satisfies never

 L1779  핸들러 고르기 (probe 모드면 건너뛴다)
 L1817  오류 객체 미리 만들기
 L1850  cacheContext 만들기 — private / public 갈래
```

```text
 ★★★ prerender 가 끝난 뒤에도 여기 도달한다 (주석 L1738-1746)

 주석 원문
   "In a prerender, tasky IO may result in cache reads that start
    after the prerender has already been aborted:

      await setTimeout(100)  // we can't abort this uncached IO...
      await cachedData()     // ...so we'll still get here even though the prerender aborted

    The prerender is over, so we should just return an erroring promise.
    (NOTE: we also shouldn't fill this cache, because it's behind uncached IO,
    so semantically it is not part of the prerender)"

 => 캐시 안 된 IO(`setTimeout`)는 **중단할 수가 없다.** 그것이 끝난 뒤의 캐시 읽기가 여기 온다
 => 그때는 채우지도 않는다 — 그 값은 prerender 의 일부가 아니기 때문이다
 ★ `makeUntracked…` 다. 런타임 데이터 추적에 **끼우지 않는다** —
   주석 L1751-1753 이 "prerender 는 끝났으니 참여할 필요가 없다" 고 적는다
```

```text
 ★★★ 오류 객체를 **쓰기 전에 미리 만든다** (L1817-1832)

 L1817  const timeoutError = new UseCacheTimeoutError()
 L1818  Error.captureStackTrace(timeoutError, cache)
 L1819  applyOwnerStack(timeoutError)

 L1827  let deadlockError: UseCacheDeadlockError | undefined
 L1828  if (process.env.__NEXT_DEV_SERVER) {  ... 같은 셋을 한 번 더 ...  }

 주석 L1821-1826 가 이유를 적는다 (그 위 L1821 - "Only ever thrown by the
   dev-server's hang-detection probe.")
   "`Error.captureStackTrace` has to run while `cache()` is still on the
    synchronous stack, otherwise the user's `'use cache'` invocation frames
    would already be gone — that's why the construction sits up here rather
    than next to the trigger that actually consumes it."

 => 스택 트레이스를 **동기 스택이 살아 있는 동안** 찍어야 한다.
    `await` 를 한 번이라도 넘기면 사용자 코드의 프레임이 사라진다
 => 그래서 "쓰는 자리 옆" 이 아니라 **맨 위**에 있다
 ★ `deadlockError` 는 `__NEXT_DEV_SERVER` 로 감싸 프로덕션 번들에서 클래스째 빠진다
```

```text
 ★★ 핸들러 고르기가 개발/프로덕션으로 갈린다 (L1779-1815)

 L1780  workStore.useCacheProbeMode === undefined 일 때만 고른다
        주석 L1776-1778 - probe 재실행(개발 서버의 멈춤 탐지 워커)은
          아래에서 먼저 빠져나가므로 핸들러가 아예 등록되지 않아도 부팅된다

   isPrivate 이면
 L1786    __NEXT_DEV_SERVER 이면 cacheHandler = getPrivateCacheHandler()
          주석 L1782-1784 - private 캐시는 원래 핸들러가 아니라
            **Resume Data Cache(RDC)** 로 간다. 개발에서만 전용 인메모리
            핸들러에 추가로 저장해 리로드를 빠르게 한다
   그 밖이면
 L1789    handler = getCacheHandler(kind)   없으면 => throw Error('Unknown cache handler: ' + kind)
 L1799    __NEXT_DEV_SERVER && isCustomCacheHandler(kind) 이면
 L1802      tieredCacheHandler = getDevTieredCacheHandler(kind)
            없으면 => throw InvariantError
            주석 L1794-1798 - 사용자가 설정한 핸들러는 느리거나 원격일 수 있으니
              개발에서는 인메모리 앞단을 세워 캐시 히트를 **마이크로태스크 수준**으로 유지한다
 L1812    그 밖 => cacheHandler = handler

 => private 은 프로덕션에서 **핸들러가 없다.** RDC 뿐이다
 ★★★ 그런데 그 RDC 도 요청 사이에 남지 않는다 (주석 L2150-2158)
     "private caches are only used during dynamic requests and runtime prefetches;
      for dynamic requests the RDC is **immutable and excludes private caches**,
      and for runtime prefetches it's mutable but **lives only as long as the request**."
   => 프로덕션의 private 캐시는 **요청 하나를 넘기지 못한다.**
      "RDC 뿐이다" 는 "요청 안에서만 산다" 와 같은 말이다
 => 개발에서만 캐시 핸들러가 2단이 된다
```

```text
 ★★★ `'use cache: private'` 은 갈래가 **열한**이다 (L1853-1920)

   'prerender'            => makeRuntimeHangingPromise
                             주석 L1856 - private 캐시는 요청 데이터를 읽을 수 있고
                               그것은 **런타임 데이터**다
   'prerender-ppr'        => postponeWithTracking
   'prerender-legacy'     => throwToInterruptStaticGeneration
   'prerender-client'     => throw InvariantError  (클라이언트 컴포넌트 — 정적으로 막았어야 한다)
   'validation-client'    => 〃
   'unstable-cache'       => throw  `unstable_cache()` 안에서 쓰지 말라
   'cache'                => throw  "It can only be nested inside of another
                                     \"use cache: private\""
   'generate-static-params' => throw  요청 맥락 밖이다
   'request'              => OK
   'prerender-runtime'    => OK
   'private-cache'        => OK
   default                => workUnitStore satisfies never + throw InvariantError
                             주석 L1917-1918 - 죽은 코드지만 throw 가 없으면
                               TypeScript 가 cacheContext 를 미할당으로 본다

 => private 캐시가 **정적 prerender 에서 살아남지 못한다.** 세 갈래가 각자 다른 방식으로 뺀다
 ★★ 그리고 public `'use cache'` **안에는 들어갈 수 없다.**
   private 안에만 중첩할 수 있다 — 캐시 경계가 사생활 경계를 뒤집지 못하게 한다
```

```text
 ★★ public 쪽은 부모가 `'cache'` 일 때만 오류를 미리 만든다 (L1922-1979)

 L1940  const dynamicNestedCacheError = new NestedDynamicUseCacheError()
 L1941  Error.captureStackTrace(dynamicNestedCacheError, cache)

 주석 L1930-1939
   "Eagerly capture this invocation's call site while still synchronous in `cache()`.
    Used as `cause` of the nested-dynamic cache error when the outer cache
    (whose body never re-runs during the final prerender) throws. Only
    constructed when the parent is itself a public `'use cache'` — otherwise
    this entry can never propagate dynamism into that error and the allocation
    would be wasted. Private parents are intentionally excluded: `'use cache:
    private'` is dynamic-by-definition in prerendering and deferred to the
    runtime stage in dev requests, so a public cache nested inside one never
    triggers the throw upstream."

 => 바깥 캐시는 최종 prerender 에서 **본체가 다시 돌지 않는다.**
    그래서 안쪽이 동적이었다는 사실을 알려 줄 `cause` 를 안쪽에서 미리 만들어 둔다
 ★ 부모가 private 이면 만들지 않는다 — 어차피 그 위로 전파될 일이 없어 낭비다
 ★ 나머지 여덟 갈래는 `dynamicNestedCacheError: undefined` 로 같은 모양을 만든다 (L1964-1972)
```

```text
 ★ private 캐시는 **단계를 기다린다** (L2001-2032)

 L2009  'prerender-runtime'  => await stagedRendering.waitForStage(
                             RENDER_STAGES_BY_DATA_KIND.sessionData)
                         주석 L2005-2006 - 정적 prerender 에서 hang 할 API 들이
                           런타임 prerender 에서는 **알맞은 단계에서** 풀려야 한다.
                           private 캐시는 EarlyRuntime 에서 풀린다
 L2019  'request' (개발만)    => await makeDevtoolsIOAwarePromise(..., sessionData)
                           주석 L2017-2018 - 개발 요청의 정적 단계에서 풀리면 안 되니 늦춘다
 L2028  'private-cache'      => break  (그냥 통과)

 => private 캐시는 세션 데이터 단계 전에는 값을 내주지 않는다
 => [App Render]에서 본 단계 구분(`stagedRendering`)이 여기까지 온다
```

## 결과가 쓰이는 곳

```text
 cacheContext (kind: 'private' | 'public')
      --> 이 흐름의 나머지 전부가 이 값으로 갈린다.
          outerWorkUnitStore · functionId · handlerKind · outerOwnerStack ·
          **skipPropagation**(L123 · L138)을 담는다
      ★ `skipPropagation` 이 true 가 되는 자리는 하나다 — 백그라운드 재검증(L3490-3493).
        그때 [04]의 전파 게이트(L1235)가 막힌다

 cacheHandler
      --> [03]의 세 번째 겹이 `get` / `set` 을 부르는 대상.
          private 프로덕션에서는 **undefined** 다

 timeoutError / deadlockError
      --> [03]은 `generateCacheEntry` 인자로 **넘기기만** 한다 (L3300-3308 · L3485-3499).
          실제로 발동하는 곳은 `generateCacheEntryImpl` 안이다 —
          L1370-1377 prerender 타임아웃(`workStore.invalidDynamicUsageError` 에 심고 abort) ·
          L1489-1492 개발 타임아웃 · L1563-1571 probe 완료 시 deadlockError
      ★ 그 함수는 이 흐름의 문서 다섯 편 모두가 범위 밖으로 두었다. 스택만 여기서 찍힌다

 workStore.invalidDynamicUsageError
      --> `wrapAsInvalidDynamicUsageError`(L1834)가 `??=` 로 **첫 번째만** 남긴다.
          [04]의 버퍼 스트림이 이 값을 보고 다시 오류를 낸다
```

## 다루지 않는 것

`makeUntrackedHangingPromise` / `makeRuntimeHangingPromise` / `postponeWithTracking` / `throwToInterruptStaticGeneration` 의 본문과 hanging promise 의 구현, `applyOwnerStack` · `captureOuterOwnerStack`(L835)의 소유자 스택 조립, `handlers.ts`(352줄)의 `getCacheHandler` · `getPrivateCacheHandler` · `isCustomCacheHandler` · `getDevTieredCacheHandler` 본문과 `initializeCacheHandlers`(L59)의 등록 순서, `tiered-cache-handler.ts`(208줄)의 2단 위임, `stagedRendering.waitForStage` 와 `RENDER_STAGES_BY_DATA_KIND` 의 단계 정의, `makeDevtoolsIOAwarePromise`, `UseCacheTimeoutError` · `UseCacheDeadlockError` · `NestedDynamicUseCacheError`(`use-cache-errors.ts` 30줄)의 정의, `workUnitStore` 열한 가지 타입 각각의 필드는 이 문서의 범위 밖이다.
