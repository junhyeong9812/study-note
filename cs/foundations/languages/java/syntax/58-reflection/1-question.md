# java/syntax/58 — 리플렉션: `Class`·`getDeclared*`·접근 제어 우회의 경계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력(예외 메시지 포함)을 맞힐 수 있는지**를 묻는다.
> 수치를 묻는 문항(10)은 **절댓값이 아니라 자릿수**를 맞히는 것이 목표다.
> 선행: [16 애너테이션](../16-annotations/) · [19 타입 소거](../19-type-erasure/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Class` 를 얻는 세 가지 길 (예측)

```java
Class<?> c1 = String.class;
Class<?> c2 = "hi".getClass();
Class<?> c3 = Class.forName("java.lang.String");
System.out.println(c1 == c2 && c2 == c3);

class Holder { static { System.out.println("[Holder 초기화]"); } }
Class<?> lit = Holder.class;          // (가)
Class.forName("Holder");              // (나)
Class.forName("Holder", false, loader);  // (다)
```

- 첫 출력은 무엇인가?
- (가)·(나)·(다) 중 `[Holder 초기화]` 가 찍히는 것은 어느 것인가?
- 옛날 JDBC 코드의 `Class.forName("...Driver")` 가 노린 것은 무엇인가?
- 없는 이름을 주면 무슨 예외인가, 검사 예외인가?

### 2. 이름 세 가지 (예측)

```java
// int.class · int[].class · String[][].class · Ex$Nested · 익명 클래스
// 각각의 getName() / getSimpleName() / getCanonicalName() 은?
```

- 배열 타입의 `getName()` 은 어떤 모양인가?
- 익명 클래스의 `getSimpleName()` 과 `getCanonicalName()` 은 각각 무엇인가?
- `Class.forName` 에 다시 넣을 수 있는 것은 셋 중 어느 것인가?
- 로그에 클래스 이름을 찍을 때 어느 것을 써야 하는가, 왜인가?

### 3. `getXxx` 대 `getDeclaredXxx` (예측)

```java
class Base  { public int basePublic; protected String baseProtected; private double basePrivate;
              public void basePublicM() {} private void basePrivateM() {} }
class Child extends Base { public int childPublic; private int childPrivate;
              public void childPublicM() {} private void childPrivateM() {}
              Child() {} private Child(int x) {} }
```

- `Child.class.getFields()` 와 `getDeclaredFields()` 의 원소는 각각 무엇인가?
- `getConstructors().length` 와 `getDeclaredConstructors().length` 는 각각 몇인가?
- `Child.class.getDeclaredFields()` 에 `basePrivate` 이 있는가?
- "상속받은 private"을 한 번에 주는 메서드가 있는가?

### 4. 없는 멤버를 찾으면 (예측)

```java
Child.class.getDeclaredField("nope");
Child.class.getMethod("childPrivateM");
```

- 두 줄에서 각각 어떤 예외가 나는가, 메시지는 무엇인가?
- 둘째 줄이 "없다"고 말하는 진짜 이유는 무엇인가?
- 이 예외들은 검사 예외인가?

### 5. ★ `setAccessible` 은 어디까지 통하나 (예측)

```java
class Secret { private String token = "비밀"; }

// (가) Secret 의 token 에 setAccessible(true) 후 get/set
// (나) String.class.getDeclaredField("value") 에 setAccessible(true)
// (다) ArrayList.class.getDeclaredField("elementData") 에 setAccessible(true)
// (라) Class.forName("jdk.internal.misc.Unsafe") 의 getUnsafe() 에 setAccessible(true)
// (마) String.class.getDeclaredFields() 로 목록만 읽기
```

- 다섯 중 **플래그 없이 성공하는 것**은 어느 것인가?
- 실패하는 것의 **예외 타입과 메시지**는 무엇인가?
- (나)(다) 와 (라) 의 메시지에서 **따옴표 안 낱말이 다르다** — 각각 무엇이고 왜 다른가?
- (마) 가 성공한다는 사실이 뜻하는 것은 무엇인가?

### 6. 플래그로 열면 (예측)

```text
java --add-opens java.base/java.lang=ALL-UNNAMED   ...
java --add-exports java.base/jdk.internal.misc=ALL-UNNAMED   ...
```

- 5번의 (나)~(라) 중 각 플래그로 열리는 것은 어느 것인가?
- `--add-opens` 로 `exports` 문제를 고칠 수 있는가?
- 플래그의 세 칸(`<모듈>/<패키지>=<받는 쪽>`)은 각각 무엇을 적는가?
- 클래스패스에서 실행할 때 "받는 쪽"에 무엇을 적는가?

### 7. 열고 나면 무슨 일이 생기나 (예측)

```java
String a = "hello";
String b = "hello";
Field v = String.class.getDeclaredField("value");
v.setAccessible(true);
v.set(a, new byte[]{'X','X','X','X','X'});
System.out.println(b);
```

- 마지막 줄의 출력은 무엇인가?
- 왜 `b` 까지 바뀌는가 — 어느 주제의 어떤 규칙 때문인가?
- `final` 필드인데 왜 써졌는가?
- 이 실험이 JEP 396/403 의 결정에 대해 말해 주는 것은 무엇인가?

### 8. ★ 소거됐는데 제네릭이 읽히는 이유 (연결)

```java
class Holder<T extends Number> {
    List<String> names;
    Map<String, List<Integer>> deep;
    T value;
    List<? extends Number> wild;
}
class IntHolder extends Holder<Integer> {}
```

- `names` 의 `getType()` 과 `getGenericType()` 은 각각 무엇인가?
- `value` 의 `getType()` 은 무엇인가, 왜인가?
- `IntHolder.class.getGenericSuperclass()` 에서 `Integer` 를 어떻게 꺼내는가?
- `javap -v` 로 클래스 파일을 보면 어느 속성에 제네릭이 남아 있는가?
- 19번의 "소거"와 이 사실은 모순인가?

### 9. 애너테이션과 예외 감싸기 (예측)

```java
@Retention(RUNTIME) @interface Keep {}
@Retention(CLASS)   @interface Gone {}
@Retention(SOURCE)  @interface Never {}
@Retention(RUNTIME) @Inherited @interface Passed {}

@Keep @Gone @Never @Passed class Marked { }
class Sub extends Marked {}
```

- `Marked.class.getAnnotations()` 에 몇 개가 나오는가, 무엇인가?
- `Sub.class.getAnnotations()` 와 `getDeclaredAnnotations()` 는 각각 무엇인가?
- `invoke` 한 메서드가 `IllegalStateException` 을 던지면 호출부는 **무엇을** 받는가?
- 인자 타입이 안 맞으면 무슨 예외인가?

### 10. 비용 (예측)

- 1000만 회 기준, 직접 호출과 `Method.invoke` 는 몇 배 차이인가?
- `setAccessible(true)` 를 미리 해 두면 `invoke` 가 빨라지는가?
- 첫 회차가 느린 이유는 무엇인가?
- `getDeclaredField` 를 100만 번 부르면 얼마나 걸리는가 — 왜 공짜가 아닌가?
- 이 수치에서 재현되는 것은 무엇인가?

### 11. 무엇이 계약이고 무엇이 구현인가 (경계)

- 예외 **타입**과 예외 **메시지**는 각각 어느 쪽인가?
- `getDeclaredFields()` 의 **순서**는 보장되는가 — 근거 문장을 댈 수 있는가?
- 메시지에 나오는 `unnamed module @2f0e140b` 의 해시는 대조에 쓸 수 있는가?
- `InaccessibleObjectException` 이 **비검사** 예외인 것이 JDK 업그레이드에 주는 함의는 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- `import` 를 넣으면 `Class.forName("List")` 가 되는가?
- `setAccessible` 이 우회하는 것은 어느 주제의 무엇인가?
- 리플렉션 대신 쓸 수 있는 현대적 대안은 무엇이고, 그것도 모듈 경계에 막히는가?
- 프레임워크가 `Field`·`Method` 를 캐시하는 이유를 수치로 설명할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
