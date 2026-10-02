# software-design/03-deep-modules-and-abstraction — 정답

## 정답

### 1. 경계마다 인터페이스가 생긴다

- 경계를 그을 때마다 인터페이스가 생기고, 인터페이스도 배워야 하는 것이다. 숨긴 것이 적으면 경계는 비용만 더한다.

```text
 깊은 모듈: 좁은 인터페이스 / 큰 구현     얕은 모듈: 넓은 인터페이스 / 작은 구현
 ┌──┐                                   ┌────────────┐
 │  │                                   └────────────┘
 │  │
 └──┘
```

### 2. 깊이 ≠ 줄 수

- 깊이는 인터페이스 대비 숨긴 것이다.
- Unix I/O: 함수 다섯 개 뒤에 장치·자료구조·권한·동시 접근 → 깊다.
- setter `setX(v)` → `this.x = v` → 얕다. 통과 메서드 `find(id) → next.find(id)` → 거의 0.

### 3. 버퍼 실험

(실험, JDK 21.0.12, `--cpus=2`, 2026-10-02 — 집필 2회·재실행 3회, 15라운드 범위)

```text
FileInputStream       1377~1886 ms
+BufferedInputStream    47~95 ms
Files.newInputStream  1727~2336 ms
```

- 읽은 바이트 수는 셋 다 1048576으로 같다. 결과는 같고 시간만 라운드마다 약 17~37배 차이였다.
- `Files.newInputStream`도 버퍼링되지 않는다(JDK 문서). NIO라서 빠른 게 아니다.

### 4. 흔한 경우를 단순하게

- 거의 모든 사용자가 원하는 버퍼링을 옛 입출력은 사용자가 조립하게 했다. 빠뜨려도 컴파일·테스트는 통과하고 느려지기만 한다. "버퍼를 끼워야 한다"는 지식이 호출자 각자에게 샌 것이다.
- `Files.newBufferedReader(path)` = `Files.newBufferedReader(path, StandardCharsets.UTF_8)`. 버퍼와 문자셋을 기본으로 정해 준다.

### 5. 단어 삭제 추가

```text
특수 목적: 2 files changed, 4 insertions(+)   Text 공개 메서드 6 → 8
범용:     1 file changed, 4 insertions(+)    Text 공개 메서드 6 → 6
```

- 실행 결과는 둘 다 `[hello ] cursor=6`.

### 6. 줄 수가 같은 이유

- 단어 경계를 찾는 코드는 어느 쪽이든 필요하다. 다른 것은 **그 코드가 어느 모듈에 들어가나**다.
- 이 크기에서는 이득이 "UI 기능 추가에 텍스트 모듈을 안 건드린다", "인터페이스가 안 자란다" 정도로 작다.
- 숙제: 범용 쪽의 `wordStart`·`wordEnd`는 Editor에 들어갔다. 여러 UI가 쓰면 다시 둘 곳을 정해야 한다(너무 범용으로 Text에 넣으면 그것도 비용 — "somewhat general-purpose").

### 7. 통과 계층에 인자 추가

```text
layered: 4 files changed, 6 insertions(+), 6 deletions(-)   stack depth at dao = 5
flat:    2 files changed, 4 insertions(+), 4 deletions(-)   stack depth at dao = 3
```

- 결과는 둘 다 `order#7 (삭제 포함 조회)`. Service·Manager는 시그니처만 바뀌었다.

### 8. 계층 판단 기준

- 아니다. 가운데 계층이 **다른 추상화**(권한 검사, 트랜잭션 경계, 상태 규칙)를 맡으면 통과 계층이 아니다.
- 판단: 그 계층이 맡은 개념을 한 문장으로 쓸 수 있나. 이웃 계층과 메서드 이름·인자가 거의 같으면 의심한다(APOSD 7장의 red flag).

### 9. tenantId

- 통과 변수(pass-through variable). 맨 아래 하나가 필요해서 사슬 전체를 지나간다.
- 처방: 이미 공유된 객체에 담거나 요청 범위 컨텍스트 객체로 옮긴다. 컨텍스트가 전역 잡동사니가 되지 않도록 담을 것을 정한다. 멀티테넌시의 테넌트 전파는 49 multi-tenancy에서 다룬다.
