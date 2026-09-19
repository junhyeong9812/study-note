# spi

상위: [Spring 함수형 엔드포인트](../README.md)

함수형 엔드포인트가 기대는 계약 인터페이스 모음이다. 여섯 개 모두 서블릿 스택과 리액티브 스택에 같은 이름으로 하나씩 있다. 라우터, 핸들러, 조건은 반환 타입만 다르고(`Optional`/`T` 대 `Mono`), 요청과 응답은 표면 자체가 다르다(서블릿은 `servletRequest()`와 `ModelAndView`, 리액티브는 `exchange()`와 `Mono<Void>`).

```text
 라우팅
   RouterFunction      요청 --> 핸들러 함수 (없으면 빈 값)
   RequestPredicate    요청이 이 라우트에 해당하는가

 처리
   HandlerFunction     요청 --> 응답
   HandlerFilterFunction  핸들러를 감싸 앞뒤에 일을 끼운다

 입출력
   ServerRequest       요청 읽기 표면
   ServerResponse      응답 쓰기 표면 (값이 아니라 쓰는 방법)
```

## 하위 인터페이스

- [RouterFunction](RouterFunction/README.md) — 라우팅 함수와 합성 규칙
- [RequestPredicate](RequestPredicate/README.md) — 라우트 조건
- [HandlerFunction](HandlerFunction/README.md) — 요청 처리 함수
- [HandlerFilterFunction](HandlerFilterFunction/README.md) — 핸들러 필터
- [ServerRequest](ServerRequest/README.md) — 요청 읽기
- [ServerResponse](ServerResponse/README.md) — 응답 쓰기
