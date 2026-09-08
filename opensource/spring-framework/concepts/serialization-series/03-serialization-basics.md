# 03. 직렬화·역직렬화 기본

> 이번 대화에서 나온 오해: **방향 혼동** — "직렬화는 객체 상태를 메모리에 올리는 것"이 아니다. 그건 역직렬화다.

## 1. 방향

직렬화와 역직렬화는 같은 통로를 반대 방향으로 지나간다.

```
# 직렬화 (serialize)   : 힙에 있는 객체  ──▶  바이트 덩어리 (파일 / 네트워크 / byte[])
                         "밖으로 꺼내서 납작하게 편다"

# 역직렬화 (deserialize): 바이트 덩어리  ──▶  힙에 새 객체
                         "다시 읽어서 메모리에 세운다"
```

왜 필요한가: **힙의 객체는 JVM이 꺼지면 사라지고, 다른 JVM으로 보낼 수도 없다.** 그래서 바이트로 평탄화해 디스크에 쓰거나 네트워크로 보낸다.

## 2. 전체 워크플로우

쓰는 쪽과 읽는 쪽이 각각 네 단계를 밟고, 그 사이를 바이트 스트림이 잇는다.

```
 [JVM A]                                                          [JVM B]
                                                        
 TypeDescriptor@7f3a                                     TypeDescriptor@e11c  ← 새 객체(주소 다름)
    │                                                          ▲
    │ writeObject(td)                                          │ readObject()
    ▼                                                          │
 ┌──────────────────────────────────────┐                ┌─────┴──────────────────────────┐
 │ ObjectOutputStream                   │                │ ObjectInputStream              │
 │  1. 클래스 설명자 기록                │                │  1. 클래스 이름으로 Class 검색  │
 │     (이름 + serialVersionUID + 필드)  │                │     → 없으면 ClassNotFound     │
 │  2. writeObject 훅 있으면 호출        │                │  2. 생성자 없이 인스턴스 생성   │
 │  3. non-transient 필드 순회           │                │  3. 스트림에서 필드 값 채움     │
 │  4. 참조 타고 그래프 전체 순회         │                │  4. readObject 훅 있으면 호출   │
 └──────────────────┬───────────────────┘                └─────▲──────────────────────────┘
                    │                                          │
                    ▼                                          │
              [ 바이트 스트림 ]  ──── 파일 / 소켓 / byte[] ────▶ [ 같은 바이트 ]
```

## 3. 무엇이 실리고, 무엇이 안 실리나

이번 대화에서 나온 오해: **"바이너리 코드(바이트코드)를 직렬화한다"** -> 아니다.

| 스트림에 실리는 것 | 실리지 **않는** 것 |
|---|---|
| 클래스 **이름** (`org.springframework...TypeDescriptor`) | 메서드 바이트코드 |
| `serialVersionUID` | 클래스 정의 자체 |
| non-transient · non-static **필드 값** | `transient` 필드 |
| 참조가 가리키는 객체들(그래프 전체) | `static` 필드 |

그래서 **받는 쪽 JVM에도 같은 클래스가 classpath에 있어야 한다.** 스트림에는 "이 클래스의 인스턴스인데 필드 값은 이러이러하다"는 **상태 기록**만 들어 있다. 클래스를 못 찾으면 `ClassNotFoundException`.

## 4. 스트림 두 겹 — 변환기와 목적지

직렬화 코드는 언제나 스트림 두 개를 겹쳐 쓴다.

```java
ByteArrayOutputStream out = new ByteArrayOutputStream();       // (1) 목적지 (바이트를 담는 통)
try (ObjectOutputStream oos = new ObjectOutputStream(out)) {   // (2) 변환기 (객체 → 바이트)
    oos.writeObject(typeDescriptor);
}
byte[] bytes = out.toByteArray();                              // (3) 쌓인 바이트 꺼내기
```

- `ObjectOutputStream` = **변환기**. 필드 순회, 훅 호출 같은 직렬화 로직 담당.
- `ByteArrayOutputStream` = **목적지**. 바이트가 쌓이는 곳.

목적지만 갈아끼우면 용도가 바뀐다:

| 목적지 | 용도 |
|---|---|
| `ByteArrayOutputStream` | 메모리 `byte[]` — **테스트용 라운드트립** |
| `FileOutputStream` | 파일 저장 |
| `socket.getOutputStream()` | 다른 서버로 전송 |

테스트에서 쓰는 패턴이 바로 이것이다 — 실제 전송을 흉내 내되 같은 JVM 안에서 왕복시킨다.

```java
// C4 테스트의 헬퍼 (TypeDescriptorTests.java)
private static TypeDescriptor serializeAndDeserialize(TypeDescriptor typeDescriptor) throws Exception {
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    try (ObjectOutputStream outputStream = new ObjectOutputStream(out)) {
        outputStream.writeObject(typeDescriptor);
    }
    try (ObjectInputStream inputStream = new ObjectInputStream(new ByteArrayInputStream(out.toByteArray()))) {
        return (TypeDescriptor) inputStream.readObject();
    }
}
```

## 5. 직렬화는 자동으로 일어나지 않는다

객체를 만들고 쓰는 것만으로는 직렬화가 시작되지 않는다.

```java
TypeDescriptor td = new TypeDescriptor(field);   // 직렬화 0회. 아무 일도 안 일어남
td.getAnnotations();                             // 직렬화 0회
```

**누군가 명시적으로 시켜야만** 직렬화가 시작된다. 실무에서 그 "누군가"는 보통 프레임워크다:

- HTTP 세션 복제 (톰캣이 세션을 직렬화해 다른 노드로 전송)
- 분산 캐시 (Redis/Hazelcast에 JDK 직렬화로 객체 저장)
- RMI 등 원격 호출의 인자·반환값·**예외**
- 파일/DB에 객체 통째로 저장

C4가 실무에서 문제가 되는 경로도 이 마지막 항목과 연결된다 — `ConversionFailedException`·`ConverterNotFoundException`이 `TypeDescriptor` 필드를 **non-transient**로 들고 있고, 예외는 `Throwable`이라 `Serializable`이다.

```java
// spring-core/.../convert/ConversionFailedException.java
public class ConversionFailedException extends ConversionException {
    private final @Nullable TypeDescriptor sourceType;   // ← 예외가 직렬화되면 같이 나간다
    private final TypeDescriptor targetType;
```

## 6. `Serializable`은 마커 인터페이스다

이 인터페이스에는 구현할 선언이 하나도 없다.

```java
public interface Serializable {
}   // 메서드가 하나도 없다
```

구현할 메서드가 없다. 그냥 **"나는 직렬화되어도 된다"는 표시**일 뿐이고, `ObjectOutputStream`이 런타임에 `instanceof Serializable`로 확인한다. 아니면 `NotSerializableException`.

`serialVersionUID`는 "쓸 때의 클래스와 읽을 때의 클래스가 같은 버전인가"를 확인하는 값이다. 선언하지 않으면 컴파일러가 클래스 구조로부터 자동 계산하는데, **필드 하나만 바뀌어도 값이 달라져** 예전 스트림을 못 읽게 된다. `TypeDescriptor`는 `@SuppressWarnings("serial")`이고 `serialVersionUID`를 선언하지 않는다 = **버전 간 호환을 원래 보장하지 않는다.**

## 7. 손으로 확인하기

transient와 static이 각각 어떻게 빠지는지 한 파일로 확인할 수 있다.

```java
import java.io.*;

public class SerializationBasics {
    static class Account implements Serializable {
        String owner;
        transient String password;      // 실리지 않는다
        static String bankName = "KB";  // static 도 실리지 않는다

        Account(String owner, String password) {
            this.owner = owner;
            this.password = password;
        }
        @Override public String toString() {
            return "Account{owner=" + owner + ", password=" + password + ", bank=" + bankName + "}";
        }
    }

    public static void main(String[] args) throws Exception {
        Account original = new Account("jun", "s3cret");
        System.out.println("before : " + original);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(out)) {
            oos.writeObject(original);
        }
        System.out.println("bytes  : " + out.size() + " bytes");

        Account.bankName = "SHINHAN";   // static 을 바꿔치기 해두면

        Account copy;
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(out.toByteArray()))) {
            copy = (Account) ois.readObject();
        }
        System.out.println("after  : " + copy);      // password=null, bank=SHINHAN
        System.out.println("same?  : " + (copy == original));   // false
    }
}
```

기대 출력:

```
before : Account{owner=jun, password=s3cret, bank=KB}
bytes  : 88 bytes
after  : Account{owner=jun, password=null, bank=SHINHAN}
same?  : false
```

- `password`가 `null` -> transient는 안 실린다
- `bank`가 `SHINHAN` -> static은 스트림이 아니라 **현재 JVM의 값**을 그대로 본다
- `same? false` -> 역직렬화는 항상 **새 객체**를 만든다

## 정리

1. 직렬화 = 힙 -> 바이트(밖으로), 역직렬화 = 바이트 -> 힙(안으로).
2. 실리는 것은 **상태**(필드 값)와 **클래스 이름**뿐. 코드는 안 실린다.
3. 자동으로 일어나지 않는다 — `writeObject()` 호출이 있어야 한다.
4. `ObjectOutputStream`(변환기) 위에 목적지 스트림을 갈아끼우는 구조.
5. 역직렬화 결과는 언제나 원본과 다른 새 객체다.
