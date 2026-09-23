# 칸 서른셋

상위: [Fiber 라는 자료구조](../README.md)

Fiber 타입 전문이 121줄인데 그중 절반이 주석이다. 그 주석들이 이 지도가 여기저기서 쓰던 칸들의 **원래 뜻**을 적어 둔다.

## 위치

`packages/react-reconciler` / `src` / `ReactInternalTypes.js` L89-L210 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactInternalTypes.js#L89-L210))

## 실제 코드

앞머리 다섯은 "인스턴스" 에 속한다는 단서가 붙어 있다.

```js
// ReactInternalTypes.js L100-L131
  // Tag identifying the type of fiber.
  tag: WorkTag,

  // Unique identifier of this child.
  key: ReactKey,

  // The value of element.type which is used to preserve the identity during
  // reconciliation of this child.
  elementType: any,

  // The resolved function/class/ associated with this fiber.
  type: any,

  // The local state associated with this fiber.
  stateNode: any,

  // Conceptual aliases
  // parent : Instance -> return The parent happens to be the same as the
  // return fiber since we've merged the fiber and instance.

  // Remaining fields belong to Fiber

  // The Fiber to return to after finishing processing this one.
  // This is effectively the parent, but there can be multiple parents (two)
  // so this is only the parent of the thing we're currently processing.
  // It is conceptually the same as the return address of a stack frame.
  return: Fiber | null,

  // Singly Linked List Tree Structure.
  child: Fiber | null,
  sibling: Fiber | null,
  index: number,
```

> An Instance is shared between all versions of a component. We can easily break this out into a separate object to avoid copying so much to the alternate versions of the tree. We put this on a single object **for now** to minimize the number of objects created during the initial render.

> This is effectively the parent, but there can be multiple parents (two) so this is only the parent of the thing we're currently processing. It is conceptually the same as **the return address of a stack frame**.

뒷머리는 렌더마다 바뀌는 것들이다.

```js
// ReactInternalTypes.js L155-L174
  // Bitfield that describes properties about the fiber and its subtree. E.g.
  // the ConcurrentMode flag indicates whether the subtree should be async-by-
  // default. When a fiber is created, it inherits the mode of its
  // parent. Additional flags can be set at creation time, but after that the
  // value should remain unchanged throughout the fiber's lifetime, particularly
  // before its child fibers are created.
  mode: TypeOfMode,

  // Effect
  flags: Flags,
  subtreeFlags: Flags,
  deletions: Array<Fiber> | null,

  lanes: Lanes,
  childLanes: Lanes,

  // This is a pooled version of a Fiber. Every fiber that gets updated will
  // eventually have a pair. There are cases when we can clean up pairs to save
  // memory if we need to.
  alternate: Fiber | null,
```

> This is a **pooled** version of a Fiber. Every fiber that gets updated will eventually have a pair. There are cases when we can clean up pairs to save memory **if we need to**.

## 동작 흐름

```text
 (가) 인스턴스에 속하는 것  L100-114

 L101  tag           WorkTag. 이 fiber 가 무엇인가
 L104  key           ReactKey
 L108  elementType   element.type 원본
                     주석 L106-107 - "which is used to preserve the identity
                                     during reconciliation of this child"
 L111  type          해소된 함수/클래스
 L114  stateNode     지역 상태

 ★ elementType 과 type 이 따로 있는 이유가 L106-107 이다.
   lazy 나 memo 는 감싼 것과 해소된 것이 다르다
   ([자식 조정]이 재사용을 판정할 때 elementType 을 본다)
   (괄호 안은 내가 흐름 11 과 맞춰 본 것이다)

 ★ stateNode 가 담는 것이 tag 마다 다르다
     HostComponent  -> DOM 노드
     ClassComponent -> 인스턴스
     HostRoot       -> FiberRoot
   (이 목록은 내가 다른 흐름들에서 모은 것이고 주석에 없다)
```

```text
 (나) 트리  L122-131

 L126  return    부모. 주석이 "복귀 주소" 라 부른다
 L129  child
 L130  sibling
 L131  index

 주석 L128 - "Singly Linked List Tree Structure."
 => 자식 배열이 없다. child 하나 + sibling 사슬이다
 => 그래서 순회가 언제나 "내려갔다 옆으로 갔다 올라온다" 모양이 된다
    ([렌더 루프]의 work loop 가 그것이다)
    (마지막 줄은 내 귀결이다)
```

```text
 (다) ref  L133-140
 L135  ref          함수이거나 객체이거나 (문자열 ref 타입이 아직 남아 있다)
 L140  refCleanup   함수 ref 가 돌려준 cleanup ([DOM 조작]에 있다)

 (라) 들어오는 것과 나가는 것  L142-153
 L143  pendingProps   주석 L142 - "Input is the data coming into process this
                                  fiber. Arguments. Props."
 L144  memoizedProps  주석 - "The props used to create the output."
 L147  updateQueue    주석 L146 - "A queue of state updates and callbacks."
 L150  memoizedState  주석 L149 - "The state used to create the output"
 L153  dependencies   주석 L152 - "Dependencies (contexts, events) for this
                                  fiber, if it has any"

 ★ pending 과 memoized 의 짝이 이 자료구조의 리듬이다.
   "이번에 들어온 것" 과 "지난번에 쓴 것" 을 나란히 들고 있어야
   바이아웃 판정이 가능하다
   (이 문장은 내 판단이다)
```

```text
 (마) 모드  L161

 L161  mode: TypeOfMode

 주석 L155-160 이 세 가지를 말한다
   "Bitfield that describes properties about the fiber and its subtree. E.g.
    the ConcurrentMode flag indicates whether the subtree should be async-by-
    default. When a fiber is created, it inherits the mode of its parent.
    Additional flags can be set at creation time, but after that the value
    should remain unchanged throughout the fiber's lifetime, particularly
    before its child fibers are created."

 ★ 부모에게서 물려받고, 만든 뒤에는 **바뀌지 않아야 한다**
 ★ 그래서 [02]의 createWorkInProgress 가 mode 를 복사만 하고 안 건드린다
```

```text
 (바) 이펙트와 우선순위  L163-169

 L164  flags         이 fiber 에 할 일
 L165  subtreeFlags  서브트리에 할 일이 있나 (올라오며 모은다)
 L166  deletions     지울 자식들
 L168  lanes         이 fiber 의 남은 일
 L169  childLanes    자식들의 남은 일

 ★ 둘씩 짝이다 - 자기 것과 서브트리 것.
   그래야 커밋과 렌더가 서브트리를 통째로 건너뛸 수 있다
   ([completeWork]의 bubbleProperties 가 subtreeFlags 를 모은다)
   (이 문장은 내 귀결이다)
```

```text
 (사) 짝  L171-174

 L174  alternate

 주석 L171-173 - "This is a pooled version of a Fiber. Every fiber that gets
   updated will eventually have a pair. There are cases when we can clean up
   pairs to save memory if we need to."

 주석 L198-199 - "workInProgress : Fiber ->  alternate  The alternate used for
   reuse happens to be the same as work in progress."

 ★ "pooled" 라는 말이 핵심이다. 새로 만드는 것이 아니라 **돌려쓴다**
 ★ 그리고 갱신된 적 없는 fiber 는 짝이 **없다** ("will eventually have")
```

```text
 (아) 선택 필드 열  L176-209

 프로파일러 넷  [FLAG:enableProfilerTimer]
   L180 actualDuration    L185 actualStartTime
   L190 selfBaseDuration  L195 treeBaseDuration
   주석 L177-178 - "This tells us how well the tree makes use of sCU for
                    memoization."
   주석 L192-193 - treeBaseDuration 은 "bubbles up during the complete phase"

 DEV 여섯  L202-209
   _debugInfo _debugOwner _debugStack _debugTask
   _debugNeedsRemount _debugHookTypes
   주석 L208 - _debugHookTypes 는 "Used to verify that the order of hooks does
               not change between renders."
```

```text
 ★ 앞머리 다섯을 왜 나누지 않았는지 주석이 적는다  L90-98

 "These first fields are conceptually members of an Instance. This used to be
  split into a separate type and intersected with the other Fiber fields, but
  until Flow fixes its intersection bugs, we've merged them into a single type."

 "An Instance is shared between all versions of a component. We can easily
  break this out into a separate object to avoid copying so much to the
  alternate versions of the tree. We put this on a single object for now to
  minimize the number of objects created during the initial render."

 => 이유가 둘이다 - Flow 의 교집합 버그, 그리고 초기 렌더의 객체 수
 ★ "for now" 와 "if we need to" 같은 한정어가 이 타입에 유독 많다
```

## 결과가 쓰이는 곳

```text
 tag
      --> 세 개의 큰 switch 가 본다 (beginWork / completeWork / unwind)

 elementType vs type
      --> [자식 조정]이 재사용 판정에 elementType 을 쓴다

 pendingProps / memoizedProps
      --> 바이아웃 판정의 두 축 중 하나

 flags / subtreeFlags
      --> [커밋]이 서브트리를 건너뛸지 정한다

 alternate
      --> [02]가 그것으로 짝을 만들고 돌려쓴다
```

## 다루지 않는 것

`WorkTag`(`ReactWorkTags.js`)의 전체 목록과 각 tag 의 뜻([beginWork](../../begin-work/spi/README.md)의 표에 있다), `TypeOfMode`(`ReactTypeOfMode.js`)의 비트 구성과 `ConcurrentMode` / `StrictLegacyMode` / `ProfileMode` 가 붙는 자리, `Flags`(`ReactFiberFlags.js`)의 비트 배치와 `StaticMask` 의 구성([02](../02_workInProgress/README.md)에서 쓰임만 다룬다), `ReactKey` / `RefObject` / `Dependencies` / `MemoCache` / `HookType` 타입, `FiberRoot`(TYPES L386-392)과 그 조각 다섯이 담는 필드, `Dispatcher`(TYPES L397)의 메서드 목록과 훅 디스패처 테이블의 대응, `ReactDebugInfo` / `ReactComponentInfo` 같은 DEV 타입은 이 문서의 범위 밖이다.
