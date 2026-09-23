# 갱신

상위: [DOM 조작](../README.md)

props 두 개를 비교해 DOM 속성을 고친다. **진짜 diff 는 스무 줄**인데, 거기에 닿는 태그가 생각보다 적다.

## 위치

진입 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L992-L1005 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L992-L1005))

본체 `packages/react-dom-bindings` / `src/client` / `ReactDOMComponent.js` L1480-L1985 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactDOMComponent.js#L1480-L1985))

## 실제 코드

진입은 다섯 줄이다.

```js
// ReactFiberConfigDOM.js L992-L1005
export function commitUpdate(
  domElement: Instance,
  type: string,
  oldProps: Props,
  newProps: Props,
  internalInstanceHandle: Object,
): void {
  // Diff and update the properties.
  updateProperties(domElement, type, oldProps, newProps);

  // Update the props handle so that we know which props are the ones with
  // with current event handlers.
  updateFiberProps(domElement, newProps);
}
```

> Update the props handle so that we know which props are the ones **with with** current event handlers.

흔한 태그 여덟은 그냥 통과한다.

```js
// ReactDOMComponent.js L1491-L1501
    case 'div':
    case 'span':
    case 'svg':
    case 'path':
    case 'a':
    case 'g':
    case 'p':
    case 'li': {
      // Fast track the most common tag types
      break;
    }
```

그리고 이것이 diff 전부다. switch 가 닫힌 **뒤**에 있다.

```js
// ReactDOMComponent.js L1964-L1984
  for (const propKey in lastProps) {
    const lastProp = lastProps[propKey];
    if (
      lastProps.hasOwnProperty(propKey) &&
      lastProp != null &&
      !nextProps.hasOwnProperty(propKey)
    ) {
      setProp(domElement, tag, propKey, null, nextProps, lastProp);
    }
  }
  for (const propKey in nextProps) {
    const nextProp = nextProps[propKey];
    const lastProp = lastProps[propKey];
    if (
      nextProps.hasOwnProperty(propKey) &&
      nextProp !== lastProp &&
      (nextProp != null || lastProp != null)
    ) {
      setProp(domElement, tag, propKey, nextProp, nextProps, lastProp);
    }
  }
```

## 동작 흐름

```text
 commitUpdate  CFG L992-1005

 L1000  updateProperties(domElement, type, oldProps, newProps)
 L1004  updateFiberProps(domElement, newProps)
         주석 L1002-1003 - "Update the props handle so that we know which
         props are the ones with with current event handlers."
         ★ 원문에 "with with" 오타가 있다

 => 둘째 줄이 없으면 루트에 위임된 이벤트가 **지난 렌더의 핸들러**를 부른다
    ([05]의 이벤트 위임과 짝이다)
```

```text
 updateProperties  DOMC L1480-1985 — switch 가 일곱 갈래다

 L1490  switch (tag)

 L1491    'div' 'span' 'svg' 'path' 'a' 'g' 'p' 'li'
 L1500      break                    ★ 아래 공통 루프로 **떨어진다**
             주석 L1499 - "Fast track the most common tag types"

 L1502    'input'     지역변수 일곱. 자기 루프 둘. L1651 updateInput
 L1661      return                   ★ **공통 루프에 안 간다**
 L1663    'select'    L1737 updateSelect / L1738 return
 L1740    'textarea'  L1816 updateTextarea / L1817 return
 L1819    'option'                      L1865 return
 L1867    'img' 'link' 'area' 'base' 'br' 'col' 'embed' 'hr' 'keygen'
          'meta' 'param' 'source' 'track' 'wbr' 'menuitem'
 L1920      return                   ★ void 엘리먼트 묶음
 L1922    default
 L1923      isCustomElement(tag, nextProps) 이면
 L1959        return                 ★ 커스텀 엘리먼트도 안 간다
             아니면 아래로 떨어진다

 L1962  switch 가 닫힌다

 --- 공통 diff ---
 L1964  for (const propKey in lastProps)
 L1966    조건 (L1967-1969)
            lastProps.hasOwnProperty(propKey)
            && lastProp != null
            && !nextProps.hasOwnProperty(propKey)
 L1971      setProp(domElement, tag, propKey, **null**, nextProps, lastProp)

 L1974  for (const propKey in nextProps)
 L1977    조건 (L1978-1980)
            nextProps.hasOwnProperty(propKey)
            && **nextProp !== lastProp**
            && (nextProp != null || lastProp != null)
 L1982      setProp(domElement, tag, propKey, nextProp, nextProps, lastProp)
```

```text
 ★★★ 공통 diff 에 닿는 태그가 둘뿐이다

 빠른 통과 여덟(L1500 의 break)과 default 의 비-커스텀 갈래.
 그 밖은 전부 **자기 case 안에서 return 한다**
   input L1661 / select L1738 / textarea L1817 / option L1865
   void 묶음 L1920 / 커스텀 엘리먼트 L1959

 => "React 의 DOM diff" 라고 부를 만한 것은 이 스무 줄인데,
    제어 컴포넌트 넷은 그 길을 안 탄다. 자기 방식으로 따로 돈다
```

```text
 ★★ diff 가 하는 일이 둘뿐이다

 (1) L1964-1973  옛것에 있었는데 새것에 **없어진** prop 을 null 로 setProp
 (2) L1974-1984  새것에서 **바뀐** prop 을 새 값으로 setProp

 => 가상 DOM 트리를 비교하는 것이 아니라 **props 객체 두 개**를 비교한다.
    트리 비교는 이미 [자식 조정]에서 끝났다

 ★ (2)의 `nextProp !== lastProp` 가 안 바뀐 prop 을 건너뛴다.
   (1)에는 그 조건이 없다 - 없어진 것만 보므로 필요 없다
 ★ 둘 다 `hasOwnProperty` 를 먼저 본다. 프로토타입 체인의 것을 세지 않는다
```

```text
 ★ 빠른 통과 여덟은 "diff 를 건너뛴다" 가 아니다

 L1500 은 return 이 아니라 **break** 다.
 특별 처리(제어 컴포넌트 동기화 등)를 건너뛰고 공통 diff 로 간다

 주석 L1499 - "Fast track the most common tag types"
 => switch 를 끝까지 내려가며 비교하는 비용을 아끼려는 것이다
    (뒷문장은 내 판단이다)
```

```text
 ★ void 엘리먼트 묶음은 제어 컴포넌트가 아니다. 던지려고 있다

 L1867-1881 의 열다섯 태그는 자식을 가질 수 없다.
 그래서 children 이나 dangerouslySetInnerHTML 이 오면 던진다
   DOMC L1906-1909 부근
     `${tag} is a void element tag and must neither have `children` nor
      use `dangerouslySetInnerHTML`.`
 ※ 정확한 줄은 L1902-1912 의 switch 안이다
```

```text
 ★ 커스텀 엘리먼트는 비교 기준이 다르다

 L1923  isCustomElement(tag, nextProps) 이면
 L1928  `lastProp !== undefined` 로 본다   ★ null 이 아니라 undefined 다
        그리고 setProp 이 아니라 setPropOnCustomElement 를 쓴다

 => 커스텀 엘리먼트에서는 null 이 의미 있는 값일 수 있어서로 보인다
    ※ 주석이 없다. 내 추측이다
```

```text
 ★ 이 경로만 변이 기록을 스스로 한다

 CHE 의 래퍼 대부분이 trackHostMutation 을 부르는데
 commitHostUpdate 만 안 부른다
   CHE L141 주석 - "Mutations are tracked manually from within commitUpdate."

 대신 DOMC 안에서 prop 하나가 실제로 바뀔 때마다 부른다
 => 아무 것도 안 바뀐 갱신은 변이로 기록되지 않는다
 ※ DOMC 쪽 호출 자리는 세지 않았다
```

## 결과가 쓰이는 곳

```text
 DOM 속성 그 자체
      --> 이 흐름의 끝이다

 updateFiberProps 가 갱신한 props
      --> 이벤트 위임이 이번 렌더의 핸들러를 찾는다

 updateInput / updateSelect / updateTextarea
      --> 제어 컴포넌트의 value 동기화. 공통 diff 와 별개다
```

## 다루지 않는 것

`setProp`(DOMC)이 속성 하나를 세우는 규칙 전체 — `style` 객체 diff, `dangerouslySetInnerHTML`, 이벤트 prop 이 리스너로 등록되지 않고 props 에만 담기는 것, 불린 속성과 `removeAttribute` 의 판정 —, 제어 컴포넌트 넷의 `updateInput` / `updateSelect` / `updateTextarea`(`ReactDOMInput` 등)와 `restoreControlledState`(DOMC L3374), `isCustomElement` / `setPropOnCustomElement` 의 규칙, `validatePropertiesInDevelopment`(DOMC L1487)의 DEV 검사, `trackHostMutation` 을 DOMC 안에서 부르는 자리들, `updateProperties` 가 `input` 에서 쓰는 지역변수 일곱의 의미는 이 문서의 범위 밖이다.
