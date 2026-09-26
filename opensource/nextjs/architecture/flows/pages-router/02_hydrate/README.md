# 02 브라우저가 하이드레이트한다

상위: [Pages Router 가 페이지를 그리기까지](../README.md)

브라우저 쪽 진입은 두 함수다. `initialize`(L190-290, 101줄)가 `__NEXT_DATA__` 를 읽고 페이지 로더를 세우고, `hydrate`(L832-1003, 172줄)가 `_app` 과 페이지 모듈을 기다렸다가 라우터를 만들고 첫 렌더를 건다. 첫 렌더는 `hydrateRoot`, 그다음부터는 **같은 함수가 `root.render`** 를 부른다 — 클라이언트 이동([03])도 결국 여기로 돌아온다.

## 위치

`packages/next` / `src/client` / `index.tsx` L832-L1003 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/index.tsx#L832-L1003))

## 실제 코드

하이드레이트와 이후의 모든 화면 교체가 한 함수다.

```tsx
// index.tsx L563-L586
function renderReactElement(
  domEl: HTMLElement,
  fn: (cb: () => void) => JSX.Element
): void {
  // mark start of hydrate/render
  if (ST) {
    performance.mark(performanceMarks.beforeRender)
  }

  const reactEl = fn(shouldHydrate ? markHydrateComplete : markRenderComplete)
  if (!reactRoot) {
    // Unlike with createRoot, you don't need a separate root.render() call here
    reactRoot = ReactDOM.hydrateRoot(domEl, reactEl, {
      onRecoverableError,
    })
    // TODO: Remove shouldHydrate variable when React 18 is stable as it can depend on `reactRoot` existing
    shouldHydrate = false
  } else {
    const startTransition = (React as any).startTransition
    startTransition(() => {
      reactRoot.render(reactEl)
    })
  }
}
```

```text
 ★★★ 모듈 변수 `reactRoot` 하나가 "처음인가" 를 가른다

   reactRoot 가 없으면  => ReactDOM.hydrateRoot(domEl, reactEl, {onRecoverableError})
   있으면              => startTransition(() => reactRoot.render(reactEl))
 => 이동할 때마다 **App 전체를 새 엘리먼트로 다시 render** 한다.
    [클라이언트 라우터]처럼 상태를 바꾸고 React 가 구독하는 모양이 아니다
 ★ 이동 렌더는 **transition** 이다. 급한 업데이트가 아니다
 ★ 주석 L578 - "TODO: Remove shouldHydrate variable when React 18 is stable as it
   can depend on `reactRoot` existing" — 같은 판정을 변수 둘이 한다
   (shouldHydrate 는 성능 표시 콜백 markHydrateComplete / markRenderComplete 만 가른다, L572)
 ★ domEl 은 appElement = document.getElementById('__next') (L288) —
   [01]의 Body 가 만든 `<div id="__next">`(PRENDER L1269-1271)다
```

## 동작 흐름

```text
 client/next.ts L22-24
   initialize({}).then(() => hydrate()).catch(console.error)
   (Turbopack 판 client/next-turbopack.ts 도 같은 둘을 import 한다, L8)

 initialize  L190-290
 L203  initialData = JSON.parse(document.getElementById('__NEXT_DATA__').textContent)
 L206  window.__NEXT_DATA__ = initialData
 L212  __next_set_public_path__(`${prefix}/_next/`)     assetPrefix 를 **런타임에** 정한다
 L214  asPath = getURL()   basePath 를 벗기고 i18n 이면 로케일도 벗긴다 (L217-263)
 L271  pageLoader = new PageLoader(initialData.buildId, prefix)
 L273  window.__NEXT_P 큐를 넘겨받는다 (아래 ★★)
 L283  headManager = initHeadManager()
 L288  appElement = document.getElementById('__next')

 hydrate  L832-1003
 L836  appEntrypoint  = await pageLoader.routeLoader.whenEntrypoint('/_app')
 L843  _app 모듈에 reportWebVitals 가 있으면 onPerfEntry 를 세운다
 L886  pageEntrypoint = await ...whenEntrypoint(initialData.page)
         개발 && 서버 오류가 있으면 기다리지 않는다 (L884, 주석 L882-883)
 L901  catch — 모듈 최상위에서 던진 오류를 initialErr 로 받는다
 L957  window.__NEXT_PRELOADREADY 가 있으면 dynamicIds 를 기다린다
 L961  router = createRouter(page, query, asPath, {
         initialProps, pageLoader, App, Component, wrapApp, err, isFallback,
         subscription: (info, App, scroll) => render({...info, App, scroll}),   ← [03] 이 부른다
         ... })
 L987  initialMatchesMiddleware = await router._initialMatchesMiddlewarePromise
 L1002 render(renderCtx)          ★ await 하지 않는다. hydrate 는 첫 렌더를 안 기다리고 끝난다

 render  L798-830
 L803  서버 오류가 있고 (Component 가 없거나 하이드레이트 패스가 아니면) => renderError
 L814  await doRender(renderingProps)
 L815  catch — cancelled 면 다시 던지고, 아니면 renderError

 doRender  L616-796  (181줄)
 L630  lastAppProps = appProps           주석 L629 - ReactDom 이 던질 때를 대비해 **먼저** 저장
 L634  renderPromise — 앞의 렌더가 남아 있으면 lastRenderReject() 로 **취소시킨다**
 L772  elem = <> <Head callback={onHeadCommit}/> <AppContainer> {App} <Portal><RouteAnnouncer/></Portal> </AppContainer> </>
 L785  renderReactElement(appElement, cb => <Root callbacks={[cb, onRootCommit]}>{elem}</Root>)
 L795  => return renderPromise      onRootCommit(L766-768)이 useLayoutEffect 에서 resolve 한다
```

```text
 ★★ 페이지 청크는 **스스로 큐에 들어온다** (L273-281)

 청크 쪽 (둘 다 같은 모양이다)
   build/webpack/loaders/next-client-pages-loader.ts L24-29
   crates/next-core/js/src/entry/page-loader.ts L7
     (window.__NEXT_P = window.__NEXT_P || []).push([page, function () { return require(...) }])

 index.tsx 쪽
   L275  이미 쌓인 것이 있으면  window.__NEXT_P.map(p => setTimeout(() => register(p), 0))
   L280  window.__NEXT_P = []
   L281  window.__NEXT_P.push = register        ← **배열의 push 를 바꿔 끼운다**

 주석 L276-277 - "Defer page registration for another tick. This will increase the
   overall latency in hydrating the page, but reduce the total blocking time."
 => initialize 전에 온 청크는 배열에 쌓아 두고, 그 뒤에 온 청크는 push 가 곧 등록이다.
    청크와 런타임의 **로드 순서를 가리지 않게** 하는 장치다
 ★ 이미 쌓인 것은 한 틱씩 미룬다 — 하이드레이트 지연을 감수하고 TBT 를 줄인다
```

```text
 ★★ 감싸는 층이 일곱 겹 — 서버([01])의 아홉 겹과 **같지 않다** (AppContainer L296-336)

   Container(오류 경계) > AppRouterContext > SearchParamsContext >
   PathnameContextProviderAdapter > PathParamsContext > RouterContext >
   HeadManagerContext > ImageConfigContext

 서버에만 있는 것  LoadableContext · StyleRegistry(styled-jsx)
 클라이언트에만    Container (componentDidCatch → renderError)
 ※ 개수는 Container 를 빼고 L311-333 의 여는 태그를 센 것이다
   (PathnameContextProviderAdapter 는 Provider 가 아니라 그것을 감싼 컴포넌트지만 한 겹으로 셌다.
    서버 아홉 겹도 같은 방식으로 PRENDER L751-786 을 센 것이다)
```

```text
 makePublicRouterInstance(router)  CROUTER L169-195

   urlPropertyFields(열네 개, L32-47)를 돌며
     객체면   Object.assign(배열이면 [] 아니면 {}, 원본 값)   ← 얕은 복사
     아니면   값 그대로
   instance.events = Router.events
   coreMethodFields(push · replace · reload · back · prefetch · beforePopState, L58-65)는
     원본 인스턴스의 같은 메서드를 부르는 화살표 함수로 감싼다

 ★★ 목록에 `forward` 가 **없다** — 타입은 있다고 말한다
   NextRouter 타입(PROUTER L373-387)의 Pick 에는 'forward' 가 들어 있고
   Router 클래스에도 forward()(L1016-1018)가 있다
   그런데 coreMethodFields(CROUTER L58-65)는 여섯이고 forward 가 빠졌다
 => 브라우저에서 useRouter().forward 는 **undefined** 다 (싱글턴 L97-103 도 같은 목록을 쓴다)
 ★ 어댑터(ADAPT L19-21)의 forward 는 동작한다 — 그쪽은 복사본이 아니라 Router 인스턴스를 받는다
   (index.tsx L301 adaptForAppRouterInstance(router))
```

```text
 ★★ RouterContext 값은 렌더마다 **새 복사본**이다 (index.tsx L318)
   <RouterContext.Provider value={makePublicRouterInstance(router)}>

 => 필드를 복사하고(query 같은 객체는 Object.assign 으로 얕은 복사, 주석 L178
    "makes sure query is not stateful"), 메서드는 원본에 위임한다
 => useRouter(CROUTER L138-147)는 이 Context 를 읽는다. 없으면
    "NextRouter was not mounted." 로 던진다
 ※ doRender 가 매번 새 복사본을 만드니 useRouter 를 쓰는 컴포넌트가 이동 때마다
   새 값을 본다 — 이 인과는 내 추론이다. Router 인스턴스 자체는 상태를 바꿔 쓰는
   가변 객체다([03]의 set L2320 `this.state = state`)
 ★ 반면 AppRouterContext 값은 **처음 한 번만** 만든다 (L300-302 useMemo, 의존 배열 [])
```

```text
 ★★★ `next/navigation` 의 훅이 Pages 에서도 돈다 — 어댑터 셋 ([클라이언트 트리] 04 의 짝)
```

```tsx
// adapters.tsx L12-L39
export function adaptForAppRouterInstance(
  pagesRouter: NextRouter
): AppRouterInstance {
  return {
    back() {
      pagesRouter.back()
    },
    forward() {
      pagesRouter.forward()
    },
    refresh() {
      pagesRouter.reload()
    },
    hmrRefresh() {},
    push(href, { scroll } = {}) {
      void pagesRouter.push(href, undefined, { scroll })
    },
    replace(href, { scroll } = {}) {
      void pagesRouter.replace(href, undefined, { scroll })
    },
    prefetch(href) {
      void pagesRouter.prefetch(href)
    },
    // The bfcacheId concept is App Router-only. Surfaced as a stable
    // placeholder so consumers using this adapter don't crash.
    bfcacheId: '0',
  }
}
```

```text
 => App Router 의 `useRouter()`(next/navigation)를 Pages 에서 부르면 이 객체를 받는다
 ★★ `refresh()` 가 `pagesRouter.reload()` 다 — PROUTER L1002-1004
     reload(): void { window.location.reload() }
   => App Router 에서는 서버 데이터만 다시 받는 refresh 가, Pages 에서는 **전체 새로고침**이다
 ★ hmrRefresh 는 빈 함수, bfcacheId 는 '0' 고정 (주석 L35-36 "App Router-only")

 adaptForSearchParams (ADAPT L47-55)
   router.isReady 가 아니거나 query 가 없으면  => new URLSearchParams()   (빈 값)
   아니면 asPathToSearchParams(router.asPath)   ← **query 가 아니라 asPath 에서** 읽는다
 adaptForPathParams (ADAPT L57-70)
   준비 전이면 null. 준비되면 getRouteRegex(pathname) 의 그룹 이름만 query 에서 골라낸다
 => [클라이언트 트리] 04 가 적은 "Pages 에서 useSearchParams / useParams 가 비는 때" 가
    바로 `isReady === false` 인 동안이다. 그 isReady 를 켜는 것이 아래 ★★★ 이다
 ★ 서버([01])도 같은 세 어댑터로 같은 Context 를 채운다 (PRENDER L727 · L751-757)
```

```text
 ★★★ 하이드레이트 **직후에** 한 번 더 이동한다 — 쿼리 채우기 (Container.componentDidMount L106-158)

 조건 (L115-128) — router.isSsr 이고 다음 중 하나
   fallback 페이지
   `nextExport` 표시 페이지이면서 (동적 경로 · location.search · rewrites · 미들웨어 매치)
     (그 표시는 PRENDER L849-852 — SSG 가 아니고, 빌드 prerender 이거나 개발의 자동 정적·fallback)
   __N_SSG 페이지이면서 (location.search · rewrites · 미들웨어 매치)
 L130  router.replace(pathname + '?' + (query ∪ location.search), asPath,
                      { _h: 1, shallow: !isFallback && !initialMatchesMiddleware })

 주석 L143-145 - "WARNING: `_h` is an internal option for handing Next.js
   client-side hydration. Your app should _never_ use this property."
 => 정적 HTML 은 쿼리를 모른 채 만들어졌다. 브라우저 URL 의 쿼리를 **하이드레이트 뒤에** 넣는다
 => 그 replace 가 [03]의 change 로 가서 isReady 를 true 로 바꾼다 (PROUTER L1239-1240)
 ★ fallback 은 shallow 가 아니다 — 주석 L147-148 "Fallback pages must trigger the data fetch"
```

```text
 ★ isReady 의 초깃값 공식이 서버와 클라이언트에서 **다르다**

 서버  PRENDER L704-709
   getServerSideProps || 페이지 gIP || (_app gIP && !isSSG) || isExperimentalCompile
 클라이언트  PROUTER L824-832
   gssp || gip || isExperimentalCompile || (appGip && !gsp)
   || (!autoExportDynamic && !location.search && !__NEXT_HAS_REWRITES)
 => 클라이언트에만 마지막 항이 있다 — 쿼리 없는 비동적 정적 페이지는 브라우저에서 곧바로 준비된다
 ※ 이 차이가 하이드레이트 불일치를 만드는지는 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 router (모듈 export, L74) · window.next.router (next.ts L16-18 getter)
      --> CROUTER 의 singletonRouter.router 에도 같은 인스턴스가 들어간다 (createRouter L158)
          `import Router from 'next/router'` 의 기본 export 가 그 싱글턴이다
          (packages/next/router.js 가 dist/client/router 를 그대로 내보낸다)

 subscription(render)
      --> Router 가 this.sub 로 쥔다. [03]의 set 이 이동마다 부른다

 reactRoot
      --> 두 번째부터의 모든 화면 교체가 여기로 온다 (L581-584)

 lastAppProps
      --> renderError(L353-428)가 오류 페이지를 그릴 때 이전 Component 와 비교한다 (L382)
```

## 다루지 않는 것

`renderError`(L353-428)의 오류 페이지 선택과 `_error` 의 getInitialProps, 개발에서 서버 오류를 클라이언트에서 다시 던지는 경로(L906-955, 문구 "Next.js navigation API is not allowed to be used in Pages Router." L941 포함)와 `devClient`, 성능 표시(`markHydrateComplete` · `markRenderComplete` L467-561)와 `reportWebVitals`, 프로덕션 CSS 토글(`onStart` L654-692 · `onHeadCommit` L694-764 의 `media="x"` 교체), `Container.scrollToHash`, `head-manager.ts` 와 `route-announcer.tsx`, `route-loader.ts`(426줄)의 `whenEntrypoint` · `onEntrypoint` 구현과 Turbopack 의 `bootstrapRoute`, i18n 로케일 감지(L221-263), `initScriptLoader`(`next/script`), `withRouter` HOC 와 singletonRouter 의 이벤트 배선(CROUTER L105-124)은 이 문서의 범위 밖이다.
