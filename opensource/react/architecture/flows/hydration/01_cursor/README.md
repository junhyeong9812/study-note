# 커서

상위: [하이드레이션](../README.md)

서버가 보낸 DOM 위를 **커서 하나**가 걷는다. fiber 를 하나 만날 때마다 커서에서 노드를 하나 집는다. 다만 "집는 것" 이 "수화하는 것" 은 아니다.

## 위치

들어가기 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L162-L179 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L162-L179))

집기 `packages/react-reconciler` / `src` / `ReactFiberHydrationContext.js` L461-L484 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHydrationContext.js#L461-L484))

## 실제 코드

들어갈 때 전역 일곱을 전부 세운다.

```js
// ReactFiberHydrationContext.js L162-L179
function enterHydrationState(fiber: Fiber): boolean {
  // $FlowFixMe[constant-condition]
  if (!supportsHydration) {
    return false;
  }

  const parentInstance: Container = fiber.stateNode.containerInfo;
  nextHydratableInstance =
    getFirstHydratableChildWithinContainer(parentInstance);
  hydrationParentFiber = fiber;
  isHydrating = true;
  hydrationErrors = null;
  didSuspendOrErrorDEV = false;
  hydrationDiffRootDEV = null;
  rootOrSingletonContext = true;

  return true;
}
```

집는 모양은 단순하다. 못 집으면 곧장 어긋남이다.

```js
// ReactFiberHydrationContext.js L461-L484
function tryToClaimNextHydratableInstance(fiber: Fiber): void {
  if (!isHydrating) {
    return;
  }

  // Validate that this is ok to render here before any mismatches.
  const currentHostContext = getHostContext();
  const shouldKeepWarning = validateHydratableInstance(
    fiber.type,
    fiber.pendingProps,
    currentHostContext,
  );

  const nextInstance = nextHydratableInstance;
  if (
    !nextInstance ||
    !tryHydrateInstance(fiber, nextInstance, currentHostContext)
  ) {
    if (shouldKeepWarning) {
      warnNonHydratedInstance(fiber, nextInstance);
    }
    throwOnHydrationMismatch(fiber);
  }
}
```

다시 들어가는 쪽만 트리 문맥을 되살린다.

```js
// ReactFiberHydrationContext.js L181-L202
function reenterHydrationStateFromDehydratedActivityInstance(
  fiber: Fiber,
  activityInstance: ActivityInstance,
  treeContext: TreeContext | null,
): boolean {
  // $FlowFixMe[constant-condition]
  if (!supportsHydration) {
    return false;
  }
  nextHydratableInstance =
    getFirstHydratableChildWithinActivityInstance(activityInstance);
  hydrationParentFiber = fiber;
  isHydrating = true;
  hydrationErrors = null;
  didSuspendOrErrorDEV = false;
  hydrationDiffRootDEV = null;
  rootOrSingletonContext = false;
  if (treeContext !== null) {
    restoreSuspendedTreeContext(fiber, treeContext);
  }
  return true;
}
```

## 동작 흐름

```text
 ★ 모듈 전역 일곱  HYD L80-94

 L80  hydrationParentFiber    지금 어느 fiber 아래를 수화하는가
 L81  nextHydratableInstance  ★ **커서**. 다음에 집을 DOM 노드
 L82  isHydrating             지금 수화 중인가
 L86  didSuspendOrErrorDEV    [DEV] 이미 서스펜드/에러가 났나
 L89  hydrationDiffRootDEV    [DEV] 어긋남 트리
 L92  hydrationErrors         모아 둔 에러
 L94  rootOrSingletonContext  루트나 싱글톤 바로 아래인가

 렌더가 내려가며 fiber 하나마다 커서에서 노드를 하나 집는다
 ("커서" 는 내 표현이다)
```

```text
 들어가는 길이 셋  L162 / L181 / L204

 enterHydrationState(fiber)                              루트에서
   L165  !supportsHydration 이면 return false      ** [DEAD] **
   L168  parentInstance = fiber.stateNode.containerInfo
   L169  nextHydratableInstance =
           getFirstHydratableChildWithinContainer(parentInstance)
   L171  hydrationParentFiber = fiber
   L172  isHydrating = true
   L173  hydrationErrors = null
   L174  didSuspendOrErrorDEV = false
   L175  hydrationDiffRootDEV = null
   L176  rootOrSingletonContext = **true**

 reenterHydrationStateFromDehydratedActivityInstance  L181
 reenterHydrationStateFromDehydratedSuspenseInstance  L204
   커서를 그 경계 **안쪽** 첫 자식으로 잡고 (L191 / L214)
   L197 / L220  rootOrSingletonContext = **false**
   L199 / L222  treeContext 가 있으면 restoreSuspendedTreeContext(fiber, treeContext)

 ★ 셋 다 일곱 중 여섯을 다시 세운다.
   그래서 [03]의 resetHydrationState 가 넷만 지워도 낡을 일이 없다
```

```text
 ★ 다시 들어가는 둘만 트리 문맥을 되살린다

 그 문맥은 [02]에서 경계를 처음 만났을 때 붙잡아 둔 것이다 -
   tryHydrateActivity L327 / tryHydrateSuspense L362 부근에서
   getSuspendedTreeContext() 를 상태에 담는다

 restoreSuspendedTreeContext(ReactFiberTreeContext L265-278)가
 그것을 스택에 밀어 넣고 현재 값으로 세운다

 => useId 가 서버와 클라이언트에서 같은 값을 내는 근거다.
    경계를 나중에 이어서 수화해도 트리 위치가 유지된다
    ※ 마지막 문장은 내가 두 파일을 맞춰 보고 낸 귀결이다
```

```text
 tryToClaimNextHydratableInstance  L461-484

 L462  !isHydrating 이면
 L463    return
 L467  currentHostContext = getHostContext()
 L468  shouldKeepWarning = validateHydratableInstance(type, pendingProps, ctx)
 L474  nextInstance = nextHydratableInstance
 L475  nextInstance 가 없거나
 L477  tryHydrateInstance(fiber, nextInstance, currentHostContext) 가 거짓이면
 L479    shouldKeepWarning 이면
 L480      warnNonHydratedInstance(fiber, nextInstance)
 L482    throwOnHydrationMismatch(fiber)
```

```text
 ★★ 집는 가족이 여섯인데 한 가족이 아니다

 tryHydrate* 넷      L251 Instance / L293 Text / L313 Activity / L348 Suspense
 집는 함수 여섯      L418 Singleton / L461 Instance / L486 Text
                     L506 Activity / L518 Suspense / L530 FormMarker

 ★ isHydrating 가드가 있는 것 - L462 / L487 / L533
 ★ **없는 것** - L506 Activity / L518 Suspense
   대신 부르는 쪽이 `if (getIsHydrating())` 안에서 부른다 (BW L1141, BW L2421)

 ★ 1대1로 짝이 맞지도 않는다
   claimHydratableSingleton 에는 짝이 되는 tryHydrate* 가 없고,
   FormMarker 는 자기 안에서 직접 맞춘다 (L537 canHydrateFormStateMarker)
```

```text
 ★★ 싱글톤은 집는 것이 아니라 찾아낸다  L418-459

 L426  instance = fiber.stateNode = resolveSingletonInstance(...)

 이 함수 안에 warnNonHydratedInstance 도 throwOnHydrationMismatch 도 **없다**.
 실패할 길이 없다

 => `<html>` `<head>` `<body>` 는 이미 거기 있으니
    맞춰 보는 대신 해소한다. 집는 단계에서 어긋날 수 없다
```

```text
 ★★ 경계를 만나면 fiber 를 하나 더 만든다

 tryHydrateActivity(L313) / tryHydrateSuspense(L348)는 맞추기만 하지 않는다
   L325-330 / L360-365  상태 객체를 만든다
     dehydrated / treeContext: getSuspendedTreeContext() /
     retryLane: OffscreenLane / hydrationErrors: null
   L336-339 / L371-374  **탈수 프래그먼트 자식 fiber** 를 만들어 붙인다
     createFiberFromDehydratedFragment(...) 로 만들고
     dehydratedFragment.return = fiber; fiber.child = dehydratedFragment

 주석 L333-335 / L368-370 이 이유를 적는다 -
   "This simplifies the code for getHostSibling and deleting nodes, since it
    doesn't have to consider all Suspense boundaries and check if they're
    dehydrated ones or not."

 => [DOM 조작]의 getHostSibling 이 DehydratedFragment 를 호스트 노드처럼
    취급하는 것이 이 덕분이다
```

```text
 ★ 커서가 null 이어도 수화가 끝난 것은 아니다

 L307 / L343 / L378  tryHydrateText / Activity / Suspense 가
 맞춘 뒤 nextHydratableInstance = null 로 만든다

 => "이 노드 아래에는 집을 것이 없다" 거나 "나중에 다시 들어온다" 는 뜻이지
    어긋남이 아니다
```

```text
 ★ getIsHydrating(L921)이 이 파일에서 가장 많이 불리는 export 다

 부르는 곳이 넓다
   [훅]           useId / useActionState 쪽 (Hooks 네 자리)
   [자식 조정]     여섯 자리
   [completeWork] 다섯 자리
   [에러와 Suspense] 둘
   [렌더 루프]     둘

 => 이 파일은 수화를 **수행**하기도 하지만
    "지금 수화 중인가" 를 온 리콘실러에 알려 주는 자리이기도 하다
```

## 결과가 쓰이는 곳

```text
 fiber.stateNode
      --> 집은 DOM 노드가 여기 붙는다
      --> 실제 속성 맞추기는 [02]가 말하는 completeWork 에서다

 nextHydratableInstance
      --> 다음 fiber 가 집을 노드
      --> [03]이 fiber 를 빠져나올 때 전진시킨다

 isHydrating
      --> getIsHydrating 으로 온 리콘실러가 본다

 treeContext
      --> useId 가 서버와 같은 값을 내게 한다
```

## 다루지 않는 것

`tryHydrateInstance`(L251) / `tryHydrateText`(L293)의 본문과 `canHydrateInstance` / `canHydrateTextInstance`(호스트 설정)가 주석 노드와 공백을 건너뛰며 후보를 고르는 규칙, `validateHydratableInstance` / `validateHydratableTextInstance` 가 무엇을 검사하는지, `resolveSingletonInstance`(호스트 설정)가 `<html>` `<head>` `<body>` 를 찾아내는 방식, `getSuspendedTreeContext` / `restoreSuspendedTreeContext`(`ReactFiberTreeContext`)의 스택 운용과 `useId` 의 id 생성 규칙, `tryToClaimNextHydratableFormMarkerInstance`(L530)가 `useActionState` 에 돌려주는 값과 그 backwards-compat 주석(L551-553), `prepareToHydrateHostActivityInstance`(L654) / `prepareToHydrateHostSuspenseInstance`(L676)가 "bug in React" 불변식만 던지는 사정은 같은 뼈대의 곁가지라 요약만 했다.
