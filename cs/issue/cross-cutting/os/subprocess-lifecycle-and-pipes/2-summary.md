# cs/issue/os/subprocess-lifecycle-and-pipes — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
부모 ──spawn──▶ 자식
  │  stdin  ──▶  (닫아야 EOF)
  │  stdout ◀──  (드레인)        파이프 버퍼 유한(리눅스 기본 64KiB, OS마다 다름), 차면 자식 write 블록
  │  stderr ◀──  (드레인)
  └─ wait ───▶  회수 (안 하면 좀비)

실패 지점
  ① kill만 / 에러 시 조기 return  → wait 없음 → 좀비 + 자식 stderr(진짜 원인) 유실
  ② 한 스트림만 드레인            → 다른 스트림 가득 참 → 자식 블록 ↔ 부모 EOF 대기 = 교착
  ③ kill 후 드레인 join           → 손자가 write-end 상속 → EOF 안 옴 → join 무한 대기
  ④ stdio 프로토콜 오염           → 대화형 프롬프트가 stdin을 점유 → 영구 대기
  ⑤ stdin 열린 채 실행            → CLI가 EOF까지 추가 입력 대기 → 영구 정지
  ⑥ 소비자 끊김 미감지            → readline 계속 대기 → 정리 경로 안 돎 → 자식 누적
  ⑦ 보조 스레드 수명 = close 경로만 → 자식 자연 종료 시 영구 폴링
  ⑧ 파이프 = 블록 버퍼링           → 진행 로그가 끝에 몰려 나옴

교정
  spawn → stdin 쓰기·스트림별 드레인 동시(별 스레드) + 상한 → try_wait 폴링 + timeout → kill → wait
  드레인 결과는 채널 recv_timeout (join X), 성공 = exit 0 AND 산출물 비어있지 않음
  stdin = null(또는 명시 리다이렉트), 대화형 확인 끄기(--yes), stderr 분리
  보조 작업자 종료 = 대상 자원의 실제 수명(채널 끊김)에 결박
  자식 버퍼링 끄기(PYTHONUNBUFFERED=1)
```

## 핵심 문장

- spawn한 자식은 **어떤 경로로 끝나든 wait**로 회수한다 — 쓰기 실패·타임아웃·kill 모두.
- 파이프는 **유한 버퍼**다. 읽지 않는 스트림이 하나라도 있으면 교착이 가능하다 → **모든 스트림 드레인**.
- 파이프 EOF는 **모든 write-end가 닫혀야** 온다. 손자가 상속하면 자식을 죽여도 EOF가 안 온다 → join 대신 타임아웃 있는 수신.
- stdio를 프로토콜로 쓰면 stdout은 **순수**해야 한다 — 대화형 프롬프트·로그 금지.
- 입력이 필요 없는 자식의 **stdin은 닫는다**(`/dev/null`).
- 보조 작업자의 수명은 명시적 close가 아니라 **대상 자원의 실제 수명**에 묶는다.
