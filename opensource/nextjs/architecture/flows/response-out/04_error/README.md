# 04 에러 페이지

상위: [응답이 만들어져 나가기까지](../README.md)

`renderErrorToResponseImpl` 은 215줄인데 하는 일은 하나다. **보여 줄 수 있는 에러 페이지를 찾을 때까지 계속 내려간다.**

## 위치

`packages/next` / `src/server` / `base-server.ts` L2945-L3159 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L2945-L3159))

`packages/next` / `src/server` / `base-server.ts` L3176-L3194 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L3176-L3194))

## 실제 코드

찾기를 포기했을 때의 마지막 바닥이 이것이다.

```ts
// base-server.ts L3155-L3157
      return {
        body: RenderResult.fromStatic('Internal Server Error', 'text/plain'),
      }
```

## 동작 흐름

```text
 ★★★ 폴백 사슬보다 **앞선 단**이 하나 있다 — NEXTSRV L1368-1399

 L1373  is404 = res.statusCode === 404
 L1375  is404 이고 app 디렉터리가 켜져 있으면
 L1376    dev 이면
 L1377      await this.ensurePage(UNDERSCORE_NOT_FOUND_ROUTE_ENTRY).catch(() => {})
           ★ **개발에서 not-found 페이지를 여기서 컴파일한다.**
             BASE L2968 이 그것을 찾을 수 있는 이유다
 L1384    그 페이지가 Edge 함수면
 L1387      await this.runEdgeFunction({page: UNDERSCORE_NOT_FOUND_ROUTE_ENTRY, ...})
 L1395      => return null
           ★★ base 의 폴백 사슬이 **아예 시작되지 않는다**. 여섯 번째 이른 출구다
 L1398  => return super.renderErrorToResponseImpl(ctx, err)
```

```text
 ★★ 셋 다 NEXTSRV 가 덮어쓴다. 아래는 super 에 닿은 뒤의 이야기다
   BASE renderError L2890            <- NEXTSRV L1401  (req/res 정규화 후 super)
   BASE render404   L3176            <- NEXTSRV L1435  (같음)
   BASE renderErrorToResponseImpl L2945 <- NEXTSRV L1368  ★ **이쪽은 동작이 다르다**

 renderError    L2890-2901   추적 껍데기 -> renderErrorImpl
 renderErrorToResponse  L2936-2943  추적 껍데기 -> renderErrorToResponseImpl
 renderErrorToResponseImpl  L2945-3159 (215줄)

 L2951  dev 이고 pathname === '/favicon.ico' 이면
 L2952    => return {body: RenderResult.EMPTY}
          주석 L2949-2950 - 브라우저가 자동으로 요청한다.
            favicon 이 없는 앱에서 404 페이지를 컴파일하지 않으려고 먼저 끊는다

 L2958  try {
 L2959    result = null
 L2961    is404 = res.statusCode === 404
 L2962    using404Page = false
 L2963    hasAppDir = this.enabledDirectories.app

 --- 폴백 사슬 1단: 404 ---
 L2965    is404 이면
 L2966      hasAppDir 이면
 L2968        result = findPageComponents(UNDERSCORE_NOT_FOUND_ROUTE_ENTRY, isAppPath: true)
 L2977        using404Page = result !== null
 L2980      아직 없고 /404 페이지가 있으면
 L2981        result = findPageComponents('/404', isAppPath: false)
 L2991        using404Page = result !== null
              주석 L2987 - "Ensuring can't be done here because you never
                            'match' a 404 route."
              ★★ 그런데 **바로 다음 줄 L2988 이 `shouldEnsure: true` 다.**
                 주석과 인자가 정반대다. L3012-3014 와 L3025-3027 도 같다
                 (같은 주석 아래 L3014 · L3027 이 전부 shouldEnsure: true)
              ※ 주석이 낡은 것인지 인자가 잘못된 것인지는 확인하지 않았다

 --- 폴백 사슬 2단: 상태 페이지 ---
 L2994    statusPage = `/${res.statusCode}`   (let)
 L2996    customErrorRender 메타가 없고 result 도 없고 상태 페이지가 목록에 있으면
 L3003      statusPage 가 '/500' 이 아니거나 dev 가 아니면
                주석 L3001-3002 - dev 의 /500 은 쓰이지 않는다.
                  개발 오버레이가 대신한다
 L3004        아직 없고 hasAppDir 이면
 L3006          result = findPageComponents(statusPage, isAppPath: true)
 L3019        **그리고 무조건** result = findPageComponents(statusPage, isAppPath: false)
              ★★ L3019 에는 `if (!result)` 가 없다.
                 바로 위에서 찾은 app 결과를 pages 결과로 **덮어쓴다**
                 주석 L3018 - "If the above App Router result is empty,
                   fallback to pages router 500 page"
                 => 주석은 "비어 있으면" 이라고 말하는데 코드는 무조건 덮어쓴다

 --- 폴백 사슬 3단: /_error ---
 L3033    아직 없으면
 L3034      result = findPageComponents('/_error', isAppPath: false)
 L3045      statusPage = '/_error'

 L3048    프로덕션이 아니고 using404Page 도 아니고 /_error 는 있는데 /404 가 없으면
 L3054      this.customErrorNo404Warn()      (L2930, execOnce 로 **한 번만**)

 --- 그래도 없으면 ---
 L3057    result 가 없으면
 L3060      dev 이면 => return {body: 폴링 스크립트가 든 HTML}   (아래 별항)
 L3083      아니면 => throw new WrappedBuildError('missing required error components')
              주석 L3058-3059 - 프로젝트 디렉터리가 옮겨지거나 지워졌을 때 그렇다.
                개발에서는 부모 프로세스가 처리한다

 --- 찾았으면 되돌아간다 ---
 L3090    찾은 것에 routeModule 이 있으면 match 메타를 그것으로 갈아끼우고
 L3096    없으면 removeRequestMeta(ctx.req, 'match')
 L3099    try {
 L3100      => return await this.renderToResponseWithComponents(
                 {...ctx, pathname: statusPage, renderOpts: {...ctx.renderOpts, err}},
                 result)
            ★★★ **[01]로 되돌아간다.** 에러 페이지도 같은 파이프라인을 탄다
 L3111    } catch (maybeFallbackError) {
 L3112      NoFallbackError 이면 => throw new Error('invariant: failed to render error page')
 L3115      아니면 => throw maybeFallbackError
          }

 --- 바깥 catch: 에러 페이지를 렌더하다 또 실패했다 ---
 L3117  } catch (error) {
 L3118    renderToHtmlError = getProperError(error)
 L3119    isWrappedError = renderToHtmlError instanceof WrappedBuildError
 L3120    감싼 것이 아니면 this.logError(renderToHtmlError)
 L3123    res.statusCode = 500
 L3124    fallbackComponents = await this.getFallbackErrorComponents(ctx.req.url)  (abstract)
 L3128    있으면
 L3131      match 메타를 그 라우트 모듈 것으로 심고
 L3136      => return this.renderToResponseWithComponents({...ctx, pathname: '/_error', ...},
                                                          {query, components: fallbackComponents})
            ★★ **두 번째 되돌아감**
 L3144        err: isWrappedError ? renderToHtmlError.innerError : renderToHtmlError
              ★ WrappedBuildError 면 **innerError 를 벗겨서** 넘긴다
              주석 L3142-3143 - renderToHtmlError 를 넘긴다.
                err 는 이미 스택트레이스에 잡혀 있기 때문이다
 L3155    없으면
 L3156      => return {body: RenderResult.fromStatic('Internal Server Error', 'text/plain')}
 L3158  }
```

```text
 ★★★ 폴백이 세 겹이다

 1겹  에러 페이지 **찾기** — 다섯 자리를 차례로 뒤진다
        app not-found -> pages /404 -> app /500 -> pages /500 -> /_error

 2겹  찾은 것으로 렌더 — L3100 이 [01]의 파이프라인으로 되돌아간다
        여기서 실패하면 바깥 catch 로 떨어진다

 3겹  폴백 컴포넌트로 다시 렌더 — L3136
        ★★★ **개발 전용이다.** getFallbackErrorComponents(L2699, abstract)를
          NEXTSRV L2146-2152 가 이렇게 채운다
            // Not implemented for production use cases, this is implemented on the
            // development server.
            return null
          진짜 구현은 DEV L1076-1081 (loadDefaultErrorComponents)뿐이다

 바닥  L3156  평문 'Internal Server Error' 한 줄

 => **프로덕션에서는 L3128 이 언제나 거짓이다.** 사슬이 실질 두 겹이고,
    바깥 catch 에 떨어지면 곧장 평문 한 줄로 간다
 => 세 겹은 개발에서만 완성된다
```

개발에서 에러 컴포넌트를 못 찾으면 HTML 대신 **스스로 다시 시도하는 스크립트**를 보낸다.

```ts
// base-server.ts L3060-L3081
        if (this.dev) {
          return {
            // wait for dev-server to restart before refreshing
            body: RenderResult.fromStatic(
              `
              <pre>missing required error components, refreshing...</pre>
              <script>
                async function check() {
                  const res = await fetch(location.href).catch(() => ({}))

                  if (res.status === 200) {
                    location.reload()
                  } else {
                    setTimeout(check, 1000)
                  }
                }
                check()
              </script>`,
              HTML_CONTENT_TYPE_HEADER
            ),
          }
        }
```

```text
 => fetch(location.href) 가 200 이면 reload, 아니면 1초 뒤 다시 확인한다
 주석 L3062 - "wait for dev-server to restart before refreshing"
 => 개발 서버가 다시 뜨는 것을 **브라우저가 기다린다**
```

```text
 ★ 경고는 한 번만 나온다 (L2930 / L3054)

   private customErrorNo404Warn = execOnce(() => { ... })

 execOnce 로 감싸 놓아서 프로세스 수명 동안 한 번이다.
 조건은 L3048-3053 — 프로덕션이 아니고, 404 페이지를 안 쓰는데,
 /_error 는 있고 /404 는 없을 때다
 => 커스텀 _error 만 만들고 404 를 안 만든 프로젝트에 하는 안내다
```

```text
 render404  L3176-3194 — 얇다

 L3185  i18n 설정이 있으면
 L3186    locale 메타가 없으면 기본 로케일을 심고
 L3189    defaultLocale 도 심는다
          주석 L3184 - 요청 메타에 로케일이 반드시 있게 한다
 L3192  res.statusCode = 404
 L3193  => return this.renderError(null, req, res, pathname, query, setHeaders)

 => 상태 코드를 박고 renderError 로 넘기는 것이 전부다.
    404 페이지 찾기는 위의 폴백 사슬 1단이 한다
```

## 결과가 쓰이는 곳

```text
 반환한 ResponsePayload | null
      --> [03]의 pipeImpl 이 받는다. 에러 페이지도 라우트 모듈을 타면
          null 이 돌아온다 — 정상 렌더와 같은 길이다
      ★ 예외 하나 — renderErrorImpl(L2918)이 감싼 fn 은 이 반환을 받고도
        minimalMode 이고 상태가 500 이면 **payload 대신 err 를 던진다**(L2921-2923)

 res.statusCode
      --> 404 / 500 이 여기서 확정된다. [01]의 STATIC_STATUS_PAGES 갈래와
          L2994 의 statusPage 계산이 이 값을 읽는다

 요청 메타 'match'
      --> L3091 이 에러 페이지의 라우트 모듈로 갈아끼운다.
          [01]이 그 match 로 다시 판정한다

 요청 메타 'customErrorRender'
      --> [요청 흐름]의 renderToResponseImpl L2821 이 켜고 끈다.
          여기 L2997 이 그것을 보고 상태 페이지 찾기를 건너뛴다
```

## 다루지 않는 것

`findPageComponents`(L365, abstract)가 컴포넌트를 찾는 방식과 `shouldEnsure` 의 의미, `getFallbackErrorComponents`(L2699, abstract)를 하위 클래스가 채우는 방식, `WrappedBuildError` / `NoFallbackError` 가 던져지는 다른 자리, `UNDERSCORE_NOT_FOUND_ROUTE_ENTRY` 와 App Router 의 `not-found` 규약, `renderErrorImpl`(L2903)의 본문과 `setHeaders` 인자, `renderErrorToHTML`(L3161) / `getStaticHTML`(L1913)의 경로, `execOnce` 의 구현, 개발 오버레이(`next-devtools`)가 /500 을 대신하는 방식은 이 문서의 범위 밖이다.
