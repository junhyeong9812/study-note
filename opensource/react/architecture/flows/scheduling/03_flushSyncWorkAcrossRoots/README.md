# flushSyncWorkAcrossRoots

상위: [스케줄링](../README.md)

**동기 작업을 그 자리에서 렌더한다.** 마이크로태스크 끝에서 불리지만 이 함수 전용은 아니다 — `flushSync()` 류 API 도 여기로 들어온다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L185-L247 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L185-L247))

## 실제 코드

들어오는 문이 둘이다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L171-L183 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L171-L183))

```js
// ReactFiberRootScheduler.js L171-L183
export function flushSyncWorkOnAllRoots() {
  // This is allowed to be called synchronously, but the caller should check
  // the execution context first.
  flushSyncWorkAcrossRoots_impl(NoLanes, false);
}

export function flushSyncWorkOnLegacyRootsOnly() {
  // This is allowed to be called synchronously, but the caller should check
  // the execution context first.
  if (!disableLegacyMode) {
    flushSyncWorkAcrossRoots_impl(NoLanes, true);
  }
}
```

> This is allowed to be called synchronously, but the caller should check the execution context first.

가드가 둘이다.

```js
// ReactFiberRootScheduler.js L189-L199
  if (isFlushingWork) {
    // Prevent reentrancy.
    // TODO: Is this overly defensive? The callers must check the execution
    // context first regardless.
    return;
  }

  if (!mightHavePendingSyncWork) {
    // Fast path. There's no sync work to do.
    return;
  }
```

루트마다 sync 인지 보고 그 자리에서 돌린다.

```js
// ReactFiberRootScheduler.js L232-L240
          if (
            (includesSyncLane(nextLanes) ||
              (enableGestureTransition && isGestureRender(nextLanes))) &&
            !checkIfRootIsPrerendering(root, nextLanes)
          ) {
            // This root has pending sync work. Flush it now.
            didPerformSomeWork = true;
            performSyncWorkOnRoot(root, nextLanes);
          }
```

그리고 실제로 렌더하는 것은 이쪽이다.

`packages/react-reconciler` / `src` / `ReactFiberRootScheduler.js` L608-L622 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRootScheduler.js#L608-L622))

```js
// ReactFiberRootScheduler.js L608-L622
function performSyncWorkOnRoot(root: FiberRoot, lanes: Lanes) {
  // This is the entry point for synchronous tasks that don't go
  // through Scheduler.
  const didFlushPassiveEffects = flushPendingEffects();
  if (didFlushPassiveEffects) {
    // If passive effects were flushed, exit to the outer work loop in the root
    // scheduler, so we can recompute the priority.
    return null;
  }
  if (enableProfilerTimer && enableProfilerNestedUpdatePhase) {
    syncNestedUpdateFlag();
  }
  const forceSync = true;
  performWorkOnRoot(root, lanes, forceSync);
}
```

## 동작 흐름

```text
 L189  isFlushingWork 면 => return            재진입 가드
       주석 L190: "Prevent reentrancy."
 L196  mightHavePendingSyncWork 가 아니면 => return
       주석 L197: "Fast path. There's no sync work to do."
 L203  isFlushingWork = true
 L204  do {
 L205    didPerformSomeWork = false
 L207    리스트를 훑는다
           L208  onlyLegacy 인데 legacy 루트가 아니면 건너뛴다
           L211  syncTransitionLanes 가 있으면
           L212    getNextLanesToFlushSync 로 구해
           L216    있으면 performSyncWorkOnRoot
           L218  아니면
           L225    getNextLanes 로 구해
           L232    sync lane 이거나 gesture 이고 prerendering 이 아니면
           L239    performSyncWorkOnRoot
 L245  } while (didPerformSomeWork)
 L246  isFlushingWork = false

 [performSyncWorkOnRoot]  L608
 L611  flushPendingEffects()
 L612  패시브가 돌았으면 => return null
       주석 L613-614: 바깥 루프로 나가 우선순위를 다시 계산한다
 L617  [enableProfilerTimer && enableProfilerNestedUpdatePhase] syncNestedUpdateFlag()
 L620  forceSync = true
 L621  performWorkOnRoot(root, lanes, forceSync)     <- 흐름 3
```

```text
 L611 의 flushPendingEffects 는 단순 flush 가 아니다

 그 함수의 **첫 문장**이 플래그 가드다 (WorkLoop L4645)
   if (enableViewTransition && pendingViewTransition !== null) {
     stopViewTransition(pendingViewTransition);
     ...
   }

 enableViewTransition 은 기본값이 true 다
 즉 진행 중인 View Transition 을 **중단**시킬 수 있는 자리다

 호출부 L611 에는 플래그가 없다. 함수 안에 있다
 (그래서 [01] L339 가 hasPendingCommitEffects 로 미리 막는 것이다)


 가드 둘의 역할이 다르다

 L189  isFlushingWork              재진입 방지
       렌더 중에 이 함수가 다시 불리는 것을 막는다

 L196  mightHavePendingSyncWork     빠른 탈출
       할 일이 없을 때 리스트 순회 자체를 건너뛴다

 주석이 각각 그렇게 적는다 (L190, L197)
 둘 다 return 이지만 막는 것이 다르다
```

```text
 do-while 인 이유

 L245  } while (didPerformSomeWork);

 소스가 적어 둔 이유는 패시브 이펙트다
 performSyncWorkOnRoot 주석 L613-614
   "If passive effects were flushed, exit to the outer work loop in the root
    scheduler, so we can recompute the priority."

 그리고 렌더 중 새 sync 갱신이 생길 수도 있다
 (뒷문장은 주석에 없다. ensureRootIsScheduled 가 리스트에 다시 넣는 것을 보고
  내가 붙인 것이다)

 L205 가 매 바퀴 false 로 초기화하는데
 L215 / L238 은 performSyncWorkOnRoot **호출 전**에 true 로 만든다
 => 렌더가 한 줄도 안 돌아도 루프가 한 번 더 돈다
    (L612 에서 바로 돌아오는 경우)
```

```text
 마이크로태스크 안에서 렌더가 돈다

 [01] L340 -> 이 함수 -> L216/L239 performSyncWorkOnRoot
   -> L621 performWorkOnRoot -> 렌더 루프

 중간에 콜백 예약이 없다. 전부 같은 스택이다

 [01] 의 주석이 그것을 전제로 말한다 (L334-335)
   "This has to come at the end, because it does actual rendering work
    that might throw."
```

```text
 들어오는 문이 마이크로태스크만이 아니다

 flushSyncWorkOnAllRoots (L171)
   WorkLoop 에서 다섯 자리가 부른다 (L1813, L1922, L1931, L4382, L4799)
   그리고 DOM 호스트 설정이 flushSyncWork 라는 이름으로 한 자리 (L4891)
   => flushSync() 류 API 가 이 경로다

 flushSyncWorkOnLegacyRootsOnly (L177)
   L180 에 !disableLegacyMode 가드가 있다
   react-dom 은 그 값이 true 라 **함수 전체가 no-op** 이다

 (grep 범위: packages 전체 *.js, __tests__ 제외)
```

```text
 두 진입의 주석이 정반대다

 flushSyncWorkOnAllRoots L172-173
   "This is allowed to be called synchronously, but the caller should check
    the execution context first."

 processRootScheduleInMicrotask L260-261
   "It should never be called synchronously."

 같은 파일인데 규약이 다르다
 앞엣것은 호출자가 실행 문맥을 확인할 책임을 진다
```

```text
 onlyLegacy 갈래는 이 빌드에서 안 온다

 L208  if (onlyLegacy && (disableLegacyMode || root.tag !== LegacyRoot))

 onlyLegacy 를 true 로 넘기는 유일한 자리가 L181 인데
 그 위 L180 가드 때문에 react-dom 에서는 거기 도달하지 않는다
```

## 결과가 쓰이는 곳

```text
 performWorkOnRoot 호출
      --> 렌더 루프가 시작된다
      --> forceSync = true 라 동기로 끝까지 돈다

 isFlushingWork
      --> 렌더 중 이 함수가 다시 불려도 즉시 돌아간다

 반환값 없음
      --> 호출자는 결과를 안 본다
      --> [01] 은 이 호출 뒤 인디케이터 루프로 넘어간다
```

## 다루지 않는 것

`getNextLanesToFlushSync` 와 `getNextLanes` 의 lane 계산, `checkIfRootIsPrerendering` 의 판정, `isGestureRender` 와 gesture transition, `flushPendingEffects` 의 패시브 이펙트 처리, `performWorkOnRoot` 이후의 렌더 루프, `flushSyncWorkOnAllRoots` 를 부르는 WorkLoop 쪽 사정은 같은 뼈대의 곁가지라 요약만 했다.
