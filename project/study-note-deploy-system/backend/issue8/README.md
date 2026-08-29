# issue8 — 도메인-우선 재편: "레이어 안에 도메인"을 "도메인 안에 레이어"로

- 이슈 #15 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/16

## 1. 배경

issue6에서 전역 레이어(api/usecase/domain/infra)로 재편했는데, 게이트 리뷰에서 사용자
지적: 원한 건 **도메인별 폴더 안에 레이어**였다 — 응집은 도메인으로, 의존은 레이어로.
그리고 의존 역전도: "리포지토리 인터페이스를 서비스가 소유"하는 구조.

## 2. 검토한 방식들 (구조 비교)

```
[issue6 — 전역 레이어]              [issue8 — 도메인-우선 (선택)]
api/      ← 모든 컨트롤러            shared/{api, infra}   ← 도메인 무소속만
usecase/  ← 모든 서비스              sync/{api, usecase}
domain/   ← 모든 순수 로직           indexing/{usecase, domain}
infra/    ← 모든 클라이언트          search/{api, usecase, domain}
                                    content/{api, usecase, domain}
```

전역 레이어의 문제: sync 작업을 하려면 4개 폴더를 오간다. 도메인-우선은 한 폴더가
한 도메인의 전부 — 파일이 늘수록 이 응집이 이긴다. 사용자의 다른 프로젝트들과 구조가
같아지는 것도 실익.

### DIP — 서비스가 인터페이스를 소유한다

```kotlin
// sync/usecase/SourceControlPort.kt — 유즈케이스가 "필요한 능력"을 선언
interface SourceControlPort {
    fun syncToRemoteHead(): String
    fun changedMarkdown(prevSha: String, headSha: String): List<Pair<Char, String>>
    fun allMarkdown(): List<String>
}

// shared/infra/GitRepository.kt — 구현체가 여러 도메인의 포트를 다중 구현
class GitRepository : SourceControlPort, NoteSourcePort, DocumentReader { ... }
```

의존 화살표가 뒤집힌다: 전에는 `usecase → infra 구체 클래스`, 지금은
`usecase → (자기가 선언한) 포트 ← infra`. 테스트가 즉시 이득을 봤다 —
`mockk<GitRepository>()`(구체 클래스+git 지식)가 `mockk<SourceControlPort>()`(능력 3개)로.

## 3. 구현 중 마주친 문제

없음 — issue6에서 배운 것(rsync --delete·동작 보존 절차) 덕에 순항. 리팩토링 2회차의
비용이 1회차보다 훨씬 쌌다는 것 자체가 기록할 값어치: **테스트 24건이 안전망**이라
패키지를 통째로 옮겨도 green이 곧 "동작 보존" 증명이었다.

## 4. 결론

<도메인>/{api,usecase,domain} + shared, 포트 7종. 24건 green·계약 diff 0. PR: #16
