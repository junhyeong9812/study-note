# 03 맵과 키

상위: [세그먼트 캐시 항목이 만들어지고 채워지고 버려지기까지](../README.md)

`CacheMap` 은 키가 **튜플**인 트리다. 튜플의 칸 하나가 트리의 한 층이고, 어느 칸이든 `Fallback` 이라는 특수 키를 가질 수 있다. 조회는 정확히 맞는 칸이 없으면 그 층의 `Fallback` 으로 내려간다. 그 튜플을 만드는 것이 `vary-path.ts` 이고, 두 항목이 같은 자리를 다툴 때의 규칙이 `upsertSegmentEntry` 다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `cache-map.ts` L161-L481 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache-map.ts#L161-L481))

`packages/next` / `src/client/components/segment-cache` / `vary-path.ts` L112-L437 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/vary-path.ts#L112-L437))

`packages/next` / `src/client/components/segment-cache` / `cache.ts` L993-L1192 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/cache.ts#L993-L1192))

## 실제 코드

조회의 본체다. 층마다 **정확 → Fallback** 순으로 재귀한다.

```ts
// cache-map.ts L300-L372
function getEntryWithFallbackImpl<V extends MapValue>(
  now: number,
  currentCacheVersion: number,
  entry: MapEntry<V>,
  keys: VaryPath | null,
  isRevalidation: boolean,
  previousKey: unknown | null,
  onlyMatchFulfilled: boolean
): MapEntry<V> | null {
  // This is similar to getExactEntry, but if an exact match is not found for
  // a key, it will return the fallback entry instead. This is recursive at
  // every level, e.g. an entry with keypath [a, Fallback, c, Fallback] is
  // valid match for [a, b, c, d].
  //
  // It will return the most specific match available.
  //
  // When `onlyMatchFulfilled` is true, terminal entries that aren't Fulfilled
  // are treated as non-matches, so the recursion will continue searching for
  // a Fallback match. See getFromCacheMap for the rationale.
  let key
  let remainingKeys: VaryPath | null
  if (keys !== null) {
    key = keys.value
    remainingKeys = keys.parent
  } else if (isRevalidation && previousKey !== Revalidation) {
    // During a revalidation, we append an internal "Revalidation" key to
    // the end of the keypath.
    key = Revalidation
    remainingKeys = null
  } else {
    // There are no more keys. This is the terminal entry.
    return lazilyEvictIfNeeded(
      now,
      currentCacheVersion,
      entry,
      onlyMatchFulfilled
    )
  }
  const map = entry.map
  if (map !== null) {
    const existingEntry = map.get(key)
    if (existingEntry !== undefined) {
      // Found an exact match for this key. Keep searching.
      const result = getEntryWithFallbackImpl(
        now,
        currentCacheVersion,
        existingEntry,
        remainingKeys,
        isRevalidation,
        key,
        onlyMatchFulfilled
      )
      if (result !== null) {
        return result
      }
    }
    // No match found for this key. Check if there's a fallback.
    const fallbackEntry = map.get(Fallback)
    if (fallbackEntry !== undefined) {
      // Found a fallback for this key. Keep searching.
      return getEntryWithFallbackImpl(
        now,
        currentCacheVersion,
        fallbackEntry,
        remainingKeys,
        isRevalidation,
        key,
        onlyMatchFulfilled
      )
    }
  }
  return null
}
```

```text
 ★★★ 정확한 자식이 있어도 그 아래에서 실패하면 **같은 층의 Fallback 으로 되돌아간다** (L343-369)

   L340  existingEntry = map.get(key)
   L343    있으면 재귀 — 결과가 null 이 아니면 return
   L357  fallbackEntry = map.get(Fallback)
   L360    있으면 그쪽으로 재귀 (remainingKeys 는 같다)

 => 되추적(backtracking)이다. docstring L32 가 "retrieval is an O(n ^ 2) operation" 이라 적는다
    ※ 층마다 두 갈래를 다 볼 수 있으니 최악은 그보다 클 수 있다 — 주석의 표현을 그대로 옮긴다
 => "가장 구체적인 것부터" — 주석 L314 "It will return the most specific match available."
 ★★ 끝에 닿으면 lazilyEvictIfNeeded(L268-298)가 판정한다 —
     만료면 **그 자리에서 지우고** null   (L283-288)
     onlyMatchFulfilled 인데 Fulfilled 가 아니면 null   (L290-294)
   null 이 되돌아오면 위 층이 Fallback 을 시도한다.
   => 낡은 구체 항목은 "없는 것" 이 되고, 그 뒤에 숨은 Fallback 항목이 드러난다
   ★ 조회가 **맵을 바꾼다.** 읽기 함수가 항목을 지운다
```

## 동작 흐름

```text
 맵의 모양 (CMAP L87-137)

 MapValue      ref · size · staleAt · version · status        ← 항목(값)이 갖춰야 할 다섯
 MapEntry      parent · key · map(자식 Map) · value            ← 트리 노드
               prev · next · size                              ← LRU 연결 리스트 노드를 **겸한다**
 CacheMap<V>   = 루트 MapEntry (L137)

 Fallback    = {} as FallbackType   (L140)   export — vary-path.ts 가 쓴다
 Revalidation = {}                  (L144)   export 하지 않는다 — "shouldn't leak outside of this module"

 ★ 두 특수 키가 **빈 객체의 동일성**으로 구별된다. 문자열이 아니므로 사용자 값과 겹칠 수 없다
 ★★ 값과 노드가 서로를 가리킨다 — value.ref → 노드, 노드.value → 값
   docstring L45-53 - "a value cannot be stored at multiple keypaths simultaneously" 그리고
   그 덕에 `ref` 로 노드를 바로 찾아 O(n^2) 조회를 건너뛴다
   => 키를 다시 건다는 것은 **값을 새 노드로 옮기고 옛 노드를 지우는 것**이다
```

```text
 setInCacheMap(map, keys, value, isRevalidation)                         CMAP L374-389

 L383  entry = getOrInitialize(map, keys, isRevalidation)   정확 경로만 따라가며 없으면 만든다
 L384  setMapEntryValue(entry, value)                        L391-419
         L392  이 노드에 다른 값이 있으면 그 값의 ref 를 끊는다 (dropRef)   ← 덮어쓰기
         L402  oldEntry = value.ref                         이 값이 원래 있던 노드
         L404  entry.value = value; value.ref = entry
         L409  oldEntry 가 다른 노드이고 아직 이 값을 들고 있으면
         L417    deleteMapEntry(oldEntry)                    ← **옛 자리를 지운다 = 이동**
 L387  lruPut(entry)                                         ([04])
 L388  updateLruSize(entry, value.size)

 getOrInitialize (L161-227) 의 재검증 처리
   키를 다 쓴 뒤 isRevalidation 이면 내부 키 Revalidation 을 한 층 더 붙인다 (L180-192)
   ★ 단 정상 노드가 비어 있으면 **정상 자리를 그대로 돌려준다** (L187-189)
   주석 L184-186 - "if the parent entry is currently empty, we don't need to store
     this as a revalidation entry. Just insert the revalidation into the normal slot."
```

```text
 deleteMapEntry(entry)                                                    CMAP L440-481

 L442  entry.value = null
 L444  deleteFromLru(entry)
 L448  자식 Map 이 없으면 — 빈 부모를 **거슬러 올라가며** 지운다 (L452-472)
 L473  자식 Map 이 있으면
 L476    revalidatingEntry = map.get(Revalidation)
 L477    값이 있으면 setMapEntryValue(entry, 그 값)   ← **재검증 항목을 정상 자리로 승격**
         주석 L474-475 - "promote it to a "normal" entry, since the normal one was just deleted."

 ★★ 이 승격이 두 곳의 주석에 등장한다
   upsertSegmentEntry(SCCACHE L1082-1098) - 교체할 때 **먼저 지우지 않는 이유**가 이것이다.
     지우면 재검증 칸의 Pending 항목이 승격되고, 바로 이어지는 삽입이 그것을 덮어
     진행 중인 재검증이 맵에서 사라진다 → 다음 패스가 **같은 요청을 한 번 더 띄운다**
   evictShadowingSegmentEntries(SCCACHE L1148-1153) - 지운 자리에 settled 재검증 값이
     올라올 수 있으니 **매번 처음부터 다시 읽는다**
 ★ 승격된 값의 LRU 계정은 [04]에서 본다 (승격 직후 목록 밖에 있다)
```

```text
 키 만들기 — vary path 는 **연결 리스트**다 (VARY L28-52)

   { id, value, isRootParam, parent }
   id    파라미터 이름 · 검색 파라미터는 '?' · 구조 노드(요청 키 등)는 null
   value 구체값 · null · Fallback

 조회 순서 = 리스트의 머리부터 parent 쪽으로 (CMAP L178-179, L322-323)

   라우트    pathname -> search('?') -> Next-Url                     getRouteVaryPath L112-135
   레이아웃  requestKey -> 가장 깊은 파라미터 -> ... -> 루트 파라미터   finalizeLayoutVaryPath L180-191
   페이지    requestKey -> search('?') -> 파라미터들                  finalizePageVaryPath L200-219
   메타데이터 페이지와 같다. 단 첫 값이 `pageRequestKey + HEAD_REQUEST_KEY`  finalizeMetadataVaryPath L228-273

 파라미터 노드는 트리를 만들며 붙인다 — SCCACHE L1626 appendLayoutVaryPath(부모 경로, 파라미터 키,
   파라미터 이름, IsRootLayoutOrAbove 힌트)
 ★ docstring L20-23 - "A segment's vary path is a pure function of a segment's position
   in a particular route tree and the (post-rewrite) URL that is being queried."
   => 같은 세그먼트를 같은 URL 로 읽으면 **언제나 같은 경로**다. 그래야 맵의 층이 맞는다
 ★ 레이아웃에는 검색 파라미터 칸이 **아예 없다** (L316-318 주석 — 페이지만 검색 파라미터를 가질 수 있다)
 ★ 모든 노드에 `isRootParam` 을 boolean 으로 늘 넣는 이유 (L47-49) —
   "so that every VaryPath node shares a single hidden class, keeping the cache hot
    paths monomorphic." 성능 이유다
```

```text
 키를 넓히는 함수 넷 — 구체 경로를 복제하며 칸을 Fallback 으로 바꾼다

 getSegmentVaryPathForRequest(strategy, tree)   VARY L275-353   **요청 전에**
   StaticShell · RuntimeShell => tree.shellVaryPath
   페이지이고 Full · PPRRuntime 가 아니면 => 검색 파라미터 칸만 Fallback
     주석 L320-322 - "Static prefetches never include search params"
   그 밖 => tree.varyPath 그대로
 getFulfilledSegmentVaryPath(original, varyParams)  L385-413   **응답 후** — 서버가 준 목록에 없는 파라미터를 Fallback
 getShellSegmentVaryPath(original)                  L415-437   구조 노드와 루트 파라미터만 남기고 Fallback
 getFulfilledRouteVaryPath(…, couldBeIntercepted)   L137-163   가로채기가 없으면 Next-Url 칸을 Fallback

 ★★ 검색 파라미터 노드는 id 가 '?' 이다 (L123 · L212).
   getFulfilledSegmentVaryPath 는 id 가 null 이 아니고 varyParams 에 없으면 Fallback 으로 바꾸므로
   **서버가 '?' 를 목록에 넣지 않으면 검색 파라미터도 Fallback 이 된다**
   서버가 그 짝을 맞춘다 — server/app-render/vary-params.ts L255-285 의 Proxy 가
   searchParams 의 get · has · ownKeys 를 전부 **한 표식 '?'** 로 기록한다
     주석 L262-264 - "All accesses bucket into the single sentinel '?'; the segment is
       keyed by the whole query string."
   => 검색 파라미터를 하나라도 건드리면 쿼리 문자열 **전체**가 키에 남고,
      전혀 안 건드리면 쿼리 문자열이 무엇이든 한 항목을 공유한다
      (varyParams 가 null 이 아니고 Full 응답이 아닐 때만 — [02]의 다시 걸기 규칙)
 ★ getSegmentVaryPathForRequest 의 주석 L294-299 -
   "This result of this function is not stored anywhere. It's only used to access
    the cache a single time." 그리고 TODO — 나중에 "vary mask" 로 바꿀 계획이다
```

```text
 라우트 키의 재료 — cache-key.ts (61줄)

 CKEY L20-31  createCacheKey(href, nextUrl) = { pathname, search, nextUrl }
   불투명 타입(Opaque, L2)으로 이 모듈 밖에서 못 만든다 (주석 L4)
   TODO L16 - "Eventually the dynamic params will be added here, too."
 CKEY L46-61  splitPathnameIntoParts — split + filter 대신 손 루프
   docstring L38-44 - split 이 packed/holey 배열을 섞어 돌려주면 이후 호출 지점이
   다형이 되어 "wrong map" 역최적화가 반복된다. push 로 채운 배열은 언제나 packed 다
 ★ 이 파일에는 키 **비교**가 없다. 비교는 CacheMap 의 층별 `Map.get` 이 한다 —
   pathname · search · nextUrl 이 문자열이므로 값 비교다
```

```text
 같은 자리를 다툴 때 — upsertSegmentEntry(now, map, varyPath, candidate, lookupVaryPath)   SCCACHE L1012-1109

 L1038  후보가 만료면 => return null                    (버전은 [01]의 upgradeToPendingSegment 가 찍었다)
 L1043  existingEntry = getFromCacheMap(…, varyPath, …)    ← Fallback 탐색을 거친 결과다
 L1055  isExistingSegmentEntryPreferred(existing, candidate) 이면
 L1068    => return null                                 후보를 **넣지 않을 뿐** 건드리지 않는다
 L1075  기존이 Empty · Pending 이면 pingBlockedTasks(existing)
 L1102  setInCacheMap(map, varyPath, candidate, false)    **지우지 않고 덮는다**
 L1104  lookupVaryPath 가 있으면 evictShadowingSegmentEntries(…)
 L1108  => return candidate

 isExistingSegmentEntryPreferred (L993-1010) — 기존이 이기는 조건 둘
   (a) 전략이 다르고 후보 전략이 더 많이 줄 수 없다  (canNewFetchStrategyProvideMoreContent)
   (b) 기존은 완전하고 후보는 부분이다
   docstring L982-984 - "On an exact tie — same fetch strategy, same partialness —
     this returns false, so the candidate replaces the existing entry."
 ★ (b) 옆의 TODO L1007 - "(TODO: can this be true if `candidateEntry.fetchStrategy >= existingEntry.fetchStrategy`?)"
   작성자도 두 조건의 겹침을 확신하지 않는다

 ★★ 후보를 변형하지 않는 이유 (주석 L1059-1067)
   "it may already have been fulfilled, resolving its promise to a waiter that holds
    the entry and reads `rsc` off it later. A navigation seed is such a waiter, via
    `waitForSegmentCacheEntry`. Nulling `rsc` after the fact resolves that read to
    `null`, so the waiter loses the data it was about to render."
 => 진 후보도 **기다리던 쪽에게는 유효한 데이터**다. 맵에서 빠질 뿐이다
 ★ L1043 의 조회가 Fallback 을 거치므로, 비교 대상은 "같은 키의 항목" 이 아니라
   "그 키로 읽으면 나오는 항목" 이다. 그런데 L1102 의 set 은 **정확한 키**에 한다
   ※ 기존이 더 일반적인 자리(Fallback)에 있었으면 덮이지 않고 둘 다 남는다 — 코드에서 읽히는 결과다
```

```text
 가림 축출 — evictShadowingSegmentEntries(now, map, lookupVaryPath, candidate)   SCCACHE L1142-1192

 docstring L1115-1127 이 문제를 적는다
   응답이 요청보다 **더 일반적인** 키로 쓰일 수 있다 (varyParams 로 넓혔을 때).
   그런데 같은 Fallback 사슬의 **더 구체적인** 자리에 낡은 항목이 남아 있으면,
   조회는 가장 구체적인 것을 이기게 하므로 새 항목이 **영영 안 보인다.**
   "That both wastes the completed request and can loop: a prefetch task that
    revalidated the segment reads back the same stale entry, decides it needs to
    revalidate again, and repeats forever."

 L1157  for (i = 0; i < 32; i++)
 L1158    shadow = getFromCacheMap(…, lookupVaryPath, …)       ← 구체 키로 읽어 본다
 L1166    null 이거나 후보 자신이면 => return                  후보가 보인다
 L1171    Fulfilled · Rejected 가 아니면 => return             Pending · Empty 는 건드리지 않는다
 L1179    기존이 이기면 => return
 L1189    pingBlockedTasks(shadow); deleteFromCacheMap(shadow)   그리고 다시 돈다

 ★ 32 는 방어적 상한이다 (주석 L1154-1156 — 실제 사슬은 vary path 길이로 묶인다)
 호출처 (grep 전수) — upsertSegmentEntry L1105, fulfillEntrySpawnedByRuntimePrefetch L3792 · L3832
```

## 결과가 쓰이는 곳

```text
 getFromCacheMap 의 반환 (V | null)
      --> [01]의 읽기 함수 넷과 readOrCreate*, 그리고 upsert 가 "기존 항목" 으로 쓴다
      --> bfcache.ts 의 읽기 셋(L152 · L172 · L193)도 같은 함수를 쓴다

 value.ref
      --> deleteFromCacheMap(L421) · setSizeInCacheMap(L483)이 노드를 바로 찾는다

 tree.varyPath / tree.shellVaryPath
      --> 라우트 트리를 만들 때 한 번 계산해 RouteTree 에 둔다 (SCCACHE L1707 등).
          읽기는 언제나 tree.varyPath, 쓰기는 이 문서의 넓히는 함수 넷 중 하나

 Fallback
      --> vary-path.ts 가 칸에 넣고, CacheMap 조회가 층마다 찾아본다
```

## 다루지 않는 것

`bfcache.ts`(201줄)가 같은 `CacheMap` 을 쓰는 방식과 `BFCacheEntry` 의 필드, `reifyRouteTree`(optimistic-routes.ts)가 예측 트리의 vary path 를 다시 계산하는 쪽, `clonePageVaryPathWithNewSearchParams`(VARY L355-374)를 쓰는 `deprecated_createOptimisticRouteTree`(SCCACHE L813), `getCacheKeyForDynamicParam`(`route-params.ts`)이 파라미터 값을 키 문자열로 바꾸는 규칙, `appendSegmentRequestKeyPart` · `HEAD_REQUEST_KEY` 의 요청 키 인코딩(`segment-value-encoding.ts`), 서버가 varyParams 에 무엇을 넣는지는 이 문서의 범위 밖이다.
