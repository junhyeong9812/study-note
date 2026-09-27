# java/syntax/57 — `Files`·`Path` — NIO.2 파일 API — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 일곱(57-a~57-g)을 **Temurin 17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판이 같았다고 적지 않는다.** 12번에서 실제로 갈렸고, fd 시작값도 17 만 하나 더 컸다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` — `java.base/java/nio/file/Files.java`·`Path.java` 원문이다.\
> 측정 조건: Linux · ext4 · `file.encoding=UTF-8` · 기본 `Locale` `ko_KR`. 실험은 전부 임시 스크래치 디렉터리 안의 `sandbox/` 아래에서 하고 매번 지웠다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `Path` 는 문자열과 무엇이 다른가

**출력** (`Ex.java` — 57-a, 17·21·25 동일)

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

**앞 다섯 줄**

| 호출 | 결과 |
|---|---|
| `getNameCount()` | **4** |
| `getFileName()` | `report.csv` |
| `getParent()` | `sandbox/data/2026` |
| `getRoot()` | **`null`** |
| `subpath(1, 3)` | `data/2026` — 끝은 배타적이다 |

**`getRoot()` 가 `null` 인 이유**

- **상대 경로**이기 때문이다. 루트 컴포넌트가 없다.
- 절대 경로면 `/` 가 나온다(이 머신의 `rootDirectories` 는 `[/]` 하나다).

**중복 구분자**

- `Path.of("sandbox//data///report.csv")` → **`sandbox/data/report.csv`**
- 생성 시점에 정리된다. 문자열에는 그 기능이 없다.

**끝 구분자**

- `Path.of("sandbox/data/").getNameCount()` = **2**
- 끝의 `/` 는 이름을 하나 더 만들지 않는다.

**문자열 연결과의 차이**

```text
  "sandbox/data/" + "/report.csv"   ->  sandbox/data//report.csv
                                                    ^^
                                        구분자가 둘. 리눅스는 통과하지만
                                        문자열 비교·정규식·로그가 어긋난다

  Path.of("sandbox/data/").resolve("report.csv")  ->  sandbox/data/report.csv
```

- 더 나쁜 경우: 한쪽에 구분자가 **없으면** `sandbox/datareport.csv` 가 된다. 조용히 다른 파일이다.

### 2. `resolve` 와 `relativize`

**출력** (`Ex.java` — 57-a, 17·21·25 동일)

```text
--- (3) resolve 의 규칙 — 절대 경로를 주면 통째로 갈아탄다
  resolve("a.txt")        : sandbox/data/a.txt
  resolve("/etc/passwd")  : /etc/passwd   <- base 가 버려진다
  resolve("")             : sandbox/data
  resolveSibling("b.txt") : sandbox/b.txt
  relativize              : data/a.txt
  거꾸로 relativize        : ../..
--- (6) startsWith 는 이름 단위다 — 문자열 prefix 가 아니다
  Path.of("sandbox/data").startsWith("sandbox")   : true
  Path.of("sandbox/data").startsWith("sand")      : false
  "sandbox/data".startsWith("sand") (String)      : true
```

**왜 절대 경로에서 base 가 버려지나**

- javadoc 의 정의다 — **"If the other parameter is an absolute path then this method trivially returns other."**
- 논리적으로도 맞다. 절대 경로는 이미 루트부터의 전체 경로라 기준이 필요 없다.

**업로드 파일명을 그대로 `resolve` 하면**

```text
  uploadDir.resolve(userFileName)

  userFileName = "photo.jpg"          -> uploads/photo.jpg           정상
  userFileName = "/etc/passwd"        -> /etc/passwd                 uploads 가 사라졌다
  userFileName = "../../etc/passwd"   -> uploads/../../etc/passwd    OS 가 밖으로 나간다
```

**막는 검사**

```java
Path base   = uploadDir.toAbsolutePath().normalize();
Path target = base.resolve(userFileName).normalize();
if (!target.startsWith(base)) {
    throw new IllegalArgumentException("디렉터리 밖 경로");
}
```

- **`normalize()` 를 두 번** 하는 것이 핵심이다. 안 하면 `..` 이 남아 `startsWith` 가 통과한다.

**`String.startsWith` 로 하면**

```text
  base   = "/app/uploads"
  target = "/app/uploads-evil/x.txt"

  String.startsWith  ->  true    <- 뚫린다
  Path.startsWith    ->  false   <- "uploads" 와 "uploads-evil" 은 다른 이름이다
```

- 이름 뒤에 글자를 붙인 형제 디렉터리에서 뚫린다.

### 3. `normalize` 는 어디까지 하는가

**출력** (`Ex.java` — 57-a, 17·21·25 동일)

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

**앞 세 줄**

- `normalize()` → `sandbox/logs/app.log`
- 없는 경로도 → `also없음/x` (`없는폴더/..` 가 상쇄됐다)
- `toRealPath()` → **`NoSuchFileException`**

**존재하지 않아도 되는 이유**

- `normalize()` 는 **이름의 열을 조작하는 연산**이다. `x/..` 를 지우고 `.` 을 빼는 것이 전부다.
- 시스템 콜이 없다. 그래서 공짜이고, 그래서 **검증이 아니다.**

**`a.equals(b)` 와 javadoc**

- **`false`** 다.

  > Whether or not two path are equal depends on the file system implementation. ... **This method does not access the file system and the file is not required to exist.** Where required, the `Files.isSameFile` method may be used to check if two paths locate the same file.

**`toAbsolutePath()` 로도 `false` 인 이유**

```text
  a = sandbox/data/a.txt        -> /...//sandbox/data/a.txt
  b = ./sandbox/data/a.txt      -> /.../ ./sandbox/data/a.txt
                                        ^^
                          "." 이 이름 하나로 그대로 남는다
```

- `toAbsolutePath()` 는 **앞에 현재 디렉터리를 붙일 뿐** 정규화하지 않는다.
- `toRealPath()` 는 OS 에게 물어 `.` 도 링크도 다 풀어 준다 — 그래서 `true` 가 됐다.

**`sandbox/logs` 가 없을 때 `isSameFile`**

- **`NoSuchFileException: sandbox/logs/../data/a.txt`**
- OS 는 `..` 을 **글자로 지우지 않는다.** 실제로 `sandbox/logs` 에 들어가려 하고, 없으니 실패한다.
- `sandbox/logs` 를 만들어 주자 **`true`** 가 됐다.
- **`normalize()` 가 성공했다고 그 경로가 유효한 것이 아니다.** 이 한 줄이 이 문항의 요점이다.

### 4. `Files.lines` 를 안 닫으면

**출력** (`Ex.java` — 57-c, JDK 21.0.5 — 17 은 모든 fd 수가 1 크다)

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
```

**예외**

- **하나도 안 난다.**

**결과**

- **정확하다.** 600줄을 제대로 셌다.
- 이 둘이 합쳐져서 **테스트가 통과한다.** 그것이 이 함정이 비싼 이유다.

**fd 변화**

- **6 → 206.** 200번 열고 하나도 안 닫았다.

**`try`-with-resources 로 하면**

- **206 에서 한 개도 안 늘었다**(앞 절이 남긴 200개 때문에 206 에서 시작할 뿐이다).
- 즉 **증가분 0** 이다.

**운영에서의 증상**

- fd 상한에 닿으면 **소켓도, 새 파일도 못 연다.** `Too many open files` 계열의 `IOException` 이 난다.
- 터지는 자리가 **누수한 코드가 아니다.** 우연히 그 다음에 파일·소켓을 여는 코드가 맞는다. 원인 추적이 어렵다.
- `lsof -p <pid>` 로 보면 같은 파일이 수백 개 열려 있는 것이 보인다.
- ★ **여기까지는 실제로 터뜨려 보지 않았다**(fd 상한까지 채우려면 수천 번을 돌려야 한다). 위 fd 숫자 6 → 206 만이 실측이다.

### 5. `Files.walk` 는 언제 새는가

**출력** (`Ex.java` — 57-f, JDK 21.0.5)

```text
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

**어느 쪽이 새나**

- **(B) — 중간에 멈추는 쪽**이다.

**얼마나**

- 100번에 **400개.** 호출당 4개다(이 디렉터리 구조에서).

**왜 한쪽만 새나**

```text
  Files.walk(box).count()

  sandbox 를 연다 -> 읽는다 -> 다 읽었다 -> 닫는다
  d0 을 연다      -> 읽는다 -> 다 읽었다 -> 닫는다
  d1 을 ...
        |
  끝까지 가면 열었던 것을 전부 닫고 끝난다 -> fd 그대로

  Files.walk(box).filter(..).findFirst()

  sandbox 를 연다 -> 읽는다
  d0 을 연다      -> f.txt 발견!
        |
  findFirst 가 "그만" 이라고 한다
        |
  아직 안 읽은 디렉터리들이 열린 채로 남는다 -> fd 증가
```

- **단락 평가가 있으면 샌다.** `findFirst`·`anyMatch`·`limit` 가 전부 그렇다.
- 그리고 `walk` 를 쓰는 대부분의 실제 코드에 그 중 하나가 붙어 있다.

**`System.gc()` 로 회수되나**

- **안 된다.** (3)에서 `gc` 뒤에도 **406 그대로**였다.
- **`Files.lines` 쪽과 다르다** — 거기서는 206 → 6 으로 줄었다.

```text
  Files.lines 를 안 닫음    System.gc()  ->  회수됐다 (206 -> 6)
  Files.walk 를 안 닫음     System.gc()  ->  회수 안 됐다 (406 그대로)
                                              ^^^^^^^^^^^^
                          GC 에 기대면 안 되는 이유가 이 대비에 있다
```

**javadoc**

> The returned stream contains references to one or more open directories. **The directories are closed by closing the stream.**
> @apiNote **This method must be used within a try-with-resources statement** or similar control structure to ensure that the stream's open directories are closed promptly after the stream's operations have completed.

- `lines` 와 **같은 문장 구조**다. `Files` 가 `Stream` 을 돌려주면 전부 이 apiNote 가 붙어 있다.

### 6. 최종 연산이 파일을 닫는가

**출력** (`Ex.java` — 57-c, JDK 21.0.5)

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

**세 지점의 fd**

```text
  Files.lines(p)   ->  6 에서 7 로 (하나 열렸다)
  count()          ->  7 그대로
  close()          ->  6 으로 (닫혔다)
```

**`count()` 뒤에 안 줄어드는 이유**

- **최종 연산은 스트림을 "소비 완료" 상태로 만들 뿐 `close()` 를 부르지 않는다.**
- [`../46-terminal-operations/`](../46-terminal-operations/) 7번에서 `onClose` 콜백으로 확인한 것과 **같은 규칙**이고, 여기서는 그 규칙의 **비용이 fd 숫자로** 보인다.

**닫은 뒤 다시 부르면**

- `java.lang.IllegalStateException: stream has already been operated upon or closed`

**같은 메시지를 본 곳**

- [`../46-terminal-operations/`](../46-terminal-operations/) 6번 — **소비한 스트림을 재사용**했을 때의 메시지와 **한 글자도 같다.**
- 즉 "소비됨"과 "닫힘"을 **같은 상태로** 취급한다.

**닫은 스트림에 `toList()`**

- **같은 예외**다. `toList` 도 최종 연산이므로 소비 여부 검사에 먼저 걸린다.

### 7. `readAllLines` 대 `lines` — 메모리

**측정 조건** — 70MB(72,888,896바이트)·200만 줄. `-Xmx` 별로 1회씩. **JMH 아님**, 반복 1회. 재현되는 것은 시간이 아니라 **어느 힙에서 죽느냐**다.

**출력** (`Ex.java` — 57-d, JDK 21.0.5)

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

**`-Xmx64m` 에서**

- `readAllLines` → **`OutOfMemoryError: Java heap space`**
- `lines` → **성공** (200,000줄 일치, 277ms)

**`readAllLines` 가 성공하는 힙**

- **256m 부터.** 128m 에서는 실패했다.
- 파일 크기(70MB)의 **3~4배**다. `String` 객체 헤더와 `List` 의 배열 오버헤드 때문이다.

**`lines` 의 최소**

- **16m 에서 돌았다.** 더 낮춰 보지는 않았다.
- 파일 크기와 **무관**하다. 한 줄씩 읽고 버린다.

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

- 마지막 JDK 프레임은 **`java.nio.file.Files.readAllLines(Files.java:3433)`** 이다. 원인이 트레이스에 그대로 적힌다.
- 줄 번호는 세 판이 달랐다 — 17 은 `String.java:4501`, 21 은 `:4768`, 25 는 `:4842`(+ `StringUTF16.java:161` 대 `:212`).

**경계 수치는 보장인가**

- **아니다.** 파일 내용(줄 길이 분포·문자 종류)·GC·JDK 판에 달렸다.
- 보장은 **성질**이다 — `readAllLines` 는 파일 크기에 비례해 힙을 쓰고, `lines` 는 안 쓴다.
- `Files.readString` 의 javadoc 은 아예 예외로 못박는다.

  > @throws OutOfMemoryError if the file is extremely large, for example larger than `2GB`

### 8. 없는 파일·없는 디렉터리

**출력** (`Ex.java` — 57-b, 17·21·25 동일 — `createDirectories(2단계)` 한 줄만 17 에서 절대 경로다)

```text
--- (1) 없는 파일을 읽으면
readString(없음)    : java.nio.file.NoSuchFileException: sandbox/없음.txt
readAllLines(없음)  : java.nio.file.NoSuchFileException: sandbox/없음.txt
size(없음)          : java.nio.file.NoSuchFileException: sandbox/없음.txt
delete(없음)        : java.nio.file.NoSuchFileException: sandbox/없음.txt
deleteIfExists(없음) : false
exists(없음)        : false
notExists(없음)     : true
--- (2) 없는 디렉터리 아래에 쓰면
writeString(없는디렉터리/x) : java.nio.file.NoSuchFileException: sandbox/없는디렉터리/x.txt
createDirectory(2단계)      : java.nio.file.NoSuchFileException: sandbox/p/q
createDirectories(2단계)    : sandbox/p/q
createDirectories(이미 있음) : sandbox/p/q
createDirectory(이미 있음)  : java.nio.file.FileAlreadyExistsException: sandbox/p/q
--- (6) 디렉터리를 지우면
delete(비어있지 않은 디렉터리) : java.nio.file.DirectoryNotEmptyException: sandbox/p/q
delete(비어있는 디렉터리)     : 지웠다
readString(디렉터리)          : java.io.IOException: 디렉터리입니다
size(디렉터리)                : 4096 바이트 (디렉터리 엔트리 크기 — 파일 내용 합계가 아니다)
```

**여덟 줄의 예외**

| 호출 | 결과 |
|---|---|
| `readString(없음.txt)` | `NoSuchFileException: sandbox/없음.txt` |
| `delete(없음.txt)` | `NoSuchFileException: sandbox/없음.txt` |
| `deleteIfExists(없음.txt)` | **예외 없음 — `false`** |
| `writeString(없는디렉터리/x.txt)` | `NoSuchFileException: sandbox/없는디렉터리/x.txt` |
| `createDirectory("p/q")` | `NoSuchFileException: sandbox/p/q` |
| `createDirectories("p/q")` | **성공** |
| `createDirectory("p/q")` (이미 있음) | `FileAlreadyExistsException: sandbox/p/q` |
| `delete("p")` (비어 있지 않음) | `DirectoryNotEmptyException: sandbox/p/q` |

- **메시지가 경로 한 줄뿐**이라는 점에 주목하라. "왜"는 **예외 타입**이 말한다.
- 덤: `readString(디렉터리)` 의 메시지 **`디렉터리입니다`** 는 OS 의 `EISDIR` 을 `ko_KR` 로 번역한 것이다 — **로케일에 따라 달라진다.**
- 덤: `size(디렉터리)` 는 **4096** 이다. 안에 든 파일 크기의 합이 아니라 **디렉터리 엔트리 자체의 크기**다.

**`delete` 와 `deleteIfExists`**

| | 없을 때 | 있을 때 |
|---|---|---|
| `delete` | **`NoSuchFileException`** | 지운다(`void`) |
| `deleteIfExists` | **`false`** | 지우고 `true` |

**`createDirectory` 와 `createDirectories`**

| | 부모가 없을 때 | 이미 있을 때 |
|---|---|---|
| `createDirectory` | `NoSuchFileException` | **`FileAlreadyExistsException`** |
| `createDirectories` | **중간 단계를 다 만든다** | **조용히 성공** |

**두 번 불러도 되나**

- **된다.** `createDirectories` 는 멱등이다. 이것이 `createDirectory` 와의 두 번째 차이다.

**디렉터리 통째로 지우기**

```java
try (var s = Files.walk(root)) {
    s.sorted(Comparator.reverseOrder())
     .forEach(p -> { try { Files.delete(p); } catch (IOException e) { throw new UncheckedIOException(e); } });
}
```

- `reverseOrder` 가 **사전식 역순**이라 자식이 부모보다 먼저 온다.
- **표준에 재귀 삭제 유틸이 없다.** 이 네 줄이 사실상의 관용구다.
- 그 `walk` 도 **닫아야 한다**(5번).

### 9. 심볼릭 링크와 `walk`

**출력** (`Ex.java` — 57-e, 17·21·25 동일)

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
```

**(A) 에 `link-to-a` 가 있나**

- **있다** — `sandbox/link-to-a` 가 원소로 나온다.
- 그러나 **그 아래로는 안 들어간다.** `link-to-a/1.txt` 같은 원소가 없다.

**(B) 와의 원소 수 차이**

- (A) **9개** → (B) **14개**. 5개가 늘었다.
- 늘어난 것은 `link-to-a/1.txt`·`link-to-a/b`·`link-to-a/b/2.txt`·`link-to-a/b/c`·`link-to-a/b/c/3.log` — **`a/` 아래 전부가 두 번째 경로로 다시** 나온 것이다.
- **같은 파일이 두 번 처리된다.** 복사·집계 코드가 여기서 틀린다.

**(C) 가 던지는 것**

```text
java.io.UncheckedIOException: java.nio.file.FileSystemLoopException: sandbox/a/b/loop
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
감싸는 타입이 UncheckedIOException 이다
```

- **원인은 `FileSystemLoopException`**(`IOException` 의 하위), **감싸는 것은 `UncheckedIOException`**.
- 무한 루프에 빠지지 않고 예외를 던지는 것이 이 옵션의 안전장치다.

**`Files.isDirectory(link)`**

- 기본 → **`true`** (링크를 따라가서 대상이 디렉터리인지 본다)
- `NOFOLLOW_LINKS` → **`false`** (링크 자체는 디렉터리가 아니다)

**끊어진 링크의 세 판정**

| 호출 | 결과 | 뜻 |
|---|---|---|
| `exists()` | **`false`** | 대상이 없다 |
| `exists(NOFOLLOW_LINKS)` | **`true`** | 링크 자체는 있다 |
| `notExists()` | **`true`** | |

- **이 조합이 "끊어진 링크"의 정의다.**
- 그리고 `walk` 는 이 링크를 **원소로 내놓는다.** `filter(Files::isRegularFile)` 를 걸면 사라진다(실측에서 4개가 남았다).

### 10. 권한 없는 디렉터리를 만나면

**출력** (`Ex.java` — 57-e, 17·21·25 동일)

```text
--- (5) 권한이 없는 디렉터리를 만나면
  walk(권한 없음)           : java.io.UncheckedIOException: java.nio.file.AccessDeniedException: sandbox/locked
  walk 를 forEach 로 소비   : java.io.UncheckedIOException: java.nio.file.AccessDeniedException: sandbox/locked
  list(권한 없음 디렉터리)  : java.nio.file.AccessDeniedException: sandbox/locked
--- (6) walkFileTree 는 예외를 콜백으로 준다
  방문한 파일 : 7개
  실패한 것   : [sandbox/locked -> AccessDeniedException]
```

**(A) 가 던지는 것**

- `java.io.UncheckedIOException` 이 `java.nio.file.AccessDeniedException` 을 감싼 것.
- `count()` 든 `forEach` 든 **똑같다** — 순회 중 어디서 소비하든 같은 자리에서 터진다.

**(B) 와의 차이**

- `Files.list(locked)` 는 **`AccessDeniedException` 을 그대로** 던진다. 감싸지 않는다.

```text
  Files.list(p)              메서드 호출 자체가 디렉터리를 연다
                             -> IOException (검사 예외) 을 직접 던진다

  Files.walk(p).count()      호출은 성공하고, 순회 중에 실패한다
                             -> Stream 의 계약상 검사 예외를 던질 수 없다
                             -> UncheckedIOException 으로 감싼다
```

**(C)**

- **끝까지 돈다.** 파일 7개를 방문했고, 실패한 것 목록에 `sandbox/locked -> AccessDeniedException` 하나가 남았다.

**`catch (IOException e)` 로 (A) 를 잡을 수 있나**

- **없다.** `UncheckedIOException` 은 `RuntimeException` 의 하위다.

```java
// 안 된다 — 순회 중 실패를 못 잡는다
try (var s = Files.walk(root)) { ... }
catch (IOException e) { ... }

// 된다
catch (UncheckedIOException e) { IOException cause = e.getCause(); ... }
```

- `Files.walk(root)` **호출 자체**는 `IOException` 을 던지므로 **두 `catch` 가 다 필요**하다.

**부분 실패를 허용해야 하면**

- **`Files.walkFileTree`** 를 쓴다. `visitFileFailed(Path, IOException)` 가 그 자리다.
- `FileVisitResult.CONTINUE` 를 돌려주면 건너뛰고 계속, `TERMINATE` 면 멈춘다.

### 11. 원자적 이동

**출력** (`Ex.java` — 57-b, 17·21·25 동일 — `/dev/shm` 파일명의 pid 만 다르다)

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

**실패하는 것**

| 호출 | 결과 |
|---|---|
| `ATOMIC_MOVE` ext4 → ext4 | **성공** |
| `ATOMIC_MOVE` ext4 → tmpfs | **`AtomicMoveNotSupportedException`** |
| 옵션 없이 ext4 → tmpfs | **성공** |
| `copy` (대상이 이미 있음) | **`FileAlreadyExistsException`** |

**메시지의 마지막 조각**

- **`부적절한 장치간 연결`** — OS 의 `EXDEV`(cross-device link) 를 이 머신의 로케일(`ko_KR`)로 번역한 것이다.
- **보장이 아니다.** 영어 로케일에서는 `Invalid cross-device link` 가 나올 것이고(이 머신에서 **안 돌려 봄**), 윈도에서는 또 다를 것이다.
- **메시지를 파싱하지 말고 `AtomicMoveNotSupportedException` 타입으로 잡는다.**

**옵션 없이 하면 무엇을 잃나**

```text
  ATOMIC_MOVE (같은 FS)           옵션 없음 (다른 FS)

  rename(2) 한 번                 read/write 로 복사 -> 원본 삭제
       |                                 |
  중간 상태가 없다                  복사 중인 파일이 보인다
  보는 쪽은 "옛 파일" 아니면       보는 쪽이 반쯤 쓰인 파일을 읽을 수 있다
  "새 파일" 둘 중 하나만 본다
```

- **원자성**을 잃는다. 크래시하면 **양쪽에 다 있거나 어느 쪽에도 없을** 수 있다.

**안전한 쓰기 관용구**

```java
Path tmp = target.resolveSibling(target.getFileName() + ".tmp");
Files.writeString(tmp, content);
Files.move(tmp, target,
           StandardCopyOption.ATOMIC_MOVE,
           StandardCopyOption.REPLACE_EXISTING);
```

**임시 파일을 어디에**

- **목적지와 같은 디렉터리**다. `resolveSibling` 이 그것을 보장한다.
- 이유: `/tmp` 에 만들면 그게 **다른 파일시스템**(tmpfs)일 수 있고, 그러면 `ATOMIC_MOVE` 가 위에서 본 예외로 실패한다.
- 이 머신에서 `/tmp` 와 홈은 같은 ext4 였지만(`df -T` 로 확인), **`/dev/shm` 은 tmpfs** 였다. 환경에 따라 갈린다는 뜻이다.

### 12. 세 JDK 에서 무엇이 달랐나

**출력** (`Ex.java` — 57-g)

```text
===== JDK 17.0.13 =====
java.version : 17.0.13
--- createDirectories 가 돌려주는 Path 는 절대인가 상대인가
  새로 만들 때        : isAbsolute=true  nameCount=10
  이미 있을 때        : isAbsolute=false  nameCount=3
  한 단계만 새로 만들 때: isAbsolute=false  nameCount=2
  createDirectory     : isAbsolute=false  nameCount=2
  인자로 준 것        : sandbox/p/q  (isAbsolute=false)
  r1.equals(인자)     : false

===== JDK 21.0.5 =====
  새로 만들 때        : isAbsolute=false  nameCount=3
  이미 있을 때        : isAbsolute=false  nameCount=3
  한 단계만 새로 만들 때: isAbsolute=false  nameCount=2
  createDirectory     : isAbsolute=false  nameCount=2
  인자로 준 것        : sandbox/p/q  (isAbsolute=false)
  r1.equals(인자)     : true

===== JDK 25.0.1 =====
  (21 과 한 글자도 다르지 않다)
```

**절대인가 상대인가**

| JDK | 여러 단계를 새로 만들 때 |
|---|---|
| 17.0.13 | **절대 경로** (`isAbsolute=true`, `nameCount=10`) |
| 21.0.5 | 상대 경로 (`nameCount=3`) |
| 25.0.1 | 상대 경로 |

**"이미 있을 때"와 "한 단계만"**

- **세 판 모두 상대 경로**다. 17 도 그렇다.
- 즉 **17 에서도 조건에 따라 달라진다.** 같은 메서드가 호출 상황에 따라 절대/상대를 오간다.
- 그래서 **테스트가 두 번째 실행부터 통과한다** — 디렉터리가 이미 있으니까.

**`src.zip` 의 그 한 줄**

```java
// JDK 17.0.13 — java.base/java/nio/file/Files.java, createDirectories
        try {
            dir = dir.toAbsolutePath();      // <- 인자 변수를 덮어쓴다
        } catch (SecurityException x) {
            se = x;
        }
        ...
        return dir;                          // <- 절대 경로가 나간다
```

```java
// JDK 21.0.5 — 같은 메서드
        Path absDir = dir;                   // <- 별도 변수
        try {
            absDir = dir.toAbsolutePath();
        } catch (SecurityException x) {
            se = x;
        }
        ...
        return dir;                          // <- 인자가 그대로 나간다
```

- 바뀐 것은 **`dir =` 이 `absDir =` 이 된 것** 하나다.
- 나머지 본문의 `dir` 도 전부 `absDir` 로 바뀌었고, `return dir` 만 그대로 남았다.

**javadoc 의 `@return`**

- **"the directory"** 라고만 적는다. 절대/상대를 **약속한 적이 없다.**
- 그러니 17 의 동작도 계약 위반이 아니다. **약속하지 않은 것에 기댄 코드가 틀린 것이다.**

**어떻게 다뤄야 하나**

```java
// 안 된다 — 반환값의 형태에 기댄다
Path created = Files.createDirectories(base.resolve("p/q"));
log.info("만듦: " + created);                 // JDK 에 따라 다르게 찍힌다
assertEquals(base.resolve("p/q"), created);    // 17 에서 실패

// 된다 — 인자를 그대로 쓴다
Path target = base.resolve("p/q");
Files.createDirectories(target);
log.info("만듦: " + target);
```

- **반환값을 버리고 인자를 쓴다.** 그러면 JDK 판과 무관하다.

### 13. 어느 것을 고르는가

| 요구 | 고를 것 | 이유 |
|---|---|---|
| 100바이트 설정 파일 | **`Files.readString(p)`** | 짧고 닫을 것이 없다 |
| 크기를 모르는 로그에서 줄 세기 | **`Files.lines(p)` + `try`-with-resources** | 메모리가 파일 크기에 안 묶인다(7번). 닫아야 한다(4번) |
| 남의 디렉터리 훑기(권한 섞임) | **`Files.walkFileTree`** | `visitFileFailed` 로 건너뛴다(10번) |

**`*.log` 만 고르는 두 방법**

```java
// (1) 한 단계만 — glob
try (DirectoryStream<Path> s = Files.newDirectoryStream(dir, "*.log")) {
    for (Path p : s) { ... }
}

// (2) 재귀 — find
try (Stream<Path> s = Files.find(dir, Integer.MAX_VALUE,
                                 (p, a) -> a.isRegularFile() && p.toString().endsWith(".log"))) {
    ...
}
```

- 실측에서 `newDirectoryStream(sandbox/a, "*.txt")` 는 `[sandbox/a/1.txt]` 하나만 냈다 — **한 단계**다.
- `Files.find(box, 10, (p,a) -> p.toString().endsWith(".txt"))` 는 세 개를 냈다 — **재귀**다.
- **둘 다 닫아야 한다.**

**`java.io.File` 의 `delete()`·`mkdirs()` 를 쓰면 안 되는 이유**

```java
if (!file.delete()) {
    // 왜 실패했는지 알 수 없다
    // - 파일이 없어서?
    // - 권한이 없어서?
    // - 디렉터리가 비어 있지 않아서?
    // - 다른 프로세스가 잡고 있어서?
}
```

- **`boolean` 하나만 돌려준다.** 실패 이유가 사라진다.
- `Files.delete` 는 `NoSuchFileException`·`AccessDeniedException`·`DirectoryNotEmptyException` 으로 **이유를 타입으로** 알려준다(8번).
- `mkdirs()` 도 같다 — 이미 있어서 `false` 인지, 권한이 없어서 `false` 인지 구분이 안 된다.
- 이것이 NIO.2 가 `java.io.File` 을 대체한 가장 실용적인 이유다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (57-a) | `Path` 의 칸 분해, 구분자 정리, `resolve`/`relativize`, `normalize` 가 FS 를 안 본다는 것, `equals` 대 `isSameFile` 대 `toRealPath`, `startsWith` 의 이름 단위, 정렬 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (57-b) | 없는 파일·없는 디렉터리의 예외 7종, `createDirectory(ies)`, 인코딩, `DirectoryNotEmptyException`, `copy`/`move`/`ATOMIC_MOVE`(같은 FS·다른 FS), 속성, 임시 파일 | 17 · 21 · 25 (**`createDirectories` 한 줄만 다름 — 12번**) |
| `Ex.java` (57-c) | `Files.lines` 를 안 닫을 때 fd 6→206, 닫으면 증가 0, `System.gc()` 회수, `readAllLines` 는 안 샌다, 최종 연산이 안 닫는다, 닫은 뒤 재사용, 읽는 중 파일 삭제, 예외가 나는 두 자리 | 17 · 21 · 25 (**fd 시작값만 17 이 7, 21·25 가 6**) |
| `Ex.java` (57-d) | 70MB·200만 줄 파일에서 `-Xmx` 별 `readAllLines` 대 `lines`, OOM 스택트레이스 | 17 · 21 · 25 (**줄 번호가 셋 다 다름**) |
| `Ex.java` (57-e) | `walk`/`list`/`find`/`newDirectoryStream` 의 범위, 심볼릭 링크(기본·`FOLLOW_LINKS`), 순환 `FileSystemLoopException`, 끊어진 링크, 권한 없는 디렉터리, `walkFileTree` 콜백, 재귀 삭제 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (57-f) | **`walk` 는 끝까지 소비하면 안 새고, 단락하면 샌다**(100번에 fd +400), `System.gc()` 가 회수 못 한다 | 17 · 21 · 25 (**fd 시작값만 다름**) |
| `Ex.java` (57-g) | **`createDirectories` 반환값이 절대인가 상대인가** — 조건별로 | 17 · 21 · 25 (**★ 17 만 다름**) |
| `src.zip` 열람·diff | `Path` 클래스·`equals` javadoc, `Files.lines`/`walk` 의 apiNote, `readString` 의 `@throws OutOfMemoryError`, `Path.of` 의 `@since 11`, **17 과 21 의 `createDirectories` 소스 diff** | 17 · 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- ★ **`Files.createDirectories` 의 반환 경로** — 17 은 여러 단계를 만들 때 절대 경로, 21·25 는 상대 경로. `src.zip` 에서 원인을 확인했다. **반환값을 쓰지 마라.**
- ★ **`Files.walk` 가 단락 시 새는 fd 개수** — 이 디렉터리 구조에서 호출당 4개. 트리 모양에 따라 다르다.
- **fd 시작값** — 17 은 7, 21·25 는 6. JVM 이 기본으로 여는 것의 수다.
- **OOM 경계 `-Xmx`** — 이 머신·이 파일에서 `readAllLines` 는 128m 실패 / 256m 성공. GC·JDK·파일 내용에 달렸다.
- **OOM 스택트레이스 줄 번호** — `String.java:4501`(17) / `:4768`(21) / `:4842`(25).
- **`AtomicMoveNotSupportedException` 의 메시지 끝** — `부적절한 장치간 연결`. OS 의 `EXDEV` 를 `ko_KR` 로 번역한 것이라 **로케일에 따라 다르다.** 영어 로케일 출력은 **안 돌려 봄.**
- **`readString(디렉터리)` 의 메시지** — `디렉터리입니다`. 같은 이유로 로케일 의존.
- **POSIX 권한 문자열** `rw-rw-r--` · **`probeContentType`** `text/plain` · **`size(디렉터리)`** `4096` — 전부 OS·umask·파일시스템에 달렸다.
- **`/tmp` 와 홈이 같은 파일시스템인지** — 이 머신은 둘 다 ext4 라 같았고, `/dev/shm` 만 tmpfs 였다. 다른 머신에서는 다르다.
- **윈도에서 "읽는 중 파일 삭제"** — POSIX 와 다를 것이다. **안 돌려 봄**(이 머신에 윈도가 없다).
- **`WatchService`·`getPathMatcher("glob:**/*")`·`getFileStore` 비교** — **안 돌려 봄.** 이 문서 범위 밖이다.
