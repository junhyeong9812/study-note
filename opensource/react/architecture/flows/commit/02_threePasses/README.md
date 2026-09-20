# 세 패스

상위: [커밋 흐름](../README.md)

before-mutation / mutation / layout 이다. **셋이 보는 flags 가 다르고, 순회 방식도 다르고, 트리 교체가 뒤의 둘 사이에 끼어 있다.**

## 위치

mutation `packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L3990-L4034 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L3990-L4034))

layout `packages/react-reconciler` / `src` / `ReactFiberWorkLoop.js` L4036-L4133 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberWorkLoop.js#L4036-L4133))

## 실제 코드

트리를 바꿔 다는 자리와 그 위 주석.

```js
// ReactFiberWorkLoop.js L4028-L4033
  // The work-in-progress tree is now the current tree. This must come after
  // the mutation phase, so that the previous tree is still current during
  // componentWillUnmount, but before the layout phase, so that the finished
  // work is current during componentDidMount/Update.
  root.current = finishedWork;
  pendingEffectsStatus = PENDING_LAYOUT_PHASE;
```

> The work-in-progress tree is now the current tree. This **must** come after the mutation phase, so that the previous tree is **still** current during `componentWillUnmount`, but before the layout phase, so that the finished work is current during `componentDidMount/Update`.

props diff 는 mutation 패스에서 일어난다.

```js
// ReactFiberCommitWork.js L2244-L2256
        if (flags & Update) {
          const instance: Instance = finishedWork.stateNode;
          if (instance != null) {
            // Commit the work prepared earlier.
            // For hydration we reuse the update path but we treat the oldProps
            // as the newProps. The updatePayload will contain the real change in
            // this case.
            const newProps = finishedWork.memoizedProps;
            const oldProps =
              current !== null ? current.memoizedProps : newProps;
            commitHostUpdate(finishedWork, newProps, oldProps);
          }
        }
```

## 대조표

| | before-mutation | mutation | layout |
|---|---|---|---|
| 진입 | `commitBeforeMutationEffects` WL L3855 | `commitMutationEffects` WL L4012 | `commitLayoutEffects` WL L4106 |
| 순회 | 모듈 전역 `nextEffect` + `_begin`/`_complete` (CW L364 / L456) | `.child`/`.sibling` 재귀 (CW L2016) | `.child`/`.sibling` 재귀 (CW L2995) |
| 마스크 | `BeforeMutationMask` | `MutationMask` **+ `Cloned`** (CW L2031) | `LayoutMask` (CW L3000) |
| 삭제 | 플래그가 켜졌을 때만 (CW L375) | **여기서 전부 처리** (CW L2027) | 안 본다 |
| 사용자 코드 | `getSnapshotBeforeUpdate` | `componentWillUnmount`, `useLayoutEffect` cleanup, `useInsertionEffect` | `componentDidMount`, `useLayoutEffect` 콜백, ref 붙이기 |

```text
 ★ 트리 교체가 정확히 가운데 있다

 WL L4012  commitMutationEffects(...)     여기서 componentWillUnmount 가 돈다
 WL L4032  root.current = finishedWork
 WL L4033  pendingEffectsStatus = PENDING_LAYOUT_PHASE
 WL L4106  commitLayoutEffects(...)       여기서 componentDidMount 가 돈다

 layout 패스는 PENDING_LAYOUT_PHASE 일 때만 도는데
 그 값을 세우는 유일한 자리가 L4033 이다
 => 상태 기계가 "교체 뒤에 layout" 을 물리적으로 강제한다

 그래서 주석의 말이 코드로 지켜진다
   언마운트하는 컴포넌트는 옛 트리를 보고
   마운트하는 컴포넌트는 새 트리를 본다
```

```text
 ★ 그리고 이 줄은 if 밖이다

 WL L4003  if (subtreeMutationHasEffects || rootMutationHasEffect) {
 WL L4010    try {
 WL L4012      commitMutationEffects(...)
 WL L4020    } finally {
 WL L4025    }          <- finally 닫힘
 WL L4026  }            <- if 닫힘
 WL L4032  root.current = finishedWork;

 들여쓰기가 말해 준다 - L4032 는 2칸이고 if 본문은 4칸이다

 => 바꿀 mutation 효과가 하나도 없어도 트리 교체는 일어난다
    "교체" 는 효과가 아니라 커밋의 정의 자체이기 때문이다
```

```text
 useLayoutEffect 가 두 패스에 걸쳐 있다

 cleanup(destroy)  mutation 패스   CW L2091
 콜백(create)      layout 패스     CW L614

 즉 옛 효과를 먼저 걷어내고 트리를 바꿔 단 뒤 새 효과를 건다
 componentWillUnmount / componentDidMount 와 같은 순서다

 useInsertionEffect 는 둘 다 mutation 패스다 (CW L2084-2090)
 DOM 을 건드리기 전에 스타일을 넣으라고 만든 것이라
 layout 보다 앞에 있어야 한다
```

```text
 삭제는 mutation 패스가 전담한다

 CW L2023-2029  recursivelyTraverseMutationEffects 의 첫 부분
   deletions 가 있으면 commitDeletionEffects(...)
   주석 L2021-2022 "before the children effects have fired"

 ★ 이 블록은 subtreeFlags 검사 **밖**이다 (검사는 L2031)
   그래서 플래그가 비어도 삭제는 처리된다

 언마운트 안쪽 순서도 정해져 있다 (CW L1543-1599 기준)
   ref 를 떼고 -> 자식으로 먼저 내려가고 -> 돌아와서 DOM 노드를 뗀다
   자식 효과가 다 풀린 뒤에 노드를 없애는 것이다

 끝나면 CW L1457 detachFiberMutation 이 return 포인터만 끊는다
 child / sibling / alternate 는 패시브 단계까지 남긴다
```

```text
 순회 방식이 두 종류다

 (가) 모듈 전역 nextEffect + _begin / _complete
      before-mutation (CW L364 / L456)
      _begin 이 자식으로 내려가고
      더 갈 곳이 없으면 _complete 가 효과를 실행한 뒤
      형제로 가거나 부모로 올라간다
      둘이 같은 전역을 읽고 쓰며 null 이 되면 끝난다

 (나) .child / .sibling 재귀
      mutation (CW L2016), layout (CW L2995)
      subtreeFlags 로 가지를 쳐서 내려간다

 (가)가 옛 방식이고 (나)가 지금 방식이다.
 다만 삭제된 트리의 패시브 정리는 아직 (가)를 쓴다
 (그 자리는 이 문서 범위 밖이다)
```

```text
 mutation 의 하강 조건에 Cloned 가 섞인다

 CW L2031  if (parentFiber.subtreeFlags & (MutationMask | Cloned))

 패스 자체의 게이트(WL L3999)는 MutationMask 만 보는데
 안쪽 하강은 Cloned 도 본다

 Cloned 는 persistence 모드(react-native Fabric 등)에서
 트리를 복제할 때 쓰는 플래그다
 react-dom 은 mutation 모드라 이 비트가 서지 않는다
```

## 결과가 쓰이는 곳

```text
 DOM
      --> mutation 패스가 삽입·이동·제거·props 갱신을 한다

 root.current
      --> L4032 에서 바뀐다
      --> 이후 모든 코드가 새 트리를 본다

 ref
      --> mutation 이 떼고 layout 이 붙인다

 효과 목록
      --> useLayoutEffect 는 여기서 끝난다
      --> useEffect 는 [패시브 이펙트]로 넘어간다
```

## 다루지 않는 것

`commitMutationEffectsOnFiber`(CW L2042)의 tag 별 갈래 전부와 `commitLayoutEffectOnFiber`(CW L591)의 본문, `commitDeletionEffectsOnFiber`(CW L1473)의 tag 별 언마운트, `commitBeforeMutationEffectsOnFiber`(CW L474)와 `getSnapshotBeforeUpdate`, Offscreen 숨김·드러냄 경로, ref 를 붙이고 떼는 함수(`safelyAttachRef` / `safelyDetachRef`), `commitAfterMutationEffects`(CW L2799), 프로파일러 계측은 같은 뼈대의 곁가지라 요약만 했다. 에러 처리는 [spi](../spi/README.md)에 있다.
