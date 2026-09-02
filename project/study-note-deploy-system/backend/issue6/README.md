# issue6 — 레이어 재편: 암묵적이던 의존 방향을 폴더로 못박다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #11 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/13

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                          [새 문서 — 지금 이것]
> "레이어 4단 채택" 결론만        ──▶   왜 재편했나(리뷰 부작용) → 왜 의존
>                                       역전은 뺐나 → 그래서 이렇게 (서사)
> git mv 했다고 서술              ──▶   [기존 폴더]↔[변경 폴더] ASCII 나란히
>                                       + 실제 커밋 641868d 이동/신설 diff
> rsync 사건 요약                 ──▶   실제 배포 명령 before/after diff
> ```
> 표현도 순화: "폴더로 박다" → "폴더로 못박다/명시".

---

## 1. 배경 — 왜 이 시점에 폴더를 다시 갈랐나

처음 구조는 **기능별 패키지**(sync / indexing / search / content)였고, 그 안에 Controller·
Service·Client가 섞여 있었다. 즉 레이어(계층)는 "클래스 이름 관례"로만 존재했다 —
`SearchController`, `SearchService`처럼 이름 끝에 역할이 붙어 있을 뿐, 폴더가 강제하지는
않았다.

> 용어 — 레이어(layer, 계층): HTTP를 받는 층(api), 흐름을 조립하는 층(usecase), 순수
> 로직(domain), 바깥 세상과 통신하는 층(infra). "무엇이 무엇을 import해도 되는가"의 방향을
> 정하는 뼈대다.

이름 관례만으로는 실제 부작용이 났다. issue5 리뷰에서 두 가지가 드러났다.

- **ES 접근이 두 곳으로 갈라졌다** — `search` 패키지와 `indexing` 패키지가 각자 ES를 찔러,
  타임아웃 같은 정책을 한 곳에서 못 걸었다(issue5 B3의 뿌리).
- **content가 sync 패키지를 역참조했다** — 읽기 전용이어야 할 콘텐츠 코드가 색인 파이프라인
  내부를 들여다봤다.

게이트 리뷰 도중 사용자가 지적했다: "도메인으로 응집도는 높이되 api/service/domain/infra
의존은 확실히 분리해야 하지 않나." 맞는 지적이라 재편에 착수했다.

---

## 2. 무엇을 고민했나 — 두 가지 선택

### 고민 1 — 폴더를 기능별로 둘까, 레이어별로 둘까

**대안(탈락): 기능별 패키지 유지 + 그 안에 레이어 폴더.** 기능 4개 × 레이어 4단 = 폴더
16개다. 파일이 18개뿐인 이 규모에는 과잉이다. 파일이 훨씬 늘어 "기능별로 다시 묶고 싶은"
날이 오면 그때 재검토하기로 하고 기각했다.

**선택: 레이어 4단.** 리포 전체를 4개 폴더로 가른다. 마침 llm 래퍼(app/api/domain/usecase/
validate)와 구조가 동형이라, 두 리포를 오가도 머릿속 지도가 같다.

### 고민 2 — 의존 역전(DIP)까지 갈까

**의존 역전(DIP, Dependency Inversion Principle)**은 "도메인이 인터페이스(포트)를 소유하고,
infra가 그 구현이 되는" 구조다. 이러면 usecase가 구체 클래스가 아니라 인터페이스에만 의존해
인프라를 갈아끼우기 쉬워진다.

이번엔 **도입하지 않기로** 했다. 지금 usecase는 infra 구체 클래스를 직접 쓴다. 인터페이스
한 겹은 "인프라를 갈아끼울 때"와 "테스트에서 인프라를 격리할 때" 가치가 생기는데 —
갈아끼울 계획이 아직 없고, 테스트 격리는 mockk(코틀린 목킹 라이브러리)가 구체 클래스를 그대로
mock해줘서 이미 된다. 그래서 "필요가 생기는 순간 뽑는다"로 결정을 기록해놨다. (이 결정은
이후 issue8에서 실제로 필요가 생겨 뒤집힌다 — DIP 포트 도입.)

---

## 3. 무엇을 어디로 옮겼나 — 기존 폴더 ↔ 변경 폴더

```
[기존 — 기능별 패키지]              [변경 — 레이어 4단]

sync/                               api/       ← HTTP 관심사
  SyncController.kt        ─────┐      SyncController.kt · SearchController.kt
  SyncService.kt          ──┐   ├──▶   ContentController.kt
  GitRepository.kt      ─┐  │   │      GlobalErrorHandler.kt · Envelope.kt
indexing/               │  │   │
  IndexingService.kt  ──┼──┘   │    usecase/   ← 흐름 조립(오케스트레이션)
  Chunker.kt          ─┼┐      │      SyncService.kt · IndexingService.kt
  DocClassifier.kt    ─┼┼──────┼──▶   SearchService.kt
  EsClient.kt         ┐│││     │
  EmbeddingClient.kt ┐││││     │    domain/    ← 순수 로직 (아무것도 import 안 함)
search/              ││││││    │      Chunker.kt · DocClassifier.kt
  SearchController.kt─┘│││ └────┘      SearchHit.kt · RewriteOutcome.kt
  SearchService.kt ──┘ │└──────────▶ infra/     ← 외부 시스템
  LlmClient.kt      ───┘ │            GitRepository.kt · EsClient.kt
content/                 │            EmbeddingClient.kt · LlmClient.kt
  ContentController.kt───┘            RequestLog.kt
common/ (Envelope·GlobalErrorHandler·RequestLog) → api/ 와 infra/ 로 분해

의존 방향:  api → usecase → (domain, infra) · infra → domain 허용 · domain은 무의존
```

이 변경은 커밋 641868d 한 방에 담겼다(git이 rename으로 추적). `--stat`에서 실제 이동이
보인다:

```
.../backend/{content => api}/ContentController.kt
.../backend/{common  => api}/GlobalErrorHandler.kt
.../backend/{search  => api}/SearchController.kt
.../backend/{sync    => api}/SyncController.kt
.../backend/{indexing => domain}/Chunker.kt · DocClassifier.kt
.../backend/{search  => infra}/LlmClient.kt
.../backend/{indexing => infra}/EsClient.kt · EmbeddingClient.kt
.../backend/{sync    => infra}/GitRepository.kt
.../backend/{indexing => usecase}/IndexingService.kt
.../backend/{search  => usecase}/SearchService.kt
.../backend/{sync    => usecase}/SyncService.kt
```

이동만 있는 게 아니라, 여러 곳에 흩어져 있던 순수 데이터 타입을 domain으로 **끌어냈다**.
예를 들어 `RewriteOutcome`·`SearchHit`는 원래 각각 LlmClient·SearchService 파일 안에
있었는데, "순수 로직·데이터는 domain, 통신은 infra"라는 방향에 맞춰 별도 파일로 분리했다.

`src/main/kotlin/xyz/junproject/backend/domain/RewriteOutcome.kt` (신설, 641868d):

```kotlin
package xyz.junproject.backend.domain

data class RewriteOutcome(
    val used: Boolean,
    val keywords: List<String> = emptyList(),
    val expanded: List<String> = emptyList(),
    val topic: String? = null,
    val docKind: String? = null,
)
```

그래서 infra의 `LlmClient`는 이제 domain의 타입을 import한다 — 방향(infra → domain)이 맞다:

```diff
- package xyz.junproject.backend.search
+ package xyz.junproject.backend.infra
+
+ import xyz.junproject.backend.domain.RewriteOutcome
```

리포 최상위 README에도 이 뼈대를 기록해놨다(커밋 641868d):

```
## 패키지 구조 (레이어 — 의존 방향 고정)
api → usecase → (domain, infra) · infra → domain 허용 · domain은 아무것도 import하지 않음
의존 역전(인터페이스)은 도입하지 않음 — 인프라 교체·테스트 격리 요구가 생기는 시점에 (결정 2026-08-27)
```

---

## 4. 리팩토링 절차 (동작 보존)

이건 "동작을 바꾸지 않는" 리팩토링이라, 순서를 고정해 안전하게 진행했다.

```
① 기존 테스트 22건 green 확인 (기준선 — 여기서 시작해 여기로 돌아온다)
② git mv로 파일 이동 + 패키지 선언·import만 수정 — 로직 변경 0
③ 테스트 다시 green + 배포 후 기존 API 응답 그대로 (계약 표면 diff 0)
```

핵심은 ②에서 **로직을 한 줄도 건드리지 않는 것**이다. 폴더와 패키지 선언·import만 바꾼다.
그래야 ③에서 green이 유지되면 "동작이 보존됐다"고 말할 수 있다.

---

## 5. 구현 중 마주친 문제 — 배포하자 앱이 무한 재시작

**증상:** 배포 후 스모크가 전부 연결 실패(exit code 000). 컨테이너 상태와 로그:

```
$ docker ps -a | grep backend-app
backend-app    Restarting (1) 38 seconds ago

$ docker logs backend-app | grep Caused
Caused by: org.springframework.context.annotation.ConflictingBeanDefinitionException:
  Annotation-specified bean name 'globalErrorHandler'
  for bean class [xyz.junproject.backend.common.GlobalErrorHandler]
  conflicts with existing, non-compatible bean definition of same name and class
  [xyz.junproject.backend.api.GlobalErrorHandler]
```

**진단:** 로그는 `common.GlobalErrorHandler`와 `api.GlobalErrorHandler`가 **동시에** 존재
한다고 말한다. 그런데 로컬엔 `common/`이 없다 — git mv로 `api/`로 옮겼으니까. 그렇다면
문제는 **서버의 소스 디렉토리**다.

당시 배포는 `rsync -a`(로컬 → 서버 파일 복사)였는데 **`--delete`가 없었다.** rsync는
`--delete` 없이는 "로컬에 있는 걸 서버로 복사"만 하고, "로컬에서 사라진 걸 서버에서 지우기"는
하지 않는다. 그래서 서버엔 옛 `common/ sync/ indexing/ search/` 패키지가 유령처럼 남았고,
Docker 빌드(`COPY src`)가 옛 파일과 새 파일을 **전부** 컴파일 → Spring이 같은 빈 이름 두
개를 보고 기동을 거부한 것이다.

> 용어 — 빈(bean): Spring이 관리하는 객체 인스턴스. `@Component`·`@Service`·
> `@RestControllerAdvice` 등이 붙은 클래스가 빈이 된다. 같은 이름·비호환 정의의 빈이 둘이면
> 어느 것을 쓸지 몰라 기동을 멈춘다.

**그래서 이렇게 했다 (배포 명령):**

```diff
- rsync -a -e "ssh -i $K" --exclude .git ... ./ jun@<host>:~/backend/
+ rsync -a --delete -e "ssh -i $K" --exclude .git --exclude .env ... ./ jun@<host>:~/backend/
+ #        ^^^^^^^^ 로컬에서 사라진 파일을 서버에서도 제거      ^^^^^^^^^^^^ 서버의 배포 설정은 보호
```

`--delete`를 켜면 서버에만 있어야 하는 파일(`.env` — 시크릿)까지 지워질 수 있어서
`--exclude .env`를 함께 넣었다.

> (참고: 이 rsync 명령은 backend 저장소가 아니라 배포 파이프라인 쪽 설정이라, backend git
> 이력에는 나오지 않는다. 위 diff는 당시 배포 스크립트의 실제 변경을 옮긴 것이다.)

**무엇을 배웠나:** "복사"만 하는 배포는 **삭제를 전달하지 못한다.** 파일 이동이 큰
리팩토링일수록 서버에 잔재가 남는다. 이번엔 Spring이 기동을 거부해줘서(시끄러운 실패) 즉시
잡았지만, 만약 충돌 없는 잔재였다면 옛 코드가 조용히 섞여 돌았을 것이다 — 시끄러운 실패가
오히려 고마운 경우다.

---

## 6. 결론

레이어가 이름 관례가 아니라 폴더로 강제되고, llm 래퍼와 구조가 동형이 됐다. 테스트 22건
green · 계약 표면(API 응답) 변화 0으로 동작 보존을 확인했다. 의존 역전은 필요가 생기는
시점(issue8)까지 미뤄뒀고, 그 결정 자체를 기록해 나중에 다시 고민하지 않게 했다. PR #13
