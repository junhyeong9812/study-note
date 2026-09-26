# 클라이언트가 화면을 바꾸기까지

상위: [Next.js 아키텍처 지도](../../README.md)

지금까지의 일곱 흐름은 전부 서버 쪽이었다. 그 서버가 만든 응답을 **받아서 화면을 바꾸는 쪽**이 여기다. 서버 흐름들이 붙인 헤더(`x-action-redirect` · 재검증 플래그)를 읽는 자리도 여기다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `RREDUCER` = `client/components/router-reducer/router-reducer.ts`(69줄), `NAVRED` = `.../reducers/navigate-reducer.ts`(56줄), `SARED` = `.../reducers/server-action-reducer.ts`(568줄), `RTYPES` = `.../router-reducer-types.ts`(272줄).

## 위치

`packages/next` / `src/client/components/router-reducer` / `router-reducer.ts` L23-L58 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/router-reducer.ts#L23-L58))

## 실제 코드

액션 6종을 받는 switch 하나가 전부다.

```ts
// router-reducer.ts L27-L57
  switch (action.type) {
    case ACTION_NAVIGATE: {
      return navigateReducer(state, action)
    }
    case ACTION_SERVER_PATCH: {
      return serverPatchReducer(state, action)
    }
    case ACTION_RESTORE: {
      return restoreReducer(state, action)
    }
    case ACTION_REFRESH: {
      return refreshReducer(state, action)
    }
    case ACTION_HMR_REFRESH: {
      if (process.env.NODE_ENV === 'development') {
        const { hmrRefreshReducer } =
          require('./reducers/hmr-refresh-reducer') as typeof import('./reducers/hmr-refresh-reducer')
        return hmrRefreshReducer(state, action)
      } else {
        throw new Error(
          'hmrRefresh can only be used in development mode. Please use refresh instead.'
        )
      }
    }
    case ACTION_SERVER_ACTION: {
      return serverActionReducer(state, action)
    }
    // This case should never be hit as dispatch is strongly typed.
    default:
      throw new Error('Unknown action')
  }
```

## 동작 흐름

```text
 ★★ 액션이 여섯이고 리듀서가 여섯이다

   ACTION_NAVIGATE       navigate-reducer.ts        56줄   ★ 접착 코드다
   ACTION_SERVER_PATCH   server-patch-reducer.ts    79줄
   ACTION_RESTORE        restore-reducer.ts        121줄
   ACTION_REFRESH        refresh-reducer.ts        116줄
   ACTION_HMR_REFRESH    hmr-refresh-reducer.ts           개발 전용
   ACTION_SERVER_ACTION  server-action-reducer.ts  568줄   ★ 가장 크다

 => 리듀서 합계 961줄(+ router-reducer 69) 중 568 이 서버 액션 관련이다 — 59%
    ★ 그중 응답 해석은 L184-308 이고 요청 만들기 L107-181 · 상태 적용 L314-568 이다.
      "절반 이상이 응답 처리" 는 과한 말이었다

 ★★ 그리고 **1:1 표가 아니다**
   ACTION_SERVER_PATCH 에는 외부 디스패처가 없다 —
   라우터 자신의 내비게이션 기계가 라우트 트리 불일치 후 재시도로 던진다
     ppr-navigations.ts L1789-1799  dispatchAppRouterAction(retryAction)
   리듀서끼리도 서로 부른다
     server-patch-reducer.ts L40  트리가 이미 바뀌었으면 => refreshReducer(state, {type: ACTION_REFRESH})
     serverAction · serverPatch · navigate 가 같은 navigate/completeHardNavigation 진입점을 공유한다
```

1. [디스패치 표면](01_dispatch/README.md) — 서버에서는 noop 이 되는 리듀서.
2. [내비게이션](02_navigate/README.md) — 56줄짜리 접착 코드와 그 뒤의 11,522줄.
3. [서버 액션 응답 받기](03_server-action/README.md) — [서버 액션] 흐름의 짝.

```text
 ★★★ 리듀서가 서버에서는 **아무것도 안 한다** (RREDUCER L60-69)

   function serverReducer(state, _action) { return state }

   // we don't run the client reducer on the server, so we use a noop function
   // for better tree shaking
   export const reducer =
     typeof window === 'undefined' ? serverReducer : clientReducer

 => 같은 모듈이 서버 번들에도 들어가는데, 거기서는 상태를 그대로 돌려준다
 => 주석이 이유를 말한다 — **트리 셰이킹**. 번들러가 clientReducer 와
    그것이 정적으로 끌고 오는 리듀서 **다섯**을 서버 번들에서 지울 수 있게 한다
    (hmr-refresh-reducer 는 애초에 정적 그래프에 없다 — 아래 별항)
```

```text
 ★★ HMR 리듀서만 **인라인 require** 다 (RREDUCER L40-50)

   case ACTION_HMR_REFRESH: {
     if (process.env.NODE_ENV === 'development') {
       const { hmrRefreshReducer } = require('./reducers/hmr-refresh-reducer')
       return hmrRefreshReducer(state, action)
     } else {
       throw new Error('hmrRefresh can only be used in development mode.
                        Please use refresh instead.')
     }
   }

 => 다른 다섯은 파일 위에서 import 한다. 이것만 `require` 다
 => 프로덕션 번들에 hmr-refresh-reducer 를 아예 넣지 않으려는 것이다
 ★ 그 갈래의 throw 는 이중 가드다 — 디스패처(app-router-instance.ts L484-489)가
   같은 문구로 먼저 던지므로 여기까지 오지 않는다
```

```text
 ★★★ navigate 리듀서가 56줄뿐인 이유 (NAVRED)

 주석 L39-41
   "Temporary glue code between the router reducer and the new navigation
    implementation. Eventually we'll rewrite the router reducer to a
    state machine."

 => 내비게이션의 본체가 **세그먼트 캐시로 옮겨졌다**.
    navigate-reducer 는 인자를 늘어놓아 넘겨 주는 일만 한다
      segment-cache/navigation.ts  navigate(...)   1278줄
      segment-cache/cache.ts                       4298줄
      segment-cache/scheduler.ts                   2741줄
      (segment-cache 전체 11,522줄)
 => 리듀서를 **상태 기계로 다시 쓸 계획**이라고 소스가 적어 놓았다
```

## 결과가 쓰이는 곳

```text
 ReducerState
      --> `app-router-instance.ts` L233-236 이 **async 래퍼로 감싸** 액션 큐의 필드로 쓴다
            action: async (state, action) => { const result = reducer(state, action); return result }
      ★ 정본 상태는 React 밖에 있다 — 모듈 전역 `globalActionQueue` 가 들고 있다.
        use-action-queue.ts L12-14 주석 - "The app router state lives outside of React"
        useState 는 그 바깥 상태를 React 에 **동기화**하려고만 있다 (L134-138)

 clientReducer 가 서버 번들에서 사라지는 것
      --> 서버 번들 크기. 정적 import 한 리듀서 **다섯**과 그 의존이 빠진다

 각 리듀서의 반환 ReducerState
      --> **Promise 를 포함하는 유니온**이다 (RTYPES L262-264)
            (Promise<AppRouterState> & {_debugInfo?}) | AppRouterState
      --> serverActionReducer 는 **언제나** Promise 다 (SARED L335 `.then(...)`)
          navigate 도 캐시에 맞는 프리페치가 없으면 Promise 를 돌려준다
          동기 객체를 돌려주는 것은 restoreReducer 와 completeHardNavigation 뿐이다
      ★★ 이것이 "상태 기계로 다시 쓰겠다" 는 이유다 —
         반환이 Promise 라 큐가 직렬화하고 await 해야 한다
```

## 다루지 않는 것

`segment-cache/`(11,522줄) 전체 — `navigation.ts` · `cache.ts` · `scheduler.ts` · `optimistic-routes.ts` · `vary-path.ts` · `bfcache.ts`, `ppr-navigations.ts`(2383줄)의 PPR 내비게이션 병합, `fetch-server-response.ts`(875줄)가 RSC 응답을 받아 파싱하는 과정, `<AppRouter>`(657줄) / `<LayoutRouter>`(988줄) 컴포넌트의 렌더, `app-router-instance.ts`(523줄)와 `useRouter()` 가 돌려주는 객체, `links.ts`(401줄)와 `<Link>` 의 프리페치 트리거, `create-initial-router-state.ts`(280줄), `compute-changed-path.ts`(251줄), `restore-reducer` / `refresh-reducer` / `server-patch-reducer` / `hmr-refresh-reducer` 의 본문, `ReducerState` 의 필드 전체는 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 디스패치 표면](01_dispatch/README.md)
- [02 내비게이션](02_navigate/README.md)
- [03 서버 액션 응답 받기](03_server-action/README.md)
