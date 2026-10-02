# software-design/18-absence-and-null-design — 정답

## 정답

### 1. 검사 의무가 퍼진다

- null을 돌려주면 "없을 수 있다"는 사실이 시그니처에 없고, 호출처마다 기억해서 `if (x != null)`을 써야 한다. 한 곳만 잊어도 NPE다.
- 쿠폰 목록은 "0개"가 정상 상태다. 빈 목록이면 호출처는 분기 없이 루프를 0번 돈다.

### 2. 다섯 방법

| 방법 | 시그니처에 드러나나 | 호출자가 할 일 | 자리 |
|---|---|---|---|
| null | 아니오 | 기억해서 검사 | 경계 밖에서만, 들여오면 바로 바꿈 |
| 빈 컬렉션 | 컬렉션 타입 | 없음 | 여러 개일 수 있는 결과 |
| Optional | 예 | map/orElse/orElseThrow | 0개 또는 1개 반환값 |
| Null Object | 아니오(일부러) | 없음 | 없음일 때 할 일이 정해짐 |
| 예외 | unchecked면 아니오 | 잡거나 전파 | 없으면 계약 위반 |

### 3. 11곳 중 1곳

(실험 A, JDK 21.0.12, 2026-10-01)

```text
    호출처 #7: Cannot invoke "java.util.List.size()" because "<local5>" is null
  null 반환: NPE 1건
  빈 목록 반환: NPE 0건
```

- null 반환: 1건(#7). 빈 목록: 0건. 반환 쪽 한 곳을 바꾸면 11곳의 검사 의무가 사라진다.

### 4. `Optional.get()`

```text
  java.util.NoSuchElementException: No value present
```

- 나아진 것: 없음이 시그니처에 드러나 호출자가 알 기회가 생겼다.
- 아닌 것: 검사 없이 `get()`하면 NPE가 `NoSuchElementException`으로 이름만 바뀐다. 메시지에 무엇이 없었는지도 없다.
- 대안: `orElseThrow(() -> new X("쿠폰 없음 code=X"))`(문맥 있는 예외), `orElse(기본값)`·`map(...).orElse(...)`.

### 5. Optional의 용도

- JDK 21 문서: "primarily intended for use as a method return type where there is a clear need to represent "no result," and where using null is likely to cause errors". Optional 타입 변수 자체는 null이면 안 된다.
- 필드: `Serializable`이 아니라 Java 직렬화가 실패한다(실험 D: `NotSerializableException: java.util.Optional`).
- 인자: 호출자가 감싸야 하고, 인자 자체가 null로 올 수 있어 검사가 두 겹이 된다. 오버로드가 보통 더 단순하다.

### 6. Null Object

- 맞는 경우: 없음일 때 할 일이 하나로 정해졌을 때. 할인 코드가 없으면 원가(`NoDiscount.apply(price) = price`). 실험 C에서 `NONE -> 할인 없음, 10000원 -> 10000`.
- 숨기는 경우: 호출자가 없었다는 사실을 알아야 할 때. 사용자가 쿠폰 코드를 잘못 입력했는데 Null Object가 조용히 원가를 적용하면 사용자는 오류를 모른다. 그때는 Optional·결과 타입.

### 7. Map과 null

```text
  get(A)=null, get(B)=null, containsKey(A)=true, containsKey(B)=false
  Map.of(값 null) -> NPE
```

- `get`은 둘 다 null이라 "키 없음"과 "값 null"을 구분하지 못한다. `containsKey`로만 구분된다.
- `Map.of`는 null 키·값을 거부해 NPE를 던진다(JDK 문서 "They disallow null keys and values").

### 8. helpful NPE 메시지

```text
[javac 기본]
  Cannot invoke "String.length()" because "<local5>" is null
[javac -g]
  Cannot invoke "String.length()" because "n" is null
```

- JEP 358은 지역 변수 표가 있을 때만 이름을 쓰고, 없으면 `<local i>`로 쓴다. javac 기본은 지역 변수 표를 넣지 않는다. `javac -g`로 컴파일하면 `"n"`이 나온다.
- 기능 자체는 JDK 14에 들어왔고 JDK 15부터 기본으로 켜졌다. `-XX:-ShowCodeDetailsInExceptionMessages`면 메시지가 `null`이다.
- 응답에 그대로 넣으면 코드 구조(필드·메서드 이름)가 노출된다. JDK 15 릴리스 노트도 이 위험을 경고한다.

### 9. 미입력이 0%로

- 원인: 원시 `int` 필드는 기본값 0이라 "미입력"을 표현할 수 없다(실험 5: `int 필드: 0`). "할인 미정"과 "할인 0%"가 섞였다.
- 설계 수정: 상태를 타입으로 드러낸다(`sealed DiscountPolicy permits Undecided, Rate`). 경계에서 nullable 입력을 이 타입으로 한 번 바꾼다. DB는 nullable 컬럼이나 상태 컬럼.
- 이미 저장된 데이터: 0이 "진짜 0%"인지 "미입력"인지 값만으로는 알 수 없다. 생성 이력·화면 로그 등 다른 근거로 따로 판별해야 한다.
