# engineering-practice/08-container-image-optimization — 정답

## 정답

### 1. 크기가 영향을 주는 순간

- 스케일 아웃: 새 노드는 이미지를 받아야 파드를 띄운다. 큰 이미지 = 긴 pull = 트래픽을 늦게 따라감.
- 롤백: 옛 이미지가 노드에 없으면 다시 받는다. 복구 시간에 pull 시간이 더해진다.
- 예시 계산(대역폭 가정 100 Mbps): `save|gzip` 234MB ≈ 19초, 71MB ≈ 6초.
- 베이스 레이어가 이미 있으면 같은 해시의 레이어는 다시 받지 않는다. 앱 레이어만 받는다. 그래서 팀 공통 베이스가 pull을 줄인다.

### 2. 레이어 스택과 해시

```text
  ┌ COPY app.jar        1.69kB ┐ ← 자주 바뀜
  │ JRE 설치            165MB  │
  │ apt 패키지          42.8MB │
  └ Ubuntu 루트 FS      78.1MB ┘ ← 거의 안 바뀜
```

- 레이어 이름 = 내용의 sha256. 같은 레이어는 노드·레지스트리에 한 번만 저장·전송된다.
- `RUN rm`: 위 레이어에 삭제 표시(whiteout)만 둔다. 아래 레이어의 파일은 남는다. 실험에서 `eclipse-temurin:21-jre-jammy`(286,266,344바이트, 레이어 5)에 `RUN rm -rf /opt/java`를 한 이미지는 286,266,344바이트, 레이어 6 — 크기가 그대로였고 그 단계는 `0B`.

### 3. 레이어 순서와 캐시

- bad(`COPY . .` 먼저)
  - (a) 소스 수정: `COPY . .`부터 다시 → 의존성·컴파일 재실행(`11.7s`, 다시실행 `[3/5 4/5 5/5]`).
  - (b) 로그 파일 생성: 컨텍스트 내용이 바뀌어 똑같이 `COPY . .`부터(`11.6s`).
- good(잠금 파일 → 의존성 → 소스 → 컴파일)
  - (a) `COPY src`부터만(`2.5s`, `[5/6 6/6]`).
  - (b) 어떤 `COPY`에도 안 걸려 전부 캐시(`0.1s`).
- (c) `touch`: 문서상 COPY 체크섬은 mtime을 빼므로 캐시 그대로. 실험(good, 레거시 빌더)에서 과거·현재 시각 두 번 모두 `Using cache` 5/5.
- 주의: 의존성 단계는 8초 대기 + 30MB 파일의 **대역**이다. 실제 다운로드 시간이 아니다. 시간은 실행마다 다르다(사실 점검 재실행: bad 수정 12.5s, good 수정 2.9s — 다시 실행된 단계는 같았다).

### 4. 세 가지 이미지

| | 크기 | 레이어 | save\|gzip |
|---|---|---|---|
| single(JDK) | 474MB | 9 | 234MB |
| multi(JRE jammy) | 286MB | 6 | 108MB |
| jlink | 160MB | 3 | 71MB |

- single의 크기는 베이스 `eclipse-temurin:21-jdk`(474MB)와 같다. 앱은 kB 단위다. 474MB의 대부분은 JDK다. `docker history`에서 JDK 설치 레이어만 308MB였다(나머지는 OS 100MB·apt 67MB). JDK에는 런타임도 들어 있어, 빌드 도구를 버린 JRE 이미지(286MB)와의 차이는 188MB였다.

### 5. jlink의 경계

- 모듈 목록: `jdeps --print-module-deps --ignore-missing-deps app.jar` → 이 앱은 `java.base,jdk.httpserver`.
- 깨질 수 있는 앱: 리플렉션·`ServiceLoader`·설정 문자열로 클래스를 동적으로 찾는 앱. 정적 분석(jdeps)이 그 모듈을 못 보고, 실행 중에야 클래스가 없다는 오류가 난다(이 실험에서는 재현하지 않음).
- 그래서 jlink 이미지는 실제 기능 테스트(스모크)를 그 이미지로 돌려야 한다.

### 6. 최소 베이스

| 베이스 | 뺀 것 |
|---|---|
| slim | 배포판의 문서·일부 패키지 |
| distroless | 패키지 관리자·셸·기타 프로그램(앱과 런타임 의존성만) |
| alpine | glibc 대신 musl + busybox — 작지만 libc가 다르다 |
| scratch | 전부 — 정적 바이너리는 그대로, 동적 프로그램은 로더·라이브러리를 함께 넣어야 한다(실험의 jlink 판) |

- distroless README: `gcr.io/distroless/static-debian13` 약 2 MiB, Alpine(~5 MiB)의 약 50%, Debian(124 MiB)의 2% 미만.
- 실험의 scratch + Go 정적 바이너리 이미지는 2,131,070바이트였다.

### 7. `.dockerignore`가 없을 때

- 빌드 로그: `Sending build context to Docker daemon    150MB`.
- 이미지: 654MB(있을 때 504MB보다 150MB 큼).
- 내용: `/app`에 `.env`·`target`이 있고, `DB_PASSWORD=dummy-not-real`이 그대로 읽힌다.
- `.dockerignore`(`target/`, `.env`, `*.log`, `.git/`)를 넣으면 컨텍스트 11.78kB, 이미지 504MB, `.env`·`target` 없음.
- 덧붙여 무관한 파일 변경이 `COPY . .` 캐시를 깨는 것도 막는다(3번).

### 8. 셸 없는 컨테이너 들여다보기

- 이유: distroless·scratch에는 셸이 없다. `exec`는 그 이미지 안의 `sh`를 찾다가 실패한다 — 고장이 아니라 설계다.
- 도커 실험: 셸이 있는 다른 이미지 컨테이너를 대상의 PID 네임스페이스에 붙인다.
  - `docker run --rm --pid=container:sn-ep-w06-target node:22-alpine sh -c "ps; ls -l /proc/1/root/"` → `1 root 0:00 /hello wait`, `/proc/1/root/`에 `hello`·`dev`·`etc`·`proc`·`sys`.
- Kubernetes: 임시 컨테이너 `kubectl debug -it <pod> --image=busybox:1.28 --target=<container>`. distroless의 `:debug` 태그(busybox 셸)는 비운영 환경용.

### 9. alpine의 `no such file or directory`

- `readelf -l`: `[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]` — glibc 로더를 요구한다.
- 기본 alpine(실험: Alpine 3.24.1)에는 `/lib64`가 없고 `/lib/ld-musl-x86_64.so.1`만 있다. 없는 것은 java가 아니라 **로더**다.
- 대처: musl용 런타임(`eclipse-temurin:21-jre-alpine` 태그 존재), 또는 glibc 베이스(slim·distroless). 로더 경로만 맞추는 것은 해법이 아니다(심볼·ABI 차이 → os/29 장애 시나리오 4).

### 10. `ImagePullBackOff`

- 뜻: 이미지를 받지 못해 컨테이너가 시작하지 못했다. Kubernetes는 간격을 늘려 가며 재시도하고, 상한은 300초(5분)다.
- 먼저 볼 원인(문서가 드는 예): 잘못된 이미지 이름·태그, 사설 레지스트리의 `imagePullSecret` 누락. 파드 이벤트 메시지를 먼저 읽는다.
- 크기는 직접 원인보다 "받는 데 오래 걸려 파드가 늦게 뜨는" 쪽으로 드러나는 경우가 많다(해석). 노드 디스크 여유도 확인하고, 멀티스테이지·작은 베이스·공통 베이스 레이어로 줄인다.
