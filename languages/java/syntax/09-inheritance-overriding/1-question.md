# java/syntax/09 — 상속과 오버라이딩: 동적 디스패치·공변 반환·필드 숨김 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **어느 구현이 도는지**를 맞힐 수 있는지 묻는다.
> 선행: [08 메서드 선언 — 오버로딩 해소](../08-method-declaration-overloading/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 변수, 다섯 줄, 네 가지 규칙 (예측)

```java
class Super {
    String field = "Super.field";
    String instanceM() { return "Super.instanceM"; }
    static String staticM() { return "Super.staticM"; }
    private String privateM() { return "Super.privateM"; }
    String callPrivate() { return privateM(); }
}
class Sub extends Super {
    String field = "Sub.field";
    @Override String instanceM() { return "Sub.instanceM"; }
    static String staticM() { return "Sub.staticM"; }
    private String privateM() { return "Sub.privateM"; }
}
// main:
Super s = new Sub();
// s.field / s.instanceM() / s.staticM() / s.callPrivate() / ((Sub) s).field
```

- 다섯 줄의 출력은 각각 무엇인가?
- 네 가지(필드·인스턴스 메서드·`static`·`private`) 중 **런타임에 정해지는 것**은 몇 개인가?
- `javap -c` 로 `main` 을 열면 `s.staticM()` 자리에 `aload_1` 다음 무슨 명령이 있는가, 그것이 무슨 뜻인가?
- 마지막 줄의 캐스트가 무엇을 바꾸는가?

### 2. 같은 `invokevirtual` 인데 왜 갈리나 (왜)

- 상수 풀에 박히는 시그니처는 `Super.instanceM` 인데 실제로 도는 것은 `Sub.instanceM` 이다 — 어떻게 가능한가?
- 컴파일러가 하는 일과 JVM 이 하는 일을 한 문장씩으로 나누면 무엇인가?
- 필드에는 왜 같은 일이 안 일어나는가?

### 3. `private` 메서드와 상속 (경계)

- `Super.callPrivate()` 가 `Sub` 인스턴스에 대해 `Super.privateM` 을 주는 이유는 무엇인가?
- `javap -c -p Super` 에서 그 호출의 명령은 무엇인가? (JDK 21 기준)
- `javac --release 8` 로 같은 코드를 컴파일하면 그 명령이 바뀌는가?
- 바뀐다면, 그때 **동작도 바뀌는가**?

### 4. 공변 반환과 브리지 메서드 (예측)

```java
class Animal { }
class Dog extends Animal { }
class Shelter    { Animal adopt() { return new Animal(); } }
class DogShelter extends Shelter {
    @Override Dog adopt() { return new Dog(); }
}
```

- 소스의 `DogShelter` 에는 `adopt` 가 하나인데 `javap -c -p` 에는 몇 개가 보이는가?
- 두 번째 것의 본문은 무엇을 하는가?
- `javap -v -p` 에서 그 메서드의 플래그는 무엇인가?
- 왜 이것이 필요한가 — JVM 수준에서 오버라이딩의 조건은 무엇인가?

### 5. `super.` 와 캐스트 (예측)

```java
class Sup { String name() { return "Sup"; } }
class Sub extends Sup {
    @Override String name() { return "Sub"; }
    String viaSuper() { return super.name(); }
    String viaCast()  { return ((Sup) this).name(); }
}
```

- `viaSuper()` 와 `viaCast()` 는 각각 무엇을 돌려주는가?
- `javap -c -p Sub` 에서 두 메서드의 **대상**과 **명령**은 각각 무엇인가?
- "상위 구현을 쓰고 싶다"에 캐스트가 안 되는 이유를 한 문장으로 말하면?

### 6. 재정의한 줄 알았는데 (예측)

```java
class Sup { String render(Object o) { return "sup"; } }
class Sub extends Sup {
    String render(String s) { return "sub"; }
}
// main: Sup x = new Sub();  x.render("a");
```

- 출력은 무엇인가?
- 컴파일 경고가 나는가?
- `@Override` 를 달면 어떻게 되는가, 에러 문구는 무엇인가?
- 이 사고를 통째로 없애는 습관 하나는 무엇인가?

### 7. `equals` 오버로딩 사고 (예측)

```java
class Sup { boolean equals(Sup other) { return true; } }
// main: Sup p = new Sup(), q = new Sup();  Object op = p, oq = q;
// p.equals(q) / op.equals(oq)
```

- 두 줄의 출력은 각각 무엇인가?
- 왜 `HashMap`·`List.contains` 에서 문제가 되는가?
- 파라미터를 `Object` 로 고치고 `@Override` 를 달면 **또 다른 에러**가 나온다 — 무엇인가?

### 8. 오버라이딩의 다섯 조건 (경계)

- 반환형을 좁혀도 되는가, 넓혀도 되는가?
- 접근 수준은 어느 방향으로만 바꿀 수 있는가?
- 검사 예외는 어느 방향으로만 바꿀 수 있는가?
- 이 세 규칙이 공통으로 지키려는 원칙은 무엇인가?
- `final`·`static` 메서드를 재정의하려 하면 각각 무슨 에러가 나오는가?

### 9. 필드 숨김이 만드는 사고 (왜)

- 상위와 하위가 같은 이름의 필드를 선언하면 객체 안에 저장소가 몇 개 생기는가?
- 부모 클래스가 쓴 코드와 자식 클래스가 쓴 코드는 각각 어느 쪽을 읽는가?
- 컴파일러가 경고를 주는가?
- `@Override` 같은 안전장치가 필드에도 있는가, 없다면 무엇으로 방어하는가?

### 10. `static` 메서드를 인스턴스 참조로 부르면 (경계)

- `s.staticM()` 이 컴파일되는가?
- 바이트코드에서 `s` 는 어떻게 되는가?
- 왜 이 표기를 쓰면 안 되는가?

### 11. 오버로딩과 오버라이딩 (연결)

- 무엇이 컴파일 타임에 정해지고 무엇이 런타임에 정해지는가?
- 각각 무엇을 보고 고르는가?
- 시그니처는 서로 같은가 다른가?
- 클래스 파일에 남는 것은 각각 무엇인가?

### 12. 정본 경계 (연결)

- 다형성·상속이 **무엇인가**는 어느 문서가 정본인가?
- 그 문서에 **없는** 것 셋을 이 주제에서 들 수 있는가?
- 가상 호출의 JIT 최적화는 어디를 보는가?
- `equals` 계약 자체는 어느 주제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
