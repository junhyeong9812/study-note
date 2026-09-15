# jun-bank — 배포·인프라 개발 기록

카드사+뱅킹 시스템 jun-bank를 만들면서 **"이 문제를 왜 이렇게 풀었나"** 를 이슈 단위로 남긴 기록이다.
코드는 각 repo에 있으니 여기서 반복하지 않고, 결정의 이유와 안 고른 후보를 남긴다.

> 이 기록의 범위는 **배포 파이프라인·분산 배포·인프라 안전 계약**이다.
> 도메인(결제·정산·원장) 업무 로직은 아직 스켈레톤이라 여기에 없다 — 인프라를 먼저 체화한 뒤 구현할 계획이다.

## 영역

이슈 하나 = 폴더 하나(`<영역>/issueN/`). 골격은 [reference/study-note-guide §2-B](../../reference/study-note-guide.md).

| 영역 | 무엇인가 | 원본 devlog |
|------|---------|------------|
| [infra/](infra/) | 배포 오케스트레이터 — 엣지→2관문(HMAC·OIDC)→배포 창 락→블루-그린·위성 RPC | `jun-bank/infra/docs/devlog/` |
| [core/](core/) | 코어 서비스의 CD·compose 동봉 | `jun-bank/core/docs/devlog/` |
| [gateway/](gateway/) | 게이트웨이 CD·동적 라우트·블루-그린 전환·내부 인가 | `jun-bank/gateway/docs/devlog/` |
| [settlement/](settlement/) | 정산 — 원격 위성(.158) 배포 대상 신설 | `jun-bank/settlement/docs/devlog/` |
| [ledger/](ledger/) | 원장 — 원격 위성(.164) 배포 대상 신설 | `jun-bank/ledger/docs/devlog/` |

## 전체 구조 한눈에

```text
[GitHub Actions]  빌드 → GHCR digest → 서명 manifest(compose 동봉)
        ↓
[오라클 엣지 nginx]  TLS 종단·전달만 (인증 안 함)
        ↓
[.9  ROLE=main]  관문1 HMAC → 관문2 OIDC → 배포 창 락
        ↓
   배포 대상 넷
        ├── core       : 로컬 블루-그린 (.9)
        ├── gateway    : 재기동 교체 (.9)
        ├── settlement : 서명 RPC → .158 위성 agent
        └── ledger     : 서명 RPC → .164 위성 agent
```

> 아키텍처 해설은 docs repo의 `study/tech/infra-journey/`, 결정 정본은 `architecture/adr/`(ADR-027·030·031·032)에 있다.

## 이슈 목록

### infra — 배포 오케스트레이터 (15)

1. [레이아웃과 배포 스키마 DDL](infra/issue1/) — 기록의 계약부터
2. [HTTP 골격](infra/issue2/) — 아직 아무것도 실행하지 않는 서버
3. [게이트 1: HMAC](infra/issue3/) — 서명만으로는 재전송을 못 막는다
4. [게이트 2: OIDC](infra/issue4/) — claim을 sub 하나로 판정하지 않는다
5. [배포 모드](infra/issue5/) — 모르면 실행하지 않는다
6. [배포 창 락](infra/issue6/) — 남의 락을 풀 수 없게
7. [HTTP를 배포 시퀀스로](infra/issue7/) — 어떤 실패가 락을 쥔 채 사람을 부르나
8. [로컬 dispatch](infra/issue8/) — pull·up·헬스, 결과를 무엇으로 부를까
9. [JWKS 실 공개키 페치](infra/issue9/) — 인증 뿌리에서 샌 fail-open
10. [false-UNKNOWN](infra/issue10/) — 배포는 됐는데 배포가 실패했다
11. [블루-그린 전환](infra/issue11/) — 정리는 미전환이 보증됐을 때만
12. [repo별 allowlist](infra/issue12/) — 확장이 곧 구멍이 되지 않게
13. [Outcome 분리·서비스 결박](infra/issue13/) — 두 결함의 한 근원
14. [compose 동봉](infra/issue14/) — 이미지는 고정, 기동 정의도 고정
15. [위성으로 배포를 넓히다](infra/issue15/) — 모른다를 상태로

### core — 코어 서비스 (2)

1. [deploy.yml 입력 하드닝](core/issue1/) — 리뷰가 찾은 세 겹의 구멍
2. [정본 compose 신설 + manifest 동봉](core/issue2/)

### gateway — 게이트웨이 (6)

1. [동적 라우트 + 블루-그린 전환 내부 API](gateway/issue1/)
2. [gateway CD](gateway/issue2/) — 네 번째 배포 대상이 되다
3. [이미지 발행 전 테스트](gateway/issue3/) — 발행 관문
4. [/internal 관리 표면 HMAC 인가](gateway/issue4/)
5. [CI 정비](gateway/issue5/) — 빌드 1회화와 wrapper 검증
6. [정본 compose 신설 + manifest 동봉](gateway/issue6/)

### settlement — 정산 (1)

1. [CD 신설](settlement/issue1/) — 원격 위성(.158) 배포 대상이 되다

### ledger — 원장 (1)

1. [CD 신설](ledger/issue1/) — 원격 위성(.164) 배포 대상이 되다
