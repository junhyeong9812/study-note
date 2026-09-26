# 04 수명과 태그

상위: [`'use cache'` 가 값을 돌려주기까지](../README.md)

캐시 수명은 세 숫자(`stale` · `revalidate` · `expire`)다. **작은 쪽이 이기는 자리가 둘**(`cacheLife()` 안, 부모에게 전파할 때)이고, **항목을 조립할 때는 다르다** — 거기서는 명시값이 무조건 이겨서 수명이 늘어날 수도 있다.

## 위치

`packages/next` / `src/server/use-cache` / `cache-life.ts` L95-L121 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/use-cache/cache-life.ts#L95-L121))

## 실제 코드

`cacheLife()` 의 마지막 27줄이 같은 모양 셋이다.

```ts
// cache-life.ts L95-L121
  if (profile.revalidate !== undefined) {
    // Track the explicit revalidate time.
    if (
      workUnitStore.explicitRevalidate === undefined ||
      workUnitStore.explicitRevalidate > profile.revalidate
    ) {
      workUnitStore.explicitRevalidate = profile.revalidate
    }
  }
  if (profile.expire !== undefined) {
    // Track the explicit expire time.
    if (
      workUnitStore.explicitExpire === undefined ||
      workUnitStore.explicitExpire > profile.expire
    ) {
      workUnitStore.explicitExpire = profile.expire
    }
  }
  if (profile.stale !== undefined) {
    // Track the explicit stale time.
    if (
      workUnitStore.explicitStale === undefined ||
      workUnitStore.explicitStale > profile.stale
    ) {
      workUnitStore.explicitStale = profile.stale
    }
  }
```

```text
 ★★★ `>` 비교로 **작은 쪽만 남긴다**

   explicitRevalidate === undefined  또는  explicitRevalidate > profile.revalidate
     이면 덮어쓴다

 => `cacheLife()` 를 두 번 부르면 **짧은 쪽이 이긴다.** 늘릴 수가 없다
 => 그래서 안쪽 캐시가 바깥 캐시의 수명을 늘리는 일이 생기지 않는다
 ★ 세 값이 완전히 같은 모양으로 따로 추적된다 — 한 번에 담은 객체가 아니다.
   `cacheLife({ revalidate: 10 })` 처럼 하나만 준 호출이 나머지를 건드리지 않게 하려는 것이다
```

## 동작 흐름

```text
 cacheLife(profile)   UCLIFE L26
 L27  !__NEXT_USE_CACHE 이면 => throw  `cacheComponents` 설정이 필요하다
 L35  switch (workUnitStore?.type)
 L47    'cache' · 'private-cache' 를 뺀 아홉 + undefined => throw
              '`cacheLife()` can only be called inside a "use cache" function.'
 L65  문자열이면 workStore.cacheLifeProfiles[profile] 을 찾는다
 L66    없으면 => throw. 단 L67 이 profile.trim() 을 먼저 보고
          있으면 **"공백 빼고 쓰려던 거 아닌가" 를 묻는다** (L70 이 그 문장)
 L57    문자열인데 workStore 가 없으면 => throw
          '`cacheLife()` can only be called during App Router rendering at the moment.'
 L83  문자열도 객체도 아니면 (null · 배열 포함) => throw
          'Invalid `cacheLife()` option. Either pass a profile name or object.'
 L92  객체면 validateAndNormalizeCacheLifeProfile(profile, { kind: 'inline' })
 L95  세 값을 각각 최솟값으로 기록

 cacheTag(...tags)    UCTAG L4
 L5   !__NEXT_USE_CACHE 이면 => throw
 L13  switch — cacheLife 와 **같은 갈래**다 (L25 가 같은 문장)
 L34  validTags = validateTags(tags, '`cacheTag()`')
 L36  workUnitStore.tags 가 없으면 대입, 있으면 push
```

```text
 ★★ 두 API 의 허용 위치가 완전히 같다

   'cache'          public `'use cache'` 안
   'private-cache'  `'use cache: private'` 안
   그 밖 아홉 + undefined  => throw

 => `cacheLife()` 도 `cacheTag()` 도 **캐시 함수 안에서만** 쓸 수 있다.
    페이지나 레이아웃 본문에서는 못 쓴다
 ★ `undefined`(스토어 없음)도 같은 오류다 — App Router 밖에서 부른 경우
 ★ 오류 문구가 API 이름만 바꿔 넣은 같은 문장이다
```

```text
 ★ 프로필 이름 오타를 **공백까지 짚어 준다** (UCLIFE L67-72)

   if (workStore.cacheLifeProfiles[profile.trim()]) {
     throw new Error(
       `Unknown \`cacheLife()\` profile "${profile}" is not configured ...
        Did you mean "${profile.trim()}" without the spaces?`)
   }

 => `cacheLife(' minutes ')` 같은 경우를 잡는다
 ★ 그게 아니면 `next.config.js` 의 `cacheLife` 블록 예시를 문자열로 붙여 던진다 (L73-81)
 ★ 기본 프로필 이름 **일곱 개**가 타입에 박혀 있다 (L16-24) —
   default · seconds · minutes · hours · days · weeks · max
   여기에 `(string & {})` 가 붙는데 그것은 프로필 이름이 아니라
   **임의 문자열을 허용하는 확장 슬롯**이다
   주석 L15 - "This gets overridden by the next-types-plugin"
   => 사용자가 설정한 이름이 타입으로 들어오도록 플러그인이 이 타입을 덮어쓴다
```

```text
 ★★★ 항목을 만들기 전에 **스트림을 전부 버퍼링한다** (UCW L1118-1164)

 L1139  buffer: Uint8Array[] = []
 L1140  reader = savedStream.getReader()
 L1143  for 로 끝까지 읽어 buffer 에 쌓는다
 L1147  catch => errors.push(error)      ★ 던지지 않고 모아 둔다

 주석 L1126-1137
   "We create a buffered stream that collects all chunks until the end to
    ensure that RSC has finished rendering and therefore we have collected
    all tags. ...
    If something errored or rejected anywhere in the render, we close
    the stream as errored. This lets a CacheHandler choose to save the
    partial result up until that point for future hits for a while to avoid
    unnecessary retries or not to retry. We use the end of the stream for
    this to avoid another complicated side-channel."

 => **태그를 다 모으려면 렌더가 끝나야 한다.** `cacheTag()` 는 렌더 중 아무 때나 불릴 수 있다
 => 오류는 별도 통로가 아니라 **스트림의 끝**으로 알린다.
    그러면 핸들러가 "부분 결과를 저장할지" 를 스스로 고를 수 있다
 ★ RSC 에 SSR 의 `allReady` 같은 것이 없어서 이렇게 한다고 적는다 (주석 L1128-1129)

 L1151  버퍼를 다시 읽는 스트림을 만든다 — pull 이 넷으로 갈린다
 L1153    workStore.invalidDynamicUsageError 가 있으면 => controller.error(그것)
 L1156    버퍼가 남았으면 => enqueue
 L1159    errors 가 있으면 => controller.error(errors[0])   (TODO: AggregateError?)
 L1161    그 밖 => close
 ★ [01]에서 미리 만들어 둔 그 오류가 여기서 나온다. **읽을 때마다** 다시 나온다

 ★★ 그리고 전파 전체가 게이트 하나에 걸려 있다 (L1235)
   if (!cacheContext.skipPropagation) { maybePropagateCacheEntryMetadata(...) }
   `skipPropagation` 이 true 가 되는 자리는 **백그라운드 재검증 하나**다 (L3490-3493)
 => 이미 내보낸 응답의 수명을 뒤늦게 바꾸지 않겠다는 것으로 보인다
 ※ 뒷문장은 내 해석이다. 소스가 이유를 적지는 않았다
```

```text
 ★★ 항목의 수명은 "명시한 것 우선, 없으면 안쪽 최솟값" 이다 (L1195-1209)

 collectedRevalidate = 개발+private ? 0
                       : explicitRevalidate ?? innerCacheStore.revalidate
 collectedExpire     = 개발+private ? MIN_PRERENDERABLE_EXPIRE(300)
                       : explicitExpire ?? innerCacheStore.expire
 collectedStale      = explicitStale ?? innerCacheStore.stale

 주석 L1192-1194
   "If cacheLife() was used to set an explicit revalidate/expire/stale time we
    use that. Otherwise, we use the lowest of all inner fetch(),
    unstable_cache() or nested "use cache", if they're lower than our default."

 => `cacheLife()` 를 안 썼으면 **안쪽 것들의 최솟값**이 된다.
    `fetch()` 하나가 짧으면 감싼 캐시 전체가 짧아진다
 ★★★ 그런데 썼으면 **최솟값이 아니다.** `explicit… !== undefined` 면 무조건 그것이다
   안쪽 `fetch()` 가 revalidate 10 을 전파했어도
   `cacheLife({ revalidate: 3600 })` 이면 결과는 **3600 — 늘어난다**
 => 즉 "작은 쪽이 이긴다" 는 `cacheLife()` 호출끼리(L95-121)와
    부모 전파(L922-945)에만 성립한다. 조립은 **명시 우선**이다
 ★ `stale` 만 개발 강제에서 빠진다 — 위 두 줄에만 삼항이 붙어 있다
```

```text
 ★★★ 개발의 private 캐시만 수명을 **강제로 동적**으로 만든다 (L1172-1190)

 forceDynamicCacheLifeInDev = isPrivateCacheInDev
                            = __NEXT_DEV_SERVER && cacheContext.kind === 'private'

 주석 L1172-1189 가 **일부러 그러지 않는 세 경우**를 적는다
   "Two other cases deliberately do NOT force this and keep their resolved
    cache life ... The size-0 case (`cacheMaxMemorySize: 0`) keeps its life so
    the entry can be considered prerenderable instead of being misread as a
    dynamic hole. An explicit short-`expire` public cache (e.g. `cacheLife({
    expire: 0 })`) keeps its life so it stays correctly excluded from static
    prerenders via its real `expire` while a reload still hits the cache;
    forcing `revalidate: 0` here would instead corrupt the cache life
    propagated to an enclosing cache and trigger the nested-dynamic error. A
    cache backed by a custom handler keeps its real cache life too, since that
    handler owns it."

 => `revalidate: 0` 이면 읽을 때마다 stale-while-revalidate 가 되어
    백그라운드에서 새로 만든다. `expire: 300` 은 인메모리 핸들러에 머무는 상한이다
 => 300 을 고른 이유 — **동적으로 취급되지 않는 가장 짧은 expire** 다.
    더 짧으면 prerender 에서 빠진다
 ★★ "주석이 '둘' 이라 하고 셋을 센다" — size-0 · 명시적 짧은 expire · 커스텀 핸들러.
   앞의 둘이 `!isPrivateCacheInDev` 로 자연히 빠지는 경우고 셋째는 덧붙인 문장이다
   (※ 뒷문장은 내 읽기다. 소스가 개수를 정정하지는 않았다)
```

```text
 ★★ 부모에게 전파하는 함수가 **둘로 나뉜다** (L922-954)

 propagateCacheLifeAndTagsToRevalidateStore(revalidateStore, metadata)   L922
   태그   중복 없이 push (includes 검사)
   stale · revalidate · expire  각각 **`>` 면 덮어쓴다** = 최솟값

 propagateCacheStaleTimeToRequestStore(requestStore, metadata)           L947
   **stale 하나만** 옮긴다. 그것도 `requestStore.stale !== undefined &&
   requestStore.stale > metadata.stale` 일 때만 — **여기도 최솟값이다** (L951-953)

 => 요청 스토어는 수명을 모은다는 개념이 없다.
    클라이언트가 얼마나 들고 있어도 되는지(`stale`)만 알면 된다
 => 그 값이 [응답 나가기]의 `Next-Router-Stale-Time` 헤더가 된다
 ★ 태그도 안 옮긴다 — 요청 단위에서는 무효화 대상이 아니다
```

```text
 ★★★ 어느 쪽으로 전파하는지가 스토어 타입으로 갈린다 (L956-1024)

 private 캐시일 때
   'prerender-runtime' · 'private-cache'  => 수명+태그 (revalidate store)
   'request'                              => stale 만
   undefined                              => 아무것도

 public 캐시일 때
   'cache'        => **readRootParamNames 합집합** + dynamicNestedCacheError `??=`
                     그리고 fallthrough 로 수명+태그까지
   'private-cache' · 'prerender' · 'prerender-runtime' · 'prerender-ppr'
   · 'prerender-legacy'                   => 수명+태그
   'request'                              => stale 만
   'unstable-cache' · 'generate-static-params'  => 아무것도

 ★★ `'cache'` 갈래에만 있는 두 가지가 핵심이다
   readRootParamNames  --> 바깥 캐시가 "나도 이 루트 파라미터를 읽는다" 로 물려받는다.
                           [02]·[03]의 리다이렉트 항목이 이 정보로 만들어진다
   dynamicNestedCacheError --> 이 항목의 수명이 동적이면 (revalidate 0 또는 expire < 300)
                           [01]에서 미리 만든 오류를 바깥에 심는다
                           주석 L988-991 - `??=` 로 **첫 번째만** 남겨 (L997 이 그 줄)
                             cause 가 가장 가까운 동적 자식을 가리키게 한다

 ★ `unstable_cache` 안에서는 전파가 **끊긴다.** 옛 API 와 수명 모형이 다르다
```

```text
 ★★★ prerender 에서는 전파를 **미룬다** (L1026-1080)

 maybePropagateCacheEntryMetadata 의 docstring (L1026-1040)
   "During prerenders (`prerender` / `prerender-runtime`) and dev
    cache-filling requests, propagation is deferred because the entry might be
    omitted from the final prerender due to short expire/stale times. If omitted,
    it should not affect the prerender. The final decision happens when the entry
    is read from the resume data cache in the final render phase — at that point
    `propagateCacheEntryMetadata` is called unconditionally (after the omission
    checks have already filtered out short-lived entries)."

 'prerender' · 'prerender-runtime'        => break   (미룬다)
 'request' 이고 개발 && cacheSignal 있으면 => break   (캐시를 채우는 중이므로 같은 취급)
 'generate-static-params'                 => break   ★ **미루는 게 아니라 아예 안 한다**
                                                     (L1074-1075 — 위 즉시 전파 갈래와 별개다)
 그 밖                                     => propagateCacheEntryMetadata 즉시

 => 짧은 수명 때문에 최종 prerender 에서 **빠질지도 모르는 항목**이
    prerender 전체의 수명을 깎아 버리는 것을 막는다
 => 판정은 [03]의 RDC 읽기에서 한다. 그때는 이미 걸러진 뒤라 조건 없이 전파한다
 ★ 루트 파라미터 이름은 예외다 — docstring L1036-1040 이,
   그것은 바깥이 `cache` 스토어일 때만 전파되고 그 경로는 **미뤄지지 않으며**,
   prerender 에서는 `addKnownRootParamNames` 가 따로 추적한다고 적는다
```

## 결과가 쓰이는 곳

```text
 CacheEntry { value · timestamp · revalidate · expire · stale · tags }
      --> 핸들러의 `set` 과 RDC 에 저장된다. `value` 는 버퍼를 다시 읽는 스트림이다

 CollectedCacheResult
      --> entry 외에 hasExplicitRevalidate · hasExplicitExpire ·
          readRootParamNames · dynamicNestedCacheError 를 함께 나른다
      --> 여기서 `CacheResultMetadata`(L186-196)가 만들어지고 (L3353-3369)
          합류자들이 공유하는 것은 그 metadata 와 `SharedCacheEntry`(L203-231)다.
          이 객체 자체가 공유되는 것은 아니다

 바깥 revalidate store 의 stale · revalidate · expire
      --> [응답 나가기]의 `Cache-Control` 과 `Next-Router-Stale-Time`

 바깥 revalidate store 의 tags
      --> [재검증]의 `revalidateTag` / `updateTag` 가 무효화할 대상

 readRootParamNames
      --> [03]이 `_N_RP_` 태그로 항목에 실어 보낸다. 다음 조회가 이것으로 좁혀진다

 workUnitStore.explicitStale / explicitExpire / explicitRevalidate
      --> collectResult 가 읽는다. `cacheLife()` 가 쓰고 여기서 소비된다
```

## 다루지 않는 것

`validateAndNormalizeCacheLifeProfile`(`cache-life-profile.ts` 96줄)의 검증 규칙과 `INFINITE_CACHE` 치환, `next.config.js` 의 `cacheLife` 설정을 `workStore.cacheLifeProfiles` 로 싣는 과정과 `next-types-plugin` 의 타입 덮어쓰기, `validateTags`(`lib/patch-fetch.ts`)의 태그 형식 검사, `generateCacheEntryImpl`(L1268-1625, 358줄)의 본체 실행과 `createUseCacheStore`(L744) 가 만드는 스토어의 필드 전부, `saveToCacheHandler`(L605) · `saveToResumeDataCache`(L490) · `saveSharedCacheEntryToResumeDataCache`(L528)의 저장 경로, `cloneCacheEntry` 와 스트림 포크, `RevalidateStore` · `RequestStore` 의 정의, 기본 프로필 여덟 개의 실제 숫자값, `getUseCacheFillTimeoutMs`(L874)와 fill 타임아웃은 이 문서의 범위 밖이다.
