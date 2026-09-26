# 04 에러 화면 다시 렌더하기

상위: [동적 응답을 스트림으로 내보내기](../README.md)

`catch` 블록 하나가 280줄이다. 로그를 찍고 끝내지 않는다. **에러 화면을 다시 렌더한다.** 다만 [02]·[03]을 그대로 되풀이하지는 않는다 — 브라우저로 나가는 데이터는 **실패한 원래 렌더의 것**이다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L4087-L4366 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L4087-L4366))

## 실제 코드

먼저 **다시 렌더하면 안 되는 것**을 걸러낸다.

```tsx
// app-render.tsx L4088-L4114
      if (
        isStaticGenBailoutError(err) ||
        (typeof err === 'object' &&
          err !== null &&
          'message' in err &&
          typeof err.message === 'string' &&
          err.message.includes(
            'https://nextjs.org/docs/advanced-features/static-html-export'
          ))
      ) {
        // Ensure that "next dev" prints the red error overlay
        endSpanWithError(err)
        throw err
      }

      // If a bailout made it to this point, it means it wasn't wrapped inside
      // a suspense boundary.
      const shouldBailoutToCSR = isBailoutToCSRError(err)
      if (shouldBailoutToCSR) {
        const stack = getStackWithoutErrorMessage(err)
        error(
          `${err.reason} should be wrapped in a suspense boundary at page "${pagePath}". Read more: https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout\n${stack}`
        )

        endSpanWithError(err)
        throw err
      }
```

## 동작 흐름

```text
 catch (err)  APPR L4087-4366

 --- 1단: 그냥 위로 던지는 둘 ---
 L4088  isStaticGenBailoutError 이거나
        메시지에 'https://nextjs.org/docs/advanced-features/static-html-export' 가 있으면
 L4099    endSpanWithError(err)
 L4100    => throw err
          주석 L4098 - "Ensure that "next dev" prints the red error overlay"

 L4105  shouldBailoutToCSR = isBailoutToCSRError(err)
 L4106  맞으면
 L4107    stack = getStackWithoutErrorMessage(err)
 L4108    error(`${err.reason} should be wrapped in a suspense boundary at
                 page "${pagePath}". Read more: .../missing-suspense-with-csr-bailout`)
 L4112    endSpanWithError(err)
 L4113    => throw err
          주석 L4103-4104 - 바이아웃이 여기까지 왔다는 것은
            **Suspense 경계 안에 감싸이지 않았다**는 뜻이다

 --- 2단: 분류 (MARK: errorRecovery classification, L4116) ---
 L4117  errorType (let)
 L4119  isHTTPAccessFallbackError 면          notFound() · forbidden() · unauthorized()
 L4120    res.statusCode = getAccessFallbackHTTPStatus(err)
 L4121    metadata.statusCode = 그것
 L4122    errorType = getAccessFallbackErrorTypeByStatus(res.statusCode)
 L4123  isRedirectError 면                    redirect() · permanentRedirect()
 L4124    errorType = 'redirect'
 L4125    res.statusCode = getRedirectStatusCodeFromError(err)
 L4128    redirectUrl = addPathPrefix(getURLFromRedirectError(err), basePath)
 L4135    headers = new Headers()
 L4136    appendMutableCookies(headers, requestStore.mutableCookies) 이면
 L4137      setHeader('set-cookie', [...headers.values()])
 L4140    setHeader('location', redirectUrl)
 L4141  아니고 CSR 바이아웃도 아니면
 L4142    res.statusCode = 500
        ★ `!shouldBailoutToCSR` 는 **죽은 가드**다.
          참이면 L4113 에서 이미 throw 했으므로 여기 도달하면 언제나 거짓이다

 --- 3단: 에러용 스크립트를 따로 고른다 ---
 L4146  [errorPreinitScripts, errorBootstrapScript] = getRequiredScripts(
           ..., UNDERSCORE_NOT_FOUND_ROUTE_ENTRY)     ★ 페이지가 아니라 **not-found 엔트리**
 L4157  개발이면 errorBootstrapScriptContent = bootstrapScriptContent (그대로 재사용)
 L4159  아니고 Turbopack 부트스트랩 정보가 있으면 not-found 엔트리로 다시 만든다

 --- 4단: 다시 렌더 (L4170 nodeStreams / L4268 webStreams) ---
 L4175  try {
 L4176    errorRSCPayload = await workUnitAsyncStorage.run(..., getErrorRSCPayload, ...)
 L4181      reactServerErrorsByDigest.has(err.digest) ? **null** : err
            ★ RSC 핸들러가 이미 기록한 에러면 err 대신 null 을 넘긴다.
              [01]이 말한 digest 공유가 실제로 쓰이는 자리다
 L4182      errorType
 L4199    reactServerResult 가 null 이면 ...      ★ [02]가 실패했을 때
 L4203  } catch (setupErr) { ... }

 L4208  try {
 L4209    generateStaticHTML = supportsDynamicResponse !== true
 L4211    {stream: errorHtmlStream, allReady: errorAllReady} =
             await workUnitAsyncStorage.run(..., <ErrorApp ... />, ...)
 L4231    errorAllReady.finally(() => renderSpan.end())
 L4235    => return await continueFizzStream(errorHtmlStream, {
 L4236         inlinedDataStream: createNodeInlinedDataStream(
 L4240           reactServerResult.consume(), ...)   ★★★ 아래 별항
 L4249         getServerInsertedHTML: makeGetServerInsertedHTML({serverCapturedErrors: [], ...})
 L4256  } catch (finalErr) {          (L4256-4267)
 L4257    개발이고 (조건) 이면
 L4261      {bailOnRootNotFound} = ...
 L4266    => throw finalErr
        }
```

```text
 ★★★ 던질지 다시 그릴지를 세 부류로 가른다

 그냥 던진다        StaticGenBailoutError · static-html-export 안내 · CSR 바이아웃
                    => 개발에서 빨간 오버레이를 띄워야 하거나
                       개발자가 코드를 고쳐야 하는 것들이다

 상태 코드를 정한다  HTTPAccessFallback(404·403·401) · Redirect(3xx) · 그 밖 500

 다시 그린다        위에서 정한 errorType 으로 getErrorRSCPayload -> <ErrorApp>

 => `notFound()` · `redirect()` 같은 **흐름 제어용 예외**가 여기서 상태 코드가 된다.
    [API 역인덱스]의 "흐름을 끊는 것" 표가 전부 이 자리로 온다
```

```text
 ★★★ 에러 화면은 **원래 렌더의 RSC 데이터**를 싣는다 (L4236-4243)

 소스가 주석으로 못박는다
   // This is intentionally using the readable datastream from the
   // main render rather than the flight data from the error page
   // render
   reactServerResult.consume(),

 => 나가는 문서는 **ErrorApp 이 그린 HTML + 실패한 원래 렌더의 Flight 데이터** 다.
    의도적인 비대칭이다
 ※ 왜 그렇게 하는지는 주석이 말하지 않는다. 클라이언트가 원래 트리를 알아야
   수화와 내비게이션이 이어지기 때문으로 보인다 (내 해석이다)

 ★★ 그리고 정상 렌더에서 모은 SSR 에러는 **버린다** (L4249)
      serverCapturedErrors: []
    빈 배열이다. allCapturedErrors 를 넘기지 않는다
```

```text
 ★★ redirect 는 쿠키를 함께 실어 보낸다 (L4133-4140)

   const headers = new Headers()
   if (appendMutableCookies(headers, requestStore.mutableCookies)) {
     setHeader('set-cookie', Array.from(headers.values()))
   }
   setHeader('location', redirectUrl)

 주석 L4133-4134 - "If there were mutable cookies set, we need to set them on
                    the response."
 => 서버 액션이나 렌더 도중 쿠키를 바꾸고 redirect() 했을 때,
    그 쿠키가 응답에서 사라지지 않게 한다
 ★ requestStore.mutableCookies 다 — [App Router]에서 본 RequestStore 다
```

```text
 ★★ 에러 화면은 **not-found 엔트리의 번들**을 쓴다 (L4146-4154)

   getRequiredScripts(..., UNDERSCORE_NOT_FOUND_ROUTE_ENTRY)

 => 원래 페이지가 아니라 not-found 엔트리의 스크립트를 고른다
 ※ 이유를 소스는 말하지 않는다. 깨진 페이지의 번들을 다시 실으면
   브라우저에서도 같은 일이 날 것이라는 것은 내 추측이다
 ★ 다만 무조건은 아니다 — 개발에서는 L4157-4158 이
   errorBootstrapScriptContent = bootstrapScriptContent 로
   **원래 페이지의 부트스트랩 내용을 그대로 재사용**한다
 ★ [응답 나가기] 04 의 폴백 사슬 1단이 찾던 그 엔트리와 같은 상수다
```

```text
 ★★ catch 안에 try 가 **형제로 둘** 있다 (겹이 아니다)

   L3451  바깥 try            정상 렌더
     L4175  try A             에러 RSC 페이로드 만들기   -> catch L4203
     L4208  try B             에러 HTML 만들기           -> catch L4256-4267
   (Edge 갈래에도 같은 짝이 있다 — L4273 · L4306)

 => A 와 B 는 순차 형제다. 서로 중첩되지 않는다. 최대 깊이는 2다
 => 그래도 에러 화면을 만들다 또 실패하는 것까지 받아 낸다

 ★ L4199-4202 - reactServerResult 가 null 이면 **포기한다**
     if (reactServerResult === null) { endSpanWithError(err); throw err }
   에러 화면을 만들지 않고 원본 err 를 그대로 던진다.
   그런데 이 검사는 errorRSCPayload 를 **이미 만든 뒤**에 한다
```

## 결과가 쓰이는 곳

```text
 res.statusCode / metadata.statusCode
      --> 둘 다 같은 값으로 맞춘다. metadata 는 RenderResult 에 실려
          [응답 나가기]의 캐시 항목에까지 간다

 setHeader('location') / setHeader('set-cookie')
      --> redirect() 의 실제 구현부다. 예외 하나가 여기서 3xx 응답이 된다

 errorType
      --> getErrorRSCPayload 와 <ErrorApp> 에 넘어가 어떤 에러 화면을 그릴지 정한다

 반환한 스트림
      --> 부른 쪽으로 그대로 돌아간다. 부른 쪽은 이것이 에러 화면인지 모른다
      ★ renderToStream 의 호출처는 **둘**이다
          [App Router] L3027  보통의 HTML 렌더
          [App Router] L2992  서버 액션이 not-found 를 냈을 때
                              (notFoundLoaderTree + res.statusCode = 404)
```

## 다루지 않는 것

`getErrorRSCPayload`(L2234)와 `ErrorApp`(L2433)의 본문, `isStaticGenBailoutError` / `isBailoutToCSRError` / `isHTTPAccessFallbackError` / `isRedirectError` 각각의 판별과 그 예외를 던지는 자리(`notFound()` · `redirect()` 등의 구현), `getAccessFallbackHTTPStatus` / `getAccessFallbackErrorTypeByStatus` / `getRedirectStatusCodeFromError` / `getURLFromRedirectError` 의 매핑, `appendMutableCookies` 와 `requestStore.mutableCookies` 의 수집 경로, `MetadataErrorType` 의 값들, 마지막 catch(Node 쪽 L4256-4267 · Edge 쪽 L4353-4364)와 `bailOnRootNotFound`, Edge 갈래(L4268-4365)의 web 스트림 판, `UNDERSCORE_NOT_FOUND_ROUTE_ENTRY` 번들이 빌드에서 만들어지는 과정은 이 문서의 범위 밖이다.
