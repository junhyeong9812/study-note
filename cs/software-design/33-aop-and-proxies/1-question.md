# software-design/33-aop-and-proxies — 질문

## 질문

1. (왜) 트랜잭션·로깅·권한 검사를 메서드마다 직접 쓰면 어떤 두 가지 증상이 생기나? AOP는 이것을 어떻게 한 곳으로 모으나?
2. (그림) JDK 동적 프록시와 CGLIB 프록시의 구조를 그려라. Spring Framework 6.2는 둘 중 무엇을 어떤 조건으로 고르고, Spring Boot의 기본은 무엇인가?
3. (예측) 인터페이스 `Greeter`를 구현한 `GreeterImpl` 빈에 애스펙트가 걸려 있다. `@EnableAspectJAutoProxy` 기본 설정에서 `ctx.getBean(GreeterImpl.class)`와 `ctx.getBean("greeter", GreeterImpl.class)`는 각각 어떻게 되나?
4. (예측) CGLIB 프록시 빈에서 `outer()`가 `this.inner()`를 부른다. `inner()`에만 어드바이스가 걸려 있을 때 `proxy.inner()`와 `proxy.outer()`의 출력은 어떻게 다른가?
5. (예측) 생성자 주입을 받는 CGLIB 프록시 대상의 `final` 메서드에 어드바이스를 걸고 호출했다. 무엇이 일어나고 왜 그런가? 클래스 자체가 `final`이면?
6. (경계) 재시도 애스펙트와 트랜잭션 애스펙트의 `@Order`를 (1, 2)와 (2, 1)로 바꿔 보았다. 각각 트랜잭션은 몇 번 열리나? 실제 DB라면 두 번째 경우에 어떤 문제가 생길 수 있나?
7. (연결) TS 표준 데코레이터 `@tx @retry pay()`에서 어느 쪽이 바깥인가? 같은 클래스 안 `this.inner()`에 붙은 데코레이터는 실행되나? Spring AOP와 왜 다른가?
8. (장애 진단) 운영에서 "특정 메서드만 캐시가 안 걸리고, 가끔 그 메서드에서 주입 필드가 null이라는 NPE가 난다"는 보고가 왔다. 의심할 원인과 확인 방법, 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
