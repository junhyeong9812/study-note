# issue8 — 로컬 dispatch: pull·up·헬스, 그리고 "결과를 무엇으로 부를까"

- 원본 PR: infra #22 · devlog: `jun-bank/infra/docs/devlog/pr-22-local-dispatch.md`

## 1. 무엇이 문제였나

여기서 처음으로 **부작용이 있는 코드**가 들어왔다.\
그전까지는 요청을 받아 락을 잡는 데까지였고, 실제로 이미지를 받고 컨테이너를 띄우는 실행 층은 스텁이었다.\
스텁을 실 dispatcher로 바꾸는 순간, "어떻게 실행하나"보다 "실행 결과를 무엇으로 부를 것인가"가 더 큰 문제가 됐다.

> **부작용(side effect)** — 함수가 값만 돌려주는 게 아니라 바깥 세상을 바꾸는 것.\
> 예: 컨테이너를 실제로 띄우면, 실패해도 "안 한 셈" 칠 수 없는 흔적이 서버에 남는다.

부작용이 생기면 실패를 세 상태로 갈라야 한다.

- pull 실패는 compose를 건드리지 않았으니 부작용 0 — **UNEXECUTED**(미실행).
- up·헬스 실패 후 정리가 성공하면 원상복구됐으니 역시 미전환 — **UNEXECUTED**.
- 정리까지 실패하면 새 컨테이너가 남았을 수 있으니 — **UNKNOWN**(모름).
- 새 컨테이너가 뜨고 digest 대조·헬스를 통과하면 — **COMPLETED**(완료).

특히 헬스체크의 **그린 위장**이 반복 주제였다.\
"프로세스가 떴다"만 보는 헬스체크는 DB 권한 오설정·스키마 불일치를 통과시킨다.

> **그린 위장(silent COMPLETED)** — 실제로는 실패인데 지표가 초록이라 완료로 보이는 것.\
> 예: `:latest`나 오타 이미지가 떠도 헬스는 "떴는가"만 보지 "무엇이 떴는가"는 못 본다.

## 2. 무엇을 고민했나

- **변이 명령에 자체 재시도 루프를 둘까.** — 두지 않기로 했다.\
  pull·up·down 같은 변이 명령은 각 1회만 실행한다.\
  UNKNOWN 상태에 단순 재시도를 걸면 부분 실행 위에 또 부분 실행을 쌓기 때문이다.
- **lease를 실행 중에 갱신할까(갱신 goroutine), 아니면 무갱신으로 갈까.** — 무갱신을 택했다.\
  대신 기동 시점에 `lease ≥ 단계예산 + 헬스deadline + 정리 + 전환 + slack`을 검증해, 미달이면 기동 자체를 거부한다.\
  갱신 goroutine은 코드가 복잡해지고 "갱신이 멈춘 걸 못 본" 창을 새로 만든다.

> **lease** — 배포 창을 한 실행자만 쓰도록 빌려주는 시한부 권리.\
> 예: "이 시간 안에 끝내라"는 임대 계약이라, 시간이 모자라면 아예 시작을 안 하는 게 안전하다.

- **digest 대조를 헬스 앞에 둘까 뒤에 둘까.** — 앞에 뒀다.\
  헬스는 "떴는가"만 보므로, "무엇이 떴는가"를 먼저 확정해야 그린 위장이 막힌다.

## 3. 그래서 이렇게

특권 실행은 **열거된 명령만 argv 슬라이스로** 실행한다.\
셸 해석을 거치지 않으므로 "raw shell 금지"가 코드 형태로 강제된다.

> **argv 슬라이스** — 명령을 문자열 한 줄이 아니라 `["docker","pull",...]`처럼 조각 배열로 넘기는 것.\
> 예: 셸을 안 거치니 `; rm -rf` 같은 주입이 문법적으로 불가능하다.

네 단계를 순서대로 밟고, 각 단계 실패가 어느 상태인지 미리 못 박았다.

```text
1. pull  (이미지 받기)          실패 = compose 미접촉 = UNEXECUTED
        ↓
2. up    (green 기동)           down 성공=UNEXECUTED · down 실패=green 잔존 가능=UNKNOWN
        ↓
3. verify digest (무결성 대조)   실패 = 정리 후 UNEXECUTED  ← 헬스보다 먼저
        ↓
4. health (CD-1 헬스)           실패 = green 종료·blue 유지 = 미전환
        ↓
   COMPLETED
```

dispatch 전체를 lease 안에 **예산으로 가둔다** — 시간이 모자라면 시작하지 않는다.

## 4. 코드 — 실제 커밋에서

네 단계와 상태 매핑이 그대로 코드에 있다.

```go
// internal/deploy/dispatcher.go:261-292 (발췌) — 4단계와 상태 매핑
// 1. 이미지 pull. 실패 = 부작용 0(compose 미접촉) = UNEXECUTED.
if err := exec.Pull(phaseCtx, imageRef); err != nil {
    return StateUnexecuted, ...
}
// 2. green 기동. down 성공=미전환(UNEXECUTED), down 실패=green 잔존 가능(UNKNOWN).
if err := exec.Up(phaseCtx, imageRef); err != nil {
    return cleanupAfterFailure(ctx, exec, "compose up 실패", err)
}
// 3. 이미지 무결성 대조. env 없이 :latest·오타 이미지가 헬스만 통과하면 위장한다.
if err := exec.VerifyImageDigest(phaseCtx, imageRef); err != nil {
    return cleanupAfterFailure(ctx, exec, "이미지 무결성 대조 실패", err)
}
// 4. CD-1 헬스. 실패 → green 종료·blue 유지 = 미전환(롤백 아님).
if err := health.Check(ctx); err != nil {
    return cleanupAfterFailure(ctx, exec, "CD-1 헬스 실패", err)
}
return StateCompleted, nil
```

## 5. 구현 중 마주친 문제

이 실행 경로에서 그린 위장이 여러 형태로 튀어나왔고, 검토가 그 목록을 잡아 코드를 바꿨다.

- **up 후 digest를 안 대조하면** 엉뚱한 이미지가 헬스만 통과한다 → verify 단계를 헬스 앞에 고정.
- **`ps -q`가 종료된 컨테이너를 은닉**해, 부분기동인데 COMPLETED로 보였다.
- **그린 위장 방어선이 컨테이너명 미설정 시 통째로 생략**됐다 → 대상 컨테이너를 설정이 아니라 compose 프로젝트에서 파생하고, 확정 못 하면 fail-closed(판정 불가 = 실패)로.
- **baseline을 첫 표본에서 잡아** 첫 프로브 도중의 재시작을 놓쳤다 → baseline을 대기 시작 전 1회로 고정.
- **거대 duration이 int64 overflow로 음수**가 되어, 작은 lease가 검증을 통과하는 fail-open이 있었다.

> **fail-open / fail-closed** — 판정이 막히면 통과시키느냐(open) 막느냐(closed).\
> 예: 시간 계산이 넘쳐 음수가 되면 "충분하다"로 통과하는 게 fail-open, 안전한 쪽은 막는 fail-closed다.

## 6. 결론

로컬 dispatch가 실행 층으로 자리 잡았고, 그린 위장 방어선을 예외 없이 항상 켜는 것이 이 작업의 결론이다.\
orphan 완전 방어("어느 compose 서비스가 app인지" 결박)는 호스트 compose 매핑과 얽혀 별도 이슈(#21)로 분리하고, 코드에 명시 마커를 남겼다 — "무음 이연 아님".

남은 빚은 곧바로 사건이 됐다.\
이 코드가 실서버에서 처음 도는 순간, "배포는 됐는데 배포가 실패했다"는 모순 상태(false-UNKNOWN)가 터진다 — issue10.
