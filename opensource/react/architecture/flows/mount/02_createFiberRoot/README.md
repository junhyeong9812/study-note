# createFiberRoot

상위: [마운트](../README.md)

루트 객체와 fiber 하나를 만들어 **서로를 가리키게 엮는다.** 주석이 그것을 "Cyclic construction" 이라고 부른다.

## 위치

`ReactFiberRoot.js` `packages/react-reconciler` / `src` / `ReactFiberRoot.js` L157-L236 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRoot.js#L157-L236))

## 실제 코드

거쳐 오는 자리부터 본다. `createContainer` 가 두 값을 하드코딩한다.

`ReactFiberReconciler.js` `packages/react-reconciler` / `src` / `ReactFiberReconciler.js` L261-L262 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberReconciler.js#L261-L262))

고리를 만드는 두 줄.

`packages/react-reconciler` / `src` / `ReactFiberRoot.js` L208-L212 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRoot.js#L208-L212))

```js
// ReactFiberRoot.js L208-L212
  // Cyclic construction. This cheats the type system right now because
  // stateNode is any.
  const uninitializedFiber = createHostRootFiber(tag, isStrictMode);
  root.current = uninitializedFiber;
  uninitializedFiber.stateNode = root;
```

캐시를 둘로 잡는다.

`packages/react-reconciler` / `src` / `ReactFiberRoot.js` L214-L225 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberRoot.js#L214-L225))

```js
// ReactFiberRoot.js L214-L216
  const initialCache = createCache();
  retainCache(initialCache);

```

> The pooledCache is a fresh cache instance that is used temporarily for newly mounted boundaries during a render. In general, the pooledCache is always cleared from the root at the end of a render: it is either released when render commits, or moved to an Offscreen component if rendering suspends. Because the lifetime of the pooled cache is distinct from the main memoizedState.cache, it must be retained separately.

그리고 초기 상태를 세운다.

```js
// ReactFiberRoot.js L226-L233
  const initialState: RootState = {
    element: initialChildren,
    isDehydrated: hydrate,
    cache: initialCache,
  };
  uninitializedFiber.memoizedState = initialState;

  initializeUpdateQueue(uninitializedFiber);
```

## 동작 흐름

```text
 [createContainer]  Reconciler L235
 L261  hydrate = false
 L262  initialChildren = null            <- 하드코딩
 L263  createFiberRoot(containerInfo, tag, hydrate, initialChildren, ...)
 L278  registerDefaultIndicator(onDefaultTransitionIndicator)
 L279  => return root

 [createFiberRoot]  ReactFiberRoot L157
 L189  root = new FiberRootNode(...)
 L200  [enableSuspenseCallback]  root.hydrationCallbacks = hydrationCallbacks
 L204  [enableTransitionTracing] root.transitionCallbacks = transitionCallbacks
 L210  uninitializedFiber = createHostRootFiber(tag, isStrictMode)
 L211  root.current = uninitializedFiber
 L212  uninitializedFiber.stateNode = root
 L214  initialCache = createCache()
 L215  retainCache(initialCache)                 <- 첫 번째
 L224  root.pooledCache = initialCache
 L225  retainCache(initialCache)                 <- 두 번째
 L226  initialState = { element: initialChildren, isDehydrated: hydrate,
                        cache: initialCache }
 L231  uninitializedFiber.memoizedState = initialState
 L233  initializeUpdateQueue(uninitializedFiber)
 L235  => return root
```

```text
 retainCache 가 두 번 불린다

 L215  memoizedState.cache 가 될 몫
 L225  pooledCache 가 될 몫

 같은 인스턴스인데 참조 수를 둘 올린다
 주석 L217-223 이 이유를 말한다 - 두 수명이 다르기 때문이다
 pooledCache 는 렌더가 끝나면 풀리거나 Offscreen 으로 옮겨 가고
 memoizedState.cache 는 커밋된 트리와 함께 남는다
```

```text
 L231 과 L233 의 순서에 뜻이 있다

 initializeUpdateQueue 는 baseState 를 fiber.memoizedState 로 잡는다
 (ReactFiberClassUpdateQueue L178)

 그래서 memoizedState 를 먼저 세워야 baseState 가 초기 상태를 갖는다
 순서를 바꾸면 baseState 가 null 이 된다

 (주석은 없다. 두 줄의 순서와 L178 을 맞춰 보고 내가 판단한 것이다)
```

```text
 루트 fiber 의 mode 가 여기서 정해진다

 createHostRootFiber (ReactFiber.js L536-558)

 L541  if (disableLegacyMode || tag === ConcurrentRoot)
 L542    mode = ConcurrentMode
 L543    isStrictMode 면 |= StrictLegacyMode | StrictEffectsMode
 L546  else
 L547    mode = NoMode
 L550  [__DEV__ 또는 enableProfilerTimer && devtools] |= ProfileMode

 react-dom 빌드에서는 disableLegacyMode 가 true 라
 앞 항만으로 언제나 ConcurrentMode 다 (tag 와 무관하다)

 사실 그 전에 tag 자체가 덮어써진다
   FiberRootNode L63  this.tag = disableLegacyMode ? ConcurrentRoot : tag;

 그래서 createRoot 이 ConcurrentRoot 를 넘기는 것은 결과적으로 무의미하다
 플래그가 이미 같은 일을 두 자리에서 한다

 (주석은 없다. 플래그 값과 세 자리를 맞춰 보고 내가 판단한 것이다)
```

```text
 이 고리가 무엇을 가능하게 하나

 root.current  커밋된 fiber 트리의 뿌리
 fiber.stateNode  그 fiber 가 속한 루트

 렌더 중에는 root.current.alternate 가 작업 중인 트리다
 커밋이 끝나면 root.current 가 그쪽으로 넘어간다

 (alternate 교체는 커밋 흐름의 일이라 여기서는 다루지 않는다)
```

## 결과가 쓰이는 곳

```text
 FiberRoot
      --> createRoot 이 ReactDOMRoot 에 담아 돌려준다
      --> 이후 모든 갱신이 이 객체를 통과한다

 memoizedState.element = null
      --> root.render 가 넣을 children 의 자리다
      --> 렌더 중 HostRoot 처리가 이 값을 갈아 끼운다

 updateQueue
      --> root.render 의 update 가 여기 쌓인다
      --> baseState 가 초기 상태를 들고 있다
```

## 다루지 않는 것

`FiberRootNode` 생성자가 세우는 필드 전부(`pendingLanes`, `callbackNode`, `entangledLanes` 등), `createFiber` 가 fiber 객체를 만드는 방식과 필드 구성, `createCache` / `retainCache` 의 참조 계수, `initializeUpdateQueue` 가 만드는 큐의 모양과 `shared.pending` 원형 리스트, `registerDefaultIndicator` 의 동작은 같은 뼈대의 곁가지라 요약만 했다.
