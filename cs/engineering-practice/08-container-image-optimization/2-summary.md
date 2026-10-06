# engineering-practice/08-container-image-optimization — 이미지 = 해시로 이름 붙은 레이어 스택: 멀티스테이지·최소 베이스·레이어 순서·.dockerignore — 정리 (힌트)

## 해결하는 문제

이미지가 크고 레이어 순서가 엉망이면 빌드·배포·복구가 모두 느려진다.

```text
  빌드할 때                     배포할 때                         장애 때
  코드 한 줄 수정                새 노드가 이미지를 받아야 뜬다      롤백 = 옛 이미지를 다시 받아 띄움
  → 의존성 설치부터 다시          → 큰 이미지 = 긴 pull               → 노드에 없으면 또 pull
  → CI 매번 수 분                → 스케일 아웃이 트래픽을 못 따라감    → 복구 시간에 pull 시간이 더해짐
```

- 이미지에 빌드 도구(JDK 전체·컴파일러·패키지 관리자)가 남으면 크기만이 아니라 공격 표면도 늘어난다.
- 빌드 컨텍스트에 `.env`·`target/`·`.git`이 섞이면 느려지고, 비밀이 이미지에 들어간다.

쉬운 예: 이사 짐이다.
- 공구 상자(빌드 도구)까지 새 집에 옮기면 트럭이 커진다. 조립이 끝난 가구(산출물)만 옮기면 된다(멀티스테이지).
- 자주 바뀌는 것(옷)을 맨 아래 상자에 넣으면, 옷 하나 바꿀 때마다 위 상자를 다 내려야 한다(레이어 순서).

똑같은 구조다.\
트럭 = 이미지, 상자 = 레이어, 상자를 위에서부터만 다시 쌓을 수 있다 = 캐시 규칙이다.

실무 예:
- 2GB 이미지라 새 노드에서 pull에 수십 초~수 분이 걸린다(규모는 대역폭에 따라 다름). 받기가 실패하면 파드가 `ImagePullBackOff`로 멈춘다.
- `COPY . .`를 의존성 설치 앞에 둬서, 코드 한 줄만 바꿔도 의존성 레이어를 다시 만든다.
- distroless로 바꿨더니 `kubectl exec`가 `exec: "sh": executable file not found`로 막힌다.

## 동작·원리

### 1. 이미지 = 읽기 전용 레이어 스택, 레이어 이름 = 내용 해시

```text
  sn-ep-w06-multi (멀티스테이지, 실험)          크기(docker history)
  ┌────────────────────────────────────┐
  │ COPY app.jar                       │  1.69kB   ← 자주 바뀜: 맨 위
  │ entrypoint.sh (temurin 베이스)      │  5.31kB
  │ JRE 21 설치 (/opt/java/openjdk)     │  165MB
  │ apt 패키지                          │  42.8MB
  │ Ubuntu jammy 루트 파일시스템        │  78.1MB   ← 거의 안 바뀜: 맨 아래
  └────────────────────────────────────┘
  각 레이어 = 파일 변경분(diff) 묶음. 이름 = 내용의 sha256 → 같은 레이어는 한 번만 저장·전송
  (베이스의 0B 레이어 1개는 그림에서 뺐다 — RootFS 레이어 수는 6)
```

- 컨테이너가 뜰 때 이 레이어들을 overlayfs로 겹쳐 하나의 루트 파일시스템으로 보인다 → [os/28](../../os/28-containers-namespaces-cgroups/2-summary.md) §5.
- 레이어는 해시로 식별되므로, 같은 베이스를 쓰는 이미지는 베이스 레이어를 노드에서 공유한다. 앱 레이어만 새로 받으면 된다.

### 2. 빌드 캐시 = 레이어 접두사 일치

```text
  Dockerfile.bad                       Dockerfile.good
  1 FROM eclipse-temurin:21-jdk        1 FROM eclipse-temurin:21-jdk
  2 WORKDIR /app                       2 WORKDIR /app
  3 COPY . .              ← 코드 변경   3 COPY deps.lock fetch-deps.sh ./
  4 RUN sh fetch-deps.sh  ← 무효        4 RUN sh fetch-deps.sh        ← 캐시
  5 RUN javac ...         ← 무효        5 COPY src src                ← 코드 변경
                                       6 RUN javac ...               ← 무효
  규칙: 한 단계의 캐시가 깨지면 그 아래 단계는 전부 다시 실행
```

- Docker 문서("Build cache invalidation"): "Once the cache is invalidated, all subsequent Dockerfile commands generate new images and the cache isn't used."
- `COPY`·`ADD`는 파일 메타데이터로 체크섬을 계산하지만 mtime은 넣지 않는다(같은 문서). 내용이 같으면 시각이 달라도 캐시를 쓴다.
- `RUN`은 명령 문자열이 같고 앞 레이어가 같으면 캐시를 쓴다. `RUN apt-get update`처럼 바깥 세상이 바뀌어도 문자열이 같으면 재실행하지 않는다(같은 문서: RUN 캐시는 빌드 사이에 자동 무효화되지 않는다).
- 그래서 **자주 바뀌는 것을 아래(뒤)로** 둔다. Docker 문서("Optimize cache usage"): "Steps that change often should appear near the end of the Dockerfile".
- 캐시 키가 "앞 레이어 + 이 단계의 입력"이라는 점은 [07](../07-build-systems-and-reproducibility/2-summary.md)의 콘텐츠 해시 캐시와 같은 구조다.

### 3. 멀티스테이지 — 빌드 도구는 버리고 산출물만

```text
  FROM eclipse-temurin:21-jdk AS build     FROM eclipse-temurin:21-jre-jammy
  ┌──────────────────────────┐             ┌──────────────────────┐
  │ JDK·javac·jar            │  app.jar    │ JRE                  │
  │ src/  out/  app.jar  ────┼────────────>│ app.jar              │ ← 최종 이미지
  └──────────────────────────┘ COPY --from └──────────────────────┘
       (최종 이미지에 안 들어감)
```

- `COPY --from=<스테이지>`로 앞 스테이지의 파일만 가져온다. 앞 스테이지의 레이어는 최종 이미지에 들어가지 않는다.
- Docker 문서("Multi-stage builds"): BuildKit은 대상 스테이지가 의존하는 스테이지만 빌드한다. 레거시 빌더는 대상이 의존하지 않는 스테이지도 빌드한다.

### 4. 최소 베이스 — slim·distroless·alpine(musl)

| 베이스 | 들어 있는 것 | 주의 |
|---|---|---|
| 일반 배포판(Ubuntu·Debian) | 셸·패키지 관리자·유틸 | 크다, 공격 표면 |
| slim | 배포판에서 문서·일부 패키지 제거 | 필요한 도구가 없을 수 있음 |
| distroless | 앱과 런타임 의존성만, "package managers, shells or any other programs" 없음(distroless README) | 셸이 없어 `exec sh` 불가 → `:debug` 태그(busybox 셸)나 임시 디버그 컨테이너 |
| alpine | musl libc + busybox | glibc로 빌드된 동적 바이너리는 기본 상태에서 안 돈다(glibc 로더가 없다). DNS·스레드 스택 기본값이 glibc와 다르다 |
| scratch | 빈 파일시스템 | 정적 링크 바이너리면 그것 하나로 충분하다. 동적 프로그램은 로더·라이브러리를 함께 넣어야 한다(아래 jlink 판) |

- distroless README: 가장 작은 `gcr.io/distroless/static-debian13`은 약 2 MiB로 Alpine(~5 MiB)의 절반, Debian(124 MiB)의 2% 미만이라고 쓴다. Java용으로 `gcr.io/distroless/java21-debian13` 등이 있다.
- *musl*: alpine이 쓰는 C 표준 라이브러리. glibc와 ABI·동작이 다르다.
  - glibc 바이너리의 ELF 인터프리터는 `/lib64/ld-linux-x86-64.so.2`인데 기본 alpine 이미지에는 없다. 그래서 파일이 분명히 있는데 `no such file or directory`가 난다 → [os/29](../../os/29-linking-and-loading/2-summary.md) 장애 시나리오 4.
  - musl wiki "Functional differences from glibc": 리졸버가 네임서버들에 "in parallel"로 질의하고, DNS over TCP는 1.2.4 전까지 지원하지 않았다. 기본 스레드 스택은 128k(1.1.21 전 80k).
  - 예외: *gcompat*은 musl 위에서 glibc API와 glibc 로더 이름의 스텁을 주는 호환 라이브러리다. 이미 glibc로 컴파일된 바이너리용이다(gcompat README). 어떤 프로그램까지 도는지는 이 노트에서 실험하지 않았다.
  - Java는 보통 musl용으로 따로 빌드된 JRE를 쓴다. Docker Hub `eclipse-temurin`에 `21-jre-alpine` 태그가 있다(태그 목록 API로 확인, 받지는 않음).

### 5. jlink — 앱이 쓰는 모듈만 담은 런타임

- `jdeps --print-module-deps`로 앱이 쓰는 모듈을 찾고, `jlink --add-modules`로 그 모듈만 담은 런타임을 만든다.
- 실험의 HTTP 서버 앱은 `java.base,jdk.httpserver` 두 모듈만 필요했다. 런타임 크기: jlink 결과 `/opt/jre` 40M vs temurin 21 JRE `/opt/java/openjdk` 159M vs JDK 295M(`du -sh`).
- 경계: 리플렉션·`ServiceLoader`로 모듈을 동적으로 쓰면 `jdeps`가 못 찾는다. 빠진 모듈은 실행 중 `ClassNotFoundException` 등으로 드러난다 `[?]`(이 실험에서 재현하지 않음).

### 실험: 같은 앱, 세 가지 이미지

(실험, Docker Engine 29.1.3 레거시 빌더(buildx 미설치 → `DEPRECATED: The legacy builder is deprecated` 경고), 베이스는 로컬에 이미 있던 이미지만, 2026-10-05 — `scratchpad/ep/06/e8-image/app/Dockerfile.{single,multi,jlink}`)

```dockerfile
# single: JDK 이미지에서 빌드하고 그대로 실행
FROM eclipse-temurin:21-jdk
WORKDIR /app
COPY src src
RUN javac -d out src/ex/App.java && jar --create --file app.jar --main-class ex.App -C out .
ENTRYPOINT ["java", "-jar", "/app/app.jar"]

# multi: 빌드는 JDK, 실행은 JRE
FROM eclipse-temurin:21-jdk AS build
...
FROM eclipse-temurin:21-jre-jammy
COPY --from=build /app/app.jar /app/app.jar

# jlink: 필요한 모듈만 담은 런타임 + JRE를 지운 jammy 파일시스템
RUN jdeps --print-module-deps --ignore-missing-deps app.jar > modules.txt \
 && jlink --add-modules $(cat modules.txt) --strip-debug --no-man-pages --no-header-files --compress=zip-6 --output /jre
FROM eclipse-temurin:21-jre-jammy AS os
RUN rm -rf /opt/java
FROM scratch
COPY --from=os / /
COPY --from=build /jre /opt/jre
COPY --from=build /app/app.jar /app/app.jar
```

- jlink 판의 베이스: 로컬에 순수 `ubuntu:jammy`가 없고 새로 받지 않기로 해서, temurin jammy 이미지에서 `/opt/java`를 지운 파일시스템을 `FROM scratch`로 옮겨 썼다. 실무라면 `ubuntu`·`debian-slim`·distroless 베이스를 쓴다.

```text
single  size= 474 MB  layers= 9  save|gzip= 234 MB  app v1 on 21.0.12+8-LTS
multi   size= 286 MB  layers= 6  save|gzip= 108 MB  app v1 on 21.0.11+10-LTS
jlink   size= 160 MB  layers= 3  save|gzip=  71 MB  app v1 on 21.0.11+10-LTS
eclipse-temurin:21-jdk 474 MB layers=6
eclipse-temurin:21-jre-jammy 286 MB layers=5
eclipse-temurin:21-jdk-jammy 442 MB layers=5
```

- `size`는 `docker image inspect`의 압축 안 된 크기, `layers`는 `RootFS.Layers` 개수, `save|gzip`은 `docker save | gzip -1` 바이트(전송 크기의 대용치 — 레지스트리의 실제 압축 크기와는 다르다).
- single의 크기는 베이스 JDK 이미지와 같다. 앱은 kB 단위다. 474MB의 내역(`docker history`): JDK 설치 레이어 308MB, OS 100MB, apt 패키지 67MB.
- JDK에는 실행용 런타임도 들어 있다. 실행에 필요 없는 부분(컴파일러 등 빌드 도구)을 버린 JRE 이미지는 286MB로, 이 실험에서 188MB 작았다. 베이스 OS·패치 버전도 달라 188MB 전부가 빌드 도구 크기는 아니다(해석).
- 로컬에 있던 베이스들의 JDK 패치 버전이 달라(21.0.12 vs 21.0.11) 버전 문자열이 다르다. 크기 비교에는 영향이 작다(해석).
- pull 시간(예시 계산, 대역폭 가정): 100 Mbps(12.5 MB/s)라면 234MB ≈ 19초, 108MB ≈ 9초, 71MB ≈ 6초. 노드에 베이스 레이어가 이미 있으면 앱 레이어만 받는다.

## 쓰이는 자료구조·알고리즘

- **콘텐츠 주소(해시) 레이어** — 레이어 이름 = 내용의 sha256. 같은 레이어는 한 번만 저장·전송 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [os/28](../../os/28-containers-namespaces-cgroups/2-summary.md).
- **Merkle 구조** — 이미지 매니페스트가 레이어 해시 목록을 담고, 이미지 다이제스트는 매니페스트의 해시다. 레이어 하나만 바뀌어도 이미지 다이제스트가 바뀐다 → [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md). OCI image-spec: 매니페스트의 `layers`는 descriptor 배열이고(manifest.md), descriptor의 `digest`는 내용 바이트의 충돌 저항 해시로 내용을 식별한다(descriptor.md).
- **캐시 = 접두사 일치** — 캐시 키가 "부모 레이어 + 이 단계의 입력"이므로, 단계 목록의 가장 긴 일치 접두사까지만 재사용한다. 트라이에서 공통 접두사를 따라 내려가다 처음 어긋난 곳부터 새로 만드는 모양이다 → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **유니온 파일시스템(overlayfs)** — 위 레이어가 아래 레이어 파일을 가린다. 아래 레이어에서 지운 파일은 위 레이어의 "화이트아웃"으로 가려질 뿐 아래 레이어에는 남는다(그래서 `RUN rm`은 이미지를 줄이지 않는다) → [os/28](../../os/28-containers-namespaces-cgroups/2-summary.md) §5.
  - 실험(위 jlink 판의 `os` 스테이지): `eclipse-temurin:21-jre-jammy`(286,266,344바이트, 레이어 5)에서 `RUN rm -rf /opt/java`를 한 이미지는 286,266,344바이트, 레이어 6이었다. `docker history`의 그 단계 크기는 `0B`. 지운 JRE(159M)가 아래 레이어에 그대로 있다. jlink 판이 `FROM scratch` + `COPY --from=os / /`로 파일시스템을 **한 레이어로 다시 담은** 이유다.

## 적용 — 풀어나가는 법

### 1. 순서: 거의 안 바뀜 → 자주 바뀜

```dockerfile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline          # 의존성: pom.xml이 바뀔 때만 다시
COPY src src
RUN mvn -B -q package -DskipTests            # 코드: src가 바뀔 때만 다시

FROM eclipse-temurin:21-jre-jammy
RUN groupadd -r app && useradd -r -g app app
COPY --from=build /app/target/app.jar /app/app.jar
USER app
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

- 위 Dockerfile은 모양 예시다(이 호스트에서는 네트워크 없이 의존성을 받을 수 없어 실행하지 않았다). 같은 원리를 아래 실험에서 대역(stand-in)으로 측정했다.
- BuildKit을 쓰면 캐시 마운트로 로컬 저장소를 빌드 사이에 유지할 수 있다. Docker 문서의 예: `RUN --mount=type=cache,target=/root/.npm npm install`. Maven이라면 대상이 `/root/.m2`가 된다(해석 — 이 호스트는 buildx가 없어 실행하지 않음).

#### 실험: 레이어 순서와 캐시 적중

의존성 설치는 네트워크를 쓰지 않으려고 **대역**으로 만들었다: `fetch-deps.sh` = 8초 대기 + 30MB 파일 생성. 실제 다운로드 시간을 잰 것이 아니다.

(실험, Docker 29.1.3 레거시 빌더, `--cpu-quota 200000 --cpu-period 100000`, 2026-10-05 — `scratchpad/ep/06/e8-image/order/run.sh`)

```text
bad   cold(첫 빌드)          11.8s  캐시적중=1  다시실행=[3/5 4/5 5/5]
bad   변경 없음              0.1s  캐시적중=4  다시실행=[]
bad   App.java 한 줄 수정   11.7s  캐시적중=1  다시실행=[3/5 4/5 5/5]
bad   무관한 build.log 생성  11.6s  캐시적중=1  다시실행=[3/5 4/5 5/5]
good  cold(첫 빌드)          11.7s  캐시적중=1  다시실행=[3/6 4/6 5/6 6/6]
good  변경 없음              0.1s  캐시적중=5  다시실행=[]
good  App.java 한 줄 수정    2.5s  캐시적중=3  다시실행=[5/6 6/6]
good  무관한 build.log 생성   0.1s  캐시적중=5  다시실행=[]
```

- 시간은 실행마다 다르다. 사실 점검 재실행(같은 스크립트)에서는 bad 수정 12.5초, good 수정 2.9초였다. 다시 실행된 단계 목록과 캐시 적중 수는 두 실행이 같았다.
- bad: 코드 한 줄에도, 상관없는 로그 파일 하나에도 `COPY . .`가 깨져 의존성 단계(4/5)부터 다시 돈다 — 11.7초.
- good: 코드 변경은 `COPY src`(5/6)부터만 다시 — 2.5초. 로그 파일은 어떤 `COPY`에도 안 걸려 전부 캐시.
- mtime만 바꾼 경우(`touch -d 2020-01-01 App.java`, 다시 `touch App.java`)는 good에서 두 번 모두 `Using cache` 5/5였다. 이 호스트의 레거시 빌더에서도 내용이 같으면 캐시를 썼다 — 문서(BuildKit 기준 Docker Build 문서)의 설명과 같은 결과다.

### 2. 컨텍스트를 줄인다 — `.dockerignore`

```text
target/
.env
*.log
.git/
```

- 빌드 클라이언트는 컨텍스트 루트의 `.dockerignore`를 읽는다. Dockerfile마다 따로 두려면 Dockerfile과 같은 폴더에 "Dockerfile 이름 + `.dockerignore`"(예: `build.Dockerfile` → `build.Dockerfile.dockerignore`)를 둔다. 둘 다 있으면 Dockerfile 전용 파일이 우선한다(Docker 문서 "Build context". 이 호스트에서는 실행 확인 안 함).

#### 실험: `.dockerignore` 유무

컨텍스트에 150MB 가짜 빌드 산출물(`target/old-build.bin`)과 가짜 비밀(`.env`, 값 `DB_PASSWORD=dummy-not-real`)을 두고 bad Dockerfile(`COPY . .`)로 빌드했다.

(실험, Docker 29.1.3 레거시 빌더, 2026-10-05 — `scratchpad/ep/06/e8-image/order/run-ignore.sh`)

```text
.dockerignore 없음: Sending build context to Docker daemon    150MB  image=654MB
   /app 안: .env Dockerfile.bad Dockerfile.good deps.lock fetch-deps.sh out run-ignore.sh run.sh src target
DB_PASSWORD=dummy-not-real
.dockerignore 있음: Sending build context to Docker daemon  11.78kB  image=504MB
   /app 안: .dockerignore Dockerfile.bad Dockerfile.good deps.lock fetch-deps.sh out run-ignore.sh run.sh src
```

- 없으면: 컨텍스트 150MB를 데몬에 보내고, 이미지가 150MB 커지고, `.env`가 이미지 안에서 그대로 읽힌다.
- 있으면: 11.78kB, `target`·`.env`가 빠진다. 이미지 504MB = 베이스 474MB + 대역 의존성 30MB.

### 3. 셸 없는 이미지를 디버깅한다

#### 실험: scratch 이미지(셸 없음)와 디버그 컨테이너

(실험, `golang:1.23-alpine`에서 `CGO_ENABLED=0` 정적 빌드 → `FROM scratch`, 2026-10-05 — `scratchpad/ep/06/e8-image/noshell/`)

```text
$ docker run --rm sn-ep-w06-noshell
static binary, no shell in this image
$ docker image ls size: 2131070 bytes
$ docker run --rm --entrypoint sh sn-ep-w06-noshell
docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "sh": executable file not found in $PATH

Run 'docker run --help' for more information
exit=127
```

- 위 크기는 첫 빌드(바이너리가 한 줄 출력만 하던 판)의 값이다. 디버그 실험을 위해 20초 대기 기능을 넣어 다시 빌드한 판은 `/hello`가 2,135,979바이트였다.

실행 중인 컨테이너에 셸이 없을 때는 **다른 이미지의 컨테이너를 같은 PID 네임스페이스에 붙여** 들여다본다.

```text
$ docker exec sn-ep-w06-target sh
OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file not found in $PATH
exit=127
$ docker run --rm --pid=container:sn-ep-w06-target node:22-alpine sh -c "ps; ls -l /proc/1/root/"
PID   USER     TIME  COMMAND
    1 root      0:00 /hello wait
   17 root      0:00 sh -c ps; ls -l /proc/1/root/
   24 root      0:00 ps
total 2092
drwxr-xr-x    5 root     root           340 Oct  4 17:14 dev
drwxr-xr-x    2 root     root          4096 Oct  4 17:14 etc
-rwxr-xr-x    1 root     root       2135979 Oct  4 17:14 hello
dr-xr-xr-x  708 root     root             0 Oct  4 17:14 proc
dr-xr-xr-x   13 root     root             0 Oct  4 17:14 sys
```

- 디버그 컨테이너(셸 있음)에서 대상 프로세스(PID 1)를 보고, `/proc/1/root`로 대상의 파일시스템을 읽었다(디버그 컨테이너는 `-u 0`으로 실행).
- Kubernetes에서는 같은 발상이 임시 컨테이너다: `kubectl debug -it <pod> --image=busybox:1.28 --target=<container>`(Kubernetes 문서 "Debug Running Pods"). 문서는 distroless 이미지에 셸·디버그 도구가 없어 임시 컨테이너가 유용하다고 쓴다.

### 4. 진단 명령

```bash
docker history --format '{{.Size}}\t{{.CreatedBy}}' <이미지>   # 어느 단계가 큰가
docker image inspect -f '{{len .RootFS.Layers}}' <이미지>      # 레이어 수
docker build ... 2>&1 | grep -c "Using cache"                  # (레거시 빌더) 캐시 적중 단계 수
readelf -l <바이너리> | grep interpreter                        # 어떤 로더를 요구하나 (musl 문제)
```

## 장애 시나리오와 대처

### 1. 큰 이미지 → 스케일 아웃·롤백 지연, `ImagePullBackOff` (⚠)

- 현상: 트래픽이 몰려 노드를 늘렸는데 새 파드가 한참 `ContainerCreating`이다. 롤백도 느리다.
- 보이는 형태: 파드 이벤트의 `Pulling image …` 후 오래 대기. 받기에 실패하면 `ImagePullBackOff`.
- Kubernetes 문서: `ImagePullBackOff`는 이미지를 못 받아 컨테이너가 시작하지 못했다는 뜻이다. 재시도 간격을 늘려 가며 계속 시도하고, 상한은 300초(5분)다. `imagePullPolicy`를 생략하면, `:latest`가 아닌 태그나 다이제스트를 지정한 경우 `IfNotPresent`가 되어 노드에 있으면 안 받는다. 태그를 생략했거나 `:latest`면 `Always`가 된다.
- 원인: 빌드 도구·캐시·불필요 파일이 든 이미지. 베이스가 이미지마다 달라 노드에서 레이어 공유가 안 됨.
- 대처: 멀티스테이지·jlink·slim/distroless, 팀 공통 베이스로 레이어 공유, 롤백 대상 이미지를 노드에 미리 받아 두기(해석). 이름 오타·인증(`imagePullSecret`) 누락도 같은 상태를 낸다 — 이벤트 메시지를 먼저 읽는다.

### 2. `COPY . .`가 앞에 → 코드 한 줄에 의존성 재설치 (⚠)

- 현상: CI 빌드가 늘 수 분 걸린다. 캐시를 켰는데도.
- 보이는 형태: 레거시 빌더 로그에 의존성 단계가 `Running in …`(재실행). BuildKit이면 캐시를 쓴 단계에 `CACHED`가 붙는다(이 호스트는 레거시 빌더라 BuildKit 출력은 보지 않았다). 위 실험의 `bad App.java 한 줄 수정 11.7s`.
- 원인: 자주 바뀌는 파일이 의존성 설치 앞 레이어에 들어 있다. 무관한 파일(로그·`target/`)도 컨텍스트에 있으면 `COPY . .`를 깬다.
- 대처: 잠금 파일·빌드 정의만 먼저 `COPY`하고 의존성 설치, 그 뒤 소스. `.dockerignore`. BuildKit 캐시 마운트.

### 3. distroless에 셸이 없어 디버깅 막힘 (⚠)

- 현상: 장애 중 컨테이너에 들어가 보려는데 안 된다.
- 보이는 형태: `exec: "sh": executable file not found in $PATH`(위 실험 그대로).
- 원인: distroless·scratch에는 셸이 없다 — 의도된 설계다.
- 대처: 임시 디버그 컨테이너(`kubectl debug --target`, `docker run --pid=container:…`), distroless `:debug` 태그(busybox 셸)를 비운영 환경에서. 로그·지표를 밖으로 충분히 내보내 "들어가 볼" 필요를 줄인다.

### 4. alpine에 glibc 바이너리 → 있는 파일이 `not found`

- 현상: temurin(Ubuntu)의 JRE를 alpine 이미지에 복사했더니 안 돈다.
- 보이는 형태(실험, `node:22-alpine` = Alpine 3.24.1에 `eclipse-temurin:21-jre`의 `/opt/java/openjdk` 복사):

```text
$ docker run --rm sn-ep-w06-musl
exec /opt/java/bin/java: no such file or directory
exit=255
-rwxr-xr-x    1 root     root         13024 Apr 22 13:29 /opt/java/bin/java
ls: /lib64: No such file or directory
/lib/ld-musl-x86_64.so.1
3.24.1
```

- 원인: `readelf -l`로 본 `java`의 인터프리터는 `[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]`. alpine에는 `/lib64`가 없고 musl 로더(`/lib/ld-musl-x86_64.so.1`)만 있다. "없다"는 것은 java 파일이 아니라 로더다.
- 대처: musl용으로 빌드된 런타임(`eclipse-temurin:21-jre-alpine` 등)을 쓰거나 glibc 베이스(slim·distroless)를 쓴다. 로더 경로만 억지로 맞추는 것은 해법이 아니다 → [os/29](../../os/29-linking-and-loading/2-summary.md) 장애 시나리오 4.

### 5. 비밀이 이미지에 들어감

- 현상: 이미지 레지스트리 접근 권한만 있는 사람이 DB 비밀번호를 읽는다.
- 보이는 형태: 위 실험의 `DB_PASSWORD=dummy-not-real`이 이미지 안 `/app/.env`에서 읽힘.
- 원인: `.dockerignore` 없이 `COPY . .`. 나중 단계에서 `RUN rm .env`해도 아래 레이어에는 남는다(유니온 파일시스템).
- 대처: `.dockerignore`, 비밀은 실행 시점 주입(환경·시크릿 저장소). BuildKit 빌드 시크릿(`--mount=type=secret`)은 내용이 캐시에 들어가지 않는다(Docker 문서 "Build cache invalidation").

## 핵심 문장

- 이미지는 해시로 이름 붙은 읽기 전용 레이어의 스택이다. 같은 레이어는 노드에서 한 번만 받고 공유한다.
- 빌드 캐시는 레이어 접두사 일치다. 한 단계가 깨지면 그 아래는 전부 다시 실행되므로, 자주 바뀌는 것을 뒤에 둔다.
- 실험에서 single(JDK) 474MB, 멀티스테이지(JRE) 286MB, jlink 160MB였다. single은 멀티스테이지보다 188MB 컸고, 그 차이의 주된 원인은 최종 이미지에 남은 빌드용 JDK다.
- `.dockerignore`가 없으면 컨텍스트가 커지고, 무관한 파일이 캐시를 깨고, 비밀이 이미지에 들어간다.
- distroless는 셸이 없어 작고 안전하지만, 디버깅은 임시 디버그 컨테이너로 해야 한다.
- alpine은 musl이다. 기본 alpine에서 glibc 동적 바이너리는 로더가 없어 `no such file or directory`로 실패한다.

## 관련 주제·근거

- 선행
  - [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md) — 콘텐츠 해시 캐시, 재현 가능 빌드
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — overlayfs, 레이어
- 후속·연결
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — musl·glibc 로더 증상
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) — 이미지를 한 번 빌드해 승격
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 롤백 시간
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
  - [security 25 supply-chain-security](../../security/25-supply-chain-security/2-summary.md)
- 근거
  - Docker Docs — "Multi-stage builds"(BuildKit vs 레거시의 스테이지 선택) <https://docs.docker.com/build/building/multi-stage/> · "Build cache invalidation"(무효화 전파, COPY/ADD 체크섬·mtime 제외, RUN 캐시, ARG, secret) <https://docs.docker.com/build/cache/invalidation/> · "Optimize cache usage"(순서, `.dockerignore`, 캐시 마운트, 외부 캐시) <https://docs.docker.com/build/cache/optimize/> · "Build context"(`.dockerignore` 위치·문법·Dockerfile 전용 ignore) <https://docs.docker.com/build/concepts/context/> · "BuildKit"(기본 빌더) <https://docs.docker.com/build/buildkit/>
  - GoogleContainerTools/distroless README — 구성, 크기 비교, java21-debian13, `:debug` <https://github.com/GoogleContainerTools/distroless>
  - musl wiki "Functional differences from glibc" — 리졸버 병렬 질의·TCP(1.2.4), 스레드 스택 128k <https://wiki.musl-libc.org/functional-differences-from-glibc.html>
  - gcompat README(Adélie Linux) — musl 위 glibc 호환 API·로더 스텁 <https://git.adelielinux.org/adelie/gcompat>
  - Docker Docs "Base images" — scratch는 최소 이미지의 시작점 <https://docs.docker.com/build/building/base-images/>
  - Kubernetes Docs — "Images"(`ImagePullBackOff`, 상한 300초, `imagePullPolicy`) <https://kubernetes.io/docs/concepts/containers/images/> · "Ephemeral Containers"·"Debug Running Pods"(`kubectl debug --target`, distroless) <https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/>
  - Docker Hub `eclipse-temurin` 태그 목록(`21-jre-alpine` 존재) — hub.docker.com API 조회
  - OCI image-spec — manifest.md(`layers` = descriptor 배열)·descriptor.md(`digest` = 내용 식별 해시) <https://github.com/opencontainers/image-spec>
- 실험 목록(모두 2026-10-05, Docker Engine 29.1.3 레거시 빌더, 로컬 기존 베이스 이미지만, 태그 `sn-ep-w06-*`는 끝나고 삭제)
  - 이미지 크기·레이어: single(`eclipse-temurin:21-jdk`)·multi(`21-jdk`→`21-jre-jammy`)·jlink(`21-jdk-jammy` jdeps/jlink → scratch + jammy 파일시스템) — 474/286/160MB, 레이어 9/6/3, save|gzip 234/108/71MB
  - 레이어 순서: bad vs good Dockerfile, 의존성 대역(8초+30MB) — 코드 수정 11.7s vs 2.5s, mtime만 변경 시 캐시 5/5
  - `.dockerignore`: 컨텍스트 150MB→11.78kB, 이미지 654→504MB, `.env` 유입 여부
  - 셸 없는 이미지: Go 정적 바이너리 → scratch(2,131,070바이트), `exec: "sh"` 오류, `--pid=container:` 디버그 컨테이너
  - musl: `node:22-alpine`(Alpine 3.24.1)에 temurin JRE 복사 → `exec /opt/java/bin/java: no such file or directory`, `readelf` 인터프리터 확인
