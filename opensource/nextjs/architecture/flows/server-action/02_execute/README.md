# 02 찾아서 실행하기

상위: [서버 액션이 실행되기까지](../README.md)

`try` 블록 497줄(L774-1270)이다. 본문을 디코드해 **어느 함수를 부를지** 알아내고, 그 함수를 부른다. 디코드가 런타임마다 달라 그것만 **364줄**(L792-1155)을 쓴다.

## 위치

`packages/next` / `src/server/app-render` / `action-handler.ts` L774-L1270 ([GitHub](https://github.com/vercel/next.js/blob/a758ffcf501f6f1ddb03175bd1033508424c261e/packages/next/src/server/app-render/action-handler.ts#L774-L1270))

## 실제 코드

찾은 함수를 부르기 직전이 이렇다.

```ts
// action-handler.ts L1172-L1179
        const actionMod = (await ComponentMod.__next_app__.require(
          actionModId
        )) as Record<string, (...args: unknown[]) => Promise<unknown>>
        const actionHandler =
          actionMod[
            // `actionId` must exist if we got here, as otherwise we would have thrown an error above
            actionId!
          ]
```

```text
 L1172  actionMod = await ComponentMod.__next_app__.require(actionModId)
 L1175  actionHandler = actionMod[actionId!]

 => **모듈 객체에서 키로 꺼낸다.** actionId 가 그 모듈의 키다
 ★ 사용자 소스의 export 이름과 같지는 않다 —
   실제 이름은 따로 `actionInfo.exportedName`(L1197 · L1208-1211)으로 읽는다
 주석 L1177 - actionId 는 여기 왔으면 반드시 있다. 없으면 위에서 이미 던졌다
 ★ `ComponentMod.__next_app__.require` 는 [App Router] 흐름의 [02]가
   "전역에 심는다" 고 한 그 번들 require 다. 여기서 쓰인다
```

## 동작 흐름

```text
 ACTION L774-1270

 L775  return await actionAsyncStorage.run({isAction: true}, async () => {
       ★ 액션 실행 문맥을 연다. 안쪽 코드가 "지금 액션 중" 임을 안다

 L779  actionModId (let)
 L780  boundActionArguments: unknown[] = []
 L782  defaultBodySizeLimit = '1 MB'
 L783  bodySizeLimit = serverActions?.bodySizeLimit ?? defaultBodySizeLimit
 L785  bodySizeLimitBytes = ...

 --- 본문 디코드: 런타임 2갈래 + 에러 1 ---
 L792  Edge 이고 isWebNextRequest(req) 이면            (L792-956, 165줄)
 L798    req.body 가 없으면 => throw 'invariant: Missing request body.'
        ...
 L957  Edge 가 아니고 isNodeNextRequest(req) 이면      (L957-1155, 199줄)
        주석 L963 - "Use react-server-dom-webpack/server.node which supports streaming"
        ...
 L1156 아니면
 L1157   => throw new Error('Invariant: Unknown request type.')

 ★ 앞의 둘은 앞에 `process.env.NEXT_RUNTIME` 검사가 붙어 있다
   주석 L793-794 · L958-959 - 타입 검사는 req 를 제대로 좁히려는 것이고,
     환경변수 검사는 **죽은 코드 제거**를 위한 것이다
   => [정적 응답]의 __NEXT_USE_NODE_STREAMS 와 같은 수법이다.
      빌드에서 한쪽이 사라진다

 --- 액션 모듈 찾기 ---
 L1172 actionMod = await ComponentMod.__next_app__.require(actionModId)
 L1175 actionHandler = actionMod[actionId!]

 --- 개발 로그 ---
 L1182 logInfo: ServerActionLogInfo | null = null
 L1183 {type: actionType} = extractInfoFromServerReferenceId(actionId!)
 L1184 (조건) ... logInfo 를 채운다 (L1184-1216)

 --- 실행 ---
 L1218 startTime = performance.now()
 L1219 {actionResult, skipPageRendering} = await executeActionAndPrepareForRender(...)
 L1226   .finally(() => {
 L1227     addRevalidationHeader(res, {workStore, requestStore})
            ★★ **재검증 결과가 여기서 헤더로 나간다.** 성공이든 실패든 붙는다
 L1228     logInfo 가 있으면
 L1230       duration = Math.round(performance.now() - startTime)
 L1231       addRequestMeta(req, 'devServerActionLog', {...})
          })                                                (L1226-1238)

 --- 응답 ---
 L1241 isFetchAction 이면                              (L1241-1262)
 L1245   maybeRevalidatesPromise = skipPageRendering ? executeRevalidates(workStore) : false
 L1251   actionAsyncStorage.**exit**(() => generateFlight(...))
         ★★ 문맥을 **명시적으로 빠져나와** flight 를 렌더한다.
            L775 에서 연 {isAction: true} 를 여기서 닫는다 —
            렌더 중에는 액션 전용 허용(쿠키 쓰기 등)이 없어야 하기 때문으로 보인다
            (※ 뒷문장은 내 해석이다)
 L1263 아니면 ... (L1263-1267)
```

```text
 ★★ 본문 디코드가 런타임마다 다르다 — 그래서 364줄이다

 L792-956   Edge (web)   165줄
 L957-1155  Node         199줄
 L1156      그 밖        throw

 => 같은 일을 두 벌 쓴다. [정적 응답]이 함수를 변수로 올려 피한 그 중복이
    여기서는 그대로 있다
 ※ 스트리밍 지원 여부가 달라 본문이 실제로 다른 것으로 보인다 (내 관찰이다)
   주석 L963 이 Node 쪽만 "supports streaming" 이라고 적는다
```

```text
 ★ 본문 크기 제한이 있다 (L782-785)

   defaultBodySizeLimit = '1 MB'
   bodySizeLimit = serverActions?.bodySizeLimit ?? defaultBodySizeLimit

 => 기본 1MB. `next.config` 의 `serverActions.bodySizeLimit` 으로 바꾼다
 => 액션은 파일 업로드에도 쓰이므로 이 값이 실무에서 자주 걸린다
```

```text
 ★★ finally 가 둘을 한다 (L1218-1238)

   const startTime = performance.now()
   const {...} = await executeActionAndPrepareForRender(...)
     .finally(() => {
       addRevalidationHeader(res, { workStore, requestStore })      ← L1227
       if (logInfo) { const duration = … }                          ← L1228
     })

 => 액션이 던져도 **재검증 헤더는 붙고** 시간도 찍힌다.
    finally 라서 redirect 로 빠져나가는 길에서도 실행된다
 ★ logInfo 조건은 소스에 **명시**돼 있다 (L1184-1190)
     NODE_ENV === 'development' && renderOpts.logServerFunctions
     && actionType !== 'use-cache'      ← `'use cache'` 함수는 로깅에서 빠진다 (TODO)
   L1195  매니페스트에 항목이 없으면 logInfo 자체를 안 만든다
   L1196  인라인 액션은 `<inline action>` 으로 적는다
   L1214  **args: boundActionArguments** — 액션 인자 원본이 그대로 담긴다
          => 개발 로그에 사용자 입력이 실린다
```

## 결과가 쓰이는 곳

```text
 actionResult
      --> isFetchAction 이면 Flight 응답에 실린다.
          아니면(MPA) formState 로 바뀌어 [App Router] L3013 이 받는다

 skipPageRendering
      --> 페이지를 다시 그릴지. 초깃값이 `actionWasForwarded` 다 (L1395).
          전달된 요청이면 처음부터 true — 전달한 워커의 응답으로
          화면을 덮어쓰지 않으려는 것이다 ([README] 참고)
          [01]의 CSRF 거절도 이 값을 true 로 보냈다

 boundActionArguments
      --> 클라이언트가 `.bind()` 로 묶어 보낸 인자들.
          디코드 갈래 둘이 각자 채운다

 actionAsyncStorage 의 {isAction: true}
      --> 액션 안에서 `cookies().set()` 이 허용되는 근거.
          일반 렌더에서는 막힌다
      ★ L1251 의 `actionAsyncStorage.exit(...)` 가 그 문맥을 닫고 flight 를 렌더한다
      ※ 막는 쪽 코드는 확인하지 않았다
```

## 다루지 않는 것

Edge 갈래(L792-956)와 Node 갈래(L957-1155)의 디코드 본문 전체, `decodeReply` / `decodeAction` / `decodeFormState` 등 `react-server-dom-webpack` 의 디코딩 규약, `executeActionAndPrepareForRender`(L1382)의 본문과 `skipPageRendering` 판정, `getActionModIdOrError`(L1443) / `areAllActionIdsValid`(L1479) / `isInvalidStringActionDescriptor`(L1530)의 검증, `extractInfoFromServerReferenceId` 와 액션 ID 형식, `ServerActionLogInfo` 와 개발 로그의 출력 형태, `bodySizeLimit` 을 실제로 적용하는 자리, `actionAsyncStorage` 를 읽는 쪽(`cookies().set()` 허용 판정)은 이 문서의 범위 밖이다.
