# java/syntax/35 — `String`: 불변성·상수 풀·자주 쓰는 메서드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> 선행: [01 기본형과 래퍼](../01-primitives-and-wrappers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 줄의 `==` 를 예측하라 (예측)

```java
String a = "hello";
String b = "hello";
String c = new String("hello");
String d = "hel" + "lo";
String g = new StringBuilder("hel").append("lo").toString();

System.out.println(a == b);
System.out.println(a == c);
System.out.println(a == d);
System.out.println(a == g);
System.out.println(c.equals(a));
System.out.println(c.intern() == a);
```

- 여섯 줄의 출력은 각각 무엇인가?
- `a == d` 가 `true` 인 이유를 바이트코드 명령 하나로 설명할 수 있는가?
- `g` 만 `false` 가 되는 이유는 무엇인가?

### 2. `final` 한 글자가 결과를 뒤집는다 (예측)

```java
static final String PREFIX  = "hel";   // final 있음
static       String DYNAMIC = "hel";   // final 없음

String e = PREFIX  + "lo";
String f = DYNAMIC + "lo";
System.out.println(e == "hello");
System.out.println(f == "hello");
```

- 두 줄의 출력은 각각 무엇인가?
- `final` 하나가 왜 차이를 만드는가 — 명세의 어떤 개념 때문인가?
- `javap -c` 로 두 메서드를 비교하면 무엇이 다른가?
- `f` 를 `e` 와 같은 객체로 만들려면 무엇을 부르는가?

### 3. 이 세 줄 뒤 `u` 는 무엇인가 (예측)

```java
String u = "hello";
u.toUpperCase();
u.replace('l', 'L');
u.concat("!");
System.out.println(u);
System.out.println(u.replace('z', 'Z') == u);
System.out.println(u.substring(0) == u);
```

- 세 줄의 출력은 각각 무엇인가?
- 왜 `u` 가 안 바뀌는가?
- 마지막 두 줄이 `true` 인 이유는 무엇이고, 그것이 안전한 이유는 무엇인가?

### 4. `trim` 과 `strip` 중 무엇이 지우는가 (예측)

```java
// 양끝에 각각 이 문자가 하나씩 붙은 "hi" 에 대해
// U+2003 (em space) · U+0000 (NUL) · U+00A0 (줄바꿈 없는 공백)
```

- 세 문자 각각에 대해 `trim()` 과 `strip()` 중 어느 쪽이 지우는가?
- 둘 다 못 지우는 문자는 무엇인가, 왜인가?
- `trim` 의 판정 기준과 `strip` 의 판정 기준은 각각 무엇인가?
- `isEmpty()` 와 `isBlank()` 는 `" "` 에 대해 각각 무엇을 돌려주는가?

### 5. `split` 결과의 길이 (예측)

```java
"a,b,,c,,".split(",")
"a,b,,c,,".split(",", -1)
"".split(",")
"a.b".split(".")
```

- 네 결과의 **원소와 길이**는 각각 무엇인가?
- 앞쪽 빈 조각과 뒤쪽 빈 조각의 처리가 왜 다른가?
- `"".split(",")` 의 길이가 `0` 이 아닌 것이 왜 위험한가?
- `split(".")` 이 빈 배열을 내는 이유는 무엇인가?

### 6. 이모지가 섞이면 (예측)

```java
String s = "a" + <U+1F600 이모지> + "b";
System.out.println(s.length());
System.out.println(s.codePointCount(0, s.length()));
System.out.println("가나다".length());
System.out.println(s.substring(0, 2));
```

- 네 줄의 출력은 각각 무엇인가?
- `length()` 가 세는 단위의 이름은 무엇인가?
- 한글만으로 테스트하면 왜 이 문제가 안 보이는가?
- `substring` 으로 이모지를 반으로 자르면 예외가 나는가?

### 7. `intern()` 이 보장하는 것 (경계)

- `intern()` 은 자기 자신을 바꾸는가, 새 참조를 돌려주는가?
- `s.intern() == t.intern()` 이 참이 되는 필요충분조건은 무엇인가?
- 이 계약은 어디에 적혀 있는가?
- `intern()` 을 실무에서 쓰는 이유는 무엇이고, 쓰지 말아야 할 이유는 무엇인가?

### 8. 어디까지가 JLS 보장이고 어디부터가 구현인가 (왜)

- 명세가 "같은 인스턴스"를 보장하는 대상은 정확히 무엇인가?
- 그 문장을 인용할 수 있는가?
- 풀이 힙 어디에 있고 크기가 얼마인지는 누가 정하는가, 그것을 어떻게 확인했는가?
- `String` 내부가 `char[]` 가 아니라 `byte[]` 라는 사실은 코드의 동작을 바꾸는가?
- `identityHashCode` 값을 로그 대조에 쓸 수 있는가?

### 9. `switch` 에 `null` 을 넣으면 (경계)

- 어떤 예외가 나는가, 그 메시지에 등장하는 메서드 이름은 무엇인가?
- 소스에 그 메서드가 없는데 왜 나오는가?
- `switch(String)` 은 어떤 두 단계로 컴파일되는가?
- `new String("A")` 를 `switch` 에 넣으면 매치되는가, 왜인가?

### 10. `substring` 의 경계와 버전 (경계)

- `"hello".substring(5)` 는 예외인가 빈 문자열인가?
- `"hello".substring(6)` 과 `"hello".substring(2, 1)` 은 각각 어떤 예외인가?
- 그 예외 메시지는 JDK 17과 21에서 같은가?
- 이 사실이 테스트 코드에 주는 함의는 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- `"Aa".hashCode()` 와 `"BB".hashCode()` 는 같은가, 그것이 왜 정상인가?
- 문자열 상수 풀의 보장과 `Integer` 캐시의 보장은 근거 조항이 어떻게 다른가?
- `"" + 'A' + 'B'` 가 `"AB"` 이고 `'A' + 'B'` 가 `131` 인 이유는 어느 주제의 규칙인가?
- 루프에서 문자열을 이어 붙이면 왜 느린가 — 이 주제의 어떤 성질 때문인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
