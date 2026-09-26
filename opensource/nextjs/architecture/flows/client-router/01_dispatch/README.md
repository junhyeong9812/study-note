# 01 디스패치 표면

상위: [클라이언트가 화면을 바꾸기까지](../README.md)

`router-reducer.ts` 는 69줄이다. switch 하나와 **서버용 noop 하나**가 전부다. 이 파일이 클라이언트 라우터 전체의 입구다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `router-reducer.ts` L1-L69 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/router-reducer.ts#L1-L69))

## 실제 코드

파일 끝이 이 파일의 요점이다.

```ts
// router-reducer.ts L60-L69
function serverReducer(
  state: ReadonlyReducerState,
  _action: ReducerActions
): ReducerState {
  return state
}

// we don't run the client reducer on the server, so we use a noop function for better tree shaking
export const reducer =
  typeof window === 'undefined' ? serverReducer : clientReducer
```

```text
 => 같은 모듈이 서버 번들에도 들어간다. 거기서는 상태를 그대로 돌려준다
 주석 L67 - "we don't run the client reducer on the server,
             so we use a noop function for better tree shaking"
 => `typeof window === 'undefined'` 를 **모듈 최상위에서** 평가한다.
    번들러가 그것을 보고 clientReducer 쪽 가지를 서버 번들에서 지울 수 있다
 ★ 조건을 함수 안에 두면 이 효과가 없다. 위치가 의도된 것이다
   (※ 뒷문장은 내 해석이다)
```

## 동작 흐름

```text
 RREDUCER L1-69

 L1-18   import — 액션 상수 여섯, 타입 셋, 리듀서 **다섯**
         ★ hmr-refresh-reducer 는 여기 없다 (아래 별항)

 L23  clientReducer(state, action)
 L27    switch (action.type)
 L28      case ACTION_NAVIGATE       L29  => navigateReducer(state, action)
 L31      case ACTION_SERVER_PATCH   L32  => serverPatchReducer(state, action)
 L34      case ACTION_RESTORE        L35  => restoreReducer(state, action)
 L37      case ACTION_REFRESH        L38  => refreshReducer(state, action)
 L40      case ACTION_HMR_REFRESH
 L41        개발이면
 L42          const { hmrRefreshReducer } =
 L43            require('./reducers/hmr-refresh-reducer') 로 그때 불러온다
 L44          => hmrRefreshReducer(state, action)
 L45        아니면
 L46          => throw 'hmrRefresh can only be used in development mode.
                        Please use refresh instead.'
 L51      case ACTION_SERVER_ACTION  L52  => serverActionReducer(state, action)
 L55      default
 L56        => throw new Error('Unknown action')
             주석 L54 - "This case should never be hit as dispatch is strongly typed."

 L60  serverReducer(state, _action) { return state }
 L68  reducer =
 L69    typeof window === 'undefined' ? serverReducer : clientReducer
```

```text
 ★★ HMR 리듀서만 다르게 다룬다

 다른 다섯      파일 위에서 정적 import (L14-18)
 HMR 하나       case 안에서 `require` (L43)

 => 정적 import 면 프로덕션 번들에도 따라 들어간다.
    `require` 로 미루면 그 갈래가 제거될 때 모듈도 함께 빠진다
 => 그리고 개발이 아니면 **던진다** (NODE_ENV === 'development' 검사라 test 에서도 던진다)
 ★★ 다만 이 throw 는 **사실상 도달 불가**다.
    유일한 디스패처인 router.hmrRefresh()(app-router-instance.ts L484-489)가
    **같은 문구로 먼저** 던진다. 이중 가드다
```

```text
 ★ default 갈래는 있지만 도달하지 않기를 기대한다 (L54-56)

   // This case should never be hit as dispatch is strongly typed.
   default:
     throw new Error('Unknown action')

 => 타입으로 막았다고 적어 놓고도 런타임 가드를 남겼다
 ★ [재검증] 흐름의 `workUnitStore satisfies never` 와 대비된다 —
   그쪽은 타입 수준 전수 확인만 하고 던지지 않았다.
   여기는 던진다
```

## 결과가 쓰이는 곳

```text
 reducer (export)
      --> import 하는 곳은 **app-router-instance.ts L15 하나**뿐이고,
          L233-236 이 **async 래퍼**로 감싸 액션 큐의 `action` 필드로 넣는다
      ★ `useReducer` 가 아니다. app-router.tsx 는 이 파일을 import 하지도 않는다
      ★ 상태도 React 가 안 들고 있다 — 모듈 전역 globalActionQueue 다.
        use-action-queue.ts 의 useState 는 그것을 React 에 동기화하는 용도다
      --> 서버 렌더 때는 serverReducer 라 상태가 그대로 통과한다

 각 리듀서의 반환 ReducerState
      --> `(Promise<AppRouterState> & {_debugInfo?}) | AppRouterState` 유니온이다
          (router-reducer-types.ts L262-264)
      ★ 동기 객체가 아니다. 대부분 Promise 다 ([README] 참고)

 throw 'Unknown action' / 'hmrRefresh can only be used in development mode.'
      --> 전자는 타입이 깨졌을 때, 후자는 프로덕션에서 HMR 액션이 왔을 때
```

## 다루지 않는 것

액션 6종의 페이로드 정의(`router-reducer-types.ts` 272줄)와 `ReducerState` / `ReadonlyReducerState` 의 필드, 리듀서 다섯의 본문(`server-patch-reducer` 79줄 · `restore-reducer` 121줄 · `refresh-reducer` 116줄 · `hmr-refresh-reducer`), `app-router-instance.ts`(523줄)가 L234 에서 이 리듀서를 부르는 방식과 디스패치를 일으키는 쪽(`links.ts` 401줄), 서버 번들에서 실제로 트리 셰이킹이 일어나는지의 확인은 이 문서의 범위 밖이다.
