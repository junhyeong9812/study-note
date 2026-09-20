# java/syntax/16 — 애너테이션: 선언·`@Retention`·`@Target`·메타 애너테이션 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·에러를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 `@Retention` 은 각각 어디까지 살아남는가 (예측)

```java
@Retention(RetentionPolicy.SOURCE)  @Target(ElementType.TYPE) @interface KeepInSource { String value() default "s"; }
@Retention(RetentionPolicy.CLASS)   @Target(ElementType.TYPE) @interface KeepInClass  { String value() default "c"; }
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @interface KeepAtRuntime{ String value() default "r"; }

@KeepInSource("A") @KeepInClass("B") @KeepAtRuntime("C")
static class Three {}
```

- `Three.class.getAnnotations().length` 는 몇인가?
- 셋을 각각 `getAnnotation(...)` 으로 조회하면 무엇이 나오는가?
- `javap -v` 로 `Three.class` 를 열면 어느 속성에 무엇이 들어 있는가?
- `KeepInSource` 라는 이름이 클래스 파일에 남아 있는가?

### 2. `@Retention` 을 안 적으면 무슨 일이 생기나 (예측)

```java
@interface NoMeta { String value() default "d"; }     // @Retention 도 @Target 도 없다

@NoMeta("on-class")
static class C {
    @NoMeta("on-field") int f;
    @NoMeta("on-method") void m(@NoMeta("on-param") int p) { @NoMeta("on-local") int x = p; }
}
```

- `C.class.getAnnotations()` 는 무엇인가?
- 클래스 파일에는 남아 있는가? 남아 있다면 어느 속성인가?
- `@Target` 을 안 적었는데 여섯 자리에 다 붙는가?
- 이 조합이 "무음 실패"가 되는 이유는 무엇인가?

### 3. `@Target` 이 막는 것 (예측)

```java
@Target(ElementType.METHOD) @Retention(RetentionPolicy.RUNTIME)
@interface MethodOnly {}

@MethodOnly static class Wrong {}                 // (A)
static class Ok { @MethodOnly void m() {}         // (B)
                  @MethodOnly int field; }        // (C)
```

- (A)(B)(C) 중 어디가 컴파일 에러인가, **메시지 전문**은 무엇인가?
- 그 메시지가 JDK 17 과 21 에서 같은가?
- `ElementType` 에는 몇 개의 상수가 있고, 그중 Java 5 이후에 추가된 것은 무엇인가?

### 4. 애너테이션 원소로 쓸 수 있는 타입 (예측)

```java
@interface Bad {
    List<String> names();     // (A)
    Object any();             // (B)
    int[] ok();               // (C)
    String[][] deep();        // (D)
}
```

- 넷 중 어디가 컴파일 에러인가, 그 에러 메시지는 무엇인가?
- 쓸 수 있는 타입을 전부 나열하면 무엇인가?
- 왜 그 목록으로 제한되는가?

### 5. 애너테이션 선언에서 안 되는 것들 (예측)

```java
@interface Need    { String value(); int order(); }   @Need("x") class A {}   // (A)
@interface Derived extends Base { }                                          // (B)
@interface DefaultNull { String v() default null; }                          // (C)
@interface Cyclic  { Cyclic self(); }                                        // (D)
@interface Thrown  { String v() throws Exception; }                          // (E)
@interface Param   { String v(int i); }                                      // (F)
@interface Generic<T> { String v(); }                                        // (G)
```

- 일곱 자리에서 각각 어떤 컴파일 에러가 나는가?
- 애너테이션은 무엇을 상속하는가? 그것을 어떻게 확인하는가?
- "값 없음"을 표현하려면 `null` 대신 무엇을 쓰는가?

### 6. `@Repeatable` 을 두 번 붙이면 런타임에 무엇으로 보이나 (예측)

```java
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) @Repeatable(Roles.class)
@interface Role { String value(); }
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
@interface Roles { Role[] value(); }

@Role("admin") @Role("user") static class Repeated {}
@Role("single")              static class Once {}
```

- `Repeated` 에 대한 `getAnnotation(Role.class)` / `getAnnotation(Roles.class)` / `getAnnotationsByType(Role.class)` 는 각각 무엇인가?
- `Once` 에 대해서는 같은 셋이 각각 무엇인가?
- 읽는 코드는 어느 API 를 써야 개수에 상관없이 동작하는가?

### 7. `@Inherited` 는 어디까지 도는가 (경계)

```java
@Retention(RetentionPolicy.RUNTIME) @Inherited @interface Inheritable { String value(); }
@Retention(RetentionPolicy.RUNTIME)            @interface NotInheritable { String value(); }

@Inheritable("from-parent") @NotInheritable("from-parent") static class Parent {}
static class Child extends Parent {}

@Retention(RetentionPolicy.RUNTIME) @Inherited @interface Inh { String value(); }
@Inh("on-interface") interface I {}
static class FromInterface implements I {}
```

- `Child.class.getAnnotation(Inheritable.class)` 와 `getDeclaredAnnotations()` 는 각각 무엇인가?
- `FromInterface.class.getAnnotation(Inh.class)` 는 무엇인가? 왜인가?
- `@Inherited` 를 메서드에 붙인 애너테이션에 달면 어떻게 되는가?

### 8. 지역 변수에 붙인 런타임 애너테이션은 읽히는가 (예측)

```java
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER, ElementType.LOCAL_VARIABLE})
@interface Mark { String value(); }

@Mark("field") String name;
@Mark("method") void work(@Mark("param") int a, int b) { @Mark("local-var") int x = 1; }
```

- 필드·메서드·파라미터·지역 변수 넷 중 리플렉션으로 읽히는 것은 무엇인가?
- 클래스 파일에는 각각 어느 속성으로 들어가는가?
- `@Target(TYPE_USE)` 로 선언한 애너테이션을 지역 변수 **타입**에 붙이면 어떻게 달라지는가?
- 파라미터 이름이 `a` 로 나오려면 무엇이 필요한가?

### 9. `getAnnotation()` 이 돌려준 객체의 정체 (예측)

```java
KeepAtRuntime k = Three.class.getAnnotation(KeepAtRuntime.class);
```

- `k.getClass()` 는 무엇인가? `k.annotationType()` 과 왜 다른가?
- 같은 조회를 두 번 하면 `==` 가 참인가? 그것을 믿어도 되는가?
- 두 애너테이션 인스턴스의 `equals` 는 무엇을 비교하는가?

### 10. 표준 애너테이션들의 `@Retention` (예측)

- `@Override`·`@Deprecated`·`@SuppressWarnings`·`@SafeVarargs`·`@FunctionalInterface` 의 `@Retention` 은 각각 무엇인가?
- `@SuppressWarnings` 의 `@Target` 은 무엇인가? 왜 그런가?
- 메타 애너테이션 다섯의 `@Retention`·`@Target` 은 무엇인가?

### 11. 애너테이션의 `toString()` 을 믿어도 되는가 (경계)

- 같은 애너테이션을 JDK 17·21·25 에서 `toString()` 하면 결과가 같은가?
- 무엇이 달라졌는가?
- 그래서 로그·테스트에서 무엇을 하면 안 되는가?

### 12. 무엇을 골라야 하나 (연결)

- 프레임워크가 리플렉션으로 읽을 애너테이션에는 어떤 `@Retention` 을 주는가?
- 애너테이션 프로세서만 읽으면 되는 것은?
- 바이트코드 분석기만 읽으면 되는 것은?
- 애너테이션에 "런타임에 바뀌는 값"을 담을 수 있는가? 없다면 왜인가?

### 13. 다른 주제와 잇기 (연결)

- 애너테이션이 **제네릭이 될 수 없는** 이유는 어느 주제와 이어지는가?
- 클래스 파일에 "지워지는 것"과 "속성으로 남는 것"이라는 구조를 공유하는 주제는 무엇인가?
- `ElementType.RECORD_COMPONENT` 는 왜 16에서야 생겼는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
