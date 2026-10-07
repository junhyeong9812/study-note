# language/18-functional-concepts — 질문

## 질문

1. (왜) 순수 함수와 참조 투명성을 정의하라. `map`·`filter`에 넘기는 함수가 순수해야 라이브러리가 할 수 있게 되는 일 세 가지는?
2. (그림) 영속 리스트 `base = 1,2,3`에서 `a = base.push(10)`, `b = base.push(20)`을 했을 때의 메모리 구조를 그려라. `a.tail() == b.tail()`은? 이 공유가 안전한 조건은?
3. (예측) `Stream.of(1,2,3,4,5).map(…print…).filter(x -> x >= 20).findFirst()`에서 `map`과 `filter`의 출력 순서와 횟수는? 왜 "가로"가 아니라 "세로"로 처리되나?
4. (예측) 같은 `Stream`에 `forEach`를 두 번 하면? 같은 일을 Python 제너레이터(`list(gen)` 두 번)와 JS 제너레이터(`[...it]` 두 번)로 하면? 어느 쪽이 운영에서 더 위험한가?
5. (예측) `List.of(1,2,3).stream().map(x -> { seen.add(x); return x; }).count()` 뒤 `seen`에는 무엇이 있나? 앞에 `filter(x -> true)`를 넣으면? 근거가 되는 API 문서 문장은?
6. (장애 진단) 병렬 스트림으로 바꾼 배치에서 `forEach(out::add)`로 모은 결과 개수가 실행마다 다르다. 원인과 고치는 코드는?
7. (경계) try-with-resources 안에서 `Files.lines(p).filter(…)`를 반환하는 메서드를 호출자가 소비하면 무슨 일이 생기나? 왜 지연 평가 때문인가?
8. (연결) 지연 리스트(SICP 3.5의 delayed list)와 Java `Stream`은 무엇이 같고 무엇이 다른가? 왜 Java `Stream`은 재사용이 금지되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
