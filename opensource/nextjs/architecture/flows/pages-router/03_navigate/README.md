# 03 클라이언트가 이동한다

상위: [Pages Router 가 페이지를 그리기까지](../README.md)

`router.push` 도, 뒤로 가기(popstate)도, 하이드레이트 직후의 쿼리 채우기도 **한 메서드**로 온다. `change`(L1207-1925)가 혼자 **719줄**이다. [클라이언트 라우터]에서는 액션 6종이 리듀서 여섯으로 갈렸던 일을, 여기서는 이 메서드 하나가 옵션 플래그(`shallow` · `_h`)로 가른다. 하드 이동으로 빠지지 않은 경로의 끝은 `set` → `this.sub(...)` → [02]의 `render` 다.

## 위치

`packages/next` / `src/shared/lib/router` / `router.ts` L1207-L1925 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/shared/lib/router/router.ts#L1207-L1925))

## 실제 코드

719줄이 결국 도착하는 곳은 열세 줄이다.

```ts
// router.ts L2315-L2327
  private set(
    state: typeof this.state,
    data: PrivateRouteInfo,
    resetScroll: { x: number; y: number } | null
  ): Promise<void> {
    this.state = state

    return this.sub(
      data,
      this.components['/_app'].Component as AppComponent,
      resetScroll
    )
  }
```

```text
 ★★★ 상태를 **먼저 바꿔 쓰고** 구독자 하나를 부른다

 L2320  this.state = state         private state 를 통째로 교체한다
 L2322  return this.sub(data, App, resetScroll)
          this.sub 는 생성자 L817 에서 받은 subscription — [02]의 index.tsx L969-979
          => render → doRender → reactRoot.render (transition)

 => 리듀서도, 액션 큐도 없다
 ★ 이전 상태와의 비교는 **한 자리** 있다 — `_h` 같은 쿼리 갱신이면 canSkipUpdating 이
   compareRouterStates(upcomingRouterState, this.state) 로 비교해 같으면 set 을 건너뛴다
   (router.ts L1873-1878). routeChangeStart · Complete 이벤트도 `!isQueryUpdating` 일 때만 나간다
   (L1624 · L1907)
 => `router.pathname` 같은 getter(L2639-2665)는 전부 this.state 를 읽는다.
    그래서 set 이 돈 순간부터 **렌더 전이라도** 새 값이 보인다
    ※ 이 "렌더 전에 보인다" 는 set 이 sub 보다 먼저 대입한다는 코드 순서에서 내가 끌어낸 것이다
 ★ 구독자가 **하나**다. 이벤트(routeChangeStart 등)는 별도의 정적 mitt 로 나간다 (L744)
```

## 동작 흐름

```text
 push(url, as, options)  L1026-1050
 L1027  javascript: URL 이면 => throw 'Next.js has blocked a javascript: URL as a security precaution.'
 L1038  (스크롤 복원 켜짐) 지금 스크롤을 sessionStorage `__next_scroll_<key>` 에 적는다
 L1048  { url, as } = prepareUrlAs(this, url, as)
 L1049  => return this.change('pushState', url, as, options)
 (replace L1058-1069 는 스크롤 저장만 빼고 같다)

 change(method, url, as, options, forcedScroll)  L1207-1925
 L1214  isLocalURL 이 아니면                                  하드 이동 => return false
 L1221  isQueryUpdating = options._h === 1                     ([02]의 쿼리 채우기)
 L1224  _h 도 shallow 도 아니면  await this._bfl(as, ...)       App Router 경로인가 (아래 ★★★)
 L1239  readyStateChange = this.isReady !== true;  this.isReady = true
 L1249  _h 인데 다른 이동이 진행 중이면(this.clc)               => return false
 L1255  (i18n) 로케일을 정하고, 없는 로케일·다른 도메인이면      하드 이동 => 끝나지 않는 Promise
 L1351  진행 중인 이동이 있으면 routeChangeError(취소) 를 내고 this.clc() 로 끊는다
 L1382  해시만 바뀌었으면  changeState + scrollToHash + set    => return true
 L1414  pages 목록 · 클라이언트 빌드 매니페스트 · 미들웨어 매처를 함께 싣는다
          실패하면                                            하드 이동 => return false
 L1431  asPath 가 그대로면 method = 'replaceState'
 L1451  this.components[pathname].__appRouter 면                하드 이동 (prefetch 가 남긴 표시)
 L1465  isMiddlewareMatch = !shallow && await matchesMiddleware(...)   (경로 정규식만 본다, L120-124)
 L1477  rewrites 를 클라이언트에서 풀어 본다 (externalDest 면 하드 이동 => return true)
 L1530  동적 pages 경로로 풀렸는데 App Router 동적 경로가 가리면  하드 이동
 L1568  동적 경로면 as 에서 파라미터를 뽑아 query 에 합친다. 모자라면 throw
 L1625  Router.events.emit('routeChangeStart', as, routeProps)
 L1631  routeInfo = await this.getRouteInfo({...})                    ← 데이터 + 컴포넌트
 L1709  routeInfo 가 미들웨어 redirect 면 내부는 재귀 change, 외부는 하드 이동
 L1728  pageProps.__N_REDIRECT 면 내부는 재귀 change, 아니면 하드 이동   ([01]의 redirect)
 L1765  props.notFound === SSG_DATA_NOT_FOUND 면 /404(없으면 /_error)의 routeInfo 로 바꾼다
 L1805  isValidShallowRoute = shallow && 같은 route 일 때만
 L1867  Router.events.emit('beforeHistoryChange')
 L1868  this.changeState(method, url, as, options)                     ← 주소창이 바뀐다
 L1882  await this.set(upcomingRouterState, routeInfo, upcomingScrollState)   ← 화면이 바뀐다
 L1908  Router.events.emit('routeChangeComplete')
 L1919  catch — cancelled 면 => return false, 아니면 throw
```

```text
 getRouteInfo  L2037-2313  (277줄) — 무엇을 받아 올지 정한다

 L2076  shallow 이고 같은 route 이고 이미 있으면        => return existingInfo   (네트워크 없음)
 L2086  cachedRouteInfo — 이미 받은 컴포넌트 정보. 'initial' 이거나 **개발이면 안 쓴다**
 L2116  미들웨어에 맞으면 먼저 data 를 받아 효과(rewrite · redirect)를 읽는다
          withMiddlewareEffects L336-356 — matchesMiddleware 가 false 면 null
 L2190  isAPIRoute(route) 면                              하드 이동 => 끝나지 않는 Promise
 L2195  routeInfo = cachedRouteInfo || fetchComponent(route) → { Component, styleSheets,
                                                               __N_SSG: mod.__N_SSG, __N_SSP: mod.__N_SSP }
 L2217  shouldFetchData = routeInfo.__N_SSG || routeInfo.__N_SSP
 L2225  props = await this._getData(async () => {
 L2226    shouldFetchData 면  fetchNextData({ dataHref, inflightCache: this.sdc, ... })
 L2255    아니면           this.getInitialProps(Component, {pathname, query, asPath, locale, ...})
        })
 L2275  __N_SSP 면 this.sdc[cacheKey] 를 **지운다**
 L2281  __N_SSG 면 (개발·프리뷰·_h 아님) 같은 주소로 **HEAD 요청을 백그라운드로** 쏜다
 L2301  this.components[route] = routeInfo
```

```text
 ★★★ "데이터를 받을지" 를 **번들의 표시**로 안다

 L2201-2202  __N_SSG: res.mod.__N_SSG,  __N_SSP: res.mod.__N_SSP
 => 클라이언트 번들의 페이지 모듈에서 읽는다. 그 표시를 넣는 것은 컴파일러다
     crates/next-custom-transforms/src/transforms/strip_page_exports.rs L43-51
       PageMode::Ssr => Some("__N_SSP"),  PageMode::Ssg => Some("__N_SSG")
     같은 파일 L568 - "Adds __N_SSG and __N_SSP declarations when eliminating data functions."
     (webpack 쪽 next_ssg.rs L446-448 도 같은 두 이름을 쓴다)
 => getStaticProps 를 번들에서 **지우는 대신** 표시 하나를 남긴다
 ★★ 표시가 없으면(= getInitialProps 페이지이거나 데이터 없는 페이지) L2255 로 간다 —
   `_app` 과 페이지의 getInitialProps 가 **브라우저에서** 돈다.
   ctx 에 req · res 가 없다 (L2260-2267 에 넣는 필드는 pathname · query · asPath · locale ·
   locales · defaultLocale 여섯이고, getInitialProps L2630 이 AppTree 를 하나 더 붙인다)
```

```text
 ★★ 데이터 주소와 요청 모양

 PLOADER getDataHref L154-186
   `/_next/data/${this.buildId}${dataRoute}${search}`   dataRoute = 경로 + '.json'
 fetchRetry L442-469
   credentials: 'same-origin'   주석 L448-449 - 프리뷰 모드와 getServerSideProps 에 쿠키가 필요하다
   headers['x-nextjs-data'] = '1'
   5xx 면 재시도 — 시도 횟수는 isServerRender ? 3 : 1 (L513). 첫 로드 때만 세 번이다
 fetchNextData L499-644  (146줄)
   404 이고 본문이 {notFound: true} 면  json.notFound = SSG_DATA_NOT_FOUND (심볼)
   응답의 배포 ID 헤더가 내 것과 다르면  "Loaded static props were from an outdated deployment,
     forcing a hard reload" 오류 — isServerRender 가 아니면 markAssetError 로 표시하고,
     handleRouteInfoError(L1977-1993)가 그 표시를 보고 하드 이동한다
   inflightCache[cacheKey] 로 **같은 URL 동시 요청을 하나로** 묶는다 (L638-643)
   개발이거나 persistCache 가 아니거나 x-middleware-cache: no-cache 면 끝난 뒤 지운다 (L597-603)

 => 서버의 [README] PHAND 가 이 요청을 isNextDataRequest 로 받아 pageData JSON 을 보낸다
```

```text
 ★★★ 하드 이동(window.location.href = url)이 **열네 자리**다

 grep -n "handleHardNavigation(" router.ts → 15줄, 그중 L654 는 정의
   끝나지 않는 Promise `new Promise(() => {})` 로 끝나는 것  아홉 자리 (return 문 여덟 개 —
     L1292 · L1320 두 자리가 L1339 하나를 함께 쓴다)
   return false  세 자리 (L1215 · L1422 · L1559)
   return true   한 자리 (L1491, rewrite 가 외부 주소)
   throw         한 자리 (L1986, handleRouteInfoError → 취소 오류)

 handleHardNavigation L654-669
   같은 URL 로 하드 이동하려 하면 throw — 주석 L661-662
     "ensure we don't trigger a hard navigation to the same URL as this can end
      up with an infinite refresh"
 => 페이지가 곧 떠나므로 change 의 Promise 를 **영원히 대기시켜** 뒤 코드가 안 돌게 한다
 ★ handleRouteInfoError 만 다르다 — 주석 L1991-1992 "Changing the URL doesn't block
   executing the current code path. So let's throw a cancellation error stop the routing logic."
```

```text
 ★★★ Pages → App 경계를 **블룸 필터**로 알아챈다 (_bfl L1071-1205)

 필터를 만드는 쪽  build/index.ts L1699-1709
   config.experimental.clientRouterFilter 면
   createClientRouterFilter([...appPaths], redirects, ...)
 => 필터에 든 것은 **App Router 경로**(와 선택적으로 redirects)다
 켜짐 여부  build/define-env.ts L244-245  clientRouterFilter ?? true
            server/config-shared.ts L2179 기본값 true

 _bfl 이 정적 필터(_bfl_s) 또는 동적 필터(_bfl_d)에 맞으면  하드 이동
 prefetch 에서는 skipNavigate=true 로 부르고, 맞으면 표시만 남긴다 (L2556-2558)
   this.components[urlPathname] = { __appRouter: true }
 => 나중 change 의 L1451 이 그 표시를 보고 하드 이동한다
 ★★ L1530-1550 이 한 겹 더 막는다. 주석 L1522-1529 -
   "When it resolves to a dynamic pages route, an app route that begins with a
    dynamic segment may be more specific and own this path on the server
    (e.g. `/en/about` resolves to the pages route `/[locale]/[category]`, but the
    app route `/[locale]/about` should win)."
 => 두 라우터가 공존할 때 Pages 라우터는 App 경로로 **클라이언트 이동을 하지 않는다**
 ★ 반대 방향은 popstate 의 `__NA` 가 막는다 ([README] 대비 표)
 ※ 블룸 필터라 거짓 양성이 있을 수 있다(그러면 불필요한 하드 이동) — 자료구조의 일반 성질이고
   이 문서에서 오류율 설정(clientRouterFilterAllowedRate)은 확인하지 않았다
```

```text
 ★★ 취소가 **단계마다** 있다 — 컴포넌트 로드 · 데이터 로드 · 렌더

 컴포넌트  getCancelledHandler L671-697  "Abort fetching component for route: ..."
 데이터    _getData L2603-2622           "Loading initial props cancelled"
             (둘 다 this.clc 에 취소 함수를 걸어 둔다)
 렌더      [02] doRender L634-649        lastRenderReject() — "Cancel rendering route"
 방아쇠    change L1351-1362             새 이동이 시작될 때 진행 중이던 것의 this.clc() 를 부른다
 => 셋 다 `error.cancelled = true` 를 단다. 렌더 취소는 L1883-1885 가 routeInfo.error 로 옮겨
    L1898 에서 다시 던지고, 결국 change 의 catch(L1919-1922)가 **false 로 삼킨다**
```

```text
 ★★ SSG 데이터를 쓸 때 **서버를 깨우는 HEAD** 를 따로 쏜다 (L2279-2294)

 주석 L2279-2280 - "we kick off a HEAD request in the background when a
   non-prefetch request is made to signal revalidation"
 조건  !this.isPreview && __N_SSG && 개발 아님 && _h 아님
 => fetchNextData(..., isBackground: true) → getData({method: 'HEAD'}) (L641-643)
    결과는 this.sbc 에 두고 persistCache: false 라 끝나면 지운다
 => 클라이언트가 캐시된 JSON 을 써도 서버의 ISR(재검증)은 HEAD 한 번으로 돈다
 ※ HEAD 가 서버 쪽 재검증을 실제로 일으키는지는 [README] PHAND 가 요청을 캐시 조회로
   보내는 데서 추론했다. HEAD 를 따로 다루는 서버 코드는 확인하지 않았다
```

```text
 ★★ 뒤로 가기 — onPopState L901-1000

 L907  state 가 없으면 (해시 이동 등) replaceState 로 현재 상태를 다시 적고 끝
 L927  state.__NA 면  window.location.reload()      App Router 가 만든 기록이다
 L932  state.__N 이 아니면 무시                        Next.js 가 만든 기록이 아니다
 L937  첫 popstate 이고 같은 주소면 무시 (주석 L936 "Safari fires popstateevent when
       reopening the browser.")
 L947  스크롤 복원 켜짐 — 떠나는 기록의 스크롤을 저장하고, 가는 기록의 것을 꺼낸다
 L984  beforePopState 콜백이 false 를 돌려주면 여기서 멈춘다
 L988  this.change('replaceState', url, as, {..., _h: 0}, forcedScroll)
 => 뒤로 가기도 getRouteInfo 를 다시 거치는 이동이다. 컴포넌트는 this.components 를
    (개발이 아니면) 다시 쓰고, SSG JSON 은 this.sdc 에 남아 있으면 다시 쓴다.
    SSP JSON 은 L2275 가 지웠으므로 **다시 받는다**
```

```text
 ★ prefetch  L2402-2587 (186줄)

 L2408  프로덕션이 아니면 => return    주석 L2407 "would trigger on-demand-entries"
 L2412  봇이면 => return
 L2507  미들웨어에 맞으면 data 로 효과를 먼저 본다 (strict 모드면 건너뛴다)
 L2556  App Router 경로면 __appRouter 표시만 남긴다
 L2560  Promise.all([
          SSG 면 fetchNextData(isPrefetch: true)     요청 헤더 purpose: prefetch (L516)
          pageLoader.prefetch(route) 또는 priority 면 loadPage(route)
        ])
 => getServerSideProps 페이지는 **데이터를 미리 받지 않는다**. 청크만 받는다
    (미들웨어에 맞을 때 L2507 이 효과를 보려고 받는 요청은 예외다)
```

## 결과가 쓰이는 곳

```text
 this.state (route · pathname · query · asPath · locale · isFallback · isPreview)
      --> getter 로 읽힌다. [02]의 makePublicRouterInstance 가 렌더마다 복사해 RouterContext 에 싣는다

 routeInfo (Component · props · styleSheets)
      --> this.sub → [02] render → doRender 가 App 의 Component / pageProps 로 넣는다
      --> this.components[route] 에 남아 다음 이동과 shallow 이동이 다시 쓴다

 history.state = { url, as, options, __N: true, key }   (changeState L1927-1962)
      --> onPopState 가 되읽는다. key 는 pushState 때만 새로 만든다 (L1953)

 Router.events (정적 mitt)
      --> routeChangeStart · beforeHistoryChange · routeChangeComplete · routeChangeError ·
          hashChangeStart · hashChangeComplete 여섯. CROUTER L48-55 가 같은 여섯을 싱글턴에 잇는다

 /_next/data/... 요청 (x-nextjs-data: 1)
      --> 서버 [README]의 PHAND 가 받는다
```

## 다루지 않는 것

i18n 로케일·도메인 처리(L1255-1341)와 `detectDomainLocale`, 클라이언트 rewrites 해석(`resolve-rewrites.ts`)과 `resolveDynamicRoute`(L155), 미들웨어 효과 해석 `getMiddlewareData`(L174-330, 157줄)와 `x-middleware-*` 헤더, `interpolateAs` · `getRouteRegex` 의 동적 경로 매칭, `hasDynamicFilterCandidate`(`dynamic-filter-pattern.ts`)와 `BloomFilter` 구현, `handleRouteInfoError`(L1964-2035)의 `_error` 폴백 세부, `unstable_skipClientCache` 와 `__NEXT_OPTIMISTIC_CLIENT_CACHE`, `route-loader.ts` 의 청크 로드·스타일시트 수집·타임아웃, `scrollToHash` 와 `disableSmoothScrollDuringRouteTransition`, `next/link` 가 prefetch 와 push 를 부르는 방식, `unstable_scriptLoader`(L1719-1725)는 이 문서의 범위 밖이다.
