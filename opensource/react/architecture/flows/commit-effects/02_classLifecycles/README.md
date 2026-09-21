# 클래스 생명주기

상위: [커밋 이펙트](../README.md)

커밋 단계의 클래스 생명주기 일곱 함수. **before-mutation 패스와 layout 패스를 잇는 것이 인스턴스의 밑줄 두 개짜리 칸 하나**다.

## 위치

layout `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L340-L495 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L340-L495))

snapshot `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L635-L707 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L635-L707))

언마운트 `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L710-L755 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L710-L755))

## 실제 코드

스냅샷을 인스턴스에 얹는다.

```js
// ReactFiberCommitEffects.js L670-L706
  try {
    const resolvedPrevProps = resolveClassComponentProps(
      finishedWork.type,
      prevProps,
    );
    let snapshot;
    if (__DEV__) {
      snapshot = runWithFiberInDEV(
        finishedWork,
        callGetSnapshotBeforeUpdates,
        instance,
        resolvedPrevProps,
        prevState,
      );
      const didWarnSet =
        didWarnAboutUndefinedSnapshotBeforeUpdate as any as Set<mixed>;
      if (snapshot === undefined && !didWarnSet.has(finishedWork.type)) {
        didWarnSet.add(finishedWork.type);
        runWithFiberInDEV(finishedWork, () => {
          console.error(
            '%s.getSnapshotBeforeUpdate(): A snapshot value (or null) ' +
              'must be returned. You have returned undefined.',
            getComponentNameFromFiber(finishedWork),
          );
        });
      }
    } else {
      snapshot = callGetSnapshotBeforeUpdates(
        instance,
        resolvedPrevProps,
        prevState,
      );
    }
    instance.__reactInternalSnapshotBeforeUpdate = snapshot;
  } catch (error) {
    captureCommitPhaseError(finishedWork, finishedWork.return, error);
  }
```

언마운트만 인스턴스를 덮어쓴다.

```js
// ReactFiberCommitEffects.js L710-L755
export function safelyCallComponentWillUnmount(
  current: Fiber,
  nearestMountedAncestor: Fiber | null,
  instance: any,
) {
  instance.props = resolveClassComponentProps(
    current.type,
    current.memoizedProps,
  );
  instance.state = current.memoizedState;
  if (shouldProfile(current)) {
    startEffectTimer();
    if (__DEV__) {
      runWithFiberInDEV(
        current,
        callComponentWillUnmountInDEV,
        current,
        nearestMountedAncestor,
        instance,
      );
    } else {
      try {
        instance.componentWillUnmount();
      } catch (error) {
        captureCommitPhaseError(current, nearestMountedAncestor, error);
      }
    }
    recordEffectDuration(current);
  } else {
    if (__DEV__) {
      runWithFiberInDEV(
        current,
        callComponentWillUnmountInDEV,
        current,
        nearestMountedAncestor,
        instance,
      );
    } else {
      try {
        instance.componentWillUnmount();
      } catch (error) {
        captureCommitPhaseError(current, nearestMountedAncestor, error);
      }
    }
  }
}
```

> Capture errors so they don't interrupt unmounting.

그리고 같은 모양의 DEV 검사가 네 자리에 있다. 이것은 그중 넷째다.

```js
// ReactFiberCommitEffects.js L526-L551
      if (
        !finishedWork.type.defaultProps &&
        !('ref' in finishedWork.memoizedProps) &&
        !didWarnAboutReassigningProps
      ) {
        if (instance.props !== finishedWork.memoizedProps) {
          console.error(
            'Expected %s props to match memoized props before ' +
              'processing the update queue. ' +
              'This might either be because of a bug in React, or because ' +
              'a component reassigns its own `this.props`. ' +
              'Please file an issue.',
            getComponentNameFromFiber(finishedWork) || 'instance',
          );
        }
        if (instance.state !== finishedWork.memoizedState) {
          console.error(
            'Expected %s state to match memoized state before ' +
              'processing the update queue. ' +
              'This might either be because of a bug in React, or because ' +
              'a component reassigns its own `this.state`. ' +
              'Please file an issue.',
            getComponentNameFromFiber(finishedWork) || 'instance',
          );
        }
      }
```

## 동작 흐름

```text
 commitClassLayoutLifecycles  L340-495 — current 로 갈린다

 L344  instance = finishedWork.stateNode
 L345  current === null 이면                     --- 마운트
 L349    [__DEV__] props/state 일치 검사 (L350-375)
 L377    shouldProfile 이면
 L378      startEffectTimer()
 L380      [__DEV__] runWithFiberInDEV(..., callComponentDidMountInDEV, ...)
 L388      아니면 instance.componentDidMount()
 L393      recordEffectDuration(finishedWork)
 L394    아니면
 L396      [__DEV__] runWithFiberInDEV(...)
 L404      아니면 instance.componentDidMount()
        ★ 같은 호출이 **넷**이다 - shouldProfile x __DEV__ 의 곱이다

 L410  아니면                                     --- 업데이트
 L411    prevProps = resolveClassComponentProps(finishedWork.type,
                                                current.memoizedProps)
 L415    prevState = current.memoizedState
 L419    [__DEV__] 같은 검사 (문구만 componentDidUpdate)
 L447    shouldProfile 이면 타이머로 감싸고
 L461      instance.componentDidUpdate(prevProps, prevState,
                                       instance.__reactInternalSnapshotBeforeUpdate)
 L471    아니면
 L484      같은 호출이 한 번 더 (여기도 곱이라 넷이다)
```

```text
 ★★ 패스 둘을 잇는 것이 칸 하나다

 before-mutation 패스
   L703  instance.__reactInternalSnapshotBeforeUpdate = snapshot

 layout 패스
   L457 / L464 / L480 / L487  그 값을 읽어 셋째 인자로 넘긴다

 => getSnapshotBeforeUpdate 의 반환값이 componentDidUpdate 에 닿는 길이
    **인스턴스에 얹힌 밑줄 두 개짜리 속성** 하나다
 => 그래서 두 생명주기가 서로 다른 커밋 패스에 있어도 짝이 맞는다
```

```text
 ★★ 같은 모양의 DEV 검사가 네 자리, 여덟 번이다

 자리마다 가드가 같고
   finishedWork.type.defaultProps 가 없고
   memoizedProps 에 'ref' 가 없고
   didWarnAboutReassigningProps 가 아직 안 켜졌을 때만 본다

 자리마다 console.error 가 **둘**이다 - props 하나, state 하나

   L351-353 가드  L355 props / L365 state   before componentDidMount
   L421-423 가드  L425 props / L435 state   before componentDidUpdate
   L527-529 가드  L531 props / L541 state   ★ before **processing the update queue**
   L644-646 가드  L648 props / L658 state   before getSnapshotBeforeUpdate

 ★ 셋째만 생명주기 이름이 아니다 (L534, L544).
   setState 의 콜백을 부르기 전에도 같은 검사를 한다

 문구는 넷이 같다
   "Expected %s props to match memoized props before X.
    This might either be because of a bug in React, or because a component
    reassigns its own `this.props`. Please file an issue."

 ※ defaultProps 와 ref 가 있으면 검사를 건너뛰는 이유는 주석에 없다.
   내 짐작으로는 그때 resolveClassComponentProps 가 새 객체를 만들어
   === 비교가 깨지기 때문이다 ([클래스 컴포넌트 02]에 그 함수가 있다)
```

```text
 ★★ 인스턴스를 덮어쓰는 곳은 언마운트 하나뿐이다

 나머지 셋은 인자로만 넘기고 인스턴스를 안 건드린다.
 그 방침을 같은 주석이 **네 번** 말한다 (L346-348 / L416-418 / L553-555 / L639-641)
   "We could update instance props and state here, but instead we rely on
    them being set during last render.
    TODO: revisit this when we implement resuming."

 그런데 safelyCallComponentWillUnmount 만 다르다 - L715-719
   instance.props = resolveClassComponentProps(current.type,
                                               current.memoizedProps)
   instance.state = current.memoizedState

 ※ 왜 언마운트만 다른지는 주석에 없다
```

```text
 commitClassSnapshot  L635-707

 L636  prevProps = current.memoizedProps          (해소 전)
 L637  prevState = current.memoizedState
 L642  [__DEV__] props/state 일치 검사
 L670  try {
 L671    resolvedPrevProps = resolveClassComponentProps(finishedWork.type,
                                                        prevProps)
 L676    [__DEV__]
 L677      snapshot = runWithFiberInDEV(finishedWork, callGetSnapshotBeforeUpdates,
                                        instance, resolvedPrevProps, prevState)
            ★ DEV 호출과 프로덕션 호출이 따로다 (L677 / L697)
 L686      snapshot === undefined 이고 아직 경고 안 했으면
 L689        console.error('%s.getSnapshotBeforeUpdate(): A snapshot value
                            (or null) must be returned. You have returned
                            undefined.')
 L696    아니면
 L697      snapshot = callGetSnapshotBeforeUpdates(instance, resolvedPrevProps,
                                                   prevState)
 L703    instance.__reactInternalSnapshotBeforeUpdate = snapshot
 L704  } catch (error) {
 L705    captureCommitPhaseError(finishedWork, finishedWork.return, error)

 ★ try 가 L670 부터라 DEV 경고도 그 안이다
 ★ undefined 경고는 **타입당 한 번**이다 (Set 선언이 L622-625 에 있다)
 ★ prevProps 는 해소 전 것을 쓰고, 넘길 때만 해소한다 (L636 vs L671)
```

```text
 ★ commitClassDidMount 는 layout 쪽의 축소판이다  L497-516

 L340 의 마운트 갈래와 비교하면 셋이 없다
   (가) `typeof instance.componentDidMount === 'function'` 가드가 **있다** (L500)
        L340 쪽에는 없다 - 부르는 쪽이 이미 걸렀다는 뜻이다
   (나) 프로파일러 타이머가 **없다**
   (다) DEV props/state 검사가 **없다**

 TODO L498 - "Check for LayoutStatic flag"
 호출처 둘 다 **다시 들어가는 길**이다
   CMW L3171  reappearLayoutEffects - 숨겼다 다시 보이게 될 때
   CMW L5318  invokeLayoutEffectMountInDEV - DEV StrictMode 이중 호출

 => 둘 다 그 fiber 를 방금 렌더한 것이 아니다.
    그래서 current 를 안 받고(L497), 마운트/업데이트 문구를 고를 수도 없다
 ※ DEV 검사가 없는 이유는 주석에 없다. 위 문장은 내가 호출처를 보고 낸 추정이다
```

```text
 콜백 셋의 모양이 같다

 commitClassCallbacks        L518   queue.callbacks
 commitClassHiddenCallbacks  L568   queue.shared.hiddenCallbacks
 commitRootCallbacks         L592   HostRoot 용

 셋 다
   updateQueue !== null 이면
     try { [__DEV__] runWithFiberInDEV(...) 아니면 직접 } catch {
       captureCommitPhaseError(...)
     }

 ★ 실제 일은 [업데이트 큐]의 commitCallbacks / commitHiddenCallbacks 가 한다.
   이 파일은 그것을 감싸 try/catch 와 DEV 스택을 붙일 뿐이다

 ★ commitRootCallbacks 만 instance 를 자식에서 찾아 넘긴다 (L598-607)
   root.render(el, cb) 의 cb 가 받는 this 가 그것이다

 주석 L519-520 - "TODO: I think this is now always non-null by the time it
 reaches the commit phase. Consider removing the type check."
```

## 결과가 쓰이는 곳

```text
 instance.__reactInternalSnapshotBeforeUpdate
      --> componentDidUpdate 의 셋째 인자

 instance.props / instance.state (언마운트 경로만)
      --> componentWillUnmount 가 보는 this

 captureCommitPhaseError
      --> 생명주기의 예외를 경계로 올려 보낸다
      --> 커밋을 멈추지 않는다

 queue.callbacks
      --> [업데이트 큐]가 채우고 여기가 비운다
```

## 다루지 않는 것

`commitCallbacks` / `commitHiddenCallbacks`([업데이트 큐 05](../../update-queue/05_capturedAndCallbacks/README.md)에 있다)의 본문, `resolveClassComponentProps`([클래스 컴포넌트 02](../../class-component/02_construct/README.md)에 있다), `callComponentDidMountInDEV` / `callComponentDidUpdateInDEV` / `callComponentWillUnmountInDEV`(`ReactFiberCallUserSpace`)가 감싸는 방식, `didWarnAboutReassigningProps` 를 켜는 곳(`ReactFiberBeginWork` L1689), `shouldProfile`(L89)이 보는 `ProfileMode`([04 프로파일러](../04_profiler/README.md)에 있다), 커밋 순회가 어느 패스에서 이 함수들을 부르는지([커밋](../../commit/README.md)에 있다)는 같은 뼈대의 곁가지라 요약만 했다.
