# cs/issue/os/process-group-and-tree-termination — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
세션(sid) ─┬─ 프로세스 그룹(pgid)
           │     셸 ──▶ 작업 ──▶ 손자
           └─ 제어 터미널(tty / pty master를 누가 쥐나)

실패 지점
  ① 부모만 kill            셸 죽음 → 손자 reparent(init) → 고아로 계속 실행
  ② 논리적 취소             flag = None → fork된 프로세스는 모름
  ③ 권한 다른 자손          root 자손에 killpg → EPERM
  ④ pkill/pgrep -f          패턴이 내 명령줄에도 있음 → 자기 셸 kill / 대기 루프 무한
  ⑤ 세션·터미널 종료         SSH 끊김·도구 타임아웃 → 그룹에 SIGHUP → 배치 사망
                            nohup = SIGHUP 무시뿐, 세션·stdin은 여전히 묶임
  ⑥ pty master 닫힘          setsid 자식도, 데몬(=master 보유자)이 죽으면 hangup → SIGHUP
  ⑦ SIGKILL / 그룹 kill     SIGKILL = 정리 코드 미실행, 별세션 자식 = 그룹 밖
  ⑧ 원격 명령               로컬 ssh 종료 ≠ 원격 종료 (TTY 없으면 원격은 SIGHUP 안 받음)
  ⑨ 대기 루프               종료 조건이 실제 완료 신호와 무관 → 영원히 돎

교정
  스폰: setsid(새 그룹·세션) → 종료: killpg(TERM → 유예 → KILL) → wait
  pid 트리 순회(pgrep -P) 또는 [p]attern 트릭, 조상 체인 확인(자기 자신 제외)
  장시간 작업: setsid … < /dev/null (세션·stdin 분리), 상주는 서비스 매니저
  정리 경로가 있는 부모: SIGTERM + wait (graceful), 내가 띄운 것만 정리(소유 플래그)
  원격: 이름 붙여 직접 kill → 종료 확인, 아니면 예외
  대기: 폴링 루프 대신 런타임 완료 알림
```

## 핵심 문장

- 종료는 **프로세스 하나가 아니라 그룹·트리 단위**로 한다 — 스폰할 때 그룹을 만들어 둬야 죽일 때 그룹으로 죽일 수 있다.
- 논리적 취소(플래그) ≠ OS 프로세스 종료. **권한이 다른 자손**에는 신호조차 못 보낸다.
- `pgrep/pkill -f`는 **전체 명령줄**을 매칭한다 → 검색하는 자신도 매칭된다.
- `nohup`은 SIGHUP만 무시한다. **setsid + stdin 분리**가 세션에서 떼어낸다. 그래도 자식의 제어 터미널을 쥔 프로세스가 죽으면 hangup이 온다.
- SIGKILL은 정리 코드를 건너뛴다. 정리 경로가 있으면 **SIGTERM으로 깨우고 wait**한다.
- "종료 신호를 보냈다" ≠ "끝났다" → **실제 종료를 확인**한다.
