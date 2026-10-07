# language/26-pl-symptom-index — 증상 사전: NoSuchMethodError·ClassCastException·NullPointerException·StackOverflowError·GC overhead·정규식 CPU 100%·async 정지 → 언어·런타임 원인·확인 명령·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **원리에서 증상으로** 간다.\
"Java 제네릭은 소거되므로 원시 타입으로 넣은 정수가 `List<String>` 안에 들어갈 수 있고, 꺼낼 때 `checkcast`에서 터진다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 로그 한 줄이다. "`java.lang.NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'`", "`StackOverflowError`", "CPU 한 코어 100%", "모든 API가 동시에 느려짐".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                  이 노트 (역방향)
  원리 --> 깨지는 조건 --> 보이는 증상                  증상 --> 보이는 형태 --> 원인 후보 --> 확인 방법 --> leaf
  "제네릭은 소거된다"                                  "CCE가 꺼낸 줄을 가리킨다. 넣은 쪽을 먼저 찾는다"
```

쉬운 예: 병원 응급실의 분류(triage)다.\
"가슴이 아프다"는 한 증상에 원인이 여럿이다(근육, 위산 역류, 심장).\
의사는 증상 → 활력 징후 → 검사 순서로 좁힌다. 증상 하나만 보고 수술하지 않는다.

똑같은 구조다.\
"`StackOverflowError`"라는 한 줄에 원인이 여럿이다.
- 깊게 중첩된 JSON을 재귀 하강 파서가 읽었다([03-1](../03-parsing-grammars-ast/2-summary.md)).
- 왼쪽 재귀 문법을 그대로 옮겨 입력을 소비하지 않고 자기를 불렀다([03-4](../03-parsing-grammars-ast/2-summary.md)).
- `java.util.regex`가 긴 입력에서 `(a|b)*`를 재귀로 돌렸다([02-2](../02-lexing-and-regular-languages/2-summary.md)).

처방이 셋 다 다르다. 깊이 상한, 문법 고치기, 문자 클래스로 바꾸기다. 그래서 원인을 고르기 전에 **보이는 형태**(예외 문구·스택 맨 위 프레임·지표)와 **조건**(어느 입력, 어느 JVM 옵션, 어느 빌드)을 먼저 모은다.

실무 예:
- 언어·런타임 증상의 대부분은 **"컴파일할 때 본 세계"와 "실행할 때의 세계"가 다를 때** 보인다. 컴파일한 판과 실행한 판(19), 정적 타입과 실제 객체(05), 소스의 검사와 최적화된 기계어(20·22), 데워진 코드와 차가운 코드(01·23), 빌드 때 본 호출 그래프와 실행 때의 리플렉션(24)이 그 짝이다.
- 그래서 첫 질문은 "그 줄을 실행한 것이 정확히 무엇이었나"다. 어떤 jar, 어떤 JVM 옵션, 어떤 빌드 플래그, 몇 번째 실행인가.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `NN-k`*: 이 영역 NN번 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `19-1` = [19-modules-and-dependency-resolution](../19-modules-and-dependency-resolution/2-summary.md)의 시나리오 1(다이아몬드 의존 → `NoSuchMethodError`).
  - *첫 확인*: 고치기 전에 원인 후보를 가르는 가장 싼 확인 한 가지.
  - *맨 위 프레임*: 스택 트레이스의 첫 `at` 줄. 예외가 **난 곳**이지 원인이 **생긴 곳**은 아닐 수 있다(2절 CCE가 대표 예).

## 동작·원리

### 0. 증상은 어느 단계의 가정이 깨진 것인가

```text
   증상                                    깨진 가정                                   단계(노트)                   이 노트의 절
   ────                                    ────────                                   ────────                    ─────────
   NoSuchMethodError·NoClassDefFoundError   "컴파일 때 본 클래스·메서드가 실행 때도 있다"     링크·로딩(19,01,24)            1절
   ClassCastException·ArrayStoreException  "정적 타입이 실제 객체와 맞는다"                타입(05,17,06)                2절
   NullPointerException·조용한 실패          "값이 있다 / 실패는 드러난다"                   값·오류 모델(08,16,13,06,18)   3절
   StackOverflowError·RecursionError       "재귀 깊이는 입력과 무관하게 작다"               파싱·정규식(03,02)            4절
   GC overhead·OOM·GC 멈춤                  "다 쓴 객체는 회수되고 힙은 넉넉하다"             메모리(09~12,07,14,16)        5절
   정규식 CPU 100%·배포 직후 느림·처리량 바닥  "코드 비용은 입력·실행 횟수와 무관하다"           정규식·JIT·디스패치(02,01,23,17,22,25)  6절
   async 정지·전체 지연                       "기다리는 동안 다른 일이 돈다"                  동시성 모델(14,15,16,13,22)   7절
   집계가 매번 다름·남의 컨텍스트              "공유 상태 갱신은 원자적이고 격리된다"            메모리 모델·패턴(07,04,15,18,13,16)  8절
   디버그에선 맞고 릴리스에서만 틀림            "소스에 쓴 검사·순서가 기계어에 남는다"           UB·최적화(20,22,05,21)        9절
   값이 엉뚱한데 예외 없음                    "이름·문법·바인딩이 내가 읽은 대로 해석된다"       어휘·구문·스코프(02,03,04,07,24)  10절
   설치·재빌드 실패, 두 사본                   "그 판이 그대로 있고, 하나뿐이다"                의존성 해석(19)               11절
```

- 커리큘럼 26번 행의 일곱 증상(`NoSuchMethodError`·`ClassCastException`·`NullPointerException`·`StackOverflowError`·`GC overhead`·정규식 CPU 100%·async 정지)이 1·2·3·4·5·6·7절의 머리다. 8~11절은 01~25 leaf 시나리오의 나머지 증상이다.
- 다른 영역 색인과 겹치는 곳: 종료 코드·errno는 [os/37](../../os/37-os-symptom-index/2-summary.md), 지연·스레드 고갈·재시도 같은 운영 증상은 [reliability/52](../../reliability/52-reliability-symptom-index/2-summary.md), 정규식·재귀의 복잡도 쪽은 [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) 3·4절, 신호(`SIGSEGV`)와 정수 표현은 [architecture/22](../../architecture/22-arch-symptom-index/2-summary.md), 공격 관점은 [security/29](../../security/29-security-symptom-index/2-summary.md)가 정본이다. 이 노트는 그 증상의 **언어·런타임 원인**을 맡는다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 원문       예외 전체(클래스·메시지·Caused by), 스택 맨 위 프레임, 같은 예외의 "첫 발생" 로그
  ② 실행체     JVM 판·옵션(jcmd VM.flags), 클래스가 온 jar(-verbose:class), 빌드 플래그(-O0/-O2, -g, LTO/PGO)
  ③ 시점       기동 직후인가 / 몇 분 뒤인가 / 며칠 뒤인가, 배포·기능 플래그 직후인가
  ④ 조건       입력 크기·중첩 깊이, 동시 요청 수, CPU 한도(--cpus), 힙 한도
```

- ①의 "첫 발생"이 중요한 이유: HotSpot은 자주 나는 내장 예외의 스택을 어느 순간부터 생략한다. 08 실험에서 같은 NPE가 약 5천 번째부터 스택 0줄·메시지 `null`이 됐다([08-4](../08-error-handling-models/2-summary.md)).
- ③의 시점이 원인을 크게 가른다. 기동 직후는 JIT 워밍업(01-1·23-1), 몇 분~몇 시간 뒤의 계단은 역최적화·할당(23-2·12-2), 며칠 뒤는 누수·코드 캐시(10-3·23-3)를 먼저 본다.

### 1. 실행 중 클래스·메서드를 못 찾는다 — `NoSuchMethodError`·`NoClassDefFoundError`·`ClassNotFoundException`

먼저 **어느 단계 오류인지**를 이름으로 가른다. 컴파일 오류(`cannot find symbol`)가 아니라 실행 중 오류라면, 컴파일러는 그 메서드를 봤다는 뜻이다.

```text
  실행 중 "없다"
     │
     ├─ NoSuchMethodError: '<반환 타입> <클래스>.<메서드>(<인자들>)' ───────▶ 컴파일한 판 ≠ 실행한 판(다이아몬드)      19-1
     ├─ NoClassDefFoundError: com/x/Money / Caused by: ClassNotFoundException ─▶ 실행 경로에 jar 없음(스코프·셰이딩)    19-2
     ├─ 등록했는데 "등록 안 됨"·instanceof false (예외 없음) ───────────────▶ 같은 패키지 두 사본                    19-5
     ├─ 네이티브 이미지에서만 ClassNotFoundException·NoSuchMethodException ──▶ 닫힌 세계 — 리플렉션 대상이 빠졌거나 등록 없음  24-1 · 01-2
     │   또는 MissingReflectionRegistrationError
     ├─ 네이티브에서 프로필·조건부 빈이 안 바뀜 ──────────────────────────▶ 빈 구성이 빌드 때 굳음                  24-5
     └─ AOT 캐시를 붙였는데 시작 시간이 그대로 ───────────────────────────▶ 훈련 때와 클래스패스·JDK가 다름(경고만)    24-6
```

| 보이는 것 (예외·로그·지표) | 원인 후보 (언어·런타임) | 첫 확인 (명령·플래그) | leaf |
|---|---|---|---|
| `java.lang.NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'`, 기동·테스트는 통과, 그 기능을 처음 쓸 때 500, 스택 맨 위가 라이브러리 내부 | 호출 지점은 컴파일 때 본 **서술자**(이름 + 인자·반환 타입)로 실행 때 메서드를 다시 찾는다. 실행 경로에 낮은 판이 올라왔다(Maven "가까운 쪽" 규칙, 클래스패스 앞의 jar가 이김). 19 실험에서 두 판을 다 올려도 먼저 나온 jar 하나만 쓰였다 | `java -verbose:class … \| grep Money`(어느 jar에서 왔나), `javap -c`로 호출 지점의 서술자, `mvn dependency:tree -Dincludes=…`·`gradle dependencyInsight` | [19-1](../19-modules-and-dependency-resolution/2-summary.md) |
| `java.lang.NoClassDefFoundError: com/x/Money` + `Caused by: java.lang.ClassNotFoundException: com.x.Money`, IDE에서는 됨 | 컴파일 경로에는 있고 실행 경로에는 없음(`provided`·`compileOnly`, 셰이딩 누락) | 패키징 결과 `jar tf`에 그 클래스가 있나 | [19-2](../19-modules-and-dependency-resolution/2-summary.md) |
| 예외 없음. 설정을 등록했는데 다른 모듈은 "없음", `instanceof`가 false, `npm ls <pkg>`에 같은 이름이 두 경로 | 범위가 겹치지 않아 중첩 설치 → 모듈 객체가 둘(19 실험 2 `same module object? false`) | `npm ls <pkg>` | [19-5](../19-modules-and-dependency-resolution/2-summary.md) |
| JVM에서는 통과, 네이티브 바이너리에서만 `ClassNotFoundException`·`NoSuchMethodException`·`MissingReflectionRegistrationError` | AOT 빌더는 빌드 때 보이는 호출 그래프만 넣는다. 이름이 설정·DB·요청에서 오는 리플렉션은 그래프에 안 보인다. 클래스가 다른 경로로 들어가 있어도 리플렉션 등록이 없으면 조회가 실패한다 | 실패한 클래스 이름이 문자열에서 오나, `reachability-metadata.json`에 있나 | [24-1](../24-aot-native-image-and-startup/2-summary.md) · [01-2](../01-compile-interpret-jit/2-summary.md) |
| 네이티브 이미지에 `--spring.profiles.active=prod`를 줬는데 dev 빈 구성 | 닫힌 세계에서는 빈 정의가 실행 중 바뀔 수 없다(Spring Boot 문서) | `@ConditionalOnProperty`·프로필별 빈이 있나 | [24-5](../24-aot-native-image-and-startup/2-summary.md) |
| AOT 캐시(JDK 24+, JEP 483)·CDS를 붙였는데 시작 시간이 그대로, 오류 없음 | JDK 판·클래스패스·모듈 옵션이 훈련 때와 다름. JEP 483: 못 쓰면 경고만 내고 계속 실행 | 배포 전 검증에서 `-XX:AOTMode=on`으로 실패하게, `-Xlog:class+load`의 아카이브 출처 수 | [24-6](../24-aot-native-image-and-startup/2-summary.md) |

- 처방의 방향: 판을 하나로 묶는다(`dependencyManagement`·BOM, Gradle 제약, npm `overrides`). 한 판으로 못 맞추면 셰이딩으로 격리한다. 네이티브는 리플렉션을 상수 인자·명시 분기로 바꾸고, 그 경로를 네이티브 통합 테스트에 넣는다.

### 2. 타입이 실제 객체와 맞지 않는다 — `ClassCastException`·`ArrayStoreException`·`TypeError`

먼저 **스택 맨 위 프레임이 "넣은 곳"인지 "꺼낸 곳"인지**를 본다. 제네릭 소거 때문에 Java의 CCE는 대개 꺼낸 곳에서 난다.

```text
  타입 예외 / 엉뚱한 메서드
     │
     ├─ ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String ─▶ 원시 타입으로 오염 + 소거, 꺼낼 때 checkcast   05-1
     ├─ instanceof List<String> 컴파일 안 됨, 역직렬화가 원소 타입을 잃음 ───────────────────▶ 소거 — 실행 중 타입 인자 없음                05-2
     ├─ ArrayStoreException: java.lang.Integer ──────────────────────────────────────────▶ 공변 배열, 저장 순간 검사                    05-3
     ├─ Python TypeError·AttributeError, 몇 주에 한 번 ──────────────────────────────────▶ 동적 검사는 그 줄이 실행될 때만              05-5
     ├─ Set에 같은 원소가 여러 번 (예외 없음) ─────────────────────────────────────────────▶ equals(UserId) = 오버로드, 재정의 아님         17-1
     ├─ List<Integer>.remove(1)이 값이 아니라 인덱스를 지움 ───────────────────────────────▶ 오버로드 해석 1단계(박싱 없이)가 remove(int)   17-2
     ├─ 같은 ID인데 == 가 false, 128 이상에서만 ──────────────────────────────────────────▶ 박싱 객체 동일성 비교(-128~127 캐시)          06-3
     └─ 64비트 ID 끝자리가 바뀜(JS) ─────────────────────────────────────────────────────▶ Number는 2^53 넘는 정수를 정확히 못 담음      21-2
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (…)`, 스택은 `for (String s : names)` 같은 꺼내는 줄 | 오래된 모듈이 원시 타입 `List`로 정수를 넣었다. 컴파일러는 unchecked 경고만, 실행 중 검사는 꺼낼 때의 `checkcast`(05 실험 C의 `javap -c`) | 넣는 쪽 찾기: 임시로 `Collections.checkedList`로 감싸면 그 뷰를 거쳐 **넣는 순간** CCE와 그 줄이 나온다(원래 리스트 참조로 넣는 경로·감싸기 전 원소는 검사 안 함). `-Xlint:unchecked` 경고 목록 | [05-1](../05-type-systems/2-summary.md) |
| `new T[]`·`T.class` 불가, 역직렬화 결과가 맵의 리스트 | JLS 4.6·4.7 — 소거된 매개변수화 타입은 실행 중 구별할 수 없다 | 타입 토큰(`Class<T>`)을 넘기고 있나 | [05-2](../05-type-systems/2-summary.md) |
| `java.lang.ArrayStoreException: java.lang.Integer` | `Object[]`로 받은 것이 실제로는 `String[]`. 배열은 공변이라 컴파일은 통과, JVM이 저장 순간 검사(JLS 10.5) | 호출자가 넘긴 배열의 실제 클래스 | [05-3](../05-type-systems/2-summary.md) |
| Python `TypeError`·`AttributeError`가 드문 요청에서만 | 동적 타입 검사는 실행된 줄만 본다. 테스트가 그 분기를 안 지남 | 그 분기의 테스트 커버리지, 정적 검사기 | [05-5](../05-type-systems/2-summary.md) |
| `ids.contains(probe)`가 false, `probe.equals(copy)`는 true(17 실험 A) | `equals(UserId)`는 `Object.equals(Object)`의 재정의가 아니라 새 오버로드. 오버로드는 컴파일 시점, 재정의는 실행 시점에 고른다 | `@Override`가 붙어 있나, 서명이 `Object`인가 | [17-1](../17-dispatch-and-polymorphism-mechanics/2-summary.md) |
| `remove(1)` 뒤 다른 원소가 사라짐, `javap`에 `List.remove:(I)` | JLS 15.12.2 1단계(박싱 없이 적용 가능)에서 `remove(int index)` 선택 | `javap -c`의 서술자 `(I)` vs `(Ljava/lang/Object;)` | [17-2](../17-dispatch-and-polymorphism-mechanics/2-summary.md) |
| `order.getUserId() == user.getId()`가 신규 사용자에게만 false(작은 ID는 통과) | 두 `Long`의 `==`는 동일성 비교. -128~127은 `Long.valueOf`·`Integer.valueOf` API 문서가 항상 캐시하는 범위라 같은 객체였고 우연히 맞음(JLS 5.1.7은 상수 식 박싱만 요구) | 실패하는 ID가 128 이상인가 | [06-3](../06-values-references-passing/2-summary.md) |
| 서버 로그 ID와 프런트 ID가 끝자리만 다름(`MAX_SAFE_INTEGER + 2` → `…992`, 21 실험 1) | JS `Number`는 2^53 − 1을 넘는 정수를 정확히 담는다는 보장이 없음. `JSON.parse`도 `Number`로 만든다 | ID가 JS `Number`를 거치나 | [21-2](../21-language-choice-tradeoffs/2-summary.md) |

- 처방의 방향: unchecked 경고를 0으로(CI `-Werror`), 공용 API는 배열 대신 `List<? super T>`, `@Override` 필수 규칙, 박싱 타입 비교는 `Objects.equals`, 큰 ID는 JSON에서 문자열.

### 3. `NullPointerException`과 "예외가 없는" 실패

NPE는 **문구로 두 갈래**다. JEP 358의 상세 메시지(`Cannot invoke "String.length()" because "<local1>" is null`)가 있으면 어느 식이 null이었는지 바로 보인다. 메시지 `null`·스택 0줄이면 HotSpot이 스택을 생략한 뒤다.

```text
  NPE / 값이 이상한데 예외가 없음
     │
     ├─ NPE 한 줄만 수천 개, 스택 0줄, 메시지 null ──────────────────────▶ OmitStackTraceInFastThrow(기본 켜짐)        08-4
     ├─ 지연 초기화한 싱글턴 필드가 드물게 null·0, ARM에서만 ──────────────▶ volatile 없는 DCL — 반쯤 생성된 객체       16-3 · 13-2
     ├─ 데이터가 빠졌는데 로그·알람 없음 ─────────────────────────────────▶ 삼킨 예외 catch {}                       08-1
     ├─ 실패가 성공 코드로 반환 ──────────────────────────────────────────▶ finally 안 return                        08-2
     ├─ "12a"가 0 또는 12로 저장 ─────────────────────────────────────────▶ 버린 에러 반환값(Go _ , C atoi)           08-3 · 21-3
     ├─ "저장했습니다"인데 데이터 없음, exit 0 ─────────────────────────────▶ CompletableFuture 예외를 아무도 안 꺼냄    16-5
     ├─ 감사 로그가 일부 API에서만 비어 있음 ──────────────────────────────▶ map 안 부수효과 + count()가 파이프라인 생략  18-2
     ├─ 두 번째 표가 매일 빈 목록 ────────────────────────────────────────▶ 다 쓴 제너레이터 재사용                   18-4
     ├─ IllegalStateException: stream has already been operated upon … ─▶ 지연 스트림 두 번 소비                     18-1
     └─ IllegalStateException: source already consumed or closed ───────▶ 지연 스트림이 자원보다 오래 삶             18-5
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `java.lang.NullPointerException`만 수천 줄, 스택 트레이스 0줄, 메시지 `null` | `OmitStackTraceInFastThrow`(OpenJDK 21 `globals.hpp`, 기본 `true`)가 컴파일된 코드의 자주 나는 내장 예외를 미리 만든 객체로 던짐. 08 실험: 약 5천 번째부터(5,181~5,272) | 기동 직후의 **첫 발생** 로그, 재현 환경에서 `-XX:-OmitStackTraceInFastThrow` | [08-4](../08-error-handling-models/2-summary.md) |
| 기본값 때문의 NPE·잘못된 포트·타임아웃 0, 재현이 거의 안 됨, x86 개발 PC에서는 안 남 | 참조 공개와 생성자 안 쓰기 사이에 happens-before가 없음 | 싱글턴 생성 코드에 `volatile`·`final`·holder 관용구가 있나 | [16-3](../16-concurrency-design-patterns/2-summary.md) · [13-2](../13-language-memory-model/2-summary.md) |
| 정산 데이터 일부 누락, 처리 건수 지표만 조금 낮음, 로그 없음 | 검사 예외를 `catch (IOException e) {}`로 막음 | 빈 catch 정적 검사, 처리 건수 vs 입력 건수 | [08-1](../08-error-handling-models/2-summary.md) |
| 결제 실패가 성공 코드(1)로 반환, 예외 로그 없음 | JLS 14.20.2 — `finally`가 급종료하면 `try`의 예외는 "discarded and forgotten" | `javac -Xlint:finally`(기본으로 안 켜짐) | [08-2](../08-error-handling-models/2-summary.md) |
| 입력 `"12a"`가 수량 0(Go) 또는 12(C)로 저장 | Go `n, _ := Atoi(…)`로 에러를 버림, C `atoi`는 실패를 알릴 수 없음 | `_`로 버린 err 검색(errcheck류), `atoi` 사용처 | [08-3](../08-error-handling-models/2-summary.md) · [21-3](../21-language-choice-tradeoffs/2-summary.md) |
| "저장했습니다" 응답, 데이터 없음, 로그 없음, 프로세스 exit 0 | 예외가 `Future` 안에 담긴 채 아무도 `get`·`join`·`whenComplete`로 꺼내지 않음 | 사슬 끝에 `whenComplete`·`exceptionally`가 있나 | [16-5](../16-concurrency-design-patterns/2-summary.md) |
| 같은 `map(o -> { audit(o); return o; })`인데 일부 API만 감사 로그 없음 | `count()`가 원본 크기로 답을 내 파이프라인을 돌리지 않음(`Stream.count` API Note), 앞에 `filter`가 있으면 돎 | 중간 연산 안에 부수효과가 있나 | [18-2](../18-functional-concepts/2-summary.md) |
| 두 번째 표가 `[]`, 에러 없음(Python) | 제너레이터를 첫 소비에서 다 씀. 다시 돌리면 예외 없이 빈 반복 | 반환 타입이 제너레이터인가 | [18-4](../18-functional-concepts/2-summary.md) |
| `java.lang.IllegalStateException: stream has already been operated upon or closed` | 한 `Stream`을 개수와 목록에 두 번 씀 | 같은 스트림 변수의 최종 연산이 둘인가 | [18-1](../18-functional-concepts/2-summary.md) |
| 호출자에서 `IllegalStateException: source already consumed or closed` | try-with-resources 안에서 `Files.lines(...)`의 지연 스트림만 반환 | 자원 블록 밖에서 소비하나 | [18-5](../18-functional-concepts/2-summary.md) |

- 처방의 방향: 첫 발생 로그를 남기는 로그 설정, 빈 catch·`finally` 안 `return` 금지 규칙, 비동기 사슬마다 실패 처리 단계, 스트림·제너레이터는 한 번 실체화(`toList()`·`list(gen)`).
- "예외가 없는 실패"는 이 색인에서 가장 늦게 발견되는 무리다. 지표(처리 건수, 기본값 비율)로 먼저 잡는다.

### 4. 스택이 넘친다 — `StackOverflowError`·`RecursionError`·`RangeError`

먼저 **반복되는 프레임**을 본다. 트레이스는 `MaxJavaStackTraceDepth` 기본 1,024프레임에서 잘리므로, 아래쪽 원인 프레임은 안 보일 수 있다. 반복되는 메서드 이름이 원인 갈래를 고른다.

```text
  StackOverflowError (또는 다른 언어의 재귀 한도)
     │
     ├─ 같은 파서 메서드가 반복, 요청 크기는 작음(수십 KB) ──────────────▶ 깊은 중첩 입력 × 재귀 하강(JSON bomb)    03-1
     ├─ 어떤 입력이든 첫 호출부터 같은 함수 반복 ─────────────────────────▶ 왼쪽 재귀 문법을 그대로 옮김             03-4
     ├─ Pattern$Branch·GroupHead·Loop·GroupTail.match 반복, 긴 입력 ────▶ java.util.regex의 재귀 매칭             02-2
     └─ Python RecursionError … while decoding a JSON array ────────────▶ 같은 원리, 다른 한도(CPython C 재귀 한도)  03-1
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `java.lang.StackOverflowError`, 같은 파서 메서드 반복. Jackson 2.15+면 `StreamConstraintsException`(메시지는 판마다 다름 — 2.17은 `Document nesting depth …`) | 재귀 하강은 중첩 한 겹마다 프레임 하나. 03 실험: 기본 스택에서 5,000단계 `StackOverflowError`, `-Xss8m`도 50,000에서 실패, 깊이 상한 256은 같은 위치에서 거부 | 실패 입력의 중첩 깊이, 파서의 깊이 상한 설정 | [03-1](../03-parsing-grammars-ast/2-summary.md) |
| Python `RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string` | CPython `_json.c`는 `sys.getrecursionlimit()`(1000)과 별개의 C 재귀 한도를 씀. 03 실험: 9,997까지 ok | 실패 입력의 중첩 깊이 | [03-1](../03-parsing-grammars-ast/2-summary.md) |
| 시작하자마자 `StackOverflowError`, 입력과 무관 | `expr ::= expr '-' term`을 그대로 함수로 → 입력 소비 없이 자기 호출 | 문법에 왼쪽 재귀가 있나 | [03-4](../03-parsing-grammars-ast/2-summary.md) |
| `StackOverflowError`, 프레임이 `Pattern$Branch.match`·`Pattern$GroupHead.match`·`Pattern$Loop.match`·`Pattern$GroupTail.match` | `java.util.regex`는 `(a\|b)*` 같은 그룹 반복에서 반복 한 번마다 프레임을 씀(문자 클래스 반복 `[ab]*`는 루프). 02 실험: `(a\|b)*`에 n=1,000 성공, n=10,000 실패. `[ab]*`는 n=100,000 성공 | 패턴에 선택 `(x\|y)`의 반복이 있나, 입력 길이 | [02-2](../02-lexing-and-regular-languages/2-summary.md) |

- 처방의 방향: 파서·정규식 앞에 **깊이·길이 상한**, 선택을 문자 클래스로, 재귀를 반복문 + 명시적 스택으로. `-Xss`를 키우는 것은 한계를 옮길 뿐이다(03 실험).
- 재귀 깊이 자체의 복잡도·스택 프레임 크기는 [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) 3절과 [architecture/22](../../architecture/22-arch-symptom-index/2-summary.md) 1절(네이티브 `SIGSEGV` 쪽)이 정본이다.

### 5. 메모리가 차오른다 — `GC overhead limit exceeded`·OOM·GC 멈춤·누수

먼저 **GC 뒤 힙 바닥선**을 본다. 바닥선이 회차마다 오르면 산 데이터가 느는 것(누수·무한 큐), 바닥선은 평평한데 멈춤이 길면 수집 방식·크기 문제다.

```text
  메모리·GC 증상
     │
     ├─ OutOfMemoryError: GC overhead limit exceeded ──────────────────▶ 산 데이터가 힙을 거의 채움(Parallel 98%/2%)  10-2
     ├─ Full GC 간격이 며칠에 걸쳐 짧아짐, 바닥선 우상향 ──────────────────▶ static 컬렉션·리스너 누수                  10-3 · 09-5
     ├─ 힙 덤프 상위 LinkedBlockingQueue$Node + 작업 람다 ────────────────▶ 무한 큐 스레드 풀                       16-1
     ├─ 힙 덤프에 …$$Lambda 수가 요청 수만큼, arg$1이 요청 객체 ──────────▶ 람다가 this를 캡처해 이벤트 버스에 남음     07-4
     ├─ node heapUsed 우상향, 작은 콜백이 큰 배열을 붙잡음 ──────────────▶ 같은 함수의 다른 클로저가 문맥을 공유       07-1
     ├─ Python RSS 계단식, gc.get_count() 0세대가 임계값보다 훨씬 큼 ─────▶ 참조 카운트 순환 + 순환 수집기 꺼짐         09-1
     ├─ 고루틴 수 우상향, 같은 chan send 위치 수천 개 ───────────────────▶ 아무도 안 받는 채널                       14-4
     ├─ 특정 액터가 느려지자 힙 증가 ────────────────────────────────────▶ 무한 메일박스                            14-5
     ├─ p99 스파이크와 Pause 시각이 겹침, liveness 실패 ───────────────────▶ STW 일시정지                             10-1
     ├─ 정해진 시각마다 Pause Full (System.gc()) ────────────────────────▶ 명시적 GC 호출                          10-4
     ├─ ZGC인데 앱 최대 지연이 10ms대 ──────────────────────────────────▶ (해석) CPU 한도에서 동시 수집 스레드와 경쟁  10-5
     ├─ 힙 = 컨테이너 한도의 25%, GC 잦음, 메모리 남음 ─────────────────────▶ MaxRAMPercentage 기본값                  11-1
     ├─ 로그 없이 재시작, exit 137 ────────────────────────────────────▶ 힙을 한도 가까이 + 힙 밖 메모리             11-2 · 15-3
     ├─ (Evacuation Failure) → Pause Full (G1 Compaction Pause) ──────▶ 산 데이터 대비 작은 힙, 회수가 할당을 못 따라감  11-3
     ├─ GC 원인 G1 Humongous Allocation ────────────────────────────────▶ 영역 절반 이상 객체 반복 할당              11-4
     ├─ 작은 파드로 줄인 뒤 p99 악화, 로그 첫 줄 Using Serial ─────────────▶ 서버급 판정에서 떨어져 수집기가 바뀜        11-5
     ├─ 히스토그램 상위 java.lang.Long 수백만 ──────────────────────────────▶ 박싱 — 원소당 헤더·패딩·참조              12-1
     ├─ 트래픽 비례 Young GC 빈도·p99 상승 ──────────────────────────────▶ 높은 할당률                              12-2
     ├─ 객체 풀 도입 뒤 Young GC 수십 배·Mixed·Full ──────────────────────▶ 풀 객체가 Old에서 새 데이터를 붙잡음        12-3
     ├─ 기능 변화 없는 리팩터링 뒤 할당률 증가 ──────────────────────────────▶ 탈출 분석이 깨짐                         12-4
     ├─ 힙을 30→40GB로 늘렸는데 쓸 공간이 기대만큼 안 늘음 ─────────────────▶ 압축 참조 32GB 경계                       12-5
     └─ C: 다른 사용자 데이터가 섞임 / free(): double free detected ──────▶ use-after-free / double free             09-2 · 09-3
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `java.lang.OutOfMemoryError: GC overhead limit exceeded`, 죽기 전 수십 초 거의 무응답. 10 실험(Parallel, `-Xmx64m`): `Pause Full (Ergonomics) 61M->61M(63M) 288ms` 연속, 28초 중 27초 STW | 산 데이터가 힙을 거의 채워 매 수집이 거의 못 회수(이 실험은 누수로 계속 늘었다. Oracle 가이드는 산 데이터가 힙에 겨우 들어가는 경우를 전형적 원인으로 든다 — 누수 없이도 난다). Parallel은 GC 시간 98% 초과 + 회수 2% 미만이면 이 OOM(`java` 문서 `-XX:+UseGCOverheadLimit`). 같은 누수를 G1(21.0.12)로 돌리면 `Java heap space`로 죽었다 | GC 로그 `-Xlog:gc*`의 Full GC 빈도·바닥선, `-XX:+HeapDumpOnOutOfMemoryError`의 덤프 | [10-2](../10-garbage-collection/2-summary.md) |
| Full GC 뒤 바닥선(`→` 오른쪽 값)이 회차마다 오름. 10 실험 2(G1, 힙 64M)에서 Full GC 뒤 값이 54M → 58M → … → 62M으로 올라 힙 꼭대기에 닿음 | 지우지 않는 static 맵·리스너·ThreadLocal이 객체를 도달 가능하게 붙잡음 — 추적 GC 기준으로는 산 객체. 안정된 부하에서 바닥선이 계속 오르면 누수의 강한 징후(Oracle 가이드), 확정은 덤프로 | 힙 덤프의 지배자 트리([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)) | [10-3](../10-garbage-collection/2-summary.md) · [09-5](../09-memory-management-models/2-summary.md) |
| `OutOfMemoryError: Java heap space`, 덤프 상위 `LinkedBlockingQueue$Node`, 그 전까지 거부·경고 없음 | `Executors.newFixedThreadPool`의 큐 용량 `Integer.MAX_VALUE`. 16 실험: 약 0.15초에 3,800건, 64MB 힙 소진 | 풀 생성 코드의 큐 종류·용량, 큐 길이 지표 | [16-1](../16-concurrency-design-patterns/2-summary.md) |
| Old 영역이 계속 참, 덤프의 `…$$Lambda` 인스턴스가 요청 수만큼, `arg$1`이 요청 처리 객체 | 필드를 쓰는 람다는 `this`를 캡처(07 실험 B `[Capture arg$1; ]`). 앱 수명의 이벤트 버스에 등록·미해제 | 람다 등록 코드에 해제 경로가 있나 | [07-4](../07-scope-closures-first-class-functions/2-summary.md) |
| node `heapUsed` 우상향, 스냅숏에서 작은 콜백 → 큰 배열 경로 | V8은 한 함수의 클로저들이 문맥을 공유. 다른 클로저가 쓰는 큰 객체가 오래 사는 콜백과 함께 남음(07 실험 C: 10개에 152.6 MiB) | `--expose-gc` + `heapUsed` 차이, 힙 스냅숏 | [07-1](../07-scope-closures-first-class-functions/2-summary.md) |
| CPython 워커 RSS가 작업마다 계단식, `tracemalloc` 상위가 특정 클래스 생성 줄, `gc.get_count()` 0세대 값이 700을 크게 넘음(09 실험 1에서 2604) | 부모↔자식 같은 순환 + `gc.disable()` 또는 수집 주기보다 빠른 누적 | `gc.isenabled()`, `gc.get_count()`, `tracemalloc` | [09-1](../09-memory-management-models/2-summary.md) |
| `runtime.NumGoroutine()` 우상향, goroutine 프로파일에 같은 `chan send` 수천 개 | 호출자가 떠난 뒤 무버퍼 채널 송신에서 영원히 대기(14 실험 4: 1,000번 호출에 1,000개 잔류) | `net/http/pprof` goroutine 프로파일 | [14-4](../14-concurrency-models/2-summary.md) |
| 특정 액터가 느려지자 힙 증가, 처리 지연이 분 단위 | 송신은 비동기 — 소비가 생산보다 느리면 메일박스(무한 큐)가 쌓임 | 메일박스 길이 지표 | [14-5](../14-concurrency-models/2-summary.md) |
| p99 수백 ms 스파이크가 `Pause Young`·`Pause Full` 시각과 겹침, liveness 실패로 재시작 | STW 동안 모든 요청 스레드 정지. 10 실험 1: 같은 부하에 Serial 앱 지연 최대 149~201ms, ZGC 12~30ms | 지연 스파이크 시각 ↔ GC 로그 시각 대조 | [10-1](../10-garbage-collection/2-summary.md) |
| 부하와 무관한 주기의 `Pause Full (System.gc())` | 라이브러리·모니터링 도구·앱의 `System.gc()` | GC 원인 칸 | [10-4](../10-garbage-collection/2-summary.md) |
| ZGC로 바꾼 뒤 로그 STW는 1ms 미만, 앱 최대 지연은 10ms대 | 해석: 동시 수집 스레드가 앱과 CPU를 나눔(`--cpus=2`). 10 실험 1은 CPU 사용을 따로 재지 않았고 호스트 부하도 배제하지 못했다 — 가설로 두고 확인한다 | CPU 한도, 수집 중 앱 스레드 CPU | [10-5](../10-garbage-collection/2-summary.md) |
| 4GiB 파드에서 힙 1GiB, GC 잦음, 컨테이너 메모리 절반 이상 남음 | `MaxRAMPercentage` 기본 25%(11 실험 1: 4GiB → 1GiB) | `java -XX:+PrintFlagsFinal -version \| grep MaxHeapSize` | [11-1](../11-gc-tuning-and-gc-logs/2-summary.md) |
| `-Xmx`를 한도의 90%로 올린 뒤 부하 때 로그 없이 재시작, exit 137(`OOMKilled`) | 힙 밖(메타스페이스·스레드 스택·코드 캐시·direct buffer)이 남은 10%를 넘음 → cgroup이 SIGKILL | NMT(`-XX:NativeMemoryTracking=summary` + `jcmd VM.native_memory`), [os/13](../../os/13-oom-and-memory-limits/2-summary.md) | [11-2](../11-gc-tuning-and-gc-logs/2-summary.md) |
| `multiprocessing`으로 바꾼 뒤 워커 수만큼 메모리 → OOMKilled | 프로세스마다 인터프리터·모듈·데이터, 인자는 pickle 복사 | 워커 수 × 프로세스당 RSS | [15-3](../15-gil-and-runtime-constraints/2-summary.md) |
| `(Evacuation Failure)` 몇 번 → `Pause Full (G1 Compaction Pause) 511M->205M`(11 실험 2) | 산 데이터(200MB)가 힙(512MB)에 비해 크고, 회수가 할당을 못 따라감 — 이 로그는 `Prepare Mixed`·`Mixed`가 이미 시작된 뒤에 실패했다(마킹 시점은 로그로 따로 확인). 같은 실험에서 힙 1GiB면 Full GC 0 | GC 로그의 `Evacuation Failure` 태그, 산 데이터 크기 | [11-3](../11-gc-tuning-and-gc-logs/2-summary.md) |
| GC 원인 `G1 Humongous Allocation`, `Humongous regions: X->Y`(11 실험 3: 600KB 배열 → GC 35~38회 중 35~37회가 이 원인, 나머지는 소스 실행기의 컴파일 중 GC라는 해석) | 영역 절반 이상 객체는 연속 영역을 통째로 씀 | 큰 배열·버퍼를 요청마다 새로 만드나, `G1HeapRegionSize` | [11-4](../11-gc-tuning-and-gc-logs/2-summary.md) |
| 1 vCPU·1GiB대 파드로 줄인 뒤 p99 악화, 로그 첫 줄 `Using Serial`(11 실험 1: 2 CPU·1791MiB까지 Serial) | 서버급 판정(CPU ≥ 2, 메모리 ≥ 1792MB)에서 떨어져 기본 수집기가 바뀜 | `-Xlog:gc` 첫 줄 | [11-5](../11-gc-tuning-and-gc-logs/2-summary.md) |
| 히스토그램 상위 `java.lang.Long`(개당 24B)·`[Ljava.lang.Object;`, 원소당 28B(12 실험 2) | 박싱 — 헤더 12B + 패딩 4B + 값 8B + 참조 4B. `long[]`은 8B | `jcmd <pid> GC.class_histogram \| head` | [12-1](../12-object-layout-and-allocation-reduction/2-summary.md) |
| 트래픽 비례 Young GC 빈도·p99 상승(12 실험 3: 탈출 분석을 꺼 할당이 두 배가 되자 Young GC 11 → 21회) | 요청마다 임시 객체·박싱·큰 버퍼 → Eden이 빨리 참 | GC 로그로 할당률 계산(11번 §4), 할당 프로파일 | [12-2](../12-object-layout-and-allocation-reduction/2-summary.md) |
| 풀 도입 뒤 Young GC 평균 2.4ms → 45~51ms, `Pause Young (Mixed)`·Full 등장(12 실험 4) | Old에 사는 풀 객체가 매 요청의 새 데이터를 가리켜, 짧게 살 데이터를 Young GC마다 산 객체로 살려 두고 결국 승격시킴 | 풀을 걷어 낸 판과 비교 | [12-3](../12-object-layout-and-allocation-reduction/2-summary.md) |
| 기능 변화 없는 리팩터링 뒤 할당률·GC 횟수 증가 | 객체가 인라인 안 되는 헬퍼로 넘어가 탈출로 판정(Shipilëv Quark #18) | `-XX:-DoEscapeAnalysis` 비교, 호출당 할당 바이트 | [12-4](../12-object-layout-and-allocation-reduction/2-summary.md) |
| 힙을 30GB에서 40GB로 늘렸는데 쓸 수 있는 공간이 기대만큼 안 늘음 | 문서 근거 + 미실험: 압축 참조 기본 범위 32GB를 넘으면 참조 8B | `-XX:+PrintFlagsFinal`의 `UseCompressedOops` | [12-5](../12-object-layout-and-allocation-reduction/2-summary.md) |
| C: 응답에 다른 사용자 이름이 드물게 섞임, 크래시 없음 / `free(): double free detected` 후 exit 134 | use-after-free(해제 블록을 다른 할당이 재사용) / 두 곳이 같은 블록을 해제 | ASan 빌드(`heap-use-after-free`와 해제·할당 위치 스택), [os/11](../../os/11-heap-allocation/2-summary.md) | [09-2](../09-memory-management-models/2-summary.md) · [09-3](../09-memory-management-models/2-summary.md) |
| Rust 빌드 실패 `E0382` | 소유권 이동 뒤 원래 변수 사용 — 소유자가 하나라는 규칙 | 오류 색인의 설명, 빌림·`clone`·`Rc`로 바꿀지 | [09-4](../09-memory-management-models/2-summary.md) |

- 처방의 방향: `GC overhead`·`Java heap space`는 누수로도, 일정한 산 데이터에 비해 힙이 작아서도 난다(Oracle 문제 해결 가이드). 메시지만으로 가르지 말고 Full GC 뒤 바닥선 추세로 가른다 — 오르면 누수, 평평하면 힙 부족([10-2](../10-garbage-collection/2-summary.md)). 알림은 OOM보다 Full GC 빈도·GC 시간 비율에 건다. 큐·캐시·메일박스에는 상한을 둔다.
- 운영 쪽 누수 분석 순서(덤프·지배자 트리)는 [reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md), cgroup OOM은 [os/13](../../os/13-oom-and-memory-limits/2-summary.md)이 정본이다.

### 6. CPU를 먹거나 느리다 — 정규식 CPU 100%·배포 직후 p99·처리량 바닥

먼저 **프로파일·스레드 덤프의 맨 위 프레임**을 본다. `Pattern$…match`면 정규식, `C2 CompilerThread`·`PrintCompilation` 폭주면 JIT, `Throwable.fillInStackTrace`면 흐름 제어용 예외다.

```text
  CPU 높음 / 느림
     │
     ├─ 코어 하나씩 100%, 덤프가 Pattern$GroupHead·Loop·GroupTail.match 반복 ──▶ 백트래킹 정규식(ReDoS)           02-1
     ├─ 프로파일 상위 Pattern.compile, 반복문 안 String.matches ───────────────▶ 매 호출 정규식 컴파일            02-4
     ├─ 새 파드만 1~몇 분 p99 급등, C2 CompilerThread ───────────────────────▶ JIT 워밍업 전                    01-1 · 23-1
     ├─ 특정 시점 CPU·지연이 잠깐 튐, 같은 메서드 made not entrant 반복 ───────▶ 역최적화 연쇄                    23-2
     ├─ 특정 환경만 처리량 수십 배 낮음, VM.flags에 -Xint·TieredStopAtLevel ────▶ JIT를 끈 옵션이 남음            01-3
     ├─ 며칠 뒤 새 핫 코드가 느린 채, "… is full. Compiler has been disabled." ─▶ 코드 캐시 가득                   01-4 · 23-3
     ├─ 구현 클래스 추가 뒤 핫 루프 10배, inline (hot) → virtual call ──────────▶ 메가모픽 호출 지점               17-3
     ├─ C++ 가상 호출 루프가 예상보다 느림, objdump에 call *… ─────────────────▶ 간접 호출·예측 실패              17-4
     ├─ 검증 실패율이 오르자 CPU 급등, fillInStackTrace 상위 ──────────────────▶ 깊은 스택에서 흐름 제어용 예외      08-5
     ├─ CPU 바운드 스레드 8개인데 CPU 약 100%(코어 1개분) ───────────────────────▶ CPython GIL                      15-1 · 15-4
     ├─ 같은 코드가 운영에서만 수 배 느림, 기계어가 스택 읽기·쓰기투성이 ─────────▶ 디버그(-O0) 빌드 배포             22-4
     ├─ PGO 빌드 뒤 특정 기능만 느림 / PGO가 효과 없음 ───────────────────────▶ 대표성 없는 프로파일 / 프로파일 미적용  25-2 · 25-4
     ├─ 네이티브 이미지 처리량 < JVM ─────────────────────────────────────────▶ 실행 중 프로파일 없는 AOT          24-3
     ├─ 짧은 CLI·함수 콜드 스타트 p99 ───────────────────────────────────────▶ 오래 사는 모형(JVM)을 짧은 프로세스에  21-5
     ├─ 링크 단계만 수 분~수십 분·러너 OOM ────────────────────────────────────▶ full LTO                         25-1
     ├─ 네이티브 빌드 단계만 느리고 러너가 죽음 ──────────────────────────────────▶ 전체 프로그램 분석 + AOT 컴파일     24-2
     ├─ 이미지가 갑자기 커지고 pull이 느림 ─────────────────────────────────────▶ 디버그 심볼이 든 채 배포           25-3
     └─ 마이크로벤치마크 0ns / 로컬과 운영의 순위가 뒤집힘 ───────────────────────▶ DCE·워밍업·단형 프로파일          22-2 · 23-4
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 특정 요청부터 응답이 안 끝나고 코어가 하나씩 100%, 요청 스레드 고갈. Java 덤프가 `Pattern$GroupHead.match` → `Pattern$Loop.match` → `Pattern$GroupTail.match` 반복. 입력에 같은 글자가 길게 이어짐 | 백트래킹 엔진이 실패 입력에서 나눔을 지수(또는 높은 다항)만큼 시도. 02 실험: Python·node는 `(a+)+$`에서 한 글자당 약 2배. Java 21은 이 모양에 메모이제이션이 있어 안 터졌지만 역참조 하나(`(a+)+$\|(b)\2`)로 꺼짐 | 스레드 덤프 2~3회의 맨 위 프레임, 의심 입력의 모양을 유지한 채 길이를 두 배씩 늘려 시간 비율([algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) 4절) | [02-1](../02-lexing-and-regular-languages/2-summary.md) |
| 프로파일 상위 `Pattern.compile`, 반복문 안 `String.matches`·`replaceAll`·`split(정규식)` | `String.matches(regex)`는 호출마다 컴파일(Java API 문서). `split`은 메타 문자가 아닌 한 글자 등 일부 구분자면 정규식 없이 빠른 경로로 자르고(jdk21u `String.java`), 그 밖의 패턴만 호출마다 컴파일한다. 02 실험(100만 회): 514~1,835ms vs 미리 컴파일 132~161ms | `static final Pattern`인가 | [02-4](../02-lexing-and-regular-languages/2-summary.md) |
| 롤링 배포·스케일아웃 뒤 새 파드만 1~몇 분 p99가 몇 배, 평균은 조금, 저절로 가라앉음 | 인터프리터·level 3 코드로 트래픽을 받음. 23 실험 1: C2 전 구간이 C2 코드보다 약 2~20배 느림(첫 호출은 그 이상). 컴파일 스레드가 앱과 CPU를 나눔 | `-XX:+PrintCompilation`의 level 3·4 컴파일 몰림, 새 파드 CPU | [01-1](../01-compile-interpret-jit/2-summary.md) · [23-1](../23-jit-tiered-compilation-and-warmup/2-summary.md) |
| 기능 플래그·드문 요청 유형 시점에 CPU·지연이 잠깐 튐 | 단형으로 굳은 호출 지점에 새 타입 → 가드 실패 → 역최적화. 23 실험 2: 재컴파일 전 약 11~17배 느림 | `-Xlog:deoptimization=debug`의 `class_check`·`unstable_if`, `PrintCompilation`의 `made not entrant` 반복 | [23-2](../23-jit-tiered-compilation-and-warmup/2-summary.md) |
| 특정 환경에서만 CPU 높고 처리량 수십 배 낮음, 시작 로그 `Picked up JAVA_TOOL_OPTIONS: …` | `-Xint`(01 실험: 데워진 기본 모드보다 약 40~210배), `TieredStopAtLevel=1`(약 2~15배)이 남음 | `jcmd <pid> VM.flags`, `java -Xint -version`이면 `interpreted mode` | [01-3](../01-compile-interpret-jit/2-summary.md) |
| 며칠 뒤 새 핫 코드가 느린 채, `CodeHeap 'non-profiled nmethods' is full. Compiler has been disabled.` 꼴의 경고 | 동적 생성 클래스·람다·프록시가 코드 캐시를 채움(문구 틀은 HotSpot 21 `codeCache.cpp`). 23은 작은 캐시로 재현을 시도했지만 그 규모에서는 경고가 안 나왔다 — 문구는 소스로만 확인 | `jcmd <pid> Compiler.codecache`의 `free`·`full_count` | [01-4](../01-compile-interpret-jit/2-summary.md) · [23-3](../23-jit-tiered-compilation-and-warmup/2-summary.md) |
| 새 구현 2개 추가 배포 뒤 배치가 느려짐, 코드 변경은 새 클래스뿐. `PrintInlining`에서 `inline (hot)` → `virtual call` | 호출 지점이 보는 수신 타입이 2개를 넘고 어느 하나가 90% 이상도 아니어서 C2가 인라인을 시도하지 않음(17 실험 C: 2종류 1.19~1.64ns → 4종류 10.01~13.58ns) | `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` | [17-3](../17-dispatch-and-polymorphism-mechanics/2-summary.md) |
| C++ 가상 `update()` 루프가 예상보다 느림, `objdump`에 `call *…`·`jmp *(%rax)` | 구현이 여럿이라 추측 탈가상화 실패, 간접 분기 목적지가 섞임 | `objdump -d`의 간접 호출 | [17-4](../17-dispatch-and-polymorphism-mechanics/2-summary.md) |
| 트래픽은 그대로인데 검증 실패율이 오르자 CPU 급등, 프로파일 상위 `Throwable.fillInStackTrace` | 실패 1건당 스택 기록 + 되감기(08 실험 C: 깊이 200에서 호출당 약 17~21µs — 호출의 절반이 실패한 측정) | 예외를 던지는 깊이, 실패율 | [08-5](../08-error-handling-models/2-summary.md) |
| 스레드 8개 배치가 그대로거나 더 느림, `top`에서 프로세스 CPU 약 100%(15 실험 1: threads(4) 2.00~2.61s vs serial 1.92~2.12s) | CPython 기본 빌드는 한 번에 한 스레드만 바이트코드 실행. free-threaded 빌드에서도 지원 표시 없는 C 확장을 import하면 GIL이 다시 켜짐 | 프로세스 CPU가 코어 1개분인가, `sys._is_gil_enabled()`(3.13+ — 3.12에는 없음) | [15-1](../15-gil-and-runtime-constraints/2-summary.md) · [15-4](../15-gil-and-runtime-constraints/2-summary.md) |
| 같은 코드가 운영에서만 수 배 느림, 핫 함수가 `mov %edi,-0x4(%rbp)` 같은 스택 저장투성이, 작은 함수도 `call` | 디버그(`-O0`) 설정이 빌드 스크립트·Dockerfile에 남음(22 실험: 반복당 3.5~8.4ns) | `DW_AT_producer`의 `-O0`, `-frecord-gcc-switches` | [22-4](../22-ir-and-optimization/2-summary.md) |
| PGO 배포 뒤 특정 기능·고객군만 느려짐, 그 경로의 루프가 벡터화 안 됨 | 훈련에서 안 돈 코드는 크기 우선 최적화(GCC 문서). 25 실험 3: PGO 없음 0.55~0.69초 → 비대표 훈련 1.14~1.22초 | `objdump`에서 xmm/ymm 사라짐, 훈련 입력의 대표성 | [25-2](../25-lto-pgo-and-binary-size/2-summary.md) |
| PGO를 켰는데 성능·코드 그대로 | `.gcda` 경로가 재빌드 목적 파일과 안 맞음 + `-Wno-missing-profile`로 경고 숨김 | 빌드 경고, 훈련·재빌드의 출력 이름·경로가 같은가(`-fprofile-dir`는 디렉터리만 바꿈) | [25-4](../25-lto-pgo-and-binary-size/2-summary.md) |
| 네이티브 이미지가 시작은 빠른데 처리량은 JVM보다 낮음 | 가설: 실행 중 프로파일 없는 AOT는 JIT의 투기적 최적화를 그대로 얻지 못함 `[?]` | 같은 부하로 JVM·네이티브 비교, PGO 빌드 | [24-3](../24-aot-native-image-and-startup/2-summary.md) |
| 호출마다 뜨는 CLI·함수가 느림(21 실험 2: 같은 hello world가 Go 4~6ms, Java 59~105ms) | JVM은 오래 살아서 판단 비용을 상각하는 모형 | 프로세스 수명 대비 기동 시간 | [21-5](../21-language-choice-tradeoffs/2-summary.md) |
| 릴리스 링크 단계만 수 분~수십 분, `ld`·`lto1`·`ld.lld`가 오래 돎(25 실험 2: 링크 0.28초 → 168초, 최대 RSS 약 6배) | full LTO는 모든 모듈을 한 덩어리로 코드 생성 | `/usr/bin/time -v`의 `Maximum resident set size` | [25-1](../25-lto-pgo-and-binary-size/2-summary.md) |
| 네이티브 빌드 단계만 느리고 작은 러너에서 OOMKilled(exit 137) | 전체 프로그램 분석 + AOT 컴파일. 문서 예시 HelloWorld도 25.5초·2.14GiB | 빌드 출력 끝의 `Peak RSS` | [24-2](../24-aot-native-image-and-startup/2-summary.md) |
| 새 이미지가 갑자기 커짐, 스케일 아웃 때 pull 지연 | `-g`가 든 채 strip 단계 누락(25 실험 4: 13.3MB 중 text 2.75MB) | `readelf -S`의 `.debug_*` 절, `size` | [25-3](../25-lto-pgo-and-binary-size/2-summary.md) |
| 최적화를 켜자 측정값 0ns, N과 무관 / 로컬에서 A가 빨랐는데 운영에서는 B | 결과를 안 쓰는 계산이 DCE로 사라짐(22 실험 `-O2` 0.003~0.004ms) / 워밍업 구간 혼입·한 타입으로만 데움(23 실험 2: 단형 1.86~2.30µs vs 혼합 재컴파일 뒤 5.98~8.42µs, 집필·재실행 6회) | 기계어에 반복문이 남았나, 측정이 운영의 타입 분포로 데웠나 | [22-2](../22-ir-and-optimization/2-summary.md) · [23-4](../23-jit-tiered-compilation-and-warmup/2-summary.md) |

- 처방의 방향: 정규식은 입력 길이 상한·패턴 재작성·선형 엔진, JIT는 예열 후 readiness·가중치 증가·CDS·AppCDS(JDK 24+면 AOT 캐시), 메가모픽은 측정으로 확정한 뒤 종류별 일괄 처리, 빌드는 릴리스 플래그 CI 검사.
- 프로파일링 도구 자체(async-profiler·flame graph 읽기)는 [reliability/36](../../reliability/36-profiling/2-summary.md), 마이크로벤치마크 방법은 [reliability/38](../../reliability/38-microbenchmarking/2-summary.md), 콜드 스타트 운영은 [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)가 정본이다.

### 7. 기다리는 동안 다른 일도 멈춘다 — async 정지·런타임 전체 지연

먼저 **"모든 요청이 동시에" 느려졌는지**를 본다. 무거운 API 하나만 느리면 그 API 문제, 무관한 API까지 같이 느리면 공유하는 실행 자원(이벤트 루프·캐리어·공용 풀)이 막힌 것이다.

```text
  무관한 요청까지 같이 멈춤
     │
     ├─ CPU 코어 하나만 100%, 이벤트 루프 지연 p99 급등 ─────────────────────▶ async 안의 동기 블로킹·계산          14-1 · 15-5
     ├─ 가상 스레드인데 처리량이 풀 시절보다 낮고 CPU가 놂 ──────────────────▶ synchronized pinning(JDK 21~23)      14-2
     ├─ 가상 스레드 전환 뒤 커넥션 풀 대기 타임아웃 증가 ─────────────────────▶ 하류 동시성 무제한                    14-3
     ├─ 외부 API 하나 느린 날 무관한 supplyAsync·병렬 스트림도 느림 ───────────▶ 공용 풀(ForkJoin common pool) 블로킹   16-2
     └─ 종료 신호 뒤 워커가 안 끝남, RUNNABLE로 같은 루프 / 자기로 jmp ────────▶ 플래그에 hb 간선 없음(JIT·C 최적화)    13-1 · 22-3
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| API 하나가 무거워졌는데 **모든** 요청 지연이 동시에 뜀, CPU는 코어 하나만 100%, 헬스 체크 타임아웃. 프로파일에서 루프 스레드가 `pbkdf2Sync`·`JSON.parse`·JDBC 드라이버 안 | 협력적 전환은 `await`·콜백 반환에서만 — 그 사이의 동기 코드는 끝날 때까지 루프를 쥔다. 14 실험 3(node 22, 4회): `sync`는 handler 156~173ms 동안 10ms 타이머 최대 지연도 같은 156~173ms, `async`는 1~4ms | `monitorEventLoopDelay` p99, 루프 스레드 스택 | [14-1](../14-concurrency-models/2-summary.md) |
| Node 보고서 생성 API가 돌 때 다른 API도 멈춤 | JS는 이벤트 루프 스레드 하나에서 CPU 작업을 함 — GIL과 같은 모양의 런타임 제약 | 그 API의 동기 CPU 시간 | [15-5](../15-gil-and-runtime-constraints/2-summary.md) |
| 가상 스레드로 바꿨는데 처리량이 낮고 CPU는 놂, 덤프에서 `ForkJoinPool-1-worker-*`가 모두 `synchronized` 안 블로킹 호출 | JDK 21~23: `synchronized` 안 블로킹은 언마운트가 안 돼 캐리어(기본 CPU 수)까지 잠듦. 14 실험 2: 100ms 작업 100개가 5초 | `-Djdk.tracePinnedThreads=short`의 `reason:MONITOR`, JFR `jdk.VirtualThreadPinned` | [14-2](../14-concurrency-models/2-summary.md) |
| 전환 뒤 `Connection is not available, request timed out` 같은 풀 대기 타임아웃 증가 | 가상 스레드는 동시 요청을 늘릴 뿐 DB 처리량은 그대로. 대기가 풀 앞으로 옮겨감 | 동시 요청 수 vs 풀 크기 | [14-3](../14-concurrency-models/2-summary.md) |
| 외부 API가 느린 날 무관한 비동기 작업·병렬 스트림까지 느림, 덤프의 `ForkJoinPool.commonPool-worker-*`가 전부 소켓 읽기·`sleep`·`park` | executor 없는 `supplyAsync`·병렬 스트림이 공용 풀(기본 코어 수 − 1)을 나눠 씀. 단 공용 풀 병렬도가 2 미만이면 `CompletableFuture`의 async 메서드는 작업마다 새 스레드를 만든다(Java 21 API 문서). 16 실험 3: 코어 4개로 보일 때(병렬도 3) 가벼운 작업이 1001~1002ms 대기, 코어 2개로 보일 때(병렬도 1 → 작업마다 새 `Thread-N`)는 1~2ms | `supplyAsync`에 executor 인자가 있나, 운영과 같은 코어 수로 시험 | [16-2](../16-concurrency-design-patterns/2-summary.md) |
| 종료 신호 뒤 워커가 안 끝나 배포가 멈춤, 덤프에서 `RUNNABLE`로 같은 루프. C는 `-O2`만 멈추고 기계어가 자기 자신으로 `jmp` | 플래그 읽기·쓰기 사이에 happens-before 없음(race). Java는 JIT가 읽기를 루프 밖으로 빼도 되고(JLS 17.3), C는 race 자체가 UB(N1570 5.1.2.4) | 플래그 필드에 `volatile`·`_Atomic`이 있나, `objdump -d`의 루프 | [13-1](../13-language-memory-model/2-summary.md) · [22-3](../22-ir-and-optimization/2-summary.md) |

- 처방의 방향: 루프·캐리어·공용 풀에서는 기다리지도 오래 계산하지도 않는다. 블로킹에는 전용 executor(또는 가상 스레드 executor), CPU 작업은 `worker_threads`·프로세스·별도 서비스, 하류 동시성은 세마포어로 제한한다.
- 운영 지표 쪽(스레드 고갈·이벤트 루프 지연의 대시보드)은 [reliability/52](../../reliability/52-reliability-symptom-index/2-summary.md) 2·6절, 이벤트 기반 서버 구조는 [os/27](../../os/27-event-based-concurrency/2-summary.md)이 정본이다.

### 8. 집계가 매번 다르거나 남의 값이 섞인다 — 공유 상태

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 같은 입력의 병렬 통계가 1,323,530~1,834,261처럼 흔들리고 가끔은 기대값 2,000,000이 그대로 나옴(07 실험 D와 재실행 12라운드) | effectively final 제한을 `int[]`로 우회해 람다들이 같은 칸을 동시에 고침 | 람다가 캡처한 배열 한 칸·가변 객체 | [07-2](../07-scope-closures-first-class-functions/2-summary.md) · [04-4](../04-semantic-analysis-and-scopes/2-summary.md) |
| 병렬 스트림 배치 건수가 59,685 / 68,777 / 71,746(기대 100,000, 18 실험 C — 재실행 9라운드 57,126~81,564) | 스레드 안전하지 않은 `ArrayList`에 여러 스레드가 `add` | `forEach` 안 외부 컬렉션 `add` | [18-3](../18-functional-concepts/2-summary.md) |
| CPython 카운터가 로그 한 줄 추가 뒤부터 모자람(15 실험 2: 5,000,000 → 약 180만~370만, 실행마다 다름) | GIL은 바이트코드 하나 단위만 직렬화. 읽기-수정-쓰기 사이 전환 지점이 생김 | 공유 카운터에 락이 있나 | [15-2](../15-gil-and-runtime-constraints/2-summary.md) |
| `setRelease`·`getAcquire`로 바꾼 뒤 두 스레드가 같이 임계 구역에 들어감(13 실험 1: 2백만 회 중 약 12만~35만 번 (0, 0)) | release/acquire는 저장 → 읽기 순서를 약속하지 않음 | 직접 만든 상호 배제 코드 | [13-3](../13-language-memory-model/2-summary.md) |
| C 릴리스 빌드만 멈추거나 엉뚱한 값, TSan `WARNING: ThreadSanitizer: data race` | C11 data race는 UB | `-fsanitize=thread` 테스트 | [13-4](../13-language-memory-model/2-summary.md) |
| non-volatile `long`이 두 값의 반쪽이 섞인 값(가능성) | JLS 17.7은 non-volatile `long`·`double` 쓰기를 둘로 나눠도 된다고 허용. 64비트 JVM에서 실제로 찢기는지는 미확인 `[?]` | 공유 `long` 필드에 `volatile`·`AtomicLong`이 있나 | [13-5](../13-language-memory-model/2-summary.md) |
| 익명 요청이 다른 사용자로 처리, 같은 워커 스레드 이름에서 연속 요청 사이에만 | 풀 스레드가 요청보다 오래 살고 `ThreadLocal.remove`가 예외 경로에서 빠짐(16 실험 6) | `set`한 곳에 `finally { remove() }`가 있나 | [16-4](../16-concurrency-design-patterns/2-summary.md) |
| 응답에 이전 요청의 사용자 ID(`user_001`)가 섞임, 재시작 직후엔 멀쩡(Python) | 가변 기본 인자 `acc=[]`는 `def` 때 한 번 만들어 모든 호출이 공유 | `func.__defaults__` | [06-1](../06-values-references-passing/2-summary.md) |
| 테넌트 A 설정을 바꿨더니 모든 테넌트가 바뀜 | 얕은 복사 — 중첩 객체 공유(06 실험 B `same element? true`) | 바깥·중첩 객체의 동일성 | [06-2](../06-values-references-passing/2-summary.md) |

### 9. 디버그 빌드에서는 맞고 릴리스에서만 틀리다 — UB와 최적화

먼저 **같은 소스를 `-O0`와 `-O2`로 돌려 결과가 다른지** 본다. 다르면 컴파일러 버그보다 미정의 동작(UB)을 먼저 의심한다.

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 일부 응답에 남의 쿠키·토큰 조각, 서버 오류 없음, 외부 신고로 처음 앎 | 끝 검사가 `==`라 포인터가 끝을 건너뛰고 계속 읽음(Cloudbleed 모양). 메모리 풀 안 넘침은 ASan도 못 잡음(20 실험 3) | 퍼징 + 풀 경계 검사 모드, ASan | [20-1](../20-undefined-behavior-and-memory-safety/2-summary.md) · [27 사건 1](../27-pl-incidents/2-summary.md) |
| 정상 응답 안에 프로세스 메모리, 로그에 이상 없음 | 요청이 주장한 길이만큼 복사하고 실제 길이와 대조 안 함(Heartbleed 모양) | 길이 필드를 쓰는 복사마다 실제 길이 대조 | [20-2](../20-undefined-behavior-and-memory-safety/2-summary.md) · [27 사건 2](../27-pl-incidents/2-summary.md) |
| 소스에 `if (p == NULL)`이 있는데 null에서 크래시·엉뚱한 값. 22 실험 `status_of(NULL)`: gcc `-O0` SIGSEGV, gcc `-O2` 0, clang `-O2` -1 | 검사 전에 역참조 → "UB가 아니었다면 non-null"로 추론해 검사 삭제 | `objdump -d`에 `test`/`cmp`가 남았나, `-fsanitize=null` | [20-3](../20-undefined-behavior-and-memory-safety/2-summary.md) · [22-1](../22-ir-and-optimization/2-summary.md) |
| 큰 입력에서 넘침 검사가 통과돼 음수 길이(20 실험 2 `bad_guard`가 -1 대신 `-2147483559`) | `if (len + add < len)`은 넘침 **뒤** 검사, 부호 있는 넘침은 UB라 `add < 0`으로 바뀜 | `-fsanitize=undefined`, `__builtin_add_overflow`로 바꿨을 때 결과 | [20-4](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 같은 입력에 디버그 빌드 0, 릴리스 1 | UB 프로그램에 최적화 수준마다 다른 가정 | UBSan 빌드로 UB 위치 | [20-5](../20-undefined-behavior-and-memory-safety/2-summary.md) |
| 길이 검사가 음수 길이 입력에서 엉뚱하게 동작(`n < sizeof(buf)`는 -1에서 거짓, `int` 상수 비교는 -1을 통과시킨 뒤 `memcpy` 인자에서 큰 수), `-Wsign-compare` 무시 상태 | 부호 있는 값과 `size_t`가 만나는 곳(비교·인자 전달)에서 -1이 `18446744073709551615`로(05 실험 A, x86-64) | 경고 목록, 비교 양쪽 타입 | [05-4](../05-type-systems/2-summary.md) |
| 재현 안 되는 값 오염(21 실험 1의 C `arr[5]`가 오류 없이 값) | C·C++의 경계·수명 위반은 언어가 막지 않음 | 새니타이저 빌드 | [21-4](../21-language-choice-tradeoffs/2-summary.md) |
| 잔액·재고가 2^31 근처에서 음수(21 실험 1 Java·Go `MAX+1 = -2147483648`) | Java·Go의 정수 넘침은 명세상 정의된 감김, 예외 아님 | 값이 2^31·2^63 근처인가, `Math.addExact`로 재실행 | [21-1](../21-language-choice-tradeoffs/2-summary.md) |

- 신호(`SIGSEGV`·`SIGILL`)와 정수 비트 해석은 [architecture/22](../../architecture/22-arch-symptom-index/2-summary.md) 1·2절, 공격 관점(카나리·ASLR)은 [security/24](../../security/24-memory-safety-exploits/2-summary.md)가 정본이다.

### 10. 예외 없이 값이 엉뚱하다 — 어휘·구문·스코프·바인딩

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 숫자만 받는 필드에 `12abc` 저장 | `find()`는 부분 일치, `matches()`는 전체 일치 | 검증 코드의 메서드 | [02-3](../02-lexing-and-regular-languages/2-summary.md) |
| 앞단 로그에 없는 요청이 뒷단에, 다른 사용자 응답이 섞임 | 두 HTTP 파서가 메시지 길이 규칙(RFC 9112 §6.3)을 다르게 구현 | `Content-Length`와 `Transfer-Encoding`이 함께 있나 | [03-2](../03-parsing-grammars-ast/2-summary.md) |
| 권한 검사를 통과한 요청이 다른 권한으로 처리, 같은 이름 파라미터·JSON 키가 두 번 | 중복을 라이브러리마다 다르게 고름(03 실험: Python `dict(parse_qsl)` 마지막 값, node `URLSearchParams.get` 첫 값) | 요청에 중복 키가 있나 | [03-3](../03-parsing-grammars-ast/2-summary.md) |
| `8-3-2`가 7 | 오른쪽 재귀 문법 → 오른쪽 결합 | 결합성 테스트 | [03-4](../03-parsing-grammars-ast/2-summary.md) |
| 세터를 불렀는데 필드 그대로(`field count = 0`) | 매개변수가 필드를 가림(섀도잉) — 이름 해석은 가장 가까운 스코프에서 멈춤 | `this.` 유무, 섀도잉 경고 | [04-1](../04-semantic-analysis-and-scopes/2-summary.md) |
| 반복문에서 등록한 콜백이 전부 마지막 값(JS `var` → 3,3,3, Python → `[2, 2, 2]`) | `var`는 함수 스코프 바인딩 하나, Python 클로저는 늦은 바인딩 | 루프 변수 선언(`var`/`let`), 기본 인자 `i=i` | [04-2](../04-semantic-analysis-and-scopes/2-summary.md) · [07-3](../07-scope-closures-first-class-functions/2-summary.md) |
| 한 줄 추가로 그 줄보다 **위**에서 `UnboundLocalError: cannot access local variable 'count' …` | 함수 안 어디든 대입이 있으면 함수 전체에서 지역(컴파일 시점 결정) | 같은 이름의 대입이 함수 안에 있나 | [04-3](../04-semantic-analysis-and-scopes/2-summary.md) |
| 복사한 주문의 `createdAt.getTime()`에서 `TypeError` | `JSON.parse(JSON.stringify(o))`가 `Date`를 문자열로 | 깊은 복사 방법 | [06-4](../06-values-references-passing/2-summary.md) |
| `normalize(list)` 안에서 재할당했는데 호출자는 그대로 | 값에 의한 전달 — 재할당은 callee의 칸만 바꿈 | 결과를 반환하나 | [06-5](../06-values-references-passing/2-summary.md) |
| 네이티브 이미지의 모든 인스턴스가 같은 "시작 시각"·난수 순서 | 빌드 때 초기화된 static 값이 이미지 힙에 저장됨 | 그 클래스의 초기화 시점(빌드/실행) | [24-4](../24-aot-native-image-and-startup/2-summary.md) |

### 11. 설치·재빌드가 깨진다 — 의존성 해석

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 코드 변경 없는 재빌드에서 테스트가 깨짐, 로컬과 CI 결과가 다름 | 범위 선언(`^`·`~`·`>=`)을 그날 레지스트리로 해석(19 실험 4의 day2) | 두 빌드의 `npm ls`·`pip freeze` 비교, 락파일 커밋 여부 | [19-3](../19-modules-and-dependency-resolution/2-summary.md) |
| 내 코드·락파일 그대로인데 설치 단계가 "패키지·판을 찾을 수 없음" | 레지스트리에서 그 판이 사라짐(left-pad, 2016-03). 락파일은 "무슨 판"을 고정할 뿐 "그 판이 남아 있음"은 보장 안 함 | 설치 로그의 패키지 이름·판, 사내 미러에 사본이 있나 | [19-4](../19-modules-and-dependency-resolution/2-summary.md) · [27 사건 3](../27-pl-incidents/2-summary.md) |

### 12. 증상별 "하지 말 것" 한 줄

| 하지 말 것 | 이유 | 대신 |
|---|---|---|
| `NoSuchMethodError`에 재빌드·재배포만 반복 | 해석 결과가 같으면 같은 낮은 판이 또 올라간다 | `-verbose:class`로 실제 jar, 해석 트리로 누가 끌어왔나 |
| CCE를 꺼낸 줄에서 캐스트로 고침 | 원인은 넣은 곳이다 | `Collections.checkedList`로 넣는 순간을 잡는다 |
| 스택 없는 NPE를 "원인 불명"으로 닫음 | 스택이 생략된 것일 뿐이다 | 첫 발생 로그, `-XX:-OmitStackTraceInFastThrow`로 재현 |
| `StackOverflowError`에 `-Xss`만 키움 | 한계가 옮겨갈 뿐이다(03 실험: 8MB도 50,000단계에서 실패) | 깊이 상한, 반복문 + 명시적 스택 |
| `GC overhead limit exceeded`에 `-XX:-UseGCOverheadLimit` | 죽는 시점만 늦어진다 | 바닥선 추세 + 힙 덤프로 붙잡는 쪽 |
| 정규식 CPU 100%에 인스턴스만 늘림 | 같은 입력이 새 인스턴스도 같은 방식으로 묶는다(해석) | 규칙 끄기·롤백, 입력 길이 상한, 패턴·엔진 교체 |
| async 정지에 루프·캐리어 수를 늘림 | 막는 코드가 그대로면 늘린 쪽도 막힌다(해석) | 블로킹·계산을 루프 밖으로 |
| "릴리스만 이상하다"를 컴파일러 버그로 단정 | 대개 UB다 | UBSan·ASan, `-O0`/`-O2` 결과 비교 |

## 쓰이는 자료구조·알고리즘

- **역색인**: 증상(키) → leaf 목록. 이 노트 자체가 손으로 만든 역색인이다([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
- **결정 트리**: 각 절의 트리는 "가장 싼 관찰로 후보를 반으로 가르는" 순서다. 예외 이름 → 맨 위 프레임 → 시점(기동 직후/며칠 뒤) → 옵션·빌드 플래그 → 재현 측정 순으로 비용이 커진다.
- **두 배 실험**: 입력 길이·중첩 깊이·스레드 수 하나만 바꿔 시간 비율을 본다. 한 글자에 2배면 지수 백트래킹(02), 깊이 상한을 넘는 지점에서 갑자기 실패면 재귀(03). 같은 방법은 [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) 1·4절.
- **그래프 순회**: GC 도달성(10), 네이티브 이미지 도달성 분석(24), 의존성 해석과 역방향 영향 범위(19, [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md), [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md))는 모두 "루트에서 닿는가"를 묻는다. 증상이 "있어야 할 것이 없다"(1절)·"없어야 할 것이 남는다"(5절)이면 그 그래프의 루트와 간선을 본다.
- 관련 색인: [os/37](../../os/37-os-symptom-index/2-summary.md)(종료 코드·errno) · [architecture/22](../../architecture/22-arch-symptom-index/2-summary.md)(신호·표현) · [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md)(복잡도·재귀·정규식) · [data-structure/43](../../data-structure/43-ds-symptom-index/2-summary.md) · [reliability/52](../../reliability/52-reliability-symptom-index/2-summary.md)(운영 지표) · [security/29](../../security/29-security-symptom-index/2-summary.md)(공격 관점) · [network/52](../../network/52-network-symptom-index/2-summary.md) · [database/56](../../database/56-db-symptom-index/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

```text
  ① 원문 보존     예외 전체(Caused by까지), 맨 위 프레임, 같은 예외의 첫 발생 로그
  ② 실행체 고정   JVM 판·옵션(jcmd VM.flags), 클래스 출처(-verbose:class), 빌드 플래그·심볼(DW_AT_producer)
  ③ 시점 고정     기동 직후 / 몇 분 / 며칠, 배포·기능 플래그·트래픽 변화 시각
  ④ 절 고르기     0절의 표로 단계를 고른다 (링크 / 타입 / 값 / 스택 / 메모리 / CPU / async / 공유 / UB / 바인딩 / 의존성)
  ⑤ 첫 확인       그 절 표의 "첫 확인" 한 가지로 후보를 줄인다
  ⑥ leaf로        원인이 하나로 줄면 leaf의 대처를 따른다. 줄지 않으면 ⑤의 다음 확인
```

### 2. 첫 확인 명령 모음

```bash
# 링크·로딩 (1절)
java -verbose:class -cp ... App 2>&1 | grep 'com.x.Money'        # 클래스가 어느 jar에서 왔나
javap -c -cp lib.jar com.b.B | grep invoke                      # 호출 지점이 기대한 서술자
mvn dependency:tree -Dincludes=com.x:money; npm ls money; go mod why -m example.com/money
# 타입 (2절)
javac -Xlint:unchecked -Xlint:finally ...                       # 소거 오염·finally 안 return 경고
# 스택·스레드 (3·4·7절)
jcmd <pid> Thread.print | grep -A3 'ForkJoinPool\|regex'          # 맨 위 프레임 세기
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json   # 가상 스레드 포함(JEP 444)
java -Djdk.tracePinnedThreads=short ...                         # JDK 21 pinning
# 메모리·GC (5절)
java -Xlog:gc*:file=gc.log ... ; jcmd <pid> GC.class_histogram | head
java -XX:+PrintFlagsFinal -version | grep -E 'MaxHeapSize|UseCompressedOops|MaxRAMPercentage'
# JIT (6절)
java -XX:+PrintCompilation ... | grep 'made not entrant'
java -Xlog:deoptimization=debug ... ; jcmd <pid> VM.flags; jcmd <pid> Compiler.codecache
# 네이티브 빌드 (6·9절)
objdump -d app | less; readelf -S app | grep debug; size app
gcc -O2 -g -fsanitize=address,undefined ...; gcc -O2 -fsanitize=thread ...
# Python·Node (4·5·6·7절)
python -X importtime -c 'import app' 2>&1 | tail; python -c 'import gc; print(gc.isenabled(), gc.get_count())'
node --expose-gc app.js                                          # heapUsed 차이로 누수 확인
```

- 위 명령의 출력 읽기와 실측 값은 해당 leaf의 「적용」에 있다. 이 목록은 "어느 leaf로 갈지"를 고르는 첫 확인용이다.

### 실험: JDK 21에서 각 증상의 첫 줄 (`msg/Symptoms.java`·`msg/run.sh`)

색인의 "보이는 것" 칸이 이 JDK에서 실제로 어떤 문구인지, 그리고 **스택 맨 위 프레임이 어디를 가리키는지**를 한 번에 확인했다.

```java
show("CCE", () -> { List raw = new ArrayList(); raw.add(42); List<String> s = raw; String x = s.get(0); });
show("NPE", () -> { Map<String, String> m = new HashMap<>(); String v = m.get("user_001"); v.length(); });
show("ASE", () -> { Object[] arr = new String[1]; arr[0] = 1; });
show("SOE", () -> { depth = 0; recurse(); });
show("STREAM", () -> { Stream<Integer> st = Stream.of(1, 2, 3); st.count(); st.toList(); });
show("REGEX-SOE", () -> { Pattern.compile("(a|b)*").matcher("ab".repeat(5000)).matches(); });
// NoSuchMethodError: Caller를 money 2.0(fmt(long, String) 있음)에 맞춰 컴파일하고 1.0으로 실행
```

(실험, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`, 소스 실행기 `java Symptoms.java` 3회 + 사실 점검 재실행 3회, 2026-10-08)

```text
CCE -> java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String
       (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
       | frames=8 | top=Symptoms.lambda$main$0(Symptoms.java:21)
NPE -> java.lang.NullPointerException: Cannot invoke "String.length()" because "<local1>" is null
       | frames=8 | top=Symptoms.lambda$main$1(Symptoms.java:22)
ASE -> java.lang.ArrayStoreException: java.lang.Integer | frames=8
SOE -> java.lang.StackOverflowError: null | frames=1024 | top=Symptoms.recurse(Symptoms.java:7)
       recursion depth reached = 21098 / 21622 / 21168          (3회; 재실행 21201 / 21273 / 21948)
STREAM -> java.lang.IllegalStateException: stream has already been operated upon or closed | frames=12
REGEX-SOE -> java.lang.StackOverflowError: null | frames=1024
       top = Pattern$GroupTail.match / Pattern$GroupHead.match / Pattern$Branch.match   (3회가 모두 다름;
             재실행 Pattern$BmpCharProperty.match / Pattern$GroupHead.match / Pattern$Branch.match)
REGEX-OK  [ab]* 에 100,000자 -> (no exception)

== NoSuchMethodError
money 2.0으로 실행:  1000 KRW
money 1.0으로 실행:  Exception in thread "main" java.lang.NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'
money 없이 실행:     Exception in thread "main" java.lang.NoClassDefFoundError: com/x/Money
                     Caused by: java.lang.ClassNotFoundException: com.x.Money
```

- 관찰 1 — CCE의 맨 위 프레임은 **꺼낸 줄**(21번 줄의 `s.get(0)` 대입)이었다. 정수를 넣은 `raw.add(42)`는 같은 줄이라 여기서는 구별되지 않지만, 05 실험 C처럼 넣는 코드가 다른 모듈이면 트레이스에 나타나지 않는다.
- 관찰 2 — NPE는 JEP 358 상세 메시지로 null이었던 식(`String.length()`의 수신자)을 보였다. `<local1>`은 클래스 파일에 지역 변수 표가 없어서다. JEP 358: 변수 이름은 지역 변수 표가 있을 때(`javac -g`)만 쓰고, 없으면 `<local i>`·`<parameter i>`로 적는다(08 실험의 `<parameter1>`과 같은 이유). JDK 21 `globals.hpp`의 `ShowCodeDetailsInExceptionMessages` 기본값이 `true`라 옵션 없이 나왔다.
- 관찰 3 — `StackOverflowError`는 메시지가 `null`이고 트레이스가 1,024프레임에서 잘렸다. 단순 재귀의 깊이는 같은 프로그램에서도 21,098~21,948(6회)로 실행마다 달랐다. 정규식 SOE는 맨 위 프레임이 실행마다 `GroupTail`·`GroupHead`·`Branch`·`BmpCharProperty`로 바뀌었다. **맨 위 한 줄이 아니라 반복되는 프레임 무리**로 판정해야 하는 이유다.
- 관찰 4 — `NoSuchMethodError`의 메시지는 컴파일 때 기록된 **서술자 전체**(반환 타입·인자 타입)다. 이름만 같고 인자가 다른 판이 올라왔다는 것을 문구만으로 알 수 있다. 같은 결과는 19 실험 1에도 있다.

## 장애 시나리오와 대처

이 노트의 시나리오는 **색인을 잘못 읽는** 경우다. 개별 원인의 대처는 각 leaf에 있다.

### 1. CCE를 꺼낸 줄에서 고침 — 원인 위치와 증상 위치를 혼동

- **현상**: `ClassCastException` 핫픽스(`(String) String.valueOf(o)`)를 배포했는데, 며칠 뒤 다른 집계에서 같은 예외가 난다.
- **보이는 형태**: 스택 맨 위가 매번 다른 "꺼내는" 줄이다. 데이터에는 정수가 섞인 리스트가 계속 생긴다.
- **원인**: 원시 타입 `List`로 넣는 오래된 모듈이 그대로다. 소거 때문에 실행 중 검사는 꺼낼 때만 있다([05-1](../05-type-systems/2-summary.md)).
- **대처**: 넣는 순간을 잡는다(`Collections.checkedList`로 임시 감싸기, `-Xlint:unchecked` 경고 0). 위 실험 관찰 1처럼 맨 위 프레임은 증상 위치일 뿐이다.

### 2. 스택 없는 NPE·SOE의 맨 위 한 줄로 원인을 단정

- **현상**: 장애 분석 회의에서 "로그에 위치가 없으니 재현될 때까지 보류"로 결론냈다. 또는 SOE 트레이스 맨 위가 `Pattern$GroupTail.match`라 "JDK 버그"로 판정했다.
- **보이는 형태**: NPE는 스택 0줄·메시지 `null`. SOE는 1,024프레임에서 잘린 트레이스.
- **원인**: NPE 스택은 `OmitStackTraceInFastThrow`가 생략했다([08-4](../08-error-handling-models/2-summary.md)). SOE의 맨 위 프레임은 실행마다 바뀌고(위 실험 관찰 3), 원인은 반복되는 무리(정규식 재귀 — [02-2](../02-lexing-and-regular-languages/2-summary.md))와 입력 길이에 있다.
- **대처**: 기동 직후의 첫 발생 로그를 찾는다. SOE는 반복되는 프레임 무리로 갈래를 고르고(4절), 실패 입력의 길이·깊이를 기록한다.

### 3. "GC 문제"를 수집기 옵션으로만 풂

- **현상**: `GC overhead limit exceeded` 뒤 수집기를 G1으로 바꿨더니 메시지가 `Java heap space`로 바뀌었고 장애는 그대로다.
- **보이는 형태**: Full GC 뒤 바닥선이 회차마다 오른다. 10 실험 2에서도 같은 누수가 Parallel에서는 `GC overhead limit exceeded`, G1에서는 `Java heap space`로 죽었다.
- **원인**: 메시지는 수집기의 판정 방식이고, 원인은 산 데이터 증가(static 컬렉션·무한 큐 — [10-3](../10-garbage-collection/2-summary.md)·[16-1](../16-concurrency-design-patterns/2-summary.md))다.
- **대처**: 바닥선 추세로 누수인지(오름)·힙 부족인지(평평)를 먼저 가르고, 오르면 힙 덤프의 지배자 트리로 붙잡는 필드를 찾아 확정한다. 수집기 선택은 그다음이다([11](../11-gc-tuning-and-gc-logs/2-summary.md)).

### 4. "모든 API가 느리다"를 트래픽 증가로 읽고 증설

- **현상**: 무관한 API까지 같이 느려져 인스턴스를 두 배로 늘렸는데 개선이 없다.
- **보이는 형태**: 인스턴스마다 코어 하나만 100%(이벤트 루프), 또는 `ForkJoinPool.commonPool-worker-*`가 전부 소켓 읽기 중. 요청 수는 평소와 같다.
- **원인**: 공유 실행 자원 하나가 막혔다 — 루프 위 동기 계산([14-1](../14-concurrency-models/2-summary.md)), 공용 풀 블로킹([16-2](../16-concurrency-design-patterns/2-summary.md)), 또는 정규식 백트래킹([02-1](../02-lexing-and-regular-languages/2-summary.md)).
- **대처**: 요청 수와 지연의 상관부터 본다. 요청 수가 같은데 다 느리면 증설보다 **막는 코드**를 찾는다(7절 첫 확인). 정규식이면 그 입력이 새 인스턴스도 묶는다.

### 5. 배포 직후 p99를 코드 회귀로 오인해 롤백

- **현상**: 배포마다 1~몇 분 p99가 튀어 매번 롤백 여부를 논의한다. 롤백해도 같은 모양이 난다.
- **보이는 형태**: 새 파드에서만, 시작 직후에만, 시간이 지나면 저절로 가라앉는다. `PrintCompilation`에 컴파일이 몰려 있다.
- **원인**: JIT 워밍업 전 구간이다([01-1](../01-compile-interpret-jit/2-summary.md)·[23-1](../23-jit-tiered-compilation-and-warmup/2-summary.md)). 롤백한 판도 같은 JVM에서 같은 워밍업을 겪는다.
- **대처**: 새 파드의 시작 후 경과 시간별 p99를 따로 본다. 예열 후 readiness·가중치 증가로 줄이고, 시작 비용은 CDS·AppCDS(JDK 24+면 AOT 캐시, JEP 483)로 줄인다. 시작 후에도 계속 느리면 그때 코드 회귀를 본다.

## 핵심 문장

- 언어·런타임 증상은 대개 "컴파일할 때 본 세계와 실행할 때의 세계가 다를 때" 보인다. 첫 질문은 "그 줄을 실행한 것이 정확히 무엇이었나(어떤 jar·옵션·빌드·몇 번째 실행)"다.
- `NoSuchMethodError`의 메시지는 컴파일 때 기록된 서술자 전체다. 이름이 같고 인자가 다른 판이 실행 경로에 올라왔다는 뜻이며, `-verbose:class`로 실제 jar를 본다.
- Java `ClassCastException`의 맨 위 프레임은 대개 꺼낸 곳이다. 제네릭 소거 때문에 원인(넣은 곳)은 트레이스에 없을 수 있다.
- 스택 없는 NPE는 원인 불명이 아니라 생략된 것이다. `StackOverflowError`는 맨 위 한 줄이 아니라 반복되는 프레임 무리와 입력 깊이로 판정한다.
- `GC overhead limit exceeded`·`Java heap space`는 같은 누수의 다른 문구일 수 있다. GC 뒤 바닥선이 오르는지를 먼저 본다.
- 무관한 요청까지 같이 느리면 공유 실행 자원(이벤트 루프·캐리어·공용 풀)이 막힌 것이다. 증설보다 막는 코드를 찾는다.

## 관련 주제·근거

- 이 영역 leaf(시나리오 번호는 각 노트의 「장애 시나리오와 대처」)
  - 실행 모델·파이프라인: [01](../01-compile-interpret-jit/2-summary.md) · [02](../02-lexing-and-regular-languages/2-summary.md) · [03](../03-parsing-grammars-ast/2-summary.md) · [04](../04-semantic-analysis-and-scopes/2-summary.md) · [22](../22-ir-and-optimization/2-summary.md)
  - 타입·값·추상화: [05](../05-type-systems/2-summary.md) · [06](../06-values-references-passing/2-summary.md) · [07](../07-scope-closures-first-class-functions/2-summary.md) · [08](../08-error-handling-models/2-summary.md) · [17](../17-dispatch-and-polymorphism-mechanics/2-summary.md) · [18](../18-functional-concepts/2-summary.md)
  - 메모리: [09](../09-memory-management-models/2-summary.md) · [10](../10-garbage-collection/2-summary.md) · [11](../11-gc-tuning-and-gc-logs/2-summary.md) · [12](../12-object-layout-and-allocation-reduction/2-summary.md) · [13](../13-language-memory-model/2-summary.md)
  - 런타임 성능: [23](../23-jit-tiered-compilation-and-warmup/2-summary.md) · [24](../24-aot-native-image-and-startup/2-summary.md) · [25](../25-lto-pgo-and-binary-size/2-summary.md)
  - 동시성: [14](../14-concurrency-models/2-summary.md) · [15](../15-gil-and-runtime-constraints/2-summary.md) · [16](../16-concurrency-design-patterns/2-summary.md)
  - 빌드·생태계·선택: [19](../19-modules-and-dependency-resolution/2-summary.md) · [20](../20-undefined-behavior-and-memory-safety/2-summary.md) · [21](../21-language-choice-tradeoffs/2-summary.md)
  - 후속: [27-pl-incidents](../27-pl-incidents/2-summary.md) — 이 색인의 증상(9절 누출, 11절 설치 실패, 6절 정규식 CPU)이 실제 사고가 된 사건
- 다른 영역 색인: [os/37](../../os/37-os-symptom-index/2-summary.md) · [architecture/22](../../architecture/22-arch-symptom-index/2-summary.md) · [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) · [data-structure/43](../../data-structure/43-ds-symptom-index/2-summary.md) · [reliability/52](../../reliability/52-reliability-symptom-index/2-summary.md) · [security/29](../../security/29-security-symptom-index/2-summary.md) · [network/52](../../network/52-network-symptom-index/2-summary.md) · [database/56](../../database/56-db-symptom-index/2-summary.md)
- 근거
  - 각 행의 수치·메시지는 해당 leaf의 실험·출처에서 옮겼다(원 출처는 그 노트의 「관련 주제·근거」 — JLS·JVMS SE21, `java` 도구 문서, HotSpot GC 튜닝 가이드, JEP 358·444·483, OpenJDK jdk21u 소스, N1570, GraalVM·Spring 문서, GCC·LLVM 문서).
  - JEP 358 "Helpful NullPointerExceptions"(Release 14) <https://openjdk.org/jeps/358> — 위 실험의 NPE 문구 형식, 지역 변수 표가 없을 때의 `<local i>` 표기
  - OpenJDK jdk21u `src/hotspot/share/runtime/globals.hpp` — `OmitStackTraceInFastThrow`(기본 `true`), `MaxJavaStackTraceDepth`(기본 1024), `ShowCodeDetailsInExceptionMessages`(기본 `true`)
  - 이 노트의 실험
    - `msg/Symptoms.java`·`msg/run.sh` — CCE·NPE·ASE·SOE·스트림 재사용·정규식 SOE의 첫 줄과 맨 위 프레임, `NoSuchMethodError`·`NoClassDefFoundError` 재현(`eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`, 3회 + 사실 점검 재실행 3회, 2026-10-08)
