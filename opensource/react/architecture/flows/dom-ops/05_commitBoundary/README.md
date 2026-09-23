# 커밋 경계

상위: [DOM 조작](../README.md)

DOM 을 바꾸기 직전과 직후에 하는 일. **브라우저 이벤트를 꺼 두고**, 포커스를 잃었으면 되돌린다. 다만 그 되돌리기가 흔히 생각하는 것보다 좁게 동작한다.

## 위치

앞 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L417-L429 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L417-L429))

뒤 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L450-L455 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L450-L455))

## 실제 코드

앞에서 저장하고 끈다.

```js
// ReactFiberConfigDOM.js L417-L429
export function prepareForCommit(containerInfo: Container): Object | null {
  eventsEnabled = ReactBrowserEventEmitterIsEnabled();
  selectionInformation = getSelectionInformation(containerInfo);
  let activeInstance = null;
  if (enableCreateEventHandleAPI) {
    const focusedElem = selectionInformation.focusedElem;
    if (focusedElem !== null) {
      activeInstance = getClosestInstanceFromNode(focusedElem);
    }
  }
  ReactBrowserEventEmitterSetEnabled(false);
  return activeInstance;
}
```

뒤에서 되돌리고 켠다.

```js
// ReactFiberConfigDOM.js L450-L455
export function resetAfterCommit(containerInfo: Container): void {
  restoreSelection(selectionInformation, containerInfo);
  ReactBrowserEventEmitterSetEnabled(eventsEnabled);
  eventsEnabled = null;
  selectionInformation = null;
}
```

이벤트는 엘리먼트가 아니라 **루트에 한 번** 붙는다. 포털이 두 번째 루트다.

```js
// ReactFiberConfigDOM.js L838-L840
export function preparePortalMount(portalInstance: Instance): void {
  listenToAllSupportedEvents(portalInstance);
}
```

## 동작 흐름

```text
 prepareForCommit  CFG L417-429

 L418  eventsEnabled = ReactBrowserEventEmitterIsEnabled()
 L419  selectionInformation = getSelectionInformation(containerInfo)
 L421  [FLAG:enableCreateEventHandleAPI=false]            ** [DEAD] **
 L422    focusedElem = selectionInformation.focusedElem
 L423    focusedElem !== null 이면
 L424      activeInstance = getClosestInstanceFromNode(focusedElem)
 L427  ReactBrowserEventEmitterSetEnabled(false)          ★ **이벤트를 끈다**
 L428  => return activeInstance

 ★ 플래그가 꺼져 있어 activeInstance 가 늘 null 이다.
   => 이 함수는 **언제나 null 을 돌려준다**

 resetAfterCommit  CFG L450-455
 L451  restoreSelection(selectionInformation, containerInfo)
 L452  ReactBrowserEventEmitterSetEnabled(eventsEnabled)
 L453  eventsEnabled = null
 L454  selectionInformation = null

 ★ 모듈 전역 둘을 쓰고 끝에서 null 로 되돌린다
```

```text
 ★★ 이벤트가 꺼져 있는 구간이 "변이 단계" 보다 넓다

 끄는 곳  CMW L348   focusedInstanceHandle = prepareForCommit(root.containerInfo)
          -> commitBeforeMutationEffects (CMW L343) 의 **첫 줄**이다
 켜는 곳  WL L4019   resetAfterCommit(root.containerInfo)
          -> flushMutationEffects (WL L3990) 안,
             L4012 commitMutationEffects 바로 다음 줄이다

 => 구간 = **before-mutation 시작 ~ mutation 끝**

 즉 getSnapshotBeforeUpdate 가 도는 동안에도 이벤트가 꺼져 있다.
 layout 이펙트와 패시브 이펙트는 그 밖이다

 ★ 끄는 파일과 켜는 파일이 다르다 (CommitWork / WorkLoop)
 ★ 감싸는 가드도 다르다 -
     들어갈 때  WL L3838-3844  BeforeMutationMask | MutationMask
     나올 때    WL L3999-4003  MutationMask
   앞엣것이 더 넓다 (Snapshot 비트가 더 있다).
   실제로 새는 경우를 나는 못 찾았지만, 대칭인 한 쌍은 아니다
```

```text
 ★★★ restoreSelection 은 흔한 경우에 아무 일도 안 한다

 ReactInputSelection.js L120-
 L121  curFocusedElem = getActiveElementDeep(containerInfo)
 L122  priorFocusedElem = priorSelectionInformation.focusedElem
 L124  **curFocusedElem !== priorFocusedElem** 이고 priorFocusedElem 이
       문서 안에 있으면
 L126    선택 범위가 있고 그 엘리먼트가 선택을 가질 수 있으면
 L129      setSelection(priorFocusedElem, priorSelectionRange)
 L133    조상들의 scrollLeft / scrollTop 을 모아 둔다
 L146    priorFocusedElem.focus()
          그리고 모아 둔 스크롤 위치를 되돌린다

 => 조건이 "**포커스가 실제로 옮겨갔을 때**" 다.
    보통 타이핑 중 리렌더에서는 포커스가 그대로라 아무 것도 안 한다

 문서주석 L118 이 목적을 밝힌다 -
   "...nodes and place them back in, resulting in focus being lost."
 => 이것은 **포커스 유실 복구** 경로다.
    React 가 포커스된 노드를 지웠다 다시 만들었을 때를 위한 것이다

 ★ 제어 입력의 캐럿이 안 튀는 것은 이것 때문이 아니다. 값 동기화 쪽 일이다
 ★ CFG L451 의 호출 자체는 조건 없이 일어난다. 조건은 함수 안에 있다
 ★ 그리고 선택만이 아니라 **조상들의 스크롤 위치**도 되돌린다
   주석 L132 - "Focusing a node can change the scroll position,
                which is undesirable"
```

```text
 ★★ 이벤트는 엘리먼트마다 안 붙는다. 루트에 한 번 붙는다

 ReactDOMRoot L258  createRoot   -> listenToAllSupportedEvents(rootContainerElement)
 ReactDOMRoot L357  hydrateRoot  -> listenToAllSupportedEvents(container)

 호스트 설정이 이것을 건드리는 자리는 하나뿐이다
 CFG L838-840  preparePortalMount(portalInstance)
                 listenToAllSupportedEvents(portalInstance)
 => 포털 컨테이너가 **두 번째 위임 루트**다

 그래서 [01]의 appendChild / insertBefore 가 이벤트 관련 일을 전혀 안 한다.
 노드를 옮겨도 리스너를 다시 달 필요가 없다
 (마지막 문장은 내 귀결이다)

 ★ 예외가 하나 있다 - 모바일 사파리 해킹
   CFG L1117-1124 (주석 L1109-1116, 이슈 #11918)
   L1124  trapClickOnNonInteractiveElement(parentNode)
   포털 밖으로 click 이 버블링되게 하려고 컨테이너에 빈 핸들러를 단다
```

```text
 ★ moveBefore 는 준비만 되어 있고 안 쓴다

 CFG L1019-1023
   const supportsMoveBefore =
     enableMoveBefore && typeof window !== 'undefined'
     && typeof window.Element.prototype.moveBefore === 'function'

 [FLAG:enableMoveBefore=false] 라 && 가 첫 항에서 끊긴다.
 => 기능 탐지조차 실행되지 않는다

 죽은 자리 다섯 - CFG L1029 / L1090 / L1102 / L1133 / L1162
 => 지금 react-dom 은 언제나 평범한 appendChild / insertBefore 를 쓴다
 (native-oss 포크에서만 true 다)
```

## 결과가 쓰이는 곳

```text
 반환 activeInstance
      --> 이 빌드에서 언제나 null 이다
      --> CMW 가 focusedInstanceHandle 에 담지만 쓰이지 않는다

 eventsEnabled / selectionInformation (모듈 전역)
      --> 커밋 한 번 동안만 산다. 끝에서 null 로 지운다

 ReactBrowserEventEmitterSetEnabled
      --> 이 구간에 들어온 브라우저 이벤트가 디스패치되지 않는다

 restoreSelection
      --> 포커스를 잃었을 때만 되돌린다
```

## 다루지 않는 것

`getSelectionInformation` / `getActiveElementDeep` / `hasSelectionCapabilities` / `setSelection`(`ReactInputSelection`)의 본문과 shadow DOM 을 뚫고 활성 엘리먼트를 찾는 방식, `ReactBrowserEventEmitterSetEnabled` 가 디스패치를 막는 실제 구현, `listenToAllSupportedEvents`(`DOMPluginEventSystem` L432)가 어떤 이벤트를 어떤 단계로 등록하는지와 합성 이벤트 전체, `trapClickOnNonInteractiveElement`(DOMC L371)와 모바일 사파리 이슈 #11918 의 내용, `enableCreateEventHandleAPI` 가 켜진 빌드(www)에서 `beforeActiveInstanceBlur` / `afterActiveInstanceBlur` 가 구간 중간에 이벤트를 다시 켜는 사정, `startViewTransition`(WL L3880)이 `flushMutationEffects` 를 콜백으로 넘겨 이 구간이 비동기로 늘어나는 경우는 이 문서의 범위 밖이다.
