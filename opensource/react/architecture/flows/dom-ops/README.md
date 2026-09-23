# DOM 조작

상위: [React 아키텍처 지도](../../README.md)

리콘실러가 실제로 DOM 에 닿는 자리다. 파일 둘이 1만 줄이라 **리콘실러가 부르는 진입점으로 잘라** 읽었다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 약어: `CHE` = `ReactFiberCommitHostEffects.js`(833줄, 리콘실러), `CFG` = `ReactFiberConfigDOM.js`(6693줄), `DOMC` = `ReactDOMComponent.js`(3390줄), `CMW` = `ReactFiberCommitWork.js`, `CW` = `ReactFiberCompleteWork.js`, `WL` = `ReactFiberWorkLoop.js`.

## 이음매가 넷이다

```text
 [커밋]  CMW                  트리를 순회한다
    |
    +--> [커밋 이펙트] CE       **사용자** 코드를 부른다      (흐름 15)
    |
    +--> CHE                  **호스트** 코드를 부른다      <- 리콘실러 쪽 끝
           |
           +--> CFG / DOMC    실제 DOM 을 만진다            <- react-dom 쪽

 CE 와 CHE 가 쌍둥이다. 이름도 한 글자 차이다
 앞엣것은 useEffect 와 componentDidMount 를, 뒤엣것은 appendChild 를 부른다
 (쌍둥이라는 표현은 내가 붙인 것이다)
```

```text
 ★ 호스트 설정 계약의 크기

 리콘실러가 './ReactFiberConfig' 에서 가져오는 **값** 이름이 164 개
 (타입까지 더하면 188 개. 아래 숫자는 전부 값 기준이다)

 가져가는 쪽이 성격으로 갈린다
   CW  (completeWork)  24 개   **만들기**
       createInstance, createTextInstance, appendInitialChild,
       finalizeInitialChildren, preloadInstance ...
   CHE (커밋 호스트)    29 개   **변이**
       commitUpdate, commitMount, appendChild, insertBefore,
       removeChild, hideInstance, unhideInstance, resetTextContent ...
   CMW (커밋 순회)      30 개   **컨테이너·리소스**
       prepareForCommit, clearContainer, acquireResource,
       suspendInstance, beforeActiveInstanceBlur ...

 => 만드는 것은 렌더 단계(completeWork)에서, 붙이는 것은 커밋에서.
    두 단계가 가져가는 이름이 겹치지 않는다
```

1. [붙일 자리 찾기](01_placement/README.md) — `getHostSibling` 과 `commitPlacement`.
2. [만들기](02_create/README.md) — `createInstance`. `<script>` 를 실행되지 않게 만드는 법.
3. [갱신](03_update/README.md) — `updateProperties`. 진짜 diff 는 스무 줄이다.
4. [숨기고 지우기](04_hideAndClear/README.md) — `display:none !important`, 컨테이너 비우기.
5. [커밋 경계](05_commitBoundary/README.md) — 이벤트를 끄고 선택을 되돌린다.

```text
 ★★ 이 빌드에서 죽어 있는 갈래들 — 먼저 밝혀 둔다

 supportsMutation      = true   CFG L882
 supportsSingletons    = true   CFG L4643
 supportsResources     = true   CFG L4770
 supportsHydration     = true   CFG L3779
 supportsPersistence   = false  ReactFiberConfigWithNoPersistence L22

 => react-dom 은 **변이 모드**다. 영속 모드가 아니다
    CW 가 가져가는 cloneInstance / createContainerChildSet 계열은 [DEAD]
    CHE L521-529 의 `if (!supportsMutation)` 블록도 [DEAD]

 enableMoveBefore               = false  FLAGS L181
 enableCreateEventHandleAPI     = false  FLAGS L56
 disableCommentsAsDOMContainers = true   FLAGS L210
 enableFragmentRefs             = true   FLAGS L152
 enableTrustedTypesIntegration  = true   FLAGS L212

 => moveBefore 갈래가 전부 [DEAD] ([01]에 있다)
 => prepareForCommit 은 언제나 null 을 돌려준다 ([05]에 있다)
 => 주석 노드를 컨테이너로 쓰는 갈래가 전부 [DEAD]
```

## 어디로 이어지는가

```text
 [completeWork]  createInstance / appendInitialChild 로 서브트리를 미리 조립한다
                 => 커밋 때는 **이미 만들어진 것을 한 번만 붙인다**

 [커밋]          변이 패스가 CHE 를 부른다
                 Placement / Update / Deletion / Visibility 플래그가 무엇을 부를지 정한다

 [커밋 이펙트]    같은 순회에서 사용자 코드를 부른다. 이 흐름과 나란히 간다

 [에러와 Suspense]  숨기는 것이 언마운트가 아니라 display:none 이다 ([04])
```

## 결과가 쓰이는 곳

```text
 fiber.stateNode
      --> 호스트 fiber 에 붙은 실제 DOM 노드
      --> getHostSibling 이 돌려주는 것도 이것이다

 DOM 그 자체
      --> 이 흐름의 끝이다. 여기서부터는 브라우저의 일이다

 selectionInformation / eventsEnabled (CFG 의 모듈 전역)
      --> 커밋 전후로 저장했다 되돌린다
```

## 다루지 않는 것

`setInitialProperties`(DOMC L1093)가 마운트 때 props 를 세우는 전체 경로, 리소스·호이스터블 계열(`getHoistableRoot` / `acquireResource` / `mountHoistable` / `preloadResource` — `<link>` `<meta>` 같은 것을 `<head>` 로 끌어올리는 구조), `suspendInstance` / `suspendResource` 와 이미지 프리로드가 커밋을 미루는 경로, 이벤트 시스템(`react-dom-bindings` 의 합성 이벤트)이 루트에 붙는 자리, 수화(hydration) 계열(`hydrateProperties` / `diffHydratedProperties` / `hydrateText`), `setProp`(DOMC)이 개별 속성을 세우는 규칙과 `dangerouslySetInnerHTML` / `style` 의 처리, 제어 컴포넌트 넷(`input` / `select` / `textarea` / `option`)의 `updateWrapper` 계열, `validateDOMNesting` 의 규칙표, `HostSingleton` 과 `HostHoistable` tag 의 전체 수명은 이 문서의 범위 밖이다.

## 하위 메서드

- [01 붙일 자리 찾기](01_placement/README.md)
- [02 만들기](02_create/README.md)
- [03 갱신](03_update/README.md)
- [04 숨기고 지우기](04_hideAndClear/README.md)
- [05 커밋 경계](05_commitBoundary/README.md)
