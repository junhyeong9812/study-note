# 02 캐시 키

상위: [`'use cache'` 가 값을 돌려주기까지](../README.md)

캐시 키는 **인자를 RSC 로 직렬화한 것**이다. 그런데 키가 하나가 아니다 — 직렬화 키와 핸들러 키가 따로 있고, 핸들러 키는 루트 파라미터를 알아낸 뒤 **두 번 조회한다**.

## 위치

`packages/next` / `src/server/use-cache` / `use-cache-wrapper.ts` L2035-L2333 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/use-cache/use-cache-wrapper.ts#L2035-L2333))

## 실제 코드

키의 재료가 셋(개발에서는 넷)이다.

```ts
// use-cache-wrapper.ts L2159-L2167
  const cacheKeyParts: CacheKeyParts = hmrRefreshHash
    ? [buildId, id, args, hmrRefreshHash]
    : [buildId, id, args]

  const encodeCacheKeyParts = () =>
    encodeReply(cacheKeyParts, {
      temporaryReferences,
      signal: hangingInputAbortSignal,
    })
```

```text
 buildId  workStore.deploymentId || workStore.buildId      L1990
 id       컴파일러가 붙인 함수 ID
 args     실제 인자 (아래에서 덮어쓰인 것)
 hmrRefreshHash  개발에서만                                 L1997

 ★★ buildId 가 들어가는 이유가 임시다 (주석 L1986-1989)
   "Because the Action ID is not yet unique per implementation of that Action
    we can't safely reuse the results across builds yet. In the meantime we add
    the buildId to the arguments as a seed to ensure they're not reused.
    Remove this once Action IDs hash the implementation."
 => 함수 ID 가 **구현 내용을 해시하지 않는다.** 코드를 고쳐도 ID 가 같을 수 있다
 => 그래서 빌드마다 키를 갈아 버린다. 같은 이유로 개발에서는 HMR 해시를 더 넣는다
   (주석 L1992-1996 - "This is a very coarse approach")
```

## 동작 흐름

```text
 L2035  isPageOrLayoutSegmentFunction = false

 L2047  isPageSegmentFunction(args) 이면    ← page · generateMetadata · generateViewport
 L2093  else if (isLayoutSegmentFunction(args)) 이면
 L2123  boundArgsLength > 0 이면 — 암호화된 bound 인자를 풀어 맨 앞에 넣는다
 L2159  cacheKeyParts 조립
 L2171  switch (workUnitStore.type) — 직렬화 방식이 갈린다
 L2240  probe 모드면 여기서 끝낸다 (개발 서버 전용)
 L2289  serializedCacheKey  — 문자열이면 그대로, FormData 면 encodeFormData
 L2306  cacheHandlerKeyBase — 개발 + private 이면 쿠키·헤더를 덧붙인다
 L2317  cacheHandlerKey     — 아는 루트 파라미터가 있으면 그것도 덧붙인다
```

```text
 ★★★ page / layout 이면 **함수를 바꿔치기한다** (L2047-2122)

 주석 L2037-2046
   "For page and layout segment functions ... the cache function is
    overwritten, which allows us to apply special handling for params and
    searchParams. For pages and layouts we're using the outer params prop,
    and not the inner one that was serialized/deserialized. While it's not
    generally true for "use cache" args, in the case of `params` the inner
    and outer object are essentially equivalent, so this is safe to do
    (including fallback params that are hanging promises). It allows us to
    avoid waiting for the timeout, when prerendering a fallback shell of a
    cached page or layout that awaits params."

 L2055  props = { params: outerParams }        ← searchParams 와 $$isPage 는 뺀다
 L2063  isPrivate 이면 props.searchParams = outerSearchParams 도 넣는다
 L2066  args = [props, ...otherOuterArgs]
 L2068  fn = { [name]: async (...) => originalFn.apply(null, [ ... ]) }[name]

 => `params` 는 **직렬화를 거치지 않은 바깥 객체**를 쓴다.
    직렬화하면 hanging promise 인 fallback params 때문에 타임아웃을 기다리게 된다
 ★ `{ [name]: async ... }[name]` — 함수 이름을 보존하려고 객체 리터럴을 경유한다
```

```text
 ★★★ public 캐시에서 searchParams 를 읽으면 **오류를 내는 객체**가 온다 (L2079-2088)

 L2079  searchParams:
 L2080    innerSearchParams ??
 L2088    makeErroringSearchParamsForUseCache()

 주석 L2081-2087
   "For public caches, search params are omitted from the cache key (and the
    serialized args) to avoid mismatches between prerendering and resuming a
    cached page that does not access search params. This is also the reason why
    we're not using a hanging promise for search params. For cached pages that
    do access them, which is an invalid dynamic usage, we need to ensure that
    an error is shown."

 => public 캐시는 searchParams 를 **키에서 뺀다.** 안 읽는 페이지에서
    prerender 와 resume 이 어긋나는 것을 막으려는 것이다
 => 그런데 읽으면 잘못된 사용이므로, hanging promise 가 아니라 **오류 객체**를 준다.
    hanging promise 면 조용히 멈추기만 하고 오류가 안 보인다
 ★ private 캐시는 반대다 — searchParams 를 읽어도 되고 키에 들어간다 (L2061-2063)
```

```text
 ★ layout 쪽은 슬롯만 통과시킨다 (L2093-2122)

 L2097  { params: outerParams, $$isLayout, ...outerSlots } 를 분해하고
 L2106  args = [{ params: outerParams, ...outerSlots }, ...]   ← $$isLayout 을 뺀다

 주석 L2101-2105 - 슬롯은 layout 컴포넌트에만 넘어가고
   generateMetadata · generateViewport 에는 안 넘어간다. 그 경우 빈 객체라
   그냥 펼쳐도 문제가 없다
 ★ `$$isPage` · `$$isLayout` 이 판별 표지다 (L3575 isPageSegmentFunction ·
   L3591 isLayoutSegmentFunction). **런타임이 심고** 여기서 떼어낸다 —
   심는 곳이 넷이다 (저장소 전수 grep, `crates/` 에는 없다)
     server/app-render/create-component-tree.tsx  L875 `$$isPage` · L1051 `$$isLayout`
       (`isUseCacheFunction(PageComponent)` 일 때만 붙인다)
     lib/metadata/resolve-metadata.ts             L560-561 (generateMetadata · generateViewport 용)
   => [트리 조립]이 페이지·레이아웃을 만들 때, [메타데이터]가 메타 함수를 부를 때
      표지를 붙여 넘기고 `cache()` 가 받아서 뗀다
```

```text
 ★★ bound 인자는 **암호화돼서 온다** (L2123-2146)

 L2130  encryptedBoundArgs = args.shift()
 L2131  boundArgs = await decryptActionBoundArgs(id, encryptedBoundArgs)
 L2145  args.unshift(boundArgs)

 InvariantError 셋이 붙어 있다
 L2124  args.length === 0            암호화된 bound 인자가 첫 인자로 안 왔다
 L2133  !Array.isArray(boundArgs)    복호화 결과가 배열이 아니다
 L2139  boundArgsLength !== 길이      개수가 안 맞는다

 => 클로저로 캡처한 값이 서버 액션과 같은 방식으로 암호화돼 왕복한다
 ★ 세 검사 모두 InvariantError 다 — 컴파일러가 잘못한 경우뿐이라는 뜻이다
```

```text
 ★★★ prerender 에서는 **직렬화 중에도 동적 접근을 감시한다** (L2181-2207)

 L2181  case 'prerender': (그리고 'prerender-runtime' 이 fallthrough)
 L2182    if (!isPageOrLayoutSegmentFunction) {
 L2190      dynamicAccessAbortController = new AbortController()
 L2192      encodedCacheKeyParts = await dynamicAccessAsyncStorage.run(
 L2193        { abortController: dynamicAccessAbortController }, encodeCacheKeyParts)
 L2197      signal.aborted 이면
 L2200        => return makeRuntimeHangingPromise(..., 'dynamic "use cache"', ...)

 주석 L2183-2189
   "If the "use cache" function is not a page or layout segment function, we
    need to track dynamic access already when encoding the arguments. If params
    are passed explicitly into a "use cache" function (as opposed to receiving
    them automatically in a page or layout), we assume that the params are also
    accessed. This allows us to abort early, and treat the function as dynamic,
    instead of waiting for the timeout to be reached."

 => params 를 **손으로 넘겼으면 읽는다고 가정한다.** 그러면 즉시 동적으로 처리한다
 => page/layout 이면 이 감시를 건너뛴다 — 위에서 바깥 params 로 바꿔치기해
    직렬화 자체를 안 하기 때문이다 (그래서 fallthrough 로 아래로 내려간다)
 ★ 남은 일곱 갈래 + `undefined` 는 그냥 `await encodeCacheKeyParts()` 다 (L2210-2223)
 ★ L2213-2215 에 TODO(restart-on-cache-miss) - page 컴포넌트의 params/searchParams 는
   tasky 라 정적 단계에서 안 풀리고, **캐시를 아예 놓칠 수 있다**고 적혀 있다
```

```text
 ★★★ 키가 **셋**이다

 serializedCacheKey   L2289  직렬화한 인자 그대로 (문자열이면 빠른 길, 아니면 FormData 인코딩)
                             주석 L2291-2292 - "We let the CacheHandler Convert it to
                               an ArrayBuffer if it wants to"
                             ==> RDC 와 요청 내 중복 제거가 이 키를 쓴다

 cacheHandlerKeyBase  L2306  = serializedCacheKey
                             + (개발 && private 이면) 쿠키·헤더 서픽스

 cacheHandlerKey      L2317  = cacheHandlerKeyBase
                             + (아는 루트 파라미터가 있으면) 루트 파라미터 서픽스

 주석 L2299-2305 - 거친(coarse) 핸들러 키다. 루트 파라미터를 안 읽었으면 항목을
   바로 가리키고, 읽었으면 **리다이렉트 항목**을 가리킨다. 거기서 구체적 키를 만든다
 ★ `rootParams` 는 `unstable_cache` 안에 중첩됐을 때 undefined 다 (주석 L2316)
```

```text
 ★★ 루트 파라미터를 **처음에는 모른다** (L376-407 · L2296-2322)

 knownRootParamsByFunctionId: Map<string, Set<string>>   L376  모듈 전역
 addKnownRootParamNames(id, names)                       L378  합집합으로 누적

 => 함수가 어떤 루트 파라미터를 읽는지 **한 번 겪어 보고 배운다.**
    배우기 전에는 거친 키로 리다이렉트 항목을 읽고, 배운 뒤에는 바로 구체적 키를 만든다
 => computeRootParamsCacheKeySuffix(L394)는 이름을 **정렬해** JSON 으로 만든다.
    비어 있으면 빈 문자열이라 키가 그대로다
 ★ 프로세스 안에만 사는 학습이다. 재시작하면 다시 한 번 우회한다
```

```text
 ★★ 개발의 private 키는 **쿠키와 헤더 전체**로 갈린다 (L467-488)

 computePrivateCacheKeyRequestSuffix(cookies, headers)  L467
   쿠키   COOKIES_EXCLUDED_FROM_PRIVATE_CACHE_KEY 를 뺀 전부, 이름순 정렬
   헤더   HEADERS_EXCLUDED_FROM_PRIVATE_CACHE_KEY 를 뺀 전부, 이름순 정렬
   둘 다 비면 빈 문자열

 제외 쿠키는 하나 — NEXT_INSTANT_TEST_COOKIE
   주석 L409-412 - 내비게이션 잠금 중에 켜졌다 꺼지므로 넣으면 **헛된 미스**가 난다
 제외 헤더는 **27개** — accept · cache-control · pragma · sec-fetch-* · x-forwarded-* 등
   주석 L417-427 - 브라우저 리로드는 `cache-control`/`pragma` 를 붙이는데 최초
     내비게이션은 안 붙인다. `accept`/`sec-fetch-*` 는 HTML 내비게이션과 RSC·프리페치
     요청이 다르다. 나머지는 연결·프록시 수준이라 애플리케이션 데이터가 아니다
   ★ `cookie` 헤더도 제외한다 — 쿠키는 위에서 따로 다루므로 중복이 되고,
     거기서 뺀 쿠키가 다시 들어와 버린다

 ★★★ TODO(L458-466)가 이것이 **어림짐작**이라고 스스로 적는다
   "It's a heuristic: it still over-keys (a cache that reads only one cookie or
    header varies by all of them) and the header denylist is necessarily
    incomplete. Follow up by tracking which cookies and headers a cache function
    actually reads (the same mechanism root params use via `readRootParamNames`)"
 => 쿠키 하나만 읽는 캐시도 **전부로 갈린다.** 거부 목록은 완전할 수 없다
 => 해법은 이미 알고 있다 — 루트 파라미터가 쓰는 그 방식(읽은 것만 기록)이다
 ★ 이것은 **개발 전용**이다. 프로덕션의 private 캐시는 핸들러가 없어 이 키가 없다
 ★★ 그리고 주석 L2150-2158 이 그 이유를 끝까지 적는다 — 프로덕션의 private 항목은
   동적 요청에서는 immutable RDC 가 **아예 제외**하고, 런타임 프리페치에서는 mutable 이지만
   **요청 수명만큼만** 산다. 요청을 넘기지 않으니 요청별 키가 필요 없다
```

## 결과가 쓰이는 곳

```text
 serializedCacheKey
      --> [03]의 첫째 겹(RDC)과 둘째 겹(요청 내 중복 제거)의 키.
          요청 안에서는 루트 파라미터가 고정이라 이 거친 키로 충분하다

 cacheHandlerKey
      --> [03]의 셋째 겹이 `cacheHandler.get` / `set` 에 넘기는 키

 args (덮어쓴 것) · fn (바꿔치기한 것)
      --> [04]의 항목 생성이 이 `fn` 을 부른다. `originalFn` 을 직접 부르지 않는다

 knownRootParamsByFunctionId
      --> 같은 함수의 다음 호출. 리다이렉트 항목 왕복을 건너뛴다

 temporaryReferences
      --> 직렬화와 역직렬화 양쪽에 같은 집합을 쓴다.
          [README]의 `createFromReadableStream` 도 이것을 받는다
```

## 다루지 않는 것

`encodeReply` · `encodeFormData`(L1663) · `decryptActionBoundArgs` 의 직렬화 형식과 `createClientTemporaryReferenceSet` 의 임시 참조, `isPageSegmentFunction`(L3575) · `isLayoutSegmentFunction`(L3591) 의 판별 세부와 `$$isPage` / `$$isLayout` 을 심는 두 파일의 조건 세부, `makeErroringSearchParamsForUseCache` 의 구현, `dynamicAccessAsyncStorage` 와 fallback params 의 hanging promise, `createHangingInputAbortSignal`(L1999)과 `getHmrRefreshHash`, probe 경로(L2240-2287)의 워커 왕복과 `use-cache-probe-scheduler.ts`(195줄), `NEXT_INSTANT_TEST_COOKIE` 와 Instant Navigation Testing, 루트 파라미터가 실제로 리다이렉트 항목에서 읽히는 자리([03]에서 다룬다)는 이 문서의 범위 밖이다.
