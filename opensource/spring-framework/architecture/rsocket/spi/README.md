# spi

상위: [Spring RSocket](../README.md)

요청자 표면, 인코딩 전략, 메타데이터 해석, 매핑 조건, 선언형 클라이언트 애노테이션이다. 앞의 셋은 연결 하나의 설정이고, 뒤의 둘은 매핑과 호출 방식이다.

```text
 보내기
   RSocketRequester    라우트와 데이터를 실어 상호작용을 고른다
   RSocketExchange     선언형 클라이언트 인터페이스의 메서드 애노테이션

 공통 설정
   RSocketStrategies   인코더, 디코더, 라우트 매처, 메타데이터 추출기 묶음
   MetadataExtractor   프레임 메타데이터 --> 헤더 값

 받기
   RSocketFrameTypeMessageCondition  같은 라우트를 프레임 타입으로 가른다
```

## 하위 인터페이스

- [RSocketRequester](RSocketRequester/README.md) — 요청자 표면
- [RSocketStrategies](RSocketStrategies/README.md) — 인코딩과 라우팅 전략 묶음
- [MetadataExtractor](MetadataExtractor/README.md) — 메타데이터 해석
- [RSocketFrameTypeMessageCondition](RSocketFrameTypeMessageCondition/README.md) — 프레임 타입 매핑 조건
- [RSocketExchange](RSocketExchange/README.md) — 선언형 클라이언트 애노테이션
