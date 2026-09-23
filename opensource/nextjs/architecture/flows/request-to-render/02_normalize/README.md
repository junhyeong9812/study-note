# 02 정규화 파이프라인

상위: [요청이 들어와서 렌더로 가기까지](../README.md)

`handleRequestImpl` 은 670줄짜리 메서드 하나다. 라우팅을 하지 않는다. **라우팅을 할 수 있는 모양으로 요청을 다듬는다.**

## 위치

`packages/next` / `src/server` / `base-server.ts` L1026-L1695 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1026-L1695))

## 실제 코드

들머리에서 매처를 기다린다.

```ts
// base-server.ts L1032-L1040
      // Wait for the matchers to be ready.
      await this.matchers.waitTillReady()

      // ensure cookies set in middleware are merged and
      // not overridden by API routes/getServerSideProps
      patchSetHeaderWithCookieSupport(
        req,
        isNodeNextResponse(res) ? res.originalResponse : res
      )
```

## 동작 흐름

```text
 handleRequestImpl  BASE L1026-1695 (670줄) — 나가는 길이 **스물**이다
                    return 13 · throw 6 · 아래로 떨어지며 500 내기 1
                    아래 [출구 n]은 **return 만** 센 번호다
                    ([03]이 return 3·4·5·6 과 throw 하나(L1506)를 가져간다)

 L1031  try {
 L1033    await this.matchers.waitTillReady()
 L1037    patchSetHeaderWithCookieSupport(req, ...)
            주석 L1035-1036 - 미들웨어가 심은 쿠키가 API 라우트·
              getServerSideProps 에 덮이지 않고 **합쳐지도록** 한다

 --- URL 다듬기 ---
 L1042    urlParts = (req.url || '').split('?', 1)
 L1049    urlNoQuery 가 `\` 나 `//` 를 가지면
 L1051      res.redirect(normalizeRepeatedSlashes(req.url), 308).body(...).send()
 L1052                                                    => return   [출구 1]
 L1056    parsedUrl 이 없거나 객체가 아니면
 L1058      req.url 도 없으면  => throw 'Invariant: url can not be undefined'
 L1061      parsedUrl = parseUrl(req.url)
 L1064    parsedUrl.pathname 이 없으면
 L1065                       => throw "Invariant: pathname can't be empty"
 L1069    parsedUrl.query 가 문자열이면 URLSearchParams 로 직접 판다

 --- 프록시 헤더 ---
 L1076    originalRequest = isNodeNextRequest(req) ? req : {}
 L1078    isHttps = x-forwarded-proto 가 있으면 그것이 'https' 인지,
                   없으면 소켓의 encrypted 인지
 L1082    x-forwarded-host  ??= host ?? this.hostname
 L1083    x-forwarded-port  ??= this.port ?? (isHttps ? '443' : '80')
 L1088    x-forwarded-proto ??= isHttps ? 'https' : 'http'
 L1089    x-forwarded-for   ??= socket.remoteAddress
          ★ 전부 `??=` 다. **이미 있으면 건드리지 않는다**
 L1093    this.attachRequestMeta(req, parsedUrl)        (abstract — 하위가 채운다)
            주석 L1091-1092 - 경로가 정규화되기 **전에** 해야 한다. 최초 URL 을 담는 일이다

 L1095    finished = await this.handleRSCRequest(req, res, parsedUrl)
 L1096    finished 이면                                 => return   [출구 2 — 죽었다]

 --- i18n ---
 L1098    domainLocale = this.i18nProvider?.detectDomainLocale(...)
 L1102    defaultLocale = domainLocale?.defaultLocale || nextConfig.i18n?.defaultLocale
 L1106    url = parseUrlUtil(req.url.replace(/^\/+/, '/'))
 L1107    pathnameInfo = getNextPathnameInfo(url.pathname, {...})
 L1113    pathnameInfo.basePath 이 있으면 req.url 에서 떼어낸다

 L1121    ★ useMatchedPathHeader 이면 388줄 블록            [03] 으로
 L1510    addRequestMeta(req, 'isLocaleDomain', Boolean(domainLocale))
 L1512    pathnameInfo.locale 이 있으면 req.url 을 다시 쓰고 didStripLocale 표시
 L1519    !minimalMode 이거나 locale 메타가 없으면 locale 을 메타에 넣는다

 --- 요청에 캐시를 붙인다 ---
 L1535    webServerConfig 가 없고 incrementalCache 메타도 없으면
 L1539      incrementalCache = await this.getIncrementalCache({...})
 L1544      addRequestMeta(req, 'incrementalCache', incrementalCache)
 L1547      ;(globalThis as any).__incrementalCache = incrementalCache
 L1552    serverComponentsHmrCache 메타가 없으면 붙인다
 L1566    hmrRefreshHash 메타가 없으면 붙인다

 --- 갈래 둘 ---
 L1577    invokePath = getRequestMeta(req, 'invokePath')
 L1578    useInvokePath = **!useMatchedPathHeader** && invokePath
          ★★ [03] 블록을 탔으면 이 갈래는 **절대 안 탄다.** 둘은 배타다
 L1580    ★ useInvokePath 이면 (L1580-1636)
 L1582      invokeStatus 가 있으면
 L1592        => return this.renderError(err, req, res, '/_error', ...)   [출구 7]
 L1595      invokePath 를 파싱해 parsedUrl.pathname 을 바꾼다
 L1622      parsedUrl.query 를 **전부 지우고** invokeQuery 로 갈아끼운다
 L1631      finished = await this.normalizeAndAttachMetadata(...)
 L1632      finished 이면                               => return   [출구 8]
 L1634      await this.handleCatchallRenderRequest(req, res, parsedUrl)
 L1635                                                  => return   [출구 9]
            ★★ **run 을 거치지 않는다.** [04]를 건너뛰고 곧장 하위 클래스로 간다

 L1638    ★ middlewareInvoke 메타가 있으면 (L1638-1659)
 L1639      finished = normalizeAndAttachMetadata     finished 이면 => return [출구 10]
 L1642      finished = await this.handleCatchallMiddlewareRequest(...)
 L1647      finished 이면                               => return   [출구 11]
 L1649      err = new Error(); err.result = {response: 'x-middleware-next: 1'}
 L1657      err.bubble = true
 L1658                                                  => throw err
            ★ 미들웨어가 "다음으로 넘겨라" 라고 답하는 것을 **예외로 전달한다**

 --- 정상 ---
 L1665    !useMatchedPathHeader 이고 basePath 이 있으면 떼어낸다
 L1672    res.statusCode = 200
 L1673    => return await this.run(req, res, parsedUrl)             [출구 12 — 정상]
          ★★ 정상 갈래는 **normalizeAndAttachMetadata 를 거치지 않는다**

 L1674  } catch (err) {
 L1675    NoFallbackError 이면                          => throw     (위로 올린다)
 L1679    ERR_INVALID_URL / DecodeError / NormalizeError 이면
 L1684      res.statusCode = 400
 L1685      => return this.renderError(null, req, res, '/_error', {})  [출구 13]
 L1688    minimalMode 이거나 dev 이거나 err.bubble 이면 => throw
 L1691    this.logError(getProperError(err))
 L1692    res.statusCode = 500
 L1693    res.body('Internal Server Error').send()
```

```text
 ★★★ 출구 2(L1096)는 **도달할 수 없다**

 handleRSCRequest  BASE L652-722 의 return 을 전수로 세면 다섯이다
   L657  L663  L693  L712  L721
 다섯이 **전부 false 다.** `return true` 가 하나도 없다

 => L1095 의 finished 는 언제나 false 다. L1096 은 죽은 줄이다

 ★★ 게다가 **앞 두 갈래는 일반 서버에서 진입조차 못 한다**
   L552  rsc: enabledDirectories.app && this.minimalMode ? new RSCPathnameNormalizer() : undefined
   L555  segmentPrefetchRSC: this.minimalMode ? new SegmentPrefixRSCPathnameNormalizer() : undefined
   => 노멀라이저가 undefined 라 L659 / L676 갈래는 **minimalMode 전용**이다
   => 일반 서버가 실제로 닿는 것은 L685(x-now-route-matches) · L694(RSC 헤더) ·
      L710(그 외) 셋뿐이다. [03]만 서버리스 전용인 게 아니다
 => 이름이 handle* 이고 타입이 RouteHandler("내가 응답을 끝냈다" 를 boolean 으로 말하는 계약)인데
    **아무것도 끝내지 않는다.** 요청 메타에 표시만 하고 돌아온다
```

```ts
// base-server.ts L1093-L1096
      this.attachRequestMeta(req, parsedUrl)

      let finished = await this.handleRSCRequest(req, res, parsedUrl)
      if (finished) return
```

```text
 ★★ 슬래시 정규화는 보안 검사가 아니다 (L1049)

 주석 L1045-1048
   "this normalizes repeated slashes in the path e.g. hello//world ->
    hello/world or backslashes to forward slashes, this does not
    handle trailing slash as that is handled the same as a next.config.js redirect"

 => 하는 일은 `\` 를 `/` 로, `//` 를 `/` 로 바꾸고 **308 로 넘기는 것**이다.
    거절이 아니라 옮기기다. 끝 슬래시는 여기서 안 다룬다 — 그것은 리다이렉트 설정의 몫
```

```text
 ★★ 진짜 보안 주의가 있는 자리는 invokePath 다 (L1574-1576)

   "when invokePath is specified we can short short circuit resolving
    we only honor this header if we are inside of a render worker to
    prevent external users coercing the routing path"

 => 이 헤더를 믿으면 요청자가 **어느 페이지를 렌더할지 직접 고를 수 있다**.
    그래서 렌더 워커 안에서만 인정한다
 ※ "렌더 워커 안" 을 실제로 판별하는 코드는 이 메서드에 없다.
    invokePath 메타를 누가 심는지를 따라가야 한다 — 이 문서의 범위 밖이다
```

```text
 ★★★ 그래서 handleNextImageRequest 는 이 흐름의 정상 경로에서 **영원히 안 불린다**

 normalizeAndAttachMetadata(BASE L1730)의 본문
   L1734  finished = await this.handleNextImageRequest(req, res, url)
   L1735  finished 이면 => return true
   L1737  pages 디렉터리가 있으면 handleNextDataRequest

 이것을 부르는 곳은 **셋뿐**이다
   L1499  [03] 안        L1631  invoke 갈래      L1639  middleware 갈래
 => 정상 갈래(L1673)에는 없다.
    [README]가 확장점 (나) 셋 중 하나로 올린 handleNextImageRequest 는
    **이 흐름의 정상 경로에서 도달 불가**다. 이미지는 다른 길로 서빙된다
 ★ handleNextDataRequest(L724-813)는 true 셋(L742·L753·L805)과
   false 셋(L731·L737·L812)을 섞어 쓴다 —
   RouteHandler 계약("내가 끝냈으면 true")을 **제대로 지키는** 쪽의 예다
```

```ts
// base-server.ts L1535-L1548
      if (
        !(this.serverOptions as any).webServerConfig &&
        !getRequestMeta(req, 'incrementalCache')
      ) {
        const incrementalCache = await this.getIncrementalCache({
          requestHeaders: Object.assign({}, req.headers),
        })

        incrementalCache.resetRequestCache()
        addRequestMeta(req, 'incrementalCache', incrementalCache)
        // This is needed for pages router to leverage unstable_cache
        // TODO: re-work this handling to not use global and use a AsyncStore
        ;(globalThis as any).__incrementalCache = incrementalCache
      }
```

```text
 ★ 전역 변수가 하나 있다 (L1547)

   ;(globalThis as any).__incrementalCache = incrementalCache
   주석 L1545-1546 - "This is needed for pages router to leverage unstable_cache
                      TODO: re-work this handling to not use global and use a AsyncStore"

 => Pages Router 의 unstable_cache 가 요청 메타에 닿을 길이 없어서
    전역을 쓴다. 소스가 스스로 TODO 로 남겨 놓았다
```

## 결과가 쓰이는 곳

```text
 parsedUrl.pathname / .query
      --> [04]의 handleCatchallRenderRequest 가 이것으로 라우트를 고른다

 요청 메타 (이 메서드가 붙인 것)
      defaultLocale · locale · localeInferredFromDefault · didStripLocale
      isLocaleDomain · incrementalCache · serverComponentsHmrCache · hmrRefreshHash
      --> 렌더 끝까지 따라간다

 x-forwarded-* 네 헤더
      --> 리버스 프록시 뒤에서도 원래 호스트·포트·프로토콜·클라이언트 IP 를 알 수 있게 한다

 globalThis.__incrementalCache
      --> Pages Router 의 unstable_cache
```

## 다루지 않는 것

`useMatchedPathHeader` 블록(L1121-1508)의 본문([03]에 있다), `handleRSCRequest`(L652-722)가 요청 메타에 실제로 무엇을 심는지, `normalizeAndAttachMetadata`(L1730)와 `normalize`(L1704)의 본문, `this.normalizers` 표(L445)와 각 노멀라이저, `attachRequestMeta`(L382, abstract)를 하위 클래스가 채우는 방식, `patchSetHeaderWithCookieSupport` 의 구현, `getIncrementalCache`(L414, abstract)와 증분 캐시 자체, `invokePath` / `middlewareInvoke` 메타를 누가 심는지, `handleCatchallMiddlewareRequest`(L825)의 미들웨어 실행은 이 문서의 범위 밖이다.
