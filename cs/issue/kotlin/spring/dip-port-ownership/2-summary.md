# cs/issue/kotlin/spring/dip-port-ownership — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

**한 문장:** 폴더의 1차 축을 "레이어"가 아니라 "도메인"으로 잡고(응집), 그 안에서 유즈케이스가 자기가 필요한 능력을 **포트(인터페이스)로 선언·소유**하고 인프라가 그걸 구현하게 하면(DIP), 기능 하나가 한 폴더로 모이고 의존 화살표가 안쪽을 향한다.

```
[전역 레이어 — 응집 기준 = 레이어]        [도메인 우선 — 응집 기준 = 도메인]
api/      ← 모든 컨트롤러                  shared/{api, infra}   ← 도메인 무소속 공용
usecase/  ← 모든 서비스                    sync/{api, usecase}
domain/   ← 모든 순수 로직                 indexing/{usecase, domain}
infra/    ← 모든 클라이언트                search/{api, usecase, domain}
                                          content/{api, usecase, domain}
sync 하나 고치기: 4폴더 왕복               sync 하나 고치기: sync/ 폴더 하나

[의존 화살표 — DIP]
[전] usecase ───────▶ GitRepository(구체)      유즈케이스가 특정 구현을 안다
[후] usecase ──▶ (자기가 선언한)Port ◀── infra 구현체   유즈케이스는 "능력"만 안다
```

**왜 왕복이 사라지나:** 레이어를 없앤 게 아니라 응집의 **1차 기준**을 바꿨을 뿐이다. 도메인 안에는 여전히 api/usecase/domain 레이어가 있다. 다만 "sync에 관한 모든 레이어"가 `sync/` 한 폴더에 모여 있어, 한 기능을 만질 때 흩어진 네 폴더가 아니라 한 폴더만 연다. 도메인 무소속 공용(`GitRepository`·`EsClient` 같은 인프라, `Envelope` 같은 공용 api)만 `shared/`로 뺀다.

**DIP — 포트 소유권:** 핵심은 **인터페이스를 "쓰는 쪽"이 소유**하는 것이다. 예전에는 `SyncService`가 구체 클래스 `GitRepository`에 직접 의존해, 유즈케이스가 "git이라는 특정 구현"을 알았다. 이제 `SyncService`는 자기가 필요한 능력 3개(`syncToRemoteHead`·`changedMarkdown`·`allMarkdown`)만 `SourceControlPort`로 선언하고, 인프라의 `GitRepository`가 그걸 **구현**한다. 화살표가 뒤집혀 유즈케이스는 능력만 알고 구현은 밖에서 채워진다.

**다중 구현이 자연스러운 이유:** 포트를 능력 단위로 좁게 쪼개니, 한 구현체(`GitRepository`)가 여러 도메인의 좁은 포트를 동시에 구현한다(`SourceControlPort`·`NoteSourcePort`·`DocumentReader`). 각 유즈케이스는 자기 포트만 보므로 서로의 능력을 모른다(ISP). 테스트도 `mockk<GitRepository>()`(git 지식 전부) 대신 `mockk<SourceControlPort>()`(능력 3개짜리)면 된다.

**안전망:** 이 재편은 순수 리팩토링이라 "밖에서 본 동작 불변"이 증명 대상이다. **특성 테스트를 먼저 green으로 세워 두면**, 패키지를 통째로 옮긴 뒤 다시 돌려 green이면 그게 곧 동작 보존 증명이다. 2회차가 1회차보다 싼 이유 — 절차(이동은 흔적 없이, 보존은 테스트 green)를 재사용했고 안전망이 이미 있었다.

## 핵심 문장

- 폴더의 1차 축을 레이어→도메인으로 바꾸면 기능 하나가 한 폴더로 모인다(응집).
- DIP = 인터페이스를 "쓰는 쪽(usecase)"이 소유, "구현하는 쪽(infra)"이 채운다 — 화살표가 안쪽을 향한다.
- 능력 단위 좁은 포트 → 한 구현체의 다중 구현이 자연스럽고, 테스트가 작은 mock로 격리된다(ISP).
- 순수 리팩토링의 "동작 보존"은 특성 테스트 green이 증명한다 — 안전망이 큰 구조 변경을 가능케 한다.
- 리팩토링 비용은 절차 재사용 + 기존 안전망으로 회차가 갈수록 싸진다.
