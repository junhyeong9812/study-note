# java/syntax/57 — `Files`·`Path` — NIO.2 파일 API — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../26-try-with-resources/`](../26-try-with-resources/)와 [`../44-stream-creation/`](../44-stream-creation/)의 질문을 먼저 푼다. 4~6번이 그 둘이 만나는 자리다.
> 예측형 문항의 출력은 **Temurin JDK 21.0.5 · Linux · ext4** 기준이다. 세 판에서 갈린 것은 12번이 따로 묻는다.
> 모든 실험은 임시 디렉터리 안의 `sandbox/` 아래에서 했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Path` 는 문자열과 무엇이 다른가 (예측)

```java
Path p = Path.of("sandbox/data/2026/report.csv");
p.getNameCount();  p.getFileName();  p.getParent();  p.getRoot();  p.subpath(1, 3);
Path.of("sandbox//data///report.csv");
Path.of("sandbox/data/").getNameCount();
"sandbox/data/" + "/report.csv";
```

- 앞 다섯 줄의 결과는 각각 무엇인가?
- `getRoot()` 가 `null` 인 이유는 무엇인가?
- 중복 구분자를 넣은 `Path.of` 는 무엇을 돌려주는가?
- 끝에 구분자가 있는 경로의 `getNameCount()` 는 무엇인가?
- 문자열 연결로 같은 일을 하면 무엇이 달라지는가?

### 2. `resolve` 와 `relativize` (예측)

```java
Path base = Path.of("sandbox/data");
base.resolve("a.txt");
base.resolve("/etc/passwd");
base.resolve("");
base.resolveSibling("b.txt");
Path.of("sandbox").relativize(Path.of("sandbox/data/a.txt"));
Path.of("sandbox/data/a.txt").relativize(Path.of("sandbox"));
```

- 여섯 줄의 결과는 각각 무엇인가?
- 절대 경로를 `resolve` 하면 왜 그렇게 되는가?
- 업로드 파일명을 그대로 `resolve` 하면 무엇이 위험한가?
- 그 위험을 막는 검사는 무엇인가?
- `String.startsWith` 로 그 검사를 하면 어떤 입력에서 뚫리는가?

### 3. `normalize` 는 어디까지 하는가 (경계)

```java
Path.of("sandbox/data/../logs/./app.log").normalize();
Path.of("없는폴더/../also없음/x").normalize();
Path.of("sandbox/없는파일.txt").toRealPath();
Path a = Path.of("sandbox/data/a.txt");
Path b = Path.of("./sandbox/data/a.txt");
a.equals(b);
a.toAbsolutePath().equals(b.toAbsolutePath());
a.toRealPath().equals(b.toRealPath());
Files.isSameFile(a, b);
```

- 앞 세 줄의 결과는 각각 무엇인가?
- 존재하지 않는 경로도 `normalize` 가 되는 이유는 무엇인가?
- `a.equals(b)` 는 무엇이며, javadoc 은 이 메서드에 대해 뭐라고 적는가?
- `toAbsolutePath()` 로 맞춰도 `equals` 가 `false` 인 이유는 무엇인가?
- `Files.isSameFile(a, "sandbox/logs/../data/a.txt")` 를 `sandbox/logs` 가 없는 상태에서 부르면 무엇이 일어나는가?

### 4. `Files.lines` 를 안 닫으면 (예측)

```java
for (int i = 0; i < 200; i++) {
    total += Files.lines(box.resolve("f" + (i % 5) + ".txt")).count();   // 닫지 않는다
}
```

- 예외가 나는가?
- 결과(줄 수)는 정확한가?
- 실행 전후로 열린 fd 수는 어떻게 변하는가?
- 같은 일을 `try`-with-resources 로 하면 fd 가 얼마나 늘어나는가?
- 이 코드가 운영에서 터질 때의 증상은 무엇인가?

### 5. `Files.walk` 는 언제 새는가 (예측)

```java
// (A)
for (int i = 0; i < 100; i++) Files.walk(box).count();
// (B)
for (int i = 0; i < 100; i++) Files.walk(box).filter(Files::isRegularFile).findFirst();
```

- (A)와 (B) 중 fd 가 느는 것은 어느 것인가?
- 느는 쪽은 얼마나 느는가?
- 왜 한쪽만 새는가?
- `System.gc()` 를 부르면 회수되는가 — `Files.lines` 쪽과 같은가?
- javadoc 은 `walk` 에 대해 뭐라고 요구하는가?

### 6. 최종 연산이 파일을 닫는가 (예측)

```java
Stream<String> s1 = Files.lines(box.resolve("f0.txt"));
// fd ?
s1.count();
// fd ?
s1.close();
// fd ?
s1.count();   // ?
```

- 세 지점의 fd 는 각각 어떻게 변하는가?
- `count()` 뒤에 fd 가 줄지 않는 이유는 무엇인가?
- 닫은 뒤 `count()` 를 다시 부르면 무엇이 던져지고 메시지는 무엇인가?
- 그 메시지는 어느 주제에서 본 것과 같은가?
- 닫은 스트림에 `toList()` 를 부르면 어떻게 되는가?

### 7. `readAllLines` 대 `lines` — 메모리 (예측)

70MB(72,888,896바이트)·200만 줄 파일에서 끝자리가 `7`인 줄을 센다.

```java
Files.readAllLines(big).stream().filter(l -> l.endsWith("7")).count();
try (Stream<String> s = Files.lines(big)) { s.filter(l -> l.endsWith("7")).count(); }
```

- `-Xmx64m` 에서 두 줄은 각각 어떻게 되는가?
- `readAllLines` 가 성공하기 시작하는 `-Xmx` 는 얼마인가?
- `lines` 는 최소 얼마에서 돌았는가?
- OOM 스택트레이스의 마지막 JDK 프레임은 무엇인가?
- 이 경계 수치는 보장인가?

### 8. 없는 파일·없는 디렉터리 (경계)

```java
Files.readString(box.resolve("없음.txt"));
Files.delete(box.resolve("없음.txt"));
Files.deleteIfExists(box.resolve("없음.txt"));
Files.writeString(box.resolve("없는디렉터리/x.txt"), "hi");
Files.createDirectory(box.resolve("p/q"));
Files.createDirectories(box.resolve("p/q"));
Files.createDirectory(box.resolve("p/q"));      // 이미 있을 때
Files.delete(box.resolve("p"));                 // 비어 있지 않을 때
```

- 여덟 줄에서 던져지는 예외의 **타입과 메시지**를 각각 말하라.
- `delete` 와 `deleteIfExists` 는 어떻게 다른가?
- `createDirectory` 와 `createDirectories` 는 어떻게 다른가?
- `createDirectories` 를 두 번 불러도 되는가?
- 디렉터리를 통째로 지우려면 어떻게 하는가?

### 9. 심볼릭 링크와 `walk` (예측)

```java
Files.createSymbolicLink(box.resolve("link-to-a"), Path.of("a"));
Files.walk(box);                              // (A)
Files.walk(box, FileVisitOption.FOLLOW_LINKS); // (B)
Files.createSymbolicLink(box.resolve("a/b/loop"), Path.of("../.."));
Files.walk(box, FileVisitOption.FOLLOW_LINKS); // (C)
```

- (A)의 결과에 `link-to-a` 가 들어 있는가, 그 아래 내용은 어떤가?
- (B)는 (A)와 원소 수가 어떻게 다른가?
- (C)는 무엇을 던지며, 감싸는 예외 타입은 무엇인가?
- `Files.isDirectory(link)` 는 기본으로 무엇을 돌려주고, `NOFOLLOW_LINKS` 를 주면 무엇인가?
- 끊어진 링크에서 `exists()`·`exists(NOFOLLOW)`·`notExists()` 는 각각 무엇인가?

### 10. 권한 없는 디렉터리를 만나면 (예측)

```java
Files.setPosixFilePermissions(locked, PosixFilePermissions.fromString("---------"));
Files.walk(box).count();                          // (A)
Files.list(locked).count();                       // (B)
Files.walkFileTree(box, new SimpleFileVisitor<>() {
    public FileVisitResult visitFileFailed(Path p, IOException e) { return FileVisitResult.CONTINUE; }
});                                               // (C)
```

- (A)는 무엇을 던지는가 — 감싸는 예외 타입까지?
- (B)는 무엇을 던지는가, (A)와 무엇이 다른가?
- (C)는 어떻게 되는가?
- `catch (IOException e)` 로 (A)를 잡을 수 있는가?
- 부분 실패를 허용해야 하면 무엇을 쓰는가?

### 11. 원자적 이동 (예측)

```java
Files.move(src, dstSameFs, StandardCopyOption.ATOMIC_MOVE);   // ext4 -> ext4
Files.move(src, dstOtherFs, StandardCopyOption.ATOMIC_MOVE);  // ext4 -> tmpfs
Files.move(src, dstOtherFs);                                  // 옵션 없이
Files.copy(src, existingDst);                                 // 옵션 없이
```

- 네 줄 중 실패하는 것은 무엇이고, 예외 타입은 무엇인가?
- 그 예외 메시지의 마지막 조각은 무엇이며, 그것은 보장인가?
- 옵션 없이 다른 파일시스템으로 `move` 하면 성공하는가, 그러면 무엇을 잃는가?
- "쓰다 만 파일이 보이면 안 된다"는 요구를 만족시키는 관용구를 써라.
- 그 관용구에서 임시 파일을 **어디에** 만들어야 하는가, 왜인가?

### 12. 세 JDK 에서 무엇이 달랐나 (경계)

```java
Files.createDirectories(Path.of("sandbox/p/q"));   // 여러 단계를 새로 만들 때
```

- 17·21·25 에서 이 호출의 반환값은 각각 절대 경로인가 상대 경로인가?
- "이미 있을 때"와 "한 단계만 새로 만들 때"는 어떤가?
- `src.zip` 에서 그 차이의 원인이 되는 코드 한 줄은 무엇인가?
- javadoc 의 `@return` 은 무엇을 약속하는가?
- 그래서 이 반환값을 어떻게 다뤄야 하는가?

### 13. 어느 것을 고르는가 (연결)

- 100바이트짜리 설정 파일을 읽는다 — 무엇을 쓰는가?
- 크기를 모르는 로그 파일에서 조건에 맞는 줄을 센다 — 무엇을 쓰는가?
- 디렉터리에서 `*.log` 만 고른다 — 방법을 둘 대라.
- 남이 만든 디렉터리를 훑는데 권한 없는 곳이 섞여 있다 — 무엇을 쓰는가?
- `java.io.File` 의 `delete()`·`mkdirs()` 를 쓰면 안 되는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
