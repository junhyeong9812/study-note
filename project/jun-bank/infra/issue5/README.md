# issue5 — 배포 모드: 모르면 실행하지 않는다

- 원본 PR: infra #12 · devlog: `jun-bank/infra/docs/devlog/pr-12-mode-failclosed.md`

## 1. 무엇이 문제였나

배포 모드를 읽는 코드가 "모르면 dev"인지 "모르면 승인"인지가 문제였다.\
이 프로젝트에서 fail-open이 실제 사고 형태로 확인된 첫 자리 중 하나다.

> **모드(dev / operational)** — 배포를 방아쇠 하나로 자동 진행할지(dev), 사람의 승인을 받을지(operational).\
> 예: "dev는 환경이 아니라 모드다" — 스테이징이 따로 없고, dev에서도 락·서명·이력·적용 순서는 그대로이며 자동이 되는 것은 방아쇠 하나뿐이다.

문제는 둘이었다.\
첫째, **승인 게이트가 장애로 열릴 수 있다** — "모드를 모르면 dev"는 저장 장애가 곧 승인 우회가 되는 형태다.\
둘째, **토글과 요청이 경쟁한다** — 모드 토글은 배포 요청이 아니라 락을 잡지 않아 배포 진행 중에도 일어날 수 있고, 수락 시점과 적용 시점 사이에 모드가 바뀌면 승격 전 모드로 실행된다.

## 2. 무엇을 고민했나

- **모드를 모르면 dev로 볼까, 운영으로 볼까.** — 운영(승인 필요)으로 닫았다.\
  dev로 열면 저장 장애가 곧 승인 우회다.\
  저장 접근 실패·모드 부재·미지의 모드 문자열 전부를 operational로 닫는다.

> **fail-closed** — 실패했을 때 열지 않고 닫는(막는) 방향으로 무너지는 것.\
> 예: 모드를 못 읽으면 자동 배포가 아니라 "승인 필요"로 닫아, 장애가 승인 우회로 이어지지 않게 한다.

- **장애로 닫힌 것과 원래 운영인 것을 같이 볼까, 구별할까.** — `FailClosed` 플래그로 구별했다.\
  기록이 없으면 "승인 없이 배포된 것"과 "승인이 필요 없는 대상이었던 것"이 사후에 구별되지 않는다.

- **store가 모드 행이 없을 때 기본값을 지어낼까, 에러를 올릴까.** — `ErrNoMode`를 올린다.\
  fail-closed 판정 자리를 호출자 한 곳으로 유지하려면, store가 기본값을 지어내면 안 된다.

## 3. 그래서 이렇게

모드 판정은 게이트가 아니라 오케스트레이션의 소유다 — 대상(target)은 검증된 manifest에서 오고, 원자 검증은 락 획득과 같은 자리에서 서야 하기 때문이다.\
판정은 세 갈래 모두 안전한 쪽으로 닫는다.

```text
모드 조회 r.Current(target)
        ↓
   저장 접근 실패?      ── 예 ──> operational · 승인필요 · FailClosed=true
        ↓ 아니오
   모드 부재(ErrNoMode)? ── 예 ──> operational · 승인필요 · FailClosed=true
        ↓ 아니오
   미지의 문자열(손상)?  ── 예 ──> operational · 승인필요 · FailClosed=true
        ↓ 아니오
   저장된 dev / operational 그대로
```

## 4. 코드 — 실제 커밋에서

```go
// internal/deploy/mode.go:47-70 (발췌) — fail-closed 3분기
// 저장 접근 실패·mode 부재(ErrNoMode)·미지의 mode 문자열(손상)은 전부
// operational(승인 필요)로 닫는다 — fail-closed(DO-17 ⑷). "모드를 모르면 dev"가 아니다:
// 승인 게이트가 장애로 열리면 승인 없이 배포가 나가므로, 모르면 승인 쪽으로 닫는다.
func DecideMode(ctx context.Context, r ModeReader, target string) ModeDecision {
    mode, version, err := r.Current(ctx, target)
    if err != nil {
        return ModeDecision{Mode: ModeOperational, ApprovalRequired: true, FailClosed: true}
    }
    ...
}
```

## 5. 구현 중 마주친 문제

가장 뼈아픈 것은 **단조 version의 fail-open**이었고, 코드가 바뀌었다.

> **단조(monotonic) version** — "현재 모드"를 항상 최댓값 version의 행으로 정하는 규약.\
> 예: 새 토글은 더 큰 version으로만 들어와야 "가장 최근"이 되는데, 더 작은 version이 끼어들 수 있으면 최근 토글이 묻힌다.

`UNIQUE(target, mode_version)` 제약은 중복만 막고, 더 작은 새 version의 삽입은 허용했다.\
dev/v2가 있는 상태에서 operational/v1을 넣어도 성공하고, "현재"는 최댓값 행이므로 계속 dev/v2다 — 성공한 운영 토글이 반영되지 않는다.\
version 결정권을 호출자에게서 빼앗아, 프로시저가 max+1을 원자로 계산하게 고쳤다.

```sql
-- deploy/schema/02_procedures.sql:351-363 (발췌) — 프로시저가 max+1을 원자 계산
CREATE PROCEDURE `sp_mode_append`(...)
BEGIN
  INSERT INTO `deploy_mode` (`target`, `mode`, `mode_version`, `actor`)
  SELECT p_target, p_mode, COALESCE(MAX(`mode_version`), 0) + 1, p_actor
    FROM `deploy_mode`
   WHERE `target` = p_target;
END $$
```

Go 쪽에서는 version 파라미터 자체가 사라졌다 — 임의 version을 넘길 자리가 없으니 낮은 version이 들어갈 길이 원천 차단된다.\
둘째는 TOCTOU였다 — `VerifyModeUnchanged`가 독립 SELECT 후 version만 비교하므로, 검증 직후·락 획득 전에 토글이 나면 이미 반환된 OK로 자동 배포가 이어진다.\
이번 수정은 재조회한 모드의 유효성 검사까지였고, 창을 진짜로 닫는 락·모드 단일 트랜잭션 원자성은 S2(#14)로 명시 이월하며 코드 주석에 `[구현 검증]`으로 남겼다.

## 6. 결론

S1 마일스톤이 여기서 닫혔다.\
이월된 TOCTOU는 이슈 #14(HTTP→오케스트레이션 배선 = issue7)로 넘어간다.\
모드 대상 ENUM은 나중에 gateway가 네 번째 배포 대상이 되며 마이그레이션으로 확장된다.
