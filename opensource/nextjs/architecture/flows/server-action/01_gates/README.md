# 01 관문 여덟

상위: [서버 액션이 실행되기까지](../README.md)

시그니처(L567-587) 다음의 185줄(L588-772)이다. **CSRF 검사가 그 절반을 쓴다.** 서버 액션은 브라우저가 보낸 POST 로 서버 함수를 부르는 길이라, 그 POST 가 우리 페이지에서 왔는지를 여기서 따진다.

## 위치

`packages/next` / `src/server/app-render` / `action-handler.ts` L588-L772 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/action-handler.ts#L588-L772))

## 실제 코드

origin 을 뽑는 자리에 `'null'` 이라는 특수값이 따로 있다.

```ts
// action-handler.ts L658-L668
  const originHeader = req.headers['origin']
  const originHost =
    typeof originHeader === 'string'
      ? // 'null' is a valid origin e.g. from privacy-sensitive contexts like sandboxed iframes.
        // However, these contexts can still send along credentials like cookies,
        // so we need to check if they're allowed cross-origin requests.
        originHeader === 'null'
        ? 'null'
        : new URL(originHeader).host
      : undefined
  const host = parseHostHeader(req.headers)
```

```text
 주석 L661-663
   "'null' is a valid origin e.g. from privacy-sensitive contexts like sandboxed iframes.
    However, these contexts can still send along credentials like cookies,
    so we need to check if they're allowed cross-origin requests."

 => 샌드박스 iframe 은 origin 을 문자열 `'null'` 로 보낸다.
    그런데 **쿠키는 그대로 실어 보낼 수 있다**.
    그래서 "origin 이 없다" 로 봐서 통과시키면 안 되고, 값으로 다뤄 검사한다
 ★ `new URL(originHeader).host` 를 바로 부르면 `'null'` 에서 터진다.
   그래서 삼항이 두 겹이다
 ★★★ 다만 이 삼항이 막는 것은 `'null'` **하나뿐**이다.
   `origin: foo` 처럼 URL 이 아닌 값이 오면 L666 이 TypeError 를 던지는데,
   이 줄은 **try(L774) 밖**이다. 그리고 부르는 쪽
   renderToHTMLOrFlightImpl(app-render.tsx L2562-3087)에도 try/catch 가 없다
   => handleAction 밖으로 그대로 탈출한다
   ※ 실제로 어디까지 올라가는지는 확인하지 않았다
```

## 동작 흐름

```text
 ACTION L588-772

 --- 준비 ---
 L588  contentType = req.headers['content-type']
 L590  serverModuleMap = getServerModuleMap()
 L592  {isFetchAction, actionId, isURLEncodedAction, ...} = getServerActionRequestMetadata(req)
 L600  handleUnrecognizedFetchAction = (err) => {...}

 --- 관문 1~4: 본문 디코드보다 앞 (디코드는 [02]의 L792~) ---
 L621  !isPossibleServerAction 이면              => return null
 L627  isURLEncodedAction 이면
 L628    isFetchAction 이면                      => return {type: 'not-found'}
 L632    아니면 (MPA 액션)                        => return null  (L634)
 L639  !hasServerActions() 이면
 L640    actionId 가 서버 참조 ID 모양도 아니면 getInvalidServerReferenceIdError
 L643    아니면 getActionNotFoundError
 L644    => handleUnrecognizedFetchAction(error)
 L647  workStore.isStaticGeneration 이면
 L648    => throw "Invariant: server actions can't be handled during static rendering"
          ★ 정적 생성 중에 액션이 오는 것은 버그다
          ★ 관문 구간(L588-772)의 throw 는 **둘**이다 — 여기 L648 과
            CSRF 실패 + MPA 액션인 L739

 --- 상태 바꾸기 ---
 L656  workStore.fetchCache = 'default-no-store'

 --- 관문 5~6: CSRF ---
 L658  originHeader = req.headers['origin']
 L659  originHost = 문자열이면 ('null' 이면 'null', 아니면 new URL(...).host)
 L668  host = parseHostHeader(req.headers)
 L672  function warnBadServerActionRequest() { warning 이 있으면 warn(warning) }

 L679  originHost 가 없으면
 L684    warning = 'Missing `origin` header from a forwarded Server Actions request.'
          ★★ **통과시킨다.** 그런데 그 문자열이 실제로 찍히는 곳은 둘뿐이다 —
             L880(Edge MPA) · L1089(Node MPA).
             주석 L879 · L1088 - "Only warn if it's a server action,
               otherwise skip for other post requests"
          ★★★ **fetch 액션에는 로그가 남지 않는다.** L1241 로 곧장 간다
          주석 L680-683 - origin 없는 손수 만든 요청이거나 안전하지 않은 브라우저다.
            그런 브라우저를 막을 방법이 없고, 손수 만든 요청은
            **사용자가 자발적으로 공유하지 않은 자격증명을 담을 수 없다**

 L685  아니고 (host 가 없거나 originHost !== host.value)이면
 L689    isCsrfOriginAllowed(originHost, serverActions?.allowedOrigins) 이면
 L690      통과 (사용자가 허용 목록에 넣었다)
 L691    아니면
 L692      host 가 있으면
 L694        console.error(`${host.type} header with value ... does not match
                            origin header with value ... Aborting the action.`)
 L703      아니면
 L705        console.error(`x-forwarded-host or host headers are not provided. ...`)
 L710      error = new Error('Invalid Server Actions request.')
 L712      isFetchAction 이면
 L713        res.statusCode = 500 / metadata.statusCode = 500
 L716        promise = Promise.reject(error)
 L722        await promise  (try/catch 로 삼킨다)
 L727        => return {type: 'done', result: await generateFlight(..., {
 L730             actionResult: promise, skipPageRendering: true, ...})}
 L739      아니면 => throw error

 --- 관문 7 자리 (관문이 아니다 — 헤더만 박는다) ---
 L744  res.setHeader('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate')

 --- 관문 8: 워커 전달 ---
 L749  actionWasForwarded = Boolean(req.headers['x-action-forwarded'])
 L754  actionId 가 있고 전달된 적 없으면
 L755    forwardedWorker = selectWorkerForForwarding(actionId, page)
 L760    있으면 => return {type: 'done', result: await createForwardedActionResponse(...)}
```

```text
 ★★★ origin 이 **없으면 통과**시킨다 (L679-684)

 직관과 반대다. 보통은 없으면 막을 것 같은데 경고 문자열만 세우고 넘긴다.
 ★★ 게다가 그 경고는 **MPA 액션에서만** 찍힌다 (L880 · L1089).
   서버 액션의 흔한 형태인 fetch 액션은 **무음으로 통과**한다
 주석 L680-683 이 근거를 댄다
   "This is a handcrafted request without an origin or a request from an unsafe browser.
    We'll let this through but log a warning.
    We can't guard against unsafe browsers and handcrafted requests can't contain
    user credentials that haven't been shared willingly."

 => CSRF 는 **피해자의 브라우저가 쿠키를 자동으로 붙여 보내는 것**이 문제다.
    curl 로 손수 만든 요청에는 그런 쿠키가 안 붙는다. 그래서 위험이 다르다
 => 반대로 샌드박스 iframe(origin: 'null')은 **쿠키를 붙일 수 있어** 검사 대상이다.
    위 인용이 그 이야기다
```

```ts
// action-handler.ts L712-L737
      if (isFetchAction) {
        res.statusCode = 500
        metadata.statusCode = 500

        const promise = Promise.reject(error)
        try {
          // we need to await the promise to trigger the rejection early
          // so that it's already handled by the time we call
          // the RSC runtime. Otherwise, it will throw an unhandled
          // promise rejection error in the renderer.
          await promise
        } catch {
          // swallow error, it's gonna be handled on the client
        }

        return {
          type: 'done',
          result: await generateFlight(req, ctx, requestStore, {
            actionResult: promise,
            // We didn't execute an action, so no revalidations could have
            // occurred. We can skip rendering the page.
            skipPageRendering: true,
            temporaryReferences,
          }),
        }
      }
```

```text
 ★★ 거절하는 방식이 fetch 액션에서만 특이하다 (L712-739)

 fetch 액션이면 에러를 던지지 않고 **거부된 Promise 를 액션 결과로 실어 보낸다**
 MPA 액션이면 그냥 **던진다** (L739)
   promise = Promise.reject(error)
   await promise   (try/catch 로 삼킨다)
   generateFlight(..., {actionResult: promise, skipPageRendering: true})

 주석 L718-721
   "we need to await the promise to trigger the rejection early
    so that it's already handled by the time we call the RSC runtime.
    Otherwise, it will throw an unhandled promise rejection error in the renderer."
 => 미리 한 번 await 해서 **거부를 처리된 상태로 만든다.**
    안 그러면 렌더러에서 unhandled rejection 이 난다
 주석 L731-732 - 액션을 실행하지 않았으므로 재검증도 없었다.
   페이지를 다시 그릴 필요가 없다 => skipPageRendering: true
 ※ 이 거부를 클라이언트의 어느 API 가 받는지는 확인하지 않았다.
   액션을 직접 await 한 호출부에도 전달될 것으로 보인다 (내 추측이다)
```

```text
 ★ 로그에 들어가는 헤더 값은 잘라 쓴다

 L697  limitUntrustedHeaderValueForLogs(host.value)
 L699  limitUntrustedHeaderValueForLogs(originHost)
 (정의는 ACTION L507)
 => 공격자가 넣은 긴 문자열이 로그를 오염시키지 않게 한다
```

## 결과가 쓰이는 곳

```text
 여기를 통과한 요청
      --> [02]가 본문을 디코드하고 액션을 실행한다

 warning (L670)
      --> 부르는 자리는 L880(Edge MPA)과 L1089(Node MPA) **둘뿐**이다.
          fetch 액션 경로에는 호출이 없다
      주석 L879 · L1088 - 서버 액션일 때만 경고한다.
        평범한 POST 에 경고를 띄우지 않으려는 것이다

 workStore.fetchCache
      --> 액션 본문 안의 fetch 기본값

 host (parseHostHeader 의 결과)
      --> CSRF 비교에 쓰고, 워커 전달(L766)에도 넘긴다
```

## 다루지 않는 것

`parseHostHeader`(L511)가 `x-forwarded-host` 와 `host` 중 무엇을 고르고 `host.type` 이 무엇인지, `isCsrfOriginAllowed` 의 매칭 규칙과 `serverActions.allowedOrigins` 설정, `getServerActionRequestMetadata`(`server/lib/server-action-request-meta.ts`)가 **헤더와 `req.method` 만 보고**(본문은 안 읽는다) `actionId` 와 `isFetchAction` 을 정하는 규칙, `mightBeServerReferenceId` / `getInvalidServerReferenceIdError` / `getActionNotFoundError`, `hasServerActions`(L88)가 무엇을 보는지, `selectWorkerForForwarding` 의 워커 선택과 `createForwardedActionResponse`(L210), `generateFlight` 의 `skipPageRendering` 처리, `limitUntrustedHeaderValueForLogs`(L507)의 자르는 길이는 이 문서의 범위 밖이다.
