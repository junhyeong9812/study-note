# language/26-pl-symptom-index — 정답

## 정답

### 1. 일곱 증상과 깨진 가정

| 증상 | 깨진 가정 | 절 |
|---|---|---|
| `NoSuchMethodError` | "컴파일 때 본 메서드가 실행 때도 있다" | 1절 |
| `ClassCastException` | "정적 타입이 실제 객체와 맞는다"(소거로 실행 중 검사가 꺼낼 때만) | 2절 |
| `NullPointerException` | "값이 있다", 그리고 "예외 기록은 늘 같은 모양이다" | 3절 |
| `StackOverflowError` | "재귀 깊이는 입력과 무관하게 작다" | 4절 |
| `GC overhead` | "다 쓴 객체는 회수되고 힙은 넉넉하다"(실제로는 산 데이터가 힙을 거의 채웠다 — 누수로 계속 늘었거나, 일정한데 힙이 작다) | 5절 |
| 정규식 CPU 100% | "코드 비용은 입력 모양과 무관하다" | 6절 |
| async 정지 | "기다리는 동안 다른 일이 돈다" | 7절 |

- 첫 질문이 실행체인 이유: 이 영역 증상의 대부분은 컴파일 때 본 세계와 실행 때의 세계가 다를 때 난다. 컴파일한 판과 실행한 판(19), 소스의 검사와 최적화된 기계어(20·22), 데워진 코드와 차가운 코드(01·23), 빌드 때 본 호출 그래프와 실행 때의 리플렉션(24)이다. 어떤 jar·옵션·빌드·몇 번째 실행인지 모르면 표의 행을 고를 수 없다.

### 2. 판을 바꿔 실행한 결과

- money 2.0으로 실행: `1000 KRW`(정상).
- money 1.0으로 실행: `java.lang.NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'`.
- money 없이 실행: `java.lang.NoClassDefFoundError: com/x/Money`, `Caused by: java.lang.ClassNotFoundException: com.x.Money`.
- 문구에서 읽을 것: 메시지가 컴파일 때 기록된 **서술자 전체**(반환 타입·인자 타입)다. 클래스는 있는데 그 서술자의 메서드가 없다는 뜻이므로, "다른 판이 실행 경로에 올라왔다"로 좁힌다. 다음 확인은 `-verbose:class`로 그 클래스가 온 jar, 해석 트리로 누가 그 판을 끌어왔는지다(19-1).

### 3. 실험의 CCE·NPE·SOE

- CCE: `class java.lang.Integer cannot be cast to class java.lang.String (…)`, 맨 위 프레임은 꺼낸 줄(`Symptoms.java:21`).
- NPE: `Cannot invoke "String.length()" because "<local1>" is null` — JEP 358 상세 메시지로 null이었던 식이 보였다.
- SOE: 메시지 `null`, 트레이스 1,024프레임에서 잘림. 단순 재귀 깊이는 6회(집필 3 + 점검 재실행 3) 21,098~21,948로 달랐다. 정규식 SOE의 맨 위 프레임은 실행마다 `GroupTail`·`GroupHead`·`Branch`·`BmpCharProperty` 등으로 바뀌었다.
- 꺼낸 줄을 고치면 안 되는 이유: 제네릭은 소거되어 실행 중 검사가 꺼낼 때의 `checkcast`에만 있다. 정수를 넣은 곳(원시 타입 `List`를 쓰는 다른 모듈)은 트레이스에 없을 수 있다(05 실험 C). 꺼낸 줄을 고치면 다른 집계에서 또 터진다. `Collections.checkedList`로 넣는 순간을 잡는다.

### 4. 스택 없는 NPE

- 원인: HotSpot `OmitStackTraceInFastThrow`(기본 `true`)가 컴파일된 코드에서 자주 나는 내장 예외를 미리 만든 객체로 던진다. 08 실험에서 같은 NPE가 약 5천 번째(5,181~5,272)부터 스택 0줄·메시지 `null`이 됐다.
- 먼저 찾을 것: 기동 직후의 **첫 발생** 로그(그때는 스택과 상세 메시지가 있다). 재현 환경에서는 `-XX:-OmitStackTraceInFastThrow`. 근본적으로는 같은 예외가 수천 번 나는 경로를 고친다(08-4).
- ARM 서버에서만 드물게: 지연 초기화한 싱글턴의 필드가 null·0으로 보이는 `volatile` 없는 DCL(16-3·13-2)을 의심한다. 참조 공개와 생성자 안 쓰기 사이에 happens-before가 없다. x86에서는 안 보일 수 있다.

### 5. `StackOverflowError`의 갈래

| 갈래 | 첫 확인 | leaf |
|---|---|---|
| 깊은 중첩 입력 × 재귀 하강 파서(JSON bomb) | 같은 파서 메서드 반복, 실패 입력의 중첩 깊이 | 03-1 |
| 왼쪽 재귀 문법을 그대로 옮김 | 입력과 무관하게 첫 호출부터 반복, 문법의 왼쪽 재귀 | 03-4 |
| `java.util.regex`의 재귀 매칭 | `Pattern$Branch`·`GroupHead`·`Loop`·`GroupTail.match` 무리 반복, 패턴의 선택 반복과 입력 길이 | 02-2 |

- `-Xss`의 한계: 한계를 옮길 뿐이다. 03 실험에서 `-Xss8m`은 10,000단계를 통과했지만 50,000단계에서 다시 실패했다. 깊이 상한 256을 둔 판은 입력 크기와 무관하게 같은 위치에서 예외로 거부했다. 정규식은 `(a|b)*`를 `[ab]*`로 바꾸자 n=100,000에서도 성공했다(02).

### 6. 수집기를 바꾸자 메시지만 바뀜

- 10 실험 2: 같은 static 컬렉션 누수를 `-Xmx64m`로 돌렸다. Parallel은 `Pause Full (Ergonomics) 61M->61M(63M)`이 연달아 찍히고 28초 중 27초가 STW였으며 `GC overhead limit exceeded`로 죽었다. G1(21.0.12)은 로그에 "GC Overhead Limit exceeded too often"이 찍혔지만 던진 메시지는 `Java heap space`였다.
- 설명: 메시지는 수집기의 판정 방식(Parallel은 GC 시간 98% 초과 + 회수 2% 미만)이고, 이 실험의 원인은 산 데이터 증가(누수)다. 수집기를 바꿔도 누수는 그대로다. 다만 같은 메시지는 누수 없이 힙이 작을 때도 난다(Oracle 문제 해결 가이드) — 그래서 메시지가 아니라 바닥선 추세로 가른다.
- 먼저 볼 지표: Full GC 뒤 힙 바닥선(`→` 오른쪽 값)의 회차별 추세, Full GC 빈도·GC 시간 비율. 바닥선이 오르면 힙 덤프의 지배자 트리로 붙잡는 필드를 찾는다(10-3, reliability/37).

### 7. CPU 100%의 세 갈래

| 보이는 형태 | 원인 | leaf |
|---|---|---|
| 덤프 맨 위가 `Pattern$GroupHead`·`Loop`·`GroupTail.match` 반복, 입력에 같은 글자가 길게 | 백트래킹 정규식(ReDoS) — 실패 입력에서 나눔을 지수·고차 다항만큼 시도 | 02-1 |
| 새 파드에서만 시작 후 1~몇 분, 저절로 가라앉음, `C2 CompilerThread`·`PrintCompilation` 몰림 | JIT 워밍업 전 — 인터프리터·level 3 코드로 트래픽을 받음(23 실험 1: 약 2~20배) | 01-1 · 23-1 |
| 기능 플래그·드문 요청 유형 시점에만 잠깐 | 단형으로 굳은 호출 지점에 새 타입 → 역최적화(`made not entrant`, `class_check`), 재컴파일 전 약 11~17배 | 23-2 |

### 8. 무관한 API까지 느려짐

| 공유 실행 자원 | 첫 확인 | leaf |
|---|---|---|
| 이벤트 루프(node·Netty) — 동기 블로킹·계산 | 코어 하나만 100%, `monitorEventLoopDelay` p99, 루프 스레드 스택 | 14-1 · 15-5 |
| 가상 스레드 캐리어 — `synchronized` 안 블로킹(JDK 21~23) | `-Djdk.tracePinnedThreads`, JFR `jdk.VirtualThreadPinned` | 14-2 |
| ForkJoin 공용 풀 — executor 없는 `supplyAsync`·병렬 스트림의 블로킹 | 덤프의 `ForkJoinPool.commonPool-worker-*`가 전부 소켓 읽기·`park` | 16-2 |

- 증설이 답이 아닌 이유: 요청 수는 같은데 모두 느린 것은 용량이 아니라 **막는 코드** 때문이다. 같은 코드가 새 인스턴스의 루프·풀도 막는다. 16 실험 3처럼 코어 수에 따라 공용 풀 병렬도가 달라, 코어가 많은 서버에서만 정지가 나타날 수도 있다(코어 4개로 보일 때 병렬도 3에서 가벼운 작업 1초 대기, 2개로 보일 때는 병렬도 1이라 `CompletableFuture`가 공용 풀 대신 작업마다 새 스레드를 만들어 1~2ms).

### 9. 사건과의 연결, 「하지 말 것」의 공통점

- 9절(UB): 끝 검사 `==`가 포인터의 끝 건너뛰기를 놓쳐 남의 데이터를 응답에 실은 것은 27의 사건 1(Cloudbleed), 요청이 주장한 길이를 실제 길이와 대조하지 않은 over-read는 사건 2(Heartbleed)다.
- 11절(설치 실패): 락파일은 판을 고정할 뿐 그 판이 남아 있음을 보장하지 않는다 — 사건 3(left-pad)이다.
- 공통점: 왼쪽 항목은 모두 **증상이 보인 자리만 고친다**(꺼낸 줄 캐스트, `-Xss`, 한도 끄기, 증설, 재배포). 원인은 다른 단계(넣은 곳, 입력 깊이, 산 데이터, 막는 코드, 해석 결과)에 있으므로 같은 증상이 다시 난다. 오른쪽은 그 단계로 내려가는 첫 확인이다.
