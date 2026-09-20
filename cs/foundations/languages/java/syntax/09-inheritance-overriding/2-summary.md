# java/syntax/09 — 상속과 오버라이딩: 동적 디스패치·공변 반환·필드 숨김 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §8.4.8 Inheritance, Overriding, and Hiding](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.3.1.1 Field Hiding](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§15.12.4 Run-Time Evaluation of Method Invocation](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · [JVMS SE 21 §6.5 invokevirtual](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html)
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.
> **버전** — 오버라이딩·필드 숨김 규칙은 Java 1.0 이래 같다. 공변 반환은 **Java 5** 부터.\
> **`private` 메서드 호출 명령은 컴파일 대상 버전에 따라 갈린다**(아래 「구현 세부사항 대 언어 보장」).
> **범위** — 다형성·상속이 **무엇인가**는 [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이다.\
> 여기는 **Java 가 그것을 어떤 규칙으로 강제하고, 어디서 강제하지 않나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**메서드는 전화번호부이고, 필드는 문패다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물 | 객체 |
| 건물의 실제 용도 | 런타임 타입 |
| 지도에 적힌 용도 | 선언 타입(변수의 타입) |
| 대표 전화로 걸면 **지금 그 건물에 있는 사람**이 받는다 | 메서드 — 동적 디스패치 |
| 지도에 적힌 문패를 읽으면 **지도에 적힌 것**이 나온다 | 필드 — 정적 접근 |
| 내선 번호(대표 전화를 안 거치는 직통) | `private` · `static` · `final` |

- 대표 전화번호는 **하나**다. 그런데 받는 사람은 그때그때 다르다.\
  바이트코드에 남는 `invokevirtual` 이 대표 전화번호이고, 실제로 도는 코드는 런타임에 정해진다.
- 문패는 **지도에서 읽는다.** 건물에 가지 않는다.\
  그래서 `Super s = new Sub(); s.field` 는 **`Super` 의 필드**를 준다.
- 이 비대칭이 이 주제의 전부다 — **같은 한 줄 안에서 메서드는 동적, 필드는 정적**이다.

```text
Super s = new Sub();   // 선언 타입 Super, 런타임 타입 Sub

  s.field         -> getfield Super.field        지도를 읽는다      -> "Super.field"
  s.instanceM()   -> invokevirtual Super.instanceM
                       |                          대표 전화를 건다
                       +-- 런타임에 Sub 의 구현으로 간다             -> "Sub.instanceM"
  s.staticM()     -> invokestatic Super.staticM  내선 직통          -> "Super.staticM"
```

**똑같은 구조로** Java 가 이렇게 동작한다: 지도 = 컴파일 타임 타입, 건물 = 힙의 객체, 대표 전화 = `invokevirtual`.

실무에서 이게 물리는 자리는 **필드를 `protected` 로 열어 두고 하위 클래스에서 같은 이름으로 다시 선언**할 때다.\
컴파일도 되고 경고도 없는데, 부모 코드가 읽는 필드와 자식 코드가 읽는 필드가 **서로 다른 저장소**가 된다.

> **동적 디스패치(dynamic dispatch)** — 어느 구현을 부를지 **런타임 타입**으로 고르는 것.\
> 예: `Object o = new ArrayList<>(); o.toString()` 은 `ArrayList` 의 `toString` 이 돈다.

> **필드 숨김(field hiding)** — 하위 클래스가 상위 클래스와 **같은 이름의 필드**를 다시 선언하는 것.\
> 예: 상위와 하위가 각각 `String name` 을 선언하면 **저장소가 둘** 생기고, 어느 쪽을 읽을지는 선언 타입이 정한다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 같은 `s.x` 라는 표기에서 **메서드와 필드가 왜 다르게 동작하는가.**
2. 무엇이 오버라이딩이고 무엇이 아닌가 — `static`·`private`·`final` 은 왜 빠지는가.
3. 오버라이딩에 **컴파일러가 거는 조건**은 무엇이고, `@Override` 는 그중 무엇을 잡아 주는가.

## 동작 방식

### (1) 한 프로그램 안에서 네 가지가 갈린다

**언제 쓰나** — 상위 타입 변수로 하위 객체를 다룰 때.

```java
class Super {
    String field = "Super.field";
    String instanceM() { return "Super.instanceM"; }
    static String staticM() { return "Super.staticM"; }
    private String privateM() { return "Super.privateM"; }
    String callPrivate() { return privateM(); }
}
class Sub extends Super {
    String field = "Sub.field";                        // 숨김 (hiding)
    @Override String instanceM() { return "Sub.instanceM"; }
    static String staticM() { return "Sub.staticM"; }  // 숨김
    private String privateM() { return "Sub.privateM"; }
}
// main: Super s = new Sub();
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
s.field         = Super.field
s.instanceM()   = Sub.instanceM
s.staticM()     = Super.staticM
s.callPrivate() = Super.privateM
((Sub) s).field = Sub.field
```

```text
javap -c Ex 의 main — 출력 그대로 (같은 변수 s 에 대한 다섯 줄)

      12: getfield      #16                 // Field Super.field:Ljava/lang/String;       <- 선언 타입으로 박힘
      27: invokevirtual #32                 // Method Super.instanceM:()Ljava/lang/String; <- 선언 타입으로 박히지만 런타임에 갈림
      41: aload_1
      42: pop                                                                              <- 객체를 꺼내서 버린다
      43: invokestatic  #37                 // Method Super.staticM:()Ljava/lang/String;   <- 객체와 무관
      58: invokevirtual #41                 // Method Super.callPrivate:()Ljava/lang/String;
      73: checkcast     #7                  // class Sub
      76: getfield      #45                 // Field Sub.field:Ljava/lang/String;          <- 캐스트가 필드를 바꾼다
```

그림 해설 (한 단계씩):

- **필드** — `getfield Super.field` 가 박힌다. 런타임에 바뀌지 않는다.\
  객체 안에는 `Super.field` 와 `Sub.field` 가 **둘 다** 있고, 어느 쪽을 읽을지는 컴파일러가 정한다.
- **인스턴스 메서드** — 상수 풀에는 `Super.instanceM` 이 박히는데 **실행 결과는 `Sub.instanceM`** 이다.\
  `invokevirtual` 이 런타임 타입으로 다시 찾는다. 이것이 동적 디스패치다.
- **`static` 메서드** — `aload_1; pop` 이 압권이다.\
  `s` 를 스택에 올렸다가 **그냥 버린다.** 객체는 평가되지만 쓰이지 않는다.
- **캐스트** — `checkcast Sub` 다음의 `getfield Sub.field`.\
  **캐스트 한 번이 읽는 필드를 바꾼다.** 메서드였다면 아무것도 안 바뀐다.

비용 — `getfield`/`invokestatic` 은 고정 오프셋. `invokevirtual` 은 vtable 한 번 더 타지만,\
JIT 가 단형(monomorphic) 호출을 인라인한다. 그 최적화는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 의 영역이다.

### (2) `private` 은 오버라이드되지 않는다 — 부모는 자기 것을 본다

**언제 쓰나** — 하위 클래스에 같은 이름의 `private` 메서드가 있을 때.

`Super.callPrivate()` 는 `Sub` 인스턴스에 대해서도 **`Super.privateM`** 을 돌려준다.

```text
javap -c -p Super  (JDK 21.0.5) — callPrivate 부분 그대로

  java.lang.String callPrivate();
    Code:
       0: aload_0
       1: invokevirtual #21                 // Method privateM:()Ljava/lang/String;
       4: areturn
```

그림 해설 (한 단계씩):

- 대상이 **`Super.privateM`** 으로 고정돼 있다(클래스 이름이 생략된 것은 같은 클래스라는 뜻이다).
- `Sub.privateM` 은 **후보에 아예 없다.** `private` 멤버는 하위 클래스에 상속되지 않기 때문이다.
- 그래서 둘은 **이름만 같은 남남**이다 — 오버라이딩이 아니다.
- ★ 명령이 `invokevirtual` 인데도 디스패치가 안 일어난다. 그 이유는 아래 「구현 세부사항」 절에 있다.

비용 — 없음. 실질적으로 정적 바인딩이다.

### (3) 공변 반환 — 컴파일러가 다리(bridge)를 놓는다

**언제 쓰나** — 하위 클래스가 더 구체적인 타입을 반환하고 싶을 때.

```java
class Animal { }
class Dog extends Animal { }

class Shelter    { Animal adopt() { return new Animal(); } }
class DogShelter extends Shelter {
    @Override Dog adopt() { return new Dog(); }    // 공변 반환
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Dog / Dog
```

```text
javap -c -p DogShelter — 출력 그대로. adopt 가 두 개다

  Dog adopt();
    Code:
       0: new           #7                  // class Dog
       3: dup
       4: invokespecial #9                  // Method Dog."<init>":()V
       7: areturn

  Animal adopt();
    Code:
       0: aload_0
       1: invokevirtual #10                 // Method adopt:()LDog;     <- 자기 자신을 다시 부른다
       4: areturn
```

```text
javap -v -p DogShelter 에서 두 번째 adopt 의 플래그

  Animal adopt();
    descriptor: ()LAnimal;
    flags: (0x1040) ACC_BRIDGE, ACC_SYNTHETIC
```

그림 해설 (한 단계씩):

- 소스에는 `adopt()` 가 **하나**인데 클래스 파일에는 **둘**이다.
- 두 번째 것은 `ACC_BRIDGE, ACC_SYNTHETIC` — **컴파일러가 만든 다리 메서드**다.
- 이유: JVM 수준에서 오버라이딩은 **반환형까지 포함한 디스크립터가 같아야** 성립한다.\
  `()LAnimal;` 와 `()LDog;` 는 다른 메서드다.
- 그래서 `Shelter s = new DogShelter(); s.adopt()` 는 `()LAnimal;` 를 부르고,\
  그 브리지가 다시 진짜 `()LDog;` 를 부른다. **호출이 한 번 더 있다.**

비용 — 호출 한 겹. JIT 가 대개 인라인한다.

> **브리지 메서드(bridge method)** — 컴파일러가 디스크립터를 맞추려고 만드는 숨은 메서드.\
> 예: 공변 반환과 제네릭 소거에서 생긴다. `javap -v` 의 `ACC_BRIDGE` 플래그로 알아본다.

### (4) `super.m()` 은 디스패치를 끈다

**언제 쓰나** — 재정의한 메서드 안에서 원래 구현을 쓸 때.

```java
class Sup { String name() { return "Sup"; } }
class Sub extends Sup {
    @Override String name() { return "Sub(위에는 " + super.name() + ")"; }
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Sub(위에는 Sup)
```

```text
javap -c -p Sub — 출력 그대로

  java.lang.String name();
    Code:
       0: aload_0
       1: invokespecial #7                  // Method Sup.name:()Ljava/lang/String;
       4: invokedynamic #11,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
       9: areturn
```

그림 해설 (한 단계씩):

- `super.name()` 은 **`invokespecial`** 이다 — `invokevirtual` 이 아니다.
- `invokespecial` 은 대상이 컴파일 타임에 고정된다. 그래서 재정의한 메서드 안에서 불러도 무한 재귀가 안 난다.
- 즉 `super.` 는 "**한 칸 위를 정확히 지목한다**"는 뜻이지, "부모 타입으로 캐스트한다"가 아니다.

★ **캐스트로는 디스패치를 못 끈다.** 같은 클래스에 둘을 나란히 두고 확인했다.

```java
class Sub extends Sup {
    @Override String name() { return "Sub"; }
    String viaSuper() { return super.name(); }
    String viaCast()  { return ((Sup) this).name(); }
}
```

```text
실행 결과 (Ex.java, JDK 21.0.5)
super.name()        = Sup
((Sup) this).name() = Sub
```

```text
javap -c -p Sub — 상수 풀 항목(#9)은 같은데 명령이 다르다

  java.lang.String viaSuper();
       0: aload_0
       1: invokespecial #9                  // Method Sup.name:()Ljava/lang/String;
       4: areturn

  java.lang.String viaCast();
       0: aload_0
       1: invokevirtual #9                  // Method Sup.name:()Ljava/lang/String;
       4: areturn
```

- **대상은 둘 다 `Sup.name`** 인데 결과가 갈린다. 명령 하나가 전부를 결정한다.
- 그래서 "상위 구현을 쓰고 싶다"에 캐스트를 쓰면 **아무 효과가 없다.** `super.` 만 된다.

비용 — 정적 바인딩이라 `invokevirtual` 보다 싸다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 오버라이딩의 조건 — 전부 컴파일러가 검사한다

```java
class Sup { protected Number get() throws java.io.IOException { return 1; } }
class Sub extends Sup {
    @Override public Integer get() { return 2; }   // 넓히기 O, 공변 반환 O, 예외 줄이기 O
}
```

| 조건 | 규칙 |
|---|---|
| 이름 + 파라미터 타입 | **똑같아야** 한다(다르면 오버로딩) |
| 반환형 | 같거나 **하위 타입**(공변 반환, Java 5+) |
| 접근 수준 | 같거나 **넓게**만. 좁히면 에러 |
| 검사 예외 | 같거나 **줄이기**만. 넓히면 에러 |
| `final` 메서드 | 재정의 **불가** |
| `static` 메서드 | 재정의가 아니라 **숨김**(hiding) |
| `private` 메서드 | 상속되지 않음 — **관계 없음** |

### 오버라이딩이 아닌 것 셋

| 무엇 | 실제로 일어나는 일 | 어떻게 고르나 |
|---|---|---|
| 같은 이름의 **필드** | 숨김 — 저장소가 둘 | **선언 타입** |
| 같은 이름의 **`static` 메서드** | 숨김 | **선언 타입** |
| 같은 이름의 **`private` 메서드** | 아무 관계 없음 | 그 클래스 안에서만 보임 |

### `@Override` 가 하는 일

- **아무 동작도 바꾸지 않는다.** 컴파일 타임 검사 하나를 켤 뿐이다.
- 검사 내용: "이 메서드가 정말 상위 타입의 무언가를 재정의하는가?"
- 인터페이스 구현에도 붙일 수 있다(Java 6+).

## 어디서 틀리나

### 1. 오버라이딩인 줄 알았는데 오버로딩이었다

```java
class Sup { String render(Object o) { return "sup"; } }
class Sub extends Sup {
    String render(String s) { return "sub"; }            // @Override 를 안 달았다
}
// main: Sup x = new Sub();  x.render("a");
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
x.render("a") = sup
```

- **에러도 경고도 없다.** 그냥 부모 것이 돈다.
- 파라미터 타입이 다르므로 **오버로딩**이고, `x` 의 선언 타입이 `Sup` 이라 `render(Object)` 가 뽑힌다(08 편).
- `@Override` 를 달면 그 자리에서 멈춘다.

  ```text
  Ex.java:3: error: method does not override or implement a method from a supertype
      @Override String render(String s) { return "sub"; }   // 파라미터 타입이 다르다
      ^
  1 error
  ```

- **방어: 재정의 의도가 있으면 무조건 `@Override` 를 단다.** 비용이 0이고 이 사고를 통째로 없앤다.

### 2. `equals` 를 오버로딩해 버린다 — 1번의 실전판

```java
class Sup { boolean equals(Sup other) { return true; } }   // Object.equals 재정의가 아니다
// main: Sup p = new Sup(), q = new Sup();  Object op = p, oq = q;
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
p.equals(q)   = true
op.equals(oq) = false
```

- **내 테스트는 통과하고 컬렉션은 틀린다.**\
  `List.contains`·`HashMap` 은 전부 `Object` 타입 참조로 부르므로 `Object.equals` 가 돈다.
- 계약 쪽 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 다.\
  여기서 말하는 것은 **그 사고의 원인이 오버라이딩 규칙이라는 것**이다 — 파라미터 타입이 다르면 재정의가 아니다.
- 그리고 `@Override` 를 달면 **또 다른 에러**가 나온다 — 접근 수준이다.

  ```text
  Ex.java:1: error: equals(Object) in Sup cannot override equals(Object) in Object
  class Sup { boolean equals(Object o) { return true; } }
                      ^
    attempting to assign weaker access privileges; was public
  ```

  `Object.equals` 는 `public` 이므로 package-private 으로 좁힐 수 없다.

### 3. 필드를 같은 이름으로 다시 선언한다

동작 방식 (1)의 `s.field` 가 그것이다.

```text
힙의 객체 하나 (new Sub())            읽는 쪽
+---------------------------+       Super s = ...;   s.field         -> "Super.field"
| Super.field = "Super..."  |  <----+
| Sub.field   = "Sub..."    |  <----+
+---------------------------+       Sub   t = ...;   t.field         -> "Sub.field"
   저장소가 둘 다 있다                       ((Sub) s).field          -> "Sub.field"
```

- **저장소가 둘**이다. 하나가 다른 하나를 덮는 게 아니다.
- 부모 클래스가 쓴 코드는 `Super.field` 를, 자식이 쓴 코드는 `Sub.field` 를 본다.\
  **같은 객체인데 두 코드가 다른 값을 본다.**
- 컴파일 경고가 **없다.** `@Override` 같은 안전장치도 필드에는 없다.
- 방어: 필드는 `private` 으로 두고 접근자를 재정의한다. `protected` 필드가 이 사고의 전제 조건이다.

### 4. `static` 메서드를 재정의했다고 믿는다

```java
class Sup { static String who() { return "sup"; } }
class Sub extends Sup { String who() { return "sub"; } }   // static 을 인스턴스로
```

```text
Ex.java:2: error: who() in Sub cannot override who() in Sup
class Sub extends Sup { String who() { return "sub"; } }   // static 을 인스턴스로
                               ^
  overridden method is static
1 error
```

`@Override` 를 `static` 에 붙이면 그것도 막힌다.

```text
Ex.java:2: error: static methods cannot be annotated with @Override
class Sub extends Sup { @Override static String who() { return "sub"; } }
                        ^
1 error
```

- 둘 다 `static` 으로 두면 **숨김**이 되고, 이것은 **컴파일된다.**\
  그리고 동작 방식 (1)에서 봤듯 **선언 타입**으로 고른다 — `s.staticM()` 이 `Super.staticM` 이었다.
- ★ 그래서 `인스턴스변수.static메서드()` 라고 쓰면 안 된다. 객체가 평가되고 버려진다(`aload_1; pop`).

### 5. 접근을 좁히거나 예외를 넓힌다

```text
Ex.java:2: error: name() in Sub cannot override name() in Sup
class Sub extends Sup { protected String name() { return "sub"; } }
                                         ^
  attempting to assign weaker access privileges; was public
1 error
```

```text
Ex.java:3: error: run() in Sub cannot override run() in Sup
class Sub extends Sup { @Override void run() throws Exception { } }
                                       ^
  overridden method does not throw Exception
1 error
```

```text
Ex.java:2: error: name() in Sub cannot override name() in Sup
class Sub extends Sup { String name() { return "sub"; } }
                               ^
  overridden method is final
1 error
```

- 셋 다 **리스코프 치환 원칙**을 컴파일러가 강제하는 것이다.\
  상위 타입으로 쓰던 코드가 하위 타입을 넣었을 때 깨지면 안 된다.
- 접근을 **넓히는** 것은 된다(`protected` → `public`).
- 예외를 **줄이는** 것도 된다(`throws IOException` → `throws` 없음).

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 인스턴스 메서드가 **런타임 타입**으로 디스패치되는 것 | **언어 보장** — JLS §15.12.4 |
| 필드·`static` 메서드가 **선언 타입**으로 결정되는 것 | **언어 보장** — JLS §8.3.1.1, §8.4.8.2 |
| `private` 메서드가 상속되지 않는 것 | **언어 보장** — JLS §8.2 |
| 공변 반환에 브리지 메서드가 생기는 것 | **구현 세부** — 결과(디스패치)는 언어 보장, **브리지라는 수단**은 javac 의 선택 |
| **`private` 메서드 호출 명령** | ★ **구현 세부** — 아래 표를 보라 |

★ **`private` 호출 명령은 컴파일 대상 버전에 따라 갈린다.**

```text
$ javac Ex.java          (JDK 17.0.13 / 21.0.5 / 25.0.1 — 기본 릴리스)
       1: invokevirtual #21                 // Method privateM:()Ljava/lang/String;

$ javac --release 8 Ex.java
       1: invokespecial #21                 // Method privateM:()Ljava/lang/String;
```

- **의미는 한 글자도 안 바뀐다.** 둘 다 `Super.privateM` 이 불린다(실행 결과가 같다).
- 바뀐 것은 **nestmate**(JEP 181, Java 11) 이후 같은 nest 안의 `private` 접근을 `invokevirtual` 로도 할 수 있게 된 것이다.
- 그러니 **「`private` 은 `invokespecial` 로 컴파일된다」는 외워 두면 틀린다.**\
  외울 것은 **「`private` 은 디스패치되지 않는다」**이고, 그것은 언어 보장이다.
- 같은 이유로 중첩 클래스와 바깥 클래스 사이의 `private` 접근도 Java 11+ 에서는 **접근자 메서드 없이** 직접 된다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 재정의 의도가 있으면 **항상 `@Override`** | `@Override` 없이 "재정의했다"고 믿기 |
| 필드는 `private` + 접근자 재정의 | `protected` 필드를 하위 클래스가 다시 선언 |
| 재정의되면 안 되는 것은 `final` | `static` 메서드를 인스턴스 참조로 호출 |
| 반환 타입을 좁힐 수 있으면 **공변 반환** | 상속 계층을 깊게 만들기 — `super.` 체인이 읽기 어려워진다 |

판단 규칙 세 줄.

- **`@Override` 는 비용이 0인 보험이다.** 안 다는 이유가 없다.
- **필드는 상속 설계의 대상이 아니다.** 공개할 것은 메서드다.
- **생성자에서는 오버라이드 가능한 메서드를 부르지 않는다** — [06 편](../06-initialization-order/)과 [07 편](../07-constructors/)의 결론이 여기서도 같다.

## 핵심 문장

- **메서드는 런타임 타입으로, 필드와 `static` 메서드는 선언 타입으로** 결정된다. 이 비대칭이 이 주제의 전부다.
- 바이트코드에는 **선언 타입의 시그니처**가 박히고, `invokevirtual` 이 런타임에 실제 구현을 찾는다.
- `private`·`static`·`final` 은 오버라이딩이 **아니다** — 각각 미상속·숨김·금지다.
- **공변 반환**은 컴파일러가 브리지 메서드를 만들어 성립시킨다(`javap -v` 의 `ACC_BRIDGE`).
- 오버라이딩에는 **접근 넓히기만·예외 줄이기만** 허용된다. 어기면 컴파일 에러로 막힌다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 09번)
- [`../../../../oop-basics/`](../../../../oop-basics/) — **다형성·상속·추상 클래스의 개념은 거기**(§14~18, 파이썬 예제).\
  ★ 그쪽은 「다형성이 무엇이고 왜 쓰나」까지, 여기는 **「Java 가 그것을 어느 문법으로 강제하고 어디서 강제하지 않나」**부터다.\
  필드 숨김·브리지 메서드·`@Override` 는 파이썬에 없는 것이라 그 문서에 없다
- [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) — **오버로딩(컴파일 타임)과의 대비**가 이 주제의 절반이다
- [`../06-initialization-order/`](../06-initialization-order/) — 생성자에서 오버라이드 메서드를 부르면 자식 필드가 기본값인 이유
- [`../07-constructors/`](../07-constructors/) — Java 25 가 그 함정을 어디까지 고쳐 주는지
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **`equals` 계약은 거기**, 여기는 **그 사고가 오버로딩이라는 것**까지
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **가상 호출의 JIT 최적화(인라인 캐시·단형화)는 거기.** 여기는 **언어 규칙**까지만
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스) — `default` 메서드가 이 규칙에 끼어들면 무엇이 달라지나
- 목록의 **19번 주제**(타입 소거) — 브리지 메서드가 제네릭에서도 생긴다

## 용어 풀이

- **오버라이딩(overriding)** — 하위 클래스가 상위 클래스의 인스턴스 메서드를 **같은 시그니처로** 다시 정의하는 것.
- **동적 디스패치(dynamic dispatch)** — 어느 구현을 부를지 런타임 타입으로 고르는 것. 가상 호출(virtual call)이라고도 한다.
- **선언 타입(static type)** — 변수·식에 소스에 적힌 타입. 컴파일러가 보는 것.
- **런타임 타입(runtime type)** — 그 참조가 실제로 가리키는 객체의 클래스. `getClass()` 가 주는 것.
- **필드 숨김(field hiding)** — 하위 클래스가 같은 이름의 필드를 다시 선언하는 것. 저장소가 둘 생긴다.
- **메서드 숨김(method hiding)** — `static` 메서드를 같은 시그니처로 다시 선언하는 것. 선언 타입으로 고른다.
- **공변 반환(covariant return)** — 재정의할 때 반환형을 하위 타입으로 좁히는 것. Java 5+.
- **브리지 메서드(bridge method)** — 디스크립터를 맞추려고 컴파일러가 만드는 숨은 메서드. `ACC_BRIDGE` 플래그.
- **`invokevirtual` / `invokespecial` / `invokestatic`** — 각각 가상 호출 / 고정 호출(`super.`·생성자) / 정적 호출.
- **nest / nestmate** — 같은 최상위 클래스에 속한 클래스들의 묶음(JEP 181, Java 11). 서로의 `private` 멤버에 직접 접근한다.
- **리스코프 치환 원칙** — 상위 타입 자리에 하위 타입을 넣어도 프로그램이 깨지면 안 된다는 원칙. 오버라이딩 조건이 그 강제다.

## 더 들어가면

- **`invokevirtual` 이 `private` 메서드를 부를 때 디스패치가 안 일어나는 이유** — JVMS 의 `invokevirtual` 해소 규칙이\
  "해소된 메서드가 `private` 이면 그것을 그대로 쓴다"고 정하기 때문이다. vtable 을 타지 않는다.
- **`final` 클래스와 `final` 메서드는 JIT 에게 힌트가 된다.** 다만 JIT 는 `final` 이 없어도\
  실제로 로드된 클래스가 하나뿐이면 단형으로 보고 인라인한다(class hierarchy analysis).\
  그래서 `final` 을 성능 때문에 붙이는 것은 대개 근거가 약하다.
- **인터페이스의 `default` 메서드도 오버라이딩 규칙을 따른다.** 다만 다중 상속이 가능해 충돌 규칙이 따로 있다 — 11번 주제.
- **필드 숨김을 의도적으로 쓰는 경우는 사실상 없다.** JLS 가 허용하는 것과 쓸모가 있는 것은 다르다.
