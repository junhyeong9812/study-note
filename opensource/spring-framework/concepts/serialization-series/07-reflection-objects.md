# 07. 리플렉션 객체 — `Field`·`Method`·`MethodParameter`

> 이번 케이스에서 직렬화를 막은 장본인들. **이것들이 정확히 무엇인지**를 알면 왜 직렬화가 안 되는지가 자연히 따라온다.

## 1. 리플렉션이란

프로그램이 **자기 자신의 구조를 런타임에 들여다보는 것**이다. 클래스에 어떤 필드·메서드·어노테이션이 있는지 코드로 물어볼 수 있다.

```java
Class<?> clazz = MyBean.class;                       // 클래스에 대한 런타임 표현
Field field = clazz.getDeclaredField("name");        // 그 안의 필드 하나
Method method = clazz.getMethod("getName");          // 메서드 하나
Annotation[] annotations = field.getAnnotations();   // 필드에 붙은 어노테이션들
```

Spring이 하는 일의 상당 부분이 이것이다 — `@Autowired`가 붙은 필드를 찾고, `@RequestMapping`이 붙은 메서드를 찾고, 그 타입을 해석한다.

## 2. `Field`는 값이 아니라 **"설계도의 한 칸"** 이다

여기서 오해하기 쉬운 지점이 하나 있다.

```java
Field field = MyBean.class.getDeclaredField("name");
```

`field`는 **어떤 특정 객체의 `name` 값**이 아니다. **"`MyBean`이라는 클래스에 `name`이라는 필드가 있다"는 사실 자체**를 가리키는 객체다. 값을 꺼내려면 대상 인스턴스를 따로 줘야 한다.

```java
MyBean bean = new MyBean();
Object value = field.get(bean);      // 이제서야 값
```

`Field` 인스턴스는 JVM이 **클래스 메타데이터로부터 만들어 낸 뷰**이고, 내부적으로 클래스·슬롯 번호·타입·접근 플래그 같은 것을 들고 있다.

## 3. 그래서 왜 `Serializable`이 아닌가

`java.lang.reflect.Field`·`Method`·`Constructor`는 `Serializable`을 구현하지 않는다. 이유를 이해하면 자연스럽다.

| 이유 | 설명 |
|---|---|
| **JVM 내부 상태에 묶여 있다** | 슬롯 인덱스, 접근 플래그 override, 캐시된 accessor 등 그 JVM에서만 의미가 있는 값을 들고 있다 |
| **다른 JVM에 그대로 옮길 수 없다** | 클래스가 다른 버전이면 슬롯 자체가 달라진다 |
| **되살릴 정보는 이름으로 충분하다** | "어느 클래스의 어떤 이름의 필드"만 알면 받는 쪽에서 다시 찾으면 된다 |

마지막 항목이 실무적 해법이다. Spring도 정확히 그렇게 한다.

```java
// SerializableTypeWrapper.FieldTypeProvider — Spring 이 같은 문제를 푼 방식
static class FieldTypeProvider implements TypeProvider {

    private final String fieldName;              // 이름은 직렬화한다 (String)
    private final Class<?> declaringClass;       // 클래스도 직렬화된다 (Class 는 Serializable)

    private transient Field field;               // Field 자체는 실어 보내지 않는다

    private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
        inputStream.defaultReadObject();
        try {
            this.field = this.declaringClass.getDeclaredField(this.fieldName);   // 받는 쪽에서 다시 찾는다
        }
        catch (Throwable ex) {
            throw new IllegalStateException("Could not find original class structure", ex);
        }
    }
}
```

**"객체를 보내지 말고, 그 객체를 다시 만들 수 있는 정보를 보낸다."** — 리플렉션 객체를 직렬화 경계 너머로 옮기는 표준 패턴이다.

> C4의 수정은 이 패턴을 쓰지 않았다. 어노테이션 결과(`AnnotatedElementAdapter`)만 있으면 되므로 `Field`를 되살릴 필요 자체가 없었기 때문이다. 목적이 다르면 해법도 달라진다.

## 4. `Class`는 직렬화된다 (예외)

리플렉션 객체 중에서 `Class`만은 그대로 실린다.

```java
Class<?> type;   // 이건 실린다
```

`java.lang.Class`는 `Serializable`이다. 다만 특별 취급을 받아서 **이름만 실리고**, 역직렬화할 때 받는 쪽 classpath에서 그 이름으로 다시 찾는다. 없으면 `ClassNotFoundException`. 결국 3번의 패턴을 JDK가 내장해 둔 셈이다.

`TypeDescriptor`의 `type` 필드가 문제없이 직렬화되는 이유다.

## 5. Spring의 리플렉션 래퍼들

이 케이스에 등장하는 타입들의 직렬화 가능 여부를 한자리에 놓으면 다음과 같다.

| 클래스 | 무엇인가 | Serializable |
|---|---|---|
| `java.lang.reflect.Field` | 필드 메타데이터 | 아니오 |
| `java.lang.reflect.Method` | 메서드 메타데이터 | 아니오 |
| `java.lang.Class` | 클래스 (이름으로 복원) | 예 |
| `org.springframework.core.MethodParameter` | **메서드의 특정 파라미터**(또는 반환값, index = -1)를 가리키는 Spring 래퍼. 중첩 레벨·제네릭 컨텍스트도 함께 | 아니오 |
| `org.springframework.core.convert.Property` | getter/setter **쌍**을 하나의 "프로퍼티"로 묶은 Spring 래퍼 | 아니오 |
| `org.springframework.core.ResolvableType` | 제네릭까지 해석 가능한 타입 표현 | 예 (`SerializableTypeWrapper` 덕분) |

`MethodParameter`와 `Property`가 직렬화 불가인 이유는 단순하다 — 내부에 `Method`/`Field`를 들고 있다.

`ResolvableType`이 직렬화 가능한 것은 공짜가 아니다. 내부의 `Type`을 `SerializableTypeWrapper`로 감싸서 위 3번 패턴을 적용해 두었기 때문이다. **다만 그 래핑이 모든 경우를 덮지는 못한다** — 이번 작업에서 `getElementTypeDescriptor()`가 `NotSerializableException: TypeVariableImpl`로 실패하는 것을 확인했다(별건).

## 6. 어노테이션 인스턴스는 무엇인가

런타임에 손에 쥐는 어노테이션의 실체는 동적 프록시다.

```java
Annotation[] annotations = field.getAnnotations();
System.out.println(annotations[0].getClass());
// class jdk.proxy1.$Proxy5   ← 실제 클래스가 아니라 동적 프록시
```

어노테이션은 인터페이스이고, 런타임에 얻는 인스턴스는 **JDK 동적 프록시**다. 내부 핸들러(`AnnotationInvocationHandler`)가 `Serializable`이라 **어노테이션 인스턴스는 직렬화된다.**

직렬화될 때는 "어노테이션 타입 이름 + 멤버 값들"이 실리고, 역직렬화할 때 받는 쪽에서 그 타입을 찾아 프록시를 새로 만든다. 여기서도 **클래스가 아니라 이름이 오간다**는 원칙이 같다.

이 사실이 C4에서 결정적이었다. `AnnotatedElementAdapter`는 `Annotation[]` 하나만 들고 있으므로 통째로 직렬화 가능하고, 그래서 **어댑터를 통로로 삼는 수정이 성립**했다.

## 7. 손으로 확인하기

무엇이 실리고 무엇이 막히는지를 한 파일로 확인할 수 있다.

```java
import java.io.*;
import java.lang.annotation.*;
import java.lang.reflect.Field;

public class ReflectionSerialization {
    @Retention(RetentionPolicy.RUNTIME)
    @interface Marker { String value(); }

    @Marker("hello") static String target;

    public static void main(String[] args) throws Exception {
        Field field = ReflectionSerialization.class.getDeclaredField("target");

        System.out.println("Field 는 값이 아니다      : " + field);
        System.out.println("어노테이션 인스턴스 클래스 : " + field.getAnnotations()[0].getClass());

        probe("Field",         field);
        probe("Class",         ReflectionSerialization.class);
        probe("Annotation[]",  field.getAnnotations());
        probe("String(이름)",   field.getName());
    }

    static void probe(String label, Object o) {
        try (ObjectOutputStream out = new ObjectOutputStream(OutputStream.nullOutputStream())) {
            out.writeObject(o);
            System.out.println("OK   " + label);
        }
        catch (Exception ex) {
            System.out.println("FAIL " + label + " -> " + ex.getClass().getSimpleName() + ": " + ex.getMessage());
        }
    }
}
```

기대 출력:

```
Field 는 값이 아니다      : static java.lang.String ReflectionSerialization.target
어노테이션 인스턴스 클래스 : class jdk.proxy1.$Proxy1
OK   Field?  → 아니다. FAIL Field -> NotSerializableException: java.lang.reflect.Field
OK   Class
OK   Annotation[]
OK   String(이름)
```

`Field`는 안 되지만 **그것을 다시 찾는 데 필요한 재료(`Class` + 이름)는 전부 직렬화된다** — 3번 패턴이 성립하는 이유가 이 출력에 다 들어 있다.

## 정리

1. `Field`/`Method`는 값이 아니라 **클래스 구조에 대한 런타임 뷰**이며, JVM 내부 상태에 묶여 있어 직렬화되지 않는다.
2. 표준 해법은 **"객체 대신 이름을 보내고 받는 쪽에서 다시 찾기"**(Spring `SerializableTypeWrapper`, JDK의 `Class` 처리).
3. `Class`와 어노테이션 인스턴스는 직렬화된다 — 둘 다 이름 기반 복원이다.
4. C4는 재료를 복원할 필요가 없어서, 결과물(`AnnotatedElementAdapter`)만 실어 보내는 더 단순한 길을 택했다.
