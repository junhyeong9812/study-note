# data-structure/29-concurrent-data-structures — 질문

## 질문

1. (왜) 비동기화 `HashMap`에 두 스레드가 동시에 `put`하면 왜 원소가 사라질 수 있나? 시간축으로 그려라. 결과가 "느려짐"이 아니라 "틀림"인 이유는?
2. (예측) 스레드 4개가 서로 다른 정수 키 10만 개씩 비동기화 `HashMap`에 넣는다. 최종 `size()`는? 끝나지 않는 경우도 있다면 스레드 덤프에 무엇이 보이나?
3. (경계) blocking, lock-free, wait-free를 진행 보장으로 구분하라. Michael–Scott 1996 논문의 "lock-free"와 "non-blocking"은 오늘날 용법과 어떻게 다른가? "lock-free면 더 빠르다"는 맞나?
4. (그림) OpenJDK 21 `ConcurrentHashMap`의 `put`은 빈 버킷과 찬 버킷에서 각각 어떻게 동기화하나? `get`은 락을 잡나? 키에 `null`을 넣으면?
5. (예측) `ConcurrentHashMap`에서 스레드 4개가 `m.put(k, m.get(k) + 1)`을 10만 번씩 하면 결과는? `merge(k, 1, Integer::sum)`이면? 차이의 이유는?
6. (그림) Treiber 스택의 pop에서 ABA가 일어나는 시간축을 그려라. Java에서 `AtomicReference`로 만든 스택이 ABA를 겪는 조건과 겪지 않는 조건은? 근거가 된 OpenJDK 소스 주석은?
7. (예측) 같은 ABA 시나리오를 `AtomicStampedReference`로 하면 T1의 CAS는 어떻게 되나? 수정 카운터가 ABA를 "완전히" 막지 못하는 이유(Michael–Scott)는?
8. (경계) `ArrayList` 순회 중 `"b"`를 지우면? 끝에서 두 번째 원소 `"c"`를 지우면? `ConcurrentModificationException`을 정확성 보장에 쓰면 안 되는 이유는?
9. (예측) CPU 2개에서 생산자 2·소비자 2로 `synchronized ArrayDeque`, `LinkedBlockingQueue`, `ArrayBlockingQueue(1024)`, `ConcurrentLinkedQueue`의 처리 시간을 비교하면 순서는? 이 결과에서 일반화하면 안 되는 것은?
10. (장애 진단) 서버 하나가 CPU 한 코어를 100% 쓰며 특정 기능이 응답하지 않는다. 예외 로그는 없다. 무엇을 어떤 순서로 보고, 어떤 스택이면 무엇을 의심하나? 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
