# 02 패턴에 맞추기

상위: [가져온 적 없는 라우트 트리를 예측하기까지](../README.md)

`matchKnownRoute` 는 라우트 캐시가 비었을 때 [01]의 트라이를 URL 조각으로 내려간다. 맞는 잎을 찾으면 그 패턴의 라우트 트리를 **복제하며 파라미터 값을 갈아 끼워** 합성 항목을 만든다. 모르는 것이 하나라도 걸리면 null 을 돌려준다 — 그러면 호출자는 서버에 묻는다.

## 위치

`packages/next` / `src/client/components/segment-cache` / `optimistic-routes.ts` L726-L1111 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/segment-cache/optimistic-routes.ts#L726-L1111))

## 실제 코드

매칭이 끝나고 합성 항목을 만드는 자리다. 템플릿이던 패턴을 **이 합성 항목으로 바꿔 끼운다.**

```ts
// optimistic-routes.ts L786-L811
  // Create a synthetic (predicted) entry and store it as the new pattern.
  //
  // Why replace the pattern? We intentionally update the pattern with this
  // synthetic entry so that if our prediction was wrong (server returns a
  // different pathname due to dynamic rewrite), the entry gets marked with
  // hasDynamicRewrite. Future predictions for this route will see the flag
  // and bail out to server resolution instead of making the same mistake.
  const syntheticEntry: FulfilledRouteCacheEntry = {
    canonicalUrl: pathname + search,
    status: EntryStatus.Fulfilled,
    blockedTasks: null,
    tree: reifiedTree,
    metadata: reifiedMetadata,
    couldBeIntercepted: pattern.couldBeIntercepted,
    supportsPerSegmentPrefetching: pattern.supportsPerSegmentPrefetching,
    hasDynamicRewrite: false,
    renderedSearch: search,
    ref: null,
    size: pattern.size,
    staleAt: pattern.staleAt,
    version: pattern.version,
  }

  matchedPart.pattern = syntheticEntry

  return syntheticEntry
```

```text
 ★★★ 합성 항목은 라우트 캐시 맵에 **들어가지 않는다**

   ref: null (L803)            CacheMap 의 항목이 아니라는 뜻이다
   L809 matchedPart.pattern = syntheticEntry     들어가는 곳은 트라이의 잎 **하나**뿐
 => 같은 URL 을 다시 읽으면 SCCACHE L522 의 캐시 조회가 또 빗나가고, L537 에서 **다시 짓는다.**
    프리페치 작업이 여러 번 ping 하면 그때마다 새 합성 항목이 생기고 잎의 패턴이 바뀐다
 ★ 수명은 늘지 않는다 — staleAt · version · size 를 **템플릿에서 그대로** 가져온다 (L804-806).
   템플릿이 만료되면(readPattern) 그 템플릿으로 만든 예측도 끝난다

 ★★ 바꿔 끼우는 이유 (주석 L788-792)
   "so that if our prediction was wrong (server returns a different pathname due to dynamic
    rewrite), the entry gets marked with hasDynamicRewrite. Future predictions for this route
    will see the flag and bail out to server resolution instead of making the same mistake."
 => 내비게이션이 쥐고 가는 routeCacheEntry 가 곧 잎의 패턴이 되게 해서,
    [03]의 markRouteEntryAsDynamicRewrite(항목) 한 줄이 **트라이에도** 닿게 한다
 ※ 그 사이 다른 URL 의 예측이 같은 잎을 또 바꿔 끼우면, 표시가 붙는 객체는 이미 잎에 없다.
   그리고 [03]에서 보듯 표시 직후의 무효화가 잎의 패턴을 어차피 만료시킨다

 ★ 합성 항목이 **가정하는 것** 둘
   canonicalUrl = pathname + search (L794)   redirect 가 없다
   renderedSearch = search (L802)             검색 문자열 rewrite 가 없다
 => 첫째가 틀리면 [PPR 내비게이션]의 RedirectRetry 판정(PPRNAV L1947-1955)이 잡는다 → [03]
 ★ couldBeIntercepted 는 템플릿 값을 옮기지만(L799) L760 을 통과했으므로 **언제나 false** 다
```

## 동작 흐름

```text
 matchKnownRoute(now, pathname, search)  OPTR L726-812
   ★ 인자에 nextUrl 이 **없다.** 라우트 캐시 키(SCCACHE L516-520)는 nextUrl 을 쓰지만
     예측은 쓰지 않는다 — 그래서 가로채질 수 있는 템플릿은 L760 에서 통째로 거절한다

 L731  pathnameParts = splitPathnameIntoParts(pathname)
 L733  match = matchKnownRoutePart(now, root, parts, 0, resolvedParams)
 L741  없으면                                    => return null   ①
 L760  pattern.couldBeIntercepted 면             => return null   ②
         주석 L748-754 - 가로채기 라우트는 referrer(Next-Url)에 따라 트리가 달라진다.
         트라이는 URL 모양 하나에 패턴 하나만 두므로 구분할 수 없다
 L768  reifiedTree = reifyRouteTree(pattern.tree, resolvedParams, search, null, acc)
 L780  acc.metadataVaryPath 가 null 이면           => return null   ③  ("shouldn't be reachable")
 L784  reifiedMetadata = createMetadataRouteTree(metadataVaryPath)
 L793-811  위 실제 코드
```

```text
 matchKnownRoutePart   OPTR L835-984 (150줄) — 한 층에서 고르는 순서

 L842  urlPart = partIndex < pathnameParts.length ? pathnameParts[partIndex] : null   (L842-843)

 L851  staticChildren === null (형제를 모른다 — [01])
 L853    URL 이 바닥났고 이 노드의 패턴이 살아 있고 표시가 없으면  => { part, pattern }
 L859                                                             => return null   ④
         주석 L845-850 - "A request for /blog/featured would incorrectly match /blog/[slug]."

 L864  정적 자식이 이 이름으로 있으면 (1순위)
 L871    빈 자리(패턴 · 동적 자식 · 정적 자식 모두 null)면           => return null   ⑤
           "We know the path exists but don't know its structure"
 L879    재귀. 맞으면 => return match
 L894    안 맞으면                                                  => return null   ⑥
           주석 L889-893 - "Do not fall through to try the dynamic child —
             the static match is authoritative."

 L901  동적 자식이 있고 hasConflictingDynamicChildren 가 아니면 (2순위)
         ★ 충돌 표시가 있으면 이 블록을 **통째로 건너뛴다** — 아래 L976 으로 떨어진다
 L907    switch (paramType)
           'c'   URL 이 남았고 동적 자식의 패턴이 살아 있으면
                   resolvedParams[이름] = 남은 조각을 '/' 로 이은 것 => { 동적 자식, 패턴 }
           'oc'  URL 이 남았으면 'c' 와 같다.
                 바닥났으면 **이 노드 자신의 패턴이 우선**이다 (L932-938) —
                   없거나 표시가 있을 때만 값 '' 로 동적 자식을 고른다
           'd'   URL 이 남았으면 값 = 그 조각, **재귀 결과를 그대로 반환** (L948)
           가로채기 여덟 ('ci(..)(..)' · 'ci(.)' · 'ci(..)' · 'ci(...)' 와 'di' 로 시작하는 같은 넷)
                                                                    => return null   ⑦
 L976  URL 이 바닥났으면 이 노드의 패턴 (3순위)
 L983                                                               => return null   ⑧

 => 거절이 **matchKnownRoute 셋 + matchKnownRoutePart 다섯(④–⑧)** 이다.
    그 밖에 패턴을 읽는 네 자리(L854 · L905 · L934 · L977)가 모두 readPattern 을 거치고,
    다섯 군데(L855 · L912 · L924 · L935 · L978)가 `hasDynamicRewrite` 를 확인한다 — 서 있으면 그 패턴은 없는 것으로 친다
 ★ 매칭은 되돌아가지 않는다(backtracking 없음). 정적 이름이 맞은 순간 동적 자식은 후보에서 빠진다
```

```text
 ★★ 검색 문자열은 **매칭에 쓰이지 않는다**

   matchKnownRoutePart 는 pathname 조각만 본다. search 는 reifyRouteTree 로 넘어가
   페이지 세그먼트의 varyPath 를 마무리할 때만 들어간다 (L1071-1075 finalizePageVaryPath)
 => ?page=2 처럼 처음 보는 검색 문자열도 그대로 예측된다
 => 옛 경로(SCCACHE L689-811)는 "같은 pathname 의 **빈 검색 문자열** 항목" 이 있어야만 됐다.
    새 경로는 다른 pathname 에서 배운 패턴으로도 된다
```

```text
 reifyRouteTree(pattern, resolvedParams, search, parentPartialVaryPath, acc)   OPTR L1006-1111

 L1017  isRootParam = prefetchHints & IsRootLayoutOrAbove        서버가 표시한 비트
 L1023  동적 세그먼트면
 L1028    newValue = resolvedParams.get(paramName)
 L1033    newSegment = [paramName, newValue, paramType, staticSiblings]    캐시 키 칸만 바꾼다
 L1034    partialVaryPath = appendLayoutVaryPath(부모, newValue, paramName, isRootParam)
 L1040    값이 없으면 원래 세그먼트 유지 — 주석 L1042 "TODO: This should never happen. Bail out with null."
 L1053  슬롯마다 재귀
 L1069  페이지면 finalizePageVaryPath(requestKey, search, partial)  + 첫 페이지의 metadata varyPath
 L1094  레이아웃이면 finalizeLayoutVaryPath(requestKey, partial)
        requestKey · refreshState · prefetchHints 는 **템플릿 값을 그대로** 쓴다

 ★★ requestKey 를 그대로 써도 되는 이유 — requestKey 는 원래 **파라미터 이름**으로 짜여 있다
   shared/lib/segment-cache/segment-value-encoding.ts L42-47
     동적 세그먼트의 조각 = '$' + paramType + '$' + 이름     (예: `$d$slug`)
 => /blog/a 와 /blog/b 의 세그먼트 요청 키는 같고, 값이 들어가는 곳은 **varyPath** 하나다.
    그래서 복제는 "varyPath 를 다시 계산" 만으로 끝난다 (docstring L999-1001)
 => 이 varyPath 로 [프리페치]의 세그먼트 캐시를 찾는다. 예측이 맞으면 **세그먼트 데이터까지**
    다른 URL 의 것과 나눠 쓸 수 있다 — 그 세그먼트가 파라미터에 따라 달라지지 않는다면
    (varyParams 재키잉 — [PPR 내비게이션] [04])

 ※ 값의 인코딩이 [01]과 다르다. [01]은 `canonicalizeURLPart(urlPart)`(encodeURIComponent(decodeURIComponent(…)))
   를 서버 키와 비교했지만(L489), 여기서는 URL 조각을 **그대로** 키에 넣는다(L947 · L917).
   브라우저 pathname 의 인코딩과 encodeURIComponent 가 다른 문자가 들어간 URL 에서 두 키가
   갈라질 수 있어 보인다. 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 합성 FulfilledRouteCacheEntry (readRouteCacheEntry 의 반환값)
      --> SCNAV L151  Fulfilled 이므로 navigateUsingPrefetchedRouteTree → 동기 내비게이션
          ([프리페치] [03]이 "캐시에 맞는 프리페치가 있으면" 이라 부른 출구)
      --> scheduler.ts L737 pingRoute → pingRootRouteTree — `/_tree` 요청 없이 세그먼트 단계로
          ([프리페치 작업](../../prefetch-tasks/README.md))
      --> scheduler.ts L633  RouteTree 단계를 마친 작업이 prefetchHints 를 읽는다 —
          여기서도 캐시 맵에 없으면 예측으로 다시 지은 트리의 hint 를 읽게 된다

 잎의 pattern (합성 항목으로 교체됨)
      --> [03]의 markRouteEntryAsDynamicRewrite 가 같은 객체에 표시를 세운다

 null
      --> 내비게이션은 navigateToUnknownRoute (응답을 기다린다), 프리페치는 Pending 항목을
          만든다 (SCCACHE L673-681). 그 뒤의 `/_tree` 요청은 [프리페치 작업]
```

## 다루지 않는 것

`appendLayoutVaryPath` · `finalizeLayoutVaryPath` · `finalizePageVaryPath` · `finalizeMetadataVaryPath` · `getShellSegmentVaryPath`(`vary-path.ts` 437줄)의 키 조립 규칙, `createMetadataRouteTree`, 프리페치 작업이 합성 항목을 받아 세그먼트를 요청하는 과정과 그 요청이 합성 트리의 `requestKey` 를 서버에 보내는 형식, 세그먼트 캐시가 varyPath 로 항목을 찾는 규칙(`readSegmentCacheEntryForNavigation`), 서버가 `paramCacheKey` 를 만드는 `getParamValue` 의 인코딩, 옛 경로 `deprecated_createOptimisticRouteTree` 의 본문은 이 문서의 범위 밖이다.
