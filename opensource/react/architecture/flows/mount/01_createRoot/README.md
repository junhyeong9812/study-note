# createRoot

상위: [마운트](../README.md)

**그릇만 만든다.** 아흔 줄 중 대부분이 옵션 읽기와 개발 모드 경고이고, 실제로 하는 일은 셋이다 — 컨테이너 검사, fiber 루트 생성, 이벤트 리스너 등록.

## 위치

`packages/react-dom` / `src/client` / `ReactDOMRoot.js` L171-L262 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom/src/client/ReactDOMRoot.js#L171-L262))

## 실제 코드

컨테이너가 아니면 바로 던진다.

```js
// ReactDOMRoot.js L175-L177
  if (!isValidContainer(container)) {
    throw new Error('Target container is not a DOM element.');
  }
```

기본값 여덟 개를 세운다.

`packages/react-dom` / `src/client` / `ReactDOMRoot.js` L181-L188 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom/src/client/ReactDOMRoot.js#L181-L188))

```js
// ReactDOMRoot.js L181-L188
  const concurrentUpdatesByDefaultOverride = false;
  let isStrictMode = false;
  let identifierPrefix = '';
  let onUncaughtError = defaultOnUncaughtError;
  let onCaughtError = defaultOnCaughtError;
  let onRecoverableError = defaultOnRecoverableError;
  let onDefaultTransitionIndicator = defaultOnDefaultTransitionIndicator;
  let transitionCallbacks = null;
```

옵션 하나만 플래그 안에 있다.

```js
// ReactDOMRoot.js L229-L233
    if (enableDefaultTransitionIndicator) {
      if (options.onDefaultTransitionIndicator !== undefined) {
        onDefaultTransitionIndicator = options.onDefaultTransitionIndicator;
      }
    }
```

그리고 루트를 만든다.

`packages/react-dom` / `src/client` / `ReactDOMRoot.js` L239-L258 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom/src/client/ReactDOMRoot.js#L239-L258))

```js
// ReactDOMRoot.js L239-L251
  const root = createContainer(
    container,
    ConcurrentRoot,
    null,
    isStrictMode,
    concurrentUpdatesByDefaultOverride,
    identifierPrefix,
    onUncaughtError,
    onCaughtError,
    onRecoverableError,
    onDefaultTransitionIndicator,
    transitionCallbacks,
  );
```

## 동작 흐름

```text
 L175  isValidContainer 가 아니면 => throw
         "Target container is not a DOM element."
 L179  warnIfReactDOMContainerInDEV(container)
 L181  기본값 여덟 개
         concurrentUpdatesByDefaultOverride = false   <- 상수다. 아래 참고
         isStrictMode = false
         identifierPrefix = ''
         onUncaughtError / onCaughtError / onRecoverableError
         onDefaultTransitionIndicator
         transitionCallbacks = null
 L191  options 가 있으면 덮어쓴다
         L192  [__DEV__] hydrate 옵션이면 경고
               JSX 를 넘겼으면 경고 (createRoot 에 엘리먼트를 넣은 실수)
         L214  unstable_strictMode
         L217  identifierPrefix
         L220  onUncaughtError / L223 onCaughtError / L226 onRecoverableError
         L229  [enableDefaultTransitionIndicator] onDefaultTransitionIndicator
         L234  unstable_transitionCallbacks
 L239  createContainer(container, ConcurrentRoot, null, isStrictMode, ...)
 L252  markContainerAsRoot(root.current, container)
 L254  rootContainerElement 를 고른다
 L258  listenToAllSupportedEvents(rootContainerElement)
 L261  => new ReactDOMRoot(root)
```

```text
 옵션 하나만 플래그로 가려져 있다

 L229  if (enableDefaultTransitionIndicator) {
 L230    if (options.onDefaultTransitionIndicator !== undefined) { ... }

 나머지 일곱은 플래그 밖이다
 그 플래그가 꺼진 빌드에서는 onDefaultTransitionIndicator 를 넘겨도
 조용히 무시된다
 (경고도 없다. 코드를 보고 내가 판단한 것이다)
```

```text
 죽은 인자가 하나 있다

 L181  const concurrentUpdatesByDefaultOverride = false;

 이것은 상수다. options 로도 안 바뀐다 (L191-237 에 해당 분기가 없다)
 그리고 받는 쪽도 안 쓴다

 createContainer 의 주석이 그것을 적어 두었다 (Reconciler L240)
   "TODO: Remove `concurrentUpdatesByDefaultOverride`. It is now ignored."

 실제로 createFiberRoot 시그니처에는 그 파라미터 자체가 없다

 그런데도 네 자리에 살아 있다
   ReactDOMRoot L181 과 L244   createRoot 이 만들어 넘긴다
   ReactDOMRoot L300 과 L346   hydrateRoot 도 똑같이 한다
 그리고 createHydrationContainer 에 같은 TODO 가 복제돼 있다
```

```text
 컨테이너가 주석 노드일 수 있다

 L254  rootContainerElement =
         !disableCommentsAsDOMContainers && container.nodeType === COMMENT_NODE
           ? container.parentNode
           : container

 주석 노드를 컨테이너로 쓰면 리스너를 부모에 건다
 disableCommentsAsDOMContainers 가 켜진 빌드에서는 그 특례가 없다
```

```text
 이벤트 리스너는 여기서 한 번만 건다

 L258  listenToAllSupportedEvents(rootContainerElement)

 모든 지원 이벤트를 루트 컨테이너에 위임으로 건다
 컴포넌트마다 거는 게 아니라 루트에 한 번이다

 이 호출은 addEventListener 등록만 한다. 스케줄하지 않는다
```

```text
 여기까지 화면에 아무것도 없다

 createContainer 가 initialChildren 을 null 로 하드코딩하므로
 (Reconciler L262) 루트 fiber 의 memoizedState.element 가 null 이다

 그래서 createRoot 만 부르고 끝내면 DOM 은 그대로다
```

## 결과가 쓰이는 곳

```text
 ReactDOMRoot 인스턴스
      --> _internalRoot 에 FiberRoot 를 들고 있다
      --> render / unmount 가 그것을 꺼내 쓴다

 markContainerAsRoot
      --> DOM 노드에서 fiber 로 거슬러 갈 수 있게 한다
      --> 이벤트 처리가 그 경로를 쓴다

 등록된 이벤트 리스너
      --> 이후 모든 사용자 입력이 이 루트로 들어온다
      --> 컴포넌트가 아직 없어도 리스너는 이미 걸려 있다
```

## 다루지 않는 것

`isValidContainer` 의 판정 기준, `warnIfReactDOMContainerInDEV` 가 보는 것, `listenToAllSupportedEvents` 의 이벤트 위임 구조와 캡처·버블 구분, `markContainerAsRoot` 가 쓰는 내부 프로퍼티 키, `hydrateRoot`(L276)의 수화 경로, `CreateRootOptions` 의 나머지 옵션은 같은 뼈대의 곁가지라 요약만 했다. 플래그별 차이는 [spi](../spi/README.md)에 있다.
