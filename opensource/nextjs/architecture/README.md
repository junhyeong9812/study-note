# Next.js 아키텍처 지도

소스를 **직접 읽어서** 그린 탑다운 지도다. 지금까지 흐름 세 편, 15개 문서다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e) (2026-09-22). 모든 줄 번호는 이 태그 기준이다.

## 두 갈래로 읽는다

```text
 흐름  무엇이 일어나는가      3편, 15개 문서
       요청 하나가 지나는 길을 메서드 단위로 따라간다
       폴더 하나 = 메서드 하나

 구조  무엇이 있는가          **아직 없다**
       라우트 모듈 · 요청 메타 · 캐시 계층 · 매니페스트처럼 자리에 관한 것
```

API 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 아직 문서가 없는 것도 전부 적어 두었다 — 그 표가 곧 남은 일의 목록이다.

## 흐름 세 편

| 흐름 | 진입점 | 문서 |
|---|---|---|
| [요청이 들어와서 렌더로 가기까지](flows/request-to-render/README.md) | `NextNodeServer.getRequestHandler` L1269 | 6 |
| [응답이 만들어져 나가기까지](flows/response-out/README.md) | `renderToResponseWithComponentsImpl` L2110 | 5 |
| [App Router 가 페이지를 만드는 길](flows/app-render/README.md) | `renderToHTMLOrFlight` L3101 | 4 |

## 흐름이 이어지는 자리

```text
 요청 하나가 지나는 길

 [요청 -> 렌더]   base-server.ts 3195줄
      getRequestHandler -> handleRequest -> handleRequestImpl
      | run -> runImpl
      v
      NEXTSRV handleCatchallRenderRequest   라우트를 고른다
      | this.render(...)  ← **base 로 되돌아온다**
      v
 [응답 나가기]    같은 파일의 뒷 절반
      renderToResponseWithComponentsImpl  플래그 23개를 세운다
      | ComponentMod.handler(req, res, {waitUntil})
      |   ★ 이 사이에 층이 다섯 이상 있고 **응답 캐시가 렌더 여부를 정한다**
      v
 [App Router]     app-render.tsx 10598줄
      renderToHTMLOrFlight -> workAsyncStorage.run -> Impl
      | if (isStaticGeneration)
      +-------------------+
      v                   v
   prerenderToStream   renderToStream        ← 둘 다 **아직 문서 없음**
   (정적 응답)          (동적 응답)
```

```text
 ★ 세 흐름을 꿰는 한 가지 — 반환값이 계약이다

   handleRSCRequest        return 다섯이 **전부 false**  (계약을 안 지킨다)
   handleCatchallRender…   return 일곱이 **전부 true**   ("내가 끝냈다")
   renderPageComponent     false = "내 것이 아니다"      / null = "Edge 로 이미 썼다"
   renderToResponse*       null  = "응답은 이미 나갔다"

 => base-server 가 ResponsePayload 를 실제로 만드는 자리는 **넷뿐**이고
    넷 다 정적이거나 에러다. 평범한 페이지는 라우트 모듈이 직접 쓴다
```

## 읽는 법

```text
 위치          그 코드가 실제로 어디 있는가 (파일·줄·퍼머링크)
 실제 코드     인용. 줄 번호를 붙였다
 동작 흐름     아스키 그림. 왼쪽 숫자가 소스 줄 번호다
 결과가 쓰이는 곳  이 코드가 만든 것을 누가 받는가
 다루지 않는 것    일부러 뺀 것. 다음에 뭘 읽을지의 목록이기도 하다

 표기
   +--   직접 호출
   ~~>   태스크·콜백 경계 (지금 프레임에서 이어지지 않는다)
   =>    갈래의 끝 (return / throw 가 적힌 줄에만 쓴다)
   ★     읽다가 놀란 것
   ※     내 해석이다. 소스가 그렇게 말한 것이 아니다
```

## 아직 안 쓴 것

```text
 A  App Router 의 나머지     server/app-render/        약 28,700줄
      renderToStream 1112 · prerenderToStream 1996 · 검증기계 3800
      create-component-tree 1307 · dynamic-rendering 1592
      action-handler 1580 · collect-segment-data 1528
 B  클라이언트 라우팅·캐시   client/components/        23,345줄
 E  Pages Router             server/render.tsx 외       약 4,000줄
 D  빌드 (webpack 경로)      build/                    62,106줄

 Turbopack(Rust, 294,455줄)은 언어도 도구도 달라 **별도 문서 트리**로 간다
```
