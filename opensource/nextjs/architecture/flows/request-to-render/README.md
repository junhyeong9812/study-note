# 요청이 들어와서 렌더로 가기까지

상위: [Next.js 아키텍처 지도](../../README.md)

브라우저가 보낸 HTTP 요청 하나가 `base-server.ts` 를 지나 렌더러에 닿기까지를 따라간다. 이 파일이 Next.js 서버의 척추다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `BASE` = `server/base-server.ts`(3195줄), `NEXTSRV` = `server/next-server.ts`(2195줄), `DEV` = `server/dev/next-dev-server.ts`.

## 위치

`packages/next` / `src/server` / `base-server.ts` L325-L325 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L325-L325))

## 실제 코드

```ts
// base-server.ts L325-L328
export default abstract class Server<
  ServerOptions extends Options = Options,
  ServerRequest extends BaseNextRequest = BaseNextRequest,
  ServerResponse extends BaseNextResponse = BaseNextResponse,
```

파일 전체가 **추상 클래스 하나**다(본문은 다음 줄 `> {` 에서 열려 L3195 까지 간다). 이것을 직접 상속하는 것은 **하나뿐**이다.

```ts
// next-server.ts L175-L178
export default class NextNodeServer extends BaseServer<
  Options,
  NodeNextRequest,
  NodeNextResponse
```

```text
 ★★ 계층이 2단이 아니라 **3단**이다

 BASE    L325   abstract class Server<ServerOptions, ServerRequest, ServerResponse>
   +-- NEXTSRV L175  NextNodeServer extends BaseServer<Options, NodeNextRequest, NodeNextResponse>
         +-- DEV L130  DevServer extends Server

 ★ DEV 의 `extends Server` 의 `Server` 는 base-server 가 아니다
   DEV L40  import Server, { WrappedBuildError } from '../next-server'
   => **NextNodeServer 다.** DevServer 는 base 를 직접 상속하지 않는다

 => abstract 21개를 채우는 것은 **NextNodeServer 하나**다.
    DevServer 는 그중 다섯쯤(getPagesManifest · getBuildId · findPageComponents ·
    hasPage · getMiddleware)만 개발용으로 다시 쓰고 나머지는 물려받는다
 => 제네릭 인자도 NextNodeServer 가 이미 고정해 놓은 것을 물려받는다
```

## 동작 흐름

```text
 ★★★ 넘김이 한 방향이 아니다. 경계를 **네 번 이상** 넘는다

 BASE  handleRequest        L910    추적 껍데기   (DEV L607 이 덮어쓴다)
   +-- handleRequestImpl    L1026   정규화 파이프라인 (670줄)
       +-- run              L1814   추적 껍데기   (DEV L630 이 덮어쓴다)
           +-- runImpl      L1824   본문 한 줄
               +-- handleCatchallRenderRequest
                   |                            ← 1차 경계
                   NEXTSRV L1078    라우트를 고른다
                     +-- this.render(...)       NEXTSRV L1124 / L1189
                         |
                         NEXTSRV render L1336   ← 2차 경계. **여기서 한 번 더 잡힌다**
                           normalizeReq/Res 를 씌우고 super.render 를 부른다
                           |
                           BASE render L1936 -> renderImpl L1980
                             +-- renderToResponseImpl L2704
                                 +-- this.renderPageComponent(...)  L2761
                                     |                    ← 3차 경계
                                     NEXTSRV renderPageComponent L781
                                       Edge 함수 페이지면 runEdgeFunction 하고
                                       L806 => return null
                                       ★★ **여기서 렌더가 끝난다.** base 로 안 돌아온다
                                       L811 아니면 super.renderPageComponent

 ★★★ 그러니 "렌더 파이프라인의 주인은 끝까지 base-server 다" 는 **틀렸다**.
   BASE L2772 의 `result !== false` 는 `null` 도 통과시킨다.
   Edge 함수로 서빙되는 페이지는 응답을 **하위 클래스가 만든다**
 ※ 에러 경로도 같다 — BASE renderErrorToResponseImpl L2945 를
   NEXTSRV L1368 이 덮어쓰고 app-dir 404 를 Edge 로 처리한 뒤 null 을 돌린다
```

NEXTSRV 에서 BASE 의 메서드 이름으로 되돌아오는 자리를 전수로 세면 열이다.

```text
 NEXTSRV L996   this.render404      L1124  this.render        L1140  this.render404
         L1181  this.render404      L1189  this.render        L1207  this.renderError
         L1787  this.render404      L1906  this.render404     L1912  this.renderError
         L1919  this.renderError
 + L1103  this.render404.bind(this) 를 전역 문맥에 심는다 — 나중에 **외부가** 부른다

 ★ L1787 만 `await` 이 없다 (runMiddleware 안)
 ★★ 그런데 이 열은 **어느 것도 BASE 로 바로 가지 않는다.**
    render / render404 / renderError 를 NEXTSRV 가 전부 덮어썼기 때문이다
    (L1336 / L1435 / L1401) — 한 겹을 반드시 거친다
```

```text
 ★★ 확장점이 세 종류다

 (가) abstract  **21개**  — 하위가 반드시 채운다
      L353 getPublicDir          L354 getHasStaticDir       L355 getPagesManifest
      L356 getAppPathsManifest   L357 getBuildId            L358 getinterceptionRoutePatterns
      L361 getEnabledDirectories L365 findPageComponents    L378 getPrerenderManifest
      L379 getNextFontManifest   L382 attachRequestMeta     L386 hasPage
      L388 sendRenderResult      L399 runApi                L406 renderHTML
      L414 getIncrementalCache   L435 loadEnvConfig         L1765 handleUpgrade
      L2698 getMiddleware        L2699 getFallbackErrorComponents
      L2702 getRoutesManifest

 (나) 속성형 셋 — 기본값이 `() => false` 다
      BASE L815 handleNextImageRequest        <- NEXTSRV L931  덮어씀
      BASE L820 handleCatchallRenderRequest   <- NEXTSRV L1078 덮어씀
      BASE L825 handleCatchallMiddlewareRequest <- NEXTSRV L1814 덮어씀
      ※ abstract 로 두지 않은 이유를 소스는 말하지 않는다.
        L2779 의 `extended in child class web-server` 주석이 가리키는
        **지금은 사라진 제3의 하위 클래스** 때문이었을 수 있다 (내 추측이다)

 (다) 비abstract 메서드 — 동작하는 기본값을 두고 하위가 덮어쓴다. **열일곱**이다
      ★★ 이 흐름의 척추와 출구가 전부 여기 들어 있다

      NEXTSRV 가 덮어쓰는 것 (열셋)
        L1758 getRequestHandler             <- NEXTSRV L1269   [01]
        L1748 getRequestHandlerWithMetadata <- NEXTSRV L1283
        L1936 render                        <- NEXTSRV L1336   ★ [05] 앞
        L3176 render404                     <- NEXTSRV L1435
        L2890 renderError                   <- NEXTSRV L1401
        L2865 renderToHTML                  <- NEXTSRV L1354
        L3161 renderErrorToHTML             <- NEXTSRV L1419
        L2945 renderErrorToResponseImpl     <- NEXTSRV L1368   ★ null 을 돌린다
        L2640 renderPageComponent           <- NEXTSRV L781    ★★ 렌더를 가로챈다
        L1796 prepareImpl                   <- NEXTSRV L372
        L1797 loadInstrumentationModule     <- NEXTSRV L353
        L878  instrumentationOnRequestError <- NEXTSRV L2154
        L1799 close                         <- NEXTSRV L2172
        L1976 getInternalWaitUntil          <- NEXTSRV L2176

      DEV 가 덮어쓰는 것
        L910  handleRequest                 <- DEV L607   ★★ [01]의 시작점이다
        L1814 run                           <- DEV L630   ★★ [04]의 시작점이다
        L830  getRouteMatchers              <- DEV L268
        L2033 getStaticPaths                <- DEV L815
        L418  getServerComponentsHmrCache       <- DEV L260 만
        L431  getServerComponentsHmrRefreshHash <- DEV L264 만
```

```text
 ★★ 개발 서버에서는 [01]과 [04]의 시작점이 다르다

 DEV L607  handleRequest  -> super.handleRequest
 DEV L630  run            -> await this.ready?.promise
                             basePath 를 떼고 /_next 를 따로 처리한 뒤 super.run
 => 이 문서들이 그린 "BASE 에서 시작한다" 는 **프로덕션 기준**이다
```

`protected` 라고 전부 확장점인 것은 아니다. `getAppPathRoutes`(L1801) · `reloadMatchers`(L648) 같은 것은 아무도 덮어쓰지 않는다.

```text
 ★★ public 메서드가 거의 전부 추적 껍데기다. Impl 짝이 **열**이다

   handleRequestImpl L1026   prepareImpl L1796   runImpl L1824
   pipeImpl L1846            renderImpl L1980
   renderToResponseWithComponentsImpl L2110     renderToResponseImpl L2704
   renderToHTMLImpl L2876    renderErrorImpl L2903
   renderErrorToResponseImpl L2945

 껍데기는 대개 이 모양이다
   protected async run(req, res, parsedUrl) {
     return getTracer().trace(BaseServerSpan.run, async () =>
       this.runImpl(req, res, parsedUrl))
   }

 => 껍데기가 OTEL 스팬을 만들고 Impl 이 일한다. **관측이 구조에 박혀 있다**
```

1. [진입과 추적](01_entry/README.md) — 요청이 실제로 들어오는 자리와 스팬 이름이 뒤늦게 바뀌는 이유.
2. [정규화 파이프라인](02_normalize/README.md) — `handleRequestImpl` 670줄과 그 출구 스물.
3. [x-matched-path 블록](03_matched-path/README.md) — 서버리스에서만 도는 388줄.
4. [하위 클래스로 넘겼다 되받기](04_handoff/README.md) — `run` 부터 `handleCatchallRenderRequest` 까지.
5. [렌더로 들어가기](05_render/README.md) — 위로 되돌아가는 고리와 매치 순회.

```text
 ★★ minimalMode 가 이 흐름 전체를 가른다 — 파일에 **28번** 나온다

 갈리는 자리
   L538   값이 주입되는 곳
   L552   RSC 노멀라이저를 만들지 (L555 도 같다)   [02]
   L1118  x-matched-path 블록에 들어갈지           [03]
   L1519  로케일을 지울지
   L1688  에러를 위로 올릴지
   L1960  getWaitUntil 이 undefined 를 돌려줄지
   L2011  renderImpl 이 위로 되돌아갈지            [05]
   L2141  CDN 오염 방어를 켤지                     [05]
   L2712  캐시 무효화 파라미터를 심을지            [05]

 ★ 켜지는 길이 셋이다 (L535-539)
   ① 생성자 옵션 minimalMode
   ② 환경변수 NEXT_PRIVATE_MINIMAL_MODE
   ③ **프로덕션 번들에서 상수 치환** — L535-536 주석이 그것을 말한다
        "this is a hack to avoid Webpack knowing this is equal to this.minimalMode
         because we replace this.minimalMode to true in production bundles."
     => L537 이 키를 문자열로 빼서 `this[minimalModeKey]` 로 쓴 것은
        Webpack 이 이 대입을 알아보지 못하게 하려는 것이다
   ※ ②로만 켜면 L521 `hasStaticDir = !minimalMode && ...` 이 **치환 전 지역변수**를 쓰므로
     minimalMode 가 참인데 hasStaticDir 도 참일 수 있다 (내 관찰이다)

 뜻은 L1961-1963 의 주석이 말한다
   "we're built for a serverless environment, and `waitUntil` is not available,
    but using a noop would likely lead to incorrect behavior,
    because we have no way of keeping the invocation alive."

 => minimalMode = **서버리스**. 응답을 보내면 실행이 끝난다.
    그래서 "응답 뒤에 뭘 더 한다"(after)를 지원할 수 없고,
    조용히 넘기는 noop 대신 **에러를 고른다**
```

## 결과가 쓰이는 곳

```text
 parsedUrl (다듬어진 것)
      --> [04]의 handleCatchallRenderRequest 가 이것으로 라우트를 고른다

 요청 메타 (addRequestMeta 로 붙인 것들)
      --> isRSCRequest · isNextDataReq · locale · postponed · params 가
          렌더 끝까지 따라간다. 요청 객체가 이 흐름의 **누적 상태**다

 this.run 의 반환
      --> handleRequestImpl 의 정상 출구. 여기서부터 응답이 만들어진다
```

## 다루지 않는 것

`pipe` / `pipeImpl`(L1832 / L1846)이 응답을 흘려보내는 방식과 `getStaticHTML`(L1913) · `getStaticPaths`(L2033), 미들웨어 갈래(`handleCatchallMiddlewareRequest`, NEXTSRV L1814)의 본문, `handleUpgrade`(L1765)의 웹소켓 경로, `DevServer`(DEV L130)가 덮어쓰는 것 전부, 증분 캐시(`getIncrementalCache` L414)의 구현과 `'use cache'`, `route-modules/` 의 라우트 모듈 실행, Edge 런타임(`server/web/`)의 별도 서버, 그리고 렌더러 안쪽(App Router 의 `app-render.tsx`, Pages Router 의 `render.tsx`)은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 진입과 추적](01_entry/README.md)
- [02 정규화 파이프라인](02_normalize/README.md)
- [03 x-matched-path 블록](03_matched-path/README.md)
- [04 하위 클래스로 넘겼다 되받기](04_handoff/README.md)
- [05 렌더로 들어가기](05_render/README.md)
