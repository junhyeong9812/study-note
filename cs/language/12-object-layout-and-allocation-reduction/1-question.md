# language/12-object-layout-and-allocation-reduction — 질문

## 질문

1. (그림) JDK 21 HotSpot(압축 참조 켬)에서 `java.lang.Long` 객체 하나의 바이트 배치를 그려라. 왜 24바이트인가? `Integer`는 몇 바이트인가?
2. (예측) `class Order { boolean paid; long amount; int qty; byte status; Object customer; }`의 필드 오프셋은 선언 순서대로인가? 압축 참조를 켰을 때와 껐을 때 인스턴스 크기는?
3. (계산) `List<Long>`(`ArrayList`, 캐시 범위 밖 값) 1천만 개와 `long[]` 1천만 개는 대략 몇 바이트씩인가? 원소당 바이트를 헤더·참조·값으로 나눠 설명하라.
4. (왜) TLAB 할당이 싼 이유는? 그런데도 "할당을 줄이라"고 하는 이유는 무엇인가?
5. (경계) "HotSpot은 탈출하지 않는 객체를 스택에 할당한다"는 말은 어디가 틀렸나? 탈출 분석이 깨지는 대표적인 경우 두 가지는?
6. (예측) `record Point(long x, long y)`를 만들어 바로 계산만 하는 메서드와, 만든 객체를 static 필드에 저장하는 메서드를 각각 1천만 번 불렀다(워밍업 후). 호출당 할당 바이트는 각각 얼마인가? `-XX:-DoEscapeAnalysis`와 `-XX:TieredStopAtLevel=1`에서는?
7. (예측) 요청 객체 50만 개를 풀로 두고 재사용하면서 요청마다 `payload`를 새로 만들어 매단 경우와, 요청 객체도 새로 만든 경우를 G1 1GB 힙으로 비교했다. Young GC 평균 멈춤은 어떻게 갈리나? 그 이유를 카드 테이블과 승격으로 설명하라.
8. (연결) AoS와 SoA는 무엇이고, SoA가 메모리와 지역성에서 유리한 이유를 이 노트와 architecture/11의 결과로 설명하라.
9. (장애 진단) 리팩터링 뒤 기능은 같은데 Young GC 횟수가 두 배가 됐다. 무엇을 의심하고 어떻게 확인하나?
10. (장애 진단) ID 1천만 개를 `Set<Long>`에 올리는 배치가 OOM이 난다. 히스토그램에서 무엇이 보이고, 어떤 순서로 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
