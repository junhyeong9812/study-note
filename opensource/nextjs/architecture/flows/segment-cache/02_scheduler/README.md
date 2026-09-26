# 02 프리페치 큐

상위: [프리페치가 쌓이고 내비게이션이 그것을 쓰기까지](../README.md)

2741줄이다. **동시 요청 수를 세어 네트워크 대역폭을 제어한다.** hover 한 링크에는 한도를 따로 준다 — 12 대 4.

## 위치

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L489-L528 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L489-L528))

`packages/next` / `src/client/components/segment-cache` / `scheduler.ts` L530-L541 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/scheduler.ts#L530-L541))

## 실제 코드

한도가 숫자 둘로 박혀 있다. 다만 그 앞에 **무조건 막는 관문이 둘** 있다.

```text
 scheduler.ts L491-505
   if (process.env.__NEXT_USE_OFFLINE) {
     const { getOffline } = require('../offline') as typeof import('../offline')
     if (getOffline()) {
       return false            // 오프라인이면 아예 안 보낸다
     }
   }

   // Check if we're within the revalidation cooldown window
   if (revalidationCooldownTimeoutHandle !== null) {
     return false              // 재검증 직후 300ms 는 CDN 전파를 기다린다
   }

 scheduler.ts L514-527
   if (task.priority === PrefetchPriority.Intent) {
     // The most recently hovered link is allowed to exceed the default limit.
     //
     // The goal is to always have enough bandwidth to start a new prefetch
     // request when hovering over a link.
     //
     // However, because we don't abort in-progress requests, it's still possible
     // we'll run out of bandwidth. When links are hovered in quick succession,
     // there could be multiple hover requests running simultaneously.
     return inProgressRequests < 12
   }

   // The default limit is lower than the limit for a hovered link.
   return inProgressRequests < 4
```

```text
 => hover 한 링크(Intent)는 **12**, 그 밖은 **4**
 ★★ 그 전에 오프라인·재검증 쿨다운이 우선한다. 한도는 **셋째 관문**이다
   재검증 쿨다운은 `startRevalidationCooldown`(L285)이 켜고
   `REVALIDATION_COOLDOWN_MS = 300`(L274) 뒤 스스로 풀면서
   `pingPrefetchScheduler()` 로 큐를 다시 돌린다
   주석 L273 - "CDN cache propagation delay after revalidation"
   => [재검증]에서 서버 쪽 무효화를 본 그 지점의 클라이언트 짝이다
 ★ 주석이 한계를 스스로 인정한다 — 진행 중인 요청을 **중단하지 않으므로**
   링크를 빠르게 연달아 hover 하면 대역폭이 바닥날 수 있다
```

## 동작 흐름

```text
 scheduler.ts 의 공개 표면

 L67   type PrefetchTask
 L253  type PrefetchSubtaskResult<T>
 L285  startRevalidationCooldown()
 L300  type IncludeDynamicData = null | 'full' | 'dynamic'
       ★ 선언뿐이다 — 저장소 전체에서 이 이름의 참조가 이 한 줄이다
 L317  schedulePrefetchTask(...)
 L379  cancelPrefetchTask(task)
 L391  reschedulePrefetchTask(...)
 L435  isPrefetchTaskDirty(...)
 L471  pingPrefetchScheduler()
 L569  pingPrefetchTask(task)
 L2570 subtreeHasSpeculativePrefetch(...)

 => 2741줄 중 export 가 열한 개다. 나머지는 내부 스케줄링이다
```

```text
 ★★ Intent 우선순위는 **언제나 하나**다

 주석 L269-270
   "scheduled at Intent priority. There's only ever a single task at Intent
    priority at a time. We reserve special network bandwidth for this task only."
 주석 L455  "task at Intent priority. There must only be one such task at a time."

 L419  task === mostRecentlyHoveredLink ? PrefetchPriority.Intent : priority
       주석 L418 - 재스케줄된 우선순위가 더 낮아도 **Intent 를 유지한다**
 => `mostRecentlyHoveredLink` 라는 모듈 변수가 그 "하나" 를 가리킨다
 => [README]에서 본 대로, 새 Intent 가 오면 이전 것은 Default 로 내려간다
```

```text
 ★★★ 결과를 await 하지 않는다 (L530-541)

 주석 L533-541
   "When the scheduler spawns an async task, we don't await its result.
    Instead, the async task writes its result directly into the cache, then
    pings the scheduler to continue.

    We process server responses streamingly, so the prefetch subtask will
    likely resolve before we're finished receiving all the data. The subtask
    result includes a promise that resolves once the network connection is
    closed. The scheduler uses this to control network bandwidth by tracking
    and limiting the number of concurrent requests."

 => 하위 작업이 **캐시에 직접 쓰고** 스케줄러를 깨운다(ping).
    스케줄러는 반환값을 기다리지 않는다
 ★ 그래서 "연결이 닫혔다" 를 따로 알아야 한다 —
   그것이 `PrefetchSubtaskResult`(L253)에 든 약속이고,
   동시 요청 수를 세는 근거다
 => 응답이 스트리밍이라 "작업 완료" 와 "연결 종료" 가 다른 시점이다.
    대역폭은 **후자**로 센다

 L542  inProgressRequests++
 L544    result === null 이면 (스트림을 잡기 전에 실패한 경우)
 L547      => onPrefetchConnectionClosed()   주석 - "Assume the connection is closed"
 L551    그 밖 => result.closed.then(onPrefetchConnectionClosed)
 L556  onPrefetchConnectionClosed  inProgressRequests-- 하고 pingPrefetchScheduler()
 ★ 실패 경로에서 카운트가 새지 않게 **닫힘을 가정**한다.
   안 그러면 한도 4 가 영구히 줄어든다
```

```text
 ★ TODO 둘이 현재 한계를 말한다 (L507-512)

 L507-510  "Also check if there's an in-progress navigation. We should never
            add prefetch requests to the network queue if an actual navigation is
            taking place, to ensure there's sufficient bandwidth for render-blocking
            data and resources."
   => 지금은 **실제 내비게이션 중에도 프리페치를 계속 보낸다**

 L512  "Consider reserving some amount of bandwidth for static prefetches."
   => 정적 프리페치용 대역폭은 따로 없다
```

## 결과가 쓰이는 곳

```text
 캐시 항목 (하위 작업이 직접 쓴다)
      --> [01]의 routeCacheMap · segmentCacheMap.
          스케줄러를 거치지 않고 바로 들어간다

 inProgressRequests 카운트
      --> 다음 작업을 시작할지 말지. 12 / 4 한도의 기준

 mostRecentlyHoveredLink
      --> Intent 우선순위를 가진 그 하나.
          `<Link>` 에 마우스를 올리면 이 값이 바뀐다

 pingPrefetchScheduler / pingPrefetchTask
      --> 하위 작업이 끝난 뒤 스케줄러를 깨우는 통로.
          await 대신 ping 을 쓰는 설계의 짝이다
```

## 다루지 않는 것

`PrefetchTask`(L67)의 필드와 작업 상태 전이, `schedulePrefetchTask`(L317) / `cancelPrefetchTask`(L379) / `reschedulePrefetchTask`(L391) / `isPrefetchTaskDirty`(L435) / `pingPrefetchScheduler`(L471) / `pingPrefetchTask`(L569)의 본문, `startRevalidationCooldown`(L285)과 재검증 쿨다운, `IncludeDynamicData`(L300)가 선언만 있고 쓰이지 않는 이유, `subtreeHasSpeculativePrefetch`(L2570)와 추측 프리페치, 우선순위 큐의 자료구조와 작업 선택 규칙, `<Link>`(`links.ts` 401줄)가 hover 를 감지해 `mostRecentlyHoveredLink` 를 세우는 쪽, `PrefetchSubtaskResult`(L253)의 약속이 실제로 해소되는 자리는 이 문서의 범위 밖이다.
