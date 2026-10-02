# software-design/03-deep-modules-and-abstraction — 깊은 모듈·좋은 인터페이스·추상화 계층 — 정리 (힌트)

## 해결하는 문제

02에서 모듈 경계를 긋고 결정을 숨기라고 했다.\
그런데 경계를 많이 긋는다고 단순해지지 않는다. 경계마다 인터페이스가 하나씩 생기고, 인터페이스도 배워야 하는 것이기 때문이다.\
이 노트는 **모듈 하나가 값을 하는가**를 재는 눈금이다.

```text
 모듈의 값 = 숨겨 준 것(구현) − 배워야 하는 것(인터페이스)

   깊은 모듈                 얕은 모듈
   ┌──────┐ ← 인터페이스     ┌──────────────────┐ ← 인터페이스
   │      │   (좁다)         │                  │   (넓다)
   │      │                 └──────────────────┘
   │ 구현 │                    구현 (얕다)
   │(깊다)│
   │      │
   └──────┘
```

- *깊은 모듈(deep module)*: 인터페이스는 단순한데 그 뒤에 많은 기능을 숨긴 모듈. Ousterhout 대담 원문: 가장 좋은 메서드는 "provide a lot of functionality but have a very simple interface"하고, 구현을 읽는 큰 부하를 인터페이스를 배우는 작은 부하로 바꿔 준다.
- *얕은 모듈(shallow module)*: 숨기는 기능에 비해 인터페이스가 복잡한 모듈. 대담 원문: 이런 인터페이스는 "don't help much in terms of reducing what the programmer needs to know".
- *추상화(abstraction)*: 중요하지 않은 세부를 뺀 단순화된 관점(APOSD 4장, 독자 노트로 확인).

쉬운 예: 자동차 운전석은 페달 둘과 핸들 하나다(좁은 인터페이스). 그 뒤에 엔진·변속기·ABS가 숨어 있다(깊은 구현). 바퀴마다 브레이크 레버가 따로 있는 차는 기능이 같아도 운전이 어렵다.\
똑같은 구조다.\
실무 예: Unix 파일 입출력은 `open·read·write·lseek·close` 다섯 함수 뒤에 디스크 장치·자료구조·권한·동시 접근을 숨긴다(APOSD 4장의 대표 예, Valente의 해설로 확인). Java의 옛 입출력은 버퍼링을 쓰려면 `BufferedInputStream`을 직접 끼워야 하고, 잊으면 느려진다(아래 실험).

## 동작·원리

### 1. 깊이는 비율이다

```text
          인터페이스(배울 것)          구현(숨긴 것)
 Unix I/O  open read write lseek close  파일시스템·캐시·권한·장치 드라이버 ...
           5개                          매우 큼            → 깊다
 setX(v)   setX                         this.x = v          → 얕다
 통과 메서드 find(id)                     return next.find(id) → 얕다(0에 가까움)
```

- 깊이는 줄 수가 아니라 **인터페이스 대비 숨긴 것**이다.
- 인터페이스에는 비형식 부분(호출 순서, 부수효과, 성능 특성)도 들어간다(02).
- *클래스 과잉(classitis)*: "클래스는 작아야 한다"를 지나치게 따라 얕은 클래스가 잔뜩 생긴 상태. 하나하나는 단순한데 전체 시스템 복잡도는 커진다(APOSD 4장, 독자 노트로 확인).

### 2. 흔한 경우를 단순하게 — Java 입출력

```text
 옛 방식 (조합을 사용자가 짠다)                  NIO 편의 메서드 (흔한 경우를 한 번에)
 new BufferedReader(                            Files.newBufferedReader(path)
     new InputStreamReader(                       = UTF-8, 버퍼링 포함
         new FileInputStream(f), UTF_8))
 버퍼를 빼먹어도 컴파일된다 → 느리다
```

- APOSD 4장은 인터페이스를 **흔한 경우가 가장 단순하도록** 설계하라고 한다(독자 노트로 확인). 버퍼링은 거의 모든 사용자가 원하는데, 옛 Java 입출력은 그것을 사용자가 고르게 했다.
- `Files.newBufferedReader(Path)`는 `Files.newBufferedReader(path, StandardCharsets.UTF_8)`과 같다(JDK 21 `Files` 문서).
- 반면 `Files.newInputStream`이 돌려주는 스트림은 **버퍼링되지 않는다**(같은 문서). NIO라고 다 깊은 것이 아니다.

### 실험 A: 버퍼를 잊으면 — 같은 1 MiB를 1바이트씩 읽기

```java
try (InputStream in = new FileInputStream(f)) { while (in.read() != -1) n++; }                        // 버퍼 없음
try (InputStream in = new BufferedInputStream(new FileInputStream(f))) { while (in.read() != -1) m++; } // 버퍼
try (InputStream in = Files.newInputStream(p)) { while (in.read() != -1) k++; }                       // NIO, 버퍼 없음
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02 — 시간은 실행마다 다르다. 집필 때 2회 6라운드와 사실 점검 재실행 3회 9라운드를 합친 범위: 버퍼 없음 1377~1886 ms, 버퍼 47~95 ms, `Files.newInputStream` 1727~2336 ms. 아래 출력은 집필 때 한 번의 실행)

```text
round 1: FileInputStream 1456 ms (1048576 B) | +BufferedInputStream 77 ms (1048576 B) | Files.newInputStream 1963 ms (1048576 B)
round 2: FileInputStream 1624 ms (1048576 B) | +BufferedInputStream 62 ms (1048576 B) | Files.newInputStream 1807 ms (1048576 B)
round 3: FileInputStream 1542 ms (1048576 B) | +BufferedInputStream 67 ms (1048576 B) | Files.newInputStream 1917 ms (1048576 B)
```

- 읽은 바이트 수는 셋 다 1048576으로 같다. 결과가 같으니 테스트는 통과한다.
- 버퍼가 없으면 라운드마다 약 17~37배 느렸다(같은 라운드 안 비율, 위 15라운드 범위). 버퍼 없는 `FileInputStream.read()`는 호출마다 네이티브 `read0()`로 내려간다(jdk21u 소스 `java/io/FileInputStream.java`). 1바이트마다 운영체제까지 다녀오는 셈이다(시스템 호출 비용은 os 영역).
- 해석: "버퍼를 끼워야 한다"는 지식이 호출자 각자에게 새어 나와 있다. 깊은 인터페이스라면 이 결정을 모듈이 대신 내린다.

### 3. 범용 인터페이스가 더 깊다 (APOSD 6장)

```text
 특수 목적 Text                         범용 Text
 backspace(Cursor)                      insert(Position, String)
 delete(Cursor)                         delete(Position start, Position end)
 deleteSelection(Selection)             changePosition(Position, int)
 (UI 동작마다 메서드)                     (텍스트의 기본 연산만)
        │                                      │
 UI 동작이 늘면 Text도 바뀐다              UI 동작이 늘어도 Text는 그대로
```

- APOSD 2판 6장(저자가 공개한 발췌로 열람): 학생들의 텍스트 클래스가 UI 동작마다 메서드를 만들었다. 그 결과 "a large number of shallow methods"가 생겼고, UI의 개념(선택, 백스페이스)이 텍스트 클래스로 새어 들어갔다.
- 저자의 처방은 **조금 범용적으로(somewhat general-purpose)**: 기능은 지금 필요한 만큼, 인터페이스는 여러 쓰임을 받칠 만큼. "somewhat"가 중요하다 — 너무 범용이면 지금 쓰기에 불편하다(같은 발췌 6.1절).
- 같은 발췌 6.3절: 범용 API로 쓰면 UI 쪽 코드는 **조금 길어진다**. 대신 "백스페이스가 어느 글자를 지우나"가 UI 코드에 드러난다.

### 실험 B: 같은 기능 추가 — 특수 목적 Text vs 범용 Text

변경 요청: Ctrl+Backspace(앞 단어 삭제)와 Ctrl+Delete(뒤 단어 삭제).

```java
// 특수 목적: Text에 메서드 2개 추가 + Editor 분기 2개
public void deleteWordBefore(Cursor c) { /* 공백 건너뛰고 단어 시작까지 */ }
public void deleteWordAfter(Cursor c)  { /* ... */ }

// 범용: Editor만 바뀐다 — Text의 기본 연산으로 조합
case "CTRL_BACKSPACE" -> { int p = wordStart(cur); text.delete(p, cur); cur = p; }
case "CTRL_DELETE"    -> text.delete(cur, wordEnd(cur));
```

(실험, 같은 환경, 2026-10-02 — 입력 `"hello world"`, 커서 끝, 키 BACKSPACE → "!" → CTRL_BACKSPACE)

```text
## shallow diff
 src/ed/Editor.java | 2 ++
 src/ed/Text.java   | 2 ++
 2 files changed, 4 insertions(+)
## shallow run
[hello ] cursor=6
public methods of Text: 8 (생성자 포함)
## general diff
 src/ed/Editor.java | 4 ++++
 1 file changed, 4 insertions(+)
## general run
[hello ] cursor=6
public methods of Text: 6 (생성자 포함)
```

| | 바뀐 파일 | 추가 줄 | Text 공개 메서드(생성자 포함) |
|---|---|---|---|
| 특수 목적 | 2 (Text + Editor) | 4 | 6 → 8 |
| 범용 | 1 (Editor) | 4 | 6 → 6 |

- 줄 수는 4줄로 같았다. 이 실험에서 차이는 **어느 모듈이 바뀌나**와 **인터페이스가 커지나**다.
- 특수 목적 설계에서는 UI 기능 하나마다 텍스트 모듈 담당자도 함께 고친다. 인터페이스는 기능 수만큼 자란다.
- 정직한 한계: 이 크기에서는 범용의 이득이 작다. 범용 쪽 `wordStart`·`wordEnd`는 UI에 들어갔고, 여러 UI가 쓰게 되면 다시 어디에 둘지 정해야 한다.

### 4. 계층마다 다른 추상화 (APOSD 7장)

```text
 좋은 계층                                나쁜 계층(통과 메서드)
 Controller   HTTP 요청 ↔ 유스케이스       Controller.get(id)  → service.find(id)
 Service      주문 규칙(권한·상태 검사)     Service.find(id)    → manager.find(id)   ← 하는 일 없음
 Repository   행 ↔ 객체 변환              Manager.find(id)    → dao.find(id)       ← 하는 일 없음
                                         Dao.find(id)        실제 조회
 계층마다 다루는 개념이 다르다              이웃 계층이 같은 추상화를 반복한다
```

- APOSD 7장: 이웃한 계층이 **비슷한 추상화**를 가지면 분해가 잘못됐다는 신호(red flag)다(독자 노트로 확인).
- *통과 메서드(pass-through method)*: 받은 인자를 거의 그대로 다른 메서드에 넘기기만 하는 메서드. 새 기능을 더하지 않고 인터페이스만 늘린다.
- *통과 변수(pass-through variable)*: 맨 아래 메서드 하나가 필요해서 긴 호출 사슬을 따라 내려가는 변수. 처방은 이미 공유된 객체에 넣기, 컨텍스트 객체 등이다(같은 독자 노트).

### 실험 C: 통과 계층에 인자 하나 추가

변경 요청: "삭제된 주문도 포함해 조회하는 옵션(`includeDeleted`)".

(실험, 같은 환경, 2026-10-02 — 스택 깊이는 Dao에서 `StackWalker`로 센 프레임 수)

```text
## layered diff
 src/po/OrderController.java | 4 ++--
 src/po/OrderDao.java        | 4 ++--
 src/po/OrderManager.java    | 2 +-
 src/po/OrderService.java    | 2 +-
 4 files changed, 6 insertions(+), 6 deletions(-)
## layered run
  stack depth at dao = 5
order#7 (삭제 포함 조회)
## flat diff
 src/po/OrderController.java | 4 ++--
 src/po/OrderDao.java        | 4 ++--
 2 files changed, 4 insertions(+), 4 deletions(-)
## flat run
  stack depth at dao = 3
order#7 (삭제 포함 조회)
```

- 통과 계층 둘(Service·Manager)이 있으니 인자 하나에 4파일이 바뀌었다. 두 계층은 시그니처만 바뀌고 하는 일은 그대로다.
- 결과는 같다. 통과 계층은 기능 없이 변경 증폭과 호출 깊이(5 대 3)만 더했다.
- 반대 상황: 가운데 계층이 **다른 추상화**(권한 검사, 트랜잭션 경계, 상태 규칙)를 맡는다면 통과 메서드가 아니다. 계층 수가 아니라 계층마다 새 개념이 있는지가 기준이다.

## 쓰이는 자료구조·알고리즘

- **호출 그래프·호출 깊이** — 통과 메서드는 호출 그래프에 진입 1·진출 1인 노드로 보인다. 계층 수 대비 하는 일을 볼 때 쓴다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **버퍼(배치)** — `BufferedInputStream`은 내부 배열에 한 번에 많이 읽어 두고 `read()`를 배열 접근으로 바꾼다. 시스템 호출 횟수를 줄이는 배치 기법이다([os](../../os/README.md) 영역의 시스템 호출, [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md)).
- **데코레이터 사슬** — `BufferedReader(InputStreamReader(FileInputStream))`은 같은 인터페이스를 감싸 기능을 더하는 사슬이다. 독자 노트(Matt Duck 2021 <https://www.mattduck.com/2021-04-a-philosophy-of-software-design.html>)는 저자가 데코레이터를 "보일러플레이트만 더하는 얕은 통과 메서드"인 경우가 많다고 본다고 요약한다. 그 논의가 7장의 어느 절인지는 확인하지 못했다 [?]. 패턴 자체는 27 design-patterns-gof.
- **위치 기반 연산(Position·범위)** — 범용 텍스트 API의 `insert(pos)`·`delete(start, end)`는 문자열 버퍼 위의 범위 연산이다. 큰 텍스트에서는 rope 같은 자료구조로 구현을 바꿔도 인터페이스는 그대로다. [data-structure/28-rope](../../data-structure/28-rope/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 모듈 하나를 점검하는 순서

1. 공개 메서드를 나열한다(`javap -public`).
2. 각 메서드에 "호출자가 이것 대신 직접 했다면 무엇을 알아야 했나"를 적는다. 답이 "거의 없음"이면 얕다.
3. 흔한 사용 3가지를 적고, 각각 몇 번의 호출·몇 개의 객체 조립이 필요한지 센다. 흔한 경우가 조립을 요구하면 편의 메서드를 둔다(예: `Files.newBufferedReader`).
4. 이웃 계층의 메서드 이름·인자가 거의 같으면 통과 계층을 의심한다.
5. 인터페이스가 특정 호출자의 개념(Cursor, Selection, 화면 이름)을 담고 있으면 그 호출자 쪽으로 누출된 것이다.

### 2. 코드 (Java) — 통과 계층 걷어내기

```java
// 전: 하는 일 없는 계층
public String find(long id, boolean includeDeleted) { return manager.find(id, includeDeleted); }

// 후 1: 계층을 없애고 호출자가 아래 계층을 바로 쓴다
// 후 2: 계층을 남기되 다른 일을 맡긴다
public Order find(long id, Viewer viewer) {
    Order o = dao.find(id, viewer.canSeeDeleted());   // 권한 → 조회 조건 변환: 이 계층만 아는 규칙
    return o.visibleTo(viewer) ? o : Order.hidden(id);
}
```

### 3. 진단 도구

- `javap -public -cp out <클래스>`로 인터페이스 크기, 메서드 수.
- IDE의 Call Hierarchy로 진입 1·진출 1 메서드(통과 메서드 후보)를 찾는다.
- 정적 분석: PMD·Sonar 등에 "위임만 하는 메서드" 규칙이 있는지는 도구별로 다르다 [?]. 확실한 것은 사람이 호출 그래프를 읽는 것이다.

## 장애 시나리오와 대처

### 1. 얕은 래퍼 남발 → 호출 경로만 길어지고 복잡도 그대로 (⚠ 커리큘럼)

- 현상: 기능 하나를 따라가려면 클래스 대여섯 개를 거쳐야 하는데, 각 클래스는 다음 클래스를 부르기만 한다.
- 보이는 형태: 스택 트레이스가 길고 같은 이름의 메서드가 반복된다(`find → find → find`). 인자 하나 추가 PR이 통과 계층까지 건드린다(실험 C: 4파일 대 2파일).
- 원인: 계층을 "관례상" 만들었고, 각 계층에 새 추상화가 없다.
- 대처: 계층마다 맡은 개념을 한 문장으로 적어 본다. 못 적는 계층은 합친다.

### 2. 통과 메서드·통과 변수 (⚠ 커리큘럼)

- 현상: 맨 아래에서만 쓰는 값(로케일, 테넌트 ID, 요청 ID)이 모든 메서드 시그니처에 붙어 있다.
- 보이는 형태: 새 값을 하나 내려보낼 때마다 시그니처 수십 개가 바뀐다.
- 원인: 통과 변수.
- 대처: 이미 공유된 객체에 담거나 컨텍스트 객체를 하나 둔다. 컨텍스트 객체가 전역 잡동사니가 되지 않게 범위를 정한다.

### 3. 흔한 경우를 사용자가 조립 → 기본 동작이 느림

- 현상: 파일 처리 배치가 다른 환경보다 수십 배 느리다. 결과는 맞다.
- 보이는 형태: 프로파일러에서 `read` 시스템 호출이 대부분. 실험 A에서 버퍼 없음 1377~1886 ms 대 버퍼 47~95 ms.
- 원인: 깊어야 할 결정(버퍼링)을 호출자에게 맡긴 인터페이스.
- 대처: 버퍼를 포함한 API(`Files.newBufferedReader`, `BufferedInputStream`)로 바꾼다. 우리 모듈을 설계할 때는 흔한 경우를 기본값으로 둔다.

### 4. 특수 목적 인터페이스 → UI 기능마다 하위 모듈 수정

- 현상: 화면 기능 하나 추가에 도메인·저장 모듈 담당자까지 리뷰에 들어간다.
- 보이는 형태: 하위 모듈의 공개 메서드 수가 화면 기능 수와 함께 늘어난다(실험 B: 6 → 8).
- 원인: 하위 모듈이 상위 모듈의 개념으로 인터페이스를 만들었다.
- 대처: 하위 모듈은 자기 개념의 기본 연산만 내보낸다(조금 범용적으로).

## 핵심 문장

- 모듈의 값은 숨긴 것에서 배워야 하는 것을 뺀 것이다. 깊은 모듈은 좁은 인터페이스 뒤에 많은 기능을 숨긴다.
- 흔한 경우는 가장 단순해야 한다. 버퍼링을 호출자에게 맡긴 옛 Java 입출력은 실험에서 버퍼를 잊으면 약 17~37배 느렸다.
- 하위 모듈이 상위의 개념(커서·선택)으로 인터페이스를 만들면 기능마다 인터페이스가 자란다. 실험에서 특수 목적 Text는 6 → 8 메서드, 범용 Text는 그대로였다.
- 통과 메서드는 기능 없이 변경 증폭만 더한다. 실험에서 인자 하나 추가가 통과 계층 때문에 2파일에서 4파일이 됐다.
- 계층 수가 아니라 계층마다 다른 추상화가 있는지가 기준이다.

## 관련 주제·근거

- 선행
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 인터페이스(형식+비형식), 정보 은닉
- 후속
  - [04-decompose-by-change](../04-decompose-by-change/2-summary.md) — 무엇을 숨길지
  - [08-function-design](../08-function-design/2-summary.md) · [11-when-to-abstract](../11-when-to-abstract/2-summary.md) · [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) · [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md)(데코레이터)
  - [49 multi-tenancy](../49-multi-tenancy/2-summary.md)(테넌트 전파), 기존 노트 [systems/multi-tenancy](../../systems/multi-tenancy/2-summary.md)
- 다른 영역
  - [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) — 버퍼·배치로 호출 횟수 줄이기
  - [data-structure/28-rope](../../data-structure/28-rope/2-summary.md) — 범용 텍스트 인터페이스 뒤에 숨길 수 있는 구현
- 글·문서
  - J. Ousterhout, 『A Philosophy of Software Design』 2판 6장 "General-Purpose Modules are Deeper" — 저자가 공개한 2판 발췌 PDF로 6.1~6.3절 열람 <https://web.stanford.edu/~ouster/cgi-bin/aposd2ndEdExtract.pdf>
  - 같은 책 4장(깊은 모듈, classitis, 흔한 경우를 단순하게)·7장(다른 계층 다른 추상화, 통과 메서드·통과 변수) — 본문 미열람. 독자 노트(Lebrero 2021) <https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/>와 Marco Tulio Valente "Modules Should Be Deep!" <https://softengbook.org/articles/deep-modules>(Unix I/O 다섯 함수)로 확인한 요지
  - Ousterhout·Martin 대담(깊은·얕은 메서드 원문) <https://github.com/johnousterhout/aposd-vs-clean-code/blob/main/README.md>
  - JDK 21 `java.nio.file.Files` 문서(`newBufferedReader(Path)` = UTF-8, `newInputStream`은 버퍼링 안 됨) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Files.html>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02)
  - A 버퍼 유무: scratchpad `sd/01/e03/io/Io.java` (`java Io.java`), 1 MiB 1바이트씩 읽기 3라운드 × 2회(집필) + 3회(사실 점검 재실행)
  - B 단어 삭제 2종 추가: `sd/01/e03/{shallow,general}/src/ed/*.java`, `run.sh` — diff 2파일 대 1파일, 공개 메서드 6→8 대 6
  - C `includeDeleted` 추가: `sd/01/e03/{layered,flat}/src/po/*.java`, `run2.sh` — diff 4파일 대 2파일, 스택 깊이 5 대 3
