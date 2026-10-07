# language/05-type-systems — 질문

## 질문

1. (왜) "동적 타입 언어는 타입이 없다"는 말은 왜 틀렸나? Python의 `"1" + 1`과 JS의 `"1" + 1`이 다르게 끝나는 것을 두 축(검사 시점, 암묵 변환)으로 설명하라.
2. (예측) C에서 `int n = -1; if (n < sizeof(int)) …`은 참인가 거짓인가? 그 이유와, 이것이 UB인지 정의된 동작인지 답하라. 어떤 컴파일 경고가 잡아 주나?
3. (경계) 명목적 타입과 구조적 타입을 정의하라. `read()` 메서드만 가진 클래스를 `Reader` 인터페이스 변수에 넣으면 Java와 Go는 각각 어떻게 하나? 구조적 타입에서 생기는 함정 하나와 막는 법은?
4. (그림) `List<String> names`에 원시 타입 경유로 정수 42를 넣은 뒤 `String s = names.get(0)`을 하면 어디서 무엇이 실패하나? `javap -c`에서 어떤 명령이 실패 지점인지, 왜 넣을 때는 실패하지 않는지 그려라.
5. (예측) `new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass()`의 결과는? 그렇다면 `javap -v`의 `Signature` 속성에 남은 `List<String>`은 무엇에 쓰이나?
6. (경계) 배열은 공변, 제네릭은 무공변이다. 각각 잘못된 쓰기를 언제(컴파일/실행) 어떤 형태로 막나? 왜 제네릭은 배열처럼 실행 중 검사를 할 수 없나?
7. (계산) `\f. \x. f (f x)`의 타입을 단일화로 구하라. 그리고 `(\id. id id) (\x.x)`가 거부되는데 `let id = \x.x in id id`는 통과하는 이유를 설명하라.
8. (장애 진단) 운영에서 `ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String`이 집계 루프 줄에서 났다. 원인 위치를 찾는 순서와 도구(컴파일 옵션, 런타임 래퍼)를 대라.
9. (연결) TypeScript 타입 검사를 통과한 코드가 실행 중 외부 JSON 때문에 `undefined` 접근으로 죽었다. 타입 소거라는 점에서 Java 제네릭과 무엇이 같고, 대처는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
