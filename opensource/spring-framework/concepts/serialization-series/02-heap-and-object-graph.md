# 02. 힙과 객체 그래프

> 이번 대화에서 나온 오해: **"객체를 힙에 올리는 순간 직렬화가 일어난다"** -> 아니다. 둘은 완전히 별개다.

## 1. 스택과 힙

변수는 스택에 있고 객체는 힙에 있다. 이 구분이 뒤의 모든 이야기의 바탕이다.

```java
void doWork() {
    TypeDescriptor td = new TypeDescriptor(field);
    //              ↑ 이 '변수'는 스택에 있다 (참조값 = 주소)
    //                        ↑ 실제 '객체'는 힙에 있다
}
```

```
   스택 (스레드마다 하나)              힙 (JVM 전체가 공유)
   ┌───────────────┐                ┌──────────────────────────┐
   │ td = 0x7f3a.. │───────────────▶│ TypeDescriptor@7f3a      │
   │ field = 0x91c │──┐             │  type = 0x22b            │──▶ Class@22b
   └───────────────┘  │             │  resolvableType = 0x55d  │──▶ ResolvableType@55d
                      │             │  supplier = 0x88e        │──▶ Lambda@88e
                      │             │  annotatedElement = null │      └ field = 0x91c ─┐
                      │             └──────────────────────────┘                        │
                      └───────────────────────────────────────────────────────────────▶ Field@91c
```

**핵심**: 객체는 필드를 통해 다른 객체를 가리키고, 그 객체가 또 다른 객체를 가리킨다. 이 연결 전체를 **객체 그래프(object graph)** 라고 부른다.

## 2. 객체 생성 주기 — `new`가 하는 일

`new` 한 줄은 다음 순서로 진행된다.

```java
new TypeDescriptor(field)
```

1. 힙에 `TypeDescriptor` 크기만큼 공간 확보
2. 모든 필드를 **기본값**으로 초기화 (참조형 `null`, `int` `0`, `boolean` `false`)
3. 부모 생성자 실행 (여기서는 `Object()`)
4. 필드 초기화식 실행
5. **생성자 본문 실행** <- 여기서 `this.annotatedElementSupplier = () -> ...` 가 실행됨
6. `new` 표현식이 그 객체의 참조를 반환

이 5단계 어디에도 직렬화는 없다. **직렬화는 누군가 `writeObject()`를 호출해야만 시작된다.**

> 주의: 역직렬화는 이 순서를 따르지 않는다 — 생성자를 건너뛴다. [05 문서](05-serialization-hooks.md) 참고.

## 3. 도달 가능성과 GC

객체의 수명은 누가 그것을 가리키고 있느냐가 정한다.

```java
TypeDescriptor td = new TypeDescriptor(field);
td = null;   // 이제 아무도 그 객체를 가리키지 않는다 → GC 대상
```

GC는 **루트(스택 변수, static 필드 등)에서 참조를 타고 갈 수 있는가**로 살릴지 정한다. 여기서 중요한 사실 하나:

> **람다가 캡처한 값도 참조다.** `() -> field.getAnnotations()` 람다가 살아 있는 한, 그 `Field` 객체도 GC되지 않는다.

C4에서 `TypeDescriptor`가 `Field`를 계속 붙들고 있었던 것은 메모리 관점에서도 의미가 있다(리플렉션 객체 유지). 직렬화 문제와는 별개지만, "람다가 값을 붙든다"는 사실은 동일하다.

## 4. 직렬화는 객체 그래프 순회다

`writeObject(td)`가 하는 일은 **위 그래프를 깊이 우선으로 훑으면서 각 객체의 상태를 바이트로 옮기는 것**이다.

```
writeObject(td)
 └─ TypeDescriptor@7f3a
     ├─ type            → Class@22b            O Class 는 직렬화 가능
     ├─ resolvableType  → ResolvableType@55d   O Serializable
     │                     └─ (내부 참조들도 계속 따라간다)
     ├─ annotatedElement→ null                 O null 은 그냥 null 로 기록
     └─ supplier        → Lambda@88e           → SerializedLambda 로 변환
                            └─ capturedArgs[0] → Field@91c
                                                 X Field 는 Serializable 아님
                                                 ! NotSerializableException
```

그래서 예외 메시지가 `NotSerializableException: java.lang.reflect.Field` — **어느 클래스에서 막혔는지**를 알려준다. 그래프 순회 중 막힌 지점이다.

### 그래프의 두 가지 특성

**(1) 순환 참조도 처리된다.** 직렬화기는 이미 쓴 객체에 **핸들(번호)** 을 매겨두고, 같은 객체를 또 만나면 핸들만 기록한다. 그래서 A->B->A 같은 순환도 무한루프에 빠지지 않는다.

**(2) 같은 스트림 안에서는 동일성이 보존된다.**

```java
Object shared = new ArrayList<>();
List<Object> list = List.of(shared, shared);   // 같은 객체를 두 번 참조

// 직렬화 → 역직렬화 후에도
readList.get(0) == readList.get(1)   // true — 핸들 덕분에 하나로 복원된다
```

단 이것은 **한 스트림 안에서만**이다. 스트림 밖의 JVM 싱글턴과는 아무 관계가 없다 -> 이것이 [08 문서](08-identity-and-singleton.md)의 EMPTY 문제로 이어진다.

## 5. lazy 초기화 — 힙 관점에서

C4의 `TypeDescriptor`는 "필요할 때만 만든다" 패턴을 쓴다.

```java
private volatile @Nullable AnnotatedElementAdapter annotatedElement;   // 처음엔 null

private AnnotatedElementAdapter getAnnotatedElement() {
    AnnotatedElementAdapter annotatedElement = this.annotatedElement;   // (1) 로컬로 한 번 읽고
    if (annotatedElement == null) {
        annotatedElement = this.annotatedElementSupplier.get();          // (2) 없으면 만들어서
        this.annotatedElement = annotatedElement;                        // (3) 필드에 저장(캐시)
    }
    return annotatedElement;
}
```

힙 상태 변화:

```
생성 직후          : annotatedElement = null          (어댑터 객체 없음)
getAnnotations() 후: annotatedElement = Adapter@a1b   (어댑터 객체 생성됨)
```

**아무도 호출하지 않으면 어댑터는 영원히 만들어지지 않는다.** 이것이 gh-33948이 노린 절약이고, C4에서 "직렬화 직전에 강제로 한 번 호출해야 하는" 이유이기도 하다.

`(1)`처럼 필드를 로컬 변수로 한 번만 읽는 것도 의도적이다 — `volatile` 읽기 횟수를 줄이고, 읽는 사이에 값이 바뀌어도 일관되게 동작하도록. -> [04 문서](04-transient-and-volatile.md)

## 6. 손으로 확인하기

순환 참조가 무한루프가 되지 않는 것과 동일성이 어디까지 보존되는지를 한 파일로 확인할 수 있다.

```java
import java.io.*;
import java.util.*;

public class ObjectGraph {
    static class Node implements Serializable {
        String name;
        Node next;                       // 다른 객체를 가리키는 참조
        Node(String name) { this.name = name; }
    }

    public static void main(String[] args) throws Exception {
        Node a = new Node("A");
        Node b = new Node("B");
        a.next = b;
        b.next = a;                      // 순환 참조!

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ObjectOutputStream(out).writeObject(a);      // 무한루프 안 빠진다

        Node readA = (Node) new ObjectInputStream(
                new ByteArrayInputStream(out.toByteArray())).readObject();

        System.out.println(readA.name);                       // A
        System.out.println(readA.next.name);                  // B
        System.out.println(readA.next.next == readA);         // true — 동일성 보존
        System.out.println(readA == a);                       // false — 원본과는 다른 객체
    }
}
```

마지막 두 줄이 핵심이다. **스트림 안에서는 동일성이 유지되지만, 원본 객체와는 완전히 별개의 새 객체**다.

## 정리

1. 객체는 힙에, 참조는 서로를 가리키며 **그래프**를 이룬다.
2. `new`는 객체를 만들 뿐, 직렬화와 무관하다.
3. 직렬화 = **그래프 순회**. 순회 중 직렬화 불가능한 객체를 만나면 그 자리에서 예외.
4. 람다가 캡처한 값도 그래프의 일부다 — 그래서 `Field`까지 따라간다.
5. 스트림 안에서는 동일성이 보존되지만, JVM 싱글턴과의 동일성은 보존되지 않는다.
