# 02 요청이 있다는 것 자체를 묻는 두 API

상위: [동적 API 가 값을 내주기까지](../README.md)

`connection()` 과 `io()` 는 둘 다 `Promise<void>` 를 돌려준다. **값이 없다.** 이 둘이 하는 일은 "여기서부터는 정적으로 만들지 마라" 는 표시뿐이다. 그런데 **캐시 스코프 안에서 정반대로 끝난다** — `connection()` 은 던지고 `io()` 는 즉시 풀린다. 두 docstring 이 그 차이를 서로를 가리키며 설명한다.

## 위치

`packages/next` / `src/server/request` / `connection.ts` L21-L144 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/connection.ts#L21-L144))

`packages/next` / `src/server/request` / `io.ts` L11-L108 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/request/io.ts#L11-L108))

## 실제 코드

`io()` 가 돌려주는 "이미 풀린 약속" 은 평범한 `Promise.resolve` 가 아니다.

```ts
// io.ts L11-L15
// A fulfilled thenable that React can unwrap synchronously via `use()` without
// ever suspending. Reusing a single instance avoids allocating on every call.
const resolvedIOPromise: Promise<void> = Promise.resolve(undefined)
;(resolvedIOPromise as any).status = 'fulfilled'
;(resolvedIOPromise as any).value = undefined
```

```text
 ★★★ React 가 약속을 추적할 때 쓰는 필드를 **미리 박아 둔다**

   (resolvedIOPromise as any).status = 'fulfilled'
   (resolvedIOPromise as any).value  = undefined

 주석 L11-12 - "A fulfilled thenable that React can unwrap synchronously via
   `use()` without ever suspending. Reusing a single instance avoids
   allocating on every call."

 => `Promise.resolve()` 만으로는 React 의 `use()` 가 **한 번 매달린다** —
    약속이 풀렸는지 동기적으로 알 방법이 없기 때문이다
 => `status` 와 `value` 를 붙여 두면 React 가 그것을 보고 **매달리지 않고 바로 꺼낸다**
 ★ Next.js 가 React 의 thenable 추적 규약에 **직접 기댄다**. `as any` 가 두 번 나오는
   이유다 — 공개 타입에 없는 필드다
 ★ 모듈 최상위에서 **하나만** 만들어 모든 호출에 재사용한다
 ※ "React 가 status 필드를 본다" 는 주석의 "unwrap synchronously" 에서 읽은 것이다.
   React 쪽 구현은 이 저장소에서 확인하지 않았다
```

## 동작 흐름

```text
 두 docstring 이 서로를 가리킨다

 connection()  CONN L21-25
   "This function allows you to indicate that you require an actual user
    Request before continuing.
    During prerendering it will never resolve and during rendering it
    resolves immediately."

 io()  IOAPI L17-27
   "This function allows you to indicate that the code following it performs
    I/O or accesses dynamic data sources such as `new Date()` or `Math.random()`.
    ...
    **Unlike `connection()`, `io()` does not require an actual HTTP request and
    can be used freely inside cache scopes and client components.**"

 ★ docstring 의 "can be used freely inside ... client components" 는 **요청 중에만** 맞다 —
   `prerender-client` 에서는 io() 도 D 로 매달린다 (IOAPI L60 · L65)

 => connection() 의 질문  "지금 **실제 사용자 요청**이 있는가"
 => io() 의 질문          "지금 **정적 결과를 만드는 중**인가"
 ★ 같은 `Promise<void>` 인데 묻는 것이 다르다
```

```text
 ★★★ 캐시 스코프에서 정반대다

                     connection()                    io()
 cache               throw   (L52)                   즉시 풀림 (L74)
 private-cache       **throw** (L61)                 즉시 풀림
 unstable-cache      throw   (L73)                   즉시 풀림
 generate-static-params throw (L77)                  즉시 풀림
 validation-client   InvariantError (L91)            즉시 풀림
 prerender-legacy    중단 throw (L107)               즉시 풀림

 connection() 의 'cache' 문구 (L54)
   "caches must be able to be produced before a request, so this function
    is not allowed in this scope"
 io() 의 주석 (L77-79)
   "Inside cache scopes, io() resolves immediately. Caches can contain
    IO-dependent code like new Date() — it will simply return the value
    at cache-fill time."

 => 캐시는 요청 **전에** 만들어질 수 있어야 한다. 그러니 "요청이 있어야 한다"
    (connection) 는 캐시 안에서 성립할 수 없다 — 던진다
 => 반면 IO 는 캐시를 채우는 순간에 하면 된다. 그 순간의 값이 캐시에 박힌다 — 풀린다
 ★ prerender-legacy 에서도 io() 는 풀린다. 주석 L96 -
   "Without cache components, IO is not inherently dynamic."
```

```text
 ★★ private-cache 에서 connection() 이 던지는 것은 **직관에 반한다고 스스로 적는다**

 L62-64  주석
   "It might not be intuitive to throw for private caches as well, but
    we don't consider runtime prefetches as "actual requests" (in the
    navigation sense), despite allowing them to read cookies."

 => `'use cache: private'` 은 쿠키를 읽을 수 있다 ([01]의 표에서 cookies 는 값).
    그런데 connection() 은 안 된다
 => 런타임 프리페치는 쿠키를 가지고 오지만 **사용자가 실제로 이동한 것은 아니기** 때문이다
 ★ 그래서 connection() 의 문구만 "actual **navigation** request" 라고 적는다 (L66)
 ★ [README] 표에서 prerender-runtime 은 connection() 과 io() **둘 다** D 매달림이다.
   그런데 이유가 다르다 —
     connection  런타임 prerender 는 "실제 **이동** 요청" 이 아니다 (L62-64)
     io          캐시 스코프 밖이면 그것은 "실제 **IO**" 다 (IOAPI L62-64)
```

```text
 ★★ 매달리는 약속이 **Runtime 이 아니라 Dynamic** 이다

 connection()  L81-83  'prerender' · 'prerender-client' · 'prerender-runtime'
               L86     => makeDynamicHangingPromise(renderSignal, route, '`connection()`')
 io()          L59-61  같은 세 갈래
               L65     => makeDynamicHangingPromise(..., '`io()`')

 => [01]의 cookies/headers 는 makeRuntimeHangingPromise 였다
 => 여기는 "런타임 요청이면 채울 수 있다" 를 **기록하지 않는다**
 ★ 그래서 런타임 프리페치가 이 구멍을 채우러 오지 않는다.
   실제 이동 요청만 채운다
 ★ io() 의 주석 L62-64 - "we consider `io()` to be actual IO if not in a cache
   scope and we can avoid actually executing anything after it by making it
   return a hanging promise"
```

```text
 ★ io() 에만 있는 죽은 갈래 (L70-73)

   case 'prerender-ppr':
     // Dead code to be removed when we eliminate legacy ppr code
     throwPrerenderPPRRemovedError()
     break

 => 옛 PPR 모드는 **제거됐다.** 함수 이름이 `…PPRRemovedError` 다
    (shared/lib/ppr-removed-error.ts L9)
 ★ 그런데 cookies · headers · connection 의 'prerender-ppr' 갈래는 여전히
   postponeWithTracking 을 부른다 — io() 만 새로 생긴 API 라 옛 경로를 안 받는다
   ※ 뒷문장은 내 추론이다. io() 가 언제 생겼는지는 확인하지 않았다
```

```text
 request 갈래 (두 API 공통 모양)

 connection()  L116  trackDynamicDataInDynamicRender(workUnitStore)
               L117  개발 && asyncApiPromises 있으면 => asyncApiPromises.connection
                     개발                          => makeDevtoolsIOAwarePromise(undefined, store, RenderStage.Dynamic)
                     프로덕션 && asyncApiPromises   => asyncApiPromises.connection
                     그 밖                          => Promise.resolve(undefined)
 io()          L39   (trackDynamicDataInDynamicRender 가 **없다**)
                     개발 => asyncApiPromises.io 또는 makeDevtoolsIOAwarePromise(..., Dynamic)
                     그 밖 => resolvedIOPromise

 ★ io() 는 요청 중에 **동적 사용으로 기록조차 하지 않는다.**
   요청이면 그냥 IO 일 뿐이다
 ★ 개발 모드에서 둘 다 `RenderStage.Dynamic` 에서 풀린다 — [01]의 cookies 가
   `sessionData` 단계에서 풀리는 것과 다르다. 단계 순서가 곧 "얼마나 동적인가" 다
```

## 결과가 쓰이는 곳

```text
 makeDynamicHangingPromise
      --> [정적 응답]이 이 자리를 구멍으로 남긴다. 런타임 기록이 없으므로
          [프리페치]의 런타임 재요청 대상이 **아니다**

 resolvedIOPromise
      --> React `use()` 가 매달리지 않고 바로 꺼낸다

 캐시 스코프 오류 (connection 의 'cache' · 'private-cache')
      --> `workStore.invalidDynamicUsageError ??= error` (L58 · L70) —
          [`'use cache'`] [04]가 버퍼를 읽을 때마다 다시 낸다

 trackDynamicDataInDynamicRender (connection 만)
      --> [동적 판별] [01]. 개발 서버의 정적/동적 표시
```

## 다루지 않는 것

`makeDevtoolsIOAwarePromise` 와 `RenderStage` 의 단계 정의, `asyncApiPromises` 를 요청 스토어가 만드는 과정, `throwPrerenderPPRRemovedError`(`shared/lib/ppr-removed-error.ts`)의 문구, React 가 thenable 의 `status` · `value` 를 읽는 구현, `io()` 의 클라이언트 쪽 동작(워크 스토어가 없을 때 L104-107), `connection()` 을 클라이언트 컴포넌트에서 import 하는 것을 정적으로 막지 못한다는 TODO(NAR-789 — L92 · L141-142 두 곳)는 이 문서의 범위 밖이다.
