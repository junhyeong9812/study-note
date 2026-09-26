# 05 실패 처리

상위: [정적 응답을 미리 만들기](../README.md)

`catch` 가 559줄이다. [동적 응답]의 280줄보다 두 배다. **먼저 다섯을 위로 던지고**, 살아남은 것만 에러 화면으로 만든다.

## 위치

`packages/next` / `src/server/app-render` / `app-render.tsx` L9665-L10223 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/app-render.tsx#L9665-L10223))

## 실제 코드

던지는 넷 중 하나가 이 흐름 고유의 것이다.

```tsx
// app-render.tsx L9680-L9684
    // If this is a static generation error, we need to throw it so that it
    // can be handled by the caller if we're in static generation mode.
    if (isDynamicServerError(err)) {
      throw err
    }
```

```text
 주석 L9680-9681
   "If this is a static generation error, we need to throw it so that it
    can be handled by the caller if we're in static generation mode."

 => `isDynamicServerError` 는 [04]가 기대는 **바로 그 예외**다.
    `cookies()` 같은 동적 API 를 정적 생성 중에 쓰면 이것이 난다
 => 여기서 잡지 않고 **위로 올린다**. 부르는 쪽이 "이 페이지는 정적으로 못 만든다"
    고 판단해야 하기 때문이다
 ★ [동적 응답]의 catch 에는 이 갈래가 없다. 거기서는 동적이 정상이다
```

## 동작 흐름

```text
 catch (err)  APPR L9665-10223

 --- 1단: 그냥 던지는 넷 (다섯째는 2단에 숨어 있다) ---
 L9666  isStaticGenBailoutError 이거나 static-html-export 안내 메시지면
 L9677    => throw err
          주석 L9676 - "Ensure that "next dev" prints the red error overlay"
 L9682  isDynamicServerError(err) 이면
 L9683    => throw err                         ★ 위 별항
 L9688  shouldBailoutToCSR = isBailoutToCSRError(err)
 L9689  맞으면 stack 을 찍고
 L9695    => throw err
          주석 L9686-9687 - Suspense 경계 안에 감싸이지 않았다는 뜻이다
 L9700  reactServerPrerenderResult === null 이면
 L9701    => throw err
          주석 L9698-9699 - RSC 스트림조차 못 얻고 실패했다.
            단순한 렌더 에러가 아니므로 **일찍** 던진다

 --- 2단: 분류 ---
 L9703  errorType (let)
 L9704  isHTTPAccessFallback = isHTTPAccessFallbackError(err)
 L9705  isRedirect = isRedirectError(err)
 L9707  isHTTPAccessFallback 이면 ...          404 · 403 · 401
 L9711  isRedirect 이면 ...                    3xx
 L9719  아니면 ...                             그 밖
        ★ [동적 응답]의 같은 자리(L4141)는 `else if (!shouldBailoutToCSR)` 로
          조건이 붙어 있다 (다만 그 조건은 죽은 가드다)
 L9724  ★★ cacheComponents 이고 404 도 redirect 도 아니면
 L9725    => throw reactServerErrorsByDigest.get(err.digest) ?? err
          **다섯 번째로 던지는 자리다.** 분류부에 섞여 있어 눈에 안 띈다
          => cacheComponents 에서 일반 에러는 **에러 화면을 만들지 않고 빌드를 실패시킨다**
             아래 L9748 에 닿는 것은 404 와 redirect 뿐이다

 --- 3단: 에러용 스크립트 ---
 L9728  [errorPreinitScripts, errorBootstrapScript] = getRequiredScripts(...)
 L9738  errorBootstrapScriptContent = ...

 --- 4단: 에러 화면 ---
 L9748  cacheComponents 이면 ... (L9748-10104, 357줄)
 L10106 prerenderLegacyStore: PrerenderStore = {...}
 L10126 errorRSCPayload = await workUnitAsyncStorage.run(...)
 L10137 errorServerStream = workUnitAsyncStorage.run(...)
 ... (L10137-10222)
```

```text
 ★★★ 던지는 이유가 갈래마다 다르다

 isStaticGenBailoutError       개발 오버레이를 띄워야 한다
 static-html-export 안내       〃
 isDynamicServerError          **부르는 쪽이 정적 생성을 포기해야 한다**
 isBailoutToCSRError           개발자가 Suspense 로 감싸야 한다
 reactServerPrerenderResult null  RSC 도 못 만들었다. 에러 화면도 못 만든다

 => 넷 다 "여기서 고칠 수 없는 것" 이다.
 ★ 다섯째는 2단 분류부 안에 있다 (L9724-9726) —
   cacheComponents 이고 404·redirect 가 아니면 던진다
 ★ [동적 응답]의 catch 는 최상위에서 그냥 던지는 갈래가 **둘**뿐이다
     L4100  isStaticGenBailoutError / static-html-export
     L4113  isBailoutToCSRError
   여기는 그 둘에 **두 개가 더** 붙는다 — isDynamicServerError(L9683)와
   reactServerPrerenderResult === null(L9701)
```

```text
 ★★ 에러 화면도 cacheComponents 면 따로 간다 (L9748)

 L9748  if (cacheComponents) { ... }     357줄
 L10106 그 밖                             117줄

 => 정상 경로의 3갈래가 catch 안에서 2갈래로 다시 나타난다.
 ★★ 다만 cacheComponents 일 때 L9748 에 닿는 것은 **404 와 redirect 뿐**이다.
    일반 에러는 L9725 에서 이미 던져졌다
```

```text
 ★ [동적 응답]의 catch 와 나란히 놓으면

                        renderToStream        prerenderToStream
 catch 크기              280줄                 559줄
 그냥 던지는 갈래        둘                    **다섯** (isDynamicServerError · RSC 없음
                                                + cacheComponents 일반 에러)
 에러 화면 갈래          node/web 둘           cacheComponents 여부 둘
 인라인 데이터           원래 렌더의 것        (본문 미독)
 스팬                    **직접 연다** (L3372)  **호출처가 감싼다** ([App Router] L2790)
                         endSpanWithError 로     getTracer().wrap 이 종료·예외기록을 대신한다
                         손수 닫는다             그래서 이 함수 안에 endSpanWithError 가 없다
```

## 결과가 쓰이는 곳

```text
 throw 한 에러
      --> [App Router]의 L2801 이 await 하던 자리로 올라간다.
          그 위는 renderToHTMLOrFlightImpl 의 정적 갈래이고,
          거기서 더 위로 가면 빌드 도구나 ISR 재검증이 받는다
      => "이 페이지는 정적으로 못 만든다" 가 여기서 결정된다

 에러 화면을 만들었을 때의 PrerenderToStreamResult
      --> 정상 경로와 같은 자리로 돌아간다.
          404 · 500 페이지도 캐시에 저장될 수 있다는 뜻이다

 res.statusCode / metadata.statusCode
      --> 2단의 분류가 정한다
```

## 다루지 않는 것

`isDynamicServerError` 를 던지는 자리(`dynamic-rendering.ts` 의 동적 API 가드)와 그것을 받는 상위(빌드 도구 · ISR 재검증), L9707-9726 분류부의 세부와 `cacheComponents` 전용 가지(L9724-9726), L9748-10104 의 cacheComponents 에러 화면 357줄, L10106-10222 의 legacy 에러 화면, `getErrorRSCPayload` / `ErrorApp` 의 본문([동적 응답] 04 와 같다), 에러 화면이 인라인 데이터로 무엇을 싣는지, `errorPreinitScripts` / `errorBootstrapScript` 의 엔트리 선택은 이 문서의 범위 밖이다.
