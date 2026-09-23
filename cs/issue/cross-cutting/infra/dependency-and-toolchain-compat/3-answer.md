# cs/issue/infra/dependency-and-toolchain-compat — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **import 단계에서 깨진다. 빌드 도구는 기동조차 못 해 원인을 설명하지 못한다.**\
   표준 라이브러리 API도 버전별로 추가된다 — `itertools.batched`는 3.12+라 3.10에서는 모듈 import에서 실패한다.\
   교정: `islice`로 자체 `batched()`를 구현하고 "운영 버전(3.10) 호환 유지"를 컨벤션으로 적었다.\
   빌드 도구도 JVM 위에서 도는 프로그램이라 지원 범위 밖 JDK에서는 자기 자신이 뜨지 못하고, 메시지는 `What went wrong: 25.0.1`처럼 버전 문자열뿐이었다.\
   교정: 도구가 쓸 JDK를 설정 파일에 고정하고, 실행 스크립트에서 사용자 `JAVA_HOME`을 지워 환경 영향을 없앴다.

2. **API 버전이 협상되고, 로거 바인딩이 없어 진단 로그가 버려졌다.**\
   데몬(메이저 업그레이드 후)은 최소 API 1.44를 요구하는데 테스트 라이브러리의 내장 클라이언트는 1.32로 협상했다.\
   CLI(`docker ps`)는 최신 클라이언트라 되고, 테스트 JVM의 구 클라이언트만 거부됐다.\
   로깅 파사드에 바인딩이 없으면(NOP) 라이브러리의 debug 로그가 사라져 "환경 없음"만 보인다 — 바인딩을 추가하자 `client version 1.32 is too old` 가 드러났다.
   > **API 버전 협상** — 클라이언트와 서버가 서로 지원하는 프로토콜 버전을 맞추는 과정. 서버의 최소 요구가 오르면 구 클라이언트의 요청은 (연결은 되더라도) 버전 오류로 거부된다.

3. **shade된 사본은 (relocate한 경우) 다른 패키지 이름으로 재배치된 복사본이라, 외부 의존성 override가 그 클래스를 가리키지 않는다.**\
   외부에서 같은 라이브러리 새 버전을 선언해도 그건 원래 패키지명의 별개 클래스다.\
   환경변수·시스템 프로퍼티·설정 파일 여섯 가지 시도가 모두 무효였다 — 내장 사본이 그 설정을 읽도록 연결돼 있지 않아 하드코딩 기본값에 닿지 않았다(설정이 닿는지는 라이브러리가 그 값을 전달하느냐에 달렸다 — shade 자체가 설정을 막는 것은 아니다).\
   남는 대응: 그 라이브러리 **자체**를 업그레이드한다(부모 BOM이 버전을 묶으면 명시 버전으로 override).\
   함정: 메이저 업그레이드에서 artifactId가 바뀌어 옛 이름은 "artifact 없음"이 됐다.
   > **shade** — 의존성을 자기 jar 안에 복사하고, 흔히 패키지명까지 바꿔(relocate, 선택 사항) 충돌을 피하는 빌드 기법.

4. **둘 다 "최종 해석 트리"가 정본이다.**\
   상위를 핀해도 상위가 전이 의존성에 상한을 두지 않으면 최신이 설치되고, 그 버전의 버그가 import 시점에 터진다 — "상위가 상한을 안 두면 우리가 핀한다".\
   선언 삭제는 필요조건일 뿐이다 — 소스에서 쓰지 않는 다른 직접 의존성이 전이로 같은 라이브러리를 공급하고 있었다.\
   `dependency:tree`의 들여쓰기(공급 경로)로 공급원을 찾아 제거하고, 재실행에서 해당 라이브러리 grep 0건으로 완료를 판정했다.

5. **서로에게 위임하면 무한 루프가 되기 때문이다.**\
   한 브리지는 "A API 호출 → B로 보냄", 다른 브리지는 "B 호출 → A로 보냄"이다.\
   둘이 함께 있으면 로그 한 줄이 두 브리지 사이를 끝없이 돈다 — 그래서 이 조합을 아는 프레임워크는 기동 시점에 명시적으로 거부한다(감지하지 못하는 조합이면 StackOverflowError로 드러난다).\
   교정: 쓸 백엔드를 하나 정하고, 전이로 들어오는 반대 방향 브리지를 모든 공급 경로에서 `exclusion`한다.

6. **peer는 "내가 설치하지 않고, 호스트 프로젝트가 이 범위로 갖고 있어야 한다"는 요구다.**\
   npm 7부터 peer를 자동 설치·엄격 검증해, 해석할 수 없는 peer 범위 충돌이 트리에 있으면 그 트리를 건드리는 조작(uninstall 포함)이 `ERESOLVE`로 거부될 수 있다(충돌 위치에 따라 경고로 끝나기도 한다).\
   `--legacy-peer-deps`는 검증을 끄는 것이라, 실제로 호환되지 않는 조합이 런타임까지 숨는다 — 가능하면 버전을 맞추고, 우회했다면 프로젝트 주의사항으로 남긴다.

7. **각각 다른 두 쪽의 호환을 확인하지 않았다.**\
   wrapper 체크섬: 저장소에 커밋된 실행 스크립트 ↔ 공식 배포본.\
   HTTP/2 고정: 클라이언트 기본 프로토콜 협상 ↔ 서버가 지원하는 프로토콜.\
   GNU 옵션 폴백: 스크립트가 쓰는 확장 옵션 ↔ 대상 OS의 유틸리티.\
   타입드 클라이언트: 클라이언트가 모델링한 스키마 ↔ 서버(플러그인)가 받는 옵션.\
   자세한 비교는 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — 개발 런타임 ≠ 실행 런타임
① 문제 코드
```python
from itertools import batched          # 3.12+ ; 실행 서버는 3.10
for chunk in batched(rows, 1000): ...
```
② 고친 코드
```python
from itertools import islice
def batched(it, n):
    it = iter(it)
    while batch := tuple(islice(it, n)):
        yield batch
```
깨진 것: 표준 API 가용성이 런타임 버전에 달려 있었다.\
같은 구조:
- 빌드 도구 × 지원 범위 밖 JDK → 기동 실패(버전 문자열만 출력) → 도구 전용 JDK 고정 + 사용자 `JAVA_HOME` 제거.
- 프레임워크 새 메이저가 요구하는 Node(≥20)보다 시스템 Node(18)가 낮음 → 버전 파일(`.nvmrc` 류) 고정.
- 테스트 러너가 로컬 Node 18에 없는 API를 import → 테스트도 빌드 이미지와 같은 런타임(컨테이너)에서 실행, 순수 함수는 JSX 파일 밖으로 분리.
- 버전 매니저는 대화형 셸 초기화에서만 PATH를 주입 → 비대화형 셸(자동화)은 구 버전 → 절대 경로·`JAVA_HOME` 명시.
- 패키지 매니저의 optional 플랫폼 의존성 버그로 네이티브 바인딩 누락 → 전 페이지 500 → 호스트 직접 빌드 금지, 고정 런타임 이미지로만 빌드.
- 번들러가 프로젝트 루트 밖을 가리키는 심링크 `node_modules`를 거부 → 같은 파일시스템 하드링크 복사(`cp -al`).
- 가상환경 폴더 이동 → 스크립트 shebang에 박힌 절대 경로가 낡음 → `python -m pip` 또는 재생성.
- Dockerfile이 참조하는 아티팩트 버전과 실제 파일 버전 불일치(빌드 입력 어긋남).
- 샌드박스 도구(bwrap 류)가 네트워크 네임스페이스 설정 권한이 없는 환경에서 기동 실패 → 샌드박스 옵션 조정 또는 다른 검증 경로로 대체.

### 변형 B — 상대편 최소 요구 × 내장(shade)된 구 클라이언트
① 문제 코드
```xml
<!-- 테스트 라이브러리 1.2x : 내부에 shade된 docker 클라이언트(API 1.32) -->
<dependency><artifactId>testcontainers</artifactId><version>1.21.3</version></dependency>
<!-- 시도: 외부 docker 클라이언트 3.5.x override, DOCKER_API_VERSION, -Ddocker.api.version ... 전부 무효 -->
```
② 고친 코드
```xml
<!-- 라이브러리 자체를 업그레이드 (메이저에서 artifactId 변경 주의) -->
<dependency><artifactId>testcontainers-mysql</artifactId><version>2.0.5</version><scope>test</scope></dependency>
<!-- 진단: 로깅 바인딩 추가 → "client version 1.32 is too old. Minimum supported API version is 1.44" -->
```
깨진 것: 데몬이 최소 API를 올렸고, 내장 사본에는 외부 설정이 닿지 않았다.\
같은 구조:
- 같은 사건의 다른 프로젝트: 1.20.x → 1.21.x 업그레이드로 해결(slf4j 바인딩으로 원인 확인 후).
- DB 서버 메이저 업그레이드에서 서버 기동 옵션 제거(`--default-authentication-plugin`) → 옵션 삭제.
- WebSocket 구현 라이브러리 새 메이저가 서버 런타임과 비호환 → handshake 403 → 다른 구현 선택.

### 변형 C — 해석 트리가 선언과 다름
① 문제 코드
```text
# 상위만 핀
embedding-lib==1.3.4          # transitive: model-lib(최신) → import 시 NameError
```
```xml
<!-- 쓰지 않는 starter 삭제 -->
- <dependency><artifactId>orm-starter</artifactId></dependency>
<!-- 그런데 다른 직접 의존성이 전이로 계속 공급 -->
[INFO] +- vendor:framework-dataaccess:jar:5.0.0:compile
[INFO] |  +- org.orm:orm-core:jar:3.5.19:compile
```
② 고친 코드
```text
embedding-lib==1.3.4
model-lib==4.44.2             # 상위가 상한을 안 두면 우리가 핀 (업그레이드 시 재검토)
```
```sh
# 공급원(소스 import 0건)까지 제거 → 재실행 판정
mvn dependency:tree | grep -icE 'orm-core'   # = 0 이어야 완료 (mvn 자체 실패가 파이프에 가려지지 않게 pipefail·종료코드 확인)
```
깨진 것: 선언만 보고 판단했는데 실제 해석 트리는 달랐다.\
같은 구조:
- 서로 반대로 위임하는 로깅 브리지 두 개가 전이로 동시 유입 → 기동 거부 → 모든 공급 경로에서 `exclusion`.
- 게시된 starter가 핵심 의존성을 runtime 스코프로 선언 → 앱이 컴파일 안 됨 → compile로 명시. 네임스페이스 전환 후 APT는 classifier(`:jakarta`) 필요. BOM 관리 밖 라이브러리는 버전 명시. README가 아니라 게시 메타데이터(pom·module)로 확정.
- 프레임워크 메이저에서 테스트 지원이 별도 starter로 분리 → 기존 테스트 의존성만으로 보안 테스트 컨텍스트가 서지 않아 403 → 새 starter로 교체. (권한 예외가 일반 예외 핸들러로 떨어져 500이 된 것도 전용 핸들러로 403 복원.)
- npm 7+ peer 범위 불일치(프레임워크 18 프로젝트에 16/17 peer 요구 패키지, 컴파일러 6.x vs peer ^5) → 트리 조작 거부 → 버전 맞춤 또는 `--legacy-peer-deps` + 주의사항 기록.

### 변형 D — 선언 누락·엉뚱한 패키지
① 문제 코드
```python
import psutil              # 코드에만 추가, requirements·이미지는 그대로
# → ModuleNotFoundError  (또는 try/except로 메트릭이 조용히 '-')
```
② 고친 코드
```text
# requirements.txt
psutil==...
# 이미지 재빌드, 서비스 설치 스크립트가 가상환경 인터프리터를 자동 감지
```
깨진 것: import 추가가 매니페스트·이미지 갱신으로 이어지지 않았다.\
같은 구조:
- 프론트 코드가 import하는 패키지가 `package.json`/lock에 없어 번들러 미해결 → 설치 후 lock 갱신(CSS는 자동 주입 안 돼 별도 import).
- 이름이 비슷한 포크 패키지가 같은 모듈명을 제공 → 엉뚱한 구현이 import돼 `ImportError` → 제거 후 정식 패키지 버전 고정. (마이그레이션 자동 생성은 env에서 import된 모델만 비교 — 모델 import 목록 규칙화.)

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

> 같은 원리("양쪽 호환을 게시된 사실·실제 대상으로 확인한다")에서, 확인 대상이 버전·트리가 아니라 **실행 코드·프로토콜·OS 유틸리티·클라이언트 스키마**인 방안들이다.

### 방안 1 — 커밋된 wrapper는 실행 코드다: 체크섬 검증
① 문제 코드
```yaml
steps:
  - run: ./gradlew build          # 저장소의 wrapper를 무검증 실행
```
② 고친 코드
```yaml
steps:
  - uses: gradle/actions/wrapper-validation@v4   # 공식 배포본 체크섬과 대조
  - run: ./gradlew build          # test + jar 1회 (이미지 빌드는 이 jar를 COPY만)
```
깨진 것: 커밋된 wrapper jar는 리뷰로 변조를 알아채기 어려운 바이너리라, 변조되면 빌드가 곧 임의 코드 실행이다.\
(같은 작업에서 테스트용 컴파일과 이미지 안 컴파일이 중복돼, CI 산출물을 이미지로 COPY하는 단일 스테이지로 합쳐 잡 시간이 약 160s → 88s가 됐다.)

### 방안 2 — 클라이언트 기본 프로토콜 협상: HTTP/1.1 고정
① 문제 코드
```java
RestClient client = RestClient.builder()
    .requestFactory(new JdkClientHttpRequestFactory())   // JDK HttpClient 기본: HTTP/2 — 평문 http면 h2c Upgrade 헤더 전송
    .build();
// 상대 서버가 Upgrade 헤더를 처리 못함(규격상 1.1 서버는 무시해도 되지만 거부하는 구현이 있다) → 400 "Invalid HTTP request" → 게이트웨이 502
```
② 고친 코드
```java
HttpClient http = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
RestClient client = RestClient.builder()
    .requestFactory(new JdkClientHttpRequestFactory(http)).build();
```
깨진 것: 클라이언트 기본 협상(h2c 업그레이드 요청)을 서버가 이해하지 못해 요청 자체가 malformed로 거부됐다.\
진단: `curl --http2` 와 `curl --http1.1`의 결과 비교로 격리(처음엔 멀티파트 경계로 오진).

### 방안 3 — GNU 전용 옵션: 이식 가능한 폴백 체인
① 문제 코드
```sh
canon=$(realpath -m "$path")        # BSD/macOS에 -m 없음 → 실패
[ -z "$canon" ] && deny             # fail-closed라 모든 쓰기 차단
```
② 고친 코드
```sh
canon=$(realpath -m "$path" 2>/dev/null) \
  || canon=$(realpath "$path" 2>/dev/null) \
  || canon=$(python3 -I -S -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$path")
# -I -S: PYTHONPATH·sitecustomize 격리
```
깨진 것: POSIX가 아닌 확장 옵션이 다른 유닉스에서 실패했고, fail-closed 설계에선 그게 곧 전면 차단이었다.

### 방안 4 — 타입드 클라이언트의 스키마 커버리지: raw 요청으로 우회
① 문제 코드
```java
indexOps.createWithSchema();   // 타입드 클라이언트가 플러그인 필터 옵션을 모델링 안 함 → 옵션 누락 → 생성 실패
```
② 고친 코드
```sh
# 선행: 분석기 컴포넌트 템플릿 적용
curl -X PUT "$SEARCH/<index>" -H 'Content-Type: application/json' -d @index-settings.json
```
깨진 것: 타입드 클라이언트는 자신이 모델링한 필드만 직렬화한다.

### 비교 표

| 방안 | 전제 | 비용 | 실패 모드(안 했을 때) | 맞는 조건 |
|------|------|------|------------------------|-----------|
| 1 wrapper 체크섬 | 실행 스크립트가 저장소에 커밋됨 | CI 단계 1개 | 공급망 변조 시 임의 코드 실행 | 커밋된 빌드 wrapper가 있는 모든 CI |
| 2 프로토콜 고정 | 클라이언트 기본값이 상대 지원 범위 밖 | HTTP/2 이점 포기 | 400/502, 원인 오진 | 상대가 h2c 업그레이드 요청을 거부하는 HTTP/1.1 서버 |
| 3 폴백 체인 | 여러 OS에서 실행 | 폴백 경로 유지·테스트 | 이식성 실패 = fail-closed 전면 차단 | 보안 훅처럼 실패가 차단으로 이어지는 스크립트 |
| 4 raw 요청 | 클라이언트 모델 < 서버 기능 | 타입 안전성 포기, JSON 관리 | 옵션 누락으로 생성 실패 | 플러그인 전용 옵션을 쓰는 인덱스·리소스 |

**결론**: 버전·트리(본문 변형 A~D)는 "무엇이 실제로 설치·해석되나"를, 이 방안들은 "상대가 실제로 무엇을 받아들이나"를 확인한다.\
기본값을 믿지 말고, 확인 불가능한 쪽(외부 서버·다른 OS·게시된 스크립트)과 맞닿는 지점마다 명시적으로 고정(1·2)하거나 폴백(3)·우회(4)를 둔다 — 어느 것이 낫다기보다 맞닿은 상대의 종류가 방안을 정한다.
