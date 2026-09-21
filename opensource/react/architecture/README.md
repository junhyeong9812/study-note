# React 아키텍처 지도

소스를 **직접 읽어서** 그린 탑다운 지도다. 흐름 열세 편, 72개 문서로 되어 있다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 모든 줄 번호는 이 커밋 기준이고, 대상은 **react-dom 클라이언트 빌드**다.

`useState` 나 `useEffect` 같은 API 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다.

## 흐름 열세 편

| 흐름 | 진입점 | 문서 |
|---|---|---|
| [마운트](flows/mount/README.md) | `createRoot` → `root.render` → `scheduleUpdateOnFiber` | 7 |
| [스케줄링](flows/scheduling/README.md) | `processRootScheduleInMicrotask` | 6 |
| [렌더 루프](flows/render-loop/README.md) | `performWorkOnRoot` `ReactFiberWorkLoop.js` L1123 | 7 |
| [beginWork](flows/begin-work/README.md) | `beginWork` `ReactFiberBeginWork.js` L4189 | 5 |
| [completeWork](flows/complete-work/README.md) | `completeWork` `ReactFiberCompleteWork.js` L1080 | 6 |
| [훅](flows/hooks/README.md) | `renderWithHooks` `ReactFiberHooks.js` L502 | 6 |
| [커밋](flows/commit/README.md) | `commitRoot` `ReactFiberWorkLoop.js` L3706 | 5 |
| [패시브 이펙트](flows/passive-effects/README.md) | `flushPassiveEffects` `ReactFiberWorkLoop.js` L4672 | 4 |
| [lane 우선순위](flows/lanes/README.md) | `ReactFiberLane.js` — 비트 배치와 선택 규칙 | 5 |
| [에러와 Suspense](flows/throw/README.md) | `throwException` `ReactFiberThrow.js` L364 | 5 |
| [자식 조정](flows/reconcile-children/README.md) | `reconcileChildFibers` `ReactChildFiber.js` L2108 | 4 |
| [컨텍스트 전파](flows/context/README.md) | `propagateParentContextChanges` `ReactFiberNewContext.js` L411 | 4 |
| [업데이트 큐](flows/update-queue/README.md) | `processUpdateQueue` `ReactFiberClassUpdateQueue.js` L487 | 6 |

## 흐름이 이어지는 자리

```text
 한 번의 setState 가 화면에 닿기까지

 [훅] dispatchSetState
      | scheduleUpdateOnFiber
      v
 [스케줄링]  다음 태스크를 정한다
      | performWorkOnRoot
      v
 [렌더 루프]  work loop 를 돌린다
      |
      +-- performUnitOfWork --> [beginWork]     내려가며 자식을 만든다
      |                              |  processUpdateQueue
      |                              +--> [업데이트 큐]  쌓인 setState 를 접는다
      |                              |  reconcileChildren
      |                              +--> [자식 조정]  옛 fiber 와 짝짓는다
      |                              |
      +-- completeUnitOfWork --> [completeWork] 올라오며 인스턴스를 만든다
      |
      | finishConcurrentRender -> completeRoot
      v
 [커밋]  DOM 을 바꾸고 root.current 를 교체한다
      |
      +-- scheduleCallback ~~> [패시브 이펙트]   useEffect 가 여기서 돈다
      |
      | ensureRootIsScheduled
      v
 [스케줄링]으로 돌아간다        <- 고리가 닫힌다
```

```text
 가로지르는 둘

 [lane 우선순위]  모든 흐름이 "무엇을 먼저" 를 여기에 묻는다
                  [스케줄링]이 태스크 우선순위를 정할 때
                  [렌더 루프]가 양보할지 정할 때 (shouldTimeSlice)
                  [beginWork]가 바이아웃할지 볼 때
                  [completeWork]가 리소스를 프리로드할지 볼 때

 [에러와 Suspense]  정상 경로가 끊길 때 어디로 가는지를 정한다
                  [렌더 루프]의 catch 에서 시작해
                  경계를 찾아 되감고
                  [beginWork]로 되돌려 보낸다
```

```text
 ★ throw 가 제어 흐름이다 - 세 갈래

 컴포넌트가 서스펜드   SuspenseException        [훅]의 use / 렌더 중
 조정 중 에러          case Throw 가 되던짐      [beginWork] L4465
 리소스 미준비         SuspenseyCommitException  [completeWork] L1463

 셋 다 [렌더 루프]의 handleThrow 가 받아 상태로 바꾸고,
 되감기에서 [에러와 Suspense]가 경계를 찾는다
```

```text
 ★ 같은 tag 에 대한 switch 가 넷이다

 [beginWork]    L4283  29 case   실제로 평가한다
 [beginWork]    L3929  14 case   평가하지 않고 스택만 맞춘다 (빠른 바이아웃)
 [completeWork] L1091  29 case   올라오며 마무리한다
 [에러와 Suspense] UnwindWork L66  되감으며 pop 한다

 넷이 짝을 이뤄야 스택이 어긋나지 않는다
```

## 읽는 순서

```text
 처음이면
   [마운트] -> [스케줄링] -> [렌더 루프]
   한 번의 렌더가 어떻게 시작되고 도는지가 보인다

 컴포넌트가 어떻게 그려지는지 알고 싶으면
   [beginWork] -> [훅] -> [completeWork]

 화면에 어떻게 반영되는지 알고 싶으면
   [커밋] -> [패시브 이펙트]

 "왜 이것이 먼저 도는가" 가 궁금하면
   [lane 우선순위]

 Suspense 나 에러 바운더리가 궁금하면
   [에러와 Suspense]

 key 가 왜 필요한지, 리스트를 어떻게 diff 하는지 궁금하면
   [자식 조정]

 useContext 가 값이 바뀐 것을 어떻게 아는지 궁금하면
   [컨텍스트 전파]

 setState 가 실제로 언제 상태가 되는지,
 "우선순위가 높으면 먼저 반영되는가" 가 궁금하면
   [업데이트 큐]
```

## 문서의 생김새

```text
 흐름 폴더마다

 README        그 흐름의 전체 그림과 하위 메서드 목록
 NN_이름        메서드 하나 또는 한 덩어리
 spi           그 흐름의 계약 - 상태값, 플래그, 대조표

 메서드 문서는 이 차례다

 상위 링크 -> 한 문장 요약 -> 위치 -> 실제 코드
 -> 동작 흐름(아스키) -> 결과가 쓰이는 곳 -> 다루지 않는 것
```

```text
 아스키 그림의 표기

 +--   직접 호출 (같은 스택에서 이어진다)
 ~~>   태스크나 콜백 경계 (여기서 끊긴다)
 =>    그 갈래를 끝낸다 (return 이나 throw)
 [FLAG:x]    빌드 플래그로 갈리는 자리
 [DEAD]      이 빌드에서 도달할 수 없는 자리

 인용은 소스 주석 원문이고
 그 아래 한국어는 원문이 이유를 말하지 않을 때 내가 붙인 것이다
 그 구분을 문장 안에 밝혀 두었다
```

## 이 지도가 조심한 것

```text
 빌드 플래그
   react-dom 클라이언트 빌드 기준이다.
   플래그로 죽은 갈래는 [DEAD] 로 표시했고,
   빌드마다 달라지는 것(__PROFILE__, __EXPERIMENTAL__,
   React Native 포크)은 그 범위를 밝혔다

 주석과 코드가 어긋나는 자리
   주석이 코드보다 넓게 말하거나, 옛 구현의 흔적인 자리가 있다.
   그런 곳은 코드를 따르고 어긋남을 적어 두었다

 "안 읽은 자리"
   각 문서 끝의 "다루지 않는 것" 은 요약이 아니라
   **내가 열어보지 않았다는 표시**다
```

## 다루지 않는 것

서버 렌더링(`react-server`, `ReactFizzServer`), 서버 컴포넌트와 Flight, 수화(hydration)의 전체 경로, `Scheduler` 패키지 내부, 이벤트 시스템(`react-dom-bindings` 의 합성 이벤트), `react-reconciler` 의 다른 호스트 설정(React Native, Test Renderer, Noop), DevTools 연동, 컴파일러(`react-compiler`), `react-art` 같은 다른 렌더러는 이 지도의 범위 밖이다.
