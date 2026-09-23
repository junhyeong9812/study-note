# 04 하위 클래스로 넘겼다 되받기

상위: [요청이 들어와서 렌더로 가기까지](../README.md)

[02]의 정상 출구 `this.run(...)` 부터를 따라간다. 여기서 추상 클래스가 하위 클래스로 일을 넘긴다. **그리고 되받는다.**

## 위치

`packages/next` / `src/server` / `base-server.ts` L1814-L1830 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1814-L1830))

`packages/next` / `src/server` / `next-server.ts` L1078-L1213 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/next-server.ts#L1078-L1213))

## 실제 코드

`run` 과 `runImpl` 을 합쳐 열일곱 줄이다.

```ts
// base-server.ts L1814-L1830
  protected async run(
    req: ServerRequest,
    res: ServerResponse,
    parsedUrl: NextUrlWithParsedQuery
  ): Promise<void> {
    return getTracer().trace(BaseServerSpan.run, async () =>
      this.runImpl(req, res, parsedUrl)
    )
  }

  private async runImpl(
    req: ServerRequest,
    res: ServerResponse,
    parsedUrl: NextUrlWithParsedQuery
  ): Promise<void> {
    await this.handleCatchallRenderRequest(req, res, parsedUrl)
  }
```

```text
 run      추적 스팬만 연다
 runImpl  본문이 **한 줄**이다
```

그 한 줄이 부르는 것은 BASE 에서 이렇게 생겼다.

```ts
// base-server.ts L820-L823
  protected handleCatchallRenderRequest: RouteHandler<
    ServerRequest,
    ServerResponse
  > = () => false
```

```text
 ★ 기본값이 `() => false` 다. abstract 가 아니다
 => "아무것도 안 함" 이 쓸 만한 기본값이라서다.
    [README]의 확장점 (나) 세 개가 전부 이 모양이다
```

## 동작 흐름

```text
 handleCatchallRenderRequest  NEXTSRV L1078-1213 (136줄)
   ★ **return 이 일곱인데 전부 `true` 다**
     L1126  L1141  L1157  L1182  L1186  L1191  L1208

 L1083  {pathname, query} = parsedUrl
 L1084  pathname 이 없으면        => throw 'Invariant: pathname is undefined'
 L1090  addRequestMeta(req, 'bubbleNoFallback', this.minimalMode ? undefined : true)
          주석 L1088-1089 - minimal 모드에서는 폴백을 위로 올리지 않는다.
            그것을 받아 줄 router-server 가 없기 때문이다

 --- 전역 문맥 채우기 ---
 L1094  routerServerGlobal[RouterServerContextSymbol] 이 없으면 만든다
 L1097  relativeProjectDir = relative(process.cwd(), this.dir)
 L1101  그 프로젝트 칸이 비어 있으면
 L1102    {render404: this.render404.bind(this)} 를 넣는다
 L1106  nextConfig 를 넣는다
 L1109  isWrappedByNextServer = true
          주석 L1092-1093 - router-server 가 없는 환경에서도
            render404 와 nextConfig 를 꺼내 쓸 수 있게 노출한다

 --- 매칭 ---
 L1113  try {
 L1115    pathname = removeTrailingSlash(pathname)
            주석 L1114 - "next.js core assumes page path without trailing slash"
 L1117    options = {i18n: this.i18nProvider?.fromRequest(req, pathname)}
 L1120    match = await this.matchers.match(pathname, options)

 L1123    ★ match 가 없으면
 L1124      await this.render(req, res, pathname, query, parsedUrl, true)
 L1126                                              => return true
            주석 L1122 - "If we don't have a match, try to render it anyways."
            ★★ **못 찾아도 렌더로 보낸다.** 여기서 404 를 내지 않는다

 L1131    addRequestMeta(req, 'match', match)
            주석 L1129-1130 - 같은 요청에 매처를 다시 돌리지 않으려고 붙여 둔다
            => [05]의 fastPath 가 이것을 쓴다

 --- Edge 함수 ---
 L1135    edgeFunctionsPages 를 돌며
 L1137      이 매치의 page 가 아니면 continue
 L1139      output === 'export' 이면 render404 => return true
 L1143      delete query[NEXT_RSC_UNION_QUERY]
 L1148      handled = await this.runEdgeFunction({...})
 L1157      handled 이면                            => return true
 L1158      catch (apiError)
 L1160        await this.instrumentationOnRequestError(apiError, req, {...}, false)
 L1172                                              => throw apiError
              주석 L1167 - "Edge runtime does not support ISR"

 --- Pages API ---
 L1179    isPagesAPIRouteMatch(match) 이면
 L1180      output === 'export' 이면 render404       => return true
 L1185      handled = await this.handleApiRequest(req, res, query, match)
 L1186      handled 이면                            => return true
            주석 L1178 - "TODO: move this behavior into a route handler."

 --- 그 밖 전부 ---
 L1189    await this.render(req, res, pathname, query, parsedUrl, true)
 L1191                                              => return true
            ★★★ **BASE 로 되돌아간다**

 L1192  } catch (err) {
 L1193    NoFallbackError 이면                      => throw   (위로 올린다)
 L1197    try {
 L1198      dev 면 formatServerError + logErrorWithOriginalStack
 L1204      아니면 this.logError(err)
 L1206      res.statusCode = 500
 L1207      await this.renderError(err, req, res, pathname, query)
 L1208                                              => return true
 L1209    } catch {}                                 ★ 삼킨다
 L1211                                              => throw err
```

```text
 ★★★ 같은 리터럴 `false` 가 파일마다 다른 뜻이다

 BASE L823   handleCatchallRenderRequest = () => false     "구현이 아직 없다"
 NEXTSRV     handleCatchallRenderRequest                   return 일곱이 **전부 true**
 BASE L652   handleRSCRequest                              return 다섯이 **전부 false**
 BASE L2678  renderPageComponent 의 false                  "내 것이 아니다. 다음 매치로"
             (L2772 는 그것을 **소비하는** `if (result !== false)` 쪽이다)

 RouteHandler 타입의 계약은 "내가 응답을 끝냈다" 를 boolean 으로 말하는 것인데
 그 계약을 **지키는 곳과 안 지키는 곳이 섞여 있다**
```

```text
 ★★★ 넘김이 한 방향이 아니다 — 경계를 **두 번** 넘는다

 BASE handleRequestImpl L1673  this.run(...)
   +-- BASE run L1814 / runImpl L1824
       +-- NEXTSRV handleCatchallRenderRequest L1078   ← 1차 경계
           |  하는 일 = **라우트를 고르는 것**
           |    matchers.match / Edge 함수 / Pages API 갈래
           +-- NEXTSRV L1124 또는 L1189  this.render(...)
               |
               NEXTSRV render L1336  normalizeReq/Res 를 씌운다  ← 2차 경계
                 +-- super.render
                     BASE render L1936 -> renderImpl L1980       [05]

 => 하위 클래스가 가져가는 것이 라우트 선택**만**은 아니다.
    [05]의 renderPageComponent 에서 한 번 더 가로챈다 ([README] 참고)
```

NEXTSRV 에서 BASE 로 되돌아오는 자리를 전수로 세면 열이다.

```text
 L996   this.render404      L1124  this.render        L1140  this.render404
 L1181  this.render404      L1189  this.render        L1207  this.renderError
 L1787  this.render404      L1906  this.render404     L1912  this.renderError
 L1919  this.renderError

 render / render404 / renderError 는 셋 다 BASE 에 산다
 (L996 은 handleNextImageRequest, L1787 은 runMiddleware,
  L1906-1919 는 handleCatchallMiddlewareRequest 쪽이다)
 ★ 열 중 L1787 하나만 **await 이 없다** — 응답이 끝나기를 기다리지 않는다
 ★ 위 L1102 의 `render404: this.render404.bind(this)` 는 열한 번째 경로다.
   호출이 아니라 **참조를 전역에 심어** 나중에 외부(router-server)가 부른다
 ★★ 그리고 이 열은 어느 것도 BASE 로 바로 가지 않는다 —
    render / render404 / renderError 를 NEXTSRV 가 전부 덮어썼다
    (L1336 / L1435 / L1401). 한 겹을 반드시 거친다
```

```text
 ★ 에러 처리의 catch 가 비어 있다 (L1209)

   } catch {}
   throw err

 => 에러 페이지를 렌더하다가 **또** 실패하면 그 두 번째 에러는 버리고
    원래 에러를 던진다. 사용자가 보는 것은 첫 원인이다
```

## 결과가 쓰이는 곳

```text
 요청 메타 'match'
      --> [05]의 renderToResponseImpl 이 fastPath 로 쓴다.
          매처를 두 번 돌리지 않는다

 요청 메타 'bubbleNoFallback'
      --> [05]의 매치 순회가 NoFallbackError 를 위로 올릴지 여기서 삼킬지 가른다

 routerServerGlobal[RouterServerContextSymbol][프로젝트경로]
      --> render404 / nextConfig / isWrappedByNextServer.
          router-server 없이 도는 환경이 이것을 꺼내 쓴다

 this.render(...) 호출
      --> [05]로 넘어간다. 이 흐름의 실제 종착이다
```

## 다루지 않는 것

`this.matchers`(`RouteMatcherManager`)의 매칭 규칙과 `waitTillReady` / `reloadMatchers`, `runEdgeFunction` 과 Edge 런타임 샌드박스, `handleApiRequest` 와 Pages API 라우트 실행, `getEdgeFunctionsPages` / `isPagesAPIRouteMatch` 의 판별, `routerServerGlobal` 을 읽는 쪽(router-server), `instrumentationOnRequestError` 와 계측 훅, `output: 'export'` 정적 내보내기 모드, `handleCatchallMiddlewareRequest`(NEXTSRV L1814)의 미들웨어 실행, `pipe` / `pipeImpl`(BASE L1832 / L1846)은 이 문서의 범위 밖이다.
