# cs/issue/reliability/atomic-file-replace — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[덮어쓰기]  open(path,'w')  →  truncate(원본 즉시 0바이트)  →  write ... ✗ 크래시/ENOSPC
                                                         → "이전도 새것도 아닌" 절단 파일

[원자 교체]  같은 디렉터리에  .name.<pid>-<seq>.tmp  작성 (완성)
             → rename(tmp, path)   ← 같은 FS 안에서 한 번에 "이전 전체 | 새 전체"
             → 실패 시 tmp 삭제 (잔해 0)

 깨지는 지점                         교정
 ───────────────────────────────    ─────────────────────────────────────
 temp 고정 이름 → 동시 writer 충돌    pid + 원자 카운터 / mkdtemp (실행마다 새 경로)
 staging을 /tmp에 → EXDEV            staging은 dest.parent 안에
 디렉터리: 삭제→rename 사이 공백      dest→.old 로 치움 → tmp→dest → .old 제거
                                     (실패 시 .old 원위치 복원, 잔여 .old 는 다음 실행이 회수)
 교체 창의 옛 fd append → 유실        swap(rename~재오픈) 전체를 writer 락으로 배타
 실행 중 바이너리 cp → ETXTBSY        새 파일을 옆에 두고 rename (또는 unlink 후 생성)
 rename 원자 ≠ 내구                   부모 디렉터리 fsync · torn tail(개행 없는 끝줄)만 버림
                                     · 락은 경로가 아니라 대상 정체성에
```

## 핵심 문장

- 덮어쓰기는 **먼저 지우고 나중에 쓴다** — 중간 실패는 절단 파일을 남긴다.
- **같은 파일시스템의 rename**만이 "완성본 아니면 원본"을 준다 — temp는 목적지와 같은 디렉터리에, **writer마다 유일한 이름**으로.
- 고정 이름 temp/staging은 동시 writer 충돌과 **이전 실행 잔재의 재주입**을 만든다.
- 디렉터리는 **옆으로 치우기 → 커밋 → 제거**, 실패 시 복원.
- rename은 이름만 바꾼다 — **이미 열린 fd는 옛 inode**를 계속 쓴다. 교체 창은 락으로 배타.
- rename 원자성과 **내구성(fsync·부모 디렉터리 fsync)**은 별개의 보장이다.
