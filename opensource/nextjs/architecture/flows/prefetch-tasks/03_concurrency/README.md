# 03 순서와 대역폭

상위: [프리페치 작업 하나가 태어나서 끝나기까지](../README.md)

큐는 **이진 힙 하나**(`taskHeap`, L261)이고 비교 기준은 셋이다 — 우선순위, phase, 나중에 만든 것. 대역폭은 **전역 카운터 하나**(`inProgressRequests`, L263)로 잰다. 한도 12 대 4 와 오프라인·쿨다운 관문은 [프리페치] [02 프리페치 큐](../../segment-cache/02_scheduler/README.md)가 이미 인용했으므로 여기서는 그것이 **어디서 몇 번 검사되는가**와 힙의 규칙을 본다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L261-L300 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L261-L300))

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L2585-L2741 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L2585-L2741))

## 실제 코드

비교 함수가 큐 순서의 전부다.

```ts
// scheduler.ts L2591-L2612
function compareQueuePriority(a: PrefetchTask, b: PrefetchTask) {
  // Since the queue is a MinHeap, this should return a positive number if b is
  // higher priority than a, and a negative number if a is higher priority
  // than b.

  // `priority` is an integer, where higher numbers are higher priority.
  const priorityDiff = b.priority - a.priority
  if (priorityDiff !== 0) {
    return priorityDiff
  }

  // If the priority is the same, check which phase the prefetch is in — is it
  // prefetching the route tree, or the segments? Route trees are prioritized.
  const phaseDiff = b.phase - a.phase
  if (phaseDiff !== 0) {
    return phaseDiff
  }

  // Finally, check the insertion order. `sortId` is an incrementing counter
  // assigned to prefetches. We want to process the newest prefetches first.
  return b.sortId - a.sortId
}
```

```text
 1  priority   클수록 먼저   Intent 2 > Default 1 > Background 0   (SCTYPES L15-32)
 2  phase      클수록 먼저   RouteTree 2 > Shell 1 > Speculative 0  (L247-251)
 3  sortId     클수록 먼저   나중에 schedule/reschedule 된 작업

 ★★ phase 가 둘째 기준이라서 **같은 우선순위 안에서는 라우트 트리 요청이 세그먼트 요청을 모두 앞선다**
   주석 L2602-2603 - "Route trees are prioritized."
   phase 주석 L239-242 - Shell 도 같은 이유로 Speculative 앞이다. App Shell 은 같은 라우트로 가는
     모든 내비게이션이 공유하므로 링크 수가 아니라 라우트 수에 비례한다
 ★★ 셋째 기준이 "최신 우선" 이다. 필드 주석 L111-114 -
   "Newer prefetches are prioritized over older ones, so that as new links enter the viewport,
    they are not starved by older links that are no longer relevant."
   => 그래서 links.ts 의 IntersectionObserver 콜백이 항목을 **거꾸로** 돈다 (LINKS L251-268)
      문서 순서로 들어오니 역순으로 schedule 해야 **맨 위 링크가 마지막 = 가장 먼저** 처리된다
```

## 동작 흐름

```text
 Intent 는 하나다   trackMostRecentlyHoveredLink  L453-469

 L456-458  task.priority === Intent 이고 아직 그 작업이 아니면
 L460-465    이전 mostRecentlyHoveredLink 가 있고 **Background 가 아니면** Default 로 내리고 heapResift
 L467        mostRecentlyHoveredLink = task

 ★ 내리는 것은 Background 가 아닐 때만이다 (L462). 이미 Background 로 떨어진 작업을
   Default 로 **끌어올리지** 않으려는 것이다
 ★★ mostRecentlyHoveredLink 는 **지우는 곳이 없다** (grep — 대입은 L467 하나)
   작업이 끝나거나 취소돼도 그 자리를 지킨다. 그래서 reschedule 이 L416-419 에서
     task === mostRecentlyHoveredLink ? Intent : priority
   로 **마지막에 hover 한 링크는 뷰포트 재진입(Default)에도 Intent 를 유지한다**
 Intent 를 만드는 호출처는 LINKS L309 onNavigationIntent 하나다 (grep `PrefetchPriority.Intent` 전수)
```

```text
 Background 는 무엇인가   background(task)  L721-727

   task.priority 가 Background 면 true
   아니면 task.hasBackgroundWork = true 로 표시만 하고 false

 [01]의 큐 루프가 Speculative 패스의 Done 에서 hasBackgroundWork 를 보고
   priority = Background 로 내려 **큐에 다시 둔다** (L653-657). 다음 패스에서 background() 가 true 다

 ★★★ v16.3.6 에서 background(task) 를 부르는 곳은 L761 **하나다** (grep `background(task)` —
   L712 는 docstring 예시)
   => 백그라운드 일은 "검색 문자열을 뗀 라우트 트리 요청" 하나뿐이다 → [02]
   => SCTYPES L27-30 주석 "Assigned to tasks when they spawn non-blocking background work, like
      revalidating a partially cached entry to see if more data is available." 의 예시는
      지금 코드와 맞지 않는다. 부분 항목 재검증은 pingSegmentBundle 이 **자기 phase 안에서** 한다
      (주석 L2209-2213 "no background deferral")
 ★ TODO L716-719 - background 를 우선순위가 아니라 phase 로 모델링하자는 메모가 남아 있다
```

```text
 대역폭 검사가 일어나는 자리 — hasNetworkBandwidth(task) 호출 넷 (grep 전수)

 L594   큐 루프 머리      맨 앞 작업의 우선순위로 판단. 거짓이면 루프를 **아예 돌지 않는다**
 L859   pingRootRouteTree  라우트 트리를 받은 뒤, 세그먼트를 걷기 전에
 L1306  pingSharedPart…    겹치는 부분의 자식마다
 L1494  pingNewPart…       새 부분에서 자식으로 내려가기 전에
 => 거짓이면 InProgress 가 위로 올라가고, [01]의 루프가 L613 에서 return 한다

 ★★ 검사가 **요청 앞이 아니라 걷기 앞**에 있다
   pingSegmentBundle(L2293)과 동적 요청(L985 · L1032)은 검사 없이 spawnPrefetchSubtask 한다
   => 한 패스가 한도를 조금 넘겨 보낼 수 있다. 함수 주석 L482-483 이 스스로 "This is a
      cooperative limit" 라고 적는다
 ★ 한도는 작업마다가 아니라 **지금 맨 앞 작업의 우선순위** 로 고른다 —
   Intent 가 맨 앞일 때만 12 이고, Background 와 Default 는 4 다
```

```text
 카운터를 세지 않는 요청 — ISR fallback 재시도 루프

 fetchSegmentsOnCacheMiss 의 응답이 "올릴 수 있는 fallback 셸" 이면 (SCCACHE L2323-2340)
   ※ 조건 — 서버가 isUpgradeableISRFallback 을 참으로 싣는 것은 fallbackRouteParams 가 있는
     prerender 뿐이다(app-render.tsx L10555-10561). cacheComponents 를 끈 prerender-legacy 스토어
     (L9566-9575)에는 그 필드가 없다 => **기본 설정에서는 이 루프에 닿지 않는다**
   task.fallbackRetryStatus = Pending 으로 두고 retryUpgradeableFallbackPrefetch 를 **void 로** 띄운다
 retryUpgradeableFallbackPrefetch  SCCACHE L2951-3020
   2000ms(L2248) 간격으로 최대 3회(L2252) fetchSegmentsOnCacheMissImpl 을 **직접** 부른다 (L2973)

 ★★ 이 요청들은 spawnPrefetchSubtask 를 거치지 않는다
   => inProgressRequests 에 잡히지 않고, hasNetworkBandwidth 의 오프라인·쿨다운 관문도 보지 않는다
   ※ 작업당 한 번(주석 L2943-2945 "A loop runs at most once per task, ever")이고 요청이 세 번뿐이라
     설계가 감수한 것으로 보인다. 소스가 이유를 적지는 않았다
```

```text
 재검증 쿨다운   startRevalidationCooldown  L285-298

 호출처는 SARED L370 **하나**다 (grep 전수)
   L346  revalidationKind !== ActionDidNotRevalidate 이면
   L364    ActionDidRevalidateStaticAndDynamic 일 때만 invalidateEntirePrefetchCache  → [04]
   L370    startRevalidationCooldown()    ← **종류와 무관하게** 켠다
 => 프리페치 캐시를 비우지 않는 ActionDidRevalidateDynamicOnly(= 2, action-revalidation-kind.ts L5)에도
    300ms 동안 프리페치가 멈춘다

 ★ L502-503 주석 - "When the cooldown expires, the timeout will call ensureWorkIsScheduled()"
   => 그런 이름은 저장소에 없다 (grep 결과가 이 주석 한 줄). 실제로 부르는 것은 L296 pingPrefetchScheduler
```

```text
 ★ IncludeDynamicData (L300) — 선언뿐이다

   export type IncludeDynamicData = null | 'full' | 'dynamic'
   grep -rnw IncludeDynamicData packages/ -> 이 한 줄
 => 이름이 비슷한 pingRouteTreeAndIncludeDynamicData(L1834)는 이 타입을 쓰지 않는다.
    그 함수가 받는 것은 FetchStrategy 셋(Full · PPRRuntime · RuntimeShell)이다
 ※ 문자열 'full' · 'dynamic' 로 전략을 표시하던 이전 설계의 흔적으로 보인다. 소스가 적지 않았다
```

취소가 쓰는 힙 삭제는 **아래로만** 거른다.

```ts
// scheduler.ts L2640-L2653
function heapDelete(heap: Array<PrefetchTask>, node: PrefetchTask): void {
  const index = node._heapIndex
  if (index !== -1) {
    node._heapIndex = -1
    if (heap.length !== 0) {
      const last = heap.pop() as PrefetchTask
      if (last !== node) {
        heap[index] = last
        last._heapIndex = index
        heapSiftDown(heap, last, index)
      }
    }
  }
}
```

```text
 ★★★ 마지막 원소를 지운 자리(index)로 옮긴 뒤 heapSiftDown 만 한다
 그런데 마지막 원소는 **다른 가지**에서 왔으므로 새 부모보다 우선순위가 높을 수 있다
 => 그 경우 위로 올려야 하는데(sift up) 올리지 않는다. 같은 파일의 heapResift(L2655-2672)는
    부모와 비교해 위·아래를 고르는데, heapDelete 는 그것을 쓰지 않는다

 실증 (이 파일의 힙 함수 L2591-2741 을 그대로 떼어 node 로 무작위 시험, 10만 회 —
       13±7개 힙에서 하나를 지운다. 수치는 우선순위 · phase 분포에 따라 달라진다)
   우선순위 · phase 무작위            불변식 위반 약 4,000~6,000 회 · pop 순서 어긋남 약 1,300~2,700 회
   전부 Default · RouteTree, sortId 만 증가   불변식 위반 약 16,000 회
   => 우선순위 차이가 없어도 깨진다. 한 번 깨진 뒤에는 이후 연산 내내 위반이 이어진다 (별도 20만 스텝 시뮬레이션)
   예) 13개 힙에서 T9 를 지우자 pop 순서가
       T11 T5 T2 T0 T4 T12 ...  (기대: T11 T5 T2 T12 T0 T4 ...)
       T12(Default, sortId 12)가 T0(Default, sortId 9)보다 늦게 나왔다

 heapDelete 호출처는 cancelPrefetchTask(L388) 하나다 (grep 전수)
 => 취소는 드문 일이 아니다 — 뷰포트 이탈 · unmount(LINKS L243)뿐 아니라, **내비게이션마다**
    app-router.tsx L103-109 가 pingVisibleLinks 를 부르고, 트리가 바뀌면 보이는 링크의 작업이 전부
    dirty 라(L435-451) 한꺼번에 cancel 된다(LINKS L389). 무효화 셋도 같은 길이다
 => 결과는 "작업을 잃는다" 가 아니라 "더 새로운(sortId) · RouteTree 우선(phase) 작업이 늦게 돈다" 다
 ★ Intent 작업은 영향을 받지 않는다 — Intent 는 동시에 하나뿐이고(L456-465), heapSiftUp 이 루트까지
   올리며, heapDelete 가 옮기는 원소는 루트 아래에만 놓인다. 시뮬레이션에서 Intent 가 루트가 아닌 경우 0회
```

## 결과가 쓰이는 곳

```text
 taskHeap 의 순서
      --> [01]의 processQueueInMicrotask 가 heapPeek 으로 맨 앞만 본다

 inProgressRequests
      --> hasNetworkBandwidth 의 12 / 4 비교
      --> [01] L701 — 0 이고 큐가 비면 LRU cleanup

 revalidationCooldownTimeoutHandle
      --> hasNetworkBandwidth L500 — null 이 아니면 거짓
      --> 300ms 뒤 스스로 null 이 되며 pingPrefetchScheduler (L293-297)

 mostRecentlyHoveredLink
      --> 한도 12 를 받는 유일한 작업. reschedule 때 Intent 유지 판정(L419)
```

## 다루지 않는 것

`heapPush` · `heapPop` · `heapSiftUp` · `heapSiftDown`(L2614-2741)의 인덱스 계산은 표준 이진 힙이라 따라가지 않았다(위 시험은 그 함수들을 그대로 썼다). `offline.ts`(187줄)의 연결 감지와 `getOffline`, `lru.ts` 의 크기 계산과 `maxLruSize`, `retryUpgradeableFallbackPrefetch` 의 응답 쓰기(`writeSegmentBundleResponseVariants`), 서버 액션의 `revalidationKind` 값을 만드는 서버 쪽([서버 액션] · [재검증])은 이 문서의 범위 밖이다.
