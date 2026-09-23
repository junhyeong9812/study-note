# cross-cutting — 언어 무관 시스템 패턴

특정 언어·프레임워크가 아니라 **시스템 계층**에서 반복되는 이슈 패턴이다.\
코드가 옳아 보여도 그 아래 계층(OS·네트워크·저장소·동시성·검색엔진·렌더러)의 기본값과 경계에 부딪혀 터진 이슈가 여기 모인다.\
계층별로 나눴고, 언어에 뿌리내린 이슈는 각 언어 폴더에 있다.

## 공통 원리

```
  애플리케이션 코드 ("내 코드는 맞다")
        │  가정: 아래 계층이 알아서 해 준다
        ▼
  ┌──────────── 시스템 계층의 기본값·경계 ────────────┐
  │ 동시성 · 데이터 표현 · DB · 분산 · OS · 네트워크   │
  │ 인프라 · 보안 · 렌더링 · GUI · 검색엔진 · 테스트   │
  └────────────────────────────────────────────────────┘
        │  가정과 실제 정의가 다른 지점
        ▼
  에러 없이 틀린 결과 / 경계에서만 터지는 결함
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [concurrency/](concurrency/) | 10 | 순서·공유·취소 |
| [data/](data/) | 18 | 값의 표현·해석·키 |
| [database/](database/) | 3 | 스키마 이력·방언·트랜잭션 |
| [distributed/](distributed/) | 2 | 원격 결과와 권리의 단조성 |
| [document-rendering/](document-rendering/) | 2 | 텍스트·인쇄 레이아웃 |
| [gui-platform/](gui-platform/) | 2 | 좌표계·웹뷰 엔진 |
| [infra/](infra/) | 10 | 플랫폼·툴·배포 |
| [network/](network/) | 11 | 프로토콜·연결·프록시 |
| [os/](os/) | 6 | 프로세스·경로·터미널 |
| [reliability/](reliability/) | 23 | 실패가 삼켜지는 곳 |
| [search-engine/](search-engine/) | 8 | 색인·쿼리·점수 |
| [security/](security/) | 12 | 비밀·권한·신뢰 경계 |
| [testing/](testing/) | 5 | 초록불의 증거력 |

> 이 폴더의 메타 태그: `silent-failure`(22) · `resource-bounding`(16) · `least-privilege`(12) · `fail-closed`(3) · `race-condition`(8) · `contract-drift`(1) · `test-reliability`(5) · `parser-differential`(2) · `environment-drift`(3) · `encoding`(2) · `identity`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
