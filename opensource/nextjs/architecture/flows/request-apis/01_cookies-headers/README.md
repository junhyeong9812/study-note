# 01 요청 데이터를 읽는 두 API

상위: [동적 API 가 값을 내주기까지](../README.md)

`cookies()` 와 `headers()` 는 결말표가 **한 칸도 다르지 않다.** 둘 다 요청 데이터라서, 정적 prerender 에서는 "런타임 요청이면 채울 수 있다" 를 기록하며 매달리고, 런타임 prerender 에서는 세션 단계까지 기다렸다 값을 준다. 다른 것은 **관문의 순서**, 그리고 개발 모드에서 약속 객체에 붙이는 덫이다.

## 위치

`packages/next` / `src/server/request` / `cookies.ts` L33-L156 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/cookies.ts#L33-L156))

`packages/next` / `src/server/request` / `headers.ts` L40-L170 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/headers.ts#L40-L170))

## 실제 코드

개발 모드에서 `cookies()` 가 돌려주는 약속에는 **동기 메서드 이름들이 덫으로 붙어 있다.**

```ts
// cookies.ts L243-L262
function instrumentCookiesPromiseWithDevWarnings(
  promise: Promise<ReadonlyRequestCookies>,
  route: string | undefined
) {
  Object.defineProperties(promise, {
    [Symbol.iterator]: replaceableWarningDescriptorForSymbolIterator(
      promise,
      route
    ),
    size: replaceableWarningDescriptor(promise, 'size', route),
    get: replaceableWarningDescriptor(promise, 'get', route),
    getAll: replaceableWarningDescriptor(promise, 'getAll', route),
    has: replaceableWarningDescriptor(promise, 'has', route),
    set: replaceableWarningDescriptor(promise, 'set', route),
    delete: replaceableWarningDescriptor(promise, 'delete', route),
    clear: replaceableWarningDescriptor(promise, 'clear', route),
    toString: replaceableWarningDescriptor(promise, 'toString', route),
  })
  return promise
}
```

```text
 ★★★ Promise 객체에 `get` · `getAll` · `has` · `set` · `delete` · `clear` ·
     `size` · `toString` · `Symbol.iterator` **아홉 개**를 속성으로 심는다

 => `cookies().get('x')` 처럼 await 없이 쓰면 그 속성의 getter 가 걸린다 —
      L272  warnForSyncAccess(route, `\`cookies().${prop}\``)
      L273  return undefined
 => 경고 문구 (L315)
      "`cookies()` returns a Promise and must be unwrapped with `await` or
       `React.use()` before accessing its properties."
 ★ 경고 문구 자체가 말한다 — "returns a Promise and must be unwrapped".
   **await 없이 쓰던 사용법을 붙잡는 덫**이다
   ※ 이 API 들이 동기에서 비동기로 바뀐 커밋이 `05f159dffc`
     "[Breaking] Update Dynamic APIs to be async (#68812)" 로 남아 있다.
     덫이 그 커밋에서 생겼는지는 확인하지 않았다
 ★ setter 도 있다 — 누가 그 이름에 값을 넣으면 덫을 걷어 내고 진짜 속성으로
   바꾼다 (L264-284). 덫이 정상 코드를 막지 않게 한다
 ★ 경고는 `createDedupedByCallsiteServerErrorLoggerDev`(L239)로 **호출 자리마다 한 번**만 낸다
 ★ `enumerable: false` 다. 약속을 펼치거나 순회해도 덫이 보이지 않는다
 ★ headers 쪽 덫은 **열한 개**다 — 같은 아홉에 없는 `append` · `getSetCookie` · `forEach` ·
   `keys` · `values` · `entries` 가 있고 cookies 쪽에만 있는 것이 빠진다 (HDRS L243-263).
   Headers 객체의 메서드를 따라 붙인 것이다
```

## 동작 흐름

```text
 cookies()   CKS L33

 L34-36  callingExpression · workStore · workUnitStore
 L38     if (workStore) {
 L39       after() 안이면                            => throw  (L40)
 L45       workStore.forceStatic 이면                 => return 빈 쿠키 (L49)
             주석 L46-47 - "we override all other logic and always just return
               an empty cookies object without tracking"
 L52       workStore.dynamicShouldError 이면          => throw StaticGenBailoutError (L53)
 L58       if (workUnitStore) {
 L59         switch (workUnitStore.type)   — 열한 갈래, [README] 표의 한 열
 L116          'request' 이면
 L117            trackDynamicDataInDynamicRender(workUnitStore)
 L121            areCookiesMutableInCurrentPhase 이면 userspaceMutableCookies (L125)
 L127            아니면 workUnitStore.cookies
 L130            개발이면 => makeUntrackedCookiesWithDevWarnings(...)   (L134)
 L139            asyncApiPromises 가 있으면 => 그 약속
                 그 밖 => makeUntrackedCookies(...)
 L155    throwForMissingRequestStore(callingExpression)   ← 스토어가 없으면 여기로 떨어진다
```

```text
 ★★ 서버 액션 중에는 **쓸 수 있는 쿠키**를 돌려주는데 타입은 읽기 전용이다 (L121-127)

   if (areCookiesMutableInCurrentPhase(workUnitStore)) {
     underlyingCookies =
       workUnitStore.userspaceMutableCookies as unknown as ReadonlyRequestCookies
   }

 주석 L122-123 - "We can't conditionally return different types here based on
   the context. To avoid confusion, we always return the readonly type here."
 => 실제 객체는 `set` 이 되는데 타입은 `Readonly` 다.
    `as unknown as` 로 **타입 검사를 일부러 끈다**
 ★ 그래서 서버 액션 안의 `(await cookies()).set(...)` 은 타입상으로는 안 되는 것처럼
   보이지만 돌아간다
 ※ 사용자가 그것을 어떻게 쓰게 되는지(별도 타입 선언 등)는 확인하지 않았다
```

```text
 ★★★ headers() 는 switch 를 **두 번** 돈다 — 그 사이에 관문이 있다

 cookies()    after → forceStatic → **dynamicShouldError** → switch (L59)
 headers()    after → forceStatic → switch① (L60) → **dynamicShouldError** (L92) → switch② (L99)

 switch① 이 하는 일은 캐시 스코프 셋과 generateStaticParams 에서 던지는 것뿐이다
   L61 'cache' · L70 'unstable-cache' · L74 'generate-static-params' => throw
   L78-86 나머지 여덟 => break

 => **같은 상황에서 두 API 가 다른 오류를 낸다**
    `'use cache'` 안에서 `dynamic = "error"` 인 라우트가 부르면
      cookies()  StaticGenBailoutError  "with `dynamic = "error"` couldn't be rendered
                                         statically because it used `cookies()`"
      headers()  Error                  "used `headers()` inside "use cache". Accessing
                                         Dynamic data sources inside a cache scope is
                                         not supported."
 ★ 오류가 다른 것에서 끝나지 않는다 — headers 의 캐시 오류는 `invalidDynamicUsageError ??=`
   로 **남고**(HDRS L67), cookies 의 StaticGenBailoutError 는 **남지 않는다**(CKS L52-56).
   그래서 [`'use cache'`] [04]의 버퍼 스트림이 읽을 때마다 오류를 다시 내는지도 둘이 다르다
 ★ headers() 쪽이 **캐시 오류를 우선**한다 — 사용자가 고쳐야 할 것이 캐시 쪽이면
   그것을 먼저 말해 주는 셈이다
 ※ 어느 쪽이 의도인지 소스는 적지 않는다. 두 파일이 다르게 생겼다는 것까지가 사실이다
 ★ headers() 의 구조는 [동적 판별] [01]의 markCurrentScopeAsDynamic 과 같은 모양이다 —
   같은 값으로 switch 를 두 번 하고 첫째는 빠져나가기(여기선 던지기) 위한 것이다
```

```text
 ★★ 같은 렌더 안에서 **같은 약속 객체**를 돌려준다 (L163-200)

 const CachedCookies = new WeakMap<CacheLifetime, Promise<ReadonlyRequestCookies>>()   L163

 makeHangingCookies(workStore, prerenderStore)     L168
   L172  CachedCookies.get(prerenderStore)        ← **스토어**가 키
   L183  CachedCookies.set(prerenderStore, promise)
 makeUntrackedCookies(underlyingCookies)           L188
   L191  CachedCookies.get(underlyingCookies)     ← **쿠키 객체**가 키

 => 두 번 불러도 같은 약속이다 — **이 두 경로에서는.**
    prerender-runtime 의 `stagedRendering.delayUntilStage` 는 부를 때마다 새 약속을 만든다
    (app-render/staged-rendering.ts L284-307)
    React 의 `use()` 가 같은 약속을 다시 받으면
    다시 매달리지 않는다
 ★ 키가 두 종류인데 한 WeakMap 에 섞어 넣는다. `interface CacheLifetime {}`(L162)가
   **빈 인터페이스**라 어떤 객체든 키가 된다 — 타입이 "수명을 가진 무언가" 라는 뜻만 남긴다
 ★ WeakMap 이라 스토어나 쿠키 객체가 버려지면 약속도 함께 버려진다
```

## 결과가 쓰이는 곳

```text
 makeHangingCookies / makeHangingHeaders 의 약속
      --> makeRuntimeHangingPromise 다. [README]의 R 칸.
          `trackRuntimeDataAccessed` 가 남긴 기록이 [프리페치]의 런타임 재요청 근거가 된다

 stagedRendering.delayUntilStage(sessionData, ...)
      --> 런타임 prerender 가 세션 데이터 단계에 이르면 값을 준다.
          [`'use cache'`] [01]의 private 캐시가 기다리는 **같은 단계**다

 workStore.invalidDynamicUsageError (캐시 스코프 갈래)
      --> [`'use cache'`] [04]의 버퍼 스트림이 읽을 때마다 다시 낸다

 개발 모드의 덫
      --> 터미널 경고. 호출 자리마다 한 번
```

## 다루지 않는 것

`RequestCookiesAdapter` · `HeadersAdapter` 의 `seal` 과 읽기 전용 구현, `areCookiesMutableInCurrentPhase` 의 phase 판정과 서버 액션에서 쿠키를 응답에 쓰는 과정, `makeUntrackedCookiesWithDevWarnings`(L202)의 `asyncApiPromises` 분기 세부와 `makeDevtoolsIOAwarePromise`, `createDedupedByCallsiteServerErrorLoggerDev` 의 호출 자리 판별, `headers.ts` 의 덫 함수들(L243-320 — 구조는 cookies 와 같고 대상 메서드만 열한 개다), `throwForMissingRequestStore` 의 문구는 이 문서의 범위 밖이다.
