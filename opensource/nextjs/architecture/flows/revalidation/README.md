# 재검증이 쌓이고 실행되기까지

상위: [Next.js 아키텍처 지도](../../README.md)

`revalidateTag()` 를 부르면 그 자리에서 캐시가 지워지지 않는다. **요청이 끝날 때까지 모아 두었다가 한꺼번에 실행한다.** 앞선 흐름들이 `executeRevalidates` 와 `addRevalidationHeader` 로 계속 가리킨 자리가 여기다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `REVAL` = `server/web/spec-extension/revalidate.ts`(258줄), `REVUTIL` = `server/revalidation-utils.ts`(221줄).

## 위치

`packages/next` / `src/server/web/spec-extension` / `revalidate.ts` L128-L258 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/web/spec-extension/revalidate.ts#L128-L258))

`packages/next` / `src/server` / `revalidation-utils.ts` L186-L221 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/revalidation-utils.ts#L186-L221))

## 실제 코드

사용자 API 셋이 **같은 함수 하나**로 모인다.

```ts
// revalidate.ts L35-L44
export function revalidateTag(tag: string, profile: string | CacheLifeConfig) {
  if (!profile) {
    console.warn(
      '"revalidateTag" without the second argument is now deprecated, add second argument of "max" or use "updateTag". See more info here: https://nextjs.org/docs/messages/revalidate-tag-single-arg'
    )
  } else if (typeof profile === 'object') {
    profile = validateAndNormalizeCacheLifeProfile(profile, { kind: 'inline' })
  }
  return revalidate([encodeHeaderSafe(tag)], `revalidateTag ${tag}`, profile)
}
```

```text
 revalidateTag(tag, profile)   L35  => revalidate([tag], `revalidateTag ${tag}`, profile)
 updateTag(tag)                L52  => revalidate([tag], `updateTag ${tag}`, undefined)
 revalidatePath(path, type?)   L100 => revalidate(tags, `revalidatePath ${path}`)
 refresh()                     L73  => 유일하게 revalidate 를 안 부른다

 => 셋이 `revalidate(tags, expression, profile)` (L128)로 들어간다.
    **모두 태그로 환원된다**
```

## 동작 흐름

```text
 ★★★ 세 단계로 나뉘어 있다

 1단  쌓기     REVAL L128-258   revalidate() 가 workStore 에 밀어 넣는다     [01]
 2단  실행     REVUTIL L186-221 executeRevalidates() 가 한꺼번에 돌린다     [02]
 3단  알리기   ACTION L151      addRevalidationHeader() 가 헤더로 알린다    [03]

 => 대개 **거기서 캐시가 지워지지는 않는다.** 배열에 항목이 쌓이고 끝난다
 ★ 다만 "아무 일도" 는 아니다
     store.pathWasRevalidated 도 세운다 (L254-256)
     revalidatePath 는 항목이 **둘** 늘 수 있다 (L119-123)
     개발 모드면 workUnitStore.usedDynamic = true (L196-203)
     같은 요청의 이후 캐시 읽기는 **즉시** 영향을 받는다
       (use-cache-wrapper.ts L3733-3740 · incremental-cache/index.ts L509 · L572)
     그리고 대부분의 문맥에서는 **던진다** ([01])
```

1. [쌓기](01_collect/README.md) — 부르는 자리에 따라 열두 갈래로 갈리고 하나만 통과한다.
2. [실행](02_execute/README.md) — 세 통을 모아 `Promise.all`.
3. [알리기](03_notify/README.md) — 클라이언트가 자기 캐시를 버리게 한다.

```text
 ★★★ revalidatePath 는 경로를 **태그로 바꾼다.** 그리고 `profile` 을 안 넘긴다 (L100-126)

 L101  경로가 NEXT_CACHE_SOFT_TAG_MAX_LENGTH 보다 길면 경고하고 **return** — 아무것도 안 쌓는다
 L108  normalizedPath = `${NEXT_CACHE_IMPLICIT_TAG_ID}${removeTrailingSlash+encodeHeaderSafe(경로)}`
 L118  tags = [normalizedPath]
 L125  => return revalidate(tags, `revalidatePath ${originalPath}`)   ← **셋째 인자가 없다**

 => 경로에 접두를 붙여 **태그로 만든다**. 캐시 계층은 태그만 안다
 ★★ 그런데 profile 을 안 넘기므로 **의미상 `updateTag` 쪽**이다.
    `revalidateTag(tag, profile)` 과는 다른 갈래를 탄다 ([03] 참고)
 ★ `/` 와 `/index` 를 서로 보태 준다 (L119-123)
     `/` 면 `/index` 도, `/index` 면 `/` 도 태그에 넣는다
 ★ 동적 경로에 `type` 을 안 주면 경고하고 **아무 효과가 없다** (L112-116)
     'a dynamic page path ... was passed to "revalidatePath", but the "type"
      parameter is missing. This has no effect by default'
```

```text
 ★★ revalidateTag 는 두 번째 인자가 이제 **필수처럼 됐다** (L36-39)

   if (!profile) {
     console.warn('"revalidateTag" without the second argument is now deprecated,
                   add second argument of "max" or use "updateTag". ...')
   }

 => 인자 없이 부르면 경고가 난다. `'max'` 를 주거나 `updateTag` 를 쓰라고 한다
 ★ `updateTag` 의 에러 메시지는 "서버 액션에서만" 이라고 말하지만 (L57-63)
   실제 가드는 **둘뿐**이다 — workStore 가 있고 page 가 '/route' 로 끝나지 않는 것.
   phase 검사가 없다 (phase 를 보는 것은 refresh 뿐 — L77-81).
   실제 차단은 `revalidate()` 의 phase/type 검사가 대신한다
 ★ JSDoc L48 이 존재 이유를 말한다 — "to enable read-your-own-writes semantics".
   L242-244 주석의 "자기 쓰기를 자기가 읽지 않는다" 와 **정반대 쪽**이다
   주석 L55-56 - 라우트 핸들러에도 phase: 'action' 이 서는 이유를 아직 모른다는 TODO
   주석 L64 - updateTag 는 즉시 만료(profile 없음)를 쓰는데 **경고는 안 낸다**
```

```text
 ★★ refresh() 만 다른 일을 한다 (L73-93)

 L91  workStore.pathWasRevalidated = ActionDidRevalidateDynamicOnly

 주석 L89-90
   "The Server Action version of refresh() only revalidates the dynamic data
    on the client. It doesn't affect cached data."
 => 서버 캐시를 건드리지 않는다. **클라이언트의 동적 데이터만** 새로 받게 한다
 ★ 조건이 셋이다 (L77-81) — workStore 가 있고, page 가 '/route' 가 아니고,
   workUnitStore.phase === 'action' 이어야 한다
```

## 결과가 쓰이는 곳

```text
 workStore.pendingRevalidatedTags
      --> [02]의 executeRevalidates 가 읽는다.
          {tag, profile, revalidatedAt} 세 칸짜리 항목이 쌓인다

 workStore.pathWasRevalidated
      --> [03]의 addRevalidationHeader 가 읽어 헤더를 정한다.
          refresh() 는 여기에 ActionDidRevalidateDynamicOnly 를 넣는다

 executeRevalidates 의 반환 (false | Promise<void>)
      --> 호출처는 **다섯**이다
            app-render.tsx L2848 · L3071        (정적 갈래 · 동적 갈래)
            action-handler.ts L1246 · L1433     (액션 응답 · 에러 경로)
            route-modules/app-route/module.ts L397  (라우트 핸들러)
      --> 할 일이 없으면 false 라 호출부가 분기한다

 DynamicServerError (L188)
      --> [정적 응답]이 "예전 방식의 동적 에러 처리" 라 부른 그 예외.
          정적 생성 중에 revalidateTag 를 부르면 여기서 난다
```

## 다루지 않는 것

`IncrementalCache` 의 구현과 태그가 실제로 캐시 항목을 무효화하는 방식, `use-cache/handlers.ts`(352줄)의 `getCacheHandlers` 와 캐시 핸들러 규약, `'use cache'`(`use-cache-wrapper.ts` 3744줄)가 캐시를 채우고 태그를 붙이는 과정, `cacheLife`(`use-cache/cache-life.ts` 122줄) / `cacheTag`(41줄)와 프로필 형식, `validateAndNormalizeCacheLifeProfile` 의 검증, `NEXT_CACHE_IMPLICIT_TAG_ID` / `NEXT_CACHE_SOFT_TAG_MAX_LENGTH` 상수의 값과 유래, `unstable_cache` 의 별도 경로, `pendingRevalidates` / `pendingRevalidateWrites` 에 항목을 넣는 쪽(fetch 패치 등), 클라이언트 라우터가 재검증 헤더를 받아 캐시를 버리는 쪽은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 쌓기](01_collect/README.md)
- [02 실행](02_execute/README.md)
- [03 알리기](03_notify/README.md)
