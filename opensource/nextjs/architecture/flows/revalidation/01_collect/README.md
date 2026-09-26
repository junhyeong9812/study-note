# 01 쌓기

상위: [재검증이 쌓이고 실행되기까지](../README.md)

`revalidate(tags, expression, profile)` 다. 131줄(L128-258)인데 **금지 확인이 76줄**(L133-208)이고 실제로 쌓는 일은 31줄(L210-240)이다. 나머지 17줄(L242-258)이 `pathWasRevalidated` 판정이다.

## 위치

`packages/next` / `src/server/web/spec-extension` / `revalidate.ts` L128-L258 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/web/spec-extension/revalidate.ts#L128-L258))

## 실제 코드

렌더 중이면 type 을 보기도 전에 막는다.

```ts
// revalidate.ts L142-L146
    if (workUnitStore.phase === 'render') {
      throw new Error(
        `Route ${store.route} used "${expression}" during render which is unsupported. To ensure revalidation is performed consistently it must always happen outside of renders and cached functions. See more info here: https://nextjs.org/docs/app/building-your-application/rendering/static-and-dynamic#dynamic-rendering`
      )
    }
```

그 다음 `workUnitStore.type` 으로 **case 라벨 11개 + default** 로 가른다.

```ts
// revalidate.ts L149-L153
      case 'cache':
      case 'private-cache':
        throw new Error(
          `Route ${store.route} used "${expression}" inside a "use cache" which is unsupported. To ensure revalidation is performed consistently it must always happen outside of renders and cached functions. See more info here: https://nextjs.org/docs/app/building-your-application/rendering/static-and-dynamic#dynamic-rendering`
        )
```

## 동작 흐름

```text
 REVAL L128-258

 --- 전제 확인 ---
 L133  store = workAsyncStorage.getStore()
 L134  store 나 store.incrementalCache 가 없으면
 L135    => throw `Invariant: static generation store missing in ${expression}`

 --- ★ 렌더 중이면 무조건 금지 ---
 L140  workUnitStore = workUnitAsyncStorage.getStore()
 L142  workUnitStore.phase === 'render' 이면
 L143    => throw `Route ... used "${expression}" during render which is unsupported.
              To ensure revalidation is performed consistently it must always happen
              outside of renders and cached functions.`

 --- ★★ 그리고 type 으로 갈린다 (case 라벨 11개 + default) ---
 L148  switch (workUnitStore.type)
 L149    'cache' / 'private-cache'      => throw  'inside a "use cache" which is unsupported'
 L154    'unstable-cache'               => throw  'inside a function cached with "unstable_cache(...)"'
 L158    'generate-static-params'       => throw  "inside `generateStaticParams`"
 L162    'prerender' / 'prerender-runtime'
 L165      error = `used ${expression} without first calling \`await connection()\`.`
 L168      => return abortAndThrowOnSynchronousRequestDataAccess(...)
 L174    'prerender-client' / 'validation-client'
 L176      => throw InvariantError  "must not be used within a client component"
 L179    'prerender-ppr'
 L180      => return postponeWithTracking(store.route, expression, workUnitStore.dynamicTracking)
 L185    'prerender-legacy'
 L186      workUnitStore.revalidate = 0
 L188      err = new DynamicServerError(`Route ... couldn't be rendered statically
                because it used \`${expression}\``)
 L191      store.dynamicUsageDescription = expression
 L192      store.dynamicUsageStack = err.stack
 L194      => throw err
 L195    'request'
 L196      NODE_ENV !== 'production' 이면 workUnitStore.usedDynamic = true  (test 포함)
            주석 L197-199 - "This is most likely incorrect. It would lead to the ISR
              status being flipped when revalidating a static page with a server action."
            => 소스가 스스로 이 대입이 틀렸을 것 같다고 적어 놓았다
 L204      break          ★ **통과한다**
 L205    default
 L206      workUnitStore satisfies never     (타입 수준 전수 확인)
          ★ throw/return 이 없어서 **여기도 통과한다**.
            다만 타입이 never 라 도달할 수 없다는 뜻이다

 --- 실제로 쌓는다 ---
 L210  store.pendingRevalidatedTags 가 없으면 []
 L214  revalidatedAt = performance.timeOrigin + performance.now()
 L216  각 태그에 대해
 L217    같은 tag + 같은 profile 항목을 찾는다
 L228    없으면 push({tag, profile, revalidatedAt})
 L234    있으면 그 항목의 revalidatedAt 만 갱신한다
          주석 L235-237 - 태그를 다시 재검증하면 그때까지 만들어진 것이 전부 무효다.
            **가장 나중 재검증이 무엇이 stale 인지를 정한다**
 L245  cacheLife = store?.cacheLifeProfiles[profile] ?? undefined  (L245-252)
 L254  **!profile 이거나 cacheLife?.expire === 0 이면**
 L256    store.pathWasRevalidated = ActionDidRevalidate
          (ActionDidRevalidateStaticAndDynamic 의 별칭 — L16 의 import)
          주석 L242-244 - profile 이 있고 stale-while-revalidate 갱신이면
            경로를 재검증됨으로 표시하지 **않는다**.
            서버 액션이 **자기 쓰기를 자기가 읽지 않도록** 하려는 것이다
          ★ 그러므로 profile 이 있어도 `{expire: 0}` 이면 표시한다
          주석 L255 - "TODO: only revalidate if the path matches"
```

```text
 ★★★ 통과하는 길이 **둘**이다

 (가) workUnitStore 자체가 없으면 L141 의 `if (workUnitStore)` 블록(L141-208)을
      **통째로 건너뛴다.** phase 도 type 도 보지 않는다
 (나) workUnitStore 가 있고 type 이 'request' 일 때 (L195)

 case 라벨 11개 중 통과하는 것은 'request' 하나다

 막는 것 열 (라벨 기준)
   cache · private-cache            'use cache' 안
   unstable-cache                   unstable_cache 안
   generate-static-params           generateStaticParams 안
   prerender · prerender-runtime    cacheComponents 프리렌더
   prerender-ppr                    PPR 프리렌더 (미룬다)
   prerender-legacy                 예전 프리렌더 (DynamicServerError)
   prerender-client · validation-client   클라이언트 컴포넌트

 + 그 앞의 L142 `phase === 'render'` 가 **type 과 무관하게 먼저** 걸린다
 + default(L205)는 막지 않지만 타입상 도달 불가다

 ★ "it must always happen outside of renders and cached functions" 는
   넷에만 있다 — L144(render) · L152(cache) · L156(unstable-cache) · L160(generate-static-params).
   prerender 계열(L166 · L177 · L189) 메시지에는 없다
 => 재검증은 **렌더 바깥**에서만 한다. 서버 액션과 라우트 핸들러가 그 자리다
```

```text
 ★★ 프리렌더 갈래마다 처리가 다르다

 ★★★ 다만 **`after()` 안에서 불렀을 때만** 여기에 닿는다
   app-render.tsx 의 `phase:` 20곳이 **전부 'render'** 다 (grep 전수).
   그래서 프리렌더 중에 revalidateTag 를 부르면 L142 의
   `phase === 'render'` 가 **먼저** 걸려 던진다.
   phase 가 'after' 로 뒤집히는 것은 after/after-context.ts L46 뿐이다
     workUnitStore.phase = 'after'
   => 아래 세 갈래는 "프리렌더 중 after() 안에서 부른 경우" 의 이야기다

 'prerender' / 'prerender-runtime'   abortAndThrowOnSynchronousRequestDataAccess
     메시지가 `await connection()` 을 먼저 부르라고 한다
     ※ 'prerender' 는 [정적 응답]의 cacheComponents 갈래에서 생기고,
       'prerender-runtime' 은 **런타임 프리페치** 쪽(app-render.tsx L1627 · L1811)에서 생긴다.
       둘을 한 갈래로 묶어 읽으면 안 된다

 'prerender-ppr'                     postponeWithTracking
     => 던지지 않는다. **미룬다.** [정적 응답] [03]의 postponed 가 이렇게 생긴다

 'prerender-legacy'                  DynamicServerError
     workUnitStore.revalidate = 0 으로 만들고 던진다
     => [정적 응답] [04]가 "old-school dynamic error handling" 이라 부른 그 예외.
        [05]의 catch(L9665) 안 L9682-9683 이 이것을 받아 **다시 던진다**
     ※ 다만 프리렌더 중 revalidateTag 로 여기 오려면 after() 안이어야 한다(위 별항).
       DynamicServerError 를 던지는 다른 자리들(cookies() 등)이 더 흔한 경로다
```

```ts
// revalidate.ts L185-L194
      case 'prerender-legacy':
        workUnitStore.revalidate = 0

        const err = new DynamicServerError(
          `Route ${store.route} couldn't be rendered statically because it used \`${expression}\`. See more info here: https://nextjs.org/docs/messages/dynamic-server-error`
        )
        store.dynamicUsageDescription = expression
        store.dynamicUsageStack = err.stack

        throw err
```

```text
 ★ 같은 API 가 문맥에 따라 전혀 다른 일을 한다

 서버 액션에서  -> 태그를 쌓는다 (L216)
 PPR 프리렌더에서 -> 렌더를 미룬다 (L180)
 예전 프리렌더에서 -> 정적 생성을 포기시킨다 (L194)
 렌더 중에      -> 던진다 (L143)

 => `revalidateTag` 는 "캐시를 지우는 함수" 가 아니다.
    **어디서 불렸는지가 먼저**고, 쌓기는 그 다음이다
```

```text
 ★ 같은 태그를 두 번 재검증하면 항목이 안 늘어난다 (L217-239)

 tag 와 profile 이 둘 다 같으면 기존 항목의 revalidatedAt 만 덮어쓴다
 주석 L235-237 - "Revalidating a tag again invalidates everything produced up to now,
   so the latest revalidation is the one that decides which entries are stale."
 ★ profile 비교가 세 갈래다 (L220-226) — 둘 다 문자열이면 ===,
   둘 다 객체면 JSON.stringify 비교, 그 밖은 ===
   => 객체 profile 은 **직렬화해서** 비교한다
```

## 결과가 쓰이는 곳

```text
 store.pendingRevalidatedTags
      --> 소비자가 **넷**이다. 항목은 {tag, profile, revalidatedAt}
            revalidation-utils.ts L186   [02]의 executeRevalidates
            use-cache-wrapper.ts L3707-3741  isRevalidatedAfter —
              `item.revalidatedAt > entryTimestamp`(L3735).
              **revalidatedAt 을 실제로 쓰는 유일한 자리**다
            incremental-cache/index.ts L509 · L572  같은 요청 안의 stale 판정
            action-handler.ts L424-433   액션 포워딩 때 **태그 이름만** 헤더로 실어 보낸다
      ★ [02]의 revalidateTags 는 revalidatedAt 을 **파라미터 타입에서 버린다**
        (revalidation-utils.ts L80-84). 위 L235-237 주석의 효력은
        use-cache-wrapper 쪽에서만 실현된다

 store.dynamicUsageDescription / dynamicUsageStack
      --> 'prerender-legacy' 갈래에서만 채운다.
          정적 생성이 왜 실패했는지를 빌드 로그에 보여 주는 값이다

 workUnitStore.revalidate = 0
      --> 'prerender-legacy'. [정적 응답] [04]가 INFINITE_CACHE 로 시작한 그 값을
          0 으로 내려 "캐시하지 말라" 로 만든다

 store.pathWasRevalidated
      --> L254-256 이 조건부로 정한다. 읽는 곳이 **셋**이다
            action-handler.ts L197-198       [03]의 헤더
            action-handler.ts L1410-1412     skipPageRendering 결정
            action-handler.ts L1362-1364     에러 경로의 같은 결정
      ★ 뒤의 둘이 파급이 더 크다 — 액션 후 페이지를 다시 그릴지,
        그리고 재검증을 **먼저 await 할지**(L1433)를 가른다.
        L242-244 주석의 "자기 쓰기를 자기가 읽지 않는다" 가 그렇게 작동한다
```

## 다루지 않는 것

`abortAndThrowOnSynchronousRequestDataAccess` / `postponeWithTracking`(`dynamic-rendering.ts` 1592줄)의 구현, `workUnitAsyncStorage` 가 나르는 스토어 **열한** 종류의 정의와 `phase` 값, L242-258 의 `cacheLife` 계산과 `pathWasRevalidated` 판정 세부, `validateAndNormalizeCacheLifeProfile` 과 프로필 형식, `encodeHeaderSafe` 가 태그를 어떻게 바꾸는지, `NEXT_CACHE_IMPLICIT_TAG_ID` 상수의 값, `performance.timeOrigin + performance.now()` 를 쓰는 이유(`Date.now()` 와의 차이)는 이 문서의 범위 밖이다.
