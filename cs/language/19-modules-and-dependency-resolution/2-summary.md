# language/19-modules-and-dependency-resolution — 모듈·패키지·semver·버전 해석·락파일 — 정리 (힌트)

## 해결하는 문제

남의 코드를 가져다 쓰는 순간 세 질문이 생긴다.

```text
  ① 이름: 내 Money와 라이브러리의 Money가 부딪히지 않게 하려면?        → 모듈·패키지(이름공간)
  ② 버전: 라이브러리 A는 C 1.x를, B는 C 2.x를 원한다. 무엇을 싣나?    → semver + 버전 해석
  ③ 재현: 어제와 오늘, 내 PC와 CI가 같은 바이트를 받으려면?            → 락파일 / 최소 버전 선택
```

- *모듈(module)·패키지(package)*: 코드를 묶어 이름공간을 주고, 밖에 보일 것과 숨길 것을 정하고, 무엇에 기대는지 선언하는 단위. 언어마다 이름이 다르다(Java 패키지·JAR·JPMS 모듈, npm 패키지, Go 모듈, Python 패키지).
- *전이 의존성(transitive dependency)*: 내가 직접 고르지 않았는데 내 의존성이 기대서 따라 들어온 것.

쉬운 예: 요리책 두 권이 둘 다 "간장 1스푼"을 쓰는데, 한 권은 진간장, 다른 권은 국간장을 뜻한다.\
부엌(실행 환경)에 간장병이 하나만 놓일 수 있다면 어느 한 요리는 맛이 틀어진다.

똑같은 구조다.\
라이브러리 A·B가 같은 이름의 C를 다른 판으로 기대고, 실행 환경이 C를 한 판만 올릴 수 있으면 둘 중 하나가 깨진다. 이것이 **다이아몬드 의존**이다.

실무 예:
- 라이브러리 하나를 올렸더니 컴파일은 되는데 배포 후 특정 API를 부를 때만 `java.lang.NoSuchMethodError`가 난다.
- `package-lock.json` 없이 돌던 CI가, 코드 변경이 없는데 어느 날 깨졌다. 전이 의존성의 새 패치 판이 나왔다.
- 2016-03-22, npm에서 `left-pad`가 내려가자 그것에 기대던 빌드들이 연쇄로 실패했다(npm 블로그 원문).

## 동작·원리

### 1. 의존성 그래프와 다이아몬드

```text
            app
           /   \
     liba 1.0   libb 1.0
          \       /
     money ^1.0   money ^2.0     ← 같은 이름, 다른 판 요구
           \     /
            money ?              ← 한 판만 올릴 수 있으면 하나가 깨진다
```

- 노드 = 패키지의 한 판(이름 + 버전), 간선 = "이 판은 저 범위가 필요하다".
- 해석기(resolver)는 그래프에서 이름마다 판 하나(또는 여러 개)를 고른다. 고른 결과가 *빌드 목록(build list)*이다.

### 2. semver — 버전 번호에 호환성 약속을 싣는다

```text
   MAJOR . MINOR . PATCH
     │       │       └ 호환되는 버그 수정
     │       └ 호환되게 기능 추가
     └ 호환 안 되는 API 변경
   0.y.z 는 초기 개발 — 언제든 무엇이든 바뀔 수 있다
```

- Semantic Versioning 2.0.0(semver.org): 위 세 규칙, "한 번 낸 판의 내용은 바꾸면 안 된다(MUST NOT)", "0.y.z는 공개 API가 안정적이라 보지 말라".
- semver는 **약속**이지 검사가 아니다. 사람이 MINOR를 올리고 API를 깨면 도구는 모른다.
- 범위 표기(npm `node-semver` README)
  - `^1.2.3` = `>=1.2.3 <2.0.0-0` — 가장 왼쪽 0 아닌 자리를 바꾸지 않는 범위. `^0.2.5`는 `<0.3.0-0`.
  - `~1.2.3` = `>=1.2.3 <1.3.0-0` — 패치만.

### 3. 해석기마다 고르는 규칙이 다르다

| 생태계 | 같은 이름 다른 판이 오면 | 근거 |
|---|---|---|
| Maven | **가장 가까운 선언**(트리에서 얕은 쪽), 같은 깊이면 먼저 선언한 쪽 | Maven "Introduction to the Dependency Mechanism" — `A→B→C→D 2.0`, `A→E→D 1.0`이면 **D 1.0** |
| Gradle | 그래프 전체 요청 중 **가장 높은 판**(기본) | Gradle User Manual "Graph Resolution" Version conflicts |
| npm | 범위를 만족하는 최신 판. 못 맞추면 **중첩 `node_modules`로 두 판을 같이 설치**(일반 의존성 — `peerDependencies` 충돌은 중첩으로 못 풀어 npm 7+에서 설치 오류가 날 수 있다) | 실험 2, Node.js 22 `modules` 문서의 `node_modules` 탐색 규칙 |
| Go | **최소 버전 선택(MVS)** — 요구된 최솟값들 중 최댓값 | Go Modules Reference "Minimal version selection" |
| Cargo | 백트래킹 탐색. 서로 다른 판을 한 바이너리에 같이 링크할 수 있음 | Cox, "Version SAT"(2016-12-13)의 도구 목록 |

- Maven의 "가까운 쪽"은 **더 낮은 판**을 고를 수 있다. 위 예에서 C가 D 2.0의 새 메서드를 부르면 실행 중 `NoSuchMethodError`가 난다(§4).
- 왜 어려운가: Cox는 "Version SAT"에서 다음 네 가정 아래 버전 선택이 **NP-완전**임을 3-SAT 환원으로 보였다.
  1. 의존성에 특정 판을 지정할 수 있다.
  2. 설치하려면 의존성을 모두 설치해야 한다.
  3. 판마다 의존성이 다를 수 있다.
  4. 한 패키지의 두 판을 동시에 설치할 수 없다.
- 탈출구는 가정을 깨는 것이다(Cox 같은 글 "Alternatives?"). 4를 깨면 두 판을 같이 둔다 — 그러면 거의 어떤 탐색이든 해를 찾지만, **가장 작은** 조합 찾기는 여전히 NP-완전이다. npm의 중첩 설치가 이 방향이다(해석 — Cox는 같은 글에서 npm도 네 가정이 성립하는 도구로 꼽는다. 충돌을 선언할 수단이 있으면 가정 4가 성립하기 때문이다). 1을 깨면 "최솟값만 선언"하게 되고, 이것이 MVS의 출발점이다.

### 4. JVM — 컴파일 때 본 메서드를 실행 때 이름으로 다시 찾는다

```text
  컴파일: libb.jar 를 money 2.0 에 맞춰 javac
          → 호출 지점에 "com/x/Money.fmt:(JLjava/lang/String;)Ljava/lang/String;" 서술자를 박제
  실행:   클래스패스 앞에서부터 com/x/Money.class 를 찾는다 → 먼저 나온 jar 가 이긴다
          (HotSpot은) 처음 그 호출에 도달할 때 서술자로 메서드를 찾는다(해소, resolution)
          → 없으면 NoSuchMethodError, 클래스 자체가 없으면 NoClassDefFoundError(원인 ClassNotFoundException)
```

- JVMS SE21 §5.4.3.3: 메서드 조회가 실패하면 메서드 해소는 `NoSuchMethodError`를 던진다. §5.3.1: 부트스트랩 로더가 클래스를 못 찾으면 `ClassNotFoundException`, 그 결과 로딩이 `NoClassDefFoundError`로 실패한다.
- 이 실험(JDK 21 HotSpot)에서 해소는 **그 호출에 처음 도달할 때** 일어났다. JVMS §5.4는 지연·조기 해소를 모두 허용하되, 해소 오류는 그 참조를 쓰는 지점에서 던지도록 정한다. 그래서 기동은 되고, 특정 기능을 처음 쓸 때 터진다.

### 실험 1: 다이아몬드 → `NoSuchMethodError` (`e19/build.sh`)

`liba`는 money 1.0(`fmt(long)`)에, `libb`는 money 2.0(`fmt(long)` + `fmt(long, String)`)에 맞춰 컴파일했다. 실행 클래스패스의 뒷부분만 바꾼다.\
환경: `eclipse-temurin:21-jdk`, `--network none`.

```text
  == javap: B의 호출 지점이 기억하는 메서드 서술자
       5: invokestatic  #11  // Method com/x/Money.fmt:(JLjava/lang/String;)Ljava/lang/String;
  == classpath tail: [libc-2.0.jar]               A:1000 / B:1000 KRW
  == classpath tail: [libc-1.0.jar]               A:1000 / NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'
  == classpath tail: [libc-1.0.jar:libc-2.0.jar]  A:1000 / NoSuchMethodError (같은 메시지)
  == classpath tail: [libc-2.0.jar:libc-1.0.jar]  A:1000 / B:1000 KRW
  == classpath tail: []                           NoClassDefFoundError: com/x/Money ← Caused by: ClassNotFoundException
  == libc-3.0(fmt(long) 제거)만                    NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long)'   ← 이번엔 A가 깨짐
  == -verbose:class
  [info][class,load] com.x.Money source: file:/w/libc-1.0.jar
```

- 두 판을 다 올려도 **먼저 나온 jar 하나만** 쓰였다(이 JDK의 앱 클래스 로더 관찰). 순서를 바꾸면 결과가 바뀐다.
- `A:1000`이 먼저 찍히고 B에서 죽었다. 일부 일을 한 뒤 실패한다.
- money 3.0처럼 옛 메서드를 지우면(major 변경) A가 깨진다. 1.0은 B를, 3.0은 A를 깬다. 이 실험의 해는 둘 다 만족하는 2.0 하나다. 그런 판이 없으면(예: B가 3.0에만 있는 메서드를 요구하면 — 가정) 한 판만 올릴 수 있는 환경에서는 **해가 없는** 다이아몬드다.

### 5. Node.js — 중첩 `node_modules`로 두 판이 공존한다

```text
  /w/node_modules/money            (1.0.0)   ← liba가 require('money') 하면 위로 올라가며 찾다가 여기
  /w/node_modules/libb/node_modules/money (2.0.0)   ← libb는 자기 폴더의 node_modules부터 찾는다
```

- Node.js 22 문서: `require('x')`는 현재 모듈 폴더의 `node_modules`부터 찾고, 없으면 부모 폴더로 올라가 파일 시스템 루트까지 간다.

### 실험 2: 두 판 공존 (`e19/nodeproj`, `node:22-alpine`)

```text
  A uses money 1.0.0 from ./node_modules/money/index.js
  B uses money 2.0.0 from ./node_modules/libb/node_modules/money/index.js
  same module object?  false
```

- 둘 다 동작한다. 대신 같은 이름의 모듈이 **두 개의 다른 객체**다. 싱글턴·`instanceof`·전역 레지스트리가 둘로 갈린다. 브라우저 번들에서 같은 라이브러리 두 벌이 생기는 문제는 [web-platform/09-js-modules-and-bundling](../../web-platform/09-js-modules-and-bundling/2-summary.md) 장애 5.

### 6. 최소 버전 선택(MVS) — 요구된 최솟값 중 최댓값

```text
  app ──> a v1.2.0 ──> c v1.3.0 ─┐
   └───> b v1.2.0 ──> c v1.4.0 ─┴─ c: 요구된 판 {1.3.0, 1.4.0} 중 최고 = v1.4.0
  "최신 판"이 아니라 "누군가 실제로 요구한 판" 중에서 고른다 → 새 판이 나와도 결과가 안 바뀐다
```

- Go Modules Reference: MVS는 주 모듈에서 그래프를 순회하며 모듈마다 **요구된 가장 높은 판**을 기록한다. 그 결과가 빌드 목록이고, "다른 시스템과 달리 빌드 목록을 락 파일에 저장하지 않는다. MVS는 결정적이라 새 판이 나와도 빌드 목록이 바뀌지 않는다."
- Cox "Minimal Version Selection"(2018-02-21): 요구 사항을 최솟값으로만 적게 하면, 문제는 2-SAT·Horn-SAT·Dual-Horn-SAT의 교집합에 들어가 다항 시간에 풀린다(같은 글: "이미 선형 시간 알고리즘이 있다"). 전제는 "새 판은 옛 판만큼 동작한다"는 import 호환성 규칙이다.
- 대가: 고쳐진 새 패치가 나와도 **누군가 요구를 올리기 전까지는** 옛 판에 머문다. 올리는 것은 사람이 `go get`으로 한다.

### 실험 3: Go 1.23 MVS (`e19/gomvs`, 오프라인)

`replace`로 모듈을 로컬 폴더에 연결했다(`GOPROXY=off`, 다운로드 없음). 판 선택만 보이는 실험이다 — 모든 판이 같은 폴더 코드를 쓴다.

```text
  $ go mod graph | grep example.com/c@
  example.com/app example.com/c@v1.4.0          ← tidy 뒤 go.mod의 // indirect 요구
  example.com/a@v1.2.0 example.com/c@v1.3.0
  example.com/b@v1.2.0 example.com/c@v1.4.0
  example.com/c@v1.4.0 example.com/d@v1.2.0
  example.com/c@v1.4.0 go@1.23
  $ go list -m all
  example.com/app
  example.com/a v1.2.0 => ../a
  example.com/b v1.2.0 => ../b
  example.com/c v1.4.0 => ../c        ← 1.3.0·1.4.0 중 높은 쪽
  example.com/d v1.2.0 => ../d
```

- `go mod tidy`는 MVS 결과를 `go.mod`의 `// indirect` 요구로 적었다(`c v1.4.0`, `d v1.2.0`).

### 7. 락파일 — 해석 결과를 박제한다

```text
  선언(범위)          해석(오늘의 레지스트리)        락파일(박제)
  a ^1.2.0     ──▶   a 1.2.0, c 1.4.0        ──▶   a 1.2.0, c 1.4.0 (+ 무결성 해시)
  내일 c 1.5.0 공개 → 락 없이 다시 해석하면 c 1.5.0 / 락이 있으면 c 1.4.0
```

### 실험 4: 범위 해석 vs 락파일 vs MVS (`e19/resolve.py`, `python:3.12-slim`)

레지스트리 2일째에 c 1.5.0(회귀 버그가 있다고 가정)이 공개된다. 코드는 그대로다.

```text
  day1 caret(no lock) = {'b': '1.2.0', 'c': '1.4.0', 'a': '1.2.0'}
  day1 lockfile      = {'b': '1.2.0', 'c': '1.4.0', 'a': '1.2.0'}
  day1 MVS           = {'b': '1.2.0', 'c': '1.4.0', 'a': '1.2.0'}
  day2 caret(no lock) = {'b': '1.2.0', 'c': '1.5.0', 'a': '1.2.0'}   ← 코드 변경 없이 바뀜
  day2 lockfile      = {'b': '1.2.0', 'c': '1.4.0', 'a': '1.2.0'}
  day2 MVS           = {'b': '1.2.0', 'c': '1.4.0', 'a': '1.2.0'}
  install order = ['c', 'b', 'a']                                     ← 위상 정렬
  diamond: conflict on c: ['2.0.0', '1.0.0']                          ← ^2.0.0과 ^1.0.0, 한 판 규칙이면 해 없음
```

- "최신 만족" 해석은 레지스트리 상태의 함수다. 락파일이나 MVS는 그 의존을 끊는다.
- 락파일이 받은 바이트까지 같게 하는 무결성 해시·SBOM은 [security/25-supply-chain-security](../../security/25-supply-chain-security/2-summary.md), 빌드 전체 재현성은 [engineering-practice/07-build-systems-and-reproducibility](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md).

### 8. 찾는 경로도 "앞이 이긴다" — Python `sys.path`

- `import x`는 먼저 `sys.modules` 캐시, 내장·동결 모듈을 본다. 거기 없는 모듈(`json` 같은 순수 Python 모듈)은 `sys.path` 목록을 앞에서부터 보며 처음 찾은 `x`를 쓴다(Python 3.12 import 시스템 문서). 스크립트를 실행하면 기본으로 스크립트 폴더가 맨 앞에 붙는다.

### 실험 5: 이름 가림 (`e19/pyshadow`, `python:3.12-slim`)

스크립트 옆에 `json.py`를 두고 `import json`.

```text
  == python app.py
  loaded LOCAL json.py (shadow)
  json from: /w/json.py              ← sys.path[0] = 스크립트 폴더
  not-json
  == python -P app.py
  json from: /usr/local/lib/python3.12/json/__init__.py
  {"a": 1}
```

- Python 3.12 문서: `-P`는 "잠재적으로 안전하지 않은 경로를 `sys.path` 앞에 붙이지 않는다"(스크립트 실행이면 스크립트 폴더). 3.11에 추가됐다.
- 클래스패스·`sys.path`·`PATH`·동적 로더 검색 경로는 모두 **순서 있는 목록의 첫 일치**다. 링커·로더 쪽은 [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **의존성 그래프(유향 그래프) + 위상 정렬** — 설치·빌드 순서. 위상 정렬은 순환이 없을 때(DAG)만 된다. 순환은 도구에 따라 오류로 막거나(Java 모듈) 허용한다(Go 모듈 요구 그래프 — Cox "must not assume the module requirement graph is acyclic"). [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md)(커리큘럼 번호 32), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **그래프 도달성 순회** — MVS의 빌드 목록 = 주 모듈에서 닿는 판들 + 이름마다 최댓값. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)
- **버전 해석 = SAT** — 일반형은 NP-완전(Cox 2016). 실제 도구는 백트래킹·SAT 솔버·제약 완화로 푼다. [algorithm/13-backtracking](../../algorithm/13-backtracking/2-summary.md), [algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md)
- **순서 있는 검색 경로** — 클래스패스·`sys.path`·`node_modules` 상향 탐색은 선형 탐색의 첫 일치다.

## 적용 — 풀어나가는 법

1. **증상을 단계로 나눈다.**

| 증상 | 단계 | 의심 |
|---|---|---|
| `cannot find symbol`·`Cannot find module` | 컴파일·번들 | 선언 누락 |
| `NoSuchMethodError`·`NoSuchFieldError`·`AbstractMethodError` | 실행(해소) | 컴파일한 판 ≠ 실행한 판 |
| `NoClassDefFoundError`(원인 `ClassNotFoundException`) | 실행(로딩) | 실행 경로에 jar 없음, 스코프(`provided`·`test`) 착오 |
| 코드 변경 없이 CI가 깨짐 | 해석 | 락파일 없음·락 무시 설치 |
| 싱글턴이 둘, `instanceof` 실패 | 해석 | 같은 패키지 두 사본 |

2. **"실제로 무엇이 올라갔나"를 본다.** 선언이 아니라 결과를 본다.

```bash
java -verbose:class -cp ... App 2>&1 | grep 'com.x.Money'     # 클래스가 어느 jar에서 왔나
javap -c -cp libb.jar com.b.B | grep invoke                  # 호출 지점이 기대한 서술자
mvn dependency:tree -Dincludes=com.x:money                    # Maven이 고른 판과 경로
gradle dependencyInsight --dependency money                   # Gradle이 왜 그 판을 골랐나
npm ls money                                                  # 설치된 사본과 위치 전부
go mod graph | grep money        # 누가 어느 판을 요구했나(요구 그래프)
go mod why -m example.com/money   # 왜 이 모듈이 필요한가(주 모듈에서의 import 경로)
python -X importtime -c 'import app' 2>&1 | sort -t'|' -k2 -n | tail   # 어떤 모듈 import에 몇 μs 걸렸나(경로는 안 나온다)
python -v -c 'import app' 2>&1 | grep json                         # 어느 파일에서 불러왔나
```

3. **고친다.**
   - 판을 명시해 묶는다: Maven `dependencyManagement`·BOM, Gradle 제약(`constraints`)·`strictly`, npm `overrides`, Go `go get money@v1.4.0`.
   - 한 판으로 못 맞추면(실험 1의 3.0): 한쪽 라이브러리를 올리거나, 셰이딩(패키지 이름 바꿔 다시 묶기)으로 두 판을 격리한다.
   - 재현: 락파일을 커밋하고 CI는 락을 따르는 명령(`npm ci` 등)만 쓴다.

## 장애 시나리오와 대처

### 1. 다이아몬드 의존 → 배포 후 `NoSuchMethodError`

- **현상**: 테스트·기동은 통과했는데 운영에서 특정 기능을 처음 쓸 때 500이 난다.
- **보이는 형태**: `java.lang.NoSuchMethodError: 'java.lang.String com.x.Money.fmt(long, java.lang.String)'`. 스택 맨 위가 라이브러리 내부다.
- **원인**: B는 money 2.0에 맞춰 컴파일됐는데 실행 경로에는 1.0이 올라갔다. Maven의 "가까운 쪽" 규칙이 낮은 판을 골랐거나, 클래스패스에 두 판이 있어 앞의 것이 이겼다(실험 1).
- **대처**: `-verbose:class`로 실제 jar를 확인하고, 해석 트리로 누가 그 판을 끌어왔는지 본다. `dependencyManagement`로 판을 고정하고, 트리 안에서 판이 갈리면 빌드를 실패시킨다(Maven Enforcer `dependencyConvergence` 규칙: "트리 어디서나 의존성 판이 같아야 한다" <https://maven.apache.org/enforcer/enforcer-rules/dependencyConvergence.html>).

### 2. 실행 경로에서 jar 누락 → `NoClassDefFoundError`

- **현상**: 로컬 IDE에서는 되는데 패키징한 jar로 실행하면 실패한다.
- **보이는 형태**: `java.lang.NoClassDefFoundError: com/x/Money`, `Caused by: java.lang.ClassNotFoundException: com.x.Money`(실험 1의 빈 클래스패스).
- **원인**: 컴파일 경로에는 있지만 실행 경로에는 없다. `provided`·`compileOnly` 스코프, 셰이딩 설정 누락.
- **대처**: 스코프를 실행 필요 여부로 다시 고른다. 패키징 결과(`jar tf`)에 그 클래스가 있는지 CI에서 확인한다.

### 3. 락파일 없는 빌드 → 비재현

- **현상**: 코드 변경 없는 재빌드에서 테스트가 깨지거나 동작이 바뀐다. 로컬과 CI의 결과가 다르다.
- **보이는 형태**: 두 빌드의 해석 결과(`npm ls`·`pip freeze` 출력)를 비교하면 전이 의존성의 패치·마이너 판이 다르다(실험 4의 day2).
- **원인**: 범위 선언(`^`·`~`·`>=`)을 그날의 레지스트리로 해석했다.
- **대처**: 락파일을 커밋하고, CI는 락을 따르는 설치만 한다. 판 올림은 자동 PR(Renovate류)로 따로 검증한다. Go는 MVS가 같은 효과를 낸다.

### 4. 레지스트리에서 패키지 삭제 → 빌드 연쇄 실패 (left-pad, 2016-03)

- **현상**: 내 코드도 락파일도 그대로인데 설치 단계가 실패한다.
- **보이는 형태**: 설치 도구가 "패키지·판을 찾을 수 없음"을 낸다. npm 블로그 원문: 2016-03-22(화) 오후 2:30쯤(태평양 시) "분당 수백 건의 실패"를 관측했고, 의존하는 프로젝트와 그 의존자들이 줄줄이 실패했다.
- **원인**: 작가가 `kik`을 포함한 273개 패키지를 내렸고 그중 `left-pad`가 있었다. 10분 안에 다른 사람이 같은 기능을 1.0.0으로 냈지만, `line-numbers`를 거쳐 `0.0.3`을 정확히 요구하는 사슬(babel·atom)이 남아 실패가 이어졌다. npm은 백업에서 원래 0.0.3을 다시 올렸고, 중단은 2.5시간이었다.
- **대처**: 락파일은 "무슨 판"을 고정할 뿐 "그 판이 남아 있음"은 보장하지 않는다. 사내 미러·프록시 캐시, 벤더링, 아티팩트 보관으로 원천이 사라져도 빌드되게 한다. 공급망 보안 쪽 대처는 [security/25](../../security/25-supply-chain-security/2-summary.md).

### 5. 같은 패키지 두 사본 → 상태가 갈린다

- **현상**: 설정을 분명히 등록했는데 다른 모듈에서는 "등록 안 됨", `instanceof`가 false.
- **보이는 형태**: `npm ls <pkg>`에 같은 이름이 두 경로로 나온다. 실험 2의 `same module object? false`.
- **원인**: 범위가 겹치지 않아 해석기가 중첩 설치를 했다.
- **대처**: 범위를 맞추거나 `overrides`·`peerDependencies`로 한 사본으로 모은다. 번들 쪽은 [web-platform/09](../../web-platform/09-js-modules-and-bundling/2-summary.md).

## 핵심 문장

- 의존성 해석은 그래프에서 이름마다 판을 고르는 일이고, 한 이름에 한 판만 허용하면서 정확한 판을 지정할 수 있으면 일반형은 NP-완전이다.
- 생태계마다 고르는 규칙이 다르다: Maven은 가장 가까운 선언, Gradle은 가장 높은 판, npm은 두 판 공존, Go는 요구된 최솟값 중 최댓값(MVS)이다.
- JVM은 컴파일 때 박제한 메서드 서술자를 실행 중 처음 호출할 때 찾으므로, 판 불일치는 기동이 아니라 그 기능을 처음 쓸 때 `NoSuchMethodError`로 터진다.
- 클래스패스·`sys.path`·`node_modules`는 순서 있는 목록의 첫 일치라, 같은 이름이 둘이면 앞에 있는 것이 조용히 이긴다.
- 범위 선언을 그날 해석하면 빌드는 레지스트리 상태의 함수가 되고, 락파일이나 MVS가 그 의존을 끊는다.
- 락파일은 판을 고정할 뿐 그 판이 레지스트리에 남아 있음을 보장하지 않는다(left-pad).

## 관련 주제·근거

- 선행
  - [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) — 위상 정렬·순환 감지(커리큘럼 표의 `32-dependency-resolver`)
- 후속·연결
  - [security/25-supply-chain-security](../../security/25-supply-chain-security/2-summary.md) — 락파일 무결성 해시·SBOM·서명
  - [engineering-practice/07-build-systems-and-reproducibility](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md) — 빌드 DAG·재현 가능 빌드
  - [web-platform/09-js-modules-and-bundling](../../web-platform/09-js-modules-and-bundling/2-summary.md) — ESM/CommonJS, 번들의 두 벌 문제
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — 네이티브 링커·로더의 심볼·경로·버전
  - [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md)(닫힌 세계의 도달성), [26-pl-symptom-index](../26-pl-symptom-index/2-summary.md) · [27-pl-incidents](../27-pl-incidents/2-summary.md)
- 문서·출처
  - Semantic Versioning 2.0.0 — MAJOR/MINOR/PATCH, 낸 판 수정 금지, 0.y.z <https://semver.org/>
  - npm `node-semver` README — Caret·Tilde 범위 정의 <https://github.com/npm/node-semver>
  - Russ Cox, "Minimal Version Selection"(2018-02-21) — 최소 요구, 2-SAT·Horn-SAT·Dual-Horn-SAT, high-fidelity build <https://research.swtch.com/vgo-mvs>
  - Russ Cox, "Version SAT"(2016-12-13) — 네 가정 아래 NP-완전, 도구별 해석 방식 <https://research.swtch.com/version-sat>
  - Go Modules Reference — "Minimal version selection (MVS)", 빌드 목록을 락 파일에 저장하지 않음 <https://go.dev/ref/mod>
  - Maven "Introduction to the Dependency Mechanism" — Dependency mediation, nearest definition, 같은 깊이면 먼저 선언 <https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html>
  - Gradle User Manual "Graph Resolution" — Version conflicts에서 기본은 가장 높은 판 <https://docs.gradle.org/current/userguide/graph_resolution.html>
  - Node.js 22 `modules` — Loading from node_modules folders <https://nodejs.org/docs/latest-v22.x/api/modules.html>
  - JVMS SE21 §5.3.1(`ClassNotFoundException` → `NoClassDefFoundError`), §5.4.3.3(`NoSuchMethodError`) <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html> · `java` 도구 문서 `--class-path`
  - Python 3.12 "Command line and environment" — `-P`(3.11 추가), `-X importtime` <https://docs.python.org/3.12/using/cmdline.html>
  - npm Blog, "kik, left-pad, and npm"(2016-03-23) <https://blog.npmjs.org/post/141577284765/kik-left-pad-and-npm>
- 실험(로컬, 컨테이너 `--network none`, `--cpus=2`)
  - `e19/build.sh`(`eclipse-temurin:21-jdk`) — 클래스패스 순서 5가지 + money 3.0, `NoSuchMethodError`·`NoClassDefFoundError`, `javap` 서술자, `-verbose:class` 출처 jar
  - `e19/nodeproj`(`node:22-alpine`, v22.23.2) — 중첩 `node_modules`의 money 1.0.0·2.0.0 공존, 모듈 객체 불일치
  - `e19/gomvs`(`golang:1.23-alpine`, go1.23.12, `GOPROXY=off`) — `go mod graph`·`go list -m all`로 c v1.4.0 선택
  - `e19/resolve.py`(`python:3.12-slim`) — 캐럿 최신 해석·락파일·MVS의 이틀 비교, 위상 정렬, 한 판 규칙 다이아몬드 충돌
  - `e19/pyshadow`(`python:3.12-slim`) — 스크립트 폴더 `json.py`가 표준 `json`을 가림, `-P`로 해소
