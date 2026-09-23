# 01 진입과 추적

상위: [요청이 들어와서 렌더로 가기까지](../README.md)

요청이 실제로 들어오는 자리는 `base-server.ts` 가 아니다. 그리고 들어온 뒤 가장 먼저 하는 일은 라우팅이 아니라 **추적 스팬을 여는 것**이다.

## 위치

`packages/next` / `src/server` / `next-server.ts` L1269-L1304 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/next-server.ts#L1269-L1304))

`packages/next` / `src/server` / `base-server.ts` L910-L1024 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L910-L1024))

## 실제 코드

진입점은 `NEXTSRV` 가 덮어쓴다.

```ts
// next-server.ts L1300-L1303
    const handler = super.getRequestHandler()

    return (req, res, parsedUrl) =>
      handler(this.normalizeReq(req), this.normalizeRes(res), parsedUrl)
```

인용한 것은 `getRequestHandler`(L1269-1278)가 부르는 `private makeRequestHandler()`(L1291-1304)의 끝부분이다. `super.getRequestHandler()` 로 BASE 의 핸들러를 받아 놓고, 그것을 부르기 전에 `normalizeReq` / `normalizeRes` 를 한 겹 씌운다.

```text
 => 노드의 IncomingMessage / ServerResponse 가 BASE 에 닿기 **전에**
    Next 의 BaseNextRequest / BaseNextResponse 로 감싸인다
    BASE 가 `req.body(...)` · `res.send()` 같은 메서드를 쓸 수 있는 이유다
```

```text
 ★★ 그런데 같은 메서드의 첫 줄에서 prepare 가 **이미 발사된다**

 NEXTSRV L1296-1298
   this.prepare().catch((err) => {
     console.error('Failed to prepare server', err)
   })

 => 핸들러를 **만드는 시점**, 즉 첫 요청보다 먼저 걸쇠가 걸린다.
    아래 L915 의 `await this.prepare()` 는 대개 이미 끝난 약속을 기다리는 것이다
```

그 다음이 `handleRequest`(L910) 다. 115줄짜리 메서드인데 상태를 바꾸는 줄은 맨 앞 셋뿐이다.

```ts
// base-server.ts L915-L917
    await this.prepare()
    const method = req.method.toUpperCase()
    const tracer = getTracer()
```

## 동작 흐름

```text
 handleRequest  BASE L910-1024  (115줄) — 거의 전부 추적이다

 L915  await this.prepare()                     ★ 유일하게 상태를 바꾸는 일
 L916  method = req.method.toUpperCase()
 L917  tracer = getTracer()

 L919  handleRequest = () =>
 L920    tracer.withPropagatedContext(req.headers, () =>
 L926      parentSpan = tracer.getActiveScopeSpan()
 L928      tracer.trace(
 L929        BaseServerSpan.handleRequest,
 L931        spanName: `${method}`               ★ 처음 이름은 **메서드뿐**이다
 L934        'http.method' / 'http.target'
 L938        async (span) =>
 L939          this.handleRequestImpl(req, res, parsedUrl)   ← 실제 일은 [02]
 L939            .finally(() => {                 ← 응답이 끝난 **뒤에** 스팬을 손본다
 L940              span 이 없으면              => return
 L942              isRSCRequest = getRequestMeta(req, 'isRSCRequest') ?? false
 L943              span.setAttributes({'http.status_code', 'next.rsc'})
 L948              statusCode >= 500 이면
 L951                span.setStatus({code: SpanStatusCode.ERROR})
 L955                span.setAttribute('error.type', statusCode)
 L958              rootSpanAttributes = tracer.getRootSpanAttributes()
 L960              없으면 (OTEL 이 꺼져 있다)  => return
 L962              루트 스팬 타입이 handleRequest 가 아니면
 L966                console.warn('Unexpected root span type ...')
 L971                                          => return
 L974              route = rootSpanAttributes.get('next.route')
 L975              route 가 있으면
 L985                span.updateName(name)        ★ **스팬 이름을 바꾼다**
 L991                parentSpan 이 있고 자기가 아니면
 L992                  parentSpan.setAttribute('http.route', route)
 L994              아니면
 L995                span.updateName(isRSCRequest ? `RSC ${method}` : `${method}`)

 L1001  isRequestInsightsEnabled() 가 아니면
 L1002    => return handleRequest()               평소의 길
 L1005  requestIdHeader = req.headers[NEXT_REQUEST_ID_HEADER]
 L1006  requestId = 문자열이면 그것, 아니면 nanoid()
 L1013  => return runWithRequestInsightsIdentity({...}, handleRequest)
```

```text
 ★★ 스팬 이름을 **뒤늦게 고친다** (L985)

 요청을 받는 시점에는 어느 라우트인지 모른다. 그것을 알아내는 것이
 이 흐름의 [02]·[03]·[04] 가 하는 일이다.
 그래서 스팬은 `GET` 으로 시작해 일이 다 끝난 뒤 `GET /blog/[slug]` 가 된다

 L939 의 `.finally` 가 그 자리다 — 성공이든 실패든 이름은 고친다
```

```ts
// base-server.ts L974-L996
              const route = rootSpanAttributes.get('next.route')
              if (route) {
                const name = isRSCRequest
                  ? `RSC ${method} ${route}`
                  : `${method} ${route}`

                span.setAttributes({
                  'next.route': route,
                  'http.route': route,
                  'next.span_name': name,
                })
                span.updateName(name)

                // Propagate http.route to the parent span if one exists and
                // is different from the handleRequest span. This ensures APM
                // tools that read attributes from the outermost span (e.g.
                // a platform-created HTTP span) can derive the resource name.
                if (parentSpan && parentSpan !== span) {
                  parentSpan.setAttribute('http.route', route)
                }
              } else {
                span.updateName(isRSCRequest ? `RSC ${method}` : `${method}`)
              }
```

```text
 ★ RSC 요청이 **이름에서부터** 갈린다

 L976  name = isRSCRequest ? `RSC ${method} ${route}` : `${method} ${route}`
 => APM 화면에서 같은 URL 의 문서 요청과 RSC 요청이 다른 줄로 뜬다
```

주석 둘이 이 껍데기가 왜 이렇게 생겼는지 말한다.

```ts
// base-server.ts L921-L927
        // Capture the parent span before creating the handleRequest span.
        // When deployed with an adapter, the platform's runtime may create its
        // own OTEL HTTP server span before Next.js runs. We propagate http.route
        // to this parent span so APM tools (e.g. Datadog) can derive the
        // resource name correctly.
        const parentSpan = tracer.getActiveScopeSpan()

```

```ts
// base-server.ts L1008-L1013
    const htmlRequestIdHeader = req.headers[NEXT_HTML_REQUEST_ID_HEADER]

    // The request root and route-matching spans start before App Render creates
    // its workStore. Carry their identity in this outer scope; App Render copies
    // it into the workStore so the complete timeline uses one request ID.
    return runWithRequestInsightsIdentity(
```

```text
 앞의 주석 - 어댑터로 배포하면 **플랫폼 런타임이 먼저** OTEL HTTP 서버 스팬을 만든다.
   그 부모 스팬에 http.route 를 올려 줘야 Datadog 같은 도구가 리소스 이름을 제대로 뽑는다
   => L992 가 그 일이다. 자기 스팬만 고치면 부족하다

 뒤의 주석 - 요청 루트와 라우트 매칭 스팬은 App Render 가 workStore 를 만들기 **전에** 시작한다.
   정체를 바깥 스코프에 담아 두면 App Render 가 그것을 workStore 로 복사해
   타임라인 전체가 한 요청 ID 를 쓴다
```

## prepare 는 추적 껍데기가 아니다

`handleRequest` 안의 다른 것들과 달리 `prepare` 는 스팬을 열지 않는다. 걸쇠다.

```ts
// base-server.ts L1781-L1796
  public async prepare(): Promise<void> {
    if (this.prepared) return

    // Get instrumentation module
    if (!this.instrumentation) {
      this.instrumentation = await this.loadInstrumentationModule()
    }
    if (this.preparedPromise === null) {
      this.preparedPromise = this.prepareImpl().then(() => {
        this.prepared = true
        this.preparedPromise = null
      })
    }
    return this.preparedPromise
  }
  protected async prepareImpl(): Promise<void> {}
```

```text
 L1782  this.prepared 이면                       => return       (두 번째부터)
 L1785  this.instrumentation 이 없으면
 L1786    this.instrumentation = await this.loadInstrumentationModule()
 L1788  this.preparedPromise 가 null 이면        (아직 아무도 시작 안 했으면)
 L1789    this.preparedPromise = this.prepareImpl().then(() => {
 L1790      this.prepared = true
 L1791      this.preparedPromise = null
 L1794  => return this.preparedPromise

 ★ **멱등 걸쇠**다. 여러 요청이 동시에 들어와도 prepareImpl 은 한 번만 돈다
   먼저 들어온 요청이 만든 약속을 뒤에 온 요청이 그대로 기다린다 (L1794)
 ★ 다만 실제로 처음 부르는 것은 요청이 아니라 **NEXTSRV L1296** 이다 (위 별항)
 ★ BASE 의 prepareImpl 은 L1796 `protected async prepareImpl(): Promise<void> {}`
   — **본문이 비어 있다.** 실제 준비는 하위 클래스가 채운다
```

## 결과가 쓰이는 곳

```text
 span (BaseServerSpan.handleRequest)
      --> 요청 하나의 루트 스팬. 아래 모든 스팬의 부모가 된다
      --> 이름이 확정되는 것은 [02]~[04] 가 라우트를 알아낸 **뒤**다

 normalizeReq / normalizeRes 로 감싼 req/res
      --> 이 흐름 전체가 이 두 객체를 들고 다닌다.
          addRequestMeta 로 붙는 상태도 여기에 쌓인다

 this.prepare() 가 끝났다는 사실
      --> 매니페스트·매처가 준비됐다. [02]의 matchers.waitTillReady 가 이어받는다
```

## 다루지 않는 것

`getTracer()` 와 `BaseServerSpan` 열거의 전체 목록, `withPropagatedContext` 가 `traceparent` 헤더를 읽는 방식, `isRequestInsightsEnabled` / `runWithRequestInsightsIdentity` 의 구현과 Request Insights 기능 자체, `NEXTSRV L1271-1276` 의 `experimentalTestProxy` 갈래, `normalizeReq` / `normalizeRes` 가 씌우는 `NodeNextRequest` / `NodeNextResponse` 의 인터페이스, `NEXTSRV` 가 채우는 `prepareImpl` 의 본문은 이 문서의 범위 밖이다.
