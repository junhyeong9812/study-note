# 패시브 이펙트

상위: [React 아키텍처 지도](../../README.md)

`useEffect` 가 도는 자리다. [커밋](../commit/README.md)이 끝난 뒤에 돈다 — 대개는 별도 태스크로, **그런데 sync lane 이면 같은 태스크 안에서** 돈다.

이 흐름의 핵심은 셋이다. **예약과 실행 허가가 나뉘어 있고**, **삭제된 컴포넌트의 cleanup 을 위해 옛 fiber 를 따로 들고 있으며**, **체인의 끝이 아니다** — 여기서 다시 동기 렌더가 돌 수 있다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). `WL` = `ReactFiberWorkLoop.js`, `CW` = `ReactFiberCommitWork.js`, `CE` = `ReactFiberCommitEffects.js`.

## 전체 그림

```text
 [커밋]의 commitRoot
      +-- [FLAG:enableYieldingBeforePassive 가 꺼졌을 때]   WL L3783
      |     scheduleCallback(NormalSchedulerPriority, ...)   WL L3787
      |       그 안에서 flushPassiveEffects()                WL L3796
      +-- flushSpawnedWork 가 허가를 낸다                     WL L4190
      +-- sync lane 이면 기다리지 않고 바로 배출              WL L4305-4310

 [01] flushPassiveEffects                          WL L4672-4707
      +-- 가드: PENDING_PASSIVE_PHASE 가 아니면 => return false   L4674
      +-- 우선순위를 낮춰 잡고 try 로 감싼다                  L4689-4696
      +-- => return [02] flushPassiveEffectsImpl()           L4697
      +-- finally 에서 releaseRootPooledCache                L4705

 [02] flushPassiveEffectsImpl                      WL L4709-4856
      +-- 전역을 지운다 (GC 목적)                             L4716-4722
      +-- 렌더/커밋 중이면 => throw                           L4731
      +-- commitPassiveUnmountEffects(root.current)          L4769
      +-- commitPassiveMountEffects(...)                     L4770
      +-- flushSyncWorkOnAllRoots()                          L4799  ** 끝이 아니다 **
      +-- => return true                                     L4855
```

1. [flushPassiveEffects](01_flushPassiveEffects/README.md)가 가드하고 우선순위를 잡는다.
2. [flushPassiveEffectsImpl](02_flushPassiveEffectsImpl/README.md)이 실제로 돌린다.
3. [순회](03_traversal/README.md)가 정리와 실행을 나눠 훑는다.

```text
 ★ "패시브" 인 이유 - 대개 별도 태스크다

 [커밋]의 commitRoot 가 Normal 우선순위 스케줄러 태스크를 건다 (WL L3787)
 그래서 useLayoutEffect 와 달리 페인트 뒤로 밀린다

 그런데 예약만으로는 아무 일도 안 일어난다
   flushPassiveEffects 의 가드(L4673)가 PENDING_PASSIVE_PHASE 를 요구하는데
   그 값은 [커밋]의 flushSpawnedWork L4190 이 세운다

 => 예약과 실행 허가가 나뉘어 있다
    콜백이 먼저 돌면 조용히 돌아간다
```

```text
 ★ 그런데 sync lane 이면 기다리지 않는다

 [커밋]의 flushSpawnedWork L4305-4310
   if (includesSyncLane(pendingEffectsLanes) && ...) {
     flushPendingEffects();
   }

 주석이 이유를 적는다 (WL L4297-4301)
   "If the passive effects are the result of a discrete render, flush them
    synchronously at the end of the current task so that the result is
    immediately observable. Otherwise, we assume that they are not
    order-dependent and do not need to be observed by external systems,
    so we can wait until after paint."

 => 클릭 같은 이산 이벤트에서 나온 useEffect 는
    같은 태스크 안에서 돈다. 페인트를 기다리지 않는다
    (예약된 콜백은 나중에 돌아도 가드에 걸려 no-op 한다)

 그 밖에도 배출 경로가 더 있다
   completeRoot 가 다음 커밋 전에 루프로 비운다 (WL L3511-3519)
   루트 스케줄러가 태스크 진입부에서 비운다
   act() 안에서는 스케줄러 대신 act 큐로 들어간다
```

```text
 ★ 체인의 끝이 아니다

 WL L4799  flushSyncWorkOnAllRoots();

 패시브 이펙트 안에서 setState 를 하면 sync 작업이 쌓이는데,
 이 줄이 그것을 **그 자리에서** 돌린다

 그래서 completeRoot 는 flushPendingEffects 를 루프로 돈다
   WL L3511-3519  do { flushPendingEffects(); }
                  while (pendingEffectsStatus !== NO_PENDING_EFFECTS);
 한 번 비워도 그 과정에서 또 쌓일 수 있기 때문이다
```

```text
 정리가 실행보다 먼저다

 WL L4769  commitPassiveUnmountEffects(root.current)
 WL L4770  commitPassiveMountEffects(root, root.current, lanes, ...)

 이 두 줄에는 주석이 없다.
 다만 레이아웃 이펙트 쪽에 같은 논리를 적은 주석이 있다 (CE L119-123)
   "Layout effects are destroyed during the mutation phase so that all
    destroy functions for all fibers are called before any create
    functions. This prevents sibling component effects from interfering
    with each other, e.g. a destroy function in one component should never
    override a ref set by a create function in another component during
    the same commit."

 => 형제 간 간섭을 막으려는 것으로 읽힌다.
    다만 그 문장은 **레이아웃 이펙트 주석**이고
    패시브 쪽에 같은 설명이 복사돼 있지는 않다
```

## 어디로 이어지는가

```text
 [커밋]        commitRoot 가 예약하고 flushSpawnedWork 가 허가한다

 [스케줄링]    L4799 의 flushSyncWorkOnAllRoots 가 새 작업을 돌릴 수 있다

 [훅]          여기서 부르는 cleanup/create 가 useEffect 가 등록한 것이다
```

## 결과가 쓰이는 곳

```text
 useEffect 의 create 반환값
      --> 훅 인스턴스의 destroy 에 저장된다
      --> 다음 커밋의 정리 단계가 그것을 부른다

 pendingEffects* 전역
      --> 여기서 전부 지워진다. 커밋 한 바퀴가 끝난다

 flushSyncWorkOnAllRoots
      --> 패시브 중 쌓인 sync 작업을 그 자리에서 돌린다

 반환값 boolean
      --> flushPendingEffects 가 그대로 돌려준다
      --> "패시브를 실제로 비웠는가" 를 뜻한다
```

## 다루지 않는 것

`commitPassiveMountOnFiber`(CW L3605)의 tag 별 갈래 열둘과 `commitPassiveUnmountOnFiber`(CW L4882)의 다섯, Offscreen 숨김·재등장 경로(`disconnectPassiveEffect` / `reconnectPassiveEffects`), 숨은 트리의 캐시 refcount(`commitAtomicPassiveEffects`), `commitDoubleInvokeEffectsInDEV`(WL L5371)의 StrictMode 이중 실행, 프로파일러 로거들, transition tracing 의 Idle 콜백은 같은 뼈대의 곁가지라 요약만 했다. 순회 방식과 삭제 트리 처리는 [03 순회](03_traversal/README.md)에 있다.

## 하위 메서드

- [01 flushPassiveEffects](01_flushPassiveEffects/README.md)
- [02 flushPassiveEffectsImpl](02_flushPassiveEffectsImpl/README.md)
- [03 순회](03_traversal/README.md) — 정리와 실행, 삭제 트리
