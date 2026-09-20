# java/syntax/57 — `Files`·`Path` — NIO.2 파일 API — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../26-try-with-resources/`](../26-try-with-resources/)(자원을 닫는 문법)과 [`../44-stream-creation/`](../44-stream-creation/)(스트림 소스). 이 문서의 절반이 그 둘이 만나는 자리다.
> **기준 소스** — Temurin **JDK 21.0.5** 표준 라이브러리 소스 `java.base/java/nio/file/Files.java`·`Path.java`(`lib/src.zip`) · [`Files` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Files.html) · [`Path` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Path.html)
> **실행 검증** — 이 문서의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 일곱(57-a~57-g)을 **17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판의 출력이 전부 같지는 않았다.** `Files.createDirectories` 의 반환값이 **17 에서만 절대 경로**였다(아래 「구현 세부사항 대 언어 보장」이 정본).
> **버전** — `Path` 인터페이스는 `@since 1.7`, `Path.of` 는 **11**, `Files.lines`·`walk`·`list`·`find`·`readAllLines` 는 **1.8**, `Files.readString`·`writeString` 은 **11**.
> **측정 조건** — Linux · ext4 · `file.encoding=UTF-8` · 기본 `Locale` `ko_KR`. 실험은 전부 **임시 스크래치 디렉터리 안의 `sandbox/` 아래**에서 하고 매번 지웠다.\
> 경로 구분자·권한·`probeContentType` 결과는 **OS 에 달렸다.** 그 줄에는 그 사실이 붙어 있다.
> **범위** — 파일 시스템을 **자료구조로 구현하는 것**(트리·경로 정규화 알고리즘)은 [`../../../../../data-structure/33-filesystem/`](../../../../../data-structure/33-filesystem/) 가 정본이다.\
> 그쪽은 **디렉터리 트리를 어떻게 만들고 탐색하나**까지, 여기는 **java.nio.file 이 그것을 어떤 API 로 노출하나**부터다.\
> 스트림을 닫는 **문법**은 [`../26-try-with-resources/`](../26-try-with-resources/)가, 스트림 **소스 팩토리**는 [`../44-stream-creation/`](../44-stream-creation/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`Path` 는 주소지, `Files` 는 그 주소로 가는 심부름꾼이다.**

| 비유 | 실체 |
|---|---|
| **"서울시 강남구 테헤란로 1길 5"라고 적힌 주소지** | `Path` |
| 주소지의 **칸**(시·구·길·번지) | `getName(0)`·`getParent`·`getFileName` |
| 주소지를 **말로 이어 붙이는 것** | 문자열 연결 — 구분자가 어긋난다 |
| 주소지를 **칸 단위로 붙이는 것** | `Path.resolve` |
| **그 주소에 실제로 가 보는 심부름꾼** | `Files` |
| 심부름꾼이 **집 열쇠를 들고 나가서 안 돌려주는 것** | `Files.lines`/`walk` 를 안 닫는 것 |
| 열쇠를 반납하게 하는 **문** | `try`-with-resources |
| **이삿짐을 통째로 트럭에 싣는 것** | `Files.readAllLines` |
| **한 상자씩 들고 나르는 것** | `Files.lines` |

- **주소지는 종이다.** 적어 놓기만 해도 되고, 그 집이 실제로 있는지 없는지와 무관하다.
- 그래서 `Path.of("없는폴더/../also없음/x")` 도 **아무 문제 없이 만들어진다.** `normalize()` 도 된다.
- **심부름꾼이 나가는 순간** 비로소 "그 집이 없다"가 드러난다 — `NoSuchFileException`.
- 심부름꾼 중 **열쇠를 들고 나가는 둘**이 `Files.lines` 와 `Files.walk` 다. 반납을 안 하면 아무 말 없이 열쇠가 쌓인다.

```text
  Path 를 만든다              Files 로 실제로 간다

  Path.of("sandbox/a.txt")    Files.readString(p)
        |                            |
  문자열 조작만 한다            OS 를 부른다
  파일시스템을 안 본다           파일이 없으면 여기서 예외
        |                            |
  exists 검사 없음              NoSuchFileException: sandbox/a.txt
```

그림 해설:

- 왼쪽은 **절대 실패하지 않는다**(문법적으로 잘못된 경로가 아닌 한).
- 오른쪽은 **실패할 수 있다.** 그 경계가 어디인지가 이 주제의 절반이다.

> **NIO.2** — Java 7(JSR 203)에서 들어온 새 파일 API. `java.io.File` 을 대체한다.\
> 예: `new File("x").delete()` 는 실패해도 `false` 만 돌려주지만, `Files.delete(path)` 는 **왜 실패했는지**를 예외로 알려준다.

> **파일 서술자(file descriptor, fd)** — OS 가 열린 파일 하나에 붙이는 번호. 프로세스당 개수 상한이 있다.\
> 예: 리눅스에서 `/proc/self/fd` 디렉터리의 항목 수가 지금 열려 있는 fd 수다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Path` 가 `String` 과 **무엇이 다른가** — 문자열로 경로를 다루면 어디서 틀리나.
2. 어떤 `Files` 메서드가 **닫아야 하는 것**을 돌려주고, 안 닫으면 무슨 일이 생기나.
3. `readAllLines` 와 `lines` 중 **언제 어느 것**인가 — 그 경계는 무엇으로 정해지나.

## 동작 방식

### (1) `Path` 는 구조를 안다

**언제 쓰나** — 경로를 조립·분해할 때.

**실행 결과** (`Ex.java` — 57-a, 17·21·25 동일)

```text
--- (1) Path 는 구조를 안다 — 문자열은 모른다
  toString      : sandbox/data/2026/report.csv
  getFileName   : report.csv
  getParent     : sandbox/data/2026
  getRoot       : null
  getNameCount  : 4
  getName(0..)  : sandbox / data / 2026 / report.csv
  subpath(1,3)  : data/2026
  isAbsolute    : false
  iterator      : [sandbox, data, 2026, report.csv]
--- (2) 구분자를 손으로 이어 붙이면 생기는 일
  문자열 이어붙이기 : sandbox/data/report.csv
  구분자가 두 번이면 : sandbox/data//report.csv
  Path.resolve      : sandbox/data/report.csv
  Path.of 가변인자  : sandbox/data/report.csv
  중복 구분자도 정리 : sandbox/data/report.csv
  Path.of("sandbox/data/") 의 nameCount : 2
```

```text
  String "sandbox/data/2026/report.csv"       Path.of(같은 문자열)

  +-----------------------------------+       +---------+---------+------+------------+
  | s a n d b o x / d a t a / ... .csv|       | sandbox |  data   | 2026 | report.csv |
  +-----------------------------------+       +---------+---------+------+------------+
        글자 28개                                  이름 4개 (getNameCount)
              |                                          |
  substring·indexOf 로 잘라야 한다             getName(i)·getParent 로 꺼낸다
  구분자 규칙을 내가 지켜야 한다                 중복 구분자를 알아서 정리한다
```

그림 해설 (한 단계씩):

- `Path` 는 **이름의 열**이다. 글자가 아니라 칸으로 센다.
- `"sandbox/data/" + "/report.csv"` 는 **`sandbox/data//report.csv`** 가 된다 — 구분자가 둘이다.
- 같은 것을 `Path.of("sandbox//data///report.csv")` 로 만들면 **`sandbox/data/report.csv`** 로 정리된다.
- 끝의 구분자도 무시된다 — `Path.of("sandbox/data/")` 의 `getNameCount()` 는 **2** 다.
- `getRoot()` 가 `null` 인 것은 **상대 경로**라서다. 절대 경로면 `/` 가 나온다.

비용 — `Path` 하나를 만드는 데 파싱 한 번. 대신 구분자 실수가 원천적으로 사라진다.

### (2) `resolve` 는 절대 경로를 만나면 통째로 갈아탄다

**언제 쓰나** — 사용자 입력·설정값을 기준 디렉터리에 붙일 때.

**실행 결과** (`Ex.java` — 57-a, 17·21·25 동일)

```text
--- (3) resolve 의 규칙 — 절대 경로를 주면 통째로 갈아탄다
  resolve("a.txt")        : sandbox/data/a.txt
  resolve("/etc/passwd")  : /etc/passwd   <- base 가 버려진다
  resolve("")             : sandbox/data
  resolveSibling("b.txt") : sandbox/b.txt
  relativize              : data/a.txt
  거꾸로 relativize        : ../..
```

```text
  base = sandbox/data

  resolve("a.txt")       sandbox/data + a.txt      = sandbox/data/a.txt
  resolve("/etc/passwd") sandbox/data 를 버린다     = /etc/passwd
                              ^^^^^^^^^^^^
                    "사용자가 준 경로"를 그대로 resolve 하면
                    디렉터리 밖으로 나갈 수 있다
```

그림 해설 (한 단계씩):

- **절대 경로를 주면 기준이 통째로 버려진다.** javadoc 이 그렇게 정의한다.
- `resolveSibling` 은 **마지막 칸을 바꾼다** — `sandbox/data` 의 형제는 `sandbox/b.txt`.
- `relativize` 는 **두 경로 사이의 상대 경로**를 만든다. 거꾸로 하면 `../..` 이 나온다.
- 업로드 파일명을 `baseDir.resolve(userInput)` 로 붙이는 코드가 **디렉터리 밖으로 나가는 경로**를 만든다.

비용 — `resolve` 자체는 싸다. 대가는 **검증을 내가 해야** 한다는 것이다(「어디서 틀리나」 2).

### (3) `normalize` 는 글자 연산이고 OS 는 아니다

**언제 쓰나** — `..` 이 든 경로를 다룰 때.

**실행 결과** (`Ex.java` — 57-a, 17·21·25 동일)

```text
--- (4) normalize 는 문자열 연산이다 — 파일시스템을 보지 않는다
  원본      : sandbox/data/../logs/./app.log
  normalize : sandbox/logs/app.log
  존재하지 않아도 normalize 는 된다 : also없음/x
  toRealPath(존재하지 않는 경로) : java.nio.file.NoSuchFileException: sandbox/없는파일.txt
--- (5) equals 는 경로 문자열 비교다 — 같은 파일을 가리켜도 다르다
  a : sandbox/data/a.txt
  b : ./sandbox/data/a.txt
  c : sandbox/logs/../data/a.txt
  a.equals(b) : false
  a.equals(c) : false
  a.equals(c.normalize()) : true
  Files.isSameFile(a, b)  : true
  Files.isSameFile(a, c)   : java.nio.file.NoSuchFileException: sandbox/logs/../data/a.txt
    (sandbox/logs 가 없어서다 — OS 는 .. 를 글자가 아니라 실제 디렉터리로 푼다)
  logs 를 만든 뒤 다시      : true
  a.toAbsolutePath().equals(b.toAbsolutePath()) : false
  a.toRealPath().equals(b.toRealPath())         : true
```

```text
  "sandbox/logs/../data/a.txt" 를 두 방식으로 푼다

  Path.normalize()                     OS (Files.isSameFile)
  +-------------------------+          +--------------------------+
  | 글자만 본다             |          | 실제로 sandbox/logs 에    |
  | logs/.. 를 지운다       |          | 들어갔다 나온다           |
  | -> sandbox/data/a.txt   |          | logs 가 없으면            |
  | 파일이 없어도 성공      |          | NoSuchFileException       |
  +-------------------------+          +--------------------------+

  normalize 가 성공했다고 그 경로가 유효한 것이 아니다.
```

그림 해설 (한 단계씩):

- `normalize()` 는 **파일 시스템을 한 번도 안 본다.** 없는 폴더도 정리해 준다.
- `Files.isSameFile` 은 **실제로 간다.** 중간 디렉터리가 없으면 `NoSuchFileException` 이다.
- 그 디렉터리를 만들어 주자 **`true`** 가 됐다. 같은 경로, 같은 코드, 다른 결과다.
- `toRealPath()` 는 **존재해야** 쓸 수 있다 — 없는 경로에 부르면 예외다.
- `equals` 는 **글자 비교**다. javadoc 이 못박는다.

  > **This method does not access the file system** and the file is not required to exist. Where required, the `Files.isSameFile` method may be used to check if two paths locate the same file.

- `toAbsolutePath()` 로 맞춰도 **`./` 가 남아** 여전히 `false` 다. `toRealPath()` 라야 `true` 가 된다.

비용 — `normalize` 는 공짜(문자열 연산), `toRealPath` 는 **시스템 콜**이고 존재를 요구한다.

### (4) `startsWith` 는 이름 단위다

**언제 쓰나** — "이 경로가 기준 디렉터리 안에 있나"를 검사할 때.

**실행 결과** (`Ex.java` — 57-a, 17·21·25 동일)

```text
--- (6) startsWith 는 이름 단위다 — 문자열 prefix 가 아니다
  Path.of("sandbox/data").startsWith("sandbox")   : true
  Path.of("sandbox/data").startsWith("sand")      : false
  "sandbox/data".startsWith("sand") (String)      : true
  endsWith("a.txt")      : true
  endsWith("txt")        : false
--- (7) 비교와 정렬 — compareTo 는 사전식이다
  정렬 결과 : [a/1.txt, a/10.txt, a/2.txt, b/1.txt]
```

```text
  Path.startsWith            String.startsWith

  sandbox / data             s a n d b o x / d a t a
  ^^^^^^^                    ^^^^
  칸 단위로 맞춘다            글자 단위로 맞춘다
      |                          |
  "sand" 는 칸이 아니다       "sand" 가 접두사다
  -> false                   -> true
```

그림 해설 (한 단계씩):

- **`Path` 쪽이 우리가 원하는 답**이다. `sandbox-evil/` 을 `sandbox` 의 하위로 잘못 판정하지 않는다.
- `endsWith("txt")` 가 `false` 인 것도 같은 이유다 — 확장자는 칸이 아니다.
- 정렬은 **사전식**이다. `a/10.txt` 가 `a/2.txt` 보다 앞에 온다 — 숫자 순이 아니다.

비용 — `String.startsWith` 보다 조금 비싸지만, **디렉터리 탈출 검사에서는 이쪽만 맞다.**

### (5) `Files.lines` 를 안 닫으면 — 조용히 샌다

**언제 쓰나** — 파일을 줄 단위로 읽을 때. 이 주제에서 가장 비싼 함정이다.

**실행 결과** (`Ex.java` — 57-c, JDK 21.0.5 — 17 은 시작 fd 가 7이라 모든 수가 1 크다)

```text
--- (1) Files.lines 는 닫아야 하는 스트림이다 — 안 닫으면 예외가 없다
  시작 열린 fd 수 : 6
  200번 읽은 줄 수 : 600   (예외 0건)
  안 닫고 200번 뒤 fd 수 : 206
--- (2) try-with-resources 로 같은 일을 하면
  200번 읽은 줄 수 : 600
  닫고 200번 뒤 fd 수 : 206
--- (3) GC 를 돌리면 어떻게 되나
  System.gc() 뒤 fd 수 : 6   (Cleaner 가 언제 도는지는 보장이 없다)
--- (4) Files.readAllLines 는 닫을 것이 없다
  전 fd : 6
  200번 읽은 줄 수 : 600
  후 fd : 6   (메서드가 돌아오기 전에 스스로 닫는다)
--- (5) Files.walk 도 같다
  전 fd : 6
  walk 결과 합 : 1200
  후 fd : 6
  닫고 나서 fd : 6
```

```text
  안 닫고 200번                        try-with-resources 로 200번

  fd 6 ----------------> fd 206        fd 206 ----------------> fd 206
       한 번에 하나씩 쌓인다                  하나도 늘지 않았다
            |                                      |
  예외 0건 · 경고 0건 · 결과는 정확          같은 결과, 같은 줄 수
            |
  파일이 더 많거나 오래 돌면
  "Too many open files" 로 죽는다
```

그림 해설 (한 단계씩):

- **결과는 정확하다.** 600줄을 제대로 셌고 예외가 하나도 없다. 그래서 테스트가 통과한다.
- 그런데 **fd 가 6 → 206** 으로 늘었다. 200번 열고 하나도 안 닫았다.
- (2)에서는 **206 에서 한 개도 안 늘었다** — 닫은 쪽은 쌓이지 않는다.
  (앞 절의 200개가 아직 남아 있어 숫자가 206 에서 시작할 뿐이다.)
- (4)의 `Files.readAllLines` 는 **닫을 것이 없다** — 메서드가 돌아오기 전에 스스로 닫는다.
- (5)의 `Files.walk` 는 **여기서는 fd 가 안 늘었다.** `count()` 로 **끝까지 소비**했기 때문이다 — 순회가 끝나면 열린 디렉터리 핸들이 하나씩 닫힌다.\
  **중간에 멈추면 이야기가 다르다.** 따로 확인했다(`Ex.java` — 57-f).

```text
===== JDK 21.0.5 =====
--- (1) walk 를 끝까지 소비하고 안 닫으면
  전 fd : 6
  후 fd : 6   (순회가 끝나면 디렉터리 핸들이 하나씩 닫힌다)
--- (2) walk 를 중간에 멈추고 안 닫으면
  전 fd : 6
  찾은 것 100개? true
  후 fd : 406   <- 여기서 샌다
--- (3) 같은 일을 try-with-resources 로
  gc 뒤 fd : 406
  후 fd : 406
```

```text
  Files.walk(box).count()                     Files.walk(box).filter(..).findFirst()

  모든 디렉터리를 끝까지 읽는다                 첫 파일을 찾자마자 멈춘다
        |                                            |
  다 읽은 디렉터리는 그때그때 닫힌다            아직 안 읽은 디렉터리가 열린 채 남는다
        |                                            |
  100번 돌려도 fd 그대로                        100번 돌리면 fd +400 (호출당 4개)
```

- **`findFirst`·`anyMatch`·`limit` 로 단락하는 순간 `walk` 는 샌다.** 실측에서 100번에 fd 400개가 남았다.
- (3)에서 `try`-with-resources 로 같은 일을 100번 더 했더니 **406 에서 한 개도 안 늘었다.**
- ★ 그리고 여기서는 **`System.gc()` 가 회수하지 않았다**(406 그대로). `lines` 쪽은 (3)에서 회수됐는데 `walk` 쪽은 아니다 — **GC 에 기대면 안 되는 이유**가 이 대비에 있다.
- javadoc 이 `walk` 에도 `lines` 와 같은 apiNote 를 단다((6) 아래 인용).

**javadoc 이 뭐라고 적나**

> (`Files.lines`) The returned stream contains a reference to an open file. **The file is closed by closing the stream.**
> @apiNote **This method must be used within a try-with-resources statement** or similar control structure to ensure that the stream's open file is closed promptly after the stream's operations have completed.

> (`Files.walk`) The returned stream contains references to one or more open directories. **The directories are closed by closing the stream.**
> @apiNote **This method must be used within a try-with-resources statement** or similar control structure ...

비용 — `try` 블록 한 줄. 안 쓰면 **무음 누수**다. 46번의 표현을 빌리면 "조용하고, 배포 뒤에 발견된다".

### (6) 최종 연산은 스트림을 닫지 않는다

**언제 쓰나** — "`count()` 했으니 끝났겠지"라고 생각할 때.

**실행 결과** (`Ex.java` — 57-c, JDK 21.0.5)

```text
--- (6) 최종 연산이 스트림을 닫지는 않는다 (46번과 이어진다)
  열기 직후 fd : 7
  count()      : 3
  count() 뒤 fd: 7   <- 줄지 않았다
  close() 뒤 fd: 6
--- (7) 닫힌 뒤 다시 쓰면
  첫 count : 3
  두 번째    : java.lang.IllegalStateException: stream has already been operated upon or closed
--- (8) 닫은 뒤 lazy 하게 읽으려 하면
  닫고 나서 toList : java.lang.IllegalStateException: stream has already been operated upon or closed
```

```text
  Files.lines(p)   -> fd 7 (하나 열렸다)
        |
  count()          -> 3 을 돌려준다
        |
  fd 7             <- 그대로다. 최종 연산은 close() 를 부르지 않는다
        |
  close()          -> fd 6
```

그림 해설 (한 단계씩):

- **최종 연산은 스트림을 "소비 완료"로 만들 뿐 `close()` 를 부르지 않는다** — [`../46-terminal-operations/`](../46-terminal-operations/) 7번에서 `onClose` 로 확인한 것과 같은 규칙이다.
- 여기서는 그 결과를 **fd 숫자로** 볼 수 있다.
- 닫힌 뒤 다시 쓰면 `IllegalStateException: stream has already been operated upon or closed` — **소비한 스트림과 같은 메시지**다.

비용 — 없음. 다만 **"최종 연산 = 정리 완료"라는 직관이 틀렸다**는 것을 알아야 한다.

### (7) 메모리 — `readAllLines` 는 전부 올린다

**언제 쓰나** — 파일 크기가 커질 수 있을 때.

**측정 조건** — 70MB(정확히 72,888,896바이트)·200만 줄 텍스트 파일. `-Xmx` 를 바꿔 가며 1회씩 실행. **JMH 가 아니다.** 시간은 참고용이고, 재현되는 것은 **어느 힙에서 죽느냐**다.

**실행 결과** (`Ex.java` — 57-d, JDK 21.0.5)

```text
  -Xmx64m    readAllLines : Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
  -Xmx128m   readAllLines : Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
  -Xmx256m   readAllLines : Files.readAllLines: 200000 줄 일치, 432ms
  -Xmx512m   readAllLines : Files.readAllLines: 200000 줄 일치, 428ms
  -Xmx16m    lines        : Files.lines      : 200000 줄 일치, 279ms
  -Xmx32m    lines        : Files.lines      : 200000 줄 일치, 259ms
  -Xmx64m    lines        : Files.lines      : 200000 줄 일치, 277ms
  -Xmx512m   lines        : Files.lines      : 200000 줄 일치, 248ms
```

```text
  같은 70MB 파일, 같은 일(끝자리가 7인 줄 세기)

  Files.readAllLines              Files.lines
  +---------------------+         +---------------------+
  | 200만 String 을     |         | 한 줄씩 읽고 버린다 |
  | 전부 힙에 올린다    |         |                     |
  +---------------------+         +---------------------+
  -Xmx128m  OutOfMemory           -Xmx16m   성공
  -Xmx256m  성공                  -Xmx512m  성공
        ^                               ^
  파일 크기에 비례해 힙이 든다     파일 크기와 무관하다
```

**OOM 스택트레이스** (JDK 21.0.5)

```text
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
	at java.base/java.lang.StringUTF16.compress(StringUTF16.java:161)
	at java.base/java.lang.String.<init>(String.java:4768)
	at java.base/java.io.BufferedReader.implReadLine(BufferedReader.java:403)
	at java.base/java.io.BufferedReader.readLine(BufferedReader.java:347)
	at java.base/java.io.BufferedReader.readLine(BufferedReader.java:436)
	at java.base/java.nio.file.Files.readAllLines(Files.java:3395)
	at java.base/java.nio.file.Files.readAllLines(Files.java:3433)
	at Ex.main(Ex.java:29)
```

그림 해설 (한 단계씩):

- **`Files.lines` 는 16MB 힙에서도 돌았다.** 70MB 파일인데 그렇다.
- `readAllLines` 는 **256MB 가 있어야** 돌았다. 파일의 3~4배다(`String` 객체 헤더·`char` 배열 오버헤드).
- 스택트레이스에 `Files.readAllLines` 가 그대로 찍힌다 — 원인을 찾기는 쉽다.
- 다만 이 OOM 은 **파일이 커지고 나서야** 난다. 개발 환경의 작은 샘플로는 안 드러난다.

비용 — `lines` 는 닫아야 하고, `readAllLines` 는 메모리를 쓴다. **둘 중 하나는 낸다.**

### (8) 심볼릭 링크 — `walk` 는 기본적으로 안 따라간다

**언제 쓰나** — 디렉터리를 재귀 순회할 때.

**실행 결과** (`Ex.java` — 57-e, 17·21·25 동일)

```text
--- (2) 심볼릭 링크 — 기본 walk 는 따라가지 않는다
  isSymbolicLink       : true
  readSymbolicLink     : a
  isDirectory(기본)     : true   (링크를 따라간다)
  isDirectory(NOFOLLOW) : false
  walk 기본        : [sandbox, sandbox/a, sandbox/a/1.txt, sandbox/a/b, sandbox/a/b/2.txt, sandbox/a/b/c, sandbox/a/b/c/3.log, sandbox/link-to-a, sandbox/top.txt]
  walk FOLLOW_LINKS: [sandbox, sandbox/a, sandbox/a/1.txt, sandbox/a/b, sandbox/a/b/2.txt, sandbox/a/b/c, sandbox/a/b/c/3.log, sandbox/link-to-a, sandbox/link-to-a/1.txt, sandbox/link-to-a/b, sandbox/link-to-a/b/2.txt, sandbox/link-to-a/b/c, sandbox/link-to-a/b/c/3.log, sandbox/top.txt]
--- (3) 링크가 자기 조상을 가리키면 — 순환
  만든 링크 : sandbox/a/b/loop -> ../..
  walk 기본(따라가지 않음) : 10개, 예외 없음
  walk FOLLOW_LINKS        : java.io.UncheckedIOException: java.nio.file.FileSystemLoopException: sandbox/a/b/loop
```

```text
  sandbox/                         walk 기본            walk FOLLOW_LINKS
  ├── a/
  │   ├── 1.txt                    a/1.txt 한 번         a/1.txt
  │   └── b/                                             link-to-a/1.txt   <- 같은 파일이 두 번
  │       ├── 2.txt
  │       └── c/3.log
  ├── link-to-a -> a               원소로는 나오지만      들어가서 내용을 편다
  └── top.txt                      들어가지 않는다        (9개 -> 14개)

  링크가 조상을 가리키면

  sandbox/a/b/loop -> ../..  (= sandbox)
        |
  기본      : 원소로만 나온다. 예외 없음
  FOLLOW    : FileSystemLoopException
```

그림 해설 (한 단계씩):

- **기본은 안 따라간다.** 링크 자체는 원소로 나오지만 그 안으로는 안 들어간다.
- `FOLLOW_LINKS` 를 주면 **같은 파일이 두 경로로 두 번** 나온다 — 9개가 14개가 됐다.
- 링크가 조상을 가리키면 `FOLLOW_LINKS` 는 **`FileSystemLoopException`** 을 던진다. 무한 루프로 안 빠진다.
- 그 예외가 **`UncheckedIOException` 으로 감싸여** 나온다는 점이 중요하다 — `IOException` 으로는 안 잡힌다.
- `Files.isDirectory` 는 **기본이 따라가기**다(`true`). 링크 자체를 보려면 `NOFOLLOW_LINKS` 를 준다.

비용 — 기본값이 안전하다. `FOLLOW_LINKS` 를 켜면 **중복과 순환**을 직접 감당해야 한다.

### (9) 끊어진 링크와 권한 없는 디렉터리

**언제 쓰나** — 남이 만든 디렉터리를 훑을 때.

**실행 결과** (`Ex.java` — 57-e, 17·21·25 동일)

```text
--- (4) 끊어진 링크
  exists                    : false
  exists(NOFOLLOW)          : true
  notExists                 : true
  isSymbolicLink            : true
  readString(끊어진 링크)    : java.nio.file.NoSuchFileException: sandbox/dangling
  readAttributes(기본)       : java.nio.file.NoSuchFileException: sandbox/dangling
  readAttributes(NOFOLLOW)   : true
  walk 는 끊어진 링크를 원소로 내놓는다 : true
  walk + filter(isRegularFile) 에서 사라진다 : 4개
--- (5) 권한이 없는 디렉터리를 만나면
  walk(권한 없음)           : java.io.UncheckedIOException: java.nio.file.AccessDeniedException: sandbox/locked
  walk 를 forEach 로 소비   : java.io.UncheckedIOException: java.nio.file.AccessDeniedException: sandbox/locked
  list(권한 없음 디렉터리)  : java.nio.file.AccessDeniedException: sandbox/locked
--- (6) walkFileTree 는 예외를 콜백으로 준다
  방문한 파일 : 7개
  실패한 것   : [sandbox/locked -> AccessDeniedException]
```

```text
  Files.walk                           Files.walkFileTree

  스트림 순회 중 예외를 만나면          visitFileFailed 콜백이 불린다
        |                                      |
  UncheckedIOException 으로 감싸        CONTINUE 를 돌려주면 계속 간다
  파이프라인 전체가 중단된다                   |
        |                              나머지 7개를 다 방문했고
  이미 처리한 원소도 결과가 없다          실패한 것 목록도 남았다
```

그림 해설 (한 단계씩):

- **`Files.walk` 는 중간 실패에 약하다.** 하나 실패하면 전체가 `UncheckedIOException` 으로 끝난다.
- 그 예외는 **검사 예외가 아니다.** `catch (IOException e)` 로는 안 잡힌다.
- **`Files.walkFileTree`** 는 `visitFileFailed` 콜백으로 **건너뛰며 계속**할 수 있다. 실패 목록도 모을 수 있다.
- 끊어진 링크는 **`exists()` 가 `false`, `exists(NOFOLLOW)` 가 `true`** 다 — 그 조합이 "링크는 있는데 대상이 없다"의 정의다.
- `notExists()` 도 `true` 다. **`!exists()` 와 `notExists()` 는 일반적으로 같지 않다**(권한 때문에 판정 불가면 둘 다 `false` 일 수 있다).

비용 — `walkFileTree` 는 코드가 길다. 대신 **부분 실패를 감당**할 수 있다.

### (10) 원자적 이동 — 같은 파일시스템에서만

**언제 쓰나** — "쓰다 만 파일이 보이면 안 된다"는 요구가 있을 때.

**실행 결과** (`Ex.java` — 57-b, 17·21·25 동일)

```text
--- (7) copy 와 move
copy(덮어쓰기 옵션 없이) : java.nio.file.FileAlreadyExistsException: sandbox/data/b.txt
copy(REPLACE_EXISTING)  : sandbox/data/b.txt
  b.txt 내용 : [덮어씀]
move(같은 디렉터리)      : sandbox/data/c.txt
move(원본 없음)          : java.nio.file.NoSuchFileException: sandbox/data/b.txt
move(ATOMIC_MOVE 같은 FS) : sandbox/data/e.txt
  /dev/shm 파일시스템 : tmpfs  /  현재 디렉터리 : ext4
move(ATOMIC_MOVE 다른 FS) : java.nio.file.AtomicMoveNotSupportedException: sandbox/data/e.txt -> /dev/shm/java-nio-probe-2576339.txt: 부적절한 장치간 연결
move(옵션 없이 다른 FS)   : /dev/shm/java-nio-probe-2576339.txt
  옮겨진 파일 지우기       : true
```

```text
  같은 파일시스템 (ext4 -> ext4)        다른 파일시스템 (ext4 -> tmpfs)

  ATOMIC_MOVE   성공                    ATOMIC_MOVE   AtomicMoveNotSupportedException
  (rename(2) 한 번)                     (rename(2) 가 EXDEV 를 돌려준다)

  옵션 없음     성공                    옵션 없음     성공
                                        (복사한 뒤 원본 삭제 — 원자적이지 않다)
```

그림 해설 (한 단계씩):

- **같은 파일시스템 안에서만 원자적**이다. OS 의 `rename` 이 그렇게 정의돼 있기 때문이다.
- 다른 파일시스템으로 옮기려 하면 `AtomicMoveNotSupportedException` 이다.
- 메시지 끝의 **`부적절한 장치간 연결`** 은 OS 의 `EXDEV` 를 이 머신의 로케일(`ko_KR`)로 번역한 것이다 — **다른 로케일에서는 다른 글자**가 나온다.
- 옵션 없이 `move` 하면 **성공한다.** 대신 복사 + 삭제라 **중간 상태가 보인다.**
- 안전한 쓰기의 관용구는 이렇다.

```java
Path tmp = target.resolveSibling(target.getFileName() + ".tmp");
Files.writeString(tmp, content);
Files.move(tmp, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
// 같은 디렉터리에 임시 파일을 만드는 것이 핵심 — 다른 파일시스템으로 나가지 않는다
```

비용 — 임시 파일 하나. 대신 **읽는 쪽이 반쯤 쓰인 파일을 볼 일이 없다.**

## 문법 — 형태와 규칙

### `Path` 만들기

```java
Path.of("sandbox/data/a.txt")            // 11+
Path.of("sandbox", "data", "a.txt")      // 가변 인자 — 구분자를 안 쓴다
Paths.get("sandbox/data/a.txt")          // 7~ (지금은 Path.of 를 쓴다)
new File("x").toPath()                   // File 에서
FileSystems.getDefault().getPath("x")    // 가장 밑바닥
```

- **`Path.of` 는 Java 11** 부터다(`src.zip` 의 `@since 11`). `Paths.get` 은 7부터.
- javadoc 은 `Paths` 클래스를 "may be deprecated in future" 취급하지 않지만, `Path.of` 쪽이 읽기 좋다.

### 주요 `Files` 연산 지도

| 하고 싶은 일 | 메서드 | 닫아야 하나 | `@since` |
|---|---|---|---|
| 통째로 읽기(문자열) | `readString(Path)` | 아니다 | **11** |
| 통째로 읽기(줄 리스트) | `readAllLines(Path)` | 아니다 | 1.8 |
| 통째로 읽기(바이트) | `readAllBytes(Path)` | 아니다 | 1.7 |
| **줄 단위 스트림** | `lines(Path)` | **그렇다** | 1.8 |
| 통째로 쓰기 | `writeString(Path, CharSequence, OpenOption...)` | 아니다 | **11** |
| 통째로 쓰기(바이트·줄) | `write(Path, byte[]/Iterable, OpenOption...)` | 아니다 | 1.7 |
| 버퍼 읽기·쓰기 | `newBufferedReader`/`newBufferedWriter` | **그렇다** | 1.7 |
| 한 단계 목록 | `list(Path)` | **그렇다** | 1.8 |
| **재귀 순회** | `walk(Path, FileVisitOption...)` | **그렇다** | 1.8 |
| 조건으로 찾기 | `find(Path, int, BiPredicate, ...)` | **그렇다** | 1.8 |
| 콜백 순회 | `walkFileTree(Path, FileVisitor)` | 아니다 | 1.7 |
| glob 으로 한 단계 | `newDirectoryStream(Path, String)` | **그렇다** | 1.7 |
| 복사·이동·삭제 | `copy`/`move`/`delete`/`deleteIfExists` | 아니다 | 1.7 |
| 디렉터리 생성 | `createDirectory`/`createDirectories` | 아니다 | 1.7 |
| 속성 | `readAttributes`/`size`/`getLastModifiedTime` | 아니다 | 1.7 |
| 존재 확인 | `exists`/`notExists`/`isRegularFile`/`isDirectory` | 아니다 | 1.7 |

- **「닫아야 하나」 칸이 `그렇다`인 것은 전부 `Stream`·`Reader`·`DirectoryStream` 을 돌려준다.**
- 외우는 규칙: **`Stream` 을 돌려주는 `Files` 메서드는 전부 닫아야 한다.**

### `walk` · `list` · `find` 의 차이

**실행 결과** (`Ex.java` — 57-e, 17·21·25 동일)

```text
--- (1) walk / list / find 가 각각 무엇을 돌려주나
  list(box)      : [sandbox/a, sandbox/top.txt]
  walk(box)      : [sandbox, sandbox/a, sandbox/a/1.txt, sandbox/a/b, sandbox/a/b/2.txt, sandbox/a/b/c, sandbox/a/b/c/3.log, sandbox/top.txt]
  walk(box, 1)   : [sandbox, sandbox/a, sandbox/top.txt]
  walk(box, 2)   : [sandbox, sandbox/a, sandbox/a/1.txt, sandbox/a/b, sandbox/top.txt]
  find(*.txt)    : [sandbox/a/1.txt, sandbox/a/b/2.txt, sandbox/top.txt]
  newDirectoryStream(glob) : [sandbox/a/1.txt]
  walk 는 자기 자신을 포함한다 : [sandbox]
```

| | 범위 | 자기 자신 | 필터 |
|---|---|---|---|
| `list` | **한 단계** | **포함 안 함** | 없다 |
| `walk` | 재귀(깊이 지정 가능) | **포함** | 없다 |
| `walk(p, 0)` | 자기 자신만 | 포함 | 없다 |
| `find` | 재귀 + 술어 | 포함(술어를 통과하면) | `BiPredicate<Path, BasicFileAttributes>` |
| `newDirectoryStream(p, glob)` | 한 단계 | 포함 안 함 | glob 문자열 |

- **`walk` 는 시작 경로 자신을 포함한다.** `walk(p).forEach(Files::delete)` 가 디렉터리까지 지우려 드는 이유다.
- `find` 의 술어는 **속성을 같이 받는다** — `isRegularFile` 를 다시 호출하지 않아도 된다.

### 삭제 — 아래에서 위로

**실행 결과** (`Ex.java` — 57-b·57-e, 17·21·25 동일)

```text
--- (6) 디렉터리를 지우면
delete(비어있지 않은 디렉터리) : java.nio.file.DirectoryNotEmptyException: sandbox/p/q
delete(비어있는 디렉터리)     : 지웠다
--- (7) 삭제는 아래에서 위로
  deleteTree 없이 Files.delete(box) : java.nio.file.DirectoryNotEmptyException: sandbox
  reverseOrder 로 walk 해서 지우면 : sandbox 존재? false
```

```java
try (var s = Files.walk(root)) {
    s.sorted(Comparator.reverseOrder())     // 깊은 것부터
     .forEach(p -> { try { Files.delete(p); } catch (IOException e) { throw new UncheckedIOException(e); } });
}
```

- `Files.delete` 는 **빈 디렉터리만** 지운다. `DirectoryNotEmptyException` 이 그것을 말한다.
- `Comparator.reverseOrder()` 가 **사전식 역순**이라 자식이 부모보다 먼저 온다((4)의 정렬 규칙).
- **재귀 삭제 유틸이 표준에 없다.** 위 네 줄이 사실상의 관용구다.

### 인코딩

**실행 결과** (`Ex.java` — 57-b, 17·21·25 동일)

```text
--- (5) 인코딩 — 기본은 UTF-8(18+) 이지만 깨진 바이트를 만나면
readString(기본 UTF-8)  : java.nio.charset.MalformedInputException: Input length = 1
readString(ISO_8859_1)  : Ã(a
  file.encoding : UTF-8
  Charset.defaultCharset : UTF-8
```

- `Files.readString`·`readAllLines`·`lines` 의 **기본 인코딩은 UTF-8** 이다 — `file.encoding` 과 무관하게 javadoc 이 그렇게 정한다.
- 깨진 바이트를 만나면 **`MalformedInputException`** 이다. 조용히 `?` 로 바꾸지 않는다.
- `ISO_8859_1` 로 읽으면 어떤 바이트든 통과한다 — 바이너리를 문자열로 왕복시킬 때 쓰는 수법이다.

## 어디서 틀리나

### 1. `Files.lines`·`Files.walk` 를 안 닫는다

- (5)에서 본 것이다. **fd 가 6 → 206** 으로 늘었고 예외는 0건이었다.
- 짧게 도는 CLI 에서는 프로세스가 끝나며 정리되므로 **안 드러난다.** 오래 도는 서버에서 터진다.
- 증상은 `Too many open files` — **전혀 다른 코드에서** 난다. 원인 추적이 어렵다.
- 방어: **`Files` 가 `Stream` 을 돌려주면 무조건 `try`-with-resources.** [`../26-try-with-resources/`](../26-try-with-resources/)가 문법의 정본이다.

```java
// 안 된다
long n = Files.lines(p).filter(...).count();

// 된다
try (Stream<String> s = Files.lines(p)) {
    long n = s.filter(...).count();
}
```

### 2. 사용자 입력을 그대로 `resolve` 한다

```java
Path target = uploadDir.resolve(userFileName);   // 위험하다
```

- (2)에서 본 것이다. `userFileName` 이 `/etc/passwd` 면 **`uploadDir` 이 통째로 버려진다.**
- `../../../etc/passwd` 면 `resolve` 는 그대로 이어 붙이고, OS 가 밖으로 나간다.
- 방어:

```java
Path base = uploadDir.toAbsolutePath().normalize();
Path target = base.resolve(userFileName).normalize();
if (!target.startsWith(base)) {          // (4) 의 이름 단위 검사
    throw new IllegalArgumentException("디렉터리 밖 경로");
}
```

- **`startsWith` 는 `Path` 의 것**을 써야 한다. `String.startsWith` 로는 `sandbox-evil` 이 통과한다((4)).

### 3. `Path.equals` 로 같은 파일인지 판단한다

- (3)에서 본 것이다. `sandbox/data/a.txt` 와 `./sandbox/data/a.txt` 가 **`equals` 로 `false`** 다.
- `toAbsolutePath()` 로 맞춰도 `./` 가 남아 여전히 `false` 였다.
- 방어: **`Files.isSameFile`** 또는 **`toRealPath()` 로 정규화한 뒤 비교.** 둘 다 파일이 존재해야 한다.

### 4. `readAllLines` 로 큰 파일을 읽는다

- (7)에서 본 것이다. 70MB 파일이 **`-Xmx128m` 에서 OOM** 이었다.
- 개발 환경의 샘플 파일은 작아서 **안 드러난다.** 운영 로그에서 터진다.
- 방어: **크기가 예측 불가하면 `Files.lines`.** 그리고 닫는다(1번).
- `Files.readString` 도 같다. javadoc 이 `@throws OutOfMemoryError if the file is extremely large, for example larger than {@code 2GB}` 라고 **예외로 못박아** 둔다.

### 5. `Files.walk` 를 `catch (IOException)` 으로 감싼다

- (9)에서 본 것이다. 순회 중 실패는 **`UncheckedIOException`** 으로 감싸여 나온다.
- `Files.walk(...)` **호출 자체**는 `IOException` 을 던지고, **순회 중**은 `UncheckedIOException` 이다 — 두 곳이 다르다.
- 방어: 부분 실패를 감당해야 하면 **`Files.walkFileTree`** 를 쓴다. `visitFileFailed` 가 그 자리다.

### 6. 빈 디렉터리가 아닌데 `Files.delete` 를 부른다

- `DirectoryNotEmptyException` 이다. **재귀 삭제는 표준에 없다.**
- 방어: `walk` + `reverseOrder` 관용구(위 「문법」 절). 그리고 그 `walk` 도 닫는다.

### 7. `exists()` 를 검사한 뒤 여는 것을 안전하다고 믿는다

```java
if (Files.exists(p)) {
    String s = Files.readString(p);   // 그 사이에 지워질 수 있다
}
```

- **TOCTOU**(검사 시점과 사용 시점의 틈)다. 다른 프로세스가 그 사이에 지울 수 있다.
- 게다가 `exists()` 는 권한 때문에 판정 불가면 `false` 를 돌려준다 — **"없다"와 "모르겠다"를 구분하지 않는다.**
- 방어: **그냥 열고 `NoSuchFileException` 을 잡는다.** 예외가 곧 원자적 검사다.

### 8. 다른 파일시스템으로 `ATOMIC_MOVE` 를 한다

- (10)에서 본 것이다. `AtomicMoveNotSupportedException` 이다.
- 흔한 실수: 임시 파일을 `/tmp` 에 만들고 최종 위치로 `ATOMIC_MOVE` 하는 것. `/tmp` 가 tmpfs 면 실패한다.
- 방어: **임시 파일을 목적지와 같은 디렉터리에** 만든다 — `target.resolveSibling(...)`.

### 9. 심볼릭 링크를 생각 안 한다

- (8)에서 본 것이다. `FOLLOW_LINKS` 를 켜면 **같은 파일이 두 번** 나오고, 순환이 있으면 **`FileSystemLoopException`** 이다.
- 끊어진 링크는 `exists()` 가 `false` 인데 `walk` 의 원소로는 **나온다**((9)).
- 방어: `walk` 결과에 **`filter(Files::isRegularFile)`** 를 거는 것이 기본기다. 실측에서 그것만으로 끊어진 링크가 사라졌다.

## 구현 세부사항 대 언어 보장

### `Files.createDirectories` 의 반환값이 17 에서만 달랐다

**실행 결과** (`Ex.java` — 57-g)

```text
===== JDK 17.0.13 =====
  새로 만들 때        : isAbsolute=true  nameCount=10
  이미 있을 때        : isAbsolute=false  nameCount=3
  한 단계만 새로 만들 때: isAbsolute=false  nameCount=2
  createDirectory     : isAbsolute=false  nameCount=2
  r1.equals(인자)     : false

===== JDK 21.0.5 =====                 ===== JDK 25.0.1 =====
  새로 만들 때        : isAbsolute=false  nameCount=3      (둘이 같다)
  이미 있을 때        : isAbsolute=false  nameCount=3
  한 단계만 새로 만들 때: isAbsolute=false  nameCount=2
  createDirectory     : isAbsolute=false  nameCount=2
  r1.equals(인자)     : true
```

**`src.zip` 에서 원인이 그대로 보인다.**

```java
// JDK 17.0.13 — java.base/java/nio/file/Files.java
        SecurityException se = null;
        try {
            dir = dir.toAbsolutePath();      // <- 인자 변수를 덮어쓴다
        } catch (SecurityException x) {
            se = x;
        }
        ...
        return dir;                          // <- 절대 경로가 나간다
```

```java
// JDK 21.0.5 — 같은 파일
        SecurityException se = null;
        Path absDir = dir;                   // <- 별도 변수를 쓴다
        try {
            absDir = dir.toAbsolutePath();
        } catch (SecurityException x) {
            se = x;
        }
        ...
        return dir;                          // <- 인자가 그대로 나간다
```

```text
  Files.createDirectories("sandbox/p/q")

  JDK 17                              JDK 21 · 25
  여러 단계를 만들어야 할 때           언제나
        |                                   |
  절대 경로를 돌려준다                 인자를 그대로 돌려준다
  nameCount 10 (머신 경로 깊이)        nameCount 3
        |                                   |
  r1.equals(인자) == false             r1.equals(인자) == true
```

그림 해설 (한 단계씩):

- **17 은 "여러 단계를 새로 만들 때"에만** 절대 경로를 돌려줬다. 이미 있거나 한 단계만 만들 때는 상대 경로였다.
- 그래서 **테스트가 어쩌다 통과한다** — 같은 테스트를 두 번째 돌리면 디렉터리가 이미 있어 상대 경로가 나온다.
- javadoc 의 `@return` 은 "the directory" 라고만 적는다. **절대/상대를 약속한 적이 없다.**
- 방어: **`createDirectories` 의 반환값을 쓰지 말고 인자로 쓴 `Path` 를 그대로 쓴다.**

### 표

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `Path.equals` 가 파일시스템을 안 본다 | **보장** | javadoc — "This method does not access the file system" |
| `Files.lines`/`walk` 를 닫아야 한다 | **보장** | javadoc apiNote — "must be used within a try-with-resources statement" |
| `readAllLines` 가 스스로 닫는다 | **보장** | 반환 타입이 `List` 다. 열린 자원이 없다 |
| 최종 연산이 스트림을 닫지 않는다 | **보장** | [`../46-terminal-operations/`](../46-terminal-operations/) 7번 |
| `Files.readString` 의 기본 인코딩 UTF-8 | **보장** | javadoc |
| `delete` 가 비지 않은 디렉터리를 거부 | **보장** | javadoc — `DirectoryNotEmptyException` |
| `walk` 기본이 링크를 안 따라간다 | **보장** | javadoc — `FOLLOW_LINKS` 옵션이 있어야 따라간다 |
| `FOLLOW_LINKS` + 순환에서 `FileSystemLoopException` | **보장** | javadoc |
| `ATOMIC_MOVE` 가 다른 FS 에서 실패 | **보장** | javadoc — `AtomicMoveNotSupportedException` |
| **`createDirectories` 의 반환 경로가 절대인가 상대인가** | **보장 아님 — 17 과 21 이 달랐다** | 위 실측 + `src.zip` diff |
| **`AtomicMoveNotSupportedException` 의 메시지 끝 문구** | **보장 아님** | OS 의 `EXDEV` 를 로케일로 번역한 것 — 이 머신은 `부적절한 장치간 연결` |
| **fd 숫자(6 / 7)** | **보장 아님** | 17 은 7, 21·25 는 6 에서 시작했다 |
| **OOM 이 나는 `-Xmx` 경계** | **보장 아님** | 파일·GC·JDK 에 달렸다. 이 머신 70MB 파일에서 128m 실패 / 256m 성공 |
| `probeContentType` 의 결과 | **보장 아님** | OS 의 MIME 데이터베이스에서 온다. 이 머신은 `text/plain` |
| POSIX 권한 문자열 | **보장 아님** | umask·OS 에 달렸다. 이 머신은 `rw-rw-r--` |

**세 판에서 같았던 것**

- 57-a·57-c(fd 숫자 제외)·57-e 는 출력이 같았다.
- 57-b 는 `createDirectories` 한 줄만 달랐다.
- 57-d 의 OOM 스택트레이스는 **줄 번호가 세 판 다 달랐다**(`String.java:4501` / `:4768` / `:4842`).
- **하지만 그것은 관찰이지 보장이 아니다.**

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 | 왜 |
|---|---|---|
| 작은 설정 파일 읽기 | `Files.readString` | 짧고 닫을 것이 없다 |
| 크기를 모르는 파일 읽기 | `Files.lines` + `try`-with-resources | 메모리가 파일 크기에 안 묶인다 |
| 줄 수가 확실히 적다 | `Files.readAllLines` | 스트림을 닫는 부담이 없다 |
| 바이너리 | `Files.readAllBytes` / `newInputStream` | |
| 한 디렉터리 목록 | `Files.list` + `try` | |
| 재귀 순회(전부 성공 전제) | `Files.walk` + `try` | |
| 재귀 순회(부분 실패 허용) | `Files.walkFileTree` | `visitFileFailed` 로 건너뛴다 |
| 조건으로 찾기 | `Files.find` + `try` | 속성을 같이 받아 재조회가 없다 |
| glob 패턴 | `Files.newDirectoryStream(p, "*.log")` + `try` | |
| 안전한 쓰기 | 같은 디렉터리에 `.tmp` → `ATOMIC_MOVE` + `REPLACE_EXISTING` | 반쯤 쓰인 파일이 안 보인다 |
| 디렉터리 통째 삭제 | `walk` + `reverseOrder` + `delete` (+ `try`) | 표준 유틸이 없다 |
| 같은 파일인지 | `Files.isSameFile` | `equals` 는 글자 비교다 |
| 디렉터리 밖 검사 | `normalize()` 후 `Path.startsWith` | `String.startsWith` 는 틀린다 |
| **쓰면 안 되는 것** | `java.io.File` 의 `delete()`·`mkdirs()` | 실패 이유를 안 알려준다(`boolean` 만 돌려준다) |

판단 규칙 세 줄.

- **`Files` 가 `Stream` 을 돌려주면 무조건 `try`-with-resources.** 예외 없다.
- **크기를 모르면 스트림, 확실히 작으면 통째로.**
- **경로 판단은 `Path` 의 메서드로.** `String` 으로 내려가는 순간 구분자·`..`·접두사에서 틀린다.

## 핵심 문장

- `Path` 는 **이름의 열**이지 문자열이 아니다 — `startsWith("sand")` 가 `false` 인 것이 그 증거다.
- **`normalize()` 는 파일시스템을 안 본다.** 없는 디렉터리도 정리해 주고, 같은 경로를 OS 는 `NoSuchFileException` 으로 거부했다.
- **`Files.lines`·`Files.walk` 는 닫아야 한다.** 안 닫고 200번 읽자 fd 가 6 → 206 으로 늘었고 **예외는 0건**이었다.
- **`readAllLines` 는 파일 크기에 비례해 힙을 쓴다.** 70MB 파일이 `-Xmx128m` 에서 OOM, `Files.lines` 는 `-Xmx16m` 에서 성공했다.
- `walk` 는 기본적으로 **심볼릭 링크를 안 따라간다.** 따라가게 하면 같은 파일이 두 번 나오고, 순환이면 `FileSystemLoopException` 이다.

## 관련 자료

- [`../26-try-with-resources/`](../26-try-with-resources/) — **이 주제의 선행.** 그쪽은 **`AutoCloseable` 과 suppressed 예외의 문법**까지, 여기는 **어느 `Files` 메서드가 그 문법을 요구하나**부터
- [`../44-stream-creation/`](../44-stream-creation/) — **이 주제의 선행.** 그쪽은 **스트림 소스 팩토리 전반**까지, 여기는 **그중 파일 소스가 자원을 잡는다는 점**부터
- [`../46-terminal-operations/`](../46-terminal-operations/) — 최종 연산이 스트림을 닫지 않는다는 규칙의 정본. 여기서는 그것을 **fd 숫자로** 확인한다
- [`../../../../../data-structure/33-filesystem/`](../../../../../data-structure/33-filesystem/) — 파일 시스템을 **자료구조로 구현**하는 쪽. 그쪽은 **트리·경로 정규화를 직접 만드는 것**까지, 여기는 **표준 API 가 그것을 어떻게 노출하나**부터
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 57번)
- [**25번 주제**](../25-exceptions/)(예외) — `IOException` 은 검사 예외, `UncheckedIOException` 은 아니다. 그 경계가 (9)의 핵심
- [**45번 주제**](../45-intermediate-operations/)(중간 연산) — `walk` 결과에 `filter` 를 거는 패턴
- [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) — 자원 누수를 운영 관점에서 분류한 쪽. 그쪽은 **실패 모드의 분류**까지, 여기는 **그 실패를 만드는 API 호출**까지
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — `Files.lines`·`walk` 가 스트림과 함께 들어온 맥락

## 용어 풀이

- **NIO.2** — Java 7 에서 들어온 `java.nio.file` 패키지. `java.io.File` 을 대체한다. 실패 이유를 예외로 알려주는 것이 가장 큰 차이다.
- **`Path`** — 파일 위치를 **이름의 열**로 표현한 것. 파일이 실제로 존재하지 않아도 만들 수 있다.
- **`Files`** — `Path` 를 받아 실제 파일시스템 연산을 하는 정적 유틸리티 클래스.
- **`normalize()`** — 경로에서 `.` 과 `..` 을 글자 수준에서 정리하는 것. 예: `a/b/../c` → `a/c`. 파일시스템을 보지 않는다.
- **`toRealPath()`** — OS 에게 실제 경로를 물어보는 것. 심볼릭 링크를 풀고, **파일이 존재해야** 한다.
- **파일 서술자(fd)** — OS 가 열린 파일에 붙이는 번호. 프로세스당 상한이 있어 누수하면 `Too many open files` 가 난다.
- **`UncheckedIOException`** — `IOException` 을 감싼 비검사 예외. 스트림 순회처럼 검사 예외를 던질 수 없는 자리에서 쓰인다.
- **심볼릭 링크(symbolic link)** — 다른 경로를 가리키는 파일. 예: `link-to-a -> a` 는 `a` 디렉터리를 가리키는 별칭이다.
- **끊어진 링크(dangling link)** — 가리키는 대상이 없는 심볼릭 링크. `exists()` 는 `false`, `exists(NOFOLLOW_LINKS)` 는 `true` 다.
- **`FileSystemLoopException`** — `FOLLOW_LINKS` 로 순회하다 순환을 만났을 때의 예외. 무한 루프 대신 이것을 던진다.
- **원자적 이동(atomic move)** — 중간 상태가 보이지 않는 이동. OS 의 `rename` 으로 되며 **같은 파일시스템 안에서만** 가능하다.
- **`AtomicMoveNotSupportedException`** — 다른 파일시스템으로 `ATOMIC_MOVE` 를 시도했을 때의 예외.
- **TOCTOU(time-of-check to time-of-use)** — 검사한 시점과 쓰는 시점 사이에 상태가 바뀌는 문제. 예: `exists()` 가 `true` 였는데 읽으려니 지워져 있다.
- **glob** — `*.log` 처럼 파일명을 고르는 간단한 패턴 문법. 정규식이 아니다.

## 더 들어가면

- **`Files.lines` 를 안 닫아도 GC 가 결국 정리한다 — 다만 언제인지 모른다.**\
  실측에서 `System.gc()` 뒤에 fd 가 206 → 6 으로 줄었다.\
  JDK 9 부터 `FileChannel`·`FileInputStream` 이 `Cleaner` 에 등록되기 때문인데, **언제 도는지는 보장이 없다.** fd 상한에 먼저 닿으면 그걸로 끝이다.
- **읽는 도중 파일이 지워져도 계속 읽힌다.**

  ```text
  --- (9) 읽는 도중 파일이 사라지면
    첫 줄 : line 1
    지운 뒤 둘째 줄 : line 2   (열린 핸들은 살아 있다 — POSIX)
  ```

  POSIX 에서 `unlink` 는 **디렉터리 엔트리만** 지운다. 열린 fd 가 있는 동안 내용은 살아 있다.\
  **윈도에서는 다르다** — 이 머신에 윈도가 없어 **안 돌려 봄**이다.
- **`Files.lines` 의 예외는 두 곳에서 난다.**

  ```text
  --- (10) Files.lines 는 어디서 예외를 던지나
    없는 파일로 lines() : java.nio.file.NoSuchFileException: sandbox/없음.txt
    lines() 호출 자체는 성공
    순회 중 : java.io.UncheckedIOException: java.nio.charset.MalformedInputException: Input length = 1
  ```

  **파일이 없으면 `lines()` 호출에서 `IOException`**(검사 예외), **인코딩이 깨졌으면 순회 중 `UncheckedIOException`**(비검사)다.\
  두 예외를 한 `catch` 로 잡을 수 없다.
- **`Files.newDirectoryStream` 의 glob 은 정규식이 아니다.**\
  `*` 는 구분자를 넘지 않고, `**` 는 넘는다. `FileSystem.getPathMatcher("glob:**/*.log")` 로 따로 쓸 수도 있다.\
  이 문서는 `newDirectoryStream(p, "*.txt")` 한 형태만 돌려 봤다.
- **`WatchService` 로 디렉터리 변경을 감시할 수 있다.**\
  `path.register(watcher, ENTRY_CREATE, ENTRY_MODIFY)` 형태다. 이 문서 범위 밖이고 **안 돌려 봤다.**
- **`Files.getFileStore(path).type()` 으로 파일시스템 종류를 알 수 있다.**\
  (10)에서 `ext4` 와 `tmpfs` 를 이것으로 확인했다. `ATOMIC_MOVE` 가능 여부를 미리 판단할 때 쓸 수 있지만, **같은 타입이라고 같은 파일시스템인 것은 아니다** — 확실한 방법은 `getFileStore` 두 개를 `equals` 로 비교하는 것이다(**안 돌려 봄**).
