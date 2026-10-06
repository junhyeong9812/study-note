# engineering-practice/07-build-systems-and-reproducibility — 빌드 = 입력 해시로 산출물을 고르는 DAG: 증분 빌드·캐시·재현 가능 빌드 — 정리 (힌트)

## 해결하는 문제

빌드 시스템이 없거나 허술하면 세 가지를 동시에 못 얻는다.

```text
  빠르게              정확하게                    똑같이
  바뀐 것만 다시      옛 산출물을 쓰지 않게        같은 소스 → 같은 바이트
  (증분·캐시)         (캐시 오염 없음)             (재현 가능 빌드)
        \                 |                       /
         └── 셋 다 "산출물이 어떤 입력에서 나왔나"를 정확히 아는 데서 나온다 ──┘
```

- 매번 전부 다시 빌드하면 정확하지만 느리다. 바뀐 것만 다시 빌드하면 빠르지만, "바뀐 것"을 잘못 판정하면 옛 산출물이 섞인다.
- 같은 소스에서 빌드할 때마다 다른 바이트가 나오면, 누구나 다시 빌드해 바이트를 대조하는 방식으로는 배포된 바이너리가 그 소스에서 나왔는지 확인할 수 없다.
  - 남는 길은 빌드 서비스가 서명한 출처 증명(SLSA provenance) 검증이다. 이것은 "그 빌더를 믿는" 다른 방식이다(SLSA "Verifying artifacts").

쉬운 예: 요리 레시피와 반찬통이다.
- 레시피·재료가 같으면 어제 만든 반찬을 꺼내 써도 된다(캐시).
- 그런데 "소금 양"을 반찬통 라벨에 안 적었다. 싱겁게 바꿨는데 라벨이 같으니 어제의 짠 반찬을 꺼낸다(캐시 오염).

똑같은 구조다.\
라벨 = 캐시 키, 재료·레시피 = 빌드 입력, 반찬 = 산출물이다.

실무 예:
- 로컬에선 테스트가 통과하는데 CI에선 실패한다. 시간대·로캘·도구 버전이 숨은 입력이었다.
- 빌드 캐시가 스테이징 설정으로 만든 번들을 운영 빌드에 재사용한다.
- 같은 태그를 두 번 빌드했더니 jar 해시가 다르다. 어느 쪽이 배포됐는지 증명할 수 없다.

## 동작·원리

### 1. 빌드 = 의존 DAG + 위상정렬

```text
  모듈 의존 (화살표 = "이것에 의존")          빌드 순서(위상정렬)
     app ──> api ──> domain ──> util          util → domain → api → service → app
      └────> service ──┘ └─────> util
                       (service → util 도)
  util이 바뀌면 다시 빌드할 후보 = util에서 "역방향"으로 도달하는 모든 모듈
```

- 빌드 도구는 모듈·작업 사이 의존을 그래프로 보고, 의존이 먼저 오도록 위상정렬한다. 순환이 있으면 순서를 정할 수 없어 오류를 낸다.
- *증분 빌드(incremental build)*: 바뀐 입력에 영향받는 부분만 다시 빌드하는 것. 영향 범위(다시 빌드할 후보) = 바뀐 노드의 후손(역방향 의존) 집합이다.
  - 후보 전부를 실제로 다시 컴파일하는지는 도구마다 다르다. Gradle은 의존 모듈이 ABI 호환으로만 바뀌면(메서드 본문만 수정 등) 하위 모듈 컴파일을 건너뛴다(Gradle 문서 "Java Plugin" — Compilation avoidance).

### 2. "바뀌었나"를 판정하는 두 방식 — 시각 vs 내용 해시

```text
  시각 비교 (make)                         내용 해시 (Docker COPY 캐시*, Bazel 원격 캐시 등)
  target이 prerequisite보다 오래됐나?       key = hash(모든 입력) 가 전에 본 값인가?
  - touch만 해도 다시 빌드 (헛빌드)          - 내용이 같으면 시각이 달라도 재사용
  - 시각이 거꾸로 가면 못 알아챔 (옛 산출물)   - 입력을 key에서 빠뜨리면 옛 산출물 (오염)
```

- 시각 비교는 싸지만 시각을 믿는다. 아래 실험처럼 시각만 바꾸면 헛빌드, 시각을 과거로 되돌리면 놓친다.
- 내용 해시는 내용을 믿는다. 대신 **무엇을 입력으로 셀지**가 정확해야 한다. 빠진 입력이 있으면 오염된다(아래 실험).
- \*Docker `COPY`는 순수 내용 해시가 아니다. Docker 문서("Build cache invalidation"): `COPY`·`ADD`는 파일 메타데이터로 캐시 체크섬을 계산하되 "the modification time of a file (`mtime`) is not taken into account". → [08](../08-container-image-optimization/2-summary.md).

#### 실험: make의 시각 비교 — 헛빌드와 놓침

```makefile
out.txt: in.txt
	cp in.txt out.txt
```

(실험, GNU Make 4.3 / Linux, 2026-10-05 — `scratchpad/ep/06/e10-make/`)

```text
== 1 (첫 빌드)
cp in.txt out.txt
== 2 (변경 없음)
make: 'out.txt' is up to date.
== 3 (내용 그대로, touch만)
cp in.txt out.txt
== 4 (내용을 b로 바꾸고 mtime을 2000-01-01로)
make: 'out.txt' is up to date.
out.txt = a
```

- 3: 내용이 같은데 다시 했다(헛빌드). 4: 내용이 바뀌었는데 안 했다 → 산출물은 옛 값 `a`.
- 4가 실무에서 생기는 길(해석): 시각을 보존하는 복사·압축 해제(`cp -p`, `tar` 추출), CI 캐시 복원으로 산출물이 소스보다 "새것"으로 보일 때.

### 3. 작업 기반 vs 산출물 기반 — SWE@G 18장의 분류

| | 작업 기반(task-based) | 산출물 기반(artifact-based) |
|---|---|---|
| 기본 단위 | 작업 = 임의의 스크립트 | 산출물 = 선언된 입력 → 출력 |
| 예(SWE@G의 분류) | Ant, Maven, Gradle, Grunt, Rake | Blaze/Bazel, Pants, Buck |
| 증분·캐시 | 작업이 무엇을 읽는지 도구가 다 알 수 없어 어렵다 | 입력이 선언돼 있어 해시로 판정 |
| 도구(컴파일러) | 기계에 깔린 것 | 도구도 의존으로 선언(Bazel) |

- SWE@G 18장(Erik Kuefler, Google 관례·저자 주장): "Most major build systems in use today, such as Ant, Maven, Gradle, Grunt, and Rake, are task based." 작업 기반은 임의 코드를 허용하므로 "the system can't have enough information to always be able to run builds quickly and correctly"라고 본다.
- Gradle에도 작업 입력·출력 선언과 빌드 캐시가 있다. Gradle 문서("Build Cache"): "Since a task describes all of its inputs and outputs, Gradle can compute a build cache key that uniquely defines the task's outputs based on its inputs." 위 표는 SWE@G 저자의 분류이고, 실제 도구는 그 사이 어딘가에 있다(해석).
- SWE@G 18장, 원격 캐시의 조건: "the same set of inputs will produce exactly the same output on any machine". 캐시 항목은 "keyed on both its target and a hash of its inputs".
  - *밀폐성(hermeticity)*: 빌드 단계가 선언한 입력만 볼 수 있게 하는 성질. SWE@G는 Bazel의 샌드박스가 "each action can see only a restricted view of the filesystem that includes the inputs it has declared"라고 쓴다.

### 4. 재현 가능 빌드 — 같은 입력이면 같은 바이트

```text
  소스 + 빌드 환경 + 빌드 절차 ──> 산출물 바이트
          같다                       같아야 한다 (bit-by-bit)
  흔한 비결정 요인:  현재 시각(아카이브 엔트리 시각) · 파일 나열 순서 · 빌드 경로 · 사용자 이름
                    · 로캘·시간대 · 도구(JDK) 메이저 버전 · 줄 끝(CRLF/LF) · 범위 버전 의존성
```

- reproducible-builds.org 정의: "Given the same source code, build environment and build instructions, any party can recreate bit-by-bit identical copies of all specified artifacts."
- *SOURCE_DATE_EPOCH*: 빌드 도구가 현재 시각 대신 쓰도록 배포판이 설정하는 표준 환경 변수. 값은 "the last modification of something, usually the source code"를 Unix epoch 초로 나타낸다(reproducible-builds.org "SOURCE_DATE_EPOCH" 문서. 형식 규칙은 같은 사이트의 spec).
- Maven: `pom.xml`에 `project.build.outputTimestamp` 속성을 두면 재현 가능 모드가 켜진다(Maven 가이드 "Configuring for Reproducible Builds"). 플러그인이 지원해야 한다. `mvn artifact:check-buildplan`으로 업그레이드할 플러그인을 확인하고, `mvn clean verify artifact:compare`로 검증한다. 가이드는 Maven 4.0.0-beta-5부터 기본으로 켜진다고 쓴다.
- 같은 가이드가 꼽는 남는 차이: JDK 메이저 버전(바이트코드가 달라짐), 줄 끝, 의존성 버전 범위, 사용자 이름·현재 디렉터리 같은 환경 누출.

#### 실험: 타임스탬프가 jar 해시를 바꾼다

(실험, maven:3.9-eclipse-temurin-21 — Maven 3.9.16, JDK 21.0.11, maven-jar-plugin 3.5.1 고정, `--network none`, 2026-10-05 — `scratchpad/ep/06/e6-repro/`)\
같은 소스를 `clean package`로 두 번, 빌드 사이 3초를 두고 만든 jar의 sha256 앞 16자:

```text
== outputTimestamp 없음 (빌드 사이 3초)
bf0b98304c05ce73
aeeff60013ea9cfc
== outputTimestamp 고정
f418ea6b2a18687e
f418ea6b2a18687e
== 엔트리 시각 비교
     0 Sun Oct 04 17:08:58 UTC 2026 META-INF/
    99 Sun Oct 04 17:08:58 UTC 2026 META-INF/MANIFEST.MF
     0 Sun Oct 04 17:08:56 UTC 2026 ex/
...
     0 Thu Jan 01 00:00:00 UTC 2026 META-INF/
    99 Thu Jan 01 00:00:00 UTC 2026 META-INF/MANIFEST.MF
     0 Thu Jan 01 00:00:00 UTC 2026 ex/
```

- 고정하지 않은 쪽 해시는 실행마다 다르다(앞선 실행에서는 `2f10c8ba10137277`·`e66553ea24a658f3`, 약 30분 뒤 재실행에서는 `e88518d13fa9bd3b`·`aae503d6e5b71139`). 고정한 쪽은 별도 실행 세 번 모두 `f418ea6b2a18687e`였다.
- 차이는 jar(zip) 엔트리에 기록된 시각뿐이다. 고정하지 않은 두 jar를 풀어 `diff -r`하면 내용이 같았고, `cmp`의 첫 차이는 11번째 바이트(첫 엔트리 로컬 헤더의 수정 시각 필드)였다.
- Maven 없이 `jar` 도구만으로도 같다(eclipse-temurin:21-jdk): `jar --create` 두 번 → `92423953837bf05d` / `f780cfc4647dca8a`, `jar --date=2026-01-01T00:00:02Z` 두 번 → `535c9689be4535b0` 두 번.

## 쓰이는 자료구조·알고리즘

- **DAG + 위상정렬(Kahn)** — 빌드 순서. 진입 차수 0부터 꺼내고, 남은 노드가 있으면 순환 → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)(위상정렬 절).
- **역방향 도달 집합** — "이게 바뀌면 무엇을 다시 빌드하나". Maven `-pl X -amd`(also-make-dependents)가 이 집합이다.
- **콘텐츠 해시 캐시 키** — key = H(소스, 의존 산출물 해시, 도구 버전, 플래그, 환경 입력). 해시맵 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **Merkle 구조** — 상위 산출물 키에 하위 산출물 해시가 들어가면, 맨 아래 하나만 바뀌어도 위 키가 연쇄로 바뀐다 → [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md). git 객체도 같은 구조다 → [03](../03-version-control-and-git-internals/2-summary.md).

### 실험: 위상정렬 직접 구현 vs Maven reactor

```java
// BuildTopo.java 핵심 — deps: 모듈 -> 의존 모듈
deps.forEach((m, ds) -> { indeg.put(m, ds.size());
    for (String d : ds) dependents.computeIfAbsent(d, k -> new ArrayList<>()).add(m); });
Deque<String> q = new ArrayDeque<>();
indeg.forEach((m, d) -> { if (d == 0) q.add(m); });
while (!q.isEmpty()) { String m = q.poll(); order.add(m);
    for (String x : dependents.getOrDefault(m, List.of()))
        if (indeg.merge(x, -1, Integer::sum) == 0) q.add(x); }
if (order.size() < deps.size()) System.out.println("CYCLE: not orderable " + left);
```

(실험, eclipse-temurin:21-jdk `java BuildTopo.java` / Maven 3.9.16 `mvn -o validate`, 2026-10-05 — `scratchpad/ep/06/e4-topo/`)

```text
build order = [util, domain, api, service, app]
util changed -> rebuild [util, service, domain, app, api]
api changed  -> rebuild [api, app]
CYCLE: not orderable [app, api, service, util, domain]
```

```text
[INFO] Reactor Build Order:
[INFO] 
[INFO] root                                                               [pom]
[INFO] util                                                               [jar]
[INFO] domain                                                             [jar]
[INFO] api                                                                [jar]
[INFO] service                                                            [jar]
[INFO] app                                                                [jar]
```

`-pl <모듈> -amd`(그 모듈과, 그것에 의존하는 모듈만)로 빌드할 때 Maven이 고른 모듈(출력에서 모듈 줄만 grep):

```text
== -pl util -amd
[INFO] util                                                               [jar]
[INFO] domain                                                             [jar]
[INFO] api                                                                [jar]
[INFO] service                                                            [jar]
[INFO] app                                                                [jar]
== -pl api -amd
[INFO] api                                                                [jar]
[INFO] app                                                                [jar]
```

- `util`에 `app` 의존을 넣어 순환을 만들면 Maven은 이렇게 멈춘다:

```text
[ERROR] [ERROR] The projects in the reactor contain a cyclic reference: Edge between 'Vertex{label='ex:util:1'}' and 'Vertex{label='ex:app:1'}' introduces to cycle in the graph ex:app:1 --> ex:service:1 --> ex:util:1 --> ex:app:1 @ 
```

- 직접 구현과 Maven의 순서가 이 그래프에서는 같았다. 위상정렬 결과는 하나가 아닐 수 있다(api와 service는 서로 의존하지 않아 순서가 바뀌어도 맞다).

## 적용 — 풀어나가는 법

### 1. 모든 입력을 드러낸다

- 숨은 입력 후보를 점검한다: 시간대·로캘, 환경 변수, 도구 버전(JDK·Node), OS 패키지, 네트워크에서 받는 것(범위 버전 의존성), 현재 시각.
- 코드에서 기본값에 기대지 않는다.

```java
// 숨은 입력: 기본 시간대·기본 로캘
String day = LocalDate.ofInstant(t, ZoneId.systemDefault()).toString();
String amount = String.format("%.1f", 1.5);
// 드러낸 입력
String day2 = LocalDate.ofInstant(t, ZoneId.of("Asia/Seoul")).toString();
String amount2 = String.format(Locale.ROOT, "%.1f", 1.5);
```

#### 실험: 같은 코드, 환경만 다르게

(실험, eclipse-temurin:21-jdk, `-e TZ=…`와 `-Duser.language/-Duser.country`만 바꿈, 2026-10-05 — `scratchpad/ep/06/e7-envdep/EnvDep.java`, 기준 시각 2026-10-04T20:00:00Z)

```text
## TZ=Asia/Seoul -Duser.language=ko -Duser.country=KR
zone=Asia/Seoul locale=ko_KR day=2026-10-05 amount=1.5 -> test PASS
  explicit zone/locale -> day=2026-10-05 amount=1.5
## TZ=UTC -Duser.language=en -Duser.country=US
zone=UTC locale=en_US day=2026-10-04 amount=1.5 -> test FAIL
  explicit zone/locale -> day=2026-10-05 amount=1.5
## TZ=Asia/Seoul -Duser.language=de -Duser.country=DE
zone=Asia/Seoul locale=de_DE day=2026-10-05 amount=1,5 -> test FAIL
  explicit zone/locale -> day=2026-10-05 amount=1.5
```

- 개발자 PC(서울)에서는 통과, UTC CI에서는 날짜가 하루 밀려 실패, 독일 로캘에서는 소수점이 쉼표라 실패. 입력을 명시한 줄은 세 환경 모두 같다.
- 곁가지 관찰: 이 컨테이너에서 `LANG=de_DE.UTF-8`만 주면 기본 로캘이 `en_US`로 남았다. 이 이미지의 `locale -a`에는 `C`·`C.utf8`·`en_US.utf8`·`POSIX`만 있어 de_DE가 설치돼 있지 않다. 그래서 로캘은 JVM 속성으로 바꿨다.

### 2. 캐시 키에 모든 입력을 넣는다

```java
// MiniBuild.java 핵심 — 설정(API_URL)을 산출물에 "굽는" 빌드
String key = keyMode.equals("src") ? sha(src) : sha(src + "\0API_URL=" + apiUrl);
if (Files.exists(cache.resolve(key))) artifact = Files.readString(cache.resolve(key));   // HIT
else { artifact = src.replace("${API_URL}", apiUrl); Files.writeString(cache.resolve(key), artifact); }
```

(실험, eclipse-temurin:21-jdk `java MiniBuild.java`, 2026-10-05 — `scratchpad/ep/06/e5-hashcache/`)

```text
== keyMode=src
MISS key=70af500bf94e  requested API_URL=https://staging.example.invalid  artifact -> const API = "https://staging.example.invalid";
HIT  key=70af500bf94e  requested API_URL=https://staging.example.invalid  artifact -> const API = "https://staging.example.invalid";
HIT  key=70af500bf94e  requested API_URL=https://prod.example.invalid  artifact -> const API = "https://staging.example.invalid";
== keyMode=src+conf
MISS key=19cceeffa18b  requested API_URL=https://staging.example.invalid  artifact -> const API = "https://staging.example.invalid";
HIT  key=19cceeffa18b  requested API_URL=https://staging.example.invalid  artifact -> const API = "https://staging.example.invalid";
MISS key=289c76ee06ca  requested API_URL=https://prod.example.invalid  artifact -> const API = "https://prod.example.invalid";
```

- 키에서 설정을 빠뜨리면 운영 빌드가 스테이징 산출물을 받는다. 오류도 경고도 없다. "HIT"는 성공처럼 보인다.
- CI 캐시를 설정할 때도 같다. 의존성 캐시 키에 잠금 파일 해시를, 산출물 캐시 키에 도구 버전·빌드 플래그를 넣는다.

### 3. Maven에서 재현 가능 빌드 켜기

```xml
<properties>
  <project.build.outputTimestamp>2026-01-01T00:00:00Z</project.build.outputTimestamp>
</properties>
<!-- 플러그인 버전을 고정한다. 기본 버전에 기대면 Maven 버전에 따라 결과가 바뀐다 -->
```

```bash
mvn artifact:check-buildplan            # 재현성을 지원하지 않는 플러그인 확인
mvn clean install
mvn clean verify artifact:compare       # 다시 빌드해 설치된 것과 비교
```

- 차이를 찾을 때는 Maven 가이드가 권하는 diffoscope로 두 산출물을 비교한다.
- 릴리스 태그의 커밋 시각을 `outputTimestamp`나 `SOURCE_DATE_EPOCH`로 쓰면, 같은 태그는 언제 빌드해도 같은 시각을 쓴다. reproducible-builds.org 문서도 git 저장소에서 `export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)`를 예로 든다.

### 4. 증분 빌드의 한계를 안다

(실험, Maven 3.9.16 + maven-compiler-plugin 3.15.0, 2026-10-05 — `scratchpad/ep/06/e9-stale/`)

실행 1 — 소스 2개(Hello·Legacy)로 빌드를 거듭하며, 매번 끝에 jar 안의 클래스 목록을 찍었다.

```text
== 1. 첫 빌드
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 2 source files with javac [debug release 21] to target/classes
[INFO] BUILD SUCCESS
ex/Legacy.class ex/Hello.class
== 2. 변경 없이 다시
[INFO] Nothing to compile - all classes are up to date.
[INFO] BUILD SUCCESS
ex/Legacy.class ex/Hello.class
== 3. Legacy.java 삭제 후 (clean 없이)
[INFO] Recompiling the module because of added or removed source files.
[INFO] Compiling 1 source file with javac [debug release 21] to target/classes
[INFO] BUILD SUCCESS
ex/Hello.class
```

실행 2 — Hello.java 한 파일만 고친 뒤, 그리고 Maven 없이 출력 폴더를 유지하는 손 스크립트로 같은 삭제를 했다(마지막 두 줄은 `ls out/ex`).

```text
== Hello.java 한 파일만 수정
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 2 source files with javac [debug release 21] to target/classes
== 손으로 짠 증분 스크립트: javac -d out (out 유지), Legacy.java 삭제
Hello.class
Legacy.class
```

- 이 버전의 Maven 컴파일러 플러그인은 기본 설정(`useIncrementalCompilation=true`)에서 모듈 안 파일 하나만 바뀌어도 **모듈 전체**를 다시 컴파일했다. 기본 모드의 증분 단위가 파일이 아니라 모듈이다.
- `useIncrementalCompilation=false`로 바꾸면 클래스 파일보다 새로운 소스만 컴파일한다. 플러그인 문서는 이 모드를 "not recommended"라 하고, 바뀐 클래스를 쓰는 다른 클래스는 다시 컴파일하지 않아 런타임 오류가 날 수 있다고 쓴다(compile-mojo 문서).

(실험, 같은 프로젝트·플러그인 3.15.0, `-Dmaven.compiler.useIncrementalCompilation=false`, 2026-10-05 — `scratchpad/ep/adj-06/e9-incr/`)

```text
== useIncrementalCompilation=false, Hello.java 한 파일만 수정
[INFO] Compiling 1 source file with javac [debug release 21] to target/classes
```
- 소스 삭제는 감지해 옛 클래스를 jar에 넣지 않았다. 반면 출력 폴더를 유지하는 손 스크립트는 지운 소스의 `.class`를 남긴다 — 운영에 옛 코드가 실려 나가는 길이다.

## 장애 시나리오와 대처

### 1. 로컬에선 되는데 CI에선 실패 (⚠ 환경 의존)

- 현상: 같은 커밋이 개발자 PC에서는 초록, CI에서는 빨강.
- 보이는 형태: 날짜·금액 문자열 비교 실패(위 실험의 `day=2026-10-04`, `amount=1,5`), "class file has wrong version", 특정 OS에서만 경로 구분자 오류.
- 원인: 기본 시간대·로캘·도구 버전·환경 변수가 선언되지 않은 입력이다.
- 대처: 코드에서 시간대·로캘을 명시. CI와 로컬의 도구 버전을 고정(툴체인·컨테이너 빌드). CI의 `TZ`·로캘을 일부러 다르게 돌리는 작업을 하나 둔다.

### 2. 캐시 오염 → 옛 산출물 배포 (⚠)

- 현상: 운영에 스테이징 설정이 박힌 번들이 나갔다. 수정한 코드가 반영되지 않았다.
- 보이는 형태: 빌드 로그는 "cache hit"·"up to date"뿐 오류 없음. 산출물 안에 옛 값이 있다.
- 원인: 캐시 키에서 입력(설정·플래그·도구 버전)이 빠졌다. 또는 시각 기반 판정이 복원된 산출물을 새것으로 봤다(위 make 실험 4).
- 대처: 키에 모든 입력을 넣는다. 릴리스 빌드는 깨끗한 환경에서 하거나 원격 캐시를 밀폐 빌드에만 쓴다. 의심되면 캐시 없이 다시 빌드해 해시를 비교한다.

### 3. 같은 소스, 다른 바이트 — 공급망 검증 불가

- 현상: 릴리스 jar를 다시 빌드하면 해시가 다르다.
- 보이는 형태: 위 실험의 `bf0b98…` / `aeeff6…`. diffoscope로 보면 엔트리 시각·파일 순서·빌드 경로 차이.
- 원인: 현재 시각, 파일 시스템 나열 순서, 빌드 경로, JDK 메이저 버전 차이.
- 대처: `project.build.outputTimestamp`/`SOURCE_DATE_EPOCH`, 플러그인 버전 고정, 같은 JDK 메이저, `artifact:compare`를 CI에 넣는다. 의미: 재현되면 "이 바이너리가 이 소스에서 나왔다"를 제3자가 확인할 수 있다 → [security/25-supply-chain-security](../../security/25-supply-chain-security/2-summary.md).

### 4. 순환 의존으로 빌드 불가

- 현상: 모듈 하나를 추가했더니 빌드가 시작도 안 된다.
- 보이는 형태: `The projects in the reactor contain a cyclic reference: … ex:app:1 --> ex:service:1 --> ex:util:1 --> ex:app:1`.
- 원인: 하위 모듈이 상위 모듈을 의존했다.
- 대처: 공통 부분을 새 하위 모듈로 빼거나 인터페이스를 하위로 옮겨 의존 방향을 한쪽으로(의존성 역전 → [software-design](../../software-design/README.md)).

### 5. 지운 코드가 산출물에 남음

- 현상: 삭제한 클래스·엔드포인트가 운영에서 여전히 동작한다.
- 보이는 형태: jar 안에 소스가 없는 `.class`. 위 손 스크립트 실험의 `Legacy.class`.
- 원인: 출력 폴더를 비우지 않는 증분 빌드가 삭제를 반영하지 않는다.
- 대처: 릴리스는 `clean` 빌드. 산출물 목록을 소스 목록과 대조하는 검사.

## 핵심 문장

- 빌드는 의존 DAG다. 순서는 위상정렬로, 다시 빌드할 후보는 바뀐 노드의 역방향 도달 집합으로 정한다.
- "바뀌었나"를 시각으로 보면 헛빌드와 놓침이 둘 다 생긴다. 내용 해시로 보면 정확하지만, 키에 모든 입력이 들어가야 한다.
- 캐시 키에서 입력 하나를 빠뜨리면 오류 없이 옛 산출물이 나온다. "HIT"는 정답을 뜻하지 않는다.
- 재현 가능 빌드는 같은 소스·환경·절차에서 비트 단위로 같은 산출물을 만든다. 가장 흔한 방해꾼은 현재 시각이다.
- Maven은 `project.build.outputTimestamp`로 엔트리 시각을 고정한다. 실험에서 두 빌드의 해시가 같아졌다.
- 로컬과 CI가 다르게 도는 것은 숨은 입력이 있다는 신호다. 시간대·로캘·도구 버전을 코드와 설정에 드러낸다.

## 관련 주제·근거

- 선행
  - [03-version-control-and-git-internals](../03-version-control-and-git-internals/2-summary.md) — 콘텐츠 주소·해시
  - language/19 modules-and-dependency-resolution — [language 영역](../../language/README.md)(미작성)
- 후속·연결
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) — 한 번 빌드한 산출물을 파이프라인으로 승격
  - [08-container-image-optimization](../08-container-image-optimization/2-summary.md) — 이미지 레이어 캐시(내용 해시, mtime 무시)
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
  - [testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md) — 환경 의존 테스트
  - [security 25 supply-chain-security](../../security/25-supply-chain-security/2-summary.md)
- 근거
  - SWE@G 18장 "Build Systems and Build Philosophy"(Erik Kuefler) — task-based(Ant·Maven·Gradle·Grunt·Rake) vs artifact-based(Blaze/Bazel·Pants·Buck), 타임스탬프 등 비결정 요소, 도구를 의존으로, 샌드박스, 원격 캐시 키(target + 입력 해시), "same set of inputs … exactly the same output", One-Version Rule <https://abseil.io/resources/swe-book/html/ch18.html>
  - reproducible-builds.org — Definition <https://reproducible-builds.org/docs/definition/> · SOURCE_DATE_EPOCH(정의·`git log -1 --pretty=%ct` 예) <https://reproducible-builds.org/docs/source-date-epoch/> · spec <https://reproducible-builds.org/specs/source-date-epoch/>
  - Apache Maven, "Configuring for Reproducible Builds" — `project.build.outputTimestamp`, `artifact:check-buildplan`·`artifact:compare`·`artifact:buildinfo`, 4.0.0-beta-5 기본, 남는 차이(JDK 메이저·줄 끝·버전 범위·환경 누출), diffoscope <https://maven.apache.org/guides/mini/guide-reproducible-builds.html>
  - Docker Docs, "Build cache invalidation" — COPY/ADD 체크섬은 mtime 미포함 <https://docs.docker.com/build/cache/invalidation/>
  - SWEBOK v4.0a — Software Configuration Management KA(8장 §6.1 "Software Building", §6 "Software Release Management and Delivery")·Software Engineering Operations KA(6장 §3.2 "Deployment/Release Engineering"). computer.org PDF 목차로 확인 <https://ieeecs-media.computer.org/media/education/swebok/swebok-v4.pdf>
  - Gradle User Manual "Build Cache"(9.x) — 작업 입력·출력 선언으로 캐시 키 계산 <https://docs.gradle.org/current/userguide/build_cache.html> · "Java Plugin" Compilation avoidance <https://docs.gradle.org/current/userguide/java_plugin.html>
  - Maven Compiler Plugin `compiler:compile` — `useIncrementalCompilation` 두 모드 <https://maven.apache.org/plugins/maven-compiler-plugin/compile-mojo.html>
  - SLSA v1.2 "Verifying artifacts" — 출처 증명 검증 <https://slsa.dev/spec/v1.2/verifying-artifacts>
- 실험 목록(모두 2026-10-05, `--network none`, `--cpus=2`)
  - 위상정렬: `BuildTopo.java`(JDK 21) vs Maven 3.9.16 reactor 순서·`-pl … -amd`·순환 오류
  - make 시각 판정: GNU Make 4.3 — touch 헛빌드, 과거 mtime 놓침
  - 캐시 오염: `MiniBuild.java` — 소스만 키 → 운영 요청에 스테이징 산출물 HIT
  - 재현 가능 jar: Maven 3.9.16·jar-plugin 3.5.1 `outputTimestamp` 유무, JDK `jar --date` 유무
  - 환경 의존: `EnvDep.java` — TZ·로캘 3조합
  - 증분 한계: maven-compiler-plugin 3.15.0 모듈 단위 재컴파일(기본 모드)·`useIncrementalCompilation=false`면 1파일·삭제 감지 vs 손 스크립트의 남은 `.class`
