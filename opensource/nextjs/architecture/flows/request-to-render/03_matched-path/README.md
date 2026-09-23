# 03 x-matched-path 블록

상위: [요청이 들어와서 렌더로 가기까지](../README.md)

[02]의 한가운데에 388줄짜리 `if` 블록이 하나 있다. **서버리스에서만 돈다.** 일반 서버는 통째로 건너뛴다.

## 위치

`packages/next` / `src/server` / `base-server.ts` L1117-L1508 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/base-server.ts#L1117-L1508))

## 실제 코드

들어갈지 말지가 두 줄로 결정된다.

```ts
// base-server.ts L1117-L1118
      const useMatchedPathHeader =
        this.minimalMode && typeof req.headers[MATCHED_PATH_HEADER] === 'string'
```

블록의 존재 이유는 안쪽 주석이 말한다.

```ts
// base-server.ts L1133-L1138
          // x-matched-path is the source of truth, it tells what page
          // should be rendered because we don't process rewrites in minimalMode
          let { pathname: matchedPath } = new URL(
            fixMojibake(req.headers[MATCHED_PATH_HEADER] as string),
            'http://localhost'
          )
```

```text
 "x-matched-path is the source of truth, it tells what page
  should be rendered because we don't process rewrites in minimalMode"

 => minimalMode 는 rewrite 를 **처리하지 않는다**. 플랫폼(어댑터)이 먼저 처리했다.
    그 결과가 헤더로 온다. 이 블록은 그 헤더를 받아
    **일반 서버가 라우팅으로 만들었을 상태를 되짚어 복원한다**
```

## 동작 흐름

```text
 BASE L1121-1508 — 진입 조건은 minimalMode && x-matched-path 헤더가 문자열

 L1122  try {
 L1123    app 디렉터리가 켜져 있으면
 L1126      req.url 이 /index 로 시작하면 / 로 바꾼다
 L1129      parsedUrl.pathname 이 '/index' 면 '/' 로
             주석 L1124-1125 - minimal 모드의 프리렌더를 위해 /index 를 정규화한다

 L1135    matchedPath = new URL(fixMojibake(헤더), 'http://localhost').pathname
 L1140    urlPathname = new URL(req.url, 'http://localhost').pathname
 L1145    normalizers.data 가 urlPathname 에 맞으면
 L1146      addRequestMeta(req, 'isNextDataReq', true)
             주석 L1142-1144 - ISR 은 URL 이 prerenderPath 로 정규화된다.
               데이터 요청이면 URL 경로가 곧 데이터 URL 이다

 --- PPR 재개 ---
 L1151    isAppPPREnabled && minimalMode && NEXT_RESUME_HEADER === '1' && POST 이면
          (lib/constants.ts L29  NEXT_RESUME_HEADER = 'next-resume')
 L1157      {maxPostponedStateSize, maxPostponedStateSizeBytes} = getMaxPostponedStateSize(...)
 L1165      body = await readBodyWithSizeLimit(req.body, maxPostponedStateSizeBytes)
 L1169      body 가 null 이면 (한도 초과)
 L1170        res.statusCode = 413
 L1171        res.body(getPostponedStateExceededErrorMessage(...)).send()
 L1176                                                => return   [출구 3]
 L1180      addRequestMeta(req, 'postponed', body.toString('utf8'))

 L1185    isNextDataReq 이고 postponed 도 문자열이면
 L1194      res.statusCode = 422
 L1196                                                => return   [출구 4]
             주석 L1189-1193 - 헤더는 PPR 재개라고 말하는데 URL 은 Pages Router 의
               데이터 라우트를 가리킨다. **모순이라 처리할 수 없는 요청**이다

 --- 경로·로케일 ---
 L1199    matchedPath = this.normalize(matchedPath)
 L1200    normalizedUrlPath = this.stripNextDataPath(urlPathname)
 L1202    matchedPath = denormalizePagePath(matchedPath)
 L1205    localeAnalysisResult = this.i18nProvider?.analyze(matchedPath, {defaultLocale})
 L1212    결과가 있으면
 L1213      addRequestMeta(req, 'locale', detectedLocale)
 L1217      기본 로케일에서 추론된 것이면 localeInferredFromDefault 도 심는다
 L1220      아니면 그 표시를 **지운다** (removeRequestMeta)

 --- 매칭 ---
 L1224    srcPathname = matchedPath
 L1225    pageIsDynamic = isDynamicRoute(srcPathname)
 L1226    paramsResult = {params: false, hasValidParams: false}
 L1234    match = await this.matchers.match(srcPathname, {i18n: localeAnalysisResult})
 L1238    정적으로 보였는데 match 가 있으면
 L1240      srcPathname = match.definition.pathname
 L1245      match.params 가 있으면 pageIsDynamic = true 로 **뒤집는다**
             주석 L1242-1244 - 파라미터가 파싱됐다면 이 단계에서 정적 페이지가 아님을 안다
 L1255    localeAnalysisResult 가 있으면 matchedPath 를 로케일 뗀 것으로 되돌린다
             주석 L1252-1254 - 이 함수의 나머지는 i18n 을 제대로 못 다룬다

 --- rewrite 를 여기서 다시 돌린다 ---
 L1259    utils = getServerUtils({pageIsDynamic, page: srcPathname, i18n, basePath,
                                  rewrites: this.getRoutesManifest()?.rewrites || {...},
                                  caseSensitive})
 L1274    defaultLocale 이 있고 pathnameInfo.locale 이 없으면 경로 앞에 로케일을 붙인다
             주석 L1272-1273 - rewrite 를 처리하기 전에 붙여야 제대로 맞는다
 L1280    originQueryParams = {...parsedUrl.query}        (handleRewrites 전 사본)
 L1283    {rewriteParams, rewrittenParsedUrl} = utils.handleRewrites(req, parsedUrl)
 L1293    didRewrite = 경로가 바뀌었는가
 L1296    바뀌었으면 addRequestMeta(req, 'rewrittenPathname', ...)

 L1305    parsedUrl.query 를 돌며
 L1306      normalizeNextQueryParam(key) 가 있으면 (nxtP 접두)
 L1311        원래 키를 지우고 routeParamKeys 에 정규화된 이름을 넣는다
 L1317        값을 decodeQueryPathParameter 로 푼다

 L1322    ★★★ pageIsDynamic 이면 파라미터를 **일곱 번** 찾는다 (아래 별항)
 L1469    pageIsDynamic 이거나 didRewrite 이면 utils.normalizeCdnUrl(req, [...])
 L1479    routeParamKeys 중 원래 쿼리에 없던 것은 parsedUrl.query 에서 지운다
 L1485    parsedUrl.pathname = matchedPath       ★ 여기서 경로가 확정된다
 L1486    url.pathname = parsedUrl.pathname
 L1492    match 가 PAGES / PAGES_API 면 parsedUrl.query = rewrittenQueryParams
             주석 L1488-1491 - Pages 는 catch-all 이 배열 값을 제대로 받아야 한다.
               App Router 는 rewrite 쿼리를 넣으면 **RSC 페이로드가 달라진다**

 L1499    finished = await this.normalizeAndAttachMetadata(req, res, parsedUrl)
 L1500    finished 이면                          => return   [출구 5]
 L1501  } catch (err) {
 L1502    DecodeError / NormalizeError 이면
 L1503      res.statusCode = 400
 L1504      => return this.renderError(null, req, res, '/_error', {})   [출구 6]
 L1506    아니면                                 => throw
```

```text
 ★★★ 머리기사 — 동적 파라미터를 알아내려고 **일곱 번** 시도한다 (L1322-1436)

 뒤의 여섯이 `!paramsResult.hasValidParams` 를 달고 있어 앞이 성공하면 건너뛴다.
 다만 **그것 하나로만 묶여 있지는 않다** — 시도마다 자기 조건이 더 붙는다

   1  L1245  match.params                              매처가 이미 뽑아 준 것
   2  L1328  normalizeDynamicRouteParams(rewrittenQueryParams, false)
   3  L1342  utils.dynamicRouteMatcher(normalizedUrlPath)      URL 에서 직접
   4  L1364  utils.dynamicRouteMatcher(matchedPath)            매치된 경로에서
   5  L1390  x-now-route-matches 헤더                          플랫폼이 준 것
   6  L1408  normalizeDynamicRouteParams(rewrittenQueryParams, true)
   7  L1426  utils.defaultRouteMatches                         최후

 ★ 2번과 6번은 **같은 함수**다. 둘째 인자만 false -> true 로 바뀐다.
   분기가 인자로 옮겨갔다 — 주석 L1405-1406
   "Try to parse the params from the query if we couldn't parse them
    from the route matches but ignore missing optional params."
   => true 는 "빠진 선택 파라미터를 눈감아 준다" 는 뜻이다

 => 서버리스에서는 파라미터의 출처가 하나가 아니다.
    일곱 갈래로 흩어진 단서를 순서대로 훑는다
```

각 시도가 왜 필요한지를 소스가 주석으로 남겨 놓았다.

```ts
// base-server.ts L1334-L1349
            // for prerendered ISR paths we attempt parsing the route
            // params from the URL directly as route-matches may not
            // contain the correct values due to the filesystem path
            // matching before the dynamic route has been matched
            if (
              !paramsResult.hasValidParams &&
              !isDynamicRoute(normalizedUrlPath)
            ) {
              let matcherParams = utils.dynamicRouteMatcher?.(normalizedUrlPath)

              if (matcherParams) {
                utils.normalizeDynamicRouteParams(matcherParams, false)
                Object.assign(paramsResult.params, matcherParams)
                paramsResult.hasValidParams = true
              }
            }
```

```ts
// base-server.ts L1351-L1377
            // if an action request is bypassing a prerender and we
            // don't have the params in the URL since it was prerendered
            // and matched during handle: 'filesystem' rather than dynamic route
            // resolving we need to parse the params from the matched-path.
            // Note: this is similar to above case but from match-path instead
            // of from the request URL since a rewrite could cause that to not
            // match the src pathname
            if (
              // we can have a collision with /index and a top-level /[slug]
              matchedPath !== '/index' &&
              !paramsResult.hasValidParams &&
              !isDynamicRoute(matchedPath)
            ) {
              let matcherParams = utils.dynamicRouteMatcher?.(matchedPath)

              if (matcherParams) {
                const curParamsResult = utils.normalizeDynamicRouteParams(
                  matcherParams,
                  false
                )

                if (curParamsResult.hasValidParams) {
                  Object.assign(params, matcherParams)
                  paramsResult = curParamsResult
                }
              }
            }
```

```text
 ★ 7번(L1421-1436)에는 곁가지가 하나 붙어 있다

 L1433  routeMatchesHeader 가 **빈 문자열**이면
 L1434    addRequestMeta(req, 'renderFallbackShell', true)

 주석 L1428-1432
   "If the route matches header is an empty string, we want to
    render a fallback shell. This is because we know this came from
    a prerender (it has the header) but it's values were filtered
    out (because the allowQuery was empty). If it was undefined
    then we know that the request is hitting the lambda directly."

 => 헤더가 **없는 것**과 **비어 있는 것**이 다른 뜻이다
    없다 = 람다를 직접 때렸다 / 비었다 = 프리렌더를 거쳤는데 값이 걸러졌다
```

파라미터를 찾으면 경로에 끼워 넣는다.

```ts
// base-server.ts L1439-L1440
              matchedPath = utils.interpolateDynamicPath(srcPathname, params)
              req.url = utils.interpolateDynamicPath(req.url!, params)
```

```text
 L1439  matchedPath = utils.interpolateDynamicPath(srcPathname, params)
 L1440  req.url  = utils.interpolateDynamicPath(req.url, params)
 => `/blog/[slug]` 가 `/blog/hello` 가 된다. **경로와 req.url 둘 다** 고친다
 L1445-1465  세그먼트 프리페치 요청이면 그 경로에도 같은 보간을 하고
             헤더와 메타를 함께 갱신한다
```

```text
 ★ 헤더 글자가 깨져서 오는 일이 있다 — fixMojibake
```

```ts
// fix-mojibake.ts L1-L14
// x-matched-path header can be decoded incorrectly
// and should only be utf8 characters so this fixes
// incorrectly encoded values
export function fixMojibake(input: string): string {
  // Convert each character's char code to a byte
  const bytes = new Uint8Array(input.length)
  for (let i = 0; i < input.length; i++) {
    bytes[i] = input.charCodeAt(i)
  }

  // Decode the bytes as proper UTF-8
  const decoder = new TextDecoder('utf-8')
  return decoder.decode(bytes)
}
```

```text
 각 문자의 charCode 를 **바이트로 보고** 다시 UTF-8 로 디코드한다
 => latin1 로 잘못 읽힌 UTF-8 을 되돌린다. 한글 경로가 여기에 걸린다
```

## 결과가 쓰이는 곳

```text
 parsedUrl.pathname  (L1485 에서 확정)
      --> [02]의 나머지를 지나 [04]로 간다. 이 블록을 거쳤으면
          경로는 이미 **구체적인 값이 박힌 것**이다 (`/blog/hello`)

 요청 메타
      isNextDataReq · postponed · locale · localeInferredFromDefault
      rewrittenPathname · renderFallbackShell · segmentPrefetchRSCRequest
      --> postponed 는 PPR 재개에, renderFallbackShell 은 폴백 셸 렌더에 쓰인다

 정리된 parsedUrl.query
      --> 라우트 파라미터와 검색 파라미터가 갈린 상태. App Router 는
          rewrite 쿼리를 받지 않는다 (L1492 의 갈래)
```

## 다루지 않는 것

`getServerUtils` 가 돌려주는 `handleRewrites` · `normalizeDynamicRouteParams` · `dynamicRouteMatcher` · `interpolateDynamicPath` · `normalizeCdnUrl` · `defaultRouteMatches` 각각의 구현, `this.matchers.match` 의 매칭 규칙과 `RouteKind` 열거, `i18nProvider.analyze` 의 로케일 판별, PPR(`isAppPPREnabled`)과 postponed 상태의 형식·`readBodyWithSizeLimit`, `normalizers.data` / `stripNextDataPath` / `denormalizePagePath` 의 경로 규칙, `x-now-route-matches` 헤더를 플랫폼이 만드는 방식, `normalizeAndAttachMetadata`(L1730)의 본문은 이 문서의 범위 밖이다.
