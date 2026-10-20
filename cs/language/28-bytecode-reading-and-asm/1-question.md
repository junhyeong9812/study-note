# language/28-bytecode-reading-and-asm — 질문

## 질문

1. (왜) 클래스에 붙은 어노테이션을 알고 싶을 때, 프레임워크가 리플렉션 대신 클래스 파일 바이트를 직접 읽는 이유 두 가지는? 각각 어떤 실패·비용을 피하나?
2. (그림) ASM으로 클래스를 읽기만 할 때, 변환할 때, 새로 만들 때 `ClassReader`·`ClassVisitor`·`ClassWriter`가 어떻게 이어지는지 그려라. 이벤트 API와 트리 API는 언제 고르나?
3. (예측) static 블록과 `@Route(handler = OrderHandler.class)`가 붙은 `Heavy`를 컴파일한 뒤 `OrderHandler.class`만 지웠다. ASM으로 읽고 나서 리플렉션으로 `getAnnotation(...).handler()`를 부르면 출력은 어떤 순서로 무엇이 나오나? ASM은 `handler` 값을 어떤 타입으로 주나?
4. (경계) ASM 9.7.1과 9.8로 `--release 25` 클래스를 읽으면 각각 어떻게 되나? Spring 내장 ASM의 `ClassReader` 패치는 이 동작을 어떻게 바꾸고, 그 대가는 무엇일 수 있나?
5. (예측) 같은 디렉터리를 가리키는 `URLClassLoader` 두 개로 `"dep.OrderHandler"`를 각각 로드하면 `c1 == c2`는? `c2.cast(c1 인스턴스)`의 메시지는? 앱 로더로 풀면?
6. (연결) Spring 컴포넌트 스캔이 `ClassPathScanningCandidateComponentProvider`에서 `MergedAnnotation.of(...)`까지 가는 경로를 JDK 17~23과 JDK 24 이상으로 나눠 대라. 스캔 중 로드되는 클래스와 로드되지 않는 것은 각각 무엇인가?
7. (장애 진단) 격리 로더로 스캔한 클래스에서, 직접 붙은 어노테이션의 `Class` 속성은 풀리는데 메타 어노테이션 쪽 같은 속성만 `TypeNotPresentException`이 난다. 원인과 테스트 방법은?
8. (장애 진단) spring-core jar의 클래스를 `Class.forName(name, false, jar만 보는 로더)`로 모두 로드하면 일부가 실패한다. 어떤 오류이고 왜 ASM 스캔은 실패하지 않나? 두 방식의 시간은 어땠나?
9. (경계) `ClassWriter.COMPUTE_FRAMES`를 켜고 변환하다 `TypeNotPresentException`이 났다. ASM이 무엇을 하다가 실패했나? 생성한 클래스를 정의할 로더는 어떻게 고르나?
10. (연결) JEP 484 Class-File API가 생긴 동기는 무엇이고, ASM·Byte Buddy·Javassist·리플렉션 중 무엇을 언제 고르나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
