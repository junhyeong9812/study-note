# 06. 람다 내부 동작

> 이번 대화의 핵심 질문: **"람다가 캡처한 값의 타입이 왜 문제가 되나?"**

## 1. 람다는 "코드 조각"이 아니라 **객체**다

람다에도 클래스가 있고, 그 사실은 한 줄로 확인된다.

```java
Supplier<String> s = () -> "hello";
System.out.println(s.getClass());   // class Study$$Lambda/0x000078... — 클래스가 있다!
```

람다를 쓰면 JVM이 런타임에 **그 인터페이스를 구현한 클래스를 만들어** 인스턴스를 하나 찍어낸다. 즉 힙에 객체가 생긴다.

### 컴파일 결과

javac는 람다 본문을 **캡처하는 클래스의 private 메서드**로 옮기고, 그 자리에 `invokedynamic` 명령을 남긴다.

```java
// 소스
this.annotatedElementSupplier = () -> AnnotatedElementAdapter.from(field.getAnnotations());

// 컴파일 결과 (개념적으로)
private static AnnotatedElementAdapter lambda$new$1(Field field) {     // ← 본문이 메서드로 이동
    return AnnotatedElementAdapter.from(field.getAnnotations());
}
// 생성자 안에는: invokedynamic → LambdaMetafactory 가 런타임에 구현체를 만들어 준다
```

`.class` 파일의 `BootstrapMethods` 속성에 "이 invokedynamic은 `LambdaMetafactory`로 `lambda$new$1`을 감싼 `AnnotatedElementSupplier`를 만들라"는 지시가 들어 있다.

## 2. 캡처(capture)

람다가 **바깥 변수를 쓰면** 그 값이 람다 객체 안에 저장된다.

```java
void demo() {
    int base = 10;
    IntUnaryOperator add = x -> x + base;   // base 를 캡처
}
```

캡처 여부에 따라 람다 객체가 붙드는 것이 달라진다.

| 종류 | 예 | 람다 객체가 붙드는 것 |
|---|---|---|
| **비캡처(non-capturing)** | `() -> "hello"` | 없음 — JVM이 인스턴스를 **재사용**한다 |
| **캡처(capturing)** | `() -> field.getAnnotations()` | `field` 참조 — 호출할 때마다 **새 인스턴스** |

캡처는 **람다가 생성되는 시점(런타임)** 에 일어난다. 값을 복사해 넣는 것이므로, 캡처 대상 지역변수는 `final`이거나 사실상 final이어야 한다.

> **주의**: 참조형을 캡처하면 "참조값"이 복사될 뿐, 가리키는 객체는 공유된다. 그래서 `field` 객체 자체가 람다에 묶여 GC되지 않는다.

## 3. `Serializable` 람다

기본적으로 람다는 직렬화되지 않는다.

```java
Supplier<String> plain = () -> "hi";
new ObjectOutputStream(out).writeObject(plain);   // NotSerializableException
```

직렬화하려면 타깃 타입이 `Serializable`을 함께 상속해야 한다. C4의 인터페이스가 정확히 그 형태다.

```java
private interface AnnotatedElementSupplier extends Supplier<AnnotatedElementAdapter>, Serializable {
}
```

이때 컴파일러는 두 가지를 더 한다.

1. `LambdaMetafactory.altMetafactory`로 **직렬화 플래그**를 켜서 람다를 만든다 -> 만들어진 람다 객체에 `writeReplace()`가 생긴다
2. 캡처하는 클래스(`TypeDescriptor`)에 **`$deserializeLambda$`** 라는 private static 메서드를 자동 생성한다

## 4. 직렬화되면 무엇이 실리나 — `SerializedLambda`

람다 객체의 `writeReplace()`가 자기 자신 대신 `java.lang.invoke.SerializedLambda`를 내보낸다. 그 안에 들어가는 것:

| 필드 | C4의 경우 |
|---|---|
| `capturingClass` | `org.springframework.core.convert.TypeDescriptor` |
| `functionalInterfaceClass` / `MethodName` | `...TypeDescriptor$AnnotatedElementSupplier` / `get` |
| `implClass` / `implMethodName` | `TypeDescriptor` / `lambda$new$1` |
| `instantiatedMethodType` | 시그니처 문자열 |
| **`capturedArgs`** | **`[java.lang.reflect.Field 인스턴스]`** <- 문제의 지점 |

`capturedArgs`는 그냥 `Object[]`다. 직렬화기는 이 배열의 원소를 **평범한 객체처럼 하나씩 직렬화**한다. 그래서:

```
Field 는 Serializable 이 아니다  →  NotSerializableException: java.lang.reflect.Field
```

**요점: 람다를 되살리려면 그 람다가 쓰는 재료도 함께 되살려야 한다. 재료가 직렬화 불가능하면 람다 전체가 직렬화 불가능하다.**

### 역직렬화

`SerializedLambda`의 `readResolve()`가 `capturingClass`의 `$deserializeLambda$`를 호출해서 람다를 재조립한다. 그래서 **받는 쪽에도 그 클래스가 있어야 하고, 메서드 시그니처가 같아야 한다.** 리팩터링으로 람다 순서가 바뀌면 `lambda$new$1` 같은 합성 이름이 달라져 예전 스트림을 못 읽는 일이 생긴다(직렬화 람다의 알려진 취약점).

## 5. C4의 네 생성자 비교

네 생성자가 각각 무엇을 캡처하는지 늘어놓으면 결과가 갈리는 이유가 보인다.

```java
new TypeDescriptor(field)            → 캡처: Field            → X
new TypeDescriptor(methodParameter)  → 캡처: MethodParameter  → X
new TypeDescriptor(property)         → 캡처: Property         → X
new TypeDescriptor(rt, type, anns)   → 캡처: Annotation[]     → O (annotation 프록시는 Serializable)
```

네 번째만 통과한다. 그리고 기존 테스트 `serializable()`이 하필 이 경로(`forObject("")` -> 4번 생성자, `annotations = null`)만 밟고 있어서 회귀가 CI를 통과했다.

수정 후 `readObject`가 설치하는 람다는 이렇게 다르다.

```java
this.annotatedElementSupplier = () -> annotatedElement;   // 캡처: AnnotatedElementAdapter (Serializable)
```

재료(`Field`)가 아니라 **완성된 결과**를 캡처한다. 게다가 그 필드는 `transient`라 다시 직렬화될 일도 없다.

## 6. 손으로 확인하기

캡처 대상만 바꿔 가며 라운드트립해 보면 차이가 그대로 드러난다.

```java
import java.io.*;
import java.lang.reflect.Field;
import java.util.function.Supplier;

public class LambdaCapture {
    interface SerializableSupplier<T> extends Supplier<T>, Serializable {}

    static String name = "target";

    public static void main(String[] args) throws Exception {
        Field field = LambdaCapture.class.getDeclaredField("name");

        // (1) 비캡처 람다 — 재사용되는 인스턴스
        Supplier<String> a = () -> "hi";
        Supplier<String> b = () -> "hi";
        System.out.println("비캡처 같은 인스턴스? " + (a == b));    // 보통 false (다른 람다식이라 다른 클래스)

        // (2) 직렬화 가능 람다 + 직렬화 가능한 캡처
        SerializableSupplier<String> ok = () -> "captured:" + 42;
        System.out.println("ok   : " + roundTrip(ok).get());

        // (3) 직렬화 가능 람다 + 직렬화 불가능한 캡처
        SerializableSupplier<String> bad = () -> field.getName();
        try {
            roundTrip(bad);
        }
        catch (Exception ex) {
            System.out.println("bad  : " + ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }

        // (4) 같은 동작인데 결과만 캡처하면 통과한다
        String resolved = field.getName();
        SerializableSupplier<String> fixed = () -> resolved;
        System.out.println("fixed: " + roundTrip(fixed).get());
    }

    @SuppressWarnings("unchecked")
    static <T> SerializableSupplier<T> roundTrip(SerializableSupplier<T> s) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(out)) {
            oos.writeObject(s);
        }
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(out.toByteArray()))) {
            return (SerializableSupplier<T>) ois.readObject();
        }
    }
}
```

기대 출력:

```
비캡처 같은 인스턴스? false
ok   : captured:42
bad  : NotSerializableException: java.lang.reflect.Field
fixed: name
```

(3)과 (4)가 C4의 before/after를 그대로 축약한 것이다 — **하는 일은 같은데 캡처하는 것만 바꿨더니 직렬화가 된다.**

## 정리

1. 람다는 런타임에 만들어지는 **객체**이고, 바깥 변수를 쓰면 그 값을 **필드로 붙든다**(캡처).
2. 캡처는 **람다가 생성될 때**(생성자 실행 시점) 일어난다.
3. `Serializable` 람다는 `SerializedLambda`로 직렬화되며, 그 안의 `capturedArgs`가 통째로 직렬화된다.
4. 그래서 **캡처값의 타입이 직렬화 가능해야** 람다가 직렬화된다.
5. C4의 수정은 "재료를 캡처하는 람다"를 "결과를 캡처하는 람다"로 바꾼 것.
