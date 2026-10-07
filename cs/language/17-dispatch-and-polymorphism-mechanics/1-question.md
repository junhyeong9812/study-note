# language/17-dispatch-and-polymorphism-mechanics — 질문

## 질문

1. (왜) `Object o = "hello"; f(o);`에서 `f(Object)`와 `f(String)` 중 무엇이 불리나? `Animal a = new Dog(); a.speak()`는 왜 `Dog.speak`인가? 두 결정이 각각 언제, 무엇을 보고 내려지는지 답하라.
2. (예측) `public boolean equals(UserId other)`만 정의한 클래스를 `HashSet`에 넣고 같은 값의 새 객체로 `contains`하면? 직접 `probe.equals(copy)`를 부르면? 이 실수를 컴파일 시점에 잡는 방법은?
3. (예측) `List<Integer> ids = new ArrayList<>(List.of(10, 20, 1)); ids.remove(1);`의 결과는? JLS의 어떤 규칙 때문인가? `javap -c`에서 무엇으로 확인하나?
4. (그림) `Animal`·`Dog`의 vtable을 그리고 `a.speak()` 한 번에 CPU가 하는 일을 세 단계로 적어라. 인터페이스 호출은 무엇이 한 단계 더 드나?
5. (예측) gcc 13 `-O2`로 `int call_virtual(const Shape& x) { return x.area(); }`를 컴파일하면 기계어에 무엇이 나오나? `-fno-devirtualize-speculatively`를 주면? `Sq`가 `final`일 때 `call_final`은?
6. (경계) 단형화(C++ 템플릿·Rust 제네릭)와 Java의 소거된 제네릭은 메서드 호출을 어떻게 다르게 처리하나? 각각의 비용은?
7. (예측) 한 호출 지점에 수신 타입이 1·2·4·8종류 올 때 HotSpot C2의 인라인 판단은 어떻게 달라지나? 실험 C의 ns/call 범위와 `PrintInlining` 출력으로 답하라.
8. (장애 진단) 결제 수단 구현 클래스를 2개 추가한 배포 뒤 수수료 계산 배치만 느려졌다. 무엇을 의심하고, 어떤 JVM 옵션 출력으로 확인하고, 어떤 대처를 고려하나?
9. (연결) HotSpot `compiledIC.hpp` 주석의 Clean → Monomorphic → Megamorphic 전이는 무엇을 뜻하나? 이것이 CPU의 간접 분기 예측과 어떻게 닮았나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
