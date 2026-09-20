# ReactDOMRoot.render

상위: [마운트](../README.md)

서른 줄인데 **실제 코드는 넉 줄**이고 나머지는 개발 모드 경고다. 그리고 이 함수 하나가 **두 클래스의 프로토타입에 동시에 붙는다.**

## 위치

`packages/react-dom` / `src/client` / `ReactDOMRoot.js` L107-L136 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom/src/client/ReactDOMRoot.js#L107-L136))

## 실제 코드

한 줄에서 두 프로토타입에 대입한다.

```text
 ReactDOMRoot.js L107-109

 ReactDOMHydrationRoot.prototype.render = ReactDOMRoot.prototype.render =
   // $FlowFixMe[missing-this-annot]
   function (children: ReactNodeList): void {
```

그 안의 가드는 이것 하나다.

```js
// ReactDOMRoot.js L110-L113
    const root = this._internalRoot;
    if (root === null) {
      throw new Error('Cannot update an unmounted root.');
    }
```

경고를 지나면 남는 것은 한 줄이다.

```js
// ReactDOMRoot.js L135-L135
    updateContainer(children, root, null, null);
```

`unmount` 도 같은 모양이다.

`packages/react-dom` / `src/client` / `ReactDOMRoot.js` L139-L169 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom/src/client/ReactDOMRoot.js#L139-L169))

```js
// ReactDOMRoot.js L165-L167
      updateContainerSync(null, root, null, null);
      flushSyncWork();
      unmarkContainerAsRoot(container);
```

## 동작 흐름

```text
 L107  ReactDOMHydrationRoot.prototype.render = ReactDOMRoot.prototype.render = fn
 L110  root = this._internalRoot
 L111  null 이면 => throw "Cannot update an unmounted root."
 L115  [__DEV__] 두 번째 인자를 넘겼으면 경고 세 갈래
         L118  함수면      "does not support the second callback argument"
         L123  컨테이너면  "You passed a container to the second argument"
         L128  그 밖이면   "it only accepts one argument"
 L135  updateContainer(children, root, null, null)
```

```text
 한 함수가 둘에 붙는다

 L107 의 연쇄 대입이 그것을 한다

   ReactDOMHydrationRoot.prototype.render = ReactDOMRoot.prototype.render = fn

 unmount 도 같다 (L139)

 그래서 createRoot 로 만든 루트와 hydrateRoot 로 만든 루트가
 render 에서는 완전히 같은 코드를 탄다
 갈라지는 것은 루트를 만들 때뿐이다
```

```text
 옛 API 의 흔적이 경고로 남아 있다

 ReactDOM.render(element, container, callback) 시절에는
 세 번째 인자로 콜백을 줬다

 지금은 두 번째 인자를 받으면 전부 경고다 (L115-134)
 경고 문구가 대안까지 말한다 (L120-122)
   "To execute a side effect after rendering, declare it in a component body
    with useEffect()."

 이 경고는 __DEV__ 블록 안이라 프로덕션 빌드에는 없다
 즉 운영에서는 두 번째 인자가 조용히 무시된다
```

```text
 render 와 unmount 가 다른 함수를 부른다

 render   L135  updateContainer(children, root, null, null)
 unmount  L165  updateContainerSync(null, root, null, null)
          L166  flushSyncWork()

 unmount 는 children 을 null 로 넣어 트리를 비우고
 동기 버전을 써서 그 자리에서 끝낸다

 render 는 lane 을 요청해 받고(Reconciler L360) 비동기로 스케줄한다
```

```text
 _internalRoot 가 null 이 되는 때

 unmount 가 끝나면서 세운다 (L168 부근)
 그 뒤에 render 를 부르면 L111 이 던진다
   "Cannot update an unmounted root."
```

## 결과가 쓰이는 곳

```text
 updateContainer 로 넘어간 children
      --> update.payload = {element} 가 되어 큐에 쌓인다

 updateContainer 의 반환값 (lane)
      --> 이 함수는 그것을 버린다. void 를 돌려준다
      --> 호출자가 우선순위를 알 방법이 없다

 throw
      --> 언마운트된 루트에 render 하면 여기서 끝난다
      --> 스케줄까지 안 간다
```

## 다루지 않는 것

`unmount` 의 나머지 절차(`flushSyncWork`, `unmarkContainerAsRoot`)와 렌더 중 unmount 경고, `hydrateRoot` 가 만드는 `ReactDOMHydrationRoot` 와 `unstable_scheduleHydration`, `isValidContainer` 판정, `updateContainerSync` 가 `flushSyncWork` 와 짝이 되는 이유는 같은 뼈대의 곁가지라 요약만 했다.
