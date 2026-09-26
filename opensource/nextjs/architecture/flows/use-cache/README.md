# 'use cache' 가 값을 돌려주기까지

상위: [Next.js 아키텍처 지도](../../README.md)

`'use cache'` 지시어를 붙인 함수는 컴파일러가 **다른 함수 호출로 바꿔 놓는다.** 그 함수가 `cache()` 이고, 혼자 **1855줄**(L1715-3569)이다. 이 지도에서 다룬 것 중 가장 길지만 저장소 최장은 아니다 — `build/templates/app-page-runtime.ts` 의 `createAppPageEntrypoint`(L147-2228, 2082줄)와 [정적 응답]의 `prerenderToStream`(L8229-10224, 1996줄)이 더 길다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `UCW` = `server/use-cache/use-cache-wrapper.ts`(3744줄), `UCCONST` = `.../constants.ts`(13줄), `UCLIFE` = `.../cache-life.ts`(122줄), `UCTAG` = `.../cache-tag.ts`(41줄), `UCHAND` = `.../handlers.ts`(352줄).

## 위치

`packages/next` / `src/server/use-cache` / `use-cache-wrapper.ts` L1715-L1721 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/use-cache/use-cache-wrapper.ts#L1715-L1721))

## 실제 코드

임계값 셋이 이 흐름 전체의 판단 기준이다.

```ts
// constants.ts L3-L13
export const MIN_PRERENDERABLE_EXPIRE = 300 // 5 minutes
export const MIN_PREFETCHABLE_STALE = 30 // 30 seconds
export const MIN_SHELL_STALE = 300 // 5 minutes

if (process.env.NODE_ENV !== 'production') {
  if (MIN_PREFETCHABLE_STALE > MIN_SHELL_STALE) {
    throw new InvariantError(
      'MIN_PREFETCHABLE_STALE must not exceed MIN_SHELL_STALE.'
    )
  }
}
```

```text
 MIN_PRERENDERABLE_EXPIRE = 300   expire 가 5분 미만이면 **정적으로 만들 값어치가 없다**
 MIN_PREFETCHABLE_STALE   =  30   stale 이 30초 미만이면 프리페치에 안 담는다
 MIN_SHELL_STALE          = 300   stale 이 5분 미만이면 셸에 안 담는다

 ★★ 불변식을 개발 빌드에서 **런타임에 검사한다** (L7-13)
   MIN_PREFETCHABLE_STALE > MIN_SHELL_STALE 이면 InvariantError 를 던진다
 => 금지되는 것은 "**셸에는 담기는데 프리페치에는 안 담기는**" 조합이다
 ★★★ 그 반대(30 <= stale < 300)는 금지가 아니라 **정규 경로**다 —
   셸에서만 빼고 post-shell 단계로 미룬다 (UCW L2584-2594 makeStageHangingPromise ·
   L3211-3217 이 stale < 30 이면 RenderStage.Dynamic, 아니면 staticLinkData)
   주석 L2586-2588 - "The entry was omitted only because this render ends
     before the post-shell stage; a render that reaches its post-shell stage
     would serve it."
   주석 L2595-2596 - "An unprefetchable entry (stale < MIN_PREFETCHABLE_STALE)
     is excluded from runtime prerenders too."
 ※ constants.ts 에는 이유 주석이 없다. 위 인과는 두 소비처를 읽고 내가 붙인 것이다
 ★ `process.env.NODE_ENV !== 'production'` 으로 감싸 프로덕션에서는 사라진다
```

진입은 컴파일러가 심는다.

```text
 build/create-compiler-aliases.ts L217-218
   [RSC_CACHE_WRAPPER_ALIAS]:
     'next/dist/build/webpack/loaders/next-flight-loader/cache-wrapper'

 그 파일 전체가 **한 줄**이다
   export { cache } from '../../../../server/use-cache/use-cache-wrapper'

 ★ 등록 지점이 **둘**이다 — Turbopack 도 같은 alias 를 자기 import map 에 심는다
   crates/next-core/src/next_import_map.rs L1197-1200
     "private-next-rsc-cache-wrapper" -> 같은 loader 파일

 => `'use cache'` 함수는 번들에서
      cache(kind, id, boundArgsLength, originalFn, args)
    호출로 바뀐다. `kind` 가 `'private'` 이면 `'use cache: private'` 이다
 ★ 그래서 함수 본체(`originalFn`)는 **인자로 넘어온다.** 캐시 미스일 때만 불린다
```

## 동작 흐름

```text
 server/use-cache/ 4,884줄

   use-cache-wrapper.ts        3744   cache() 혼자 1855줄        [01][02][03][04]
   handlers.ts                  352   핸들러 등록·조회
   tiered-cache-handler.ts      208   개발용 2단 핸들러
   use-cache-probe-scheduler.ts 195   개발 서버의 멈춤 탐지
   cache-life.ts                122   cacheLife()               [04]
   cache-life-profile.ts         96   프로필 검증·정규화
   use-cache-probe-globals.ts    63 · cache-tag.ts 41 · use-cache-errors.ts 30
   clone-cache-entry.ts          20 · constants.ts 13
   (열거 합계 = 4,884)
```

```text
 cache()  UCW L1715-3569 — 네 구획이다

 L1715-2033  스토어 둘을 확인하고 핸들러를 고른다          [01]
 L2035-2333  캐시 키를 조립한다                            [02]
 L2335-3540  **캐시를 세 겹으로 찾는다**                    [03]
             (그 안에서 실제로 순서대로 보는 저장소는 다섯이다 — [03] 참조)
 L3542-3568  받은 스트림을 RSC 로 되돌린다

 L3562  return createFromReadableStream(stream, {
          findSourceMapURL, serverConsumerManifest,
          temporaryReferences, replayConsoleLogs,
          environmentName: 'Cache',
        })
 ★ 캐시 항목이 **RSC 스트림**이다. 값을 JSON 으로 담는 것이 아니라
   직렬화된 렌더 결과를 담고, 읽을 때 다시 역직렬화한다
 ★ `environmentName: 'Cache'` — 개발자 도구에서 이 경계가 따로 보인다
```

1. [진입과 두 스토어](01_enter/README.md) — 어디서 불렸는지가 갈래 열 개를 만든다.
2. [캐시 키](02_key/README.md) — 인자를 직렬화하고 루트 파라미터를 뒤에 붙인다.
3. [캐시를 세 겹으로 찾는다](03_lookup/README.md) — RDC → 요청 안 → 요청 사이(+ 핸들러 조회).
4. [수명과 태그](04_life/README.md) — 중첩은 **언제나 최솟값**으로 좁아진다.

```text
 ★★★ 캐시 수명이 HTTP Cache-Control 의 번역이다 (UCLIFE L8-10)

 주석 원문
   "The equivalent header is kind of like:
    Cache-Control: max-age=[stale],s-max-age=[revalidate],
      stale-while-revalidate=[expire-revalidate],stale-if-error=[expire-revalidate]
    Except that stale-while-revalidate/stale-if-error only applies to
    shared caches - not private caches."

   stale      --> max-age                          클라이언트가 서버에 안 묻고 쓰는 기간
   revalidate --> s-max-age                        서버가 갱신하는 주기
   expire     --> stale-while-revalidate=[expire-revalidate]
                  그리고 stale-if-error 도 **같은 값**
 ★ 셋째는 `expire` 그대로가 아니라 **`expire - revalidate`(차)** 다.
   트래픽이 없어 오래 묵었을 때 동적으로 떨어지기까지의 여유분이다

 => 세 값의 이름이 왜 그런지가 여기 있다
 ★ 그리고 `expire` 는 `revalidate` 보다 길어야 한다 —
   그 제약은 UCLIFE 가 아니라 `cache-life-profile.ts` L11 의 필드 주석이다
     // In the worst case scenario, where you haven't had traffic in a while,
     // how stale can a value be until you prefer deopting to dynamic.
     // **Must be longer than revalidate.**
 ★ UCLIFE L12-13 은 다른 이야기다 — 기본 프로필이 "자주 revalidate 하되
   expire 하지 않아 언제나 빠른 결과를 주고 기본적으로 멈추지 않는다"
```

## 결과가 쓰이는 곳

```text
 createFromReadableStream 의 반환
      --> `'use cache'` 함수를 부른 자리로 돌아간다.
          [App Router]의 렌더 트리 안이면 그대로 컴포넌트가 된다

 CacheEntry (value · timestamp · revalidate · expire · stale · tags)
      --> 핸들러에 저장된다. [04]가 조립한다

 밖으로 전파되는 수명·태그
      --> 감싼 쪽(부모 `'use cache'` · prerender · request)의 store 에 **최솟값으로** 기록된다.
          [응답 나가기]가 읽는 `Cache-Control` 과 [재검증]의 태그가 이 값들이다

 workStore.invalidDynamicUsageError
      --> [App Render]의 검증이 읽는다. `'use cache'` 안에서 동적 API 를 쓴 흔적
```

## 다루지 않는 것

`cache()` 의 스트림 조립 세부(`createTrackedReadableStream` L1697 · `cloneCacheResult` L1627 · `getNthCacheResult` L1656)와 `generateCacheEntryImpl`(L1268-1625) 본문 전체, `handlers.ts`(352줄)의 핸들러 등록·초기화(`initializeCacheHandlers` L59 · `setCacheHandler` L322)와 `tiered-cache-handler.ts`(208줄)의 2단 구조, `use-cache-probe-scheduler.ts`(195줄) · `use-cache-probe-globals.ts`(63줄)와 개발 서버의 멈춤 탐지 워커, `cache-life-profile.ts`(96줄)의 프로필 검증과 `next.config` 의 `cacheLife` 설정, Resume Data Cache 자체(`server/resume-data-cache/`)의 구조, `unstable_cache`(옛 API)와 `fetch` 캐시(`lib/patch-fetch.ts`), SWC 가 `'use cache'` 지시어를 읽어 함수를 다시 쓰는 Rust 쪽(`crates/next-custom-transforms` 의 `create_cache_wrapper`)과 Turbopack import map(`next_import_map.rs` L1197-1200)의 등록 절차, `handlers.ts` 의 `isBuiltInCacheHandler`(L210) · `isMemoryCacheDisabled`(L178)가 핸들러 **인스턴스 집합**으로 판정하는 방식, 클라이언트 참조 매니페스트와 `encodeReply`/`decryptActionBoundArgs` 의 직렬화는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 진입과 두 스토어](01_enter/README.md)
- [02 캐시 키](02_key/README.md)
- [03 캐시를 세 겹으로 찾는다](03_lookup/README.md)
- [04 수명과 태그](04_life/README.md)
