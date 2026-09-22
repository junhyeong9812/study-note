# issue5 — CI 정비: 빌드 1회화와 wrapper 검증

- 원본 PR: gateway #13 · devlog: `jun-bank/gateway/docs/devlog/pr-07-ci-cleanup.md`

## 1. 무엇이 문제였나

CI가 같은 소스를 두 번 컴파일하고 있었다.\
`gradlew test`로 한 번 컴파일하고, 그 뒤 Dockerfile의 빌드 스테이지가 `gradlew clean bootJar`로 또 컴파일했다.\
같은 소스를 두 번 빌드하니 잡 시간이 배로 들었다.

원인은 구조에 있었다 — Dockerfile이 이미지 안에서 gradle을 돌려 jar를 만드는 멀티스테이지였다.

> **멀티스테이지 빌드** — Dockerfile 안을 여러 스테이지로 나눠, 빌드용 스테이지에서 산출물을 만들고 실행용 스테이지로 넘기는 방식.\
> 예: 이미지 안에서 gradle을 돌려 jar를 만들면, CI가 밖에서 이미 만든 jar와 별개로 컴파일이 한 번 더 든다.

이 잔여는 issue3(발행 전 테스트)에서 이미 비용으로 기록돼 있던 것이다.\
낮은 stakes지만 배포 파이프라인의 입력이라, "테스트 실패 = 발행 차단" 순서를 깨지 않는 게 조건이었다.

## 2. 무엇을 고민했나

컴파일을 한 번으로 줄이는 방향은 정해져 있었고, 유지할 불변식이 조건을 좁혔다.

- **`gradlew build` 한 번으로** — `build`는 test와 bootJar를 한 번에 만든다(컴파일 1회).\
  그 산출 jar를 이미지가 재사용하도록 Dockerfile을 바꾼다. (채택)
- Dockerfile은 빌드 스테이지 없이, CI가 만든 jar를 COPY하는 단일 run 스테이지로 바꾼다.

깨지면 안 되는 불변식은 issue3에서 세운 "**테스트 실패 = 발행 차단**"이었다.\
`build`가 test를 포함하고 login·push 앞단에 있으면, test 실패 시 잡이 중단되고 이미지가 발행되지 않는다 — 별도 게이트가 필요 없다.

공급망 방어도 하나 더했다.

> **wrapper 검증(공급망 방어)** — 저장소에 커밋된 `gradlew`(gradle wrapper)가 변조되지 않았는지 실행 전에 확인하는 것.\
> 예: 누가 wrapper를 바꿔치기하면 빌드 과정에서 임의 코드가 돌 수 있으니, 그 전에 지문을 대조해 막는다.

`gradle/actions/wrapper-validation`을 gradlew 실행 **전**에 둬서 변조된 래퍼가 도는 것을 막았다.

## 3. 그래서 이렇게

스텝 순서 자체를 계약으로 삼았다 — issue3와 같은 방식이다.

```text
Gradle wrapper 검증               변조 래퍼 차단 (gradlew 실행 전)
        ↓
JDK 21 셋업
        ↓
빌드 (gradlew build)             test + bootJar를 한 번에 → 컴파일 1회
        ↓
GHCR 로그인                       test 실패 시 여기 도달 못 함
        ↓
빌드·push
```

Dockerfile은 재컴파일을 없애고, CI가 만든 jar를 COPY만 한다.

## 4. 코드 — 실제 커밋에서

워크플로는 순서가 곧 보증 수단이다.

```yaml
# build.yml (발췌) — 순서 자체가 보증 수단
- name: Gradle wrapper 검증       # 변조 래퍼 차단 (gradlew 실행 전)
  uses: gradle/actions/wrapper-validation@v4
- name: JDK 21 셋업 ...
- name: 빌드 (test + bootJar)      # 컴파일 1회
  run: ./gradlew --no-daemon build
- name: GHCR 로그인 ...            # test 실패 시 여기 도달 못 함
```

Dockerfile은 빌드 스테이지를 지우고 CI 산출 jar를 재사용한다.

```dockerfile
# Dockerfile (발췌) — 재컴파일 제거
# bootJar 는 CI 의 gradlew build 가 이미 만들었다(컴파일 1회). 이미지 안에서 다시 빌드하지
# 않는다(과거엔 이 Dockerfile 이 clean bootJar 를 돌려 컴파일이 총 2회였다).
FROM eclipse-temurin:21-jre AS run
COPY build/libs/*-SNAPSHOT.jar app.jar
```

## 5. 구현 중 마주친 문제

검증에서 그린 위장을 자가 점검했다.\
Gradle이 입력이 안 바뀌면 테스트를 캐시로 건너뛰고 성공을 보고하는 UP-TO-DATE 함정을, 로컬 확인을 `--rerun-tasks`로 강제해 배제했다.\
이미지 기동 스모크(actuator UP)로 CI가 만든 jar가 정상 실행됨을 확인했다.

잡 시간 전후 비교는 CI 실행에서만 가능해 이연했고, 머지 후 실측에서 이전 ~160초 → **88초**(약 45% 단축)로 확인됐다.

## 6. 결론

빌드 1회화의 잔여(컴파일 2회 비용)가 이 이슈로 닫혔다.\
잡 시간이 ~160초에서 88초로 약 45% 줄었고, "테스트 실패 = 발행 차단" 순서는 그대로 유지됐다.

낮은 stakes라 셀프체크로 채택했고(가역), 이걸로 G2 마일스톤(issue4 인가·issue5 CI)이 완주됐다.
