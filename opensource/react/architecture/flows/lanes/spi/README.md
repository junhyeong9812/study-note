# spi

상위: [lane 흐름](../README.md)

다른 흐름들이 lane 에 묻는 질문은 **술어 함수**로 되어 있고, 답의 근거는 **루트의 lane 필드**에 있다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberLane.js` 기준이다.

## 비트 연산 헬퍼

```js
// ReactFiberLane.js L784-L802
export function includesSomeLane(a: Lanes | Lane, b: Lanes | Lane): boolean {
  return (a & b) !== NoLanes;
}

export function isSubsetOfLanes(set: Lanes, subset: Lanes | Lane): boolean {
  return (set & subset) === subset;
}

export function mergeLanes(a: Lanes | Lane, b: Lanes | Lane): Lanes {
  return a | b;
}

export function removeLanes(set: Lanes, subset: Lanes | Lane): Lanes {
  return set & ~subset;
}

export function intersectLanes(a: Lanes | Lane, b: Lanes | Lane): Lanes {
  return a & b;
}
```

```text
 이 파일의 헬퍼는 대개 한 줄이다

 L757  getHighestPriorityLane = lanes & -lanes
 L777  pickArbitraryLaneIndex = 31 - clz32(lanes)
 L781  laneToIndex -> 위와 같다
 L785  includesSomeLane(a, b) = (a & b) !== NoLanes
 L789  isSubsetOfLanes(set, subset) = (set & subset) === subset
 L793  mergeLanes(a, b) = a | b
 L797  removeLanes(set, subset) = set & ~subset
 L801  intersectLanes(a, b) = a & b

 예외가 하나 있다
 L760  getLanesOfEqualOrHigherPriority 는 본문이 두 줄이다
       주석이 예를 든다 (L761-763)
         0b100 -> 0b111, 0b101 -> 0b111

 그리고 존재 이유가 주석에 적힌 래퍼도 하나 있다
 L768  pickArbitraryLane
       주석 L769-772 - 인라인될 것이고,
       "어느 비트를 고르든 상관없다" 를 말하려고 만들었다.
       연산이 가장 적어서 getHighestPriorityLane 을 쓴다
```

## 술어 — 다른 흐름이 묻는 질문

| 술어 | 묻는 것 | 쓰는 흐름 |
|---|---|---|
| `includesSyncLane` L615 | 동기 lane 이 있나 | [스케줄링], [커밋] |
| `includesNonIdleWork` L619 | idle 이 아닌 일이 있나 | [렌더 루프] |
| `includesOnlyRetries` L622 | 전부 retry 인가 | [beginWork], [렌더 루프] |
| `includesOnlyNonUrgentLanes` L625 | 급한 것이 하나도 없나 | [훅] (`useDeferredValue`) |
| `includesOnlyTransitions` L632 | 전부 트랜지션인가 | [렌더 루프] |
| `includesTransitionLane` L636 | 트랜지션이 섞여 있나 | [렌더 루프] |
| `includesRetryLane` L640 | retry 가 섞여 있나 | [렌더 루프] |
| `includesIdleGroupLanes` L644 | idle 그룹이 섞여 있나 | [렌더 루프] |
| `includesOnlyHydrationLanes` L656 | 전부 수화인가 | 프로파일러 |
| `includesOnlyOffscreenLanes` L660 | 전부 Offscreen 인가 | 프로파일러 |
| `includesOnlyHydrationOrOffscreenLanes` L664 | 둘의 합집합인가 | 프로파일러 |
| `includesOnlyViewTransitionEligibleLanes` L668 | 뷰 트랜지션 대상인가 | [커밋] |
| `includesOnlySuspenseyCommitEligibleLanes` L672 | 위 + Gesture | [completeWork] L591 |
| `includesLoadingIndicatorLanes` L680 | Sync\|Default 가 있나 | [커밋] |
| `includesBlockingLane` L684 | 막는 lane 인가 (+Gesture) | [렌더 루프] L1156, [훅] |
| `includesExpiredLane(root, lanes)` L696 | 만료된 것이 있나 | [렌더 루프] L1157 |
| `isBlockingLane(lane)` L702 | 위의 단수형 | 프로파일러 |
| `isTransitionLane(lane)` L714 | 트랜지션 lane 인가 | [훅] (얽힘 조건) |
| `isGestureRender(lanes)` L718 | 제스처 렌더인가 | [커밋], [스케줄링] |

```text
 두 가지가 눈에 띈다

 includesExpiredLane 만 인자가 root 다 (L696)
   다른 술어는 lanes 만 보는데 이것은 root.expiredLanes 를 봐야 한다
   주석 L697-698 - 렌더가 시작된 뒤에도 만료될 수 있어
   includesBlockingLane 과 따로 둔다

 isGestureRender 는 교집합이 아니라 **완전 일치**다 (L722-723)
   lanes === GestureLane 이어야 한다
   그리고 플래그가 꺼져 있으면 무조건 false 를 돌려준다 (L719-721)

 (이 표의 "쓰는 흐름" 은 검증 과정에서 호출처를 전수 조사한 결과다.
  나는 앞 흐름들에서 직접 만난 여섯 개만 확인했다)
```

## 루트의 lane 필드

| 필드 | 뜻 | 세우는 곳 | 지우는 곳 |
|---|---|---|---|
| `pendingLanes` | 아직 안 한 일 전부 | `markRootUpdated` L826 | `markRootFinished` L905 (대입) |
| `suspendedLanes` | 데이터가 없어 막힌 lane | `markRootSuspended` L859 | `markRootUpdated` L845, `markRootFinished` L908 |
| `pingedLanes` | 막혔다가 promise 가 풀린 lane | `markRootPinged` L888 | `markRootSuspended` L860, `markRootFinished` L909 |
| `warmLanes` | 예열을 다 해 본 lane | `markRootSuspended` L864 (조건부) | `markRootPinged` L891, `markRootFinished` L910 |
| `expiredLanes` | 기아로 만료된 lane | **`markStarvedLanesAsExpired` L583 하나뿐** | `markRootFinished` L916 |
| `expirationTimes[]` | lane 인덱스 → 만료 시각 | 같은 함수 L579 | `markRootSuspended` L877, `markRootFinished` L934 |
| `entangledLanes` | 얽힘이 걸린 lane 의 합집합 | `markRootEntangled` L1041 등 | `markRootFinished` L918 |
| `entanglements[]` | lane 인덱스 → 같이 렌더할 lane | `markRootEntangled` L1053 등 | `markRootFinished` L933 |
| `errorRecoveryDisabledLanes` | 동기 재시도를 금지한 lane | [렌더 루프] 쪽 | `markRootFinished` L920 |
| `shellSuspendCounter` | 셸이 연속 서스펜드한 횟수 | [렌더 루프] 쪽 | `markRootFinished` L921 |

```text
 ★ markRootUpdated 는 낙관적으로 전면 재시도한다

 L844-848  updateLane 이 IdleLane 이 **아니면**
           suspendedLanes / pingedLanes / warmLanes 를
           셋 다 통째로 NoLanes 로 지운다

 => "새 갱신이 들어왔으니 막혀 있던 것도 다시 해 보자" 다
    idle 갱신은 그런 힘이 없어서 제외된다

 (이 동작은 검증 과정에서 확인된 것이고,
  나는 필드 목록과 줄번호까지 대조했다)
```

## 얽힘(entanglement)

```text
 정의를 주석이 적는다 (L440-443)
   "A lane is said to be entangled with another when it's not allowed
    to render in a batch that does not also include the other lane."

 => 같이 렌더되지 않으면 안 되는 관계다

 왜 필요한가 - 같은 출처에서 나온 여러 갱신 중
 **가장 최근 것만** 보이게 하려는 것이다.
 흩어져 렌더되면 중간 상태가 화면에 나타난다

 언제 얽히나
   트랜지션 갱신   같은 훅 큐에 쌓인 트랜지션 lane 들끼리
   useDeferredValue 가 낳은 lane   DeferredLane 과, 그리고 부모의 lane 과
   제스처
   flushSync 승격  대상 lane 들을 SyncLane 과 얽어 같이 동기로 민다

 ★ useOptimistic 은 얽지 않는다
   주석이 이유를 적는다 - optimistic 갱신은 언제나 동기라서다

 전개는 조회 때가 아니라 **저장 때** 닫아 둔다
   markRootEntangled 가 "C 가 A 와 얽혀 있으면
   A 를 B 와 얽을 때 C 도 B 와 얽는다" 를 처리한다

 그래서 getEntangledLanes(L427)는 한 단계만 펼치면 된다

 (얽힘 목록과 저장 시점 전개는 검증 과정에서 확인된 것이다.
  나는 getEntangledLanes 의 위치와 호출처까지 확인했다)
```

```text
 beginWork 가 받는 것은 renderLanes 가 아니다

 [렌더 루프]가 getEntangledLanes(root, lanes) 로 한 번 더 확장한 뒤
 entangledRenderLanes 로 넘긴다

 주석이 그것을 밝힌다 (L483-484 부근)
   "Most things in begin/complete phases should deal with
    entangledRenderLanes"

 => 앞 흐름들의 renderLanes 는 이미 얽힘이 반영된 값이다
```

## 플래그

```text
 enableRetryLaneExpiration   false
   => retry lane 은 만료 순회에서 아예 빠진다

 enableParallelTransitions   false
   => getHighestPriorityLanes 의 L212-214 가 안 돈다
      트랜지션이 배치로 묶인 채 처리된다

 enableGestureTransition     __EXPERIMENTAL__
   => isGestureRender 가 stable 에서는 언제나 false
      canary 에서는 산다
```

## 결과가 쓰이는 곳

```text
 술어들
      --> 다른 흐름이 lane 묶음의 성질을 묻는 통로다
      --> lane 비트를 직접 비교하는 코드가 흩어지지 않게 한다

 루트 필드
      --> getNextLanes 가 (1)(2)(3) 을 이 셋으로 판정한다
      --> markRoot* 네 함수가 상태를 옮긴다

 entanglements
      --> 같이 렌더돼야 하는 묶음
      --> beginWork 가 받는 entangledRenderLanes 의 근거다
```

## 다루지 않는 것

`markRootUpdated` / `markRootSuspended` / `markRootPinged` / `markRootFinished` 네 함수의 본문 전체, `markRootEntangled`(L1028)의 전개 알고리즘, `claimNext*Lane`(L726/738/747)의 순환 커서와 고갈, `upgradePendingLanesToSync`(L1059), `markHiddenUpdate`(L1076), `getBumpedLaneForHydration`(L1092)의 수화 승급, transition tracing 3종(L1210 이하), DevTools updater 추적(L1159 이하), async action 의 별도 "entangled scope"(`ReactFiberAsyncAction.js` — 이름만 같고 자료구조가 다르다)는 이 문서의 범위 밖이다.
