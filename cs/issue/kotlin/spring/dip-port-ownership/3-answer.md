# cs/issue/kotlin/spring/dip-port-ownership — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답

<!-- 질문 1:1 대응 -->

1. 전역 레이어는 응집의 기준을 **"같은 종류의 코드"** 로 잡는다 — 모든 컨트롤러는 api/에, 모든 서비스는 usecase/에. 그런데 사람이 실제로 하는 작업 단위는 "종류"가 아니라 **"기능(도메인)"** 이다. sync를 고치려면 sync의 컨트롤러·서비스·순수 로직·git 클라이언트가 필요한데, 이것들이 종류별로 흩어져 있으니 네 폴더를 왕복한다. 즉 "레이어 응집"은 코드를 이해·수정하는 실제 단위(기능)와 어긋나 있어, 한 기능을 만질 때 관련 없는 파일들 사이를 헤매게 만든다. 파일이 늘수록 이 왕복 비용이 커진다.
   > **응집(cohesion)** — 한 모듈 안의 요소들이 얼마나 한 목적으로 묶여 있는가. 높을수록 "함께 바뀌는 것이 함께 있다".

2. "도메인 안에 레이어"로 뒤집으면 **함께 바뀌는 것이 함께 모인다** — `sync/`를 열면 sync의 api·usecase가 다 있어 한 폴더로 끝난다. 좋아지는 것: 왕복 제거, 도메인 경계가 폴더로 드러남, 다른 저장소와 같은 지도 재사용. 그래도 남는 `shared/`는 **어느 한 도메인의 것이 아닌 공용** — `GitRepository`·`EsClient` 같은 인프라 구현체, `Envelope`·전역 에러 핸들러 같은 공용 api다. 레이어를 없앤 게 아니라 응집의 **1차 기준**만 바꿨다(도메인이 1차, 레이어가 2차). 도메인 안에 여전히 레이어가 있으니 의존 방향은 유지되고, 왕복만 사라진다.

3. **포트 소유** = 인터페이스를 정의·보유하는 주체가 그 인터페이스를 **쓰는 쪽(유즈케이스)** 이라는 뜻이다. 유즈케이스가 "나는 이런 능력이 필요하다"를 포트로 선언하고, 구현은 밖(infra)에서 그 포트를 구현한다. 화살표 변화: `[전] SyncService ─▶ GitRepository(구체)` — 유즈케이스가 특정 구현을 알고, 컴파일 의존이 안→밖으로 흐른다. `[후] SyncService ─▶ SourceControlPort ◀─ GitRepository` — 유즈케이스는 자기가 선언한 추상만 알고, 구현이 그 추상에 의존한다. 상위 정책과 하위 세부가 **둘 다 추상에 의존**하게 되어, 의존 화살표가 세부에서 추상 쪽(=안쪽)으로 뒤집힌다.
   > **DIP(의존 역전 원칙)** — 상위 정책이 하위 세부에 의존하지 말고, 둘 다 추상에 의존하라. 추상을 상위 정책이 소유하는 것이 핵심.

4. 포트를 능력 단위로 좁게 선언하니, 한 실물 구현체가 여러 좁은 포트를 동시에 만족시키는 것이 자연스럽다 — `GitRepository`는 물리적으로 하나의 git 볼륨 관리자지만, sync에게는 `SourceControlPort`, content에게는 `NoteSourcePort`, indexing에게는 `DocumentReader`로 보인다. 문제가 아닌 이유: 각 유즈케이스는 **자기 포트만** 보므로 서로의 능력을 모르고, 결합이 능력 단위로 끊긴다. 테스트 이득: 예전엔 `mockk<GitRepository>()`로 git 지식 전부를 흉내 내야 했지만, 이제 `mockk<SourceControlPort>()`(메서드 3개)만 세우면 유즈케이스를 격리해 검증한다 — 가짜로 채울 표면이 작아진다.

5. "동작을 안 바꿨다"를 증명한 것은 **테스트 스위트 전량 green**이다(24건). 밖에서 관찰 가능한 동작(API 응답)이 안 바뀌었는지는 그 동작을 고정한 테스트가 재편 후에도 통과하는지로 확인된다 — 외부 계약 diff 0. 특성 테스트를 먼저 green으로 세워 두면 안전망이 되는 이유: 리팩토링은 정의상 "동작 보존 구조 변경"이므로, 변경 **전**에 현재 동작을 테스트로 못 박아 두어야 변경 **후** 그 못이 그대로 박혀 있는지로 보존을 판정할 수 있다. 못을 나중에 박으면 이미 바뀐 동작을 "정답"으로 굳혀 버린다. 2회차가 싼 이유: 절차(파일 이동은 흔적 없이, 보존은 green으로 증명)를 재사용했고 안전망이 이미 서 있었다.
   > **특성 테스트(characterization test)** — 코드의 "현재 동작"을 있는 그대로 포착해 고정하는 테스트. 옳은 동작이 아니라 지금 동작을 기록해, 리팩토링의 회귀를 잡는 안전망.

6. **ISP**는 "클라이언트가 안 쓰는 메서드에 의존하지 않게 인터페이스를 잘게 쪼개라"이고, **DIP**는 "그 추상을 상위가 소유하라"이다. 여기서 둘은 함께 작동한다 — 유즈케이스마다 "필요한 능력만" 좁은 포트로 선언(ISP)하고, 그 포트를 유즈케이스가 소유(DIP)한다. 큰 `GitRepository` 하나에 모두 의존하게 두면, content가 sync용 메서드 변경에도 재컴파일·재테스트되는 **부수 결합**이 생긴다. 능력 단위 포트로 쪼개면 결합이 "실제로 쓰는 능력"으로 좁혀져, git 구현이 어떻게 바뀌든 그 능력을 안 쓰는 도메인은 영향받지 않는다.
   > **ISP(인터페이스 분리 원칙)** — 클라이언트는 자신이 사용하지 않는 메서드에 의존하도록 강요받아선 안 된다. 뚱뚱한 인터페이스를 역할별로 쪼갠다.

## 발생한 문제 / 해결 (추상 원리)

**문제:** ① 응집 기준을 레이어로 잡아 기능 하나가 여러 폴더로 흩어짐(왕복 비용). ② 유즈케이스가 구체 클래스에 직접 의존해 특정 구현 지식이 정책에 스며듦(테스트·교체 곤란).

**해결:** ① 폴더의 1차 축을 도메인으로 재편(`<도메인>/{api,usecase,domain} + shared`) — 함께 바뀌는 것을 함께 둔다. ② 유즈케이스가 "필요한 능력"을 좁은 포트로 선언·소유(DIP+ISP), 인프라 구현체가 여러 포트를 다중 구현. ③ 이 순수 리팩토링의 동작 보존은 **먼저 세워 둔 특성 테스트 green**으로 증명 — 외부 계약 diff 0.

## 이번 프로젝트 사례

- [backend/issue8](../../../../../project/study-note-deploy-system/backend/issue8/) — 전역 레이어(api/usecase/domain/infra)를 도메인 우선(`sync`·`indexing`·`search`·`content` + `shared`)으로 재편. 유즈케이스가 포트를 소유하도록 DIP 적용(`SyncService`가 구체 `GitRepository` → `SourceControlPort`에 의존), 한 구현체가 여러 포트를 다중 구현. 24건 green이 곧 동작 보존 증명이라 외부 계약 diff 0. 리팩토링 절차·안전망은 [refactoring 계열]과도 통한다.

## 검증 기록

- 2026-09-23: 이슈8 README + 코드 대조 작성(Claude 초안). 코드 확인:
  - 포트 소유(usecase 소속): `.../sync/usecase/SourceControlPort.kt` L4-8, `.../indexing/usecase/ports.kt` L4-18 (`DocumentReader`·`TextEncoder`·`IndexStore`), `.../search/usecase/ports.kt` L6-16 (`QueryRewritePort`·`QueryEncoder`·`SearchIndexPort`), `.../content/usecase/NoteSourcePort.kt` L6-12.
  - 다중 구현(shared/infra): `.../shared/infra/GitRepository.kt` L18 (`class GitRepository : SourceControlPort, NoteSourcePort, DocumentReader`), `.../shared/infra/EsClient.kt` L14 (`class EsClient : IndexStore, SearchIndexPort`).
  - 구체→포트 의존 역전: `.../sync/usecase/SyncService.kt` L20-25 (생성자 `private val git: SourceControlPort`).
  - 동작 보존 증명(24건 green·외부 계약 diff 0): issue8 README §3·§4.
