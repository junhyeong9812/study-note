# 서버 액션이 실행되기까지

상위: [Next.js 아키텍처 지도](../../README.md)

[App Router 가 페이지를 만드는 길](../app-render/README.md)의 갈림길에서 `isPossibleActionRequest` 이면 `handleAction` 이 불린다. **본문에 닿기 전에 통과해야 하는 관문이 여덟이다.** 사용자 코드를 서버에서 실행시켜 주는 길이라 그렇다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e). 약어: `ACTION` = `server/app-render/action-handler.ts`(1580줄).

## 위치

`packages/next` / `src/server/app-render` / `action-handler.ts` L567-L1374 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/action-handler.ts#L567-L1374))

## 실제 코드

가장 이른 관문이 이것이다.

```ts
// action-handler.ts L618-L623
  // If it can't be a Server Action, skip handling.
  // Note that this can be a false positive -- any multipart/urlencoded POST can get us here,
  // But won't know if it's an MPA action or not until we call `decodeAction` below.
  if (!isPossibleServerAction) {
    return null
  }
```

```text
 주석 L619-620
   "Note that this can be a false positive -- any multipart/urlencoded POST can get us here,
    But won't know if it's an MPA action or not until we call `decodeAction` below."

 => `isPossibleActionRequest` 는 **확실한 판정이 아니다.**
    multipart 나 urlencoded POST 면 일단 여기까지 온다.
    진짜 액션인지는 본문을 디코드해 봐야 안다
 => [App Router] 흐름에서 이 값이 `getIsPossibleServerAction(req)` 였던 이유다
```

## 동작 흐름

```text
 handleAction  ACTION L567-1374 (808줄)

 L588-772   관문 여덟                                    [01]
 L774-1270  try {
 L775-1269    actionAsyncStorage.run({isAction: true}, ...) 안에서
              액션을 찾아 실행한다                        [02]
 L1270      } catch (err) {
 L1271-1373   redirect · notFound 를 응답으로 바꾼다      [03]
            }
 L1374      }   (함수 끝. 이 뒤 L1380 SERVER_ACTION_ARGS_LIMIT 은 밖이다)
```

1. [관문 여덟](01_gates/README.md) — CSRF 검사와 워커 전달.
2. [찾아서 실행하기](02_execute/README.md) — 본문 디코드부터 사용자 함수 호출까지.
3. [흐름 제어 예외를 응답으로](03_control-flow/README.md) — catch 104줄.

```text
 ★★★ 관문 여덟 — 다만 그중 요청을 **실제로 끊는** 것은 여섯이다 (L588-772)

 1  L621  isPossibleServerAction 이 아니면          => return null      (액션이 아니다)
 2  L627  URL 인코딩 액션이면                        => not-found 또는 null
          주석 L625 - "We don't currently support URL encoded actions, so we bail out early."
 3  L639  앱에 서버 액션이 하나도 없으면             => 404
          (handleUnrecognizedFetchAction — 이름과 달리 fetch 액션이 아닌 요청에도 걸린다.
           L609-611  next-action-not-found: 1 + text/plain + 404)
 4  L647  workStore.isStaticGeneration 이면          => **throw**
          "Invariant: server actions can't be handled during static rendering"
 5  L679  origin 헤더가 없으면                       통과 (경고는 MPA 에서만)
 6  L685  **host 가 없거나** origin 과 host 가 다르면
          (host 는 parseHostHeader 가 x-forwarded-host 를 먼저 보고 고른 값이다)
          L689  allowedOrigins 에 있으면              통과
          L691  아니면                                => **CSRF. 중단**   ★ [01]
 7  L744  Cache-Control: no-cache, no-store, ...     **관문이 아니다.** 헤더만 박는다
 8  L754  이 워커에 그 액션이 없으면                 => 다른 워커로 전달

 ★ 끊는 것은 1·2·3·4·6·8 여섯이다.
   5(origin 없음)는 아무것도 막지 않고, 7 은 관문이 아니다
 ★ 8 도 "거르는" 것이 아니라 **넘기는** 것이다 —
   createForwardedActionResponse 가 본문을 그대로 흘려보낸다 (L259-273)
 => 본문에 닿기 전에 끝나는 것은 다섯이다
```

```text
 ★★ 캐시 금지 헤더는 **관문 1~6 을 통과한 뒤에** 붙는다 (L744-747)

   res.setHeader('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate')
   주석 L743 - "ensure we avoid caching server actions unexpectedly"

 ★★★ 그 앞에서 나가는 응답에는 **안 붙는다**
     L609-615  액션을 못 찾았을 때의 404
     L713-736  CSRF 거절 500
     L627-636  URL 인코딩 액션의 not-found / null

 ★ 그리고 fetch 기본값도 바꾼다 (L656)
     workStore.fetchCache = 'default-no-store'
     주석 L655 - "When running actions the default is no-store,
                  you can still `cache: 'force-cache'`"
 => 액션 안에서는 fetch 가 기본으로 캐시를 안 한다. 명시하면 쓸 수 있다
```

```text
 ★★ 요청이 다른 워커로 넘어갈 수 있다 (L754-772)

 L749  actionWasForwarded = Boolean(req.headers['x-action-forwarded'])
 L754  actionId 가 있고 아직 전달된 적 없으면
 L755    forwardedWorker = selectWorkerForForwarding(actionId, page)
 L760    있으면 => createForwardedActionResponse(...)

 주석 L751-753
   "Only attempt to forward if this request has not already been forwarded.
    Otherwise middleware that rewrites the action POST can cause the receiving
    worker to forward again, looping indefinitely."
 => **무한 전달 고리**가 실제 위험이었다.
    미들웨어가 액션 POST 를 rewrite 하면 받은 워커가 또 전달할 수 있다
 => `x-action-forwarded` 헤더가 그 고리를 끊는다
 ★★ 역할이 하나 더 있다 — 이 값이 `skipPageRendering` 의 **초깃값**이 된다
     L887 · L1096 · L1225 가 executeActionAndPrepareForRender 에 넘기고
     L1395  let skipPageRendering = actionWasForwarded
   헤더를 **심는 쪽**(L228)의 주석이 그 목적을 말한다 (L225-227)
     "we use this to skip rendering the flight tree so that we don't update
      the UI with the response from the forwarded worker"
   => 전달된 워커의 응답으로 화면을 덮어쓰지 않으려는 것이다
```

## 결과가 쓰이는 곳

```text
 반환한 HandleActionResult
      --> [App Router] L2987 이 받는다
          type === 'not-found'  -> notFoundLoaderTree 로 렌더
                                   (상태 코드는 이미 박혀 있다 — 404·403·401)
          type === 'done' + result -> 그대로 응답
          type === 'done' + formState -> **아래로 내려가** 페이지를 다시 그린다
          null -> 액션이 아니었다. 평범한 렌더로 간다

 workStore.fetchCache = 'default-no-store'
      --> 액션 본문 안의 모든 fetch

 res 의 Cache-Control
      --> **관문을 통과한** 액션 응답만 캐시 금지가 된다.
          거절·404 로 일찍 나가는 응답에는 이 헤더가 없다
```

## 다루지 않는 것

`createForwardedActionResponse`(L210)와 `selectWorkerForForwarding` 의 워커 선택, `createRedirectRenderResult`(L366)의 리다이렉트 렌더, `getForwardedHeaders`(L109) / `nodeHeadersToRecord`(L97) / `addRevalidationHeader`(L151)의 헤더 처리, `decodeAction` / `decodeReply` / `decodeFormState` 등 React 의 액션 디코딩, `getServerModuleMap` 과 액션 ID 가 모듈로 풀리는 과정, `extractInfoFromServerReferenceId` 와 액션 ID 형식, `actionAsyncStorage` 가 나르는 것, 서버 액션이 빌드에서 등록되는 과정은 이 흐름의 범위 밖이다.

## 하위 메서드

- [01 관문 여덟](01_gates/README.md)
- [02 찾아서 실행하기](02_execute/README.md)
- [03 흐름 제어 예외를 응답으로](03_control-flow/README.md)
