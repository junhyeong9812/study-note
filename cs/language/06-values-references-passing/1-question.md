# language/06-values-references-passing — 질문

## 질문

1. (왜) Java·Python·JS에서 "객체는 참조로 전달된다"는 말이 반만 맞는 이유는? 메서드 안에서 `b.v = 99`와 `b = new Box(7)`이 호출자에게 다르게 보이는 이유를 스택 칸과 힙 객체 그림으로 설명하라.
2. (예측) C++에서 `swap_ptr(int *a, int *b)`가 포인터 변수 `a`, `b`만 바꾸면 호출자의 `i`, `j`는 바뀌나? `swap_ref(int &a, int &b)`는? 원고 §4의 "C 포인터 = 참조에 의한 전달" 서술을 어떻게 고쳐야 하나?
3. (그림) `orig = [Box1, Box2]`에서 `new ArrayList<>(orig)`, `List.copyOf(orig)`, 원소까지 새로 만든 복사를 각각 참조 그래프로 그려라. `shallow.get(0).v = 100`과 `shallow.add(...)` 중 원본에 보이는 것은?
4. (예측) Java에서 `Integer a = 127, b = 127`과 `Integer c = 128, d = 128`의 `==` 결과는? `-XX:AutoBoxCacheMax=1000`을 주면 어떻게 되나? 이 결과에서 얻는 교훈은?
5. (경계) 동일성과 동등성을 정의하고, Java·Python·JS에서 각각 어떤 연산자가 무엇을 보는지 표로 정리하라. JS에서 `NaN === NaN`과 `Object.is(NaN, NaN)`의 차이는?
6. (장애 진단) Python 웹 핸들러의 응답에 앞 요청 사용자의 데이터가 섞인다. 재시작 직후에는 정상이다. 무엇을 의심하고, 어떻게 확인하고, 어떻게 고치나?
7. (연결) 순환 참조가 있는 객체를 깊은 복사하려면 무엇이 필요한가? 이것이 그래프 순회 알고리즘의 어떤 요소와 같은가? Python `copy.deepcopy`는 이를 어떻게 처리하나?
8. (경계) JS에서 깊은 복사로 `JSON.parse(JSON.stringify(o))`와 `structuredClone(o)`를 쓸 때 각각 무엇이 깨지나?
9. (연결) 원고 §6은 `sys.getrefcount("abcde")`가 4294967295인 것을 인터닝 때문이라고 했다. CPython 3.12 기준으로 더 정확한 설명은? 실행 중 만든 `"a" * n`은 왜 다른 값이 나오나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
