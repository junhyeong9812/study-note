# 훅 리스트

상위: [훅 흐름](../README.md)

훅에는 이름이 없다. **순서로만 짝지어진다.** 연결 리스트를 앞에서부터 나란히 훑는 것이 전부다.

## 위치

마운트 `packages/react-reconciler` / `src` / `ReactFiberHooks.js` L979-L998 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L979-L998))

갱신 `packages/react-reconciler` / `src` / `ReactFiberHooks.js` L1000-L1069 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L1000-L1069))

## 실제 코드

마운트는 만들어 붙인다.

```js
// ReactFiberHooks.js L979-L998
function mountWorkInProgressHook(): Hook {
  const hook: Hook = {
    memoizedState: null,

    baseState: null,
    baseQueue: null,
    queue: null,

    next: null,
  };

  if (workInProgressHook === null) {
    // This is the first hook in the list
    currentlyRenderingFiber.memoizedState = workInProgressHook = hook;
  } else {
    // Append to the end of the list
    workInProgressHook = workInProgressHook.next = hook;
  }
  return workInProgressHook;
}
```

갱신은 이전 리스트를 따라가며 복제하거나 재사용한다. 짝이 없으면 던진다.

```js
// ReactFiberHooks.js L1033-L1046
    if (nextCurrentHook === null) {
      const currentFiber = currentlyRenderingFiber.alternate;
      if (currentFiber === null) {
        // This is the initial render. This branch is reached when the component
        // suspends, resumes, then renders an additional hook.
        // Should never be reached because we should switch to the mount dispatcher first.
        throw new Error(
          'Update hook called on initial render. This is likely a bug in React. Please file an issue.',
        );
      } else {
        // This is an update. We should always have a current hook.
        throw new Error('Rendered more hooks than during the previous render.');
      }
    }
```

그리고 모자란 쪽은 렌더가 끝난 뒤에 잡는다.

```js
// ReactFiberHooks.js L658-L661
  // This check uses currentHook so that it works the same in DEV and prod bundles.
  // hookTypesDev could catch more cases (e.g. context) but only in DEV bundles.
  const didRenderTooFewHooks =
    currentHook !== null && currentHook.next !== null;
```

> This check uses `currentHook` so that it works the same in DEV and prod bundles. `hookTypesDev` could catch more cases (e.g. context) but **only** in DEV bundles.

## 동작 흐름

```text
 mountWorkInProgressHook  L979

 L980  hook = { memoizedState, baseState, baseQueue, queue, next }
 L990  workInProgressHook === null 이면 (첫 훅)
 L992    currentlyRenderingFiber.memoizedState = workInProgressHook = hook
 L993  아니면
 L995    workInProgressHook = workInProgressHook.next = hook
 L997  => return workInProgressHook
```

```text
 updateWorkInProgressHook  L1000

 --- 이전 트리에서 다음 훅을 찾는다 ---
 L1006  currentHook === null 이면 (첫 훅)
 L1008    alternate 가 있으면 nextCurrentHook = alternate.memoizedState
 L1011    아니면 null
 L1013  아니면 nextCurrentHook = currentHook.next

 --- 지금 트리에서 다음 훅을 찾는다 ---
 L1018  workInProgressHook === null 이면
 L1019    nextWorkInProgressHook = currentlyRenderingFiber.memoizedState
 L1021  아니면 nextWorkInProgressHook = workInProgressHook.next

 L1024  nextWorkInProgressHook 이 있으면 (재사용)
 L1026    workInProgressHook = nextWorkInProgressHook
 L1029    currentHook = nextCurrentHook
           ★ 여기서는 nextCurrentHook 이 null 이어도 던지지 않는다

 L1030  아니면 (복제)
 L1033    nextCurrentHook 이 null 이면 (짝이 없다)
 L1035      alternate 가 null 이면
 L1039        => throw 'Update hook called on initial render. ...'
 L1042      아니면
 L1044        => throw 'Rendered more hooks than during the previous render.'
 L1048    currentHook = nextCurrentHook
 L1050    newHook = { ...복사, next: null }
 L1060    workInProgressHook === null 이면
 L1062      currentlyRenderingFiber.memoizedState = workInProgressHook = newHook
 L1063    아니면
 L1065      workInProgressHook = workInProgressHook.next = newHook
 L1068  => return workInProgressHook
```

```text
 훅 객체의 다섯 칸

 memoizedState   이번에 렌더된 값
 baseState       baseQueue 의 첫 갱신을 적용하기 직전의 상태
 baseQueue       우선순위가 모자라 건너뛴 갱신부터 그 뒤 전부
 queue           dispatch 와 대기 중인 갱신 (current 와 **공유**한다)
 next            다음 훅

 memoizedState 가 두 군데 뜻이 다르다
   fiber.memoizedState   훅 리스트의 머리
   hook.memoizedState    그 훅의 값
```

```text
 두 throw 의 조건

 공통 전제
   nextWorkInProgressHook === null    재사용할 훅이 없고
   AND nextCurrentHook === null       복제할 훅도 없다

 L1039  거기에 alternate === null
        주석 L1036-1038 이 말한다
          "This is the initial render. This branch is reached when the
           component suspends, resumes, then renders an additional hook.
           **Should never be reached** because we should switch to the
           mount dispatcher first."
        => 도달하면 안 되는 방어선이다

 L1044  거기에 alternate !== null
        주석 L1043 "This is an update. We should always have a current hook."
        => 갱신인데 이전 리스트가 먼저 바닥났다. 훅이 늘었다는 뜻이다
```

```text
 ★ 모자란 쪽은 검사에 구멍이 있다

 finishRenderingHooks L660-661
   didRenderTooFewHooks = currentHook !== null && currentHook.next !== null

 currentHook 은 **이번 렌더에서 마지막으로 소비한 이전 훅**이다
 L1029 와 L1048 에서만 전진한다

 그래서 훅을 하나도 부르지 않으면 currentHook 이 null 로 남고
 첫 항이 거짓이라 검사가 통과한다

   function C({ready}) {
     if (!ready) return null;      // 훅 전에 반환
     const [x] = useState(0);
     ...
   }

 ready 가 false 인 렌더는
   - L526 이 memoizedState 를 null 로 지우고
   - 훅을 안 불러 리스트가 비고
   - L660 검사를 통과해 던지지 않고
   - 그대로 커밋된다

 다음 렌더에서 ready 가 true 가 되면
   L561 의 current.memoizedState === null 이 참이라
   **마운트 디스패처가 골라지고 useState 가 0 부터 다시 시작한다**

 주석 L658-659 가 왜 이 조건을 골랐는지는 적지만
 (DEV 와 운영이 같게 동작하도록 currentHook 을 쓴다)
 이 구멍은 언급하지 않는다
 (내가 조건식을 보고 판단한 것이다)
```

```text
 마운트와 갱신의 비대칭

 마운트  훅 객체를 새로 만들어 이어 붙인다. 짝 검사가 없다
 갱신    이전 리스트와 나란히 가며 짝을 확인한다

 그래서 "훅은 조건부로 부르면 안 된다" 가
 마운트 렌더에서는 아무 일도 일으키지 않고
 그 다음 갱신 렌더에서 터진다
```

## 결과가 쓰이는 곳

```text
 fiber.memoizedState
      --> 리스트의 머리
      --> 다음 렌더가 마운트/갱신을 이것으로 판정한다 (L561)

 hook.queue
      --> current 훅과 **같은 객체**를 공유한다
      --> dispatchSetState 가 여기에 갱신을 넣는다

 hook.baseQueue / baseState
      --> 이번 렌더 우선순위로 처리 못 한 갱신이 남는다
      --> 다음 렌더의 updateReducerImpl 이 이어서 처리한다

 currentHook / workInProgressHook
      --> 리스트를 훑는 두 커서
      --> [02]가 매 바퀴 null 로 되돌린다
```

## 다루지 않는 것

`updateReducerImpl`(L1303)이 `baseQueue` 를 재베이스하는 규칙과 건너뛴 lane 처리, `mountStateImpl`(L1896)이 `queue` 를 만드는 과정, optimistic / gesture 갱신 갈래, `use` 가 훅 리스트 대신 `thenableIndexCounter` 를 쓰는 이유([spi](../spi/README.md)에 있다), DEV 의 `hookTypesDev` 순서 검사, `bailoutHooks`(L904)는 같은 뼈대의 곁가지라 요약만 했다.
