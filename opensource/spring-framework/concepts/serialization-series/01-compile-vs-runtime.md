# 01. 컴파일 시점 vs 런타임 시점

> 이번 대화에서 나온 오해: **"직렬화가 안 되면 컴파일 오류가 나는 것 아닌가?"** -> 아니다. 컴파일은 100% 성공한다.

## 1. 두 시점에 각각 무슨 일이 일어나나

소스 한 벌은 두 시점을 지나면서 서로 다른 것으로 바뀐다.

```
[작성]  Foo.java  ──javac──▶  Foo.class          ──JVM──▶  실행 중인 객체들
         소스              바이트코드 + 메타데이터            힙 위의 인스턴스
        ↑ 컴파일 시점(build time)                  ↑ 런타임(run time)
```

| | 컴파일 시점 (javac) | 런타임 (JVM) |
|---|---|---|
| 다루는 것 | **타입 정보** | **값(인스턴스)** |
| 결과물 | `.class` 파일 | 힙 위의 객체, 스레드, 스택 |
| 실패하면 | 컴파일 에러 | 예외(Exception/Error) |

## 2. javac가 검사하는 것

javac가 잡아 주는 것은 전부 타입 수준에서 판정할 수 있는 규칙이다.

- 타입 일치 (`String s = 1;` -> 에러)
- 제네릭 규칙 (`List<String>`에 `Integer` 넣기 -> 에러)
- `final` 변수 재대입 (에러)
- checked exception 처리 여부 (`throws` / `try-catch`)
- 접근 제어자 위반, 미구현 추상 메서드, 도달 불가 코드 등

## 3. javac가 **검사하지 않는 것**

반대로 실제 값이 무엇이냐에 달린 것은 컴파일러가 판정하지 못한다.

- **어떤 값이 `Serializable`인지 아닌지** -> 직렬화 가능 여부는 컴파일러의 관심사가 아니다
- 참조가 런타임에 `null`인지
- 다운캐스트가 실제로 성공할지 (`(String) obj` -> `ClassCastException`은 런타임)
- 배열 인덱스 범위
- 리플렉션으로 무엇을 찾을지 (`getField("name")` — 이름은 그냥 문자열이다)

즉 **"이 객체를 바이트로 바꿀 수 있는가"는 실제로 바꿔보려고 시도하는 순간에만 알 수 있다.**

## 4. C4 케이스에 대입

앞의 구분을 C4의 생성자 한 줄에 그대로 대입해 본다.

```java
public TypeDescriptor(Field field) {
    this.annotatedElementSupplier = () -> AnnotatedElementAdapter.from(field.getAnnotations());
}
```

단계별 결과는 마지막 한 칸에서만 갈린다.

| 단계 | 결과 |
|---|---|
| `javac` | 성공. `Field`가 `Serializable`이 아니라는 사실은 검사 대상이 아님 |
| `new TypeDescriptor(field)` | 성공. 힙에 객체 생성 |
| `td.getAnnotations()` | 성공. 정상 동작 |
| `objectOutputStream.writeObject(td)` | 실패 — `NotSerializableException: java.lang.reflect.Field` |

실제로 이번 작업의 RED 테스트에서도 Gradle 로그에 `> Task :spring-core:compileTestJava` 가 **성공**으로 찍힌 뒤, 테스트 **실행 단계**에서 실패했다. 컴파일 문제였다면 테스트가 시작조차 못 했을 것이다.

## 5. 제네릭은 컴파일 시점 개념이다 (타입 소거)

이번 대화에서 나온 또 다른 오해: `extends Supplier<AnnotatedElementAdapter>, Serializable`을 "`AnnotatedElementAdapter`의 부모를 상속한다"로 읽은 것.

```java
private interface AnnotatedElementSupplier extends Supplier<AnnotatedElementAdapter>, Serializable {
}
```

읽는 법:

```
extends Supplier<AnnotatedElementAdapter>   ← Supplier 인터페이스를 상속. get()의 반환 타입이 AnnotatedElementAdapter
       , Serializable                        ← 동시에 Serializable 도 상속 (인터페이스는 다중 상속 가능)
```

`<...>` 안은 **상속 대상이 아니라 타입 인자**다. 그리고 이 정보는 **컴파일 시점에만 존재**한다 — 런타임에는 소거되어 `Supplier`의 `get()`은 그냥 `Object`를 반환하는 것으로 동작하고, 컴파일러가 넣어준 캐스트가 대신 붙는다.

```java
List<String> a = new ArrayList<>();
List<Integer> b = new ArrayList<>();
System.out.println(a.getClass() == b.getClass());   // true — 런타임엔 둘 다 그냥 ArrayList
```

## 6. `.class` 파일에는 무엇이 들어 있나

바이트코드만 있는 게 아니다.

- 상수 풀(constant pool) — 문자열·클래스명·메서드 시그니처
- 메서드 바이트코드
- 필드 테이블 (이름, 타입, **`transient`/`volatile` 같은 수식자 플래그**)
- `BootstrapMethods` 속성 — 람다(invokedynamic)가 쓰는 정보 -> [06 문서](06-lambda-internals.md)
- 어노테이션 정보 (`RetentionPolicy.RUNTIME`인 것만 런타임까지 살아남음)

`transient`가 컴파일러에게 하는 말은 없다. **필드 플래그로 `.class`에 기록되어 두었다가, 런타임에 직렬화기가 그 플래그를 읽는다.** 이것이 "컴파일 시점에 기록되고 런타임에 해석되는" 전형적인 예다.

## 7. 손으로 확인하기

같은 타입의 두 객체가 담긴 값 때문에 갈리는 것을 다음 프로그램으로 확인할 수 있다.

```java
import java.io.*;

public class CompileVsRuntime {
    static class Box implements Serializable {
        Object payload;                       // 컴파일러는 여기에 뭐가 들어올지 모른다
        Box(Object payload) { this.payload = payload; }
    }

    public static void main(String[] args) throws Exception {
        Box ok  = new Box("hello");                        // String 은 Serializable
        Box bad = new Box(new Object());                   // Object 는 Serializable 아님

        System.out.println("두 줄 다 컴파일됨 + 객체 생성됨");

        write(ok);    // OK
        write(bad);   // NotSerializableException: java.lang.Object
    }

    static void write(Object o) {
        try (ObjectOutputStream out = new ObjectOutputStream(OutputStream.nullOutputStream())) {
            out.writeObject(o);
            System.out.println("OK   " + o);
        }
        catch (Exception ex) {
            System.out.println("FAIL " + ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
    }
}
```

같은 `Box` 타입인데 담긴 값에 따라 런타임 결과가 갈린다 — 컴파일러가 막을 수 없는 이유가 이것이다.

## 정리

1. 컴파일러는 **타입**을 보고, JVM은 **값**을 본다.
2. `Serializable` 여부는 값의 문제라 **런타임에만** 드러난다.
3. `transient`/`volatile`은 컴파일 시점에 `.class`의 플래그로 기록되고, 런타임에 각각 직렬화기/메모리 모델이 읽는다.
4. 제네릭 타입 인자는 컴파일 시점 개념이며 상속 관계와 무관하다.
