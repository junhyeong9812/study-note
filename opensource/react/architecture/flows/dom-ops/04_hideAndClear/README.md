# 숨기고 지우기

상위: [DOM 조작](../README.md)

Offscreen 으로 숨긴 트리는 **언마운트되지 않는다.** 인라인 `display:none !important` 가 붙을 뿐이다. 그리고 루트를 비우는 것도 통째로 지우는 것이 아니다.

## 위치

숨기기 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L1399-L1438 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L1399-L1438))

지우기 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L3671-L3739 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L3671-L3739))

## 실제 코드

숨기는 법.

```js
// ReactFiberConfigDOM.js L1399-L1414
export function hideInstance(instance: Instance): void {
  // TODO: Does this work for all element types? What about MathML? Should we
  // pass host context to this method?
  instance = instance as any as HTMLElement;
  const style = instance.style;
  // $FlowFixMe[method-unbinding]
  if (typeof style.setProperty === 'function') {
    style.setProperty('display', 'none', 'important');
  } else {
    style.display = 'none';
  }
}

export function hideTextInstance(textInstance: TextInstance): void {
  textInstance.nodeValue = '';
}
```

> TODO: Does this work for all element types? What about MathML? Should we pass host context to this method?

되돌리는 법. props 의 `display` 로 돌아간다.

```js
// ReactFiberConfigDOM.js L1422-L1438
export function unhideInstance(instance: Instance, props: Props): void {
  instance = instance as any as HTMLElement;
  const styleProp = props[STYLE];
  const display =
    styleProp !== undefined &&
    // $FlowFixMe[invalid-compare]
    styleProp !== null &&
    styleProp.hasOwnProperty('display')
      ? styleProp.display
      : null;
  instance.style.display =
    display == null || typeof display === 'boolean'
      ? ''
      : // The value would've errored already if it wasn't safe.
        // eslint-disable-next-line react-internal/safe-string-coercion
        ('' + display).trim();
}
```

지우기는 두 갈래다.

```js
// ReactFiberConfigDOM.js L3671-L3687
export function clearContainer(container: Container): void {
  const nodeType = container.nodeType;
  if (nodeType === DOCUMENT_NODE) {
    clearContainerSparingly(container);
  } else if (nodeType === ELEMENT_NODE) {
    switch (container.nodeName) {
      case 'HEAD':
      case 'HTML':
      case 'BODY':
        clearContainerSparingly(container);
        return;
      default: {
        container.textContent = '';
      }
    }
  }
}
```

## 동작 흐름

```text
 hideInstance  CFG L1399-1410

 L1403  style = instance.style
 L1405  typeof style.setProperty === 'function' 이면
 L1406    style.setProperty('display', 'none', 'important')   ★ **!important**
 L1407  아니면
 L1408    style.display = 'none'

 TODO L1400-1401 - "Does this work for all element types? What about MathML?
 Should we pass host context to this method?"

 hideTextInstance  CFG L1412-1414
 L1413  textInstance.nodeValue = ''      ★ 텍스트는 빈 문자열로

 unhideInstance  CFG L1422-1438
 L1424  styleProp = props[STYLE]
 L1425    display = styleProp 이 undefined 도 null 도 아니고
                    'display' 를 가지고 있으면 styleProp.display, 아니면 null
 L1432  instance.style.display =
 L1433    display 가 null/undefined 이거나 boolean 이면
 L1434      ''
 L1436    아니면
 L1437      ('' + display).trim()
```

```text
 ★★ 숨긴다는 것이 언마운트가 아니다

 DOM 노드는 그대로 남고 인라인 스타일만 붙는다.
 그래서 다시 보이게 될 때 **상태도 DOM 도 그대로**다
 (iframe 이 다시 로드되지 않고, 스크롤 위치도 남는다)
 ※ 괄호 안은 내 귀결이고 주석에 없다

 ★ !important 를 쓰는 이유는 사용자 CSS 가 display 를 이기지 못하게 하려는
   것으로 보인다. 주석은 없다
```

```text
 ★★ 방아쇠는 Suspense 가 아니라 Offscreen/Activity 의 가시성이다

 CMW L2609  hideOrUnhideAllChildren(finishedWork, isHidden)
 CMW L1185    hideOrUnhideAllChildren
 CMW L1199      hideOrUnhideAllChildrenOnFiber
 CMW L1208        commitShowHideHostInstance(fiber, isHidden)
 CHE L206         commitShowHideHostInstance
 CHE L211/213       hideInstance(instance)  (DEV 는 runWithFiberInDEV 로 감싼다)
 CFG L1406            style.setProperty(...)

 ★ 순회가 **둘**이다
   CMW L1206  case HostHoistable 도 같은 방식으로 숨긴다
   CMW L1219  hideOrUnhideNearestPortals — 포털은 따로 훑는다

 Suspense fallback 은 그 Offscreen 을 숨김으로 바꾸는 여러 이유 중 하나다
 ※ 그 경로 전체는 [커밋]과 [에러와 Suspense]에 있다
```

```text
 지우기 — removeChild 는 한 줄이다

 CFG L1206-1211  removeChild(parentInstance, child)
   L1210  parentInstance.removeChild(child)

 CFG L1213  removeChildFromContainer(container, child)
   L1218  container.nodeType === DOCUMENT_NODE 이면
   L1219    parentNode = container.body
   L1220  아니면 (주석 컨테이너 갈래)                 ** [DEAD] **
          [FLAG:disableCommentsAsDOMContainers=true]
   ...    아니면 parentNode = container

 ★ 컨테이너 갈래가 갈리는 이유는 루트가 document 일 수 있어서다.
   주석 노드를 컨테이너로 쓰는 갈래는 이 빌드에서 죽었다
```

```text
 ★★ 루트를 비울 때 통째로 지우지 않는다

 clearContainer  CFG L3671-3687
 L3672  nodeType = container.nodeType
 L3673  DOCUMENT_NODE 이면
 L3674    clearContainerSparingly(container)
 L3675  아니면 ELEMENT_NODE 이면
 L3676    switch (container.nodeName)
 L3677      case 'HEAD'
 L3678      case 'HTML'
 L3679      case 'BODY'
 L3680        clearContainerSparingly(container)
 L3681        return
 L3682      default
 L3683        container.textContent = ''      ★ 보통은 이 한 줄이다

 clearContainerSparingly  CFG L3689-3739
 L3691  nextNode = container.firstChild
 L3692  첫 자식이 DOCUMENT_TYPE_NODE 이면
 L3693    nextNode = nextNode.nextSibling    ★ doctype 을 안 지운다
 L3695  while (nextNode)
 L3698    switch (node.nodeName)
 L3699      'HTML' / 'HEAD' / 'BODY'
 L3705        detachDeletedInstance(element)  ★ 안으로 들어가되 **노드는 남긴다**
 L3723      'SCRIPT' / 'STYLE'
 L3725        continue                        ★ 남긴다
 L3728      'LINK'
 L3729        rel 이 'stylesheet' 이면
 L3732          continue                      ★ 남긴다
 L3736    container.removeChild(node)         그 밖은 지운다
```

```text
 ★ 무엇을 남기고 왜 남기는가

 주석 L3714-3722 가 이유를 적는다 (요지) -
   스트리밍 중 아직 안 닫힌 <script> 를 지우면 영영 실행되지 않고,
   <style> 은 서드파티 확장이 넣었을 가능성이 크다

 => 문서 전체를 루트로 쓰는 경우(SSR 하이드레이션 실패 복구 등)를 위한 장치다
 ※ 괄호 안은 내 짐작이다. 주석이 거기까지 말하지 않는다

 ★ 그리고 거의 같은 함수가 하나 더 있다 - clearHead (L3741)
   그쪽은 isMarkedHoistable(node) 인 것도 남긴다 (L3747)
```

## 결과가 쓰이는 곳

```text
 instance.style.display
      --> 숨김/보임의 실제 수단
      --> 되돌릴 때 props 의 값으로 간다. 기억해 두지 않는다

 textInstance.nodeValue
      --> 텍스트 노드는 빈 문자열로 숨긴다

 남겨진 script / style / link[rel=stylesheet] / doctype
      --> 루트를 비워도 살아남는다
```

## 다루지 않는 것

`hideOrUnhideAllChildren`(CMW L1185)과 `hideOrUnhideNearestPortals`(CMW L1219)의 순회 본문, Offscreen fiber 가 언제 숨김으로 바뀌는지([커밋](../../commit/README.md)과 [에러와 Suspense](../../throw/README.md)에 있다), `hideDehydratedBoundary` / `unhideDehydratedBoundary` 와 수화 경계의 숨김, `detachDeletedInstance`(CFG)가 fiber 포인터를 끊는 방식, `clearHead`(CFG L3741)와 `isMarkedHoistable`, `clearSuspenseBoundary` / `clearSuspenseBoundaryFromContainer`, 삭제 순회가 자식을 지우는 순서와 `commitDeletionEffects`([커밋](../../commit/README.md)에 있다), `STYLE` 상수의 정체는 이 문서의 범위 밖이다.
