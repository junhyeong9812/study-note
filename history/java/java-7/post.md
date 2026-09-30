# Java 7 (Java SE 7, Dolphin, 2011년 7월)

> 원본: `~/project/java-history/java/java-7.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR 번호·클래스/패키지 이름·코드블록 11개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 그리고 같은 시리즈 다른 편의 원문을 끌어와 적은 교차 주 4개는 원문에 없는 보충이다.\
> 새로 그린 도식은 없다 — 원문에 도식이 없고, 원문이 전/후를 보여 주는 자리는 「도입 전」·「도입 후」 코드블록 쌍이 이미 맡고 있다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Oracle의 Sun 인수 후 첫 메이저 릴리스. "Project Coin"이라는 소소한 언어 개선 묶음과 NIO.2, Fork/Join, invokedynamic을 담아 5년 만에 Java를 다시 진전시킨 버전.

이 편을 하나의 비유로 읽으면 **미뤄 둔 이사 짐을 다 싸고 한 번에 옮기려다 5년을 끌던 집이, "다 싼 상자부터 먼저 보내자"로 방침을 바꾼 일**이다.\
람다 상자와 모듈 상자는 아직 못 쌌으니 다음 트럭에 싣고, 이미 싼 상자들로 먼저 이사를 마쳤다.\
**Java 7의 Plan B도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "기능을 다 채우고 늦게 내기보다, 준비된 것부터 내자".

본문 흐름에 쓰는 비유는 이 이삿짐 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 다 싸고 한 번에 보내려다 끌린 5년 | 원문 표현으로 "Java SE 6(2006) 이후 무려 약 5년의 공백" |
| "다 싼 상자부터 먼저 보내자" | 원문 표현으로 **Plan B** — "준비된 것부터 내자" |
| 다음 트럭에 실린 상자 둘 | 원문이 미뤘다고 든 둘 — 람다(Java 8)와 모듈(Project Jigsaw, Java 9) |
| 이번 트럭에 실린 자잘한 상자 묶음 | 원문 표현으로 **Project Coin** — "작은 문법 개선들의 묶음(JSR 334)" |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **`<>`(다이아몬드)가 붙었다고 실행 중에 타입이 남는 것은 아니다.**\
  원문은 다이아몬드를 "타입 추론으로 간결"해진 것으로만 적는다.\
  같은 시리즈 `java-5.md`가 제네릭을 이렇게 적는다 — "제네릭은 **컴파일 시점에만** 타입을 검사하고, 바이트코드에서는 타입 인자를 지운다(type erasure)".
- **이름이 이어질 뿐, 1.4의 NIO와 7의 NIO.2는 다루는 것이 다르다.**\
  같은 시리즈 `jdk-1.4.md`의 NIO는 "채널(Channel), 버퍼(Buffer), 셀렉터(Selector) 기반의 고성능·논블로킹 I/O"이고,\
  이 편의 NIO.2는 원문 제목 그대로 "새 파일 시스템 API"로 `java.nio.file`의 `Path`/`Files` 쪽이다.
- **G1은 이 버전에서 "기본 GC"가 아니다.**\
  원문이 「그 외 변경 / API 추가」에 적은 그대로 "Java 7 GA에서는 experimental 상태였고, 정식 지원은 7u4부터"다.

## 릴리스 정보
- 정식 출시일: 2011년 7월 28일 (General Availability) — 발표는 7월 7일
- 개발 주체: Oracle (2010년 Sun Microsystems 인수 완료 후 첫 릴리스), OpenJDK 커뮤니티 협업
- 공식 명칭: Java SE 7 (내부 버전 1.7)
- 코드네임: Dolphin
- 플랫폼 스펙: JSR 336 (Java SE 7 Release Contents)
- LTS 여부: 해당 시대엔 LTS 개념 없음

> **GA(General Availability)** — 누구나 받아서 실제 서비스에 쓰라고 내놓는 정식 출시.\
> 예: 원문은 이 날짜를 2011년 7월 28일로 적고, 그보다 앞선 7월 7일을 "발표"로 따로 구분해 적는다.

> **JSR(Java Specification Request)** — 자바에 무엇을 어떻게 넣을지 정하는 규격 문서에 붙는 번호.\
> 예: 이 편에 나오는 번호가 플랫폼 전체를 정한 JSR 336, 작은 문법 묶음 JSR 334, 파일 API JSR 203, 병렬 작업 JSR 166y, 동적 호출 JSR 292다.

> **LTS(Long-Term Support)** — 한 버전을 오래 지원해 주기로 정해 두는 제도.\
> 예: 원문이 이 칸에 적은 말은 "해당 시대엔 LTS 개념 없음"이다 — 이 제도가 언제 생겼는지는 같은 시리즈 `java-9.md`·`java-11.md`가 다룬다.

## 시대적 배경

*(「한눈에」의 이삿짐 비유가 가리키는 자리다.)*

Java SE 6(2006) 이후 무려 약 5년의 공백이 있었다. Sun의 경영난, JCP 내부 갈등, 그리고 2009~2010년 Oracle의 Sun 인수 절차가 겹치며 Java 7의 출시가 크게 지연되었다. Oracle은 인수 후 "기능을 다 채우고 늦게 내기보다, 준비된 것부터 내자"는 **Plan B**를 채택해 람다는 Java 8로, 모듈(Project Jigsaw)은 Java 9로 미루고, 완성된 기능들로 Java 7을 먼저 출시했다.

언어 측면에서는 Joshua Bloch가 제안한 **Project Coin** — 큰 부담 없이 일상 코드를 간결하게 만드는 작은 문법 개선들의 묶음(JSR 334) — 이 핵심이었다.

> **JCP(Java Community Process)** — 자바에 들어갈 규격을 여러 회사·개인이 함께 정하는 절차.\
> 예: 원문이 공백의 원인으로 든 셋 가운데 하나가 "JCP 내부 갈등"이다.

> **Plan B** — 준비된 기능만 실어 먼저 내보내고, 남은 것은 다음 버전으로 미루는 방침.\
> 예: 이 방침으로 미뤄진 것이 람다(→ Java 8)와 모듈(Project Jigsaw → Java 9)이고, 실제로 그렇게 나왔다.

> **Project Coin** — 원문 표현으로 "큰 부담 없이 일상 코드를 간결하게 만드는 작은 문법 개선들의 묶음(JSR 334)".\
> 예: 아래 절들 가운데 원문이 이 이름을 붙인 것은 try-with-resources이고, 「영향과 의의」에서 이 묶음으로 함께 든 것이 다이아몬드·멀티 catch·switch-on-String이다.

## 주요 추가 기능

### try-with-resources (Project Coin, JSR 334)

`AutoCloseable`을 구현한 자원을 try 괄호에서 선언하면 블록 종료 시 자동으로 `close()`가 호출된다. 자원 누수와 장황한 finally를 제거한다.

> **자원(resource)과 `close()`** — 파일·연결처럼 다 쓰고 나면 반드시 닫아 줘야 하는 것, 그리고 그것을 닫는 메서드.\
> 예: 아래 코드에서 여는 것이 `new BufferedReader(new FileReader("a.txt"))`이고, 닫는 것이 `br.close()`다.

> **`AutoCloseable`** — "이 객체는 try 괄호에 넣으면 자동으로 닫아도 되는 것"임을 나타내는 인터페이스.\
> 예: 원문 문장이 요구하는 조건이 바로 이 인터페이스를 "구현한 자원"이라는 것이다.

도입 전:
```java
BufferedReader br = new BufferedReader(new FileReader("a.txt"));
try {
    return br.readLine();
} finally {
    if (br != null) br.close(); // 수동 닫기, 예외 처리 번거로움
}
```

도입 후:
```java
try (BufferedReader br = new BufferedReader(new FileReader("a.txt"))) {
    return br.readLine();
} // 자동으로 br.close() 호출 (예외가 나도 보장)
```

**왜 이것이 나왔나** — 위 "도입 전" 코드에 원문이 직접 달아 둔 주석이 "수동 닫기, 예외 처리 번거로움"이고, 본문은 그것을 "자원 누수와 장황한 finally"라고 적는다.

두 블록을 한 줄씩 맞대어 보면, 위쪽 `finally` 안의 `if (br != null) br.close();`가 아래쪽에서는 사라지고, 그 역할이 `try (...)` 괄호 안으로 들어간 `BufferedReader br = ...` 선언 하나로 옮겨 간다.\
원문이 아래 블록 끝 주석에 적어 둔 말이 그 결과다 — "자동으로 br.close() 호출 (예외가 나도 보장)".

### 다이아몬드 연산자 (Diamond Operator, `<>`)

제네릭 인스턴스 생성 시 우변의 타입 인자를 생략할 수 있다.

> **타입 인자(type argument)** — `List<Integer>`의 `<Integer>`처럼 "무엇을 담는 목록인지"를 꺾쇠 안에 적어 주는 것.\
> 예: 아래 "도입 전" 코드에서 좌변과 우변에 두 번 적힌 `<String, List<Integer>>`가 그것이고, "도입 후"에서는 우변의 것이 `<>`로 줄었다.

도입 전:
```java
Map<String, List<Integer>> map = new HashMap<String, List<Integer>>();
```

도입 후:
```java
Map<String, List<Integer>> map = new HashMap<>(); // 타입 추론으로 간결
```

원문이 아래 줄 주석에 적어 둔 말이 이 절의 요약이다 — "타입 추론으로 간결".\
좌변의 `Map<String, List<Integer>>`는 그대로 남고, 우변에서 똑같이 반복되던 `<String, List<Integer>>`만 `<>`가 된다.

> **재서술자 주:** 다이아몬드가 생략해 주는 것은 *적는 수고*이지 타입 검사 자체가 아니다. 같은 시리즈 `java-5.md`가 제네릭을 "컴파일 시점에만 타입을 검사하고, 바이트코드에서는 타입 인자를 지운다(type erasure)"고 적는데, 이 편의 원문은 그 이야기를 다시 적지 않는다. 두 편을 함께 읽어야 하는 자리로 보인다.

### switch문에서 String 사용

도입 전(정수/enum만 가능)에는 if-else 체인을 써야 했다.

도입 후:
```java
String cmd = "start";
switch (cmd) {
    case "start":
        System.out.println("시작");
        break;
    case "stop":
        System.out.println("정지");
        break;
    default:
        System.out.println("알 수 없음");
}
```

원문은 이 절에서 "도입 전" 코드를 따로 보여 주지 않고, 한 문장으로만 적는다 — 정수/enum만 되던 시절에는 "if-else 체인"을 썼다는 것이다.

> **`switch` 문** — 값 하나를 여러 `case` 후보와 맞춰 보고 맞는 가지로 들어가는 문법.\
> 예: 위 코드에서 맞춰 보는 값이 `cmd`이고, 후보가 `"start"`·`"stop"`이며, 어디에도 안 맞으면 `default`로 간다.

### 멀티 catch (Multi-catch)

여러 예외를 하나의 catch 블록에서 처리한다.

도입 전:
```java
try {
    doWork();
} catch (IOException e) {
    log(e);
} catch (SQLException e) {
    log(e); // 동일 처리인데 중복
}
```

도입 후:
```java
try {
    doWork();
} catch (IOException | SQLException e) {
    log(e); // 한 번에 처리
}
```

**왜 이것이 나왔나** — 위 "도입 전" 코드에 원문이 달아 둔 주석이 "동일 처리인데 중복"이다.

두 블록에서 `doWork()`와 `log(e)`는 그대로다. 달라진 것은 `catch` 줄로, 따로 적히던 `catch (IOException e)`와 `catch (SQLException e)`가 `catch (IOException | SQLException e)` 한 줄로 합쳐진다.

### 숫자 리터럴 개선 (언더스코어 / 바이너리 리터럴)

가독성을 위해 숫자에 `_`를 넣을 수 있고, `0b` 접두사로 2진수 리터럴을 쓸 수 있다.

```java
int million   = 1_000_000;       // 언더스코어로 자릿수 구분
long card     = 1234_5678_9012L;
int binary    = 0b1010_0001;     // 바이너리 리터럴
```

> **리터럴(literal)** — 코드에 값을 그대로 적어 넣은 것.\
> 예: 위 코드의 `1_000_000`·`1234_5678_9012L`·`0b1010_0001`이 전부 숫자 리터럴이다.

원문이 주석으로 이름 붙인 것은 둘이다 — `1_000_000`에 붙은 "언더스코어로 자릿수 구분", `0b1010_0001`에 붙은 "바이너리 리터럴".

### NIO.2 — 새 파일 시스템 API (JSR 203)

`java.nio.file` 패키지로 파일 I/O가 현대화되었다. `Path`/`Files`, 심볼릭 링크, 파일 속성, 디렉터리 변경 감시(`WatchService`)를 지원한다.

> **`Path` / `Files`** — 파일이 어디 있는지를 가리키는 타입 / 그 파일을 읽고 쓰고 지우는 도구 모음.\
> 예: 아래 코드에서 자리를 가리키는 것이 `Paths.get("data.txt")`이고, 실제로 읽고 복사하고 지우는 것이 `Files.readAllLines`·`Files.copy`·`Files.delete`다.

> **`WatchService`(디렉터리 변경 감시)** — 폴더 안에서 무언가 바뀌면 알려 주는 장치. 원문이 NIO.2가 지원하는 것으로 든 넷 가운데 하나다.\
> 예: 원문이 이 절에서 함께 든 나머지 셋이 `Path`/`Files`, 심볼릭 링크, 파일 속성이다(이 셋 중 코드로 보여 준 것은 `Path`/`Files`뿐이다).

도입 전:
```java
File file = new File("data.txt");
boolean ok = file.delete(); // 실패 사유를 알기 어려움
```

도입 후:
```java
import java.nio.file.*;

Path path = Paths.get("data.txt");
List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
Files.copy(path, Paths.get("backup.txt"));
Files.delete(path); // 실패 시 구체적 예외(NoSuchFileException 등)
```

**왜 이것이 나왔나** — 두 블록에 원문이 달아 둔 주석이 서로 짝이다. 위쪽 `file.delete()`에 붙은 것이 "실패 사유를 알기 어려움"이고, 아래쪽 `Files.delete(path)`에 붙은 것이 "실패 시 구체적 예외(NoSuchFileException 등)"다.\
위쪽은 성공·실패를 `boolean ok`로만 돌려받고, 아래쪽은 실패의 종류가 예외 타입으로 갈라진다.

> **재서술자 주:** 같은 시리즈 `jdk-1.4.md`도 `java.nio`를 다루지만 그쪽이 든 것은 "채널(Channel), 버퍼(Buffer), 셀렉터(Selector) 기반의 고성능·논블로킹 I/O"다. 이 편의 NIO.2는 이름은 잇지만 대상이 다른 파일 시스템 API(`java.nio.file`)다 — 원문은 두 편의 관계를 직접 적지 않는다.

### Fork/Join 프레임워크 (JSR 166y)

분할 정복(divide-and-conquer) 작업을 멀티코어에서 병렬 실행하는 프레임워크(`ForkJoinPool`, `RecursiveTask`)다. 작업 훔치기(work-stealing) 스케줄링을 사용하며, 후일 Java 8 병렬 스트림의 엔진이 된다.

> **분할 정복(divide-and-conquer)** — 큰 일을 작은 조각으로 쪼개 따로 풀고, 그 답을 다시 합치는 방식.\
> 예: 아래 코드가 배열 구간 `[lo, hi)`를 `mid`에서 둘로 쪼개고(`left`·`right`), `compute()`의 마지막 줄에서 `right.compute() + left.join()`으로 두 답을 합친다.

> **작업 훔치기(work-stealing)** — 원문이 이 프레임워크의 스케줄링 방식으로 든 이름.\
> 예: 이 편의 원문은 이름만 들고 그 동작을 설명하지 않는다 — 이 절에서 원문이 이 이름에 붙인 말은 Fork/Join이 그 스케줄링을 "사용하며"까지다.

```java
class SumTask extends RecursiveTask<Long> {
    final long[] arr; final int lo, hi;
    SumTask(long[] a, int lo, int hi) { this.arr = a; this.lo = lo; this.hi = hi; }
    protected Long compute() {
        if (hi - lo <= 1000) {
            long s = 0; for (int i = lo; i < hi; i++) s += arr[i]; return s;
        }
        int mid = (lo + hi) >>> 1;
        SumTask left = new SumTask(arr, lo, mid);
        left.fork();
        SumTask right = new SumTask(arr, mid, hi);
        return right.compute() + left.join();
    }
}
long total = new ForkJoinPool().invoke(new SumTask(data, 0, data.length));
```

위 코드에서 원문 문장의 두 이름이 실제로 어디에 있는지 짚으면, `RecursiveTask`는 `SumTask`가 상속하는 타입이고, `ForkJoinPool`은 마지막 줄에서 그 작업을 `invoke`로 받아 돌리는 쪽이다.\
쪼개는 기준은 `hi - lo <= 1000`이고, 그보다 크면 `mid`에서 나눠 `fork()`와 `join()`으로 맡기고 받아 온다.

### invokedynamic (JSR 292)

JVM 바이트코드에 동적 메서드 호출을 위한 새 명령 `invokedynamic`과 `java.lang.invoke`(MethodHandle) API가 추가되었다. 정적 타입에 묶이지 않은 호출을 효율적으로 지원해 JRuby, Groovy 등 JVM 동적 언어의 성능을 끌어올렸고, Java 8 람다 구현의 기반이 되었다.

> **바이트코드(bytecode)와 명령(instruction)** — 자바 소스를 컴파일하면 나오는, JVM이 읽는 중간 형태의 코드와 그 한 단위.\
> 예: 원문이 이 자리에 "새 명령"으로 추가됐다고 적은 것이 `invokedynamic`이다.

> **`MethodHandle`(`java.lang.invoke`)** — 어떤 메서드를 가리켜 두었다가 나중에 불러 쓰게 해 주는 손잡이.\
> 예: 원문은 이 API가 `invokedynamic` 명령과 함께 추가됐다고만 적고, 사용 코드는 이 편에 없다.

> **재서술자 주:** 이 문장은 람다를 다루는 같은 시리즈 `java-8.md`를 읽을 때 함께 볼 자리다. 이 편은 `invokedynamic`이 "Java 8 람다 구현의 기반이 되었다"고 적는데, `java-8.md`의 람다 절은 그 구현 방식을 다시 적지 않고 익명 클래스와의 코드 비교만 보여 준다.

## 그 외 변경 / API 추가
- G1 (Garbage-First) 가비지 컬렉터 도입 — Java 7 GA에서는 experimental 상태였고, 정식 지원은 7u4부터 (CMS를 잇는 차세대 GC)
- 동시성 유틸리티 보강: `Phaser`, `ThreadLocalRandom`, `ConcurrentLinkedDeque`
- `java.util.Objects` 유틸리티 클래스 (`requireNonNull`, `equals`, `hash` 등)
- 향상된 타입 추론 및 가변인자 경고(`@SafeVarargs`)
- Unicode 6.0 지원, 새 `Locale`/통화 API 개선
- 클라이언트 측 RIA(Rich Internet Application) 관련 개선 (Java FX 별도 발전)

**언제 쓸 수 있게 됐나** — 위 목록 첫 줄이 그 이야기다. G1은 이 버전 GA 시점에는 experimental이었고, 원문이 적은 정식 지원 시점은 7u4다.

> **experimental(실험적)** — 들어는 있지만 아직 정식으로 지원한다고 보증하지 않는 상태.\
> 예: 원문이 이 상태로 적은 것이 Java 7 GA 시점의 G1이고, 정식 지원은 "7u4부터"다.

> **가비지 컬렉터(GC)** — 더 이상 쓰지 않는 객체가 차지한 메모리를 자동으로 거둬 가는 장치.\
> 예: 원문이 이 줄에서 G1을 "CMS를 잇는 차세대 GC"라 적는다 — CMS가 앞선 것, G1이 뒤이은 것이다.

> **재서술자 주:** G1이 이후 어떻게 되는지는 이 편 밖이다. 같은 시리즈 `java-9.md`가 "JEP 248"로 G1을 기본 GC로 채택했다고 적고, `java-10.md`가 "JEP 307"로 G1의 Full GC를 병렬화했다고 적는다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문 한 문단을 나눠 적은 것이다.)*

- Java SE 7은 Oracle 체제에서 Java가 정상적으로 발전을 재개했음을 보여준 릴리스다.
- Project Coin의 작은 문법 개선들(try-with-resources, diamond, multi-catch, switch-on-String)은 일상 코드의 장황함을 눈에 띄게 줄였고, NIO.2는 노후한 `java.io.File` API를 대체했다.
- 특히 Fork/Join과 invokedynamic은 그 자체로도 유용했지만, 약 2년 8개월 뒤(2014년 3월) Java 역사상 또 한 번의 분수령이 되는 **Java 8의 람다와 스트림**을 떠받치는 인프라로서 더 큰 의미를 가진다.

## 용어 풀이

- **GA(General Availability)** — 누구나 받아 실제로 쓰라고 내놓는 정식 출시. 원문은 이 날짜(7월 28일)와 "발표"(7월 7일)를 구분해 적는다.
- **JSR(Java Specification Request)** — 자바에 무엇을 어떻게 넣을지 정하는 규격 문서의 번호. 이 편에 나온 것이 336·334·203·166y·292다.
- **JCP(Java Community Process)** — 자바 규격을 여러 주체가 함께 정하는 절차. 원문이 공백의 원인 중 하나로 "JCP 내부 갈등"을 든다.
- **LTS(Long-Term Support)** — 한 버전을 오래 지원해 주기로 정해 두는 제도. 원문 표현으로 이 시대엔 "LTS 개념 없음"이다.
- **Plan B** — 준비된 기능만 먼저 내보내고 남은 것은 다음 버전으로 미루는 방침. 원문 표현으로 "기능을 다 채우고 늦게 내기보다, 준비된 것부터 내자".
- **Project Coin** — 원문 표현으로 "큰 부담 없이 일상 코드를 간결하게 만드는 작은 문법 개선들의 묶음(JSR 334)". 제안자는 Joshua Bloch.
- **자원(resource) / `close()`** — 다 쓰면 반드시 닫아야 하는 파일·연결 등 / 그것을 닫는 메서드.
- **`AutoCloseable`** — try 괄호에 넣으면 자동으로 닫히는 대상임을 나타내는 인터페이스. try-with-resources가 요구하는 조건이다.
- **타입 인자(type argument)** — `List<Integer>`의 `<Integer>`처럼 꺾쇠 안에 적는 타입. 다이아몬드는 **우변의** 타입 인자를 생략하게 해 준다.
- **리터럴(literal)** — 코드에 값을 그대로 적어 넣은 것. 이 편에서 개선된 것은 숫자 리터럴의 `_`와 `0b` 접두사다.
- **`Path` / `Files`** — 파일의 자리를 가리키는 타입 / 파일을 읽고 쓰고 지우는 도구 모음. 둘 다 `java.nio.file` 소속이다.
- **`WatchService`** — 디렉터리 변경 감시 장치. 원문이 NIO.2 지원 목록에 든 것이다.
- **분할 정복(divide-and-conquer)** — 큰 일을 쪼개 따로 풀고 답을 합치는 방식. 원문이 Fork/Join이 다루는 작업의 성격으로 든 말이다.
- **작업 훔치기(work-stealing)** — 원문이 Fork/Join의 스케줄링 방식으로 든 이름. 동작은 원문에 없다.
- **바이트코드(bytecode) / 명령(instruction)** — JVM이 읽는 중간 형태의 코드 / 그 한 단위. `invokedynamic`이 이 층에 새로 생긴 명령이다.
- **`MethodHandle`(`java.lang.invoke`)** — 메서드를 가리켜 두었다가 나중에 불러 쓰게 해 주는 손잡이. `invokedynamic`과 함께 추가됐다.
- **experimental(실험적)** — 들어 있으나 아직 정식 지원을 보증하지 않는 상태. 원문이 Java 7 GA 시점의 G1을 이렇게 적는다.
- **가비지 컬렉터(GC)** — 쓰지 않는 객체의 메모리를 자동으로 거둬 가는 장치. 원문은 G1을 "CMS를 잇는 차세대 GC"라 적는다.

## 참고 출처
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [JSR 336: Java SE 7 Release Contents — JCP](https://jcp.org/en/jsr/detail?id=336)
- [Java 7 — WikiChip](https://en.wikichip.org/wiki/Java_7)
- [JSR 334: Small Enhancements to the Java Programming Language (Project Coin) — JCP](https://jcp.org/en/jsr/detail?id=334)
