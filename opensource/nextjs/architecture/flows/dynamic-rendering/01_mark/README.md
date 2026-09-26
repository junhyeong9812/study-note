# 01 표시하고 끊는다

상위: [무엇이 동적인지 가려내기](../README.md)

`unstable_noStore()` 를 한 번 부르거나 `fetch` 에 `cache: 'no-store'` 를 붙였을 때 무슨 일이 일어나는가는 **렌더 모드마다 완전히 다르다.** 아무 일도 안 일어나거나, 서브트리가 postpone 되거나, 던져진다. 그 갈림이 이 구획에 있다.

★ `cookies()` 는 여기 오지 않는다. 그쪽은 [README]가 말한 **②(동적 원천 읽기)** 라서 자기 파일에 자기 switch 를 들고 있다 — 아래에서 나란히 본다.

## 위치

`packages/next` / `src/server/app-render` / `dynamic-rendering.ts` L165-L394 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/dynamic-rendering.ts#L165-L394))

## 실제 코드

`markCurrentScopeAsDynamic` 이 **같은 값으로 switch 를 두 번** 한다. 첫째는 빠져나가기 위한 것이다.

```ts
// dynamic-rendering.ts L177-L197
  if (workUnitStore) {
    switch (workUnitStore.type) {
      case 'cache':
      case 'unstable-cache':
        // Inside cache scopes, marking a scope as dynamic has no effect,
        // because the outer cache scope creates a cache boundary. This is
        // subtly different from reading a dynamic data source, which is
        // forbidden inside a cache scope.
        return
      case 'private-cache':
        // A private cache scope is already dynamic by definition.
        return
      case 'prerender-legacy':
      case 'prerender-ppr':
      case 'request':
      case 'generate-static-params':
        break
      default:
        workUnitStore satisfies never
    }
  }
```

```text
 'cache' · 'unstable-cache'  => return   아무 일도 안 일어난다
   주석 L181-184 - 캐시 스코프 안에서는 **바깥 캐시 경계가 이미 캐시를 만들므로**
     스코프를 동적이라 표시해도 효과가 없다. 동적 데이터 원천을 **읽는** 것과는
     미묘하게 다르다 — 그쪽은 캐시 스코프 안에서 금지다
 'private-cache'             => return   이미 정의상 동적이다
 그 밖 넷                     => break    아래로 내려간다

 ★★★ [README]의 "두 종류" 가 여기 한 줄로 나타난다.
   이 함수는 ①(의사 표시)이라서 캐시 경계가 삼켜 버린다

 ★★★ 그 증거가 **호출처 전수**다 (저장소 전체 grep)
   server/lib/patch-fetch.ts  L790 · L1203 · L1251   `cache: 'no-store'` 계열 fetch
   server/web/spec-extension/unstable-no-store.ts L53  `unstable_noStore()`
 => 딱 둘이다. 그리고 그 둘이 파일 헤더 L11 이 ①의 예로 든 바로 그것이다
 => `cookies()` · `headers()` · `draftMode()` 는 **이 함수를 부르지 않는다**
```

## 동작 흐름

```text
 markCurrentScopeAsDynamic(store, workUnitStore, expression)   DYNR L172

 L177  if (workUnitStore) { L178 switch ① — 캐시 스코프면 여기서 끝 (위 실제 코드)

 L202  store.forceDynamic || store.forceStatic 이면 => return
        주석 L199-201 - 이미 전체가 동적이거나, 정적이니 여기서 던지거나
          postpone 하면 안 된다

 L204  store.dynamicShouldError 이면
 L205    => throw StaticGenBailoutError
           `Route ... with \`dynamic = "error"\` couldn't be rendered statically
            because it used \`${expression}\``

 L211  switch ② — 같은 값으로 다시 가른다
 L213    'prerender-ppr'     => postponeWithTracking(route, expression, dynamicTracking)  [02]
 L219    'prerender-legacy'  => workUnitStore.revalidate = 0
 L223                           err = new DynamicServerError(...)
 L226                           store.dynamicUsageDescription = expression
 L227                           store.dynamicUsageStack = err.stack
 L229                           throw err
 L232    'request'           => 개발에서만 workUnitStore.usedDynamic = true
 L235    'generate-static-params' => break   (아무것도)
 L237    default             => workUnitStore satisfies never

 ★★ 같은 `unstable_noStore()` 가 네 갈래로 끝난다 —
   PPR 이면 **그 자리만** 구멍, 옛 정적 생성이면 **던져서 포기**,
   실제 요청이면 **표시만**, generate-static-params 면 **무시**

 ★★★ 그런데 cacheComponents 계열 스토어는 **타입이 막는다** (L174)
   workUnitStore: undefined | Exclude<WorkUnitStore, PrerenderStoreModern>
   PrerenderStoreModern = ModernClient | ModernServer | ModernRuntime | ValidationStoreClient
     (work-unit-async-storage.external.ts L123-127)
 => 그래서 위 switch 에 `'prerender'` 갈래가 **없다.** 들어올 수가 없다
 => 모던 prerender 는 아래 중단 3종과 hanging promise 로 따로 간다
 ★ 대조군 `trackDynamicDataInDynamicRender`(L274)는 열한 종을 다 받는다
 ★ 그래서 docstring L165-171 의 "calling it during a normal prerender will cause
   the entire prerender to abort" 는 **지금 시그니처와 어긋난다** — 남은 문장으로 보인다
   (※ 뒷문장은 내 해석이다)
```

```text
```text
 ★★★ `cookies()` 는 이 함수를 안 거치고 **자기 switch** 를 돈다
      (server/request/cookies.ts L58-120)

   'cache'                  => **throw**  "used `cookies()` inside "use cache".
                                Accessing Dynamic data sources inside a cache
                                scope is not supported."
   'unstable-cache'         => **throw**  (같은 취지, unstable_cache 판)
   'generate-static-params' => **throw**  "runs at build time without an HTTP request"
   'prerender'              => makeHangingCookies(...)        ← 모던 prerender
   'prerender-ppr'          => postponeWithTracking(...)      [02]
   'prerender-legacy'       => throwToInterruptStaticGeneration(...)  (아래)
   'prerender-client' · 'validation-client' => InvariantError
   'prerender-runtime'      => stagedRendering.delayUntilStage(sessionData) 또는 값
   'private-cache'          => 값 그대로
   'request'                => trackDynamicDataInDynamicRender(...) 뒤 값

 => **캐시 스코프에서 정반대다.** markCurrentScopeAsDynamic 은 조용히 return 하고
    cookies() 는 오류를 던진다
 => 이것이 [README] 헤더 L17-20 이 예고한 그 동작이다 —
    "using a dynamic data source inside unstable_cache **should error**"
 ★ 그리고 'cache' 갈래는 `workStore.invalidDynamicUsageError ??= error` 로
   [`'use cache'`]가 읽는 그 필드에도 심는다 (cookies.ts L61-66)
 ★★ 즉 ①과 ②는 **다른 함수로 구현돼 있다.** 같은 함수의 분기가 아니다
```

 ★★ `prerender-legacy` 만 revalidate 를 0 으로 만든다 (L219)

 그리고 같은 일을 하는 함수가 따로 하나 더 있다 —
 throwToInterruptStaticGeneration(expression, store, prerenderStore)   L249

   L255  err = new DynamicServerError(`Route ... couldn't be rendered statically
           because it used \`${expression}\``)
   L259  prerenderStore.revalidate = 0
   L261  store.dynamicUsageDescription = expression
   L262  store.dynamicUsageStack = err.stack
   L264  throw err

 docstring L243-248 - "meant to be used when prerendering **without
   cacheComponents or PPR**. When called during a build it will cause Next.js
   to consider the route as dynamic."

 => 본문 네 줄이 markCurrentScopeAsDynamic 의 'prerender-legacy' 갈래와 같다
 ★★★ 그런데 **앞의 두 관문이 없다** — `forceDynamic || forceStatic` 조기 return(L202)도,
   `dynamicShouldError => StaticGenBailoutError`(L204)도 여기엔 없다
 => 그 관문은 **호출처가 먼저 한다.** `cookies()`(cookies.ts L45 · L52),
    `headers()`(headers.ts L52 · L92), `connection()`(connection.ts L38 · L44) 셋 다
    `forceStatic` 이면 빈 값을 돌려주고 `dynamicShouldError` 면 StaticGenBailoutError 를
    던진 **뒤에야** 여기로 온다. 그래서 `dynamic = "error"` 에서도 `cookies()` 는
    StaticGenBailoutError 로 끝난다 → [동적 API] 흐름 참조
 ★ 나머지 호출처(params · search-params · root-params · use-cache-wrapper)의
   관문 유무는 이 문서에서 확인하지 않았다
 ★ 오류 문구도 다르다 — 이쪽만 expression 을 백틱으로 감싼다 (L256 대 L224)
 ★ 호출처는 일곱이다 — cookies · headers · params · search-params · root-params ·
   connection · use-cache-wrapper(L1869, private 캐시의 'prerender-legacy' 갈래)
```

```text
 ★★★ 중단 함수가 셋이고 **하나는 기록하고 하나는 기록하면 안 된다**

 abortOnSynchronousDynamicDataAccess(route, expression, prerenderStore)   L304  (비공개)
   L309  reason = `Route ${route} needs to bail out of prerendering at this
           point because it used ${expression}.`
   L311  error = createPrerenderInterruptedError(reason)
   L313  prerenderStore.controller.abort(error)     ← **신호를 끊는다**
   L317  dynamicTracking 이 있으면 dynamicAccesses 에 밀어 넣는다
           stack 은 isDebugDynamicAccesses 일 때만 만든다
           주석 L318-319 - "When we aren't debugging, we don't need to create
             another error for the stack trace"

 abortOnSynchronousPlatformIOAccess(route, expression, errorWithStack, prerenderStore)  L328
   L336  syncDynamicErrorWithStack 이 비어 있으면 거기 넣고
   L341    queueMicrotask(() => syncDynamicErrorWithStackPostMicrotask = true)
   L346  그리고 위 비공개 함수를 부른다

 abortAndThrowOnSynchronousRequestDataAccess(...)   L359  => never
   L372  **trackRuntimeDataAccessed(prerenderStore)**  ← 이것만 기록한다
   L375  signal.aborted 가 false 일 때만 중단하고(L381), 서버 쪽 오류를 보존한다
   L391  그리고 항상 throw createPrerenderInterruptedError(...)
```

```text
 ★★★ 셋 중 하나만 "런타임 요청이면 더 줄 수 있다" 고 기록한다 (주석 L365-371)

   "The synchronously accessed request data would have been available during
    a runtime prerender, which would have rendered past this point instead of
    aborting — so a runtime prefetch would produce more content than this
    render. Record that, same as when request data access creates a hanging
    promise (see makeRuntimeHangingPromise). Unlike
    `abortOnSynchronousPlatformIOAccess`, which aborts a runtime prerender
    all the same and therefore must not record anything."

 => 요청 데이터(쿠키·헤더)는 **런타임 prerender 였으면 읽혔을 것**이다.
    그러니 "런타임 프리페치면 더 나온다" 를 남긴다
 => 플랫폼 IO(파일·네트워크)는 런타임 prerender 에서도 똑같이 중단된다.
    그래서 **기록하면 안 된다** — 남기면 헛된 런타임 요청을 부른다
 ★ 두 함수의 이름이 `PlatformIO` 와 `RequestData` 로 갈린 이유가 이 한 줄이다
 => [프리페치]가 `FetchStrategy.PPRRuntime` 으로 다시 물을지 정하는 근거가 여기서 생긴다
```

```text
 ★★ 동기 접근의 오류를 **마이크로태스크로 클라이언트와 서버에 나눈다** (L336-344)

   if (dynamicTracking && dynamicTracking.syncDynamicErrorWithStack === null) {
     dynamicTracking.syncDynamicErrorWithStack = errorWithStack
     queueMicrotask(() => {
       dynamicTracking.syncDynamicErrorWithStackPostMicrotask = true
     })
   }

 주석 L338-340
   "React completes the task that is currently rendering before scheduled
    abort cleanup. Client tracking can attribute the sync IO only during
    that current task; server tracking keeps the error regardless."

 => React 가 **지금 렌더 중인 태스크를 끝낸 뒤에** 중단 정리를 한다.
    그 태스크 안에서만 클라이언트 쪽에 책임을 물을 수 있다
 => 그래서 마이크로태스크 하나로 "현재 태스크가 끝났는가" 를 표시한다
 ★ 읽는 쪽이 `getPendingClientSyncDynamicError`(L151)다 —
   PostMicrotask 가 켜졌으면 **null 을 돌려준다**. 서버 쪽은 그대로 들고 있는다
 ★★ 태스크 경계를 알아내려고 **플래그 하나와 큐 하나**만 쓴다.
   React 내부에 묻지 않는다
 ★★★ 그런데 이 장치가 **세 함수에 고르게 걸려 있지 않다** —
   `abortAndThrowOnSynchronousRequestDataAccess` 는 `aborted === false` 분기 안에서
   `syncDynamicErrorWithStack` 만 세우고 **queueMicrotask 를 걸지 않는다** (L384-389)
 => 요청 데이터 경로에서는 PostMicrotask 가 끝내 켜지지 않아
    `getPendingClientSyncDynamicError` 가 **언제나 그 오류를 돌려준다**
```

## 결과가 쓰이는 곳

```text
 postponeWithTracking 호출
      --> [02]로 넘어간다. PPR 이 그 서브트리를 구멍으로 남긴다

 prerenderStore.controller.abort(error)
      --> [정적 응답]의 cacheComponents prerender 전체가 끝난다.
          [`'use cache'`]가 `renderSignal.aborted` 로 보는 그 신호다

 dynamicTracking.dynamicAccesses
      --> `getFirstDynamicReason`(L159)이 첫 항목의 expression 을 꺼낸다.
          빌드 로그의 "왜 동적인가"

 dynamicTracking.syncDynamicErrorWithStack
      --> [04]의 `throwIfSyncIOUsed` 가 이것만 보고 빌드를 세운다

 trackRuntimeDataAccessed 의 기록
      --> 런타임 프리페치가 더 줄 수 있다는 표시. [프리페치]의 티어 판단으로 간다

 workUnitStore.usedDynamic (개발만)
      --> app-render.tsx L2928 `isStatic = !requestStore.usedDynamic && !workStore.forceDynamic`
          => `setIsrStatus(pathname, isStatic)`. 개발 서버의 **정적/동적 표시**다
```

## 다루지 않는 것

`createPrerenderInterruptedError`(L470)와 digest 체계([02]에서 다룬다), `trackRuntimeDataAccessed` · `makeClientHookHangingPromise`(`dynamic-rendering-utils.ts`)의 본문, `DynamicServerError`(`hooks-server-context`) · `StaticGenBailoutError`(`static-generation-bailout`)의 정의와 두 오류를 받는 쪽, `store.forceDynamic` / `forceStatic` / `dynamicShouldError` 를 `export const dynamic` 설정에서 세우는 과정, `trackDynamicDataInDynamicRender`(L274)의 갈래, `prerenderStore.controller` 를 만드는 쪽([정적 응답])과 중단 뒤의 정리, `server/request/` 의 각 API(`headers()` · `draftMode()` · `connection()` · `params` · `searchParams`)가 고르는 갈래와 `makeHangingCookies` · `makeUntrackedCookies`, 중단 3종을 실제로 부르는 자리(`io-utils.tsx` L30 · L45 의 플랫폼 IO, `draft-mode.ts` L233, `route-modules/app-route/module.ts` L1305, `revalidate.ts` L168), `patch-fetch.ts` 가 `markCurrentScopeAsDynamic` 을 부르는 세 자리의 조건은 이 문서의 범위 밖이다.
