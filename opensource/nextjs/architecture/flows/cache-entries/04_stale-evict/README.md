# 04 수명과 축출

상위: [세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지](../README.md)

항목이 사라지는 길은 셋이다 — `staleAt` 이 지나거나, 버전이 낡거나, LRU 가 50MB 를 넘겨 꼬리부터 잘리거나. 앞의 둘은 **읽을 때** 판정하고(지우는 것도 읽는 쪽이다), 셋째는 **스케줄러가 한가할 때** 돈다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache-map.ts` L260-L298 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache-map.ts#L260-L298))

`packages/next` / `src/client/components/segment-cache` / `lru.ts` L1-L127 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/lru.ts#L1-L127))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L392-L510 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L392-L510))

## 실제 코드

LRU 가 청소를 **예약만** 하고 실제 청소는 스케줄러가 한가해질 때 한다.

```ts
// lru.ts L98-L127
function ensureCleanupIsScheduled() {
  if (lruSize <= maxLruSize) {
    return
  }

  // To schedule cleanup, ping the prefetch scheduler. At the end of its work
  // loop, once there are no queued tasks and no in-progress requests, it will
  // call cleanup().
  pingPrefetchScheduler()
}

export function cleanup() {
  if (lruSize <= maxLruSize) {
    return
  }

  // Evict entries until we're at 90% capacity. We can assume this won't
  // infinite loop because even if `maxLruSize` were 0, eventually
  // `deleteFromLru` sets `head` to `null` when we run out entries.
  const ninetyPercentMax = maxLruSize * 0.9
  while (lruSize > ninetyPercentMax && head !== null) {
    const tail = head.prev
    // In practice, this is never null, but that isn't encoded in the type
    if (tail !== null) {
      // Delete the entry from the map. In turn, this will remove it from
      // the LRU.
      deleteMapEntry(tail)
    }
  }
}
```

```text
 ★★ 넘쳤다고 바로 지우지 않는다

   ensureCleanupIsScheduled  합계가 50MB(L14) 이하면 return, 넘으면 pingPrefetchScheduler()
   cleanup                   넘었으면 **90%** 가 될 때까지 꼬리(head.prev)부터 deleteMapEntry

 스케줄러 쪽 (SCHED L696-703)
   "Run LRU cleanup only when the scheduler is fully idle: no queued tasks and
    no in-progress requests. At that point, all active prefetch tasks have
    finished reading from the cache (moving recently used entries to the front
    of the list), so only genuinely stale data gets evicted."
   if (task === null && inProgressRequests === 0) cleanup()
 => 작업이 도는 동안에는 읽기가 LRU 순서를 계속 바꾼다. 그게 끝난 뒤에 자르면
    **방금 쓰일 항목을 자르지 않는다**
 ★ 90% 까지 내리는 것은 한 번 넘을 때마다 한 항목씩 지우는 것을 피하려는 여유로 보인다
   ※ 이유는 소스가 적지 않았다. 주석(L114-116)은 무한 루프가 안 되는 이유만 적는다
 ★ 50MB 는 어림값이다 — 주석 L11-13 "I chose the max size somewhat arbitrarily.
   Consider setting this based on navigator.deviceMemory ... customizable via the
   Next.js config, too." 지금은 설정으로 바꿀 수 없다
```

## 동작 흐름

```text
 판정은 한 줄이다 — isValueExpired (CMAP L260-266)

   return value.staleAt <= now || value.version < currentCacheVersion

 그리고 그 판정을 부르는 곳 (grep "isValueExpired")
   CMAP L283   lazilyEvictIfNeeded — 조회의 끝에서. 만료면 deleteMapEntry 하고 null
   SCCACHE L1038   upsertSegmentEntry — 후보가 만료면 넣지 않는다
   optimistic-routes.ts L180   예측 패턴이 만료인지

 ★★ 만료 항목을 **따로 쓸어 내는 루프가 없다.** 읽을 때 걸린 것만 지운다
   [프리페치] [01](../../segment-cache/01_entries/README.md)이 인용한 주석 SCCACHE L392-395 —
   "Invalidation does not eagerly evict anything from the cache; entries are
    lazily evicted when read."
 => 안 읽히는 낡은 항목은 LRU 가 넘칠 때까지 메모리에 남는다
```

```text
 staleAt 이 정해지는 자리 — 출처가 여럿이다

 만들 때 (임시)
   라우트 Empty          Infinity                   SCCACHE L652
   라우트 Pending        now + 60초                  SCHED L830    (검색 문자열 뗀 쪽 L762 은 안 바꾼다 — [01])
   세그먼트 Empty        now + 30초                  SCCACHE L1199

 채울 때
   라우트                now + STATIC_STALETIME_MS   L1409
                         -1 (InliningHintsStale)     L1407   즉시 만료 → 다시 받는다
   정적 세그먼트 묶음    readFulfilledStaleAt        L2903-2930  응답의 staleTime 을 **동기로** 끝까지 읽는다
   동적 Full             resolveStaleAt              L4097-4125  async iterable 을 await, 없으면 헤더
   트리 응답의 세그먼트  getStaleAtFromHeader        L4065-4079  `Next-Router-Stale-Time` 헤더
   BFCache 에서 채울 때  navigatedAt + STATIC_STALETIME_MS   L1269 · L1305

 거절할 때
   now + 10초 / -1 (오프라인·동적 rewrite)           ([02])

 공통 하한 — getStaleTimeMs (L122-124)
   return Math.max(staleTimeSeconds, 30) * 1000
   docstring L118-121 - 서버가 너무 짧은 stale 을 보내면 "would prevent anything from
     being prefetched". 그래서 **30초 아래로 내려가지 않는다**
 STATIC_STALETIME_MS 자체도 이 함수를 거친다 (navigate-reducer.ts L19-21) —
   `__NEXT_CLIENT_ROUTER_STATIC_STALETIME`(기본 5분, 주석 L14-15)에 30초 하한
 ★ 서버 값이 NaN 이면 STATIC_STALETIME_MS 로 대신한다 (L2926 · L4074-4076 · L4112-4114)
 ★ readFulfilledStaleAt 와 resolveStaleAt 은 "마지막 값이 이긴다" 는 규칙이 같다
   (docstring L2893-2895). 차이는 버퍼링 여부 — 동기로 thenable status 를 읽을 수 있느냐다
```

```text
 버전 — 무효화는 숫자 하나를 올린다 (SCCACHE L396-456)

   currentRouteCacheVersion / currentSegmentCacheVersion   모듈 변수 둘

   invalidateEntirePrefetchCache  L413   둘 다 ++
   invalidateRouteCacheEntries    L431   라우트만 ++
   invalidateSegmentCacheEntries  L448   세그먼트만 ++
   셋 다 끝에 pingVisibleLinks(…) 와 pingInvalidationListeners(…)

 부르는 곳 (grep 전수)
   server-action-reducer.ts L365  재검증 종류가 StaticAndDynamic 이면 전체
   refresh-reducer.ts L39         세그먼트만 — 주석 L26-29 "The route cache contains the tree
                                  structure ... which doesn't change during a refresh."
                                  (테스트 API 의 bypassCacheInvalidation 이면 건너뛴다 L34-35)
   ppr-navigations.ts L1762       라우트만
   cache.ts L3317                 라우트만 — 예측이 틀렸을 때 ([02])

 항목이 버전을 받는 자리
   라우트  만들 때 (L653)
   세그먼트  Pending 으로 올릴 때 (L1240) — 만들 때는 0 ([01])
 => 항목의 버전 < 현재 버전이면 isValueExpired 가 참. **읽힐 때** 지워진다
 ★ [PPR 내비게이션] [02](../../ppr-navigation/02_fill-segment/README.md)가 본 BFCache 는
   자기 버전(`currentBfCacheVersion`)을 따로 들고 같은 CacheMap 을 쓴다 (bfcache.ts L59 CacheMap · L61 버전 · L109)
```

```text
 pingInvalidationListeners (L493-510)

 L501  invalidationListeners 가 있으면
 L503    **Set 을 통째로 비운다** (null)
 L504    그중 isPrefetchTaskDirty 인 작업만 notifyInvalidationListener
 ★ 더럽지 않은 작업은 **통지 없이 목록에서 빠진다**
   isPrefetchTaskDirty(SCHED L435-451)는 두 버전 · 트리 · Next-Url 중 하나라도 바뀌었으면 참이다
   => 호출처가 전부 버전을 올린 **직후**이므로(위 grep), 실제로는 모든 작업이 더럽다
 ★ 주석 L497-500 - "This is called when the Next-Url or the base tree changes, since those
   may affect the result of a prefetch task. It's also called after a cache invalidation."
   그런데 이 함수의 호출처는 무효화 함수 셋(L421 · L438 · L455)뿐이다 (grep 전수).
   Next-Url · 트리가 바뀔 때 부르는 자리는 **없다**
 notifyInvalidationListener (L473-491) — 콜백을 null 로 지운 뒤 부른다(한 번만).
   사용자 코드라 try/catch 로 감싸고 reportError 로 넘긴다
```

```text
 LRU 의 모양 (LRU L8-96)

   head        모듈 변수 하나. **원형** 이중 연결 리스트 — head.prev 가 꼬리
   lruSize     모듈 변수 하나. 노드 size 의 합

 ★★ LRU 가 **하나**다. routeCacheMap · segmentCacheMap · bfcacheMap, 그리고 테스트 잠금의
   사설 맵(navigation-testing-lock.ts L227)까지 모두 같은 `lru.ts` 모듈 변수를 쓴다 — CMAP L2 가 lru.ts 를 import 하고
   노드(MapEntry)가 곧 리스트 노드다 (CMAP L111-114)
   주석 CMAP L99-102 - "The LRU can contain entries of different value types
     (e.g., both RouteCacheEntry and SegmentCacheEntry)."
 => 50MB 는 캐시 종류별이 아니라 **합계**다. 청소는 종류를 가리지 않고 꼬리부터 자른다

 lruPut(node)          L16-53   next/prev 가 null 이면 **삽입**(lruSize += size, 청소 예약),
                                아니면 **이동**. 그리고 머리로
 updateLruSize(node,n) L55-67   node.size = n. 리스트 밖(next === null)이면 합계는 안 바꾼다
 deleteFromLru(node)   L69-96   리스트 안이면 lruSize -= size 하고 뗀다. 밖이면 아무것도 안 한다

 누가 부르나
   getFromCacheMap  CMAP L256  읽을 때마다 lruPut — **읽기가 곧 LRU 접근**
   setInCacheMap    CMAP L387-388
   setMapEntryValue CMAP L407  updateLruSize
   deleteMapEntry   CMAP L444  deleteFromLru
   setSizeInCacheMap CMAP L496 — 주석 L492-494 "Except during initialization ..., this is
     the only place the `size` field should be updated, to ensure it's in sync with the the LRU." (원문의 "the the" 그대로)
```

```text
 ★★ 승격된 재검증 값은 **리스트 밖**에 놓인다 (CMAP L440-481 ↔ LRU L55-67)

 deleteMapEntry(entry)
   L442  entry.value = null
   L444  deleteFromLru(entry)           → entry.next = entry.prev = null, lruSize -= entry.size
   L478  setMapEntryValue(entry, 재검증 값)
           L407  updateLruSize(entry, size) → entry.next === null 이라 **합계에 더하지 않는다**
           L417  deleteMapEntry(재검증 노드) → 그 노드의 size 를 lruSize 에서 뺀다
 => 승격된 값은 맵에는 있지만 LRU 리스트에도 합계에도 없다.
    다음에 누가 그 자리를 읽어 getFromCacheMap 의 lruPut(CMAP L256)이 돌 때 다시 들어간다
 ※ 그 사이에는 cleanup 이 이 값을 자를 수 없고 합계도 그만큼 작다.
   읽히지 않으면 계속 그렇다 — 코드 경로에서 읽히는 결과이고, 실제로 얼마나 자주 생기는지는 모른다
```

```text
 크기의 출처 — 응답 바이트를 항목 수로 나눈다

   라우트 트리 응답   L2074 · L2141   응답 전체 크기를 그 라우트 항목에
   정적 묶음          L2646           응답 크기 / 묶음의 세그먼트 수  ([02]의 이중 청구 주석과 어긋남)
   동적 Full          L3135           받은 바이트가 늘 때마다 채워진 항목 수로 다시 나눈다
   동적 버퍼링        L3354           응답 크기 / 채워진 항목 수
 => 항목의 크기는 **측정값이 아니라 배분값**이다. rsc 객체의 실제 메모리를 재지 않는다
   BFCache 항목            고정 100    bfcache.ts L96-101 (TODO "This is just a heuristic")
 ★ 새로 만든 항목은 size 0 (L649 · L1213). 그리고 **끝내 크기를 받지 못하는** 항목이 많다 —
   분리 사본, insertEmpty(L3805), 내비게이션 · 첫 로드의 writePrerenderResponseIntoCache,
   트리 응답 잔여 가지(L3473)가 쓴 항목은 끝까지 0 바이트다 ([02])
```

## 결과가 쓰이는 곳

```text
 lazilyEvictIfNeeded 의 null
      --> [03]의 조회가 같은 층의 Fallback 으로 내려간다. 낡은 구체 항목 뒤의 셸이 드러난다

 버전 증가
      --> 다음 읽기부터 옛 항목이 없는 것이 된다. pingVisibleLinks 가 보이는 링크의
          프리페치를 다시 건다 → 스케줄러가 새 Empty 항목을 만든다 ([01])

 cleanup
      --> deleteMapEntry. 재검증 칸이 있으면 **승격**이 일어난다 (위 ★★)

 onInvalidate 콜백
      --> router.prefetch(href, { onInvalidate }) 로 등록한 사용자 코드
```

## 다루지 않는 것

`pingVisibleLinks`(`links.ts`)가 보이는 링크를 다시 프리페치하는 쪽, `startRevalidationCooldown`(SCHED L285)과 재검증 직후 300ms 대기([프리페치] [02](../../segment-cache/02_scheduler/README.md)), `invalidateBfCache` 와 `bfcache.ts` 의 `DYNAMIC_STALETIME_MS` · `unstable_dynamicStaleTime` 처리, 서버가 `staleTime` iterable 과 `Next-Router-Stale-Time` 헤더를 만드는 쪽, `staleTimes` 설정이 `__NEXT_CLIENT_ROUTER_STATIC_STALETIME` 이 되는 define-env 경로, `router.prefetch` 의 `onInvalidate` 옵션을 받는 `app-router-instance.ts` 쪽, 테스트 잠금의 사설 맵이 풀릴 때 버려지는 방식(`navigation-testing-lock.ts`)은 이 문서의 범위 밖이다.
