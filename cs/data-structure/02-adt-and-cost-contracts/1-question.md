# data-structure/02-adt-and-cost-contracts — 질문

## 질문

1. (왜) ADT를 "연산 계약"과 "비용 계약" 두 칸으로 나눠 읽어야 하는 이유는? 컴파일러는 어느 칸만 확인하나?
2. (예측) `for (int i = 0; i < n; i++) s += list.get(i);`를 `ArrayList`와 `LinkedList`에 n = 10,000 → 20,000 → 40,000으로 돌린다. 각각 두 배마다 시간은 몇 배가 되겠나? for-each로 바꾸면?
3. (원리) `LinkedList.get(i)`은 내부에서 무엇을 하나? OpenJDK 21의 `node(int)`가 앞·뒤 중 어디서 출발하는지와, 그래도 `get` 루프 전체가 O(n²)인 이유를 설명하라.
4. (경계) 중간 삽입 `add(size/2, x)`를 n번 할 때와, `ListIterator`로 훑으며 원소마다 `it.add(x)`를 할 때, `ArrayList`와 `LinkedList` 중 각각 어느 쪽이 이기나? 이유는?
5. (연결) `RandomAccess`는 무엇이고, JDK의 `Collections.binarySearch`는 이것을 어떻게 쓰나? 문턱값은?
6. (경계) Javadoc의 `ArrayList.add` "amortized constant time", `TreeMap.get` "guaranteed log(n)", `HashMap.get` "constant-time … assuming the hash function disperses the elements properly"는 각각 어떤 종류의 보장인가?
7. (장애 진단) 운영 JVM의 스레드 덤프 최상단이 `at java.util.LinkedList.node(java.base@21.0.12/LinkedList.java:582)`이고 그 아래 `LinkedList.get` → 우리 코드 `total()`이다. 원인과 고치는 법 두 가지를 대라.
8. (예측) `ArrayDeque`와 `LinkedList`를 큐로 쓸 때 Javadoc은 `ArrayDeque`가 "likely to be faster"라고 한다. 측정하면 항상 그렇게 나오나? 실험 결과로 답하라.
9. (장애 진단) 큐 길이 지표를 `ConcurrentLinkedQueue.size()`로 1초마다 수집했더니 적체가 클수록 시스템이 더 느려지고 숫자도 실제와 달랐다. 왜인가? 대안은?
10. (적용) 두 목록(각 10만 건)의 차집합을 `a.removeAll(b)`로 구했더니 끝나지 않는다. 비용을 계산하고 두 가지 개선안을 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
