# 01 패턴을 배우기

상위: [가져온 적 없는 라우트 트리를 예측하기까지](../README.md)

`discoverKnownRoute` 는 호출처 여섯(첫 로드 · 미스 내비게이션 · 액션 redirect · 프리페치 둘 · 재시도 표시)에서만 불린다. 새로고침(refresh-reducer L78) · 복원(restore-reducer L56) · 동적 응답(PPRNAV L1837) · 서버 패치 · 액션의 redirect 아닌 경로는 서버 트리를 받고도 **배우지 않는다**. 트리와 URL 조각을 한 칸씩 나란히 걸으며, 둘이 끝까지 맞으면 그 라우트 캐시 항목을 트라이의 잎에 **패턴**으로 매단다. 어디서든 어긋나면 리라이트로 보고 패턴을 포기한다 — 항목은 캐시에만 넣는다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `optimistic-routes.ts` L220-L718 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/optimistic-routes.ts#L220-L718))

## 실제 코드

순회가 페이지 잎에 닿았을 때다. 여기서 패턴이 저장되거나, 이미 있는 패턴이 돌아간다.

```ts
// optimistic-routes.ts L679-L717
  // Reached a page node. Create/get the route cache entry and store as a
  // pattern. First, check if there's already a pattern for this route.
  const existingPattern = readPattern(now, knownRoutePart)
  if (existingPattern !== null) {
    // If this route has a dynamic rewrite, mark the existing pattern.
    if (hasDynamicRewrite) {
      existingPattern.hasDynamicRewrite = true
    }
    return existingPattern
  }

  // Get or create the entry
  let entry: FulfilledRouteCacheEntry
  if (existingEntry !== null) {
    // Already have a fulfilled entry, use it directly. It's already in the
    // route cache map.
    entry = existingEntry
  } else {
    // Create the entry and insert it into the route cache map.
    entry = writeRouteIntoCache(
      now,
      pathname as NormalizedPathname,
      search,
      nextUrl,
      fullTree,
      metadataVaryPath,
      couldBeIntercepted,
      canonicalUrl,
      supportsPerSegmentPrefetching
    )
  }

  if (hasDynamicRewrite) {
    entry.hasDynamicRewrite = true
  }

  // Store as pattern
  knownRoutePart.pattern = entry
  return entry
```

```text
 ★★★ 이미 패턴이 있으면 **이번 URL 의 항목을 캐시에 넣지 않는다**

 L681  existingPattern = readPattern(now, knownRoutePart)
 L682  있으면 => return existingPattern          ← writeRouteIntoCache(L698)에 닿지 않는다

 docstring L207-208 - "Routes are always inserted into the cache regardless of
   whether the URL matches the route structure."
 => pendingEntry 를 넘긴 호출(프리페치 둘 — SCCACHE L2119 · L3445)에서는 맞다.
    항목이 L239 에서 이미 fulfill 되어 캐시 맵 안에 있기 때문이다
 => pendingEntry 가 null 인 호출 넷(첫 로드 · 캐시 미스 내비게이션 · 액션 redirect · 재시도)에서는
    같은 모양의 패턴이 이미 있으면 **이 URL 은 캐시에 들어가지 않고**, 돌아오는 값은
    **다른 URL 로 배운 항목**이다 (canonicalUrl 도 그 URL 의 것)
 ★ 그래도 문제가 드러나지 않는 이유 — 여섯 호출처가 **전부 반환값을 버린다** (grep, 대입하는 호출 0개).
   docstring L218 "Returns the fulfilled route cache entry" 를 쓰는 곳이 없다
 ※ 이 URL 은 다음에 readRouteCacheEntry 가 [02]의 예측으로 다시 지어낼 것이다 — 단 optimisticRouting 이
   켜져 있고 경로의 모든 동적 층이 형제를 알 때만이다. 플래그가 꺼져 있거나(트라이는 플래그와 무관하게
   쌓인다) webpack 개발에서 staticChildren 이 null 인 층이면 예측도 캐시 삽입도 없다. 실행해 확인하지는 않았다

 ★★ L716 `knownRoutePart.pattern = entry` — 패턴은 **복사본이 아니라 라우트 캐시 항목 그 객체**다.
   나중에 누가 그 항목에 hasDynamicRewrite 를 세우면 패턴도 같이 바뀐다 → [03]
```

## 동작 흐름

```text
 discoverKnownRoute(now, pathname, search, nextUrl, pendingEntry, routeTree,
                    metadataVaryPath, couldBeIntercepted, canonicalUrl,
                    supportsPerSegmentPrefetching, hasDynamicRewrite)      OPTR L220-293

 L235  pathnameParts = splitPathnameIntoParts(pathname)       '/' 로 자르고 빈 조각은 버린다 (cache-key.ts L46-61)
 L237  pendingEntry 가 있으면
 L239    fulfilledEntry = fulfillRouteCacheEntry(...)           캐시 맵 안의 항목을 채운다
 L248    hasDynamicRewrite 면 표시
 L254    discoverKnownRoutePart(root, ..., existingEntry = fulfilledEntry, ...)   반환값을 버린다
 L271    => return fulfilledEntry
 L276  => return discoverKnownRoutePart(root, ..., existingEntry = null, ...)

 누가 pendingEntry 를 넘기는가 (호출처 여섯 전수)
   SCCACHE L2119 · L3445                 entry       프리페치 — readOrCreateRouteCacheEntry 가 만든 Pending
   create-initial-router-state.ts L108   null        첫 로드
   SCNAV L555                            null        캐시 미스 내비게이션
   server-action-reducer.ts L488         null        액션 redirect
   PPRNAV L1743                          null        재시도 (hasDynamicRewrite = true)
```

```text
 discoverKnownRoutePart   OPTR L368-718 (351줄) — 트리 한 노드, URL 한 칸

 L386  segment = routeTree.segment,  urlPart = (L387-388) partIndex < pathnameParts.length ? pathnameParts[partIndex] : null

 문자열 세그먼트 (L393-428)
 L394    doesStaticSegmentAppearInURL(segment) 이면           (route-params.ts L155)
 L399      urlPart 가 없거나 segment 와 다르면 => 리라이트 ①
 L414-421  staticChildren(없으면 새 Map)에 이 이름의 자식을 get-or-create
 L425      URL 한 칸 전진
         아니면 **투명** — '' · __PAGE__ · (group) · __DEFAULT__ · /_not-found 는
         URL 에 안 나타나므로 같은 노드에 머문다 (route-params.ts L163-176)

 동적 세그먼트 [paramName, paramCacheKey, paramType, staticSiblings] (L429-605)
 L436    optional catch-all('oc')이 아닌데 URL 이 바닥났으면   => 리라이트 ②
 L455    urlPart 가 staticSiblings 에 있으면                  => 리라이트 ③  (정적 형제 이름인데 동적으로 렌더됐다)
 L483    paramType 별로 "서버가 렌더한 값" 과 URL 을 비교
           'd'        canonicalizeURLPart(urlPart) !== paramCacheKey       => 리라이트 ④
           'c' · 'oc' 남은 조각을 canonicalize 해 '/' 로 이은 것 !== key   => 리라이트 ⑤
           'ci(..)' 류 · 'di(..)' 류 여덟  비교하지 않는다 (가로채기 — 어차피 [02]가 거절)
 L548    같은 층에 **다른 이름·종류의 동적 자식**이 이미 있으면
           hasConflictingDynamicChildren = true                 => 리라이트 ⑥
 L573    dynamicChild get-or-create
 L585    staticSiblings 가 null 이 아니면 부모 staticChildren 을 Map 으로 만들고
           형제 이름마다 **빈 자리**를 꽂는다 (L590-594)
 L600    'c' · 'oc' 면 URL 을 끝까지 소비, 아니면 한 칸 전진

 자식 슬롯 (L611-659)
 L618    refreshState !== null 인 슬롯은 건너뛴다 — 다른 라우트에서 재사용된 default 슬롯이다
 L621    슬롯마다 재귀. 결과는 **마지막 슬롯의 것**으로 덮어쓴다 (L640)
 L647    슬롯이 있었는데 결과가 없으면                           => 리라이트 ⑦ ("Defensive fallback")

 잎 (L661-717)
 L664    URL 조각이 남았으면 (트리가 URL 보다 짧다)             => 리라이트 ⑧
 L681-716  위 실제 코드

 => 리라이트로 빠지는 자리가 **여덟**이다 (grep -n "handleMismatchDueToRewrite(" → L301 정의 외 8줄)
 => 여덟 모두 handleMismatchDueToRewrite(L301-327)로 간다
      existingEntry 가 있으면 그대로 반환 (프리페치 — 이미 캐시 안)
      없으면 writeRouteIntoCache 로 **캐시에만** 넣는다. 패턴은 건드리지 않는다
```

```text
 ★★★ "형제를 모른다" 와 "형제가 없다" 를 null 과 빈 Map 으로 가른다 (L103-110)

   staticChildren = null   이 층의 정적 형제를 **모른다** → [02]가 동적 자식으로 내려가지 않는다
   staticChildren = Map    안다 (비어 있어도) → Map 에 없는 이름이면 동적 자식으로 가도 된다

 그 정보는 서버가 트리 튜플 넷째 칸으로 준다. 세 군데서 null 이 된다
   next-app-loader/index.ts L549-553   webpack **개발**이면 'null'
                                        주석 "In dev mode, routes are compiled on-demand so we
                                        don't know all siblings; pass null."
   crates/next-core/src/app_page_loader_tree.rs L424-427
                                        Turbopack 은 언제나 배열을 싣는다 —
                                        "Turbopack always knows all siblings since it builds
                                         the full directory tree."
   app-render.tsx L610                  optimisticRouting 이 꺼져 있으면 null
 => 같은 개발 서버라도 **webpack 이면 동적 자식을 가진 층의 예측이 막히고, Turbopack 이면 열린다**
 ★★ 단 webpack 의 막힘은 그 층에서 정적 자식을 **하나도 배우지 않은 동안**뿐이다 — 정적 세그먼트를
   배울 때마다 staticChildren 을 Map 으로 만든다(OPTR L414-416), 그리고 매칭은 null 일 때만 막는다(L851)
   => `/blog/[slug]` · `/blog/featured` 를 한 번씩 방문하면 아직 컴파일 안 된 `/blog/archive` 가
      `[slug]` 로 **잘못 예측된다** — L103-110 주석의 "null = siblings UNKNOWN" 불변식이 깨지는 틈이다.
      틀린 예측은 [03]의 재시도로 복구된다
 ※ 개발에서 새 파일이 생기면 HMR 이 resetKnownRoutes 로 트라이를 비운다(app-router-instance.ts L492).
   Turbopack 개발에서 형제 목록이 그 사이 낡을 수 있는지는 확인하지 않았다

 ★ 정적 이름으로 꽂힌 **빈 자리**(pattern · dynamicChild · staticChildren 이 모두 null)는
   "경로는 있는데 모양을 모른다" 는 표시다. [02]가 여기서 거절한다
```

```text
 ★★ 첫 로드에서 배운 패턴이 **바로 버려지는** 경우가 있다

 SCCACHE L1406-1407  트리에 PrefetchHint.InliningHintsStale 이 있으면 staleAt = -1
 create-flight-router-state-from-loader-tree.ts L60-67
   prefetchInlining(기본 true, config-shared.ts L2177)이 켜져 있고 **빌드 때 prerender** 중인데
   hint 트리가 없으면 이 비트를 세운다 — 주석 "the initial RSC payload generated before
   collectPrefetchHints has run"
 OPTR L164-171 readPattern 주석 - "This prevents stale patterns (e.g. from InliningHintsStale
   route entries with staleAt = -1) from being cloned into synthetic entries indefinitely."
 => 빌드 때 만든 정적 HTML 로 첫 로드하면, 그 트리로 배운 패턴은 **다음 읽기에서 지워진다.**
    PPR 라우트는 다음 /_tree 응답(collect-segment-data.tsx L1096-1102 가 이 비트를 떼어 낸다)이 다시 채운다.
    그 밖의 라우트는 SCCACHE L3445 writeDynamicTreeResponseIntoCache 경로로 채우는데, 거기서 비트가
    떼어지는지는 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 knownRoutePart.pattern (= 라우트 캐시 항목 객체)
      --> [02] matchKnownRoutePart 가 readPattern 으로 읽어 템플릿으로 쓴다
      --> [03] markRouteEntryAsDynamicRewrite 가 같은 객체에 표시를 세운다

 staticChildren · dynamicChild · hasConflictingDynamicChildren
      --> [02]가 어느 갈래로 내려갈지, 아예 거절할지를 이것으로 정한다

 handleMismatchDueToRewrite 가 넣은 항목
      --> 그 URL 은 readRouteCacheEntry 의 캐시 맵 조회(SCCACHE L522)에서 바로 맞는다.
          예측을 거치지 않는다 — 리라이트된 URL 이 틀린 예측을 피하는 첫째 길이다
```

## 다루지 않는 것

`fulfillRouteCacheEntry`(SCCACHE L1380) · `writeRouteIntoCache`(L1420)의 본문과 캐시 맵 키(`getFulfilledRouteVaryPath` — `couldBeIntercepted` 가 거짓이면 `nextUrl` 없이 거는 규칙), `convertRootTreePrefetchToRouteTree` · `convertRootFlightRouterStateToRouteTree` 가 `RouteTree` 와 `metadataVaryPath` 를 만드는 과정, `getStaticSiblingSegments`(next-app-loader)와 `app_structure.rs` L1212-1226 의 형제 계산 규칙, `canonicalizeURLPart` 가 서버 쪽 `paramCacheKey` 인코딩(`get-dynamic-param.ts`)과 같아지는 근거, 가로채기 파라미터(`ci(..)` 류)의 값 형식, `collectPrefetchHints` 가 hint 트리를 만드는 빌드 단계는 이 문서의 범위 밖이다.
