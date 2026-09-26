# 03 알리기

상위: [재검증이 쌓이고 실행되기까지](../README.md)

`addRevalidationHeader` 는 55줄이다. 서버 캐시를 지우는 것과 별개로, **클라이언트에게 "네 캐시도 버려라" 고 알린다.** 값이 셋뿐이고 주석에 TODO 가 셋이다.

## 위치

`packages/next` / `src/server/app-render` / `action-handler.ts` L151-L205 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/action-handler.ts#L151-L205))

## 실제 코드

값 셋의 정의가 별도 파일에 있다.

```text
 shared/lib/action-revalidation-kind.ts
   L3  ActionDidNotRevalidate             = 0
   L4  ActionDidRevalidateStaticAndDynamic = 1
   L5  ActionDidRevalidateDynamicOnly      = 2

 => 클라이언트로 가는 것은 **숫자 하나**다.
    어떤 태그·경로가 무효화됐는지는 **안 보낸다**
```

```ts
// action-handler.ts L161-L182
  // If a tag was revalidated, the client router needs to invalidate all the
  // client router cache as they may be stale. And if a path was revalidated, the
  // client needs to invalidate all subtrees below that path.

  // TODO: Currently we don't send the specific tags or paths to the client,
  // we just send a flag indicating that all the static data on the client
  // should be invalidated. In the future, this will likely be a Bloom filter
  // or bitmask of some kind.

  // TODO-APP: Currently the prefetch cache doesn't have subtree information,
  // so we need to invalidate the entire cache if a path was revalidated.
  // TODO-APP: Currently paths are treated as tags, so the second element of the tuple
  // is always empty.

  // Only count tags without a profile (updateTag) as requiring client cache invalidation
  // Tags with a profile (revalidateTag) use stale-while-revalidate and shouldn't
  // trigger immediate client-side cache invalidation
  const isTagRevalidated = workStore.pendingRevalidatedTags?.some(
    (item) => item.profile === undefined
  )
    ? 1
    : 0
```

## 동작 흐름

```text
 addRevalidationHeader  ACTION L151-205
   ([서버 액션] [02]의 finally L1227 이 부른다)

 L178  isTagRevalidated = pendingRevalidatedTags 중 **profile 이 undefined 인 것**이 있으면 1
          주석 L175-177 - profile 없는 태그(updateTag)만 클라이언트 캐시 무효화로 센다.
            profile 이 있는 태그(revalidateTag)는 stale-while-revalidate 라
            즉시 무효화를 일으키지 않아야 한다
 L183  isCookieRevalidated = 바뀐 쿠키가 있으면 1
          (getModifiedCookieValues(requestStore.mutableCookies))

 L190  isTagRevalidated 이거나 isCookieRevalidated 이면
 L191    NEXT_ACTION_REVALIDATED_HEADER = JSON.stringify(ActionDidRevalidateStaticAndDynamic)  // 1
 L195  아니고 pathWasRevalidated 가 정의돼 있고 ActionDidNotRevalidate 도 아니면
 L200    NEXT_ACTION_REVALIDATED_HEADER = JSON.stringify(workStore.pathWasRevalidated)
          => refresh() 가 넣은 ActionDidRevalidateDynamicOnly(2)가 여기로 나간다
 (그 밖에는 헤더를 아예 안 붙인다)
```

```text
 ★★★ 갈림의 기준은 API 이름이 아니라 **`profile` 유무**다 (L178-180)

   const isTagRevalidated = workStore.pendingRevalidatedTags?.some(
     (item) => item.profile === undefined
   ) ? 1 : 0

 profile 이 **없는** 것 (=> 헤더 1, 정적·동적 전부 무효화)
   updateTag(tag)                      REVAL L65  undefined 를 명시해 넘긴다
   revalidatePath(path, type?)         REVAL L125 **셋째 인자가 없다**
   revalidateTag(tag)  — 1인자 호출     REVAL L43  경고만 하고 undefined 를 넘긴다

 profile 이 **있는** 것 (=> 이 갈래를 안 탄다)
   revalidateTag(tag, 'max') 같은 호출

 ★★ 그러므로 "updateTag 만 클라이언트 캐시를 버린다" 는 **틀리다.**
    `revalidatePath` 도 같은 결과를 낸다
 ★ 그리고 profile 이 있어도 `{expire: 0}` 이면
   REVAL L254 가 pathWasRevalidated 를 세워 **아래 else-if(L195)로** 헤더 1 이 나간다
 => `revalidateTag` 의 JSDoc(REVAL L30-31)이 "For immediate expiration in Server
    Actions, use `updateTag` instead." 라고 권하는 근거가 이 한 줄이다
```

```text
 ★★ 쿠키가 바뀌어도 클라이언트 캐시를 버린다 (L183-187)

   isCookieRevalidated = getModifiedCookieValues(requestStore.mutableCookies).length ? 1 : 0

 => 액션이 쿠키를 고쳤으면 그 쿠키에 기대던 화면이 전부 낡았다고 본다
 ★ `requestStore.mutableCookies` 는 [동적 응답] [04]가 redirect 에
   set-cookie 를 실을 때 쓴 그 값이다
```

```text
 ★★ TODO 가 셋이다. 지금 설계의 한계를 소스가 나열한다 (L165 · L170 · L172)

 L165-168  "Currently we don't send the specific tags or paths to the client,
            we just send a flag indicating that all the static data on the client
            should be invalidated. In the future, this will likely be a Bloom filter
            or bitmask of some kind."
   => 태그 하나를 재검증해도 클라이언트는 **정적 데이터를 전부** 버린다.
      장래에 블룸 필터나 비트마스크로 바꾸겠다고 적어 놓았다

 L170-171  "Currently the prefetch cache doesn't have subtree information,
            so we need to invalidate the entire cache if a path was revalidated."
   => 프리페치 캐시가 서브트리를 모른다. 그래서 경로 재검증도 전체 무효화다

 L172-173  "Currently paths are treated as tags, so the second element of the tuple
            is always empty."
   => [README]가 말한 "revalidatePath 는 내부적으로 태그다" 를 소스가 직접 확인해 준다
```

## 결과가 쓰이는 곳

```text
 NEXT_ACTION_REVALIDATED_HEADER
      --> 클라이언트 라우터가 읽는다.
          client/components/router-reducer/reducers/server-action-reducer.ts L67 이
          ActionDidNotRevalidate 등을 import 한다
      => 1 이면 정적·동적 전부, 2 면 동적만 버린다

 헤더가 없을 때
      --> 클라이언트는 캐시를 그대로 쓴다.
          `revalidateTag(tag, 'max')` 처럼 **expire 가 0 이 아닌 profile** 만 줬고
          쿠키도 안 바꿨을 때가 이 경우다

 [서버 액션] [02]의 finally
      --> 이 함수를 부르는 유일한 자리(L1227).
          액션이 던져도, redirect 로 빠져나가도 헤더는 붙는다
```

## 다루지 않는 것

`getModifiedCookieValues` 와 `mutableCookies` 에 변경이 기록되는 과정, `NEXT_ACTION_REVALIDATED_HEADER` 상수의 실제 문자열, 클라이언트 라우터가 이 헤더를 받아 캐시를 버리는 쪽(`router-reducer/reducers/server-action-reducer.ts`)의 구현, 프리페치 캐시의 구조와 서브트리 정보가 없는 이유, TODO 가 말하는 블룸 필터·비트마스크 설계, `workStore.pathWasRevalidated` 를 `ActionDidRevalidateStaticAndDynamic` 으로 세우는 다른 자리(있다면)는 이 문서의 범위 밖이다.
