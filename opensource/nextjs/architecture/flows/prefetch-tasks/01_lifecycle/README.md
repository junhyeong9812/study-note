# 01 작업의 한살이

상위: [프리페치 작업 하나가 태어나서 끝나기까지](../README.md)

작업은 **한 번에 끝나지 않는다.** 큐에서 꺼내져 한 번 걷고(패스), 결과에 따라 큐에 남거나 빠지거나 다음 phase 로 넘어간다. 이 구획은 그 바깥 고리 — `processQueueInMicrotask` 가 패스 하나의 결과를 받아 작업을 어디로 보내는가 — 를 본다. 패스 안쪽은 [02](../02_one-pass/README.md)다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L67-L251 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L67-L251))

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L584-L704 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L584-L704))

## 실제 코드

패스 하나가 돌려주는 종료 상태는 셋이고, 큐 처리 루프가 그것을 이렇게 받는다.

```ts
// scheduler.ts L609-L694
    switch (exitStatus) {
      case PrefetchTaskExitStatus.InProgress:
        // The task yielded because there are too many requests in progress.
        // Stop processing tasks until we have more bandwidth.
        return
      case PrefetchTaskExitStatus.Blocked:
        // The task is blocked. It needs more data before it can proceed.
        // Keep the task out of the queue until the server responds.
        heapPop(taskHeap)
        // Continue to the next task
        task = heapPeek(taskHeap)
        continue
      case PrefetchTaskExitStatus.Done:
        if (task.phase === PrefetchPhase.RouteTree) {
          // Finished prefetching the route tree. The two-phase (Shell then
          // Speculative) flow only applies to routes that have opted into
          // Partial Prefetching — either globally via the `partialPrefetching`
          // config or per segment (`prefetch: 'partial'` or
          // `'unstable_eager'`), all surfaced as the
          // `SubtreeHasPartialPrefetching` hint on the route tree. Every other
          // route skips the Shell phase and goes straight to Speculative.
          //
          // The route entry is fulfilled at this point (the RouteTree phase
          // just completed), so its prefetch hints are available.
          const route = readRouteCacheEntry(now, task.key)
          const routeHasPartialPrefetching =
            route !== null &&
            route.status === EntryStatus.Fulfilled &&
            (route.tree.prefetchHints &
              PrefetchHint.SubtreeHasPartialPrefetching) !==
              0
          task.phase = routeHasPartialPrefetching
            ? PrefetchPhase.Shell
            : PrefetchPhase.Speculative
          heapResift(taskHeap, task)
        } else if (task.phase === PrefetchPhase.Shell) {
          // Shell phase complete — a Done exit means the pass observed every
          // response it cares about (otherwise it would have exited Blocked;
          // see hasPendingResponses). Always advance to Speculative regardless
          // of whether Shell-phase work fired — Speculative is responsible
          // for the per-link concrete work and runs even on routes whose
          // shell phase was a no-op.
          task.phase = PrefetchPhase.Speculative
          heapResift(taskHeap, task)
        } else if (hasBackgroundWork) {
          // The task spawned additional background work. Reschedule the task
          // at background priority.
          task.priority = PrefetchPriority.Background
          heapResift(taskHeap, task)
        } else {
          // The prefetch is complete. Continue to the next task.
          //
          // Completion is terminal in the normal flow: a task only completes
          // after a full pass observed every response it cares about. In rare
          // cases, though, a task can complete while still registered on an
          // entry from an earlier pass whose subtree the final pass no longer
          // reached; when that entry later settles, it re-pings the completed
          // task. The re-run is a harmless idempotent no-op, but any
          // per-completion side effect added here must be idempotent or
          // once-guarded — in particular, the navigation-lock release below
          // must not fire twice (hence the nulling).
          if (
            process.env.__NEXT_EXPOSE_TESTING_API &&
            task._navigationLockPrefetch != null
          ) {
            // This locked-navigation prefetch is complete: the final pass
            // observed every segment response it cares about, so the data the
            // navigation will read has settled. Resolve the prefetch's
            // promise (awaited by `ensurePrefetchThenNavigate`) so the
            // navigation proceeds against present data rather than a
            // still-in-flight entry.
            const { resolveNavigationLockPrefetch } =
              require('./navigation-testing-lock') as typeof import('./navigation-testing-lock')
            resolveNavigationLockPrefetch(task._navigationLockPrefetch)
            // Release at most once per task: a stale registration from an
            // earlier pass can re-ping a completed task (see above), so it can
            // pass through here again.
            task._navigationLockPrefetch = null
          }
          heapPop(taskHeap)
        }
        task = heapPeek(taskHeap)
        continue
      default:
        exitStatus satisfies never
    }
```

```text
 종료 상태 셋 (L216-231, const enum)
   InProgress  "The task yielded because there are too many requests in progress."
   Blocked     "The task is blocked. It needs more data before it can proceed."
   Done        "There's nothing left to prefetch."

 ★★★ Done 이 "작업 끝" 이 아니다. **phase 가 끝났다**는 뜻이다
   phase 셋 (L247-251) — 숫자가 클수록 먼저 돈다 (주석 L245 "matches heap-sort convention")
     RouteTree   = 2   라우트 트리만 받는다
     Shell       = 1   재사용 가능한 App Shell (param 없는 로딩 상태)
     Speculative = 0   이 링크의 구체적인 세그먼트 데이터
   Done 을 받으면
     RouteTree 였으면   -> Shell 또는 Speculative 로 바꾸고 **큐에 그대로 둔다** (heapResift)
     Shell 이었으면     -> Speculative 로 바꾸고 큐에 둔다
     Speculative 이고 background 일이 있었으면 -> 우선순위를 Background 로 낮추고 큐에 둔다
     그 밖               -> 비로소 heapPop. 작업 완료
 => 취소되지 않은 작업은 **최소 두 번** 패스를 돈다 (RouteTree 패스 + Speculative 패스)

 ★★ Blocked 는 heapPop 으로 **큐에서 뺀다.** 다시 넣는 것은 캐시 쪽이다 → [04]
 ★★ InProgress 는 빼지도 않고 **루프 전체를 멈춘다** (L613 return).
   다음 작업을 보지도 않는다 — 대역폭은 작업마다가 아니라 전역이기 때문이다 → [03]
```

## 동작 흐름

```text
 PrefetchTask 필드 열일곱 (L67-214, 필드 줄 grep 으로 셈 — 마지막 하나는 optional)

 무엇을                       key · treeAtTimeOfPrefetch · fetchStrategy · segmentCacheMap
 무효화 판정                  routeCacheVersion · segmentCacheVersion · onInvalidate
 큐에서의 자리                sortId · priority · phase · _heapIndex
 패스 하나 동안만 유효        hasBackgroundWork · hasPendingResponses · spawnedRuntimePrefetches
 수명                         isCanceled · fallbackRetryStatus · _navigationLockPrefetch

 ★ `_heapIndex` 가 "큐에 있나" 의 판정도 겸한다 (주석 L203 "We also use this field to
   check whether a task is currently in the queue.") — -1 이면 큐 밖이다
 ★ 생성 리터럴(L341-358)은 열여섯을 채운다. `_navigationLockPrefetch` 는
   __NEXT_EXPOSE_TESTING_API 일 때만 L359-361 이 따로 넣는다
```

```text
 한 번의 큐 처리   processQueueInMicrotask  L584-704

 L585  didScheduleMicrotask = false
 L590  now = Date.now()            주석 L587-589 - 시간을 **한 번만** 읽어 인자로 넘긴다
 L593  task = heapPeek(taskHeap)
 L594  while (task !== null && hasNetworkBandwidth(task))       → [03]
 L595-596  task.routeCacheVersion / segmentCacheVersion = 현재 버전   ★ 매 패스 갱신
 L598      exitStatus = pingRoute(now, task)                   → [02]
 L604-607  패스 전용 필드 셋을 리셋한다 (hasBackgroundWork 값은 먼저 지역 변수로 챙긴다)
 L609      switch (exitStatus) — 위 실제 코드
 L701  task === null && inProgressRequests === 0 이면
 L702    cleanup()                  LRU 정리 — 큐도 비고 요청도 없을 때만 → [03]

 ★★ 버전을 **매 패스** 새로 찍는다 (L595-596)
   필드 주석 L77-82 는 "The cache versions at the time the task was initiated" 라고 적는다
   => 실제로는 "마지막 패스를 시작한 때" 의 버전이다
   ※ 그래서 [04]의 isPrefetchTaskDirty 는 "태어난 뒤 무효화됐나" 가 아니라
     "마지막 패스 뒤 무효화됐나" 를 묻는다 — 코드에서 읽은 결과이고 주석이 그렇게 말하지는 않는다
```

```text
 RouteTree -> 다음 phase 고르기   L622-643

 L633  route = readRouteCacheEntry(now, task.key)
 L634-639  route 가 Fulfilled 이고 route.tree.prefetchHints 에 SubtreeHasPartialPrefetching 이면
 L640-642    => Shell,  아니면 => Speculative
   주석 L623-629 - Shell-then-Speculative 두 단계는 Partial Prefetching 을 켠 라우트에만 —
     전역 `partialPrefetching` 설정 또는 세그먼트별 `prefetch: 'partial'` / `'unstable_eager'`

 ★★★ 기본 설정에서는 Shell phase 에 **들어가지 않는다** (규칙 16 확인)
   SubtreeHasPartialPrefetching 을 **처음** 세우는 곳은 create-flight-router-state-from-loader-tree.ts
     L109-117 하나다 (grep 전수). prefetchConfig 가 'partial' · 'unstable_eager' 일 때다.
     그 밖의 참조는 app-router-types.ts 의 enum 정의(L203) · 전파 비트 마스크 SubtreePrefetchHints(L311) ·
     자식의 비트를 부모로 올리는 전파(L331-332)다. 비트를 세우는 곳은 아니다
   그 값의 출처 둘이 모두 cacheComponents 를 요구한다
     전역 partialPrefetching   config.ts L568-572  "`partialPrefetching` requires `cacheComponents`" throw
     `export const prefetch`   get-page-static-info.ts L722-725  "cannot use `export const prefetch = ...`
                               without enabling `cacheComponents`"
 => cacheComponents 를 켜고 **그 위에** Partial Prefetching 을 켜야 Shell 이 돈다
 ★ 라우트가 Rejected 여도 L634 조건이 거짓이라 Speculative 로 간다.
   다음 패스의 pingRootRouteTree 가 Rejected 를 다시 보고 Done → 완료 (L849-851)
```

```text
 완료 처리   L658-689

 주석 L661-669 - "Completion is terminal in the normal flow ... In rare cases, though, a task can
   complete while still registered on an entry from an earlier pass whose subtree the final pass
   no longer reached; when that entry later settles, it re-pings the completed task. The re-run is
   a harmless idempotent no-op, but any per-completion side effect added here must be idempotent or
   once-guarded"
 L670-687  테스트 API 잠금 내비게이션이면 resolveNavigationLockPrefetch 를 부르고 **null 로 지운다**
           주석 L683-685 - 앞의 이유로 여기를 다시 지날 수 있으므로 "at most once"
 L688      heapPop

 ★★ 완료가 "다시는 안 깨어난다" 를 보장하지 않는다. 옛 등록이 남아 있으면
   완료된 작업이 **한 번 더 돈다**. 그래서 완료 부수효과는 한 번만 일어나도록 막아 둔다
```

```text
 깨우는 통로 둘

 pingPrefetchScheduler   L471-478
   didScheduleMicrotask 가 이미 참이면 return — 한 JS 태스크 안의 여러 번을 **한 번으로** 합친다
   아니면 scheduleMicrotask(processQueueInMicrotask)
     L55-65  queueMicrotask 가 없으면 Promise.resolve().then 으로 대신하고,
             오류는 setTimeout 안에서 다시 던진다 (삼키지 않는다)

 pingPrefetchTask(task)  L569-582   — 특정 작업을 큐에 **다시 넣는다**
   L573  task.isCanceled 이면 return
   L575  task._heapIndex !== -1 (이미 큐에 있음) 이면 return
   L580  heapPush,  L581 pingPrefetchScheduler()

 ★ 이름이 비슷하지만 하는 일이 다르다 — 앞의 것은 "큐를 한 번 돌려라",
   뒤의 것은 "이 작업을 큐에 되돌려라". [02 프리페치 큐] 가 둘을 한 줄로 묶었던 것의 구분이다
 pingPrefetchScheduler 호출처 (grep 전수): SCHED 안 L296 · L374 · L432 · L561 · L581,
   밖 offline.ts L115(연결 복구) · lru.ts L106(정리 예약)
 pingPrefetchTask 호출처 (grep 전수): SCCACHE L1351(pingBlockedTasks) · L3013(fallback 재시도 성공) 둘
```

## 결과가 쓰이는 곳

```text
 task.phase
      --> [02]의 pingRootRouteTree 가 L854(RouteTree 면 세그먼트를 안 받음) ·
          L909-912(Shell 이면 StaticShell 로 걷기) · L1003(Shell 이면 동적 갈래 생략)에서 읽는다
      --> [03]의 compareQueuePriority 둘째 기준

 exitStatus
      --> 이 파일 안에서만 쓰인다. InProgress 는 루프 정지, Blocked 는 큐에서 빼기

 task.routeCacheVersion / segmentCacheVersion (매 패스 갱신)
      --> [04]의 isPrefetchTaskDirty 가 현재 버전과 비교한다

 cleanup()
      --> lru.ts L109. 큐가 빈 **뒤에만** 축출해서, 돌고 있는 작업이 방금 읽은 항목을 지우지 않는다
          (주석 L697-700)
```

## 다루지 않는 것

`pingRoute`(L729) 이하 패스 본문은 [02](../02_one-pass/README.md), `hasNetworkBandwidth`(L489)와 힙 비교는 [03](../03_concurrency/README.md), Blocked 된 작업을 다시 깨우는 `pingBlockedTasks` 와 취소·무효화는 [04](../04_end/README.md)다. `lru.ts` 의 `cleanup`(L109-127) 축출 순서와 `deleteMapEntry`, `navigation-testing-lock.ts` 의 `resolveNavigationLockPrefetch` 본문, `fallbackRetryStatus` 를 움직이는 `retryUpgradeableFallbackPrefetch`(SCCACHE L2951) 중 L2963-3019 를 뺀 부분은 이 문서의 범위 밖이다.
