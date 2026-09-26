# 03 흐름 제어 예외를 응답으로

상위: [서버 액션이 실행되기까지](../README.md)

`catch` 104줄이다. 액션 안에서 부른 `redirect()` 와 `notFound()` 가 여기서 응답이 된다. **fetch 액션과 MPA 액션의 결과가 전혀 다르다.**

## 위치

`packages/next` / `src/server/app-render` / `action-handler.ts` L1270-L1373 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/action-handler.ts#L1270-L1373))

## 실제 코드

같은 `redirect()` 가 두 가지 응답으로 갈린다.

```ts
// action-handler.ts L1275-L1300
      if (isFetchAction) {
        // Fetch actions communicate redirects through `x-action-redirect` and
        // can include the redirect target's Flight response in the body. Since
        // this is not an HTTP redirect, keep the response successful.
        res.statusCode = 200
        metadata.statusCode = 200

        return {
          type: 'done',
          result: await createRedirectRenderResult(
            req,
            res,
            host,
            redirectUrl,
            redirectType,
            ctx.renderOpts.basePath,
            workStore,
            requestStore.url.pathname
          ),
        }
      }

      // For an MPA action, the redirect doesn't need a body, just a Location header.
      res.statusCode = RedirectStatusCode.SeeOther
      metadata.statusCode = RedirectStatusCode.SeeOther
      res.setHeader('Location', redirectUrl)
```

```text
 fetch 액션   res.statusCode = **200**
              x-action-redirect 헤더로 알리고 본문에 목적지의 Flight 응답을 담는다
              주석 L1276-1278 - "Fetch actions communicate redirects through
                `x-action-redirect` and can include the redirect target's Flight
                response in the body. Since this is not an HTTP redirect,
                keep the response successful."

 MPA 액션     res.statusCode = **303 (SeeOther)**
              Location 헤더만 붙인다
              주석 L1297 - "For an MPA action, the redirect doesn't need a body,
                just a Location header."

 ★★★ fetch 액션의 리다이렉트는 **HTTP 리다이렉트가 아니다.**
   브라우저가 따라가는 것이 아니라 클라이언트 라우터가 해석한다.
   ※ "302 를 주면 브라우저 fetch 가 먼저 따라가 버린다" 는 내 추론이다.
     주석은 "HTTP 리다이렉트가 아니므로 성공 응답을 유지한다" 까지만 말한다
```

## 동작 흐름

```text
 catch (err)  ACTION L1270-1373

 --- redirect() ---
 L1271  isRedirectError(err) 이면
 L1272    redirectUrl  = getURLFromRedirectError(err)
 L1273    redirectType = getRedirectTypeFromError(err)
 L1275    isFetchAction 이면
 L1279      res.statusCode = 200 / metadata.statusCode = 200
 L1282      => return {type: 'done', result: await createRedirectRenderResult(
 L1285           req, res, host, redirectUrl, redirectType,
                 basePath, workStore, requestStore.url.pathname)}
 (else 가 없다 — 위 if 가 L1295 에서 닫히고 아래로 떨어진다)
 L1298    res.statusCode = RedirectStatusCode.SeeOther    (303)
 L1300      res.setHeader('Location', redirectUrl)
 L1301      => return {type: 'done', ...}

 --- notFound() · forbidden() · unauthorized() ---
 L1305  isHTTPAccessFallbackError(err) 이면              (L1305-1334)
 L1306    res.statusCode = getAccessFallbackHTTPStatus(err)
          ★ 404 고정이 아니다. forbidden 은 403, unauthorized 는 401
 L1307    metadata.statusCode = res.statusCode
 L1309    isFetchAction 이면
 L1310      promise = Promise.reject(err)      (L1311-1319 에서 선삼킴)
 L1320      => return {type: 'done', result: await generateFlight(..., {
 L1322           actionResult: promise, skipPageRendering: false, ...})}
            ★ redirect 거절(L716)과 **같은 수법**이다. 다만 skipPageRendering 이 false —
              액션이 실제로 돌았으니 재검증이 있었을 수 있다
 L1331    아니면 (MPA) => return {type: 'not-found'}

 --- 그 밖 ---
 L1339  isFetchAction 이면 ... (L1339-1369)
 L1372  => throw err
```

```text
 ★★ 액션 하나에 응답 모양이 **여섯**이다

 redirect()      fetch -> 200 + x-action-redirect + 목적지 Flight   (L1279)
                 MPA   -> 303 + Location                          (L1298)
 notFound() 류   fetch -> 거부된 Promise 를 Flight 에 실어 보낸다   (L1320)
                 MPA   -> {type: 'not-found'}                      (L1331)
 그 밖의 에러    fetch -> 클라이언트로 보낸다                       (L1339-1369)
                 MPA   -> throw (위로 올린다)                       (L1372)

 => `isFetchAction` 이 catch 전체를 가른다.
    같은 예외가 **클라이언트 라우터용 페이로드**가 되기도 하고
    **평범한 HTTP 응답**이 되기도 한다
```

```text
 ★ fetch 리다이렉트는 목적지를 **미리 렌더해서 실어 보낸다** (L1284)

   createRedirectRenderResult(req, res, host, redirectUrl, redirectType, ...)

 => 클라이언트가 리다이렉트를 받고 다시 요청하는 왕복을 없앤다.
    액션 응답 하나에 "어디로 가라 + 거기 내용" 이 함께 온다
 ★ 인자에 `host` 가 있다 — [01]의 CSRF 검사가 만든 그 값이다.
   목적지를 렌더하려면 자기 호스트를 알아야 한다
```

```text
 ★ 이 catch 는 [동적 응답]·[정적 응답]의 catch 와 성격이 다르다

 [동적 응답] 04   에러 화면을 **다시 렌더한다**
 [정적 응답] 05   다섯을 위로 던지고 나머지를 에러 화면으로
 여기             흐름 제어 예외를 **응답 형식으로 번역한다**

 => 액션은 화면을 그리는 자리가 아니다. redirect 와 notFound 를
    클라이언트가 알아들을 모양으로 바꾸는 것이 catch 의 일이다
 => 진짜 에러(L1339 이후)만 화면 쪽으로 넘긴다
```

## 결과가 쓰이는 곳

```text
 {type: 'done', result}
      --> [App Router] L3010-3012 가 받아 metadata 를 옮겨 붙이고 그대로 반환한다.
          여기서 만든 응답이 그대로 나간다

 res.statusCode / Location 헤더
      --> MPA 액션의 303. 브라우저가 따라간다

 x-action-redirect (createRedirectRenderResult 안에서 붙는다)
      --> 클라이언트 라우터가 읽어 내비게이션한다.
          브라우저는 이것을 리다이렉트로 보지 않는다

 throw err (L1372)
      --> **renderToStream 에는 닿지 않는다.**
          handleAction 호출은 [App Router] L2975 이고 renderToStream 은 L3027 이라
          그 뒤다. 감싸는 renderToHTMLOrFlightImpl(L2562-3087)에는 try/catch 가 없다
      --> workAsyncStorage.run(L3181) 밖으로 올라가 라우트 모듈·base-server 쪽이 받는다
      ※ 정확히 어디가 받는지는 확인하지 않았다
```

## 다루지 않는 것

`createRedirectRenderResult`(L366)가 목적지를 렌더하고 `x-action-redirect` 를 붙이는 방식, `isRedirectError` / `getURLFromRedirectError` / `getRedirectTypeFromError` 와 `redirect()` 가 던지는 예외의 형식, `RedirectStatusCode` 열거, L1305-1334 의 HTTP 접근 폴백(`notFound()` · `forbidden()` · `unauthorized()`) 처리, L1339-1369 의 일반 에러 처리와 클라이언트로 보내는 형식, `addRevalidationHeader`(L151)가 재검증 결과를 헤더로 알리는 방식, 클라이언트 라우터가 `x-action-redirect` 를 해석하는 쪽은 이 문서의 범위 밖이다.
