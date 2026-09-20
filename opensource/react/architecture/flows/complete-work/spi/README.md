# spi

상위: [completeWork 흐름](../README.md)

이 흐름의 계약은 **반환값**이다. `null` 이면 올라가고, `null` 이 아니면 그 fiber 를 다시 begin 단계로 보낸다. 그리고 `throw` 로 향하는 갈래가 넷인데 넷 다 닿지 않는다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberCompleteWork.js` 기준이다.

## 반환 계약

```text
 completeWork 의 return 은 전부 34자리다

   return null          29자리
   return (Fiber)        5자리

 completeUnitOfWork 가 그것을 이렇게 나눈다 (WorkLoop L3389-3405)

   null 이 아니면   workInProgress = next 로 두고 return
                    => 그 fiber 를 다시 begin 단계로 보낸다
   null 이면        형제가 있으면 형제로
                    없으면 부모로 올라간다

 암묵적 undefined 반환은 없다
 switch 를 빠져나가면 L2091 의 throw 이기 때문이다
```

| 줄 | 값 | case | 언제 |
|---|---|---|---|
| L1522 | `workInProgress` | ActivityComponent | 탈수 경계를 못 끝냈고 `ForceClientRender` 일 때 |
| L1571 | `workInProgress` | SuspenseComponent | 〃 |
| L1595 | `workInProgress` | SuspenseComponent | 정상 경로에서 `DidCapture` 일 때 |
| L1787 | `workInProgress.child` | SuspenseListComponent | 1차 패스에서 서스펜드한 row 를 찾아 head 를 다시 그릴 때 |
| L1936 | `next` | SuspenseListComponent | tail 에 렌더할 row 가 남았을 때 |

```text
 앞의 셋과 뒤의 둘이 뜻이 다르다

 앞의 셋  "내 begin 단계를 다시 해라"
          이번에는 DidCapture 나 ForceClientRender 가 켜져 있어
          beginWork 가 fallback 이나 클라이언트 렌더 갈래를 고른다

 뒤의 둘  [04]가 row 를 하나씩 모는 것이다
          리스트의 row 개수만큼 completeWork 가 반복해서 불린다
```

## case 대조표

`switch`(L1091-2089)의 `case` 레이블은 **29개**이고 실행 본문은 **19개**다. [beginWork](../../begin-work/README.md)의 `switch` 도 레이블이 29개인데 그쪽은 본문도 29개였다.

| tag | case | pop 하는 것 | 반환 | 이 빌드에서 |
|---|---|---|---|---|
| IncompleteFunctionComponent | L1092 | — | 없음 → L2091 | **죽었다** — 언제나 `break` |
| LazyComponent … MemoComponent (9개) | L1098-1106 | — | `null` L1108 | 산다 (본문 공유) |
| ClassComponent | L1109 | `popLegacyContext` (조건부) | `null` L1115 | 산다 |
| HostRoot | L1117 | `popCacheProvider` `popRootTransition` `popHostContainer` `popTopLevelLegacyContextObject` `popHydrationState`(조건부) | `null` L1196 | 산다 |
| HostHoistable | L1198 | 없음 | `null` ×5 | 산다. `// Fall through`(L1298)는 죽었다 |
| HostSingleton | L1300 | `popHostContext` `popHydrationState` | `null` L1338/L1368 | 산다. `// Fall through`(L1370)는 죽었다 |
| HostComponent | L1372 | `popHostContext` `popHydrationState` | `null` L1399/L1470 | 산다 |
| HostText | L1472 | `popHydrationState` | `null` L1505 | 산다 |
| ActivityComponent | L1507 | `popSuspenseHandler` (탈수 갈래) | `workInProgress` L1522 / `null` | 산다 |
| SuspenseComponent | L1547 | `popSuspenseHandler` | `workInProgress` L1571/L1595 / `null` | 산다 |
| HostPortal | L1679 | `popHostContainer` | `null` L1687 | 산다 |
| ContextProvider | L1688 | `popProvider` | `null` L1693 | 산다 |
| IncompleteClassComponent | L1694 | — | 없음 → L2091 | **죽었다** — 언제나 `break` |
| SuspenseListComponent | L1707 | `popSuspenseListContext` | 다섯 갈래 | 산다 |
| ScopeComponent | L1941 | — | 없음 → L2091 | **죽었다** — 언제나 `break` |
| OffscreenComponent | L1964 | `popSuspenseHandler` `popHiddenContext` `popTransition` | `null` L2047 | 산다 (본문 공유) |
| LegacyHiddenComponent | L1965 | 〃 | 〃 | **레이블이 죽었다** — 그 fiber 가 만들어지지 않는다 |
| CacheComponent | L2049 | `popCacheProvider` | `null` L2061 | 산다 |
| TracingMarkerComponent | L2063 | `popMarkerInstance` | `null` L2071 | 본문은 죽고 `return null` 만 산다 |
| ViewTransitionComponent | L2073 | — | `null` L2081 | 산다 |
| Throw | L2083 | — | 없음 → L2091 | **도달 불가** |

```text
 본문을 공유하는 묶음

 (가) 무조건 공유  L1098-1106 아홉 레이블 -> L1107-1108
                   L1964-1965 두 레이블  -> L1966-2047

 (나) 조건부 fallthrough 체인
      HostHoistable -> HostSingleton -> HostComponent
      자기 capability 플래그가 참이면 return 으로 빠지고
      거짓이면 다음 case 본문으로 흘러든다

      react-dom 은 supportsResources / supportsSingletons 가 둘 다 true 라
      두 fallthrough 가 죽어 있고 세 case 가 독립이다
      둘 다 false 인 renderer 에서는 세 레이블이 한 본문을 쓴다
```

## throw 로 향하는 갈래 넷 — 그런데 닿지 않는다

```text
 L1094  IncompleteFunctionComponent  break   [disableLegacyMode=true]
 L1696  IncompleteClassComponent     break   [disableLegacyMode=true]
 L1962  ScopeComponent               break   [enableScopeAPI=false]
 L2083  Throw                        흘러나감 [disableLegacyMode=true]

 앞의 셋 - 그 tag 의 fiber 가 만들어지지 않는다
   Incomplete* 두 tag 는 생성이 아니라 tag 재기입으로 붙는데
   그 블록이 !disableLegacyMode 안에 있어 도달 불가다
   ScopeComponent 는 enableScopeAPI 가 꺼져 있어
   fiber 생성 단계에서 걸러진다
   (자세한 사슬은 [beginWork/spi](../../begin-work/spi/README.md)에 있다)

 넷째 - Throw fiber 는 completeWork 에 오지 않는다
```

```text
 ★ Throw fiber 가 이 함수에 못 오는 이유

 1  beginWork L4465 가 case Throw 에서 무조건 던진다
    => 그 fiber 는 완료되지 못하고 Incomplete 로 표시된다

 2  completeUnitOfWork 의 첫 줄이 갈림길이다 (WorkLoop L3354)
      Incomplete 플래그가 있으면
        unwindUnitOfWork(...)
        return              <- completeWork 를 아예 부르지 않는다

 3  되감기는 다른 함수를 쓴다
```

`packages/react-reconciler` / `src` / `ReactFiberUnwindWork.js` L66-L250 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberUnwindWork.js#L66-L250))

```text
 unwindWork 의 switch 에는 case Throw 가 없다

 레이블 14개 - ClassComponent / HostRoot / HostHoistable / HostSingleton /
 HostComponent / ActivityComponent / SuspenseComponent /
 SuspenseListComponent / HostPortal / ContextProvider /
 OffscreenComponent / LegacyHiddenComponent / CacheComponent /
 TracingMarkerComponent

 Throw 는 default 로 지나간다

 => completeWork L2083 은 죽은 정도가 아니라 도달 불가다
```

```text
 [beginWork] 와 대칭이다

 beginWork    플래그가 꺼진 case 가 break 로 throw 를 향하지만
              그 tag 의 fiber 가 만들어지지 않아 닿지 않는다

 completeWork case Throw 가 throw 를 향하지만
              그 fiber 가 unwind 로 갈라져 닿지 않는다

 양쪽 다 'Unknown unit of work tag' 라는 같은 메시지를 향하고
 양쪽 다 닿는 길이 없다. 순수한 방어선이다
```

## 이 파일의 다른 throw

```text
 'We must have new props for new mounts.'   셋이다
   L1325  HostSingleton
   L1386  HostComponent
   L1482  HostText

 'A dehydrated suspense component was completed without a hydrated node.'
   L926 / L1009

 'Client rendering an Activity suspended it again. This is a bug in React.'
   L1536

 'Unknown unit of work tag (...)'
   L2091

 그리고 제어 흐름으로 쓰이는 throw 가 하나 더 있다
   L1463 -> L602 suspendCommit() -> ReactFiberThenable L313
   throw SuspenseyCommitException
   => [렌더 루프]의 handleThrow 가 SuspendedOnInstance 로 바꾼다
```

## 죽은 플래그와 죽은 갈래

```text
 disableLegacyMode = true         ReactFeatureFlags L192
   L1094 / L1696 의 break 가 언제나 돈다
   L2086 의 return null 은 절대 안 돈다

 enableScopeAPI = false           L53
   ScopeComponent 본문(L1943-1960) 전체

 enableLegacyHidden = false       L109
   LegacyHiddenComponent 레이블 자체

 enableTransitionTracing = false  L106
   TracingMarkerComponent 본문(L2064-2070)
   HostRoot 의 transition 관련 블록들

 enableSuspenseCallback = false   L50
   SuspenseComponent 의 L1654-1662

 supportsPersistence = false      (react-dom)
   markCloned 의 본문(L210)
   doesRequireClone(L217) 전체
   updateHostComponent 의 persistence 갈래(L481 이하)
   appendAllChildrenToContainer(L353)
   updateHostContainer(L435) 의 본문

 enableProfilerTimer = __PROFILE__  L229
   ★ 이것은 상수가 아니다. 빌드에 따라 갈린다
     DEV   true  -> bubbleProperties 의 프로파일러 갈래
     운영  false -> 평상 갈래 (child.return 을 다시 세우는 줄이 여기 있다)
```

## 결과가 쓰이는 곳

```text
 반환값
      --> completeUnitOfWork 가 올라갈지 되돌려 보낼지 정한다

 flags / subtreeFlags
      --> 커밋의 각 패스가 읽는다
      --> [02] bubbleProperties 가 부모로 올린다

 pop 한 스택
      --> [beginWork]가 민 것의 짝이다
      --> 짝이 어긋나면 다음 fiber 가 잘못된 컨텍스트를 본다

 죽은 갈래
      --> 소스에는 있지만 이 빌드에서 재현할 수 없다
      --> 문서가 살아 있는 분기처럼 적으면 오해를 만든다
```

## 다루지 않는 것

`unwindWork`(`ReactFiberUnwindWork.js` L66)가 각 tag 에서 하는 되감기, `throwException` 이 경계를 찾는 과정, `StaticMask` 의 구성, `SuspenseListRenderState` 의 나머지 칸, `popHydrationState` 와 수화 상태 정리, 커밋 단계가 이 flags 를 소비하는 규칙은 이 문서의 범위 밖이다.
