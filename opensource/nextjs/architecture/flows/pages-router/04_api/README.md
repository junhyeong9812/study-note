# 04 API 라우트

상위: [Pages Router 가 페이지를 그리기까지](../README.md)

`pages/api/*` 는 페이지와 같은 템플릿 방식으로 번들이 되지만, 들어오는 자리가 다르고 **응답 캐시도 렌더도 없다.** 사용자 함수에 Node 의 `req` · `res` 를 거의 그대로 넘기되, 그 전에 `res` 에 메서드 여덟 개를 덧붙인다. [페이지 아닌 요청]이 "범위 밖" 으로 남긴 `handleApiRequest` 가 여기서 이어진다.

## 위치

`packages/next` / `src/server/api-utils/node` / `api-resolver.ts` L331-L489 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/api-utils/node/api-resolver.ts#L331-L489))

## 실제 코드

`apiResolver`(L331-489, 159줄)의 한가운데 — Node 응답 객체에 편의 메서드를 **직접 대입한다.**

```ts
// api-resolver.ts L410-L426
    apiRes.status = (statusCode) => sendStatusCode(apiRes, statusCode)
    apiRes.send = (data) => sendData(apiReq, apiRes, data)
    apiRes.json = (data) => sendJson(apiRes, data)
    apiRes.redirect = (statusOrUrl: number | string, url?: string) =>
      redirect(apiRes, statusOrUrl, url)
    apiRes.setDraftMode = (options = { enable: true }) =>
      setDraftMode(apiRes, Object.assign({}, apiContext, options))
    apiRes.setPreviewData = (data, options = {}) =>
      setPreviewData(apiRes, data, Object.assign({}, apiContext, options))
    apiRes.clearPreviewData = (options = {}) =>
      clearPreviewData(apiRes, options)
    apiRes.revalidate = (
      urlPath: string,
      opts?: {
        unstable_onlyGenerated?: boolean
      }
    ) => revalidate(urlPath, opts || {}, req, apiContext)
```

```text
 ★★ `res.json` · `res.status` 는 Node 에 없는 메서드다. 여기서 **원본 객체에 붙인다**
   status · send · json · redirect · setDraftMode · setPreviewData ·
   clearPreviewData · revalidate    (여덟. L410-426 에서 셌다)
 그리고 바로 위 L389-409 가 write · end 를 **감싼다** (응답 크기를 세려고)
 => 사용자 핸들러가 받는 `res` 는 **같은 ServerResponse 인스턴스**다. 래퍼 객체가 아니다
 ★ req 쪽도 같다 — cookies · previewData · preview · draftMode 는 게으른 속성으로,
   query 는 Object.defineProperty 로 (L357-375)
   주석 L358-359 - "Ensure req.query is a writable, enumerable property ...
     This addresses Express 5.x, which defines query as a getter only (read-only)."
```

## 동작 흐름

```text
 [요청 -> 렌더] 04 가 멈춘 자리
 NEXTSRV handleCatchallRenderRequest
 L1179  isPagesAPIRouteMatch(match) 이면
 L1180    output === 'export' 이면 render404                 => return true
 L1185    handled = await this.handleApiRequest(req, res, query, match)
            NEXTSRV L1244-1251  => return this.runApi(...)   (한 줄 위임)

 runApi  NEXTSRV L558-613
 L564  getEdgeFunctionsPages() 를 돌며 이 경로면 runEdgeFunction  => 처리됐으면 return true
 L584  req.url 을 요청 메타 'initURL' 로 **되돌린다** (L584-585)
         주석 L583 - "Restore original URL as the handler handles it's own parsing"
 L587  module = await new NodeModuleLoader().load(match.definition.filename)   (L587-588)
 L604  await module.handler(req.originalRequest, res.originalResponse, {waitUntil, requestMeta})
 L612  => return true

 handler  PATPL L47-212 (템플릿)
 L70   routeModule.prepare(req, res, {srcPage})       없으면 400 'Bad Request'
 L94   invokeRouteModule = routeModule.render(req, res, { query: {...query, ...params}, ... })
         PAPIMOD render L136-161  => apiResolverWrapped(...)
                                   = wrapApiHandler(page, apiResolver)  트레이싱 스팬만 씌운다
 L198  catch  개발이면 다시 던지고, 아니면 sendError(res, 500, 'Internal Server Error')
 L206  finally  ctx.waitUntil?.(Promise.resolve())

 apiResolver  APIRES L331-489
 L346  모듈이 없으면 404 'Not Found'   ※ 이 갈래는 닿지 않는다 — apiResolver 를 부르는 곳은
          PAPIMOD 하나이고 `this.userland` 를 넘기는데, 생성자가 default export 가 함수가 아니면
          먼저 던진다 (module.ts L119-123 · L141-145)
 L351  config.api 의 bodyParser · responseLimit · externalResolver
 L357  req 에 cookies · query · previewData · preview · draftMode
 L378  bodyParser 가 켜져 있고 req.body 가 없으면  parseBody(req, sizeLimit ?? '1mb')
 L389  write · end 를 감싸 contentLength 를 센다
 L410  res 에 메서드 여덟 (위 실제 코드)
 L436  const apiRouteResult = await resolver(req, res)        ← 사용자 함수
 L438  (개발) 반환값 검사 · 응답 안 보냄 경고
 L456  catch  onError(계측) → ApiError 면 그 상태 코드, 개발이면 던지고, 아니면 500
```

```text
 ★★★ 페이지와 **같은 모양**이지만 가운데가 비어 있다

                 페이지 (pages-handler)                API (pages-api 템플릿)
 들어오는 자리   BASE L2603 ComponentMod.handler        NEXTSRV L604 module.handler
                 ([응답 나가기] 를 지나서)              (renderPageComponent 를 거치지 않는다)
 prepare         RMOD prepare                          RMOD prepare
 응답 캐시        routeModule.handleResponse            **없다**
 렌더            renderToHTMLImpl                      사용자 함수 호출
 응답 쓰기       sendRenderResult                      사용자가 res 에 직접

 => 저장소 전체 grep `\.handleResponse(` 네 건([README])에 PATPL 은 없다.
    API 응답은 **ISR · 응답 캐시와 무관**하다
 ★ 주석 NEXTSRV L1178 - "TODO: move this behavior into a route handler."
```

```text
 ★★ `waitUntil` 에 **이미 풀린 약속**을 넘긴다 (PATPL L206-211) — 무엇을 닫는 것이 아니라
   "보류 작업이 없다" 는 신호다 (아래 주석)

   // We don't allow any waitUntil work in pages API routes currently
   // so if callback is present return with resolved promise since no
   // pending work
   ctx.waitUntil?.(Promise.resolve())

 => 400 으로 끝나는 조기 반환(L75)에서도 같은 한 줄을 부른다
 => 응답 뒤 작업(after 류)을 API 라우트에서 받지 않는다는 선언이다
```

```text
 ★★ "제한" 이 **경고뿐**이다 (L395-409)

   if (responseLimit && contentLength >= maxContentLength) {
     console.warn(`API response for ${req.url} exceeds ${...}. API Routes are meant to respond quickly. ...`)
   }
   return endResponse.apply(apiRes, args)

 => 기본 한도(RESPONSE_LIMIT_DEFAULT = 4 * 1024 * 1024, api-utils/index.ts L114)를 넘어도 **그대로 보낸다**
 ★ 요청 쪽은 다르다 — parseBody 에 sizeLimit(기본 '1mb')을 넘긴다 (L379-384).
   parseBody 가 넘으면 어떻게 하는지는 이 문서에서 읽지 않았다
```

```text
 ★★ 개발에서만 도는 검사가 **실제 실패를 가린다** (L431-455)

 L439  반환값이 있으면
 L440    Response 객체면  => throw 'API route returned a Response object in the Node.js
                             runtime, this is not supported. Please use `runtime: "edge"` instead'
 L445    아니면           console.warn 'API handler should not return a value'
 L450  externalResolver 가 아니고 응답을 안 보냈고 pipe 도 없으면
          console.warn 'API resolved without sending a response ..., this may result in stalled requests.'

 => 셋 다 `process.env.NODE_ENV !== 'production'` 안이다
 ※ 프로덕션에서 Response 를 돌려주면 아무도 그것을 보내지 않아 요청이 멈출 것이다 —
   위 경고 문구("stalled requests")와 코드에서 내가 추론한 것이다
```

```text
 ★★ res.revalidate — 온디맨드 ISR 이 **자기 서버에 다시 요청**한다 (L248-329)

 L261  headers[PRERENDER_REVALIDATE_HEADER] = context.previewModeId
         unstable_onlyGenerated 면 PRERENDER_REVALIDATE_ONLY_GENERATED_HEADER 도
 L281  allowedRevalidateHeaderKeys 에 든 요청 헤더만 옮겨 싣는다
         trustHostHeader 거나 개발이면 'cookie' 도 (L273-275)
 L293  internalRevalidate 가 있으면  그것으로 (router-server 의 내부 경로)
 L301  없고 trustHostHeader 면     fetch(`https://${host}${urlPath}`, {method: 'HEAD'})
         x-vercel-cache 또는 x-nextjs-cache 가 REVALIDATED 인지 본다 (L309-318)
 L319  둘 다 없으면                throw 'Invariant: missing internal router-server-methods'

 주석 L290-292 - "We use the revalidate in router-server if available. If we are
   operating without router-server (serverless) we must go through network layer
   with fetch request"
 => 받는 쪽은 [README]의 PHAND 다 — prepare 가 isOnDemandRevalidate 를 세우고
    L557-567 이 x-nextjs-cache: REVALIDATED 를 붙인다
 ★ 인증 값이 previewModeId 다 — 프리뷰 모드용 비밀이 재검증 요청의 비밀도 겸한다
   ※ 받는 쪽이 그 값을 어떻게 검증하는지(prepare 안)는 확인하지 않았다
```

## 결과가 쓰이는 곳

```text
 사용자 핸들러가 res 에 쓴 것
      --> 그대로 소켓으로 나간다. Next.js 가 몸통을 다시 만지지 않는다
          (send · json 을 쓰면 sendData L58-112 가 ETag · Content-Type · Content-Length 를 붙인다)

 NEXTSRV runApi 의 true
      --> handleCatchallRenderRequest 가 "내가 끝냈다" 로 받는다 (L1186)

 onError(계측) 호출
      --> routerKind 'Pages Router' · routeType 'route' 로 instrumentation 의 onRequestError 에 간다 (L457-470)

 Set-Cookie (setDraftMode · setPreviewData)
      --> 다음 페이지 요청에서 [01]의 tryGetPreviewData 가 읽는다
          (__prerender_bypass · __next_preview_data 쿠키 — 상수 이름 COOKIE_NAME_PRERENDER_*)
```

## 다루지 않는 것

`parseBody`(`api-utils/node/parse-body.ts`)의 본문 해석과 크기 제한 처리, `sendData`(L58-112) · `sendEtagResponse` 의 ETag 규칙, `setPreviewData`(L165-246)의 JWT 서명·암호화와 2KB 제한, `clearPreviewData` · `redirect` · `sendError` · `ApiError`(`api-utils/index.ts`), `tryGetPreviewData` 의 검증, Edge 런타임 API 라우트(`runEdgeFunction` 과 `edge-ssr` 계열 템플릿), `RouteModule.prepare` 의 본문과 온디맨드 재검증 요청을 판별하는 규칙, router-server 의 `revalidate`(internalRevalidate) 구현, PATPL 의 트레이싱(L94-171 의 스팬 속성), 개발 서버의 API 라우트 on-demand 컴파일은 이 문서의 범위 밖이다.
