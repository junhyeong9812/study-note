# 03 서버 액션 응답 받기

상위: [클라이언트가 화면을 바꾸기까지](../README.md)

568줄로 리듀서 중 가장 크다. **[서버 액션] 흐름이 붙인 헤더를 여기서 읽는다.** 서버가 200 으로 보낸 리다이렉트를 리다이렉트로 알아보는 자리이기도 하다.

## 위치

`packages/next` / `src/client/components/router-reducer/reducers` / `server-action-reducer.ts` L107-L308 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/client/components/router-reducer/reducers/server-action-reducer.ts#L107-L308))

## 실제 코드

서버가 붙인 헤더를 차례로 읽는다. 아래 셋보다 **먼저 읽는 것이 하나 더** 있다.

```ts
// server-action-reducer.ts L184-L224
  const redirectHeader = res.headers.get('x-action-redirect')
  const [location, _redirectType] = redirectHeader?.split(';') || []
  let redirectType: RedirectType | undefined
  switch (_redirectType) {
    case 'push':
      redirectType = 'push'
      break
    case 'replace':
      redirectType = 'replace'
      break
    default:
      redirectType = undefined
  }

  const isPrerender = !!res.headers.get(NEXT_IS_PRERENDER_HEADER)

  let revalidationKind: ActionRevalidationKind = ActionDidNotRevalidate
  try {
    const revalidationHeader = res.headers.get('x-action-revalidated')
    if (revalidationHeader) {
      const parsedKind = JSON.parse(revalidationHeader)
      if (
        parsedKind === ActionDidRevalidateStaticAndDynamic ||
        parsedKind === ActionDidRevalidateDynamicOnly
      ) {
        revalidationKind = parsedKind
      }
    }
  } catch {}

  const redirectLocation = location
    ? assignLocation(
        location,
        new URL(state.canonicalUrl, window.location.href)
      )
    : undefined

  const contentType = res.headers.get('content-type')
  const isRscResponse = !!(
    contentType && contentType.startsWith(RSC_CONTENT_TYPE_HEADER)
  )
```

## 동작 흐름

```text
 fetchServerAction  SARED L107-308 (응답 해석부는 L176~)

 --- 0. 액션을 못 찾았는가 (L176-182) ---
 L176  NEXT_ACTION_NOT_FOUND_HEADER('x-nextjs-action-not-found')가 있으면
 L182    => throw new UnrecognizedActionError(...)
        ★ [서버 액션] [01]의 관문 3(handleUnrecognizedFetchAction)이 붙인 그 헤더다.
          **세 헤더보다 먼저** 읽는다

 --- 1. 리다이렉트 헤더 ---
 L184  redirectHeader = res.headers.get('x-action-redirect')
 L185  [location, _redirectType] = redirectHeader?.split(';') || []
 L187  switch (_redirectType)
 L188    'push'    -> redirectType = 'push'
 L191    'replace' -> redirectType = 'replace'
 L194    그 밖      -> undefined

 --- 2. 프리렌더 표시 ---
 L198  isPrerender = !!res.headers.get(NEXT_IS_PRERENDER_HEADER)

 --- 3. 재검증 플래그 ---
 L200  revalidationKind = ActionDidNotRevalidate
 L201  try {
 L202    revalidationHeader = res.headers.get('x-action-revalidated')
 L203    있으면
 L204      parsedKind = JSON.parse(revalidationHeader)
 L205      그 값이 StaticAndDynamic 이나 DynamicOnly 면
 L209        revalidationKind = parsedKind
 L212  } catch {}          ★ 파싱 실패를 **조용히 삼킨다**

 --- 4. 목적지 절대화 ---
 L214  redirectLocation = location 이 있으면
 L215    assignLocation(location, new URL(state.canonicalUrl, window.location.href))
        ★ 기준이 `state.canonicalUrl` 인 이유 — 액션은 L150 에서
          **현재 URL 로 POST** 한다 (`fetch(state.canonicalUrl, {method: 'POST'})`)

 --- 5. 응답이 유효한가 ---
 L221  contentType = res.headers.get('content-type')
 L222  isRscResponse = contentType 이 RSC_CONTENT_TYPE_HEADER 로 시작하는가
 L229  RSC 도 아니고 리다이렉트도 아니면
 L232    status >= 400 이고 content-type 이 'text/plain' 이면 본문을 메시지로
 L235    아니면 'An unexpected response was received from the server.'
 L237    => throw new Error(message)

 --- 6. Flight 로 읽기 ---
 L245  isRscResponse 이면
 L249    responsePromise = redirectLocation 이 있으면 processFetch(res) 로 한 겹 벗기고
                           없으면 res 그대로
 L253    response = await createFromFetch(responsePromise, {callServer, ...})
 L264    actionResult = redirectLocation ? **undefined** : response.a
          ★ 내부 리다이렉트면 actionResult 가 **없다**
 L267-290 배포/빌드 ID 가 다르면 flightData 를 **버린다**
          => 멀티존에서 프리페치된 목적지가 다른 빌드의 것이면
             MPA 내비게이션으로 떨어진다
 L291  아니면 (RSC 가 아니다 = **외부 리다이렉트**)
 L292    // An external redirect doesn't contain RSC data.
 L293    actionResult · actionFlightData · actionFlightDataRenderedSearch 를 전부 undefined
        ★ §5(L229)에서 "리다이렉트면 통과" 시킨 그 응답의 귀결이 여기다.
          본문이 없으니 담을 것이 없다
```

```text
 ★★★ 고리가 여기서 닫힌다 — 서버가 붙인 것을 그대로 읽는다

 `x-action-redirect`      [서버 액션] [03]의 createRedirectRenderResult 가 붙였다
                          서버는 **200** 으로 보냈고, 여기서 리다이렉트로 해석한다
 `x-action-revalidated`   [재검증] [03]의 addRevalidationHeader 가 붙였다
                          값 0/1/2 중 하나. 여기서 revalidationKind 가 된다
 `x-nextjs-action-not-found`  [서버 액션] [01]의 관문 3 이 붙였다 (L176, **가장 먼저**)
 `x-nextjs-prerender`     NEXT_IS_PRERENDER_HEADER (L198)
 NEXT_NAV_DEPLOYMENT_ID_HEADER  배포 ID 대조 (L275-276)
 content-type             RSC 면 Flight 로 읽고, 아니면 에러로 본다

 => 서버는 fetch 액션에 **200**(action-handler.ts L1279), MPA 액션에 **303**(L1298)을 준다.
    200 이라 fetch 가 그냥 받고, **클라이언트가 직접 해석한다**
    주석 L1276-1278 - "Since this is not an HTTP redirect, keep the response successful."
 ※ [서버 액션] 문서가 적은 "302 를 주면 브라우저 fetch 가 따라간다" 는 내 추론이었다.
   코드에 302 는 없다
```

```text
 ★★ 리다이렉트 헤더 하나에 값 둘이 실려 있다 (L185)

   const [location, _redirectType] = redirectHeader?.split(';') || []

 => `목적지;push` 또는 `목적지;replace` 형식이다.
    세미콜론 하나로 두 값을 나눠 보낸다
 ★ `_redirectType` 이 그 둘이 아니면 undefined 로 둔다 (L194).
   모르는 값을 받으면 조용히 기본 동작으로 떨어진다
```

```text
 ★★ 재검증 헤더는 **파싱 실패를 삼킨다** (L201-212)

   try {
     const revalidationHeader = res.headers.get('x-action-revalidated')
     if (revalidationHeader) {
       const parsedKind = JSON.parse(revalidationHeader)
       if (parsedKind === ActionDidRevalidateStaticAndDynamic ||
           parsedKind === ActionDidRevalidateDynamicOnly) {
         revalidationKind = parsedKind
       }
     }
   } catch {}

 => `catch {}` 가 비어 있다. 값이 깨져 있으면 ActionDidNotRevalidate 로 남는다
 => 그리고 **허용 목록 검사**를 한다 — 1 이나 2 가 아니면 무시한다.
    0(ActionDidNotRevalidate)을 명시해 보내도 그대로 0 이다
 ★ [재검증] [03]이 "1 이면 정적·동적 전부, 2 면 동적만" 이라고 한 그 값이다
```

```ts
// server-action-reducer.ts L226-L238
  // Handle invalid server action responses.
  // A valid response must have `content-type: text/x-component`, unless it's an external redirect.
  // (external redirects have an 'x-action-redirect' header, but the body is an empty 'text/plain')
  if (!isRscResponse && !redirectLocation) {
    // The server can respond with a text/plain error message, but we'll fallback to something generic
    // if there isn't one.
    const message =
      res.status >= 400 && contentType === 'text/plain'
        ? await res.text()
        : 'An unexpected response was received from the server.'

    throw new Error(message)
  }
```

```text
 ★★ 유효한 응답의 조건이 주석에 있다 (L227-228)

   "A valid response must have `content-type: text/x-component`,
    unless it's an external redirect.
    (external redirects have an 'x-action-redirect' header,
     but the body is an empty 'text/plain')"

 => 바깥 URL 로 리다이렉트할 때는 본문이 없다. 그래서 RSC 가 아니어도 통과시킨다
 ★ 에러 메시지를 서버 본문에서 가져오는 조건이 까다롭다 (L232-235)
     status >= 400 **이고** content-type 이 정확히 'text/plain' 일 때만
   그 밖에는 "An unexpected response was received from the server." 로 덮는다
   => 서버가 보낸 진짜 원인이 이 조건에 안 맞으면 사라진다
```

```text
 ★ 리다이렉트 응답의 본문은 한 겹 벗겨야 한다 (L246-251)

 주석 L246-248
   "Server action redirect responses carry the Flight data of the redirect
    target, which may be prerendered with a completeness marker byte
    prepended. Strip it before passing to Flight."

 => [서버 액션] [03]이 "목적지를 미리 렌더해서 실어 보낸다" 고 한 그것이다.
 ★★ 바이트가 붙는 조건은 **프리렌더가 아니라 빌드 플래그**다
     fetch-server-response.ts L403  if (process.env.__NEXT_CACHE_COMPONENTS)
     독스트링 L387-398 - cacheComponents 가 켜져 있으면 서버가 한 바이트를 앞에 붙인다.
       '~'(0x7e)는 부분, '#'(0x23)은 완성. 꺼져 있으면 원본을 그대로 돌려준다
   => 원문 주석의 "may be prerendered with ..." 를
      "프리렌더면 바이트가 있다" 로 읽으면 안 된다
 ★ 리다이렉트가 아니면 res 를 그대로 쓴다 (L251). 그 바이트가 없다
```

## 결과가 쓰이는 곳

```text
 redirectLocation / redirectType
      --> 리듀서가 이 값으로 내비게이션을 일으킨다.
          push 냐 replace 냐가 히스토리 동작을 가른다

 revalidationKind
      --> 클라이언트 캐시를 얼마나 버릴지.
          1 이면 정적·동적 전부, 2 면 동적만, 0 이면 그대로

 actionResult
      --> 액션을 await 한 호출부로 간다.
          [서버 액션] [01]이 거부된 Promise 를 실어 보낸 그 자리의 반대편이다
      ★ 다만 **내부 리다이렉트면 undefined 다** (L264).
        외부 리다이렉트도 undefined (L293)

 actionFlightData
      --> 새 트리를 만드는 재료. 서버가 액션 뒤에 다시 그린 화면이다
      ★ 빌드 ID 가 다르면 **버려진다** (L267-290). 그때는 MPA 내비게이션이 된다

 isPrerender
      --> 받은 Flight 데이터가 프리렌더된 것인지.
          캐시 수명 판단에 쓰인다

 action.didRevalidate  (L356 — **액션 객체를 변조한다**)
      --> 큐가 그것을 읽는다 (app-router-instance.ts L115-128 needsRefresh = true,
          L88-94 에서 flush). 버려진 서버 액션이 **사후에 ACTION_REFRESH 를 일으킨다**
      ★ "리듀서는 상태만 돌려준다" 는 그림과 어긋나는 부수효과다
```

## 다루지 않는 것

`fetchServerAction`(L107-174)의 요청 만들기(헤더 조립 · `next-action` 헤더 · 인자 직렬화)와 L176-182 의 미인식 액션 검사, L261-290 의 응답 적용(트리 병합 · 캐시 갱신 · `useActionState` 전달), `createFromFetch`(`react-server-dom-webpack/client`)의 Flight 디코딩, `processFetch` 가 완성도 표시 바이트를 떼는 방식과 `NEXT_IS_PRERENDER_HEADER`, `assignLocation` 의 URL 해석 규칙, `callServer` / `findSourceMapURL` / `temporaryReferences` / `createDebugChannel`, `getRedirectError`(L42)를 쓰는 자리, `serverActionReducer` 본체가 이 결과로 상태를 갈아끼우는 과정은 이 문서의 범위 밖이다.
