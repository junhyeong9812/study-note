# ref

상위: [커밋 이펙트](../README.md)

`ref` 를 붙이고 뗀다. **함수 ref 의 반환값이 cleanup 이 된다**는 것이 이 두 함수의 축이다.

## 위치

붙이기 `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L757-L824 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L757-L824))

떼기 `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L842-L908 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L842-L908))

## 실제 코드

무엇을 넘길지 tag 로 고른다.

```js
// ReactFiberCommitEffects.js L761-L793
    switch (finishedWork.tag) {
      case HostHoistable:
      case HostSingleton:
      case HostComponent:
        instanceToUse = getPublicInstance(finishedWork.stateNode);
        break;
      case ViewTransitionComponent: {
        if (enableViewTransition) {
          const instance: ViewTransitionState = finishedWork.stateNode;
          const props: ViewTransitionProps = finishedWork.memoizedProps;
          const name = getViewTransitionName(props, instance);
          if (instance.ref === null || instance.ref.name !== name) {
            instance.ref = createViewTransitionInstance(name);
          }
          instanceToUse = instance.ref;
          break;
        }
        instanceToUse = finishedWork.stateNode;
        break;
      }
      case Fragment:
        if (enableFragmentRefs) {
          const instance: null | FragmentInstanceType = finishedWork.stateNode;
          if (instance === null) {
            finishedWork.stateNode = createFragmentInstance(finishedWork);
          }
          instanceToUse = finishedWork.stateNode;
          break;
        }
      // Fallthrough
      default:
        instanceToUse = finishedWork.stateNode;
    }
```

함수면 반환값을 cleanup 으로 받고, 객체면 `.current` 에 넣는다.

```js
// ReactFiberCommitEffects.js L794-L822
    if (typeof ref === 'function') {
      if (shouldProfile(finishedWork)) {
        try {
          startEffectTimer();
          finishedWork.refCleanup = ref(instanceToUse);
        } finally {
          recordEffectDuration(finishedWork);
        }
      } else {
        finishedWork.refCleanup = ref(instanceToUse);
      }
    } else {
      if (__DEV__) {
        // TODO: We should move these warnings to happen during the render
        // phase (markRef).
        if (typeof ref === 'string') {
          console.error('String refs are no longer supported.');
        } else if (!ref.hasOwnProperty('current')) {
          console.error(
            'Unexpected ref object provided for %s. ' +
              'Use either a ref-setter function or React.createRef().',
            getComponentNameFromFiber(finishedWork),
          );
        }
      }

      // $FlowFixMe[incompatible-use] unable to narrow type to the non-function case
      ref.current = instanceToUse;
    }
```

뗄 때는 갈래가 셋이다.

```js
// ReactFiberCommitEffects.js L849-L907
  if (ref !== null) {
    if (typeof refCleanup === 'function') {
      try {
        if (shouldProfile(current)) {
          try {
            startEffectTimer();
            if (__DEV__) {
              runWithFiberInDEV(current, refCleanup);
            } else {
              refCleanup();
            }
          } finally {
            recordEffectDuration(current);
          }
        } else {
          if (__DEV__) {
            runWithFiberInDEV(current, refCleanup);
          } else {
            refCleanup();
          }
        }
      } catch (error) {
        captureCommitPhaseError(current, nearestMountedAncestor, error);
      } finally {
        // `refCleanup` has been called. Nullify all references to it to prevent double invocation.
        current.refCleanup = null;
        const finishedWork = current.alternate;
        if (finishedWork != null) {
          finishedWork.refCleanup = null;
        }
      }
    } else if (typeof ref === 'function') {
      try {
        if (shouldProfile(current)) {
          try {
            startEffectTimer();
            if (__DEV__) {
              runWithFiberInDEV(current, ref, null) as void;
            } else {
              ref(null);
            }
          } finally {
            recordEffectDuration(current);
          }
        } else {
          if (__DEV__) {
            runWithFiberInDEV(current, ref, null) as void;
          } else {
            ref(null);
          }
        }
      } catch (error) {
        captureCommitPhaseError(current, nearestMountedAncestor, error);
      }
    } else {
      // $FlowFixMe[incompatible-use] unable to narrow type to RefObject
      ref.current = null;
    }
  }
```

> `refCleanup` has been called. Nullify all references to it to prevent double invocation.

## 동작 흐름

```text
 commitAttachRef  L757-824

 L758  ref = finishedWork.ref
 L759  ref !== null 이면
 L761    switch (finishedWork.tag) 로 instanceToUse 를 고른다
 L762      HostHoistable / HostSingleton / HostComponent
 L765        getPublicInstance(finishedWork.stateNode)
 L767      ViewTransitionComponent   [FLAG:enableViewTransition=true]
 L771        name 이 바뀌었으면 L773 새 인스턴스를 만든다
 L775        instanceToUse = instance.ref
 L781      Fragment                  [FLAG:enableFragmentRefs=true]
 L784        stateNode 가 null 이면 L785 createFragmentInstance
 L787        instanceToUse = finishedWork.stateNode
 L788        break
 L790      // Fallthrough                ** 플래그가 켜져 있어 도달 불가 **
 L791      default
 L792        instanceToUse = finishedWork.stateNode

 L794    typeof ref === 'function' 이면
 L795      shouldProfile 이면 try/finally 로 감싸고
 L798        finishedWork.refCleanup = ref(instanceToUse)  ★ 반환값이 cleanup 이다
 L800        recordEffectDuration(finishedWork)   (finally)
 L802      아니면
 L803        finishedWork.refCleanup = ref(instanceToUse)
 L805    아니면
 L806      [__DEV__]
 L809        typeof ref === 'string' 이면
 L810          console.error('String refs are no longer supported.')
 L811        아니면 ref.hasOwnProperty('current') 가 아니면
 L812          console.error('Unexpected ref object provided for %s. ...')
 L821      ref.current = instanceToUse
```

```text
 ★ Fragment 의 fallthrough 는 이 빌드에서 도달 불가다

 L782  if (enableFragmentRefs) {   <- 기본 포크에서 true 다
 L788    break;                     ** 여기서 끊긴다 **
 L789  }
 L790  // Fallthrough
 L791  default:

 플래그가 켜져 있으면 L788 에서 break 하므로 default 로 흘러가지 않는다.
 이 fallthrough 는 **플래그가 꺼진 빌드를 위한 대비**다

 ★ [업데이트 큐]의 CaptureUpdate fallthrough 와 종류가 다르다.
   그쪽은 언제나 흘러가고, 이쪽은 플래그가 꺼져야 흘러간다
```

```text
 ★★ 함수 ref 의 반환값이 cleanup 이다

 L798  finishedWork.refCleanup = ref(instanceToUse)

 그래서 떼는 쪽이 refCleanup 을 **먼저** 본다 (L850).
 있으면 그것을 부르고, 없으면 ref(null) 로 부른다

 => 함수 ref 에 cleanup 을 돌려주면 React 가 null 로 다시 부르지 않는다
    (이 귀결은 내가 두 갈래를 맞춰 보고 적은 것이고 주석에 없다)
```

```text
 safelyDetachRef  L842-908 — 갈래 셋

 L846  ref = current.ref
 L847  refCleanup = current.refCleanup
 L849  ref !== null 이면

 L850    typeof refCleanup === 'function' 이면        --- (가)
 L852      shouldProfile 이면 타이머로 감싸고
 L858        refCleanup()
 L870      catch -> captureCommitPhaseError
 L872      finally
 L874        current.refCleanup = null
 L875        finishedWork = current.alternate
 L876        finishedWork != null 이면
 L877          finishedWork.refCleanup = null

 L880    아니면 typeof ref === 'function' 이면        --- (나)
 L888      ref(null)
 L900      catch -> captureCommitPhaseError

 L903    아니면                                        --- (다)
 L905      ref.current = null
```

```text
 ★ 갈래 셋의 예외 처리가 다르다

 (가)  try / catch / finally      cleanup 을 부른다
 (나)  try / catch                ref(null) 을 부른다
 (다)  아무 것도 없다              대입뿐이라 던질 수 없다
       (마지막 문장은 내 판단이고 주석에 없다)

 ★ (가)만 finally 를 갖는다. 던져도 refCleanup 을 반드시 지우기 위해서다
   주석 L873 - "`refCleanup` has been called. Nullify all references to it
                to prevent double invocation."

 ★★ 그래서 지우는 일이 (가)에서만 일어난다.
   (나)는 catch 만 있고 아무 것도 안 지운다
   그리고 **어느 갈래도 current.ref 는 안 지운다**. refCleanup 만 지운다
```

```text
 ★ 첫째 갈래에서는 양쪽 fiber 의 refCleanup 을 다 지운다  L874 / L877

 current 와 그 alternate 둘 다다.
 [컨텍스트 전파]가 lanes 를 양쪽 alternate 에 칠한 것과 같은 사정이다 -
 다음 렌더가 어느 트리로 가든 같은 값을 봐야 한다
 (이 대비는 내가 붙인 것이다)
```

```text
 ★ 붙이기와 떼기의 감싸는 방식이 다르다

 붙이기  safelyAttachRef L827-840
         try 하나가 commitAttachRef 전체를 감싼다
         주석 L826 - "Capture errors so they don't interrupt mounting."

 떼기    safelyDetachRef L842-908
         함수 자체에 바깥 try 가 없다. **갈래마다** 잡는다

 => 붙이기는 한 번에 하나이고, 떼기는 갈래가 셋이라 그렇게 갈린 것으로 보인다
    (내 판단이다)
```

## 결과가 쓰이는 곳

```text
 ref.current / 함수 ref 의 인자
      --> 사용자가 보는 DOM 노드나 인스턴스
      --> tag 에 따라 getPublicInstance 를 거치기도 한다

 finishedWork.refCleanup
      --> 다음에 뗄 때 쓴다
      --> 첫째 갈래에서 부르고 나면 양쪽 fiber 에서 지운다

 captureCommitPhaseError
      --> ref 콜백의 예외를 경계로 보낸다
      --> 커밋을 멈추지 않는다
```

## 다루지 않는 것

`markRef`(`ReactFiberBeginWork`)가 렌더 단계에서 `Ref` 플래그를 세우는 규칙, `getPublicInstance`(호스트 설정)가 DOM 노드를 고르는 방식, `createFragmentInstance` / `FragmentInstanceType`(`enableFragmentRefs` 계열)과 `createViewTransitionInstance` / `getViewTransitionName`(`enableViewTransition`)의 본문, `refCleanup` 을 처음 도입한 배경, ref 를 떼고 붙이는 순서를 커밋 순회가 정하는 자리([커밋](../../commit/README.md)에 있다), 문자열 ref 가 제거된 경위는 같은 뼈대의 곁가지라 요약만 했다.
