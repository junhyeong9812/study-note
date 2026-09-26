# 03 웹소켓 업그레이드

상위: [페이지가 아닌 요청이 처리되기까지](../README.md)

HTTP `Upgrade` 요청(웹소켓)은 base-server 에 `handleUpgrade` 라는 abstract 메서드로 자리가 잡혀 있다. 그런데 그 유일한 구현은 **본문이 비어 있고**, `next start` 의 실제 업그레이드 처리는 router-server 에 따로 있다. 이 문서는 그 두 길을 가른다.

## 위치

`packages/next` / `src/server` / `base-server.ts` L1765-L1769 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1765-L1769))

`packages/next` / `src/server` / `next-server.ts` L348-L351 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/next-server.ts#L348-L351))

`packages/next` / `src/server/lib` / `router-server.ts` L908-L1013 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/lib/router-server.ts#L908-L1013))

## 실제 코드

abstract 를 채우는 구현 전부다.

```ts
// next-server.ts L348-L351
  protected async handleUpgrade(): Promise<void> {
    // The web server does not support web sockets, it's only used for HMR in
    // development.
  }
```

```text
 ★★★ 구현이 **주석 두 줄**이다

 BASE L1765  protected abstract handleUpgrade(req, socket, head?): Promise<void>
   +-- NEXTSRV L348  본문 없음
         "The web server does not support web sockets, it's only used for HMR in development."
   +-- DEV (next-dev-server.ts)  **덮어쓰지 않는다** — grep 으로 handleUpgrade 가 안 나온다

 => [요청 흐름] README 가 센 abstract 21개 중 하나지만,
    채우는 쪽은 "지원하지 않는다" 를 빈 본문으로 말한다
 ★ 주석의 "web server" 는 [요청 흐름] 05 가 본 `NextWebServer`(지금은 없음)를 가리키는 것으로 보인다
   (※ 내 해석이다. 이 파일은 NextNodeServer 다)
 ★ HMR 도 이 메서드를 거치지 않는다 — 아래 ③
```

## 동작 흐름

```text
 handleUpgrade 를 부르는 자리를 저장소 전체에서 grep 했다 (packages/next/src)

   server/next.ts L246           server.handleUpgrade.apply(server, [req, socket, head])
   server/dev/hot-reloader-webpack.ts L456     wsServer.handleUpgrade(...)   ← 다른 것
   server/dev/hot-reloader-turbopack.ts L1385  wsServer.handleUpgrade(...)   ← 다른 것

 => 뒤의 둘은 `ws` 라이브러리의 `WebSocket.Server#handleUpgrade` 다 (이름만 같다).
    base-server 의 handleUpgrade 를 부르는 곳은 **next.ts L246 하나**다
```

```ts
// next.ts L241-L248
  getUpgradeHandler(): UpgradeHandler {
    return async (req: IncomingMessage, socket: any, head: any) => {
      const server = await this.getServer()
      // @ts-expect-error we mark this as protected so it
      // causes an error here
      return server.handleUpgrade.apply(server, [req, socket, head])
    }
  }
```

```text
 ① NextServer.getUpgradeHandler — handleUpgrade 로 가는 유일한 길

 L243  server = await this.getServer()          NextNodeServer (dev 면 DevServer)
 L246  return server.handleUpgrade.apply(...)   => NEXTSRV L348 — 아무것도 안 한다
         주석 L244-245 - protected 라서 타입 오류를 @ts-expect-error 로 누른다

 이 핸들러를 받아 가는 곳
   render-server.ts L172 · L175   upgradeHandler = server.getUpgradeHandler()
     => initialize 결과 { requestHandler, upgradeHandler, server, ... } 에 담긴다 (L180-182)
   next.ts L565-567  NextCustomServer.getUpgradeHandler() => this.server.getUpgradeHandler()

 그런데 render-server 결과의 `.upgradeHandler` 를 읽는 곳이 **없다**
   `.upgradeHandler` 를 grep 하면 세 곳이다
     next.ts L451          NextCustomServer 의 getter — getInit() 은 router-server 의 결과다
     next.ts L501          this.upgradeHandler(req, socket, head) — 위 getter 를 부른다
     start-server.ts L499  initResult.upgradeHandler  — 이것도 router-server 의 결과다
   router-server 는 render server 에서 `handlers.server` 와 `requestHandler` 를 가져다 쓴다
   (RSRV L862-867 · L1018 · L419-422 · RROUTES L582-606). upgradeHandler 는 읽지 않는다
 => render-server 가 만든 upgradeHandler 는 **만들어지고 버려진다**
```

```text
 ② 실제 길 — next start  STARTSRV L286-294 -> RSRV L908-1013

 STARTSRV L286  server.on('upgrade', async (req, socket, head) => {
 L288             await upgradeHandler(req, socket, head)       ← router-server 의 것 (L499)
 L289           } catch — socket.destroy() + 'Failed to handle request for ...'

 RSRV upgradeHandler L908
 L910-917  req · socket 의 'error' 를 삼킨다 (TODO: log socket errors?)
 L919      dev 이고 development 가 있으면
 L920        blockCrossSiteDEV 에 걸리면                          => return
 L932-944    hmrPrefix = basePath, assetPrefix 가 있으면 그것 (URL 이면 pathname 만)
 L946        req.url 이 `${hmrPrefix}/_next/hmr` 로 시작하면
 L953          => return development.bundler.hotReloader.onHMR(req, socket, head, ...)   ③
 L978      res = new MockedResponse({ resWriter: () => { throw 'Invariant: did not expect
                                       response writer to be written to for upgrade request' } })
 L985      { finished, matchedOutput, parsedUrl, statusCode } = await resolveRoutes({
             req, res, isUpgradeReq: true, signal: signalFromNodeResponse(socket) })
 L995      matchedOutput 이 있으면 (페이지·파일에 맞았으면)        => return socket.end()
 L999      finished 이고 parsedUrl.protocol 이 있으면 (외부 rewrite)
 L1000       statusCode 가 없으면                               => return proxyRequest(req, socket, parsedUrl, head)
 L1004       있으면                                             => return socket.end()
 L1007     (그 밖 — 아무것도 안 하고 끝난다)
 L1009     catch — console.error('Error handling upgrade request') + socket.end()
```

```ts
// router-server.ts L993-L1008
      // TODO: allow upgrade requests to pages/app paths?
      // this was not previously supported
      if (matchedOutput) {
        return socket.end()
      }

      if (finished && parsedUrl.protocol) {
        if (!statusCode) {
          return await proxyRequest(req, socket, parsedUrl, head)
        }

        return socket.end()
      }

      // If there's no matched output, we don't handle the request as user's
      // custom WS server may be listening on the same path.
```

```text
 ★★★ Next 가 안 받는 업그레이드는 **닫지도 않는다**

 주석 L1007-1008
   "If there's no matched output, we don't handle the request as user's
    custom WS server may be listening on the same path."

 => 페이지·파일에 맞으면 끊고(L995), 외부 rewrite 면 넘기고(L1001),
    **어디에도 안 맞으면 소켓을 그대로 둔다.** — 안 맞을 때만이 아니다. 내부 config redirect,
    미들웨어 redirect·본문 응답도 `finished` + protocol 없는 statusCode 라 L995 · L999 를 모두
    빠져나가 **응답 없이 방치된다** (RSRV L995-1008 · RROUTES L773-800 · L826-831). 같은 http 서버에 사용자가 붙인
    다른 'upgrade' 리스너가 받을 수 있게 하려는 것이다
 ★ 주석 L993-994 - "TODO: allow upgrade requests to pages/app paths?
   this was not previously supported"
   => 라우트 핸들러로 웹소켓을 받는 길은 **없다.** 맞으면 socket.end() 다
 ★ 외부 rewrite 로 넘길 때만 proxy-request.ts L105-116 이 `proxy.ws(...)` 로 웹소켓을 잇는다
```

```text
 ★★ resolveRoutes 에서 isUpgradeReq 가 바꾸는 것은 **한 가지**다

 RROUTES 에서 isUpgradeReq 를 grep 하면 세 줄 — L121 · L126(인자 선언)과 L186
   L186  if (!isUpgradeReq) { addRequestMeta(req, 'clonableBody', getCloneableBody(req, ...)) }
 => 본문 복제만 건너뛴다. 라우트 목록은 **같은 것을 그대로 돈다**
 => headers · redirects · rewrites 규칙이 업그레이드에도 적용된다.
    그래서 외부 rewrite(L999)가 웹소켓 프록시의 근거가 된다
 ※ 미들웨어 칸(RROUTES L558)도 isUpgradeReq 를 보지 않는다. 업그레이드 요청이
   matcher 에 맞으면 [01] 의 render server 호출이 MockedResponse 를 들고 일어날 것으로 보인다.
   그때 무엇이 쓰이는지는 실행해 보지 않았다 (내 추론이다)
```

```text
 ③ HMR — 개발 서버의 웹소켓

 RSRV L953  development.bundler.hotReloader.onHMR(req, socket, head, callback)
   webpack    hot-reloader-webpack.ts L447   wsServer.handleUpgrade(req, **req.socket**, head, ...)  L456
   Turbopack  hot-reloader-turbopack.ts L1384 wsServer.handleUpgrade(req, **socket**, head, ...)     L1385
   두 파일 모두 `new ws.Server({ noServer: true })` (webpack L128 · Turbopack L153)

 ★ webpack 쪽은 받은 소켓 인자 이름이 `_socket` 이고 **쓰지 않는다** — req.socket 을 쓴다
 ★ 연결되면 RSRV L957-973 콜백이 **레거시 클라이언트에게만** ISR 매니페스트를 보낸다
   주석 L959-965 - Pages Router 이거나 Cache Components 를 끈 App Router 클라이언트다.
     ISR 매니페스트는 정적 표시기(static indicator)에만 쓰이는데 Cache Components 에서는
     부분 정적 페이지를 표시하지 못해 쓸모가 없다고 적는다
```

```text
 ★★ 커스텀 서버에서는 업그레이드 리스너가 **첫 HTTP 요청 때** 붙는다

 NEXTWRAP NextCustomServer
   L491  setupWebSocketHandler(customServer?, _req?)
   L495    didWebSocketSetup 이 아니면 한 번만
   L497    customServer = customServer || _req?.socket?.server
   L500    customServer.on('upgrade', async (req, socket, head) => {
   L501      this.upgradeHandler(req, socket, head)       ← router-server 의 것. await · catch 없음
   부르는 자리는 둘 — L513 getRequestHandler 가 **돌려주는 함수 안**, L526 render()
 => 리스너를 붙이는 계기가 요청 처리다. prepare() 는 붙이지 않는다
 ※ 그래서 서버가 뜬 뒤 HTTP 요청이 한 번도 오기 전의 업그레이드는 Next 가 받지 못하는 것으로 보인다
   (내 추론이다. start-server 는 L286 에서 서버를 만들 때 바로 붙이고, 핸들러가 준비되기 전에 온
    업그레이드는 L219-229 의 임시 핸들러가 handlersPromise 를 기다렸다 넘긴다)
 ★ start-server L287-293 은 try/catch 로 socket.destroy() 하는데
   커스텀 서버 쪽 L500-502 는 await 도 catch 도 없다

 ★★★ 그리고 커스텀 서버의 공개 메서드 getUpgradeHandler() 는 **다른 것**을 돌려준다
   L565-567  getUpgradeHandler() { return this.server.getUpgradeHandler() }
     this.server = getInit().server = router-server 결과의 server (RSRV L1018 handlers.server)
                 = render-server 가 만든 NextServer
     => NextServer.getUpgradeHandler (L241) => NEXTSRV handleUpgrade => **빈 본문**
 => 자동으로 붙는 리스너(L501)는 router-server 의 upgradeHandler 를 쓰는데,
    사용자가 `app.getUpgradeHandler()` 로 받아 직접 붙이면 아무것도 안 하는 함수를 받는다
 ※ 위 두 줄의 "=" 사슬은 각 파일에서 따로 확인했다. 실제로 호출해 보지는 않았다
```

## 결과가 쓰이는 곳

```text
 proxyRequest(req, socket, parsedUrl, head)
      --> http-proxy 의 ws 로 외부 목적지에 웹소켓을 잇는다 (proxy-request.ts L105-116)

 socket.end()
      --> 페이지·파일에 맞은 업그레이드, 상태 코드가 붙은 외부 rewrite, 예외 — 셋 다 닫힌다

 (아무것도 안 함)
      --> 같은 http 서버의 다른 'upgrade' 리스너 몫 (RSRV L1007-1008)

 hotReloader.onHMR 의 ws 클라이언트
      --> 개발 서버가 브라우저로 메시지를 밀어 보내는 통로. 그 첫 메시지가 위 ISR_MANIFEST 다
          ※ 메시지를 받는 브라우저 쪽 코드는 읽지 않았다

 NextNodeServer.handleUpgrade
      --> 쓰이지 않는다. render-server 의 결과로 만들어져 버려지거나(①),
          커스텀 서버의 getUpgradeHandler() 로 사용자에게 건네진다
```

## 다루지 않는 것

`proxyRequest`(`server/lib/router-utils/proxy-request.ts`)의 http-proxy 설정과 타임아웃, `blockCrossSiteDEV` 의 교차 출처 판정과 `allowedDevOrigins`, 핫 리로더의 웹소켓 메시지 형식(`HMR_MESSAGE_SENT_TO_BROWSER`)과 onHMR 이 클라이언트를 붙인 뒤의 처리(hot-reloader-webpack.ts L456 이후 · hot-reloader-turbopack.ts L1385 이후), `MockedResponse`(`server/lib/mock-request.ts`)의 구현, `signalFromNodeResponse`, `closeUpgraded` 가 개발 서버 종료 때 업그레이드된 연결을 닫는 방식(render-server.ts L17), `resolveRoutes` 의 라우트 목록 처리 본문, 그리고 Turbopack 핫 리로더의 구독(subscriptions) 관리는 이 문서의 범위 밖이다.
