# Next.js 아키텍처 지도

Next.js 소스를 위에서 아래로 훑는 지도다. 메서드 하나가 폴더 하나이고, 폴더마다 그 메서드의 위치 · 실제 코드 · 동작 흐름 · 결과가 쓰이는 곳을 적는다.

기준 태그: `v16.3.6` [`a758ffcf50`](https://github.com/vercel/next.js/tree/a758ffcf501f6f1ddb03175bd1033508424c261e).

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

## 흐름

1. [요청이 들어와서 렌더로 가기까지](flows/request-to-render/README.md) — `base-server.ts` 3195줄. 서버의 척추다.

## 아직 안 쓴 것

```text
 A  App Router / RSC        server/app-render/        29,527줄
 B  클라이언트 라우팅·캐시   client/components/        23,345줄
 E  Pages Router            server/render.tsx 외       약 4,000줄
 D  빌드 (webpack 경로)      build/                    62,106줄

 Turbopack(Rust, 294,455줄)은 언어도 도구도 달라 **별도 문서 트리**로 간다
```
