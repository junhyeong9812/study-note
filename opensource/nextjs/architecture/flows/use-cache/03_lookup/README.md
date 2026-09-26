# 03 캐시를 세 겹으로 찾는다

상위: [`'use cache'` 가 값을 돌려주기까지](../README.md)

`cache()` 의 1206줄(L2335-3540)이 **찾는 일**이다. 순서가 정해져 있다 — Resume Data Cache → 같은 요청 안의 다른 호출 → 다른 요청과 공유. 큰 겹은 셋이지만 **실제로 순서대로 보는 저장소는 다섯**이다.

## 위치

`packages/next` / `src/server/use-cache` / `use-cache-wrapper.ts` L2335-L3540 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/use-cache/use-cache-wrapper.ts#L2335-L3540))

## 실제 코드

셋째 겹에는 **조회를 두 번 하는 길**이 있다.

```ts
// use-cache-wrapper.ts L3048-L3065
          // Check if this is a redirect entry (coarse key → specific key).
          // Redirect entries have private tags encoding the root param names
          // (one tag per param name, prefixed with _N_RP_).
          if (entry && rootParams) {
            const paramNames = new Set<string>()
            for (const tag of entry.tags) {
              if (tag.startsWith(NEXT_CACHE_ROOT_PARAM_TAG_ID)) {
                paramNames.add(tag.slice(NEXT_CACHE_ROOT_PARAM_TAG_ID.length))
              }
            }
            if (paramNames.size > 0) {
              addKnownRootParamNames(id, paramNames)
              cacheHandlerKey =
                cacheHandlerKeyBase +
                computeRootParamsCacheKeySuffix(rootParams, paramNames)
              entry = await cacheHandler.get(cacheHandlerKey, implicitTags)
            }
          }
```

```text
 ★★★ 루트 파라미터를 태그로 실어 보낸다

 NEXT_CACHE_ROOT_PARAM_TAG_ID = '_N_RP_'   (lib/constants.ts L38)

 거친 키로 읽은 항목의 태그에 `_N_RP_<이름>` 이 있으면
   그 항목은 값이 아니라 **리다이렉트 항목**이다
   => 이름들을 모아 addKnownRootParamNames 로 기억하고
   => 구체적 키를 만들어 **한 번 더 get 한다**

 => "이 함수가 어떤 루트 파라미터를 읽는가" 를 캐시 항목 자신이 실어 온다.
    별도 메타데이터 저장소가 없다
 ★ 태그 하나에 파라미터 이름 하나다. 여러 개면 태그가 여러 개 붙는다
 ★ 두 번째 get 은 조건 없이 한다 — 첫 get 이 리다이렉트였으므로 값이 아니다
```

## 동작 흐름

```text
 L2335  if (resumeDataCache)                    ← 첫째 겹: RDC
 L2340    dynamicCacheKeys 에 있으면 — `prerender` · `prerender-runtime` **둘만**
            hanging promise 로 return 한다 (L2346). 나머지 일곱은 break 로 빠져
            아래 RDC get 으로 그대로 내려간다 (L2341-2362)
 L2368    cacheSignal.beginRead()
 L2370    rdcEntry = resumeDataCache.cache.get(serializedCacheKey)
 L2371    있으면  ... (337줄)
 L2708    없으면  미스 처리 — prerender 갈래가 둘로 갈린다

 L2786  if (stream === undefined)                ← 둘째 겹: 같은 요청 안
 L2787    pendingInvocation   = workStore.pendingCacheInvocations?.get(serializedCacheKey)
 L2794    completedInvocation = workStore.**completedCacheInvocations**?.get(...)  ← **다른 맵**
 L2800    joinedInvocation = pendingInvocation ?? completedInvocation
 L2802    있으면 그 결과에 합류한다

 L2863  if (stream === undefined)                ← 셋째 겹: 요청 사이 + 리더
 L2864    resolvableSharedCacheResult = new ResolvableSharedCacheResult()
 L2903    skipCrossRequestDedupe = isPrivate && !__NEXT_DEV_SERVER
 L2911    while (stream === undefined) {
 L2912      crossRequestPendingCacheInvocations.get(cacheHandlerKey)
 L2916        있으면 합류 — **루트 파라미터가 어긋나면 키를 다시 계산해 루프를 돈다**
 L3018        없으면 내가 리더가 된다
 L3036        refreshTagsByCacheKind.get(kind) 가 미해소면 **await 한다** (L3038-3040)
               => 종류별 refreshTags 가 풀리기 전에는 조회하지 않는다
 L3045        **if (cacheHandler && !shouldForceRevalidate(...))** ← 이 게이트가 핵심이다
 L3046          cacheHandler.get(cacheHandlerKey, implicitTags)   (위 실제 코드)
 L3068        항목이 있으면 버릴지 판단한다
 L3106        revalidate 0 이거나 expire 가 5분 미만이면 — 갈래 아홉
 L3186        stale 이 5분 미만이면 — 또 아홉 갈래
 L3243        미스면 => generateCacheEntry (L3300)
 L3332          저장은 **draft mode 가 아닐 때만** — `if (!workStore.isDraftMode)` 가
                 RDC 저장과 핸들러 저장 둘 다 감싼다
 L3457          그리고 히트여도 revalidate 를 넘겼으면 백그라운드 재검증을 건다
                 (`currentTime > entry.timestamp + entry.revalidate * 1000`, L3457-3458)
 L3375        히트면 => stream = entry.value (L3398)
 L3536    catch => resolvableSharedCacheResult.reject(error); throw

 L3562  createFromReadableStream(stream, ...)
```

```text
 ★★ 세 겹이 쓰는 키가 다르다

 첫째 RDC        serializedCacheKey    (거친 키)
 둘째 요청 안    serializedCacheKey    (거친 키)
 셋째 요청 사이  cacheHandlerKey       (루트 파라미터·쿠키까지 붙인 키)

 주석 L2780-2785 가 이유를 적는다
   "Within a single request, root params are fixed, so the coarse key
    (serializedCacheKey) is sufficient. ... This also saves cache handler `get`
    calls which may be HTTP round-trips for remote handlers."

 => 한 요청 안에서는 루트 파라미터가 변하지 않으니 거친 키로 충분하다
 => 그리고 원격 핸들러의 `get` 은 **HTTP 왕복**일 수 있다. 그것을 아끼는 것이 둘째 겹의 값어치다
```

```text
 ★★★ 합류의 조건이 pending 과 completed 로 다르다 (주석 L2790-2793)

   "A pending invocation is joined unconditionally: its fill is shared, so
    every joiner receives whatever that fill produces. A completed one is a
    stored entry instead, so it is only reused when the caller hasn't asked
    to bypass caches, and only if nothing has invalidated it since."

 => 진행 중인 것은 **조건 없이** 합류한다. 이미 같은 fill 을 쓰기로 한 것이기 때문이다
 => 완료된 것은 저장된 항목이므로 우회 요청(`shouldForceRevalidate`)과 무효화를 다시 본다
 ★★ `shouldForceRevalidate`(L3603-3617)는 합류만 막는 것이 아니다 —
   셋째 겹의 `cacheHandler.get` **자체를 끈다** (L3045).
   켜지는 조건: `isOnDemandRevalidate` · `isDraftMode`, 개발에서는
   요청 헤더 `cache-control: no-cache` 또는 캐시 스토어의 `forceRevalidate`
 ★★★ 그래서 맵이 **둘**이다 — `pendingCacheInvocations`(L2871) 와
   `completedCacheInvocations`(L2884). 완료되면 `cleanupAndRetain`(L321-326)이
   앞의 것에서 지우고 뒤의 것으로 **옮긴다**
 ★★ 그리고 뒤의 맵은 **조건부로만 만들어진다** (L2882-2888) —
   `isPrivate || !isBuiltInCacheHandler(kind)` 일 때만이다.
   내장 핸들러 + public 이면 맵 자체가 `undefined` 다 (아래 ★★ 와 이어진다)
```

```text
 ★★ 완료된 것을 요청 끝까지 들고 있을지가 **핸들러 종류로 갈린다** (주석 L2876-2881)

   "Retain the completed entry for the rest of the request where a later
    invocation would otherwise repeat real work: private caches have no cache
    handler to fall back on in production, and a platform- or config-supplied
    handler may be remote, so a second `get` can be a round trip. A built-in
    handler read is a map lookup, so retaining its entries would hold a forked
    stream buffer for nothing."

 => 내장 핸들러는 맵 조회라서 **안 들고 있는다.** 들고 있으면 포크된 스트림 버퍼만 낭비다
 => private(프로덕션)과 원격 핸들러는 들고 있는다
 ★ 최적화의 방향이 한쪽이 아니다 — 싼 조회는 다시 하고, 비싼 조회는 기억한다
```

```text
 ★★★ 요청 사이 공유에서 private 은 빠진다 (L2903, 주석 L2896-2902)

 L2903  const skipCrossRequestDedupe = isPrivate && !process.env.__NEXT_DEV_SERVER

   "Cross-request deduplication lets concurrent requests for the same key
    share a single fill. Private caches are skipped in production, where they
    hold request-specific data that must not be shared across requests. In
    development they're persisted and keyed by the request's cookies and
    headers, so concurrent requests with identical request data should share
    a fill too; that request-scoped `cacheHandlerKey` keeps requests with
    different cookies or headers in separate entries."

 => private 캐시가 요청 사이로 새면 **다른 사용자의 데이터가 섞인다.** 그래서 건너뛴다
 => 개발에서는 [02]에서 본 쿠키·헤더 서픽스가 키를 갈라 주므로 공유해도 된다
 ★ `crossRequestPendingCacheInvocations`(L334)는 **모듈 전역 Map** 이다.
   요청 스토어가 아니라 프로세스에 산다
```

```text
 ★★★ 세 겹이 공유하는 단위가 `SharedCacheEntry`(L203-231)다

   private stream                    내부에 스트림 하나
   public readonly pendingMetadata   메타데이터 약속
   fork()                            **tee() 로 갈라** 하나를 주고 남은 쪽을 자기가 쥔다

 주석 L222-225 - "Tee the stream: returns a copy for the caller, replaces the
   internal stream with the remaining branch for future callers.
   **Both the leader and joiners call this — everyone gets a fork.**"
 주석 L206-209 - 요청 간 합류자는 fork() 전에 `pendingMetadata` 를 **await 해야** 한다
   (루트 파라미터 검증 때문이다). 요청 내 합류자는 `.then()` 으로 흘려보낸다

 => 스트림은 한 번 읽으면 소진되므로, 합류란 곧 **tee 로 갈라 받는 것**이다
 => 리더도 fork 를 받는다 — 원본을 쥐는 주인이 따로 없다
 ★ 리더 히트(L3434) · 리더 생성(L3366) · 요청 간 합류(L2964) · 요청 내 합류(L573)가
   전부 이 한 클래스를 거친다. 아래 "루프" 의 재시도도 이 약속을 먼저 기다린다

 ★★ 루프가 있는 이유가 하나다 (주석 L2906-2910)

   "The loop handles cross-request root param mismatches: when a
    cross-request joiner discovers that the leader's root params differ
    from its own, it retries with a recomputed cacheHandlerKey. The loop
    exits when stream is assigned (cross-request joiner match or leader
    path) or via early return (prerender-dynamic)."

 => 리더가 읽는 루트 파라미터를 합류자가 미리 알 수 없다.
    합류해 보고 다르면 키를 다시 만들어 **한 번 더 돈다**
 ★ 나가는 길이 둘 — `stream` 이 정해지거나, prerender-dynamic 으로 조기 return
```

```text
 ★★★ 미스 판정이 개발과 프로덕션에서 다르다 (L3243-3260)

   entry === undefined
   || currentTime > entry.timestamp + (개발 ? Math.max(entry.expire, 300) : entry.expire) * 1000
   || (workStore.isStaticGeneration && currentTime > entry.timestamp + entry.revalidate * 1000)

 주석 L3245-3251
   "In dev, the built-in default handler retains a short-`expire` entry for at
    least `MIN_PRERENDERABLE_EXPIRE`, both when used directly and when fronting
    a custom cache handler. Apply that same minimum here so the retained entry
    is served and re-warmed in the background (below), rather than blocking to
    regenerate it on every read. The entry's real `expire` is untouched, so
    staging still treats it as dynamic."

 => 개발에서는 `expire` 에 **5분 하한**을 씌워 읽는다. 항목 자체는 안 고친다
 => 셋째 조건은 `workStore.isStaticGeneration` 일 때만 본다.
    그 정의는 "빌드" 가 아니라 **동적 응답이 허용되지 않은 렌더**다
      work-store.ts L116-119
        !renderOpts.supportsDynamicResponse && !isDraftMode && !isPossibleServerAction
    ★ 빌드 시점은 별도 필드 `workStore.isBuildTimePrerendering` 로 구분하고
      이 파일도 그것을 따로 쓴다 (L1348)
    그때는
    그때는 stale 항목을 쓰면 prerender 의 수명이 불필요하게 짧아진다 (주석 L3263-3266)
 ★ 즉 **런타임 요청은 stale 항목을 그냥 쓴다.** revalidate 는 백그라운드 갱신의 기준일 뿐이다
```

```text
 ★★ 생성은 **깨끗한 AsyncLocalStorage 스냅샷**에서 돈다 (주석 L3268-3274)

   "We need to run this inside a clean AsyncLocalStorage snapshot so that the
    cache generation cannot read anything from the context we're currently
    executing which might include request specific things like cookies() inside
    a React.cache().
    Note: It is important that we await at least once before this because it
    lets us pop out of any stack specific contexts as well - aka "Sync" Local
    Storage."

 => 캐시 본체가 현재 요청의 맥락을 **읽을 수 없게** 끊는다.
    `React.cache()` 안의 `cookies()` 같은 것이 새어 들어오는 것을 막는다
 ★★ 그리고 "그 전에 최소 한 번 await 해야 한다" 고 적는다 —
   동기 스택에 묶인 컨텍스트("Sync" Local Storage)는 await 를 넘겨야 벗어난다
```

```text
 ★ 히트일 때도 그냥 돌려주지 않는다 (L3375-3423)

 L3376  entryMetadata 를 조립한다
        hasExplicitRevalidate / hasExplicitExpire / dynamicNestedCacheError = undefined
        주석 L3383-3388 - 핸들러에서 온 기존 항목은 명시적 수명이 있었는지 **알 수 없다.**
          그 정보는 prerender 중 새 항목을 만들 때만 필요하고 그때는 RDC 를 쓰니 안전하다
 L3395  maybePropagateCacheEntryMetadata(cacheContext, entryMetadata)   → [04]
 L3398  stream = entry.value     주석 L3397 - "even if it's stale"
 L3402  resumeDataCache?.mutable 이면 항목을 **복제해** RDC 에도 넣는다 (cloneCacheEntry)
        주석 L3412-3413 - RDC 는 페이지 단위이고 루트 파라미터는 페이지 안에서 고정이라
          **언제나 거친 키**를 쓴다

 => 핸들러에서 읽은 것을 RDC 로 끌어올린다. 같은 페이지의 다음 단계가 핸들러를 다시 안 본다
 ★ 스트림을 복제하는 이유 — 한 번 읽으면 소진되므로 돌려줄 것과 저장할 것이 따로 필요하다
```

```text
 ★★★ RDC 미스가 prerender 에서 **경고를 띄운다** (L2708-2777)

 'prerender' 이고 resumeDataCache.mutable === false 이면
   => makeRuntimeHangingPromise  (fallback 셸을 만드는 중이고, 미스는 fallback param 의존을 뜻한다)
   주석 L2718-2730 - phase-1 prerender 가 미리 채운 **읽기 전용 씨앗**이다.
     여기서 미스면 캐시 키가 fallback param 에 의존한다는 뜻이다.
     params 를 async 함수로 변환해 넘기는 경우는 계측(instrumentation)을 빠져나가는데
     이 검사가 그것까지 잡는다. NAR-136 에서 개선할 예정이라고 적혀 있다

 'prerender-runtime' (그리고 위에서 fallthrough) 이고 !cacheSignal 이면
   => console.warn + makeRuntimeHangingPromise
   주석 L2741-2748 - cacheSignal 이 null 이면 **최종 prerender** 다.
     그렇다면 모든 캐시가 워밍 단계에서 채워졌어야 한다.
     여기서 미스면 캐시 키가 **비결정적**이라는 뜻이다 (예: 배열 순서가 불안정)
   경고 문구 (L2751) - "Unexpected cache miss after cache warming phase during prerendering.
     This is likely caused by non-deterministic arguments that differ between the
     cache warming phase and the final prerender phase (e.g. unstable array order).
     Ensure that arguments passed to cached functions are deterministic."

 => 캐시 키가 비결정적이면 **빌드가 조용히 망가지지 않고 경고가 뜬다**
 ★ 그래도 던지지 않는다. hanging promise 로 동적 구멍을 만들어 넘어간다 —
   주석 L2754-2757 이 "비정상이라 런타임 prerender 가 풀 수 있을지 알 수 없으니
   보수적으로 런타임 데이터로 취급한다. 대가는 중복 런타임 프리페치 한 번뿐" 이라고 적는다
```

## 결과가 쓰이는 곳

```text
 stream
      --> [README]의 `createFromReadableStream` 이 RSC 로 되돌린다.
          세 겹 중 어디서 왔든 같은 자리로 모인다

 resolvableSharedCacheResult
      --> 요청 사이 합류자들이 await 하는 약속. 리더가 resolve / reject 한다
      --> 리더가 던지면 합류자 전부가 같은 오류를 받는다 (L3536-3538)

 workStore.pendingCacheInvocations (Map, 요청 단위)
      --> 둘째 겹. 요청이 끝나면 함께 사라진다

 crossRequestPendingCacheInvocations (Map, 모듈 전역 L334)
      --> 셋째 겹. 프로세스에 산다

 cacheHandlerKey (두 번째 조회로 좁혀진 것)
      --> 이후의 `set` 도 이 키로 한다. 그리고 [02]의 학습 맵에 남는다

 resumeDataCache.cache
      --> 핸들러에서 읽은 항목이 복제돼 올라간다. 같은 페이지의 다음 단계가 여기서 읽는다
```

## 다루지 않는 것

RDC 히트 경로(L2371-2707, 337줄)의 태그 재검증 검사·짧은 수명 처리·`serveJoinedCacheEntry`(L566)·`saveSharedCacheEntryToResumeDataCache`(L528) 본문, 둘째 겹 합류 경로(L2802-2858)의 스트림 포크와 `cloneCacheResult`(L1627) · `getNthCacheResult`(L1656), 셋째 겹 합류 경로(L2916-3015)의 루트 파라미터 어긋남 재시도 세부와 `ResolvableSharedCacheResult`(L254-327) 의 구현, `shouldDiscardCacheEntry`(L3635) · `isRevalidatedAfter`(L3706) · `shouldForceRevalidate`(L3603)의 판정 규칙, `implicitTags` 와 `expirationsByCacheKind` 의 지연 해소, `revalidate === 0` / `expire < 5분` / `stale < 5분` 두 갈래 안의 아홉 가지 스토어별 처리(L3106-3240), `saveToCacheHandler`(L605) 와 백그라운드 재워밍, `cacheSignal.beginRead` / `endRead` 의 균형 규칙과 staged rendering 의 경계 판정, `getResumeDataCache` 와 RDC 자체의 구조, `SharedCacheEntry.fork()` 가 만드는 tee 분기의 수명과 `CacheResultMetadata`(L186-196)의 필드, `refreshTagsByCacheKind` 에 값을 넣는 쪽, `shouldForceRevalidate` 가 개발에서 보는 스토어별 갈래(L3611-3633), 백그라운드 재검증의 개발 전용 추가 조건(L3459-3483)은 이 문서의 범위 밖이다.
