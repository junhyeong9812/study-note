# issue8 — 도메인-우선 재편: "레이어 안에 도메인"을 "도메인 안에 레이어"로 뒤집다

- 이슈 #15 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/16

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "도메인-우선으로 재편했다" 결론    ──▶     issue6은 뭐가 불편했나 → 무엇을
>                                           비교했나 → 왜 이 구조인가 서사
> 구조 비교표만 제시                 ──▶     [issue6 레이어]↔[issue8 도메인] 나란히
> DIP를 한 문단으로                  ──▶     의존 화살표가 어떻게 뒤집혔는지 +
>                                           실제 포트/구현체 diff
> DIP·포트 등 용어 던짐              ──▶     그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — issue6 재편이 반만 맞았다

issue6에서 패키지를 전역 레이어(api / usecase / domain / infra 네 폴더)로 재편했다. 그런데
게이트 리뷰에서 사용자가 지적했다. **원한 건 그게 아니었다.** 원한 구조는 "도메인별 폴더 안에
레이어"였다 — 즉 응집(관련된 것끼리 모으기)의 기준은 **도메인**으로 하고, 그 안에서 의존
방향만 레이어로 정리하는 것.

무엇이 문제였느냐면, 전역 레이어는 **"기능 하나를 만지려면 폴더 네 개를 오가야 한다."** 예를
들어 sync 기능 하나를 손보려면 api의 `SyncController`, usecase의 `SyncService`, domain의
로직, infra의 git 클라이언트를 각각 다른 폴더에서 찾아야 한다. 파일이 적을 때는 견딜 만하지만
도메인이 늘수록 이 왕복 비용이 커진다.

거기에 하나 더, 의존 역전(DIP) 요구도 있었다. "리포지토리 인터페이스를 서비스가 소유하는"
구조로 가자는 것.

> 용어 — DIP(Dependency Inversion Principle, 의존 역전 원칙): "상위 정책(유즈케이스)이 하위
> 세부(구체 클라이언트)에 의존하지 말고, 둘 다 **추상(인터페이스)** 에 의존하라"는 설계 원칙.
> 여기서는 유즈케이스가 "내가 필요한 능력"을 인터페이스로 선언하고, 인프라가 그걸 구현하게 한다.

---

## 2. 검토한 방식 — 두 구조를 나란히 놓고 고르다

무엇을 비교했느냐면, issue6의 전역 레이어와 이번 도메인-우선을 같은 화면에 놓고 "무엇이 어디로
가는지"를 봤다.

```
[issue6 — 전역 레이어]              [issue8 — 도메인-우선 (선택)]
api/      ← 모든 컨트롤러            shared/{api, infra}      ← 도메인 무소속 공용만
usecase/  ← 모든 서비스              sync/{api, usecase}      ← sync 도메인 전부
domain/   ← 모든 순수 로직           indexing/{usecase, domain}
infra/    ← 모든 클라이언트          search/{api, usecase, domain}
                                    content/{api, usecase, domain}

기능 1개 손보기:                    기능 1개 손보기:
  4개 폴더를 오감                     그 도메인 폴더 하나로 끝
```

전역 레이어의 문제가 위 오른쪽에서 사라진다 — 한 폴더가 한 도메인의 전부다. 파일이 늘수록
이 응집이 이긴다. 부수적으로 사용자의 다른 프로젝트들과 구조가 같아지는 것도 실익이었다
(여러 저장소를 오갈 때 같은 지도를 쓸 수 있다).

이 재편은 코드 동작을 바꾸지 않는 순수 리팩토링이라, 실제 커밋 stat도 대부분이 파일 이동
(`{ => content}/api/ContentController.kt` 식의 rename)이다. 새로 생긴 파일은 포트 선언들
(`sync/usecase/SourceControlPort.kt`, `indexing/usecase/ports.kt`, `search/usecase/ports.kt`,
`content/usecase/NoteSourcePort.kt`)이다.

### DIP — 서비스가 "필요한 능력"을 인터페이스로 소유한다

무엇이 문제였느냐면, 이전 구조에서 `SyncService`는 `GitRepository`라는 **구체 클래스**에
직접 의존했다. 그러면 sync 유즈케이스가 "git이라는 특정 구현"을 안다는 뜻이고, 테스트할 때도
git 지식이 통째로 딸려 온다.

그래서 유즈케이스가 **자기가 필요한 능력만** 인터페이스로 선언하게 했다.

파일: `src/main/kotlin/xyz/junproject/backend/sync/usecase/SourceControlPort.kt` (커밋 `147533a`, 신규)

```kotlin
/** sync가 필요로 하는 소스 저장소 능력 — 구현은 shared/infra/GitRepository (DIP: 서비스가 인터페이스 소유) */
interface SourceControlPort {
    fun syncToRemoteHead(): String
    fun changedMarkdown(prevSha: String, headSha: String): List<Pair<Char, String>>
    fun allMarkdown(): List<String>
}

class ShaUnresolvableException(message: String) : RuntimeException(message)
```

그리고 하나의 구현체가 여러 도메인의 포트를 **다중 구현**한다. `GitRepository`는 sync의
`SourceControlPort`, content의 `NoteSourcePort`, indexing의 `DocumentReader`를 한꺼번에 구현한다.

파일: `src/main/kotlin/xyz/junproject/backend/shared/infra/GitRepository.kt` (커밋 `147533a`, 신규)

```kotlin
/** study-note clone 볼륨 관리 — shell git (es-index.md D5-1: diff가 색인 입력의 정본). */
@Component
class GitRepository : SourceControlPort, NoteSourcePort, DocumentReader {
    ...
    override fun syncToRemoteHead(): String { ... }
    override fun changedMarkdown(prevSha: String, headSha: String): List<Pair<Char, String>> { ... }
}
```

indexing 쪽 포트도 같은 방식으로, "읽기·임베딩·저장"이라는 능력만 인터페이스로 뽑았다.

파일: `src/main/kotlin/xyz/junproject/backend/indexing/usecase/ports.kt` (커밋 `147533a`, 신규)

```kotlin
/** indexing 유즈케이스가 소유하는 포트들 — 구현은 shared/infra (DIP) */
interface DocumentReader { fun readFile(path: String): String }
interface TextEncoder { fun embed(texts: List<String>): List<List<Double>> }
interface IndexStore {
    fun ensureIndex()
    fun deleteByPath(path: String)
    fun bulkUpsert(documents: List<Pair<String, String>>)
    fun countByPath(path: String): Long
    fun deleteWhereShaNot(commitSha: String): Long
}
```

그 결과 `SyncService` 생성자 파라미터의 타입이 구체 클래스에서 포트로 바뀌었다.

파일: `src/main/kotlin/xyz/junproject/backend/sync/usecase/SyncService.kt` (커밋 `147533a`)

```kotlin
@Service
class SyncService(
    private val git: SourceControlPort,     // ← 전에는 GitRepository (구체 클래스)
    private val indexing: IndexingService,
    private val tree: TreeService,
    private val requestLog: RequestLog,
) { ... }
```

의존 화살표가 이렇게 뒤집힌다.

```
[기존]  usecase ────────▶ infra 구체 클래스 (GitRepository)
        유즈케이스가 특정 구현을 안다

[변경]  usecase ──▶ (자기가 선언한) 포트 ◀── infra 구현체
        유즈케이스는 "능력"만 알고, 구현이 그 능력을 채운다
```

테스트가 즉시 이득을 봤다. 전에는 `mockk<GitRepository>()`(구체 클래스 + git 지식 전부)를
흉내 내야 했는데, 이제 `mockk<SourceControlPort>()`(능력 3개짜리 작은 인터페이스)면 된다.

> 용어 — mockk: Kotlin의 테스트용 가짜 객체(mock) 라이브러리. 진짜 git 대신 "이 메서드는 이
> 값을 돌려줘라"라고 정해둔 가짜를 끼워 넣어 유즈케이스만 격리해 검증한다.

---

## 3. 구현 중 마주친 문제 — 없었다, 그리고 그게 기록할 값어치다

이 재편에서는 이렇다 할 문제가 없었다. 그런데 그 "무사고" 자체가 남길 만하다.

리팩토링 **2회차**(issue8)의 비용이 **1회차**(issue6)보다 훨씬 쌌다. 이유는 두 가지다. 첫째,
issue6에서 배운 절차(파일 이동은 `rsync --delete`로 흔적 없이, 동작 보존은 테스트 green으로
증명)를 그대로 재사용했다. 둘째, 테스트 24건이 안전망이라 **패키지를 통째로 옮겨도 green이
곧 "동작 보존" 증명**이었다 — 옮기고 테스트를 돌려 24건이 다시 green이면 밖에서 본 동작이
안 바뀌었다는 뜻이다.

이게 "특성 테스트를 먼저 green으로 세워두고 리팩토링한다"는 절차의 실측 효과다. 안전망이
있으면 큰 구조 변경도 겁내지 않고 할 수 있다.

---

## 4. 결론

구조는 `<도메인>/{api, usecase, domain} + shared`로 정리됐고, 유즈케이스가 소유하는 포트가
7종 생겼다(sync·indexing·search·content 도메인이 각자 필요한 능력을 선언, shared/infra의
`GitRepository`·`EsClient`·`EmbeddingClient`·`LlmClient`가 구현). 24건 green, 외부 계약
diff 0(API 응답은 한 글자도 안 바뀜). PR #16
