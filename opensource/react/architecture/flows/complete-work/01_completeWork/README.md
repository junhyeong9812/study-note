# completeWork

상위: [completeWork 흐름](../README.md)

`tag` 에 대한 **세 번째 `switch`** 다. [beginWork](../../begin-work/README.md)에 둘이 있었고, 여기가 셋째다. 레이블은 29개로 같은데 **실행 본문은 19개**다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberCompleteWork.js` L1080-L2095 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCompleteWork.js#L1080-L2095))

## 실제 코드

머리는 네 줄이다.

```js
// ReactFiberCompleteWork.js L1085-L1090
  const newProps = workInProgress.pendingProps;
  // Note: This intentionally doesn't check if we're hydrating because comparing
  // to the current tree provider fiber is just as fast and less error-prone.
  // Ideally we would have a special version of the work loop only
  // for hydration.
  popTreeContext(workInProgress);
```

> Note: This intentionally doesn't check if we're hydrating because comparing to the current tree provider fiber is just as fast and less error-prone. **Ideally we would have a special version of the work loop only for hydration.**

가장 흔한 갈래는 두 줄이다. 아홉 레이블이 이 본문을 함께 쓴다.

```js
// ReactFiberCompleteWork.js L1098-L1108
    case LazyComponent:
    case SimpleMemoComponent:
    case FunctionComponent:
    case ForwardRef:
    case Fragment:
    case Mode:
    case Profiler:
    case ContextConsumer:
    case MemoComponent:
      bubbleProperties(workInProgress);
      return null;
```

마지막 case 와 그 뒤.

```js
// ReactFiberCompleteWork.js L2083-L2088
    case Throw: {
      if (!disableLegacyMode) {
        // Only Legacy Mode completes an errored node.
        return null;
      }
    }
```

> Only Legacy Mode completes an errored node.

```js
// ReactFiberCompleteWork.js L2091-L2094
  throw new Error(
    `Unknown unit of work tag (${workInProgress.tag}). This error is likely caused by a bug in ` +
      'React. Please file an issue.',
  );
```

## 동작 흐름

```text
 L1080  function completeWork(current, workInProgress, renderLanes)

 L1085  newProps = workInProgress.pendingProps
 L1090  popTreeContext(workInProgress)          모든 tag 공통

 L1091  switch (workInProgress.tag) {           case 레이블 29개

          갈래 대부분이 이 모양이다
            pop 무언가
            일 하기 (인스턴스 만들기 / flags 세우기)
            bubbleProperties(workInProgress)
            return null

 L2089  }
 L2091  => **throw** new Error('Unknown unit of work tag (...)')
```

```text
 레이블 29, 실행 본문 19

 beginWork 는 레이블 29 = 본문 29 였다. 여기는 다르다

 (가) 무조건 본문을 공유하는 묶음 둘
      L1098-1106  아홉 레이블 -> 본문 L1107-1108
        LazyComponent / SimpleMemoComponent / FunctionComponent /
        ForwardRef / Fragment / Mode / Profiler /
        ContextConsumer / MemoComponent
        본문은 bubbleProperties 후 return null 두 줄뿐이다

      L1964-1965  OffscreenComponent / LegacyHiddenComponent
        -> 본문 L1966-2047
        다만 LegacyHiddenComponent 레이블은 죽어 있다
        (그 fiber 가 만들어지지 않는다)

 (나) 조건부 fallthrough 체인 하나
      L1198 HostHoistable  -> L1300 HostSingleton -> L1372 HostComponent
      각자 본문이 있는데, 자기 capability 플래그가 참일 때만 return 하고
      거짓이면 다음 case 본문으로 흘러든다
        L1298  // Fall through
        L1370  // Fall through
      react-dom 은 supportsResources / supportsSingletons 둘 다 true 라
      두 fallthrough 가 죽어 있고 세 case 가 독립이다
```

```text
 ★ throw 로 향하는 갈래가 넷이다

 completeWork 에도 default 가 없다.
 switch 를 빠져나오면 L2091 의 throw 에 닿는다

 L1094  IncompleteFunctionComponent
          L1093  if (disableLegacyMode) {
          L1094    break;
          L1096  // Fallthrough        <- 플래그가 true 라 여기 못 온다

 L1696  IncompleteClassComponent
          같은 모양이다
          주석 L1698-1699 가 자리를 설명한다
            "Same as class component case. I put it down here so that
             the tags are sequential to ensure this switch is compiled
             to a jump table."

 L1962  ScopeComponent
          L1942  if (enableScopeAPI) { ... L1960 return null }
          L1962  break;

 L2083  Throw
          L2084  if (!disableLegacyMode) { L2086 return null; }
          L2087  }
          L2088  }        <- break 도 return 도 없다. 그냥 흘러나간다

 셋이 disableLegacyMode 때문이고 하나가 enableScopeAPI 때문이다
 그리고 넷 다 실제로는 닿지 않는다 - [spi](../spi/README.md) 에 정리했다
```

```text
 case Throw 가 beginWork 와 정반대다

 beginWork  L4465  throw workInProgress.pendingProps
            일부러 던지는 제어 흐름이다.
            조정 중에 던져진 것을 begin 단계에서 제자리에 다시 던진다

 completeWork L2083  아무것도 하지 않고 흘러나가 일반 에러에 닿는다
            "있으면 안 되는 일" 로 쓰여 있다

 주석이 조건의 뜻을 말한다 (L2085)
   "Only Legacy Mode completes an errored node."
   => 레거시 모드에서만 에러난 노드가 완료될 수 있었다
      그 모드가 꺼진 지금은 이 case 자체가 도달 불가다
```

```text
 popTreeContext 는 switch 밖에 있다

 L1090  popTreeContext(workInProgress)

 tag 를 가리지 않고 먼저 돈다
 수화 중 id 생성에 쓰는 스택이라 모든 fiber 가 대상이다

 주석이 일부러 확인하지 않는다고 적는다 (L1086-1089)
   수화 중인지 따지는 것보다 그냥 부르는 편이 빠르고 실수가 적다
   그리고 수화 전용 work loop 가 따로 있으면 좋겠다고 덧붙인다
```

## 결과가 쓰이는 곳

```text
 return null
      --> completeUnitOfWork 가 형제나 부모로 올라간다

 return (Fiber)
      --> 그 fiber 를 다시 begin 단계로 보낸다
      --> 다섯 자리가 있다 ([spi](../spi/README.md))

 workInProgress.flags
      --> 커밋의 각 패스가 읽는다
      --> [02] bubbleProperties 가 부모의 subtreeFlags 로 올린다

 L2091 throw
      --> work loop 의 catch 가 받아 handleThrow 로 간다
      --> 다만 이 빌드에서 닿는 길이 없다
```

## 다루지 않는 것

`HostRoot`(L1117) / `HostHoistable`(L1198) / `HostSingleton`(L1300) / `HostText`(L1472) / `ActivityComponent`(L1507) / `SuspenseComponent`(L1547) / `HostPortal`(L1679) / `Offscreen`(L1964) / `CacheComponent`(L2049) case 의 본문, `popTreeContext` 와 수화 중 id 생성, `isLegacyContextProvider` 와 레거시 컨텍스트, `upgradeHydrationErrorsToRecoverable`(L1181)은 같은 뼈대의 곁가지라 요약만 했다. case 별 대조표는 [spi](../spi/README.md)에 있다.
