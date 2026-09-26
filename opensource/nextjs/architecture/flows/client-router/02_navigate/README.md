# 02 내비게이션

상위: [클라이언트가 화면을 바꾸기까지](../README.md)

56줄이다. 클라이언트 라우팅의 핵심 액션인데 리듀서가 이렇게 작은 이유는 **본체가 다른 곳으로 옮겨졌기** 때문이다. 소스가 스스로 "임시 접착 코드" 라고 적어 놓았다.

## 위치

`packages/next` / `src/client/components/router-reducer/reducers` / `navigate-reducer.ts` L1-L56 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/reducers/navigate-reducer.ts#L1-L56))

## 실제 코드

파일 전체가 짧아 통째로 볼 수 있다.

```ts
// navigate-reducer.ts L23-L56
export function navigateReducer(
  state: ReadonlyReducerState,
  action: NavigateAction
): ReducerState {
  const { url, isExternalUrl, navigateType, scrollBehavior } = action

  if (isExternalUrl) {
    return completeHardNavigation(state, url, navigateType)
  }

  // Handles case where `<meta http-equiv="refresh">` tag is present,
  // which will trigger an MPA navigation.
  if (document.getElementById('__next-page-redirect')) {
    return completeHardNavigation(state, url, navigateType)
  }

  // Temporary glue code between the router reducer and the new navigation
  // implementation. Eventually we'll rewrite the router reducer to a
  // state machine.
  const currentUrl = new URL(state.canonicalUrl, location.origin)
  const currentRenderedSearch = state.renderedSearch
  return navigateUsingSegmentCache(
    state,
    url,
    currentUrl,
    currentRenderedSearch,
    state.cache,
    state.tree,
    state.nextUrl,
    FreshnessPolicy.Default,
    scrollBehavior,
    navigateType
  )
}
```

```text
 주석 L39-41
   "Temporary glue code between the router reducer and the new navigation
    implementation. Eventually we'll rewrite the router reducer to a
    state machine."

 => 리듀서에서 세그먼트 캐시로 **인자를 늘어놓아 넘기는** 일만 한다.
    상태 기계로 다시 쓸 계획이라고 적혀 있다
```

## 동작 흐름

```text
 navigateReducer  NAVRED L23-56

 L27  {url, isExternalUrl, navigateType, scrollBehavior} = action

 --- 하드 내비게이션으로 빠지는 둘 ---
 L29  isExternalUrl 이면
 L30    => return completeHardNavigation(state, url, navigateType)
 L35  document.getElementById('__next-page-redirect') 가 있으면
 L36    => return completeHardNavigation(state, url, navigateType)
        주석 L33-34 - `<meta http-equiv="refresh">` 태그가 있는 경우다.
          그것이 MPA 내비게이션을 일으킨다

 --- 그 밖 전부: 세그먼트 캐시로 넘긴다 ---
 L42  currentUrl = new URL(state.canonicalUrl, location.origin)
 L43  currentRenderedSearch = state.renderedSearch
 L44  => return navigateUsingSegmentCache(
         state, url, currentUrl, currentRenderedSearch,
         state.cache, state.tree, state.nextUrl,
         FreshnessPolicy.Default, scrollBehavior, navigateType)
       ★ 인자가 **열 개**다. 상태에서 필요한 것을 하나씩 꺼내 넘긴다
```

```text
 ★★★ 인자 열 개가 이 파일의 성격을 말한다

 상태 객체(state)를 이미 첫 인자로 넘기는데도
 state.cache · state.tree · state.nextUrl · state.renderedSearch 를
 **따로 또 넘긴다**

 => 받는 쪽이 리듀서의 상태 모양에 기대지 않으려는 것으로 보인다.
    그래야 나중에 리듀서를 상태 기계로 바꿔도 세그먼트 캐시를 안 고친다
 ※ 뒷문장은 내 해석이다. 소스는 "임시 접착 코드" 라고만 말한다
```

```text
 ★★ 하드 내비게이션 갈래가 둘이다

 isExternalUrl                        다른 오리진이면 브라우저에 맡긴다
 '__next-page-redirect' 엘리먼트 존재  `<meta http-equiv="refresh">` 가 심겨 있다

 => 둘 다 `completeHardNavigation` 으로 간다
 ★ 다만 그 함수가 문서를 받아 오는 것은 아니다 —
   `pushRef.mpaNavigation = true` 를 세운 **새 상태만** 돌려준다
   (navigation.ts L691-712). 실제 재요청은 AppRouter 가 한다
 ★ `javascript:` URL 이면 state 를 그대로 돌려주고 아무것도 안 한다 (L685-690)
 ★ 두 번째(L35)가 흥미롭다 — DOM 을 직접 조회해 판단한다.
   서버가 심어 둔 엘리먼트를 클라이언트 라우터가 읽는 통로다
```

```ts
// navigate-reducer.ts L12-L21
import { FreshnessPolicy } from '../ppr-navigations'

// These values are set by `define-env-plugin` (based on `nextConfig.experimental.staleTimes`)
// and default to 5 minutes (static) / 0 seconds (dynamic)
export const DYNAMIC_STALETIME_MS =
  Number(process.env.__NEXT_CLIENT_ROUTER_DYNAMIC_STALETIME) * 1000

export const STATIC_STALETIME_MS = getStaleTimeMs(
  Number(process.env.__NEXT_CLIENT_ROUTER_STATIC_STALETIME)
)
```

```text
 ★★ staleTime 둘이 빌드타임 상수다

 L16  DYNAMIC_STALETIME_MS = Number(process.env.__NEXT_CLIENT_ROUTER_DYNAMIC_STALETIME) * 1000
 L19  STATIC_STALETIME_MS  = getStaleTimeMs(Number(process.env.__NEXT_CLIENT_ROUTER_STATIC_STALETIME))

 주석 L14-15
   "These values are set by `define-env-plugin` (based on `nextConfig.experimental.staleTimes`)
    and default to 5 minutes (static) / 0 seconds (dynamic)"

 => 기본값이 정적 5분 / 동적 0초다 (define-env.ts L234-243).
    `next.config` 의 `experimental.staleTimes` 로 바꾼다
 ★ 다만 **비대칭이다** — 인용한 코드가 그것을 보여 준다.
   static 은 `getStaleTimeMs` 를 거치고 그 안이 `Math.max(s, 30) * 1000` 이라
   **30초 하한**이 있다 (cache.ts L122-124).
   dynamic 은 `* 1000` 뿐이라 하한이 없다
 ★★ 그런데 `DYNAMIC_STALETIME_MS` 는 **프리페치 캐시와 무관하다.**
   소비처가 segment-cache/bfcache.ts L21 의 computeDynamicStaleAt 하나뿐이고,
   그것은 **이미 받은 동적 데이터의 staleAt**(BFCache 항목)을 정한다.
   프리페치 캐시(cache.ts)는 STATIC 만 import 한다 (L107)
   bfcache.ts L45-47 주석이 못박는다 —
     "Used to compute the stale time for dynamic prefetches
      (which use **STATIC_STALETIME_MS instead of DYNAMIC_STALETIME_MS**)."
   => 두 캐시(프리페치 세그먼트 캐시 / BFCache)는 다른 것이다
 ★ 이 두 상수를 여기서 export 하는 것도 접착 코드의 흔적이다 —
   내비게이션 본체가 옮겨갔는데 상수는 남아 있다
```

## 결과가 쓰이는 곳

```text
 navigateUsingSegmentCache 의 반환
      --> 그대로 ReducerState 가 된다. [01]의 switch 가 받아 돌려준다

 completeHardNavigation 의 반환
      --> 같은 자리. 다만 이 경우 실제 화면 전환은 브라우저가 한다

 STATIC_STALETIME_MS
      --> 프리페치 세그먼트 캐시 (cache.ts L107 이 import 한다)

 DYNAMIC_STALETIME_MS
      --> **BFCache** (bfcache.ts L21 computeDynamicStaleAt). 프리페치가 아니다
```

## 다루지 않는 것

`segment-cache/navigation.ts`(1278줄)의 `navigate` 와 `completeHardNavigation` 본문, `segment-cache/cache.ts`(4298줄) · `scheduler.ts`(2741줄) · `optimistic-routes.ts`(1119줄) 등 세그먼트 캐시 전체(11,522줄), `FreshnessPolicy` 열거와 `Default` 의 의미, `ppr-navigations.ts`(2383줄)와 PPR 내비게이션 병합, `getStaleTimeMs` 의 변환, `define-env-plugin` 이 `staleTimes` 를 상수로 박는 과정, `__next-page-redirect` 엘리먼트를 심는 쪽, `NavigateAction` 의 필드(`navigateType` · `scrollBehavior` 의 값들)는 이 문서의 범위 밖이다.
