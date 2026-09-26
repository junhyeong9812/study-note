# 03 서버에 RSC 요청하기

상위: [내비게이션이 서버 응답을 트리에 합치기까지](../README.md)

`fetchServerResponse` 는 URL 하나와 [01]이 만든 요청 트리를 받아 RSC 요청을 보내고, 응답을 **디코드한 결과 객체** 또는 **URL 문자열**을 돌려준다. 문자열은 "SPA 로는 안 된다, 브라우저에 맡겨라" 라는 뜻이다. 이 함수는 예외를 거의 던지지 않는다 — 실패가 반환값으로 돌아온다.

## 위치

`packages/next` / `src/client/components/router-reducer` / `fetch-server-response.ts` L149-L359 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/fetch-server-response.ts#L149-L359))

## 실제 코드

PPR(= CC) 을 읽는 곳이 FSR 에 둘 있다. 그중 L196 의 isLegacyPPR 은 언제나 false 라([README]) 실제로 동작을 가르는 것은 L403 processFetch 하나이고, 아래는 닿지 않는 쪽이다.

```ts
// fetch-server-response.ts L192-L204
    // Typically, during a navigation, we decode the response using Flight's
    // `createFromFetch` API, which accepts a `fetch` promise.
    // TODO: Remove this check once the old PPR flag is removed
    const isLegacyPPR =
      process.env.__NEXT_PPR && !process.env.__NEXT_CACHE_COMPONENTS
    const shouldImmediatelyDecode = !isLegacyPPR
    const res = await createFetch<NavigationFlightResponse>(
      url,
      headers,
      'auto',
      shouldImmediatelyDecode,
      options.signal
    )
```

```text
 ★★★ 이 갈래는 v16.3.6 에서 **닿지 않는다** (규칙 16)

   isLegacyPPR = __NEXT_PPR && !__NEXT_CACHE_COMPONENTS
   [README]에서 확인한 대로 두 플래그는 (꺼짐, 꺼짐) · (켜짐, 켜짐) 둘뿐이다
   => isLegacyPPR 은 언제나 false, shouldImmediatelyDecode 는 언제나 **true**
 => 그래서 L254-267 의 "flightResponsePromise === null 이면 지금 디코드" 는
    fetchServerResponse 에서는 죽은 갈래다. 주석 L258-260 도 스스로 적는다 —
    "This should only be reachable if legacy PPR is enabled (i.e. PPR without Cache
     Components). Remove this branch once legacy PPR is deleted."
 ★ 다만 createFetch 자체의 `shouldImmediatelyDecode = false` 는 **살아 있다** —
   프리페치(segment-cache/cache.ts L3862-3877 fetchPrefetchResponse)가 false 로 부른다.
   주석 FSR L746-749 "a top-level prefetch response never blocks a navigation"
 ★ 즉시 디코드하는 이유 (주석 L742-744) — "so that the debug info includes the latency
   from the client to the server. The internal timer in React starts as soon as
   `createFromFetch` is called."
```

## 동작 흐름

```text
 fetchServerResponse(url, { flightRouterState, nextUrl, isHmrRefresh?, signal? })  FSR L149-359 (211줄)

 L155  headers
         rsc: '1'
         next-router-state-tree: prepareFlightRouterStateForRequest(tree, isHmrRefresh)
           HMR 이면 트리를 **그대로**, 아니면 클라이언트 전용 칸을 벗긴다 (flight-data-helpers.ts L231-243)
 L165  개발 + HMR 이면 next-hmr-refresh: '1'
 L169  nextUrl 이 있으면 next-url 헤더 (가로채기 라우트용)
 L178  프로덕션 + output: 'export' 면 경로 끝에 `.txt` / `index.txt` 를 붙인다
         주석 L180-182 - 헤더로 HTML 과 RSC 를 구분할 수 없어서다

 L198  res = await createFetch(url, headers, 'auto', shouldImmediatelyDecode, signal)
         +-- createFetch  FSR L694-851                        (아래)
 L215  canonicalUrl = res.redirected ? 응답 URL : 원래 URL
 L218  interception = vary 헤더에 next-url 이 있는가
 L219  postponed    = x-nextjs-postponed 헤더(NEXT_DID_POSTPONE_HEADER)
 L232  RSC 가 아니거나 !res.ok 거나 body 가 없으면
 L238    => return doMpaNavigation(responseUrl)               ← 문자열 ①
 L248  개발 + webpack 이면 waitForWebpackRuntimeHotUpdate()  (Turbopack 은 건너뛴다)
 L269  [flightResponse, cacheData] = await Promise.all([...])
 L274  배포 ID(헤더 또는 응답의 b) !== getNavigationBuildId() 면
 L279    => return doMpaNavigation(res.url)                   ← 문자열 ② 빌드가 바뀌었다
 L282  normalizedFlightData = normalizeFlightData(flightResponse.f)
 L284    문자열이면 => return doMpaNavigation(그것)            ← 문자열 ③ 서버가 MPA 를 지시
 L287  staticStageData = cacheData ? resolveStaticStageData(...) : null
 L292  => return { flightData, canonicalUrl, renderedSearch: q, couldBeIntercepted,
                  supportsPerSegmentPrefetching: S, postponed, dynamicStaleTime: d ?? Unknown,
                  staticStageData, runtimePrefetchStream: p ?? null, responseHeaders,
                  debugInfo, revealAfter }
 L317  catch (err)
 L318    signal 이 abort 됐으면 => throw err        HMR 이 더 새 요청으로 대체됐다 → [04] Canceled
 L335    useOffline 이고 네트워크 오류면 연결을 기다려 => return fetchServerResponse(url, options)  재귀
 L357    => return originalUrl.toString()                     ← 문자열 ④
```

```text
 ★★★ 실패가 **네 갈래 모두 문자열**로 돌아온다 (실패 return — L238 · L279 · L284 · L357. 나머지 return 은 L292 성공 객체와 L343 오프라인 재귀 `return fetchServerResponse(url, options)` 인데, 재귀도 결국 이 넷 중 하나로 끝날 수 있다)

   ① 응답이 RSC 가 아님 / 2xx 가 아님(`!res.ok`) / body 없음   응답 URL (해시 보존, L234-236)
   ② 서버 배포 ID ≠ 클라이언트 배포 ID               응답 URL
   ③ flightData 자체가 문자열                        서버가 준 URL
   ④ fetch 가 던짐 (네트워크 · CORS · 기타)           **원래** URL + console.error (L347-352)

 => 호출하는 쪽은 `typeof result === 'string'` 하나로 가른다
    PPRNAV L1824 → HardRetry,  SCNAV L518-521 → completeHardNavigation
 => 그래서 [04]의 fetchMissingDynamicData 는 try/catch 를 갖고도 catch 에 거의 안 간다.
    주석 PPRNAV L1980-1982 "This shouldn't happen because fetchServerResponse's entire
    body is wrapped in a try/catch."
 ★ catch 안에서 다시 던지는 줄은 L322 **하나**다 — signal 이 abort 됐을 때만이다
   (try 바깥 L153-175 의 헤더 조립에서 던지는 경우는 따지지 않았다)
 ★ ②는 "배포 사이에 탭을 열어 둔 사용자" 를 조용히 새 빌드로 옮기는 장치다
   ※ 이 해석은 주석 "The server build does not match the client build." 에서 끌어낸 것이다
 ★ `pagehide` 가 난 뒤(페이지를 떠나는 중)에는 ④의 console.error 를 찍지 않는다 (L128-143, L347)
```

```text
 createFetch  FSR L694-851 (158줄) — 요청 하나를 보내는 저수준 함수

 L709  배포 ID 가 있으면 x-deployment-id 헤더
 L714  개발 서버면 HTML 요청 ID · 새 요청 ID 헤더 (디버그 채널 라우팅)
 L737  fetchUrl = new URL(url);  await setCacheBustingSearchParam(fetchUrl, headers)   ← `_rsc=` 추가
 L739  processed = fetch(fetchUrl, ...).then(processFetch)
 L750  즉시 디코드면 flightResponsePromise = decodeFlightResponse(fetchPromise, ...)
 L753  browserResponse = await fetchPromise

 L778  `__NEXT_CLIENT_VALIDATE_RSC_REQUEST_HEADERS` 면 (기본 켜짐 — config-shared.ts L2228)
 L781    최대 20번 (Chrome 과 같은 한도, 주석 L779)
 L782      리다이렉트가 아니었으면 break
 L787      다른 오리진이면 break
 L792      이미 같은 `_rsc` 값이면 break
 L807      리다이렉트된 URL 에 `_rsc` 를 **다시 붙여** 한 번 더 fetch 한다
 L816      redirected = true
 L822  응답 URL 에서 `_rsc` 를 지우고 => return RSCResponse
```

```text
 ★★★ 리다이렉트를 **다시 재생한다** (주석 L755-775)

   "when following the redirect, the browser forwards the request headers, but since
    the cache busting search param is missing, the server will reject the request due
    to a mismatch."
   "Ideally, we would be able to intercept the redirect response and perform it
    manually, ... but this is not allowed by the fetch API."

 => 미들웨어가 307 을 주면 브라우저는 헤더는 들고 따라가지만 `_rsc` 는 잃는다.
    서버가 그 불일치로 요청을 거절하므로, 클라이언트가 새 위치에 `_rsc` 를 붙여 **다시 보낸다**
 ★ 서버 액션의 리다이렉트는 해당이 없다 — Flight 본문에 다르게 인코딩된다 (주석 L773-775)
 ★ 이전 요청은 끊지 않는다 — `// TODO: We should abort the previous request.` (L806)
 ★ `redirected` 는 브라우저의 것과 다르다 — "true if any redirects occurred, either
   automatically by the browser, or manually by us" (L828-831). 이 값이 L215 의 canonicalUrl 을 정하고,
   그것이 [04]의 RedirectRetry 판정으로 이어진다
```

```text
 ★★ processFetch (L399-449) — cacheComponents 일 때만 **첫 바이트를 벗긴다**

 CC 꺼짐 (기본 설정)   => return { response, cacheData: null }   (L448)
 CC 켜짐
   L410  stripIsPartialByte(body)
           첫 바이트 '~'(0x7e) = 부분,  '#'(0x23) = 완전     (docstring L391-393)
           표지가 없으면 isPartial = !!__NEXT_EXPERIMENTAL_CACHED_NAVIGATIONS
             (segment-cache/cache.ts stripIsPartialByte 주석 — 캐시된 내비게이션이면
              표지 없는 동적 응답에도 구멍이 있을 수 있어 부분으로 본다)
   L415  experimental.cachedNavigations 면 (config-shared.ts L2171 기본은 false 지만
         CC 를 켜면 명시적 false 가 아닌 한 true 가 된다 — server/config.ts L2370-2384)
           tee 를 **두 번** — Flight 디코더 · 정적 단계 추출 · 셸 단계 추출, 읽는 쪽이 셋 (L416-419)
   L426  아니면 cacheData = { isResponsePartial } 뿐
   L431  new Response 로 다시 감싸고 url · redirected 를 **defineProperty 로 되살린다** (L437-443)
         주석 "The Response constructor doesn't preserve `url` or `redirected`"

 => staticStageData 가 null 이 아니려면 CC 켜짐 **그리고** cachedNavigations 켜짐이 필요하다
    (필요조건이다 — 응답이 완전하거나 `l` 필드가 있어야 한다, L469-491)
    (resolveStaticStageData L469 `if (staticBodyClone)` 가 없으면 null)
 => [04]의 "정적 단계를 세그먼트 캐시에 쓰기" 는 기본 설정(CC 꺼짐)에서는 꺼져 있고,
    CC 를 켜면 cachedNavigations 를 명시적으로 false 로 주지 않는 한 **켜진다**
 ★ processFetch 는 서버 액션도 쓴다 (server-action-reducer.ts L250)
```

```text
 ★ HMR 요청만 **멈출 수 있게** 디코드한다 (L577-692)

 decodeFlightResponse (L679-692)
   `__NEXT_DEV_SERVER && __NEXT_SERVER_COMPONENTS_HMR_CANCELLATION && signal` 이면
     createHaltingFlightResponse — 닫을 수 있는 래퍼 스트림을 끼운다
   아니면 createFromNextFetch (React 의 createFromFetch)
 주석 L577-581 - "Closing the stream (rather than letting the aborted fetch error it) makes
   React's Flight client mark unresolved rows as halted: they suspend during render
   instead of rejecting, so a superseded request never surfaces an error on an
   already-committed tree."
 => 대체된 HMR 요청이 **이미 그려진 트리에 오류를 뿌리지 않게** 한다
 ★ 플래그 기본값은 꺼짐이다 (config-shared.ts L2237). signal 이 오는 곳도 HMR 하나다 ([04])
```

## 결과가 쓰이는 곳

```text
 문자열 (MPA)
      --> [04] fetchMissingDynamicData L1824-1834 → HardRetry
      --> SCNAV L518-521 navigateToUnknownRoute → completeHardNavigation

 flightData (NormalizedFlightData[]) · renderedSearch · dynamicStaleTime
      --> convertServerPatchToFullTree 가 NavigationSeed 로 바꾼다 (PPRNAV L1837 · SCNAV L540)
      --> dynamicStaleTime 은 computeDynamicStaleAt 으로 BFCache staleAt 이 된다 ([02])

 canonicalUrl
      --> [04]가 routeCacheEntry.canonicalUrl 과 비교해 RedirectRetry 를 정한다

 staticStageData · runtimePrefetchStream
      --> [04] 가 **라우트 캐시 적중 내비게이션일 때만** 세그먼트 캐시에 쓴다
      --> SCNAV L571-635 navigateToUnknownRoute 도 같은 두 값을 쓴다 (`metadataVaryPath !== null` 일 때만, L554)

 couldBeIntercepted · supportsPerSegmentPrefetching
      --> SCNAV L555-569 discoverKnownRoute 의 라우트 학습. [04]의 경로는 이 둘을 안 쓴다

 revealAfter (개발만)
      --> [04] finishPendingCacheNode 가 약속을 푸는 시점을 늦춘다
```

## 다루지 않는 것

`setCacheBustingSearchParam` 이 `_rsc` 값을 계산하는 방식(`computeClientCacheBustingSearchParam`)과 서버의 검증, `normalizeFlightData`(flight-data-helpers.ts)가 패치를 풀어 MPA 문자열을 내는 조건, `stripIsPartialByte` · `createNonTaskyPrefetchResponseStream` 의 스트림 조작, `resolveShellStageData`(L510) · `decodeStageUntilBoundary`(L543) · `decodeBufferedStage`(L562)와 셸 단계 추출(하이드레이션 · 프리페치 쪽이 쓴다), 오프라인 모드(`client/components/offline`), 개발 디버그 채널(`createDebugChannel`), `waitForWebpackRuntimeHotUpdate`, 서버가 `x-nextjs-postponed` · `vary` 헤더와 `b` · `q` · `S` · `d` · `l` · `a` · `p` 필드를 채우는 쪽([App Router])은 이 문서의 범위 밖이다.
