# 08. 동일성과 싱글턴 — 역직렬화가 `==`를 깨는 이유

> 이번 대화에서 마지막까지 걸렸던 지점: **"빈 어댑터면 `isEmpty()`가 당연히 true 아닌가?"** -> 아니다.

## 1. `==` vs `equals`

두 비교는 묻는 질문이 다르다.

```java
String a = new String("hi");
String b = new String("hi");

a == b        // false — 힙에 있는 서로 다른 두 객체
a.equals(b)   // true  — 내용이 같다
```

- `==` (참조형) : **같은 객체인가**(동일성, identity)
- `equals()` : **같은 값인가**(동등성, equality)

## 2. 동일성 비교를 일부러 쓰는 경우

보통은 `equals`를 쓰지만, **"미리 만들어둔 그 하나"인지 확인하려는 목적**이면 `==`가 맞다.

```java
// AnnotatedElementAdapter.java
private static final AnnotatedElementAdapter EMPTY = new AnnotatedElementAdapter(new Annotation[0]);

public static AnnotatedElementAdapter from(Annotation @Nullable [] annotations) {
    if (annotations == null || annotations.length == 0) {
        return EMPTY;                                  // 빈 경우는 항상 이 인스턴스
    }
    return new AnnotatedElementAdapter(annotations);
}

public boolean isEmpty() {
    return (this == EMPTY);                            // 내용이 아니라 '그 인스턴스냐'
}
```

이렇게 쓸 수 있는 근거는 **"빈 어댑터를 만드는 길이 `from()` 하나뿐"** 이라는 것이다. 생성자가 `private`이라 외부에서 `new`로 만들 수 없다.

용도는 성능이다 — `isEmpty()`가 true면 무거운 작업을 통째로 건너뛴다.

```java
// TypeDescriptor.java
public boolean hasAnnotation(Class<? extends Annotation> annotationType) {
    AnnotatedElementAdapter annotatedElement = getAnnotatedElement();
    if (annotatedElement.isEmpty()) {
        return false;                                                        // 빠른 길
    }
    return AnnotatedElementUtils.isAnnotated(annotatedElement, annotationType);   // 무거운 길
}
```

## 3. 역직렬화가 그 전제를 깬다

**역직렬화는 생성자도 정적 팩토리도 거치지 않는다**([05 문서](05-serialization-hooks.md)). 스트림에서 읽은 값으로 필드를 직접 채운 새 객체를 만든다.

```
JVM A                                    JVM B
EMPTY (싱글턴)                           EMPTY (싱글턴)  ← 클래스 로딩 시 만들어진 것
   │ 직렬화                                 ▲
   ▼                                        │  이것과는 아무 관계없는
[ annotations = [] ]  ──── 스트림 ────▶  새 인스턴스가 생성됨
                                            │
                                     this == EMPTY  →  false
                                     isEmpty()      →  false
```

배열 길이는 0인데 `isEmpty()`는 false다. **결과값은 여전히 맞지만**(어노테이션이 없으니 `hasAnnotation`은 어차피 false를 돌려준다) 빠른 길이 죽어서 매번 무거운 경로를 탄다.

이 증상의 고약한 점은 **예외가 아니라 조용한 성능 저하**라는 것이다. 어떤 테스트도 자동으로 잡아주지 않는다.

## 4. 표준 해법 — `readResolve()`

JDK가 준비해둔 훅이 있다.

```java
private Object readResolve() {
    return (this.annotations.length == 0 ? EMPTY : this);   // 복원된 객체 대신 싱글턴을 반환
}
```

`readResolve()`가 있으면 역직렬화기가 **복원한 객체를 버리고 이 메서드가 반환한 객체를 대신 쓴다.** enum이 직렬화되어도 싱글턴이 유지되는 것도 같은 원리다(enum은 JVM이 알아서 처리).

**그런데 `AnnotatedElementAdapter`에는 이 메서드가 없다.** 그래서 C4에서는 호출하는 쪽이 대신 정규화한다.

```java
// TypeDescriptor.readObject()
AnnotatedElementAdapter annotatedElement = AnnotatedElementAdapter.from(
        this.annotatedElement != null ? this.annotatedElement.getAnnotations() : null);
```

복원된 어댑터에서 배열만 꺼내 `from()`에 다시 통과시킨다. 길이가 0이면 `from()`이 `EMPTY`를 돌려주므로 **깨졌던 동일성이 복구된다.** 이 한 줄은 null 가드가 아니라 **싱글턴 정규화(canonicalization)** 다.

> 왜 `AnnotatedElementAdapter`에 `readResolve()`를 넣지 않았나? 그 클래스는 7.0부터 public API이고 이번 작업의 금지영역이었다. 한 클래스의 내부 사정 때문에 다른 public 클래스를 건드리는 것은 범위를 넘는다. 다만 "그쪽에 `readResolve()`를 넣는 것이 더 근본적"이라는 지적은 유효하며, 별도 개선 후보로 남는다.

## 5. 스트림 안에서는 동일성이 보존된다 (헷갈리는 지점)

같은 스트림 안에서는 동일성이 실제로 보존되고, 그래서 앞 절과 헷갈리기 쉽다.

```java
Object shared = new ArrayList<>();
List<Object> list = List.of(shared, shared);
// 라운드트립 후
readList.get(0) == readList.get(1)   // true
```

같은 스트림 안에서 같은 객체를 두 번 참조하면, 직렬화기가 핸들을 써서 **하나로 복원**한다([02 문서](02-heap-and-object-graph.md)).

**하지만 이것은 스트림 내부의 이야기다.** 스트림 밖에 있는 JVM 싱글턴(`EMPTY`)과의 동일성은 전혀 보장되지 않는다. 두 개념을 섞으면 "동일성이 보존된다고 하지 않았나?"라는 혼동이 생긴다.

범위별로 정리하면 다음과 같다.

| 범위 | 동일성 |
|---|---|
| 한 스트림 안에서 같은 객체를 여러 번 참조 | 보존됨 |
| 스트림 밖 JVM의 싱글턴과 | 안 됨 (`readResolve` 없으면) |
| 원본 객체와 복원된 객체 | 언제나 다른 객체 |

## 6. 테스트로 어떻게 잡았나

`isEmpty()`는 private 필드 안쪽 이야기라 테스트에서 직접 볼 수 없다. 대신 **관측 가능한 부수 효과**를 찾았다.

```java
// AnnotatedElementAdapter.getAnnotations()
public Annotation[] getAnnotations() {
    return (isEmpty() ? this.annotations : this.annotations.clone());
}
```

EMPTY일 때만 **복사 없이 같은 배열을 그대로** 준다. 따라서:

```java
assertThat(readObject.getAnnotations()).isSameAs(readObject.getAnnotations());
```

두 번 호출해서 **같은 배열 인스턴스가 나오면 EMPTY**, 다르면(매번 clone) EMPTY가 아니다. 리플렉션 없이 싱글턴 정규화를 고정할 수 있다.

실제로 리뷰 재점검에서 정규화를 제거한 변형을 돌려보니 이 단언이 정확히 깨지는 것을 확인했다.

## 7. 손으로 확인하기

싱글턴이 라운드트립에서 깨지는 것과 `readResolve`가 그것을 되돌리는 것을 한 파일로 확인할 수 있다.

```java
import java.io.*;

public class SingletonAndSerialization {
    static class Marker implements Serializable {
        static final Marker EMPTY = new Marker(0);
        final int size;
        Marker(int size) { this.size = size; }
        boolean isEmpty() { return this == EMPTY; }             // 동일성 비교
        static Marker of(int size) { return size == 0 ? EMPTY : new Marker(size); }
    }

    static class Fixed extends Marker {
        static final Fixed EMPTY = new Fixed(0);
        Fixed(int size) { super(size); }
        private Object readResolve() { return size == 0 ? EMPTY : this; }   // 싱글턴 복구
        boolean isEmptyFixed() { return this == EMPTY; }
    }

    public static void main(String[] args) throws Exception {
        Marker before = Marker.of(0);
        System.out.println("직렬화 전  isEmpty : " + before.isEmpty());        // true

        Marker after = roundTrip(before);
        System.out.println("라운드트립 isEmpty : " + after.isEmpty());          // false !
        System.out.println("  size는 그대로    : " + after.size);               // 0
        System.out.println("  from()으로 정규화: " + Marker.of(after.size).isEmpty());  // true

        Fixed fixedAfter = (Fixed) roundTrip(Fixed.EMPTY);
        System.out.println("readResolve 있으면 : " + fixedAfter.isEmptyFixed()); // true
    }

    @SuppressWarnings("unchecked")
    static <T> T roundTrip(T o) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(out)) { oos.writeObject(o); }
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(out.toByteArray()))) {
            return (T) ois.readObject();
        }
    }
}
```

기대 출력:

```
직렬화 전  isEmpty : true
라운드트립 isEmpty : false      ← 여기가 이 문서의 핵심
  size는 그대로    : 0
  from()으로 정규화: true       ← C4가 readObject 에서 하는 일
readResolve 있으면 : true       ← 클래스 쪽에서 해결하는 방법
```

## 정리

1. `==`는 동일성, `equals`는 동등성. **싱글턴 확인에는 `==`가 맞다.**
2. 그 전제는 "그 객체를 만드는 길이 하나뿐"인데, **역직렬화가 그 길을 우회한다.**
3. 그래서 싱글턴은 라운드트립 후 깨지고, 증상이 조용한 경우가 많다.
4. 근본 해법은 클래스에 `readResolve()`를 두는 것, 차선은 **호출하는 쪽에서 팩토리로 정규화**하는 것(C4의 선택).
5. 스트림 *안*의 동일성 보존과 스트림 *밖* 싱글턴과의 동일성은 별개다.
