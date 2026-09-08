# 05. 직렬화 훅 메서드 — 생성자를 우회하는 객체 생성

> 이번 대화에서 나온 오해: **"`writeObject`는 서로 다른 객체를 주입하는 것"** -> 아니다. 직렬화 시점에 **무엇을 내보낼지 결정**하는 훅이다.

## 1. 역직렬화는 생성자를 부르지 않는다

이 사실 하나가 이 문서 전체의 전제다.

```java
class Foo implements Serializable {
    int value;
    Foo() {
        System.out.println("생성자 실행!");
        this.value = 42;
    }
}
```

`Foo`를 직렬화했다가 되살리면 **"생성자 실행!"이 출력되지 않는다.** JVM은 다음 순서로 객체를 만든다.

```
1. 힙에 인스턴스 공간 확보 (필드는 전부 기본값)
2. Serializable 이 아닌 첫 부모 클래스의 no-arg 생성자만 실행
   (TypeDescriptor 의 경우 부모가 Object 이므로 Object() 만)
3. 스트림에서 읽은 값을 필드에 직접 밀어 넣음  ← 대입식·생성자 로직 없이
4. readObject 훅이 있으면 호출
```

**따라서 생성자·정적 팩토리에 넣어둔 어떤 규칙도 역직렬화 경로에는 적용되지 않는다.** 유효성 검사, 싱글턴 보장, 캐시 등록 — 전부 우회된다. C4의 `AnnotatedElementAdapter.from()` 싱글턴 규칙이 깨지는 이유가 정확히 이것이다([08 문서](08-identity-and-singleton.md)).

## 2. 훅 메서드 4종

이 메서드들은 인터페이스 구현이 아니다. **약속된 이름·시그니처의 private 메서드를 직렬화기가 리플렉션으로 찾아 호출**한다. 오타가 나면 조용히 무시되므로 주의.

| 훅 | 시그니처 | 언제 | 용도 |
|---|---|---|---|
| `writeObject` | `private void writeObject(ObjectOutputStream) throws IOException` | 쓰기 직전 | 무엇을 내보낼지 조정 |
| `readObject` | `private void readObject(ObjectInputStream) throws IOException, ClassNotFoundException` | 필드 복원 직후 | transient 필드 재구성, 불변식 복구 |
| `writeReplace` | `private Object writeReplace()` | 쓰기 **전** | 이 객체 대신 **다른 객체**를 직렬화 |
| `readResolve` | `private Object readResolve()` | 읽기 **후** | 복원된 객체 대신 **다른 객체**를 반환 (싱글턴 복구) |

### `writeObject` / `readObject`의 기본 골격

```java
private void writeObject(ObjectOutputStream out) throws IOException {
    // 여기서 상태를 준비한 뒤
    out.defaultWriteObject();     // ← 이 호출이 non-transient 필드를 실제로 기록
}

private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
    in.defaultReadObject();       // ← 먼저 필드를 복원하고
    // 그 다음에 transient 필드 등을 재구성
}
```

`defaultWriteObject()` / `defaultReadObject()` 를 빼먹으면 **필드가 아예 안 실리거나 안 채워진다.** 훅은 기본 동작을 대체하는 게 아니라 **감싸는** 것이다.

## 3. C4의 훅 두 개 읽기

C4가 추가한 훅은 `writeObject`와 `readObject` 둘이고, 각각 캐시 실체화와 재구성을 맡는다.

```java
private void writeObject(ObjectOutputStream outputStream) throws IOException {
    // Resolve the annotations up front since the supplier is transient: it captures
    // the Field/MethodParameter/Property this descriptor has been created from.
    getAnnotatedElement();          // (1)
    outputStream.defaultWriteObject();  // (2)
}
```

**(1)의 반환값을 버리는 게 이상해 보이지만, 목적은 반환값이 아니라 부작용이다.**

```java
private AnnotatedElementAdapter getAnnotatedElement() {
    AnnotatedElementAdapter annotatedElement = this.annotatedElement;
    if (annotatedElement == null) {
        annotatedElement = this.annotatedElementSupplier.get();
        this.annotatedElement = annotatedElement;   // 필드에 저장 — 이게 우리가 원하는 것
    }
    return annotatedElement;
}
```

(1)을 생략하면 lazy 캐시가 `null`인 채로 (2)가 실행되어 **스트림에 `annotatedElement = null`이 실린다.** 그러면 받는 쪽은 supplier(transient라 null)도 캐시(null)도 없어 어노테이션을 영구히 잃는다.

```java
private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
    inputStream.defaultReadObject();                                   // (1) 필드 복원
    AnnotatedElementAdapter annotatedElement = AnnotatedElementAdapter.from(
            this.annotatedElement != null ? this.annotatedElement.getAnnotations() : null);  // (2) 정규화
    this.annotatedElement = annotatedElement;                          // (3) 정규화된 것으로 교체
    this.annotatedElementSupplier = () -> annotatedElement;            // (4) transient 필드 재구성
}
```

- (2)의 `from(...)`은 "null 가드"가 아니라 **싱글턴 정규화**다 -> [08 문서](08-identity-and-singleton.md)
- (4)의 람다는 원래 람다와 다르다. 재료(`Field`)를 캡처하지 않고 **이미 완성된 결과만 반환**한다. 그래서 다시 직렬화될 일도 없고(필드가 transient), 캡처 문제도 없다.

### 타임라인으로 보기

```
(1) 평소 (힙에 살아있는 객체)
   supplier        = 람다 (Field 캡처, 값 있음 — transient 여도 살아있음)
   annotatedElement = null (lazy — 아무도 안 물어보면 계속 null)

(2) writeObject
   getAnnotatedElement()  → annotatedElement 채워짐
   defaultWriteObject()   → annotatedElement 실림 O / supplier 는 skip X
                            (skip 되니 Field 를 만날 일이 없어 예외가 안 남)

(3) readObject (다른 JVM, 새 객체)
   defaultReadObject()    → annotatedElement 복원 O / supplier = null
   from(...) 로 정규화     → 빈 경우 EMPTY 싱글턴 복구
   supplier = () -> adapter → 재료 없는 새 람다 설치
```

## 4. `writeReplace` / `readResolve`

객체 **자체를 바꿔치기**하는 훅이다.

```java
// 싱글턴을 직렬화해도 싱글턴으로 유지하는 고전적 관용구
private Object readResolve() {
    return INSTANCE;      // 스트림에서 복원된 객체 대신 진짜 싱글턴을 반환
}
```

`AnnotatedElementAdapter`에는 이 `readResolve()`가 **없다.** 그래서 EMPTY 싱글턴이 역직렬화를 거치면 별개 인스턴스가 되고, C4의 `readObject`가 `from(...)`으로 그 역할을 대신 수행한다.

`writeReplace`는 반대로 쓸 때 바꾼다. Spring의 `SerializableTypeWrapper`나 람다의 내부 구현이 이 방식을 쓴다(람다는 자기 자신 대신 `SerializedLambda`를 내보낸다 -> [06 문서](06-lambda-internals.md)).

## 5. 훅을 쓸 때 주의할 점

훅은 리플렉션으로 찾아 부르는 규약이라, 어긋나면 조용히 무시된다는 데서 함정이 나온다.

1. **`private`이어야 한다** — public이면 상속 관계에서 오작동하고, 직렬화기가 못 찾을 수 있다.
2. **시그니처가 정확해야 한다** — 파라미터 타입 하나만 달라도 조용히 무시된다.
3. **`default*Object()` 호출을 잊지 말 것.**
4. `readObject`는 **신뢰할 수 없는 입력**을 다룬다 — 외부에서 온 스트림이면 필드 값 검증이 필요하다(역직렬화 취약점의 근원).
5. 훅 안에서 오래 걸리는 작업·부작용은 조심 — C4의 `writeObject`는 lazy 해석을 강제하므로, 직렬화 시점에 리플렉션 호출이 한 번 일어난다(의도된 트레이드오프).

## 6. 손으로 확인하기

역직렬화가 생성자를 건너뛴다는 것을 출력으로 직접 확인할 수 있다.

```java
import java.io.*;

public class HooksDemo {
    static class WithHooks implements Serializable {
        int value;
        transient String derived;

        WithHooks(int value) {
            System.out.println("  [생성자] 실행");
            this.value = value;
            this.derived = "derived-" + value;
        }

        private void writeObject(ObjectOutputStream out) throws IOException {
            System.out.println("  [writeObject] 호출");
            out.defaultWriteObject();
        }

        private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
            System.out.println("  [readObject] 호출");
            in.defaultReadObject();
            this.derived = "derived-" + this.value;   // transient 재구성
        }

        @Override public String toString() { return value + " / " + derived; }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("생성:");
        WithHooks original = new WithHooks(7);

        System.out.println("직렬화:");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ObjectOutputStream(out).writeObject(original);

        System.out.println("역직렬화:");
        WithHooks copy = (WithHooks) new ObjectInputStream(
                new ByteArrayInputStream(out.toByteArray())).readObject();

        System.out.println("결과: " + copy);
    }
}
```

기대 출력 — **역직렬화 구간에 `[생성자] 실행`이 없다는 점**을 눈으로 확인할 것.

```
생성:
  [생성자] 실행
직렬화:
  [writeObject] 호출
역직렬화:
  [readObject] 호출
결과: 7 / derived-7
```

`readObject`에서 `derived` 재구성을 지우고 다시 돌리면 `7 / null`이 나온다 — transient 필드를 되살리는 책임이 어디에 있는지 바로 보인다.

## 정리

1. 역직렬화는 **생성자를 건너뛴다** — 생성자/팩토리의 규칙이 전부 우회된다.
2. `writeObject`/`readObject`는 약속된 이름의 private 메서드이며, `default*Object()`를 감싸는 형태로 쓴다.
3. C4의 `writeObject`는 **lazy 캐시를 강제 실체화**하는 것이 목적(반환값이 아니라 부작용).
4. C4의 `readObject`는 **정규화 + transient 재구성** 두 가지를 한다.
5. `readResolve`는 싱글턴 복구용 훅이며, 그것이 없는 클래스는 호출자가 대신 정규화해야 한다.
