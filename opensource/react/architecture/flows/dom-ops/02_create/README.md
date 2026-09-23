# 만들기

상위: [DOM 조작](../README.md)

`createInstance` 는 엘리먼트를 **만들기만** 한다. props 를 세우는 것은 다른 함수이고, 둘 다 커밋이 아니라 **completeWork** 에서 일어난다.

## 위치

만들기 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L527-L657 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L527-L657))

props 세우기 `packages/react-dom-bindings` / `src/client` / `ReactFiberConfigDOM.js` L696-L714 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-dom-bindings/src/client/ReactFiberConfigDOM.js#L696-L714))

## 실제 코드

`<script>` 를 만드는 법이 특이하다.

```js
// ReactFiberConfigDOM.js L566-L592
        case 'script': {
          // Create the script via .innerHTML so its "parser-inserted" flag is
          // set to true and it does not execute
          const div = ownerDocument.createElement('div');
          if (__DEV__) {
            if (
              enableTrustedTypesIntegration &&
              !didWarnScriptTags &&
              // Data block scripts are not executed by UAs anyway so
              // we don't need to warn: https://html.spec.whatwg.org/multipage/scripting.html#attr-script-type
              !isScriptDataBlock(props)
            ) {
              console.error(
                'Encountered a script tag while rendering React component. ' +
                  'Scripts inside React components are never executed when rendering ' +
                  'on the client. Consider using template tag instead ' +
                  '(https://developer.mozilla.org/en-US/docs/Web/HTML/Element/template).',
              );
              didWarnScriptTags = true;
            }
          }
          div.innerHTML = '<script><' + '/script>';
          // This is guaranteed to yield a script element.
          const firstChild = div.firstChild as any as HTMLScriptElement;
          domElement = div.removeChild(firstChild);
          break;
        }
```

> Create the script via .innerHTML so its "parser-inserted" flag is set to true and it does not execute

네임스페이스를 빠져나가는 자리는 하나뿐이다.

```js
// ReactFiberConfigDOM.js L388-L392
  if (parentNamespace === HostContextNamespaceSvg && type === 'foreignObject') {
    // We're leaving SVG.
    return HostContextNamespaceNone;
  }
  // By default, pass namespace below.
```

그리고 props 는 여기서 세워진다 — completeWork 가 부르는 자리다.

```js
// ReactDOMComponent.js L1468-L1477
  for (const propKey in props) {
    if (!props.hasOwnProperty(propKey)) {
      continue;
    }
    const propValue = props[propKey];
    if (propValue == null) {
      continue;
    }
    setProp(domElement, tag, propKey, propValue, props, null);
  }
```

## 동작 흐름

```text
 createInstance  CFG L527-657

 L535  [__DEV__]
 L538    validateDOMNesting(type, hostContextDev.ancestorInfo)
          ★ "<p> 안에 <div>" 같은 경고가 여기서 난다
 L544  ownerDocument = getOwnerDocumentFromRootContainer(rootContainerInstance)

 --- 네임스페이스: 두 단계로 정한다 ---
 L549  switch (hostContextProd)
 L550    case HostContextNamespaceSvg
 L551      createElementNS(SVG_NAMESPACE, type)
 L553    case HostContextNamespaceMath
 L554      createElementNS(MATH_NAMESPACE, type)
 L556    default
 L557      switch (type)
 L558        case 'svg'
 L559          createElementNS(SVG_NAMESPACE, type)
 L562        case 'math'
 L563          createElementNS(MATH_NAMESPACE, type)
 L566        case 'script'    ★ 아래 따로 적는다
 L593        case 'select'
 L594          typeof props.is === 'string' 이면
 L595            createElement('select', {is: props.is})
 L596          아니면
 L600            createElement('select')
                주석 L597-599 가 파이어폭스 버그 둘을 링크한다

 --- fiber 와 잇는다 ---
 L654  precacheFiberNode(internalInstanceHandle, domElement)
 L655  updateFiberProps(domElement, props)
 L656  => return domElement
```

```text
 ★★ 바깥 switch 가 먼저라 안쪽 case 가 늘 사는 것이 아니다

 L549 의 `switch (hostContextProd)` 가 먼저 맞으므로
 안쪽 `case 'svg'`(L558)와 `case 'math'`(L562)는
 **부모 컨텍스트가 None 일 때만** 닿는다

 => `<svg>` 안의 `<math>` 는 L563 이 아니라 **L551 에서 SVG 네임스페이스로** 만들어진다

 네임스페이스를 빠져나가는 자리는 하나뿐이다 (CFG L388-391)
   parentNamespace 가 Svg 이고 type 이 'foreignObject' 이면
   HostContextNamespaceNone 을 돌려준다
 그 밖에는 L393 - "By default, pass namespace below."
```

```text
 ★★★ script 를 innerHTML 로 만드는 이유

 L587  div.innerHTML = '<script><' + '/script>'
 L589  firstChild = div.firstChild
 L590  domElement = div.removeChild(firstChild)

 주석 L567-568 - "Create the script via .innerHTML so its "parser-inserted"
 flag is set to true and it does not execute"

 => createElement('script') 로 만들면 DOM 에 넣는 순간 **실행된다**.
    파서가 만든 것처럼 위장해 실행을 막는다

 DEV 는 따로 경고도 한다 (L578-583)
 다만 조건이 셋이다 (L571-577) -
   enableTrustedTypesIntegration 이 켜져 있고 (이 빌드에서 true)
   didWarnScriptTags 가 아직 false 이고 (L584 에서 켜니 **한 번만**)
   isScriptDataBlock(props) 가 아니어야 한다
   => type="application/json" 같은 데이터 블록은 면제다
```

```text
 ★★ props 는 여기서 안 세운다. completeWork 에서 세운다

 CFG L696  finalizeInitialChildren(domElement, type, props, hostContext)
 CFG L702    setInitialProperties(domElement, type, props)
 CFG L703    switch (type) 로 **불린 하나**를 돌려준다
 CFG L704-708  button / input / select / textarea 이면 !!props.autoFocus
 CFG L709-710  img 이면 true
 CFG L711-712  그 밖이면 false

 ★ 그 불린이 "커밋 때 commitMount 를 불러 달라" 는 뜻이다.
   autoFocus 와 img 만 마운트 시점에 할 일이 남는다
   ※ 뒷문장은 내가 반환값의 쓰임을 보고 적은 것이다

 이 함수를 부르는 것이 [completeWork] 다.
 즉 **만들기도 props 세우기도 렌더 단계**에서 끝나고,
 커밋은 **이미 완성된 노드를 붙이기만** 한다

 => 그래서 커밋의 변이 패스가 짧다
    (마지막 문장은 내 판단이다)
```

```text
 ★ 세우는 쪽은 루프가 하나다 — 갱신 쪽 둘과 대비된다

 setInitialProperties  DOMC L1468-1477
   L1468  for (const propKey in props)
   L1476    setProp(domElement, tag, propKey, propValue, props, null)

 [03]의 갱신은 루프가 둘이다 (지우기 + 세우기).
 마운트는 지울 것이 없으니 하나로 족하다

 ★ 그리고 **특별 태그 집합이 다르다**.
   setInitialProperties 의 switch(L1093-1478)는
   dialog / iframe / object / video / audio / image / details 를 따로 다루는데,
   updateProperties 의 switch 에는 그 태그들이 없다
   => 마운트에만 있는 관심사다 (load·error 리스너, toggle 등)
   ※ 각 태그가 무엇을 하는지는 안 읽었다
```

```text
 ★ DOM 에서 fiber 로 돌아오는 다리가 둘이다

 L654  precacheFiberNode(internalInstanceHandle, domElement)
         => DOM 노드에서 fiber 를 찾는 길
 L655  updateFiberProps(domElement, props)
         => DOM 노드에서 **지금 렌더의 props** 를 찾는 길

 같은 짝이 createHoistableInstance 에도 있다 (L468-472)
 그리고 갱신 쪽 짝이 [03] commitUpdate L1004 다

 이 둘이 없으면 루트에 위임된 이벤트가 어느 컴포넌트의 핸들러를
 불러야 할지 알 수 없다
 (마지막 문장은 내가 [05]의 이벤트 위임과 맞춰 보고 적은 것이다)
```

## 결과가 쓰이는 곳

```text
 반환 domElement
      --> fiber.stateNode 가 된다
      --> [completeWork]의 appendInitialChild 가 부모에 미리 붙인다
      --> 커밋의 [01]이 그 서브트리 꼭대기만 한 번 넣는다

 precacheFiberNode / updateFiberProps
      --> 이벤트 위임이 DOM 노드에서 fiber 와 props 를 찾는다

 호스트 컨텍스트
      --> 자식의 네임스페이스를 정한다
```

## 다루지 않는 것

`setInitialProperties`(DOMC L1093-1478)의 태그별 분기 전체와 `setProp` 이 개별 속성을 세우는 규칙(`style` / `dangerouslySetInnerHTML` / 이벤트 prop / 불린 속성), `validateDOMNesting` 의 규칙표와 `ancestorInfo` 의 구성, `getOwnerDocumentFromRootContainer` 와 여러 document 를 다루는 사정, `precacheFiberNode` / `updateFiberProps`(`ReactDOMComponentTree`)가 DOM 노드의 어느 키에 저장하는지, `createTextInstance`(CFG L750)와 `createHoistableInstance`(CFG L457), 호이스터블·리소스 계열이 `<head>` 로 끌어올려지는 별도 경로, `isScriptDataBlock`(CFG L476)의 판정, `select` 의 파이어폭스 버그 두 건의 내용은 이 문서의 범위 밖이다.
