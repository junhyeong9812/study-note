# 04 작업이 끝나는 자리

상위: [프리페치 작업 하나가 태어나서 끝나기까지](../README.md)

작업은 스스로 기다리지 않는다. **기다려야 할 캐시 항목에 자기를 등록하고 큐에서 빠진다.** 응답이 그 항목을 채우면 항목이 작업을 다시 큐에 넣는다. 끝나는 길은 셋이다 — 모든 응답을 본 패스가 완료하거나, 링크가 취소하거나, 무효화가 작업을 버리고 **새 작업**을 만든다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L1801-L1832 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L1801-L1832))

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L379-L451 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L379-L451))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L1345-L1355 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L1345-L1355))

## 실제 코드

기다림의 등록은 이 함수 하나로 모인다. docstring 이 phase 완료의 계약을 적는다.

```ts
// scheduler.ts L1801-L1832
/**
 * Called during a pass when a segment's response hasn't been received yet —
 * whether the request was just spawned by this pass or was already in flight.
 * Marks the task as blocked: a phase only completes once a full pass observes
 * every segment response it cares about, because later decisions (like
 * whether a segment needs a follow-up runtime request) are made against the
 * contents of those responses, and a phase may need to restart its work based
 * on what they contain. The task is re-pinged (via pingBlockedTasks in
 * cache.ts) when the entry resolves, re-running the pass against the
 * received data. Only a pass that observes every response may advance the
 * phase or complete the task.
 *
 * Never call this for an entry that's already Rejected — nothing ever pings
 * a Rejected entry, so registering on one would strand the task. A rejected
 * segment is simply skipped: the pass keeps prefetching the rest of the tree
 * without it.
 */
function blockTaskOnPendingResponse(
  task: PrefetchTask,
  segment: { blockedTasks: Set<PrefetchTask> | null }
): void {
  // This state is reset after each iteration of the task queue. We use it to
  // inform the scheduler that the task is blocked.
  task.hasPendingResponses = true
  // Add the task to this segment's blocked tasks, so it can be rescheduled
  // once the segment finishes loading.
  if (segment.blockedTasks === null) {
    segment.blockedTasks = new Set([task])
  } else {
    segment.blockedTasks.add(task)
  }
}
```

```text
 ★★★ "Only a pass that observes every response may advance the phase or complete the task."
   => 패스가 **요청을 보낸 것만으로는** phase 가 끝나지 않는다. 응답을 **본** 패스만 끝낸다
   이유 (L1805-1808) - 뒤의 결정("이 세그먼트에 후속 runtime 요청이 필요한가")이
     응답 **내용**을 보고 내려지기 때문이다
   => 그래서 [02]의 정적 시도 → 관찰 → 필요하면 runtime 이 **경쟁 없이 순서대로** 된다
      (pingNewPart… 주석 L1403-1404 "the attempt is serial, never raced")

 ★★ Rejected 에는 **절대 등록하지 않는다** (L1813-1816)
   "nothing ever pings a Rejected entry, so registering on one would strand the task."
   => 실패한 세그먼트는 건너뛰고 나머지를 계속 받는다. 재시도 시점은 항목의 staleAt 이 정한다
   ★ 코드도 그렇다 — 호출 열두 곳(grep 전수, 정의 제외)이 모두 Empty→Pending 으로 방금 올린 항목이거나
     status 가 Pending 인 항목에만 부른다 (case Pending 안이거나, L1942 · L2273 · L2356 처럼 status 를 확인한 뒤)
```

## 동작 흐름

```text
 기다림 두 종류

 라우트 트리   SCHED L841-846  route.blockedTasks 에 **직접** 넣고 => Blocked
               (blockTaskOnPendingResponse 를 거치지 않는다 — hasPendingResponses 도 세우지 않는다)
 세그먼트      blockTaskOnPendingResponse — hasPendingResponses = true + entry.blockedTasks 에 추가
               패스는 끝까지 걷고, [02]의 pingRoute L786-790 이 Done 을 Blocked 로 바꾼다

 [01]의 큐 루프  Blocked 면 heapPop — 큐에서 뺀다 (L614-620)
```

```text
 다시 깨우기   SCCACHE pingBlockedTasks  L1345-1355

   entry.blockedTasks 의 작업마다 pingPrefetchTask(task)   → [01]
   entry.blockedTasks = null

 호출처 여섯 (grep 전수)
   L1079  upsertSegmentEntry
   L1189  evictShadowingSegmentEntries
   L1416  fulfillRouteCacheEntry
   L1505  fulfillSegmentCacheEntry
   L1516  rejectRouteCacheEntry
   L1532  rejectSegmentCacheEntry
 => 채워지든 거절되든 **기다리던 작업은 깨어난다.** 그리고 그 작업은 패스를 **처음부터** 다시 돈다
    필드 주석 L155-157 - "Each ping re-runs a full traversal for the task, so expect roughly
      one re-pass per settling entry."
 ★ pingPrefetchTask 는 취소된 작업과 이미 큐에 있는 작업을 무시한다 (SCHED L571-578)
   => 같은 작업이 여러 항목에 등록돼 있어도 큐에는 한 번만 들어간다
```

```text
 완료   [01]의 L658-689

   Speculative phase 의 Done 이고 background 일이 없을 때 heapPop
 ★ 완료된 작업 객체는 버려지지 않는다 — links.ts 의 instance.prefetchTask 가 계속 쥐고 있다.
   다음 hover · 뷰포트 재진입 때 reschedulePrefetchTask 가 **같은 객체**를 되살린다
 ★★ 완료 뒤에도 옛 등록이 한 번 더 깨울 수 있다 (주석 L661-669). 무해한 재실행이다
```

```text
 취소   cancelPrefetchTask  L379-389

 L385  task.isCanceled = true
       주석 L383-384 - "so that a blocked task does not get added back to the queue when
         it's pinged by the network."
 L388  heapDelete(taskHeap, task)        ★ 이 삭제의 순서 결함 → [03]

 호출처 셋 (grep 전수) — 모두 links.ts
   L243  unmountPrefetchableInstance   링크가 사라질 때
   L325  rescheduleLinkPrefetch        보이지 않게 됐을 때
   L389  pingVisibleLinks              무효화 뒤 갈아 끼우기 직전

 ★★ 취소는 **요청을 중단하지 않는다.** 스케줄러는 AbortController 를 쥐지 않는다
   (scheduler.ts 의 "abort" 는 주석 둘뿐이다 — L520, 그리고 L828 의 TODO "We should probably also
   manually abort the fetch task, to reclaim server bandwidth."). 이미 나간 응답은 그대로 캐시에 쓰이고,
   취소된 작업만 다시 깨어나지 않는다
   ※ 그래서 뷰포트를 스쳐 지나간 링크의 요청도 끝까지 받아 캐시를 채운다고 읽힌다.
     [02 프리페치 큐] 가 인용한 "because we don't abort in-progress requests"(L520) 와 같은 태도다
 ★ ISR fallback 재시도 루프는 깨어날 때마다 isCanceled 를 본다 (SCCACHE L2967 · L2979)
```

```text
 되살리기   reschedulePrefetchTask  L391-433

 L405  isCanceled = false          "Un-cancel the task, in case it was previously canceled."
 L406  phase = RouteTree           — 처음부터 다시
 L415  sortId = sortIdCounter++    — 맨 앞으로
 L416-419  priority (마지막 hover 링크면 Intent 유지) → [03]
 L421-422  treeAtTimeOfPrefetch · fetchStrategy 교체
 L426-431  큐에 있으면 heapResift, 없으면 heapPush
 ★ fallbackRetryStatus 는 **일부러 되돌리지 않는다** (주석 L408-411) —
   "A retry loop runs at most once per task, even across reschedules"
 ★ 캐시 버전은 여기서 찍지 않는다. 다음 패스의 L595-596 이 찍는다
```

무효화 뒤 다시 태어나는 쪽은 보이는 링크를 전부 돈다.

```ts
// links.ts L368-L401
export function pingVisibleLinks(
  nextUrl: string | null,
  tree: FlightRouterState
) {
  // For each currently visible link, cancel the existing prefetch task (if it
  // exists) and schedule a new one. This is effectively the same as if all the
  // visible links left and then re-entered the viewport.
  //
  // This is called when the Next-Url or the base tree changes, since those
  // may affect the result of a prefetch task. It's also called after a
  // cache invalidation.
  for (const instance of prefetchableAndVisible) {
    const task = instance.prefetchTask
    if (task !== null && !isPrefetchTaskDirty(task, nextUrl, tree)) {
      // The cache has not been invalidated, and none of the inputs have
      // changed. Bail out.
      continue
    }
    // Something changed. Cancel the existing prefetch task and schedule a
    // new one.
    if (task !== null) {
      cancelPrefetchTask(task)
    }
    const cacheKey = createCacheKey(instance.prefetchHref, nextUrl)
    instance.prefetchTask = scheduleSegmentPrefetchTask(
      cacheKey,
      tree,
      instance.fetchStrategy,
      PrefetchPriority.Default,
      null,
      null // navigationLockPrefetch
    )
  }
}
```

```text
 무효화 → 재프리페치

 SCCACHE L413-456  invalidateEntirePrefetchCache · invalidateRouteCacheEntries · invalidateSegmentCacheEntries
   각각 버전을 올리고(항목은 지우지 않는다) pingVisibleLinks + pingInvalidationListeners
 호출처 (grep 전수)
   SARED L365                     서버 액션이 정적+동적을 재검증했을 때 — 전체
   refresh-reducer.ts L39         router.refresh() — 세그먼트만 (테스트 API 우회 가능, L34-36)
   ppr-navigations.ts L1762       내비게이션이 동적 rewrite 를 발견했을 때 — 라우트만
   SCCACHE L3317                  **프리페치 자신이** 동적 rewrite 를 발견했을 때 — 라우트만
 그리고 무효화 없이 pingVisibleLinks 만 부르는 길
   APPROUTER L103-109             nextUrl · tree 가 바뀔 때 (useEffect)

 pingVisibleLinks (위 코드)
   prefetchableAndVisible — **보이는 링크만** 돈다 (LINKS L114-118)
   L381  isPrefetchTaskDirty 가 거짓이면 건너뛴다
   L388-399  참이면 cancel 하고 **새 작업**을 schedule — reschedule 이 아니다
 ★★ 무효화 뒤에는 옛 작업 객체를 되살리지 않고 **새로 만든다**. 새 작업은 새 sortId ·
   Default 우선순위 · 지금의 tree 를 받는다. 옛 작업이 쥐던 Intent 도 여기서는 이어지지 않는다
   (단 mostRecentlyHoveredLink 는 옛 객체를 계속 가리킨다 → [03])

 isPrefetchTaskDirty  L435-451 — 넷 중 하나라도 다르면 참
   routeCacheVersion · segmentCacheVersion · treeAtTimeOfPrefetch(참조 비교) · key.nextUrl
   주석 L440-444 - "This is strictly an optimization — theoretically, if it always returned
     true, no behavior should change because a full prefetch task will effectively perform
     the same checks."
 호출처 둘 (grep 전수): LINKS L381 · SCCACHE L505
```

```text
 router.prefetch 쪽 — onInvalidate

 SCCACHE L666   readOrCreateRouteCacheEntry 가 부를 때마다 attachInvalidationListener(task)
                — onInvalidate 가 있는 작업만 전역 Set 에 넣는다 (L458-471)
 SCCACHE L493-510 pingInvalidationListeners
   Set 을 통째로 비우고, dirty 인 작업만 notifyInvalidationListener
 SCCACHE L473-491 notifyInvalidationListener
   task.onInvalidate = null 로 먼저 지우고 부른다 — **한 번만** 불린다. 예외는 reportError 로
 => SCPREF 주석 L17-25 - "This is not a live subscription — it's called at most once per
    `prefetch` call. The only supported use case is to trigger a new prefetch inside the
    listener ... Prefetching is a poll-based (pull) operation, not an event-based (push) one."
 ★ 링크는 스케줄러가 알아서 다시 받지만, router.prefetch 는 **사용자가 콜백 안에서 다시 불러야** 한다

 ★★ pingInvalidationListeners 의 주석(L497-500)과 호출처가 어긋난다
   주석 "This is called when the Next-Url or the base tree changes, since those may affect the
     result of a prefetch task. It's also called after a cache invalidation."
   호출처는 무효화 함수 셋(SCCACHE L421 · L438 · L455)**뿐**이다 (grep 전수).
   Next-Url · tree 변경 때 부르는 것은 APPROUTER L108 의 pingVisibleLinks 이고, 이것은 부르지 않는다
   => nextUrl 만 바뀌면 링크는 다시 받지만 router.prefetch 의 onInvalidate 는 **불리지 않는다**
 ※ 무효화 직후에는 모든 작업의 버전이 현재보다 낮으므로 Set 안의 작업은 전부 dirty 로 판정된다고 읽었다.
   "dirty 아닌 작업이 Set 에서 조용히 빠지는" 경우는 이 세 호출처에서는 생기지 않는다
```

## 결과가 쓰이는 곳

```text
 entry.blockedTasks
      --> [캐시 항목]의 채우기·거절·upsert 가 pingBlockedTasks 로 비운다

 task.isCanceled
      --> pingPrefetchTask(L573) · fallback 재시도 루프(SCCACHE L2967 · L2979) · reschedule(L405 해제)

 새 PrefetchTask (pingVisibleLinks)
      --> 다시 [01]의 RouteTree phase 부터. 버전이 올랐으므로 캐시 읽기가 낡은 항목을 버리고
          (주석 SCCACHE L392-395 "entries are lazily evicted when read") 새 요청을 만든다

 onInvalidate 호출
      --> router.prefetch 를 쓴 사용자 코드. 한 번 불리고 끝난다

 _navigationLockPrefetch 해소 (완료 때)
      --> SCNAV ensurePrefetchThenNavigate 의 await 가 풀린다 (테스트 API 전용)
```

## 다루지 않는 것

`upsertSegmentEntry`(SCCACHE L1012) · `evictShadowingSegmentEntries`(L1142) · `fulfillRouteCacheEntry`(L1380) · `fulfillSegmentCacheEntry`(L1470)의 본문과 버전 비교가 읽기 함수 안에서 항목을 버리는 자리는 [캐시 항목](../../cache-entries/README.md)이 본다. `invalidateBfCache` 와 bfcache, `refreshDynamicData` 이후의 새로고침 내비게이션([클라이언트 라우터](../../client-router/README.md)), 동적 rewrite 를 표시하는 `markRouteEntryAsDynamicRewrite` 와 `rejectSegmentEntriesIfStillPending`, `navigation-testing-lock.ts` 의 `beginNavigationLockPrefetch` · `resolveNavigationLockPrefetch` 본문은 이 문서의 범위 밖이다.
