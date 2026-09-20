# java/syntax/09 — 상속과 오버라이딩: 동적 디스패치·공변 반환·필드 숨김 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 출력이 같음을 확인했다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 한 변수, 다섯 줄, 네 가지 규칙

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
s.field         = Super.field
s.instanceM()   = Sub.instanceM
s.staticM()     = Super.staticM
s.callPrivate() = Super.privateM
((Sub) s).field = Sub.field
```

**왜 그런가**

```text
javap -c Ex 의 main — 출력 그대로

      12: getfield      #16                 // Field Super.field:Ljava/lang/String;
      27: invokevirtual #32                 // Method Super.instanceM:()Ljava/lang/String;
      41: aload_1
      42: pop
      43: invokestatic  #37                 // Method Super.staticM:()Ljava/lang/String;
      58: invokevirtual #41                 // Method Super.callPrivate:()Ljava/lang/String;
      73: checkcast     #7                  // class Sub
      76: getfield      #45                 // Field Sub.field:Ljava/lang/String;
```

| 무엇 | 언제 정해지나 | 무엇을 보나 |
|---|---|---|
| `s.field` | **컴파일 타임** | 선언 타입 `Super` |
| `s.instanceM()` | **런타임** | 객체의 실제 클래스 `Sub` |
| `s.staticM()` | **컴파일 타임** | 선언 타입 `Super` |
| `s.callPrivate()` → `privateM()` | **컴파일 타임** | `Super` 안에서만 보이는 `privateM` |

- **런타임에 정해지는 것은 하나뿐**이다 — 인스턴스 메서드.
- `s.staticM()` 자리의 `aload_1` 다음은 **`pop`** 이다.\
  `s` 를 스택에 올렸다가 **그냥 버린다** — 정적 호출이라 수신 객체가 필요 없기 때문이다.\
  그래도 `s` 를 만드는 식은 평가되므로, `getList().staticM()` 처럼 쓰면 `getList()` 는 돈다.
- 마지막 줄의 캐스트는 `checkcast Sub` 를 넣고 **읽는 필드를 `Sub.field` 로 바꾼다.**\
  캐스트가 **필드 선택을 바꾼다** — 메서드였다면 아무것도 안 바뀐다(5번 참조).

### 2. 같은 `invokevirtual` 인데 왜 갈리나

**컴파일러가 하는 일** — 선언 타입에서 시그니처를 찾아 상수 풀에 **`Super.instanceM:()Ljava/lang/String;`** 을 박는다.

**JVM 이 하는 일** — `invokevirtual` 을 만나면 **수신 객체의 실제 클래스부터 위로** 올라가며\
그 시그니처를 가진 메서드를 찾는다(JVMS §6.5 `invokevirtual`). `Sub.instanceM` 이 먼저 잡힌다.

```text
컴파일 타임                          런타임
+---------------------------+       +---------------------------+
| 선언 타입 Super 에서       |       | 객체는 Sub 다              |
| instanceM() 을 찾는다      |       | Sub 부터 위로 찾는다        |
| -> 상수 풀에 시그니처 기록  |  -->  | -> Sub.instanceM 을 실행    |
+---------------------------+       +---------------------------+
   "이런 모양의 메서드"                 "그 모양을 가진 가장 가까운 것"
```

**필드에는 왜 같은 일이 안 일어나는가**

- `getfield` 는 **상수 풀의 필드 참조를 그대로 쓴다.** "찾아 올라가기"가 없다.
- 이유는 JVM 의 게으름이 아니라 **설계**다 — 필드는 객체 레이아웃의 **고정 오프셋**이고,\
  `Super.field` 와 `Sub.field` 는 **서로 다른 오프셋**에 둘 다 존재한다.
- 메서드는 "하나의 이름에 여러 구현", 필드는 "여러 이름이 우연히 같은 철자"다.

### 3. `private` 메서드와 상속

**왜 `Super.privateM` 인가**

- `private` 멤버는 **하위 클래스에 상속되지 않는다**(JLS §8.2).\
  `Sub.privateM` 은 후보에 아예 들어오지 않는다.
- 그래서 둘은 **이름만 같은 남남**이고, 오버라이딩이 아니다.

**명령** (`javap -c -p Super`, JDK 21.0.5)

```text
  java.lang.String callPrivate();
    Code:
       0: aload_0
       1: invokevirtual #21                 // Method privateM:()Ljava/lang/String;
       4: areturn
```

**`--release 8` 로 컴파일하면 바뀐다.**

```text
$ javac --release 8 Ex.java
       1: invokespecial #21                 // Method privateM:()Ljava/lang/String;
```

**동작은 바뀌지 않는다.**

- 두 경우 모두 실행 결과가 `Super.privateM` 이다.
- `invokevirtual` 이 된 이유는 **nestmate**(JEP 181, Java 11) 다 — 같은 nest 안의 `private` 접근을\
  접근자 없이 직접 할 수 있게 되면서 javac 가 명령 선택을 바꿨다.
- JVMS 의 `invokevirtual` 해소 규칙이 **"해소된 메서드가 `private` 이면 그것을 그대로 쓴다"**고 정하므로\
  vtable 을 타지 않는다. 명령 이름만 보고 판단하면 틀린다.
- ★ 외울 것: **「`private` 은 `invokespecial`」이 아니라 「`private` 은 디스패치되지 않는다」.**\
  앞은 구현 세부(버전에 따라 갈림), 뒤는 언어 보장이다.

### 4. 공변 반환과 브리지 메서드

**출력** (`javap -c -p DogShelter`, JDK 21.0.5 — `adopt` 가 **두 개**다)

```text
  Dog adopt();
    Code:
       0: new           #7                  // class Dog
       3: dup
       4: invokespecial #9                  // Method Dog."<init>":()V
       7: areturn

  Animal adopt();
    Code:
       0: aload_0
       1: invokevirtual #10                 // Method adopt:()LDog;
       4: areturn
```

```text
javap -v -p DogShelter

  Animal adopt();
    descriptor: ()LAnimal;
    flags: (0x1040) ACC_BRIDGE, ACC_SYNTHETIC
```

**왜 그런가**

- 두 번째 `adopt` 의 본문은 **자기 자신의 `()LDog;` 버전을 부르고 그 결과를 그대로 반환**한다. 다리 역할이다.
- 플래그는 **`ACC_BRIDGE, ACC_SYNTHETIC`** — 컴파일러가 만든 것이라는 표시다.
- JVM 수준에서 오버라이딩은 **이름 + 디스크립터**가 같아야 성립한다. 디스크립터에는 **반환형이 들어간다.**\
  `()LAnimal;` 과 `()LDog;` 는 JVM 에게 **완전히 다른 메서드**다.
- 그래서 `Shelter s = new DogShelter(); s.adopt()` 가 `()LAnimal;` 를 부를 때 무언가가 받아 줘야 한다.\
  그 무언가가 브리지다.
- 실행 결과는 `Dog / Dog` — 어느 쪽으로 불러도 `Dog` 객체가 나온다.

### 5. `super.` 와 캐스트

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
super.name()        = Sup
((Sup) this).name() = Sub
```

**왜 그런가**

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

| | 대상 | 명령 | 결과 |
|---|---|---|---|
| `super.name()` | `Sup.name` | `invokespecial` | `"Sup"` |
| `((Sup) this).name()` | `Sup.name` | `invokevirtual` | `"Sub"` |

- **대상이 같은데 결과가 다르다.** 명령 하나가 전부를 결정한다.
- 캐스트는 **선언 타입만** 바꾼다. 선언 타입은 상수 풀 항목을 고를 뿐이고, 디스패치는 그 뒤에 일어난다.
- 한 문장: **캐스트는 "어느 시그니처인지"를 바꾸고, `super.` 는 "찾지 말고 여기로 가라"를 바꾼다.**
- 그래서 상위 구현을 쓰고 싶으면 **`super.` 만** 된다. 그리고 `super.` 는 **바로 한 칸 위**만 가리킨다 —\
  조부모를 지목하는 문법은 없다.

### 6. 재정의한 줄 알았는데

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
x.render("a") = sup
```

**왜 그런가**

- 파라미터 타입이 다르므로 이것은 **오버라이딩이 아니라 오버로딩**이다.
- `x` 의 선언 타입이 `Sup` 이라 후보는 `Sup.render(Object)` 하나뿐이고, 그것이 박힌다(08 편).
- **컴파일 경고가 없다.** javac 는 "네가 의도한 게 뭔지" 모른다.

`@Override` 를 달면 그 자리에서 멈춘다.

```text
Ex.java:3: error: method does not override or implement a method from a supertype
    @Override String render(String s) { return "sub"; }   // 파라미터 타입이 다르다
    ^
1 error
```

- **습관 하나: 재정의 의도가 있으면 무조건 `@Override` 를 단다.**\
  런타임 비용이 0이고, 이 유형의 사고를 통째로 없앤다.

### 7. `equals` 오버로딩 사고

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
p.equals(q)   = true
op.equals(oq) = false
```

**왜 그런가**

- `boolean equals(Sup other)` 는 `Object.equals(Object)` 와 **파라미터 타입이 다르다** → 오버로딩이다.
- `p.equals(q)` 는 선언 타입이 `Sup` 이라 **내가 쓴 것**이 뽑힌다 → `true`.
- `op.equals(oq)` 는 선언 타입이 `Object` 라 **`Object.equals`** 가 뽑힌다 → 참조 비교 → `false`.
- 컬렉션이 문제가 되는 이유: `HashMap`·`List.contains` 는 **내부에서 `Object` 참조로** 부른다.\
  그래서 **내 테스트는 통과하고 컬렉션만 틀린다** — 가장 찾기 어려운 형태다.

`Object` 로 고치고 `@Override` 를 달면 **또 다른 에러**가 나온다.

```text
Ex.java:1: error: equals(Object) in Sup cannot override equals(Object) in Object
class Sup { boolean equals(Object o) { return true; } }
                    ^
  attempting to assign weaker access privileges; was public
```

- `Object.equals` 는 `public` 인데 이쪽은 **package-private** 이다. **접근 수준을 좁힐 수 없다**(8번).
- 계약 자체(다섯 조항·`hashCode` 와의 관계)는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

### 8. 오버라이딩의 다섯 조건

| 조건 | 어느 방향으로 |
|---|---|
| 반환형 | **좁히기만**(공변 반환, Java 5+). 넓히면 에러 |
| 접근 수준 | **넓히기만**(`protected` → `public`). 좁히면 에러 |
| 검사 예외 | **줄이기만**. 넓히면 에러 |
| `final` 메서드 | 재정의 불가 |
| `static` 메서드 | 재정의가 아니라 숨김 |

셋을 한꺼번에 쓴 예제가 컴파일된다.

```java
class Sup { protected Number get() throws java.io.IOException { return 1; } }
class Sub extends Sup {
    @Override public Integer get() { return 2; }   // 넓히기 O, 공변 반환 O, 예외 줄이기 O
}
```

**출력** (`Ex.java`, JDK 21.0.5)

```text
s.get() = 2 (Integer)
```

**공통으로 지키려는 원칙**

- **리스코프 치환 원칙** — 상위 타입 자리에 하위 타입을 넣어도 기존 코드가 깨지면 안 된다.
- 반환형을 넓히면 `Number n = s.get();` 가 깨진다.\
  접근을 좁히면 호출 자체가 안 된다.\
  예외를 넓히면 `catch (IOException)` 만 해 둔 코드가 못 잡는다.
- 즉 세 규칙은 **"상위 타입으로 쓰는 코드가 계속 돈다"**는 하나의 요구다.

**`final`·`static` 을 재정의하려 하면**

```text
Ex.java:2: error: name() in Sub cannot override name() in Sup
class Sub extends Sup { String name() { return "sub"; } }
                               ^
  overridden method is final
1 error
```

```text
Ex.java:2: error: who() in Sub cannot override who() in Sup
class Sub extends Sup { String who() { return "sub"; } }   // static 을 인스턴스로
                               ^
  overridden method is static
1 error
```

```text
Ex.java:2: error: static methods cannot be annotated with @Override
class Sub extends Sup { @Override static String who() { return "sub"; } }
                        ^
1 error
```

### 9. 필드 숨김이 만드는 사고

**저장소는 둘이다.**

```text
힙의 객체 하나 (new Sub())            읽는 쪽
+---------------------------+       Super s = ...;   s.field         -> "Super.field"
| Super.field = "Super..."  |  <----+
| Sub.field   = "Sub..."    |  <----+
+---------------------------+       Sub   t = ...;   t.field         -> "Sub.field"
   하나가 다른 하나를 덮지 않는다            ((Sub) s).field          -> "Sub.field"
```

- 하나가 다른 하나를 **덮는 게 아니다.** 둘 다 객체 안에 있고 오프셋이 다르다.
- **부모 클래스가 쓴 코드는 `Super.field` 를, 자식이 쓴 코드는 `Sub.field` 를 읽는다.**\
  같은 객체인데 두 코드가 서로 다른 값을 본다.
- **경고가 없다.** 1번의 실행 결과가 그 증거다 — `s.field` 와 `((Sub) s).field` 가 다른 값을 줬는데 아무 소리도 안 난다.
- `@Override` 에 해당하는 안전장치가 **필드에는 없다.**
- 방어는 셋이다.
  1. **필드는 `private`** 으로 두고 접근자(`getX()`)를 재정의한다 — 메서드는 동적 디스패치된다.
  2. `protected` 필드를 두지 않는다. 그것이 이 사고의 전제 조건이다.
  3. 상속 계층에서 필드 이름을 재사용하지 않는다(정적 분석 도구가 잡아 주기도 한다).

### 10. `static` 메서드를 인스턴스 참조로 부르면

- **컴파일된다.** 에러도 경고도 없다(JDK 21.0.5 기준, 1번 프로그램이 그대로 돈다).
- 바이트코드에서 `s` 는 **`aload_1` 로 올라갔다가 `pop` 으로 버려진다.**

  ```text
        41: aload_1
        42: pop
        43: invokestatic  #37                 // Method Super.staticM:()Ljava/lang/String;
  ```

실제로 `null` 참조로도 돌고, 식은 평가된다 (`Ex.java`, JDK 21.0.5).

```text
null 참조로: Sup.who
  expensive() 가 돌았다
식으로     : Sup.who
```

- 쓰면 안 되는 이유 셋.
  1. **어느 클래스의 것이 불리는지 안 보인다.** `s.staticM()` 인데 `Super.staticM` 이 돈다.
  2. **`s` 가 `null` 이어도 돈다.** 수신 객체가 필요 없기 때문이다.
  3. **식은 평가된다.** `expensive().staticM()` 은 `expensive()` 를 부르고 결과를 버린다.
- 올바른 표기는 **`Super.staticM()`** 이다 — 클래스 이름으로 쓴다.

### 11. 오버로딩과 오버라이딩

| | 오버로딩 (08) | 오버라이딩 (09) |
|---|---|---|
| 언제 정해지나 | **컴파일 타임** | **런타임** |
| 무엇을 보고 고르나 | 인자의 **선언 타입** | 수신 객체의 **런타임 타입** |
| 시그니처 | 서로 **다르다**(파라미터가 달라야 성립) | 서로 **같다**(같아야 성립) |
| 클래스 파일에 남는 것 | 고른 **결과** 시그니처 | 선언 타입의 시그니처 + 런타임 디스패치 |
| 고르는 주체 | `javac` | JVM |
| 관계 | 같은 클래스 안이어도 된다 | 상속 관계가 **있어야** 한다 |

- 한 문장: **오버로딩은 "어느 메서드"를 고르고, 오버라이딩은 "어느 구현"을 고른다.**
- 6번·7번의 사고는 전부 **둘을 헷갈린 것**이다 — 재정의하려다 오버로딩을 만들었다.

### 12. 정본 경계

**다형성·상속이 무엇인가**

- [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이다(§14 IS-A 상속, §16 다형성과 메서드 오버라이딩, §17 추상 클래스).\
  파이썬 예제로 **개념**을 다룬다.

**그 문서에 없는 것 셋**

1. **필드 숨김** — 파이썬은 인스턴스 딕셔너리 하나라 "저장소가 둘" 이 안 생긴다.
2. **브리지 메서드·공변 반환** — 정적 타입과 디스크립터가 있어야 생기는 문제다.
3. **`@Override`·접근 좁히기 금지·예외 넓히기 금지** — 컴파일러가 강제하는 것들이다.

- 즉 그쪽은 **「다형성이 무엇이고 왜 쓰나」**, 여기는 **「Java 가 그것을 어느 문법으로 강제하고 어디서 강제하지 않나」**다.\
  ★ 그리고 이 주제의 값어치는 대부분 **"강제하지 않는 쪽"**(필드 숨김·`static` 숨김·오버로딩 사고)에 있다.

**가상 호출의 JIT 최적화**

- [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다. 인라인 캐시·단형화·역최적화는 그쪽이다.\
  여기는 **언어 규칙**(무엇이 불리나)까지만 다룬다.

**`equals` 계약**

- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.\
  여기는 **그 사고의 원인이 오버라이딩 규칙**이라는 것까지만 쓴다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `09/a/Ex` + `javap -c` | 필드·인스턴스·`static`·`private` 네 갈래 · `aload_1; pop` | 17 · 21 · 25 (출력 동일) |
| `09/a` + `javap -c -p Super` | `private` 호출이 `invokevirtual` (21 기본) | 17 · 21 · 25 (셋 다 `invokevirtual`) |
| `09/a` + `javac --release 8` | 같은 코드가 `invokespecial` 로 바뀜 — **동작은 동일** | 21 |
| `09/b/Ex` + `javap -c -p` + `javap -v -p` | 공변 반환 · 브리지 메서드 `ACC_BRIDGE, ACC_SYNTHETIC` | 17 · 21 · 25 (출력 동일) |
| `09/d/Ex` + `javap -c -p Sub` | `super.m()` = `invokespecial` | 17 · 21 · 25 (출력 동일) |
| `09/e/Ex` + `javap -c -p Sub` | `super.` 대 `((Sup) this).` — 같은 `#9`, 다른 명령 | 21 |
| `09/c/Ex` | `equals(Sup)` 오버로딩 — `true` / `false` | 21 |
| `09/e1c/Ex` | `@Override` 없는 시그니처 불일치가 조용히 통과 | 17 · 21 · 25 (출력 동일) |
| `09/e1b/Ex` | `@Override` 가 잡음 — `does not override or implement` | 21 |
| `09/e1/Ex` | package-private `equals(Object)` — `weaker access privileges` | 21 |
| `09/e2/Ex` | `final` 메서드 재정의 — `overridden method is final` | 21 |
| `09/e3/Ex` | 접근 좁히기 — `attempting to assign weaker access privileges` | 21 |
| `09/e4/Ex` | 검사 예외 넓히기 — `overridden method does not throw Exception` | 21 |
| `09/e5/Ex` | `static` 에 `@Override` — `static methods cannot be annotated` | 21 |
| `09/e6/Ex` | `static` 을 인스턴스 메서드로 — `overridden method is static` | 21 |
| `09/f/Ex` | 넓히기 + 공변 반환 + 예외 줄이기를 동시에 — 통과 | 21 |

**안 돌려 본 것**

- **JIT 가 가상 호출을 인라인하는지** — **안 돌려 봄**. 이 문서는 바이트코드까지만 본다.
- **필드 숨김에 대한 정적 분석 도구의 경고** — **안 돌려 봄**. `javac` 가 경고하지 않는다는 것만 확인했다.

**구현 의존 항목**

- `private` 메서드 호출 명령(`invokevirtual` / `invokespecial`) — **컴파일 대상 버전에 따라 갈린다.**\
  17·21·25 기본 릴리스는 전부 `invokevirtual`, `--release 8` 은 `invokespecial` 이었다.
- `javap` 의 오프셋·상수 풀 번호(`#n`) — 컴파일러 버전에 따라 달라질 수 있다.
- **브리지 메서드가 생기는 것** — 결과(디스패치가 성립하는 것)는 언어 보장이고, 브리지라는 수단은 javac 의 선택이다.

**버전이 오르면 다시 돌릴 것** — `private` 호출 명령 항목. nestmate 이후로는 안정적이지만,\
"명령 이름"을 근거로 쓴 자리가 이 문서에 하나 있으므로 LTS 가 오를 때 다시 찍는다.
