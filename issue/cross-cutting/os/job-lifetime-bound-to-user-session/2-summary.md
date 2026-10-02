# issue/os/job-lifetime-bound-to-user-session — 정리 (힌트)

## 전체 흐름

```
system (PID 1)
 └─ user.slice
     └─ user-<uid>.slice
         ├─ session-N.scope ─────────── 로그인 세션 (데스크톱·SSH)
         └─ user@<uid>.service ──────── 사용자 서비스 매니저 (linger 없으면 수명 = 로그인 세션들)
              ├─ <앱>.scope ─────────── 터미널·앱이 사는 cgroup (위치는 실행 방식에 따라 다름)
              │    └─ ① 여기서 setsid nohup job &  → job의 cgroup은 그대로 이 scope
              └─ job.service ───────── ② 별도 유닛: 자기 cgroup

실패 지점
  ① 메모리 압박 → systemd-oomd가 후보 cgroup 하나를 골라 그 안 전부에 SIGKILL
       측정이 앱의 scope 안에 있으면 앱과 함께 사망 (setsid는 세션·그룹만 바꾸고 cgroup은 안 바꿈)
       → 발견 지연: 약 2시간 46분 무진행, 원격 서버의 측정 컨테이너 3시간 방치
  ② 마지막 로그인 세션 종료 → (linger 꺼짐) 사용자 매니저 종료 → 그 아래 사용자 유닛 전부 정지
       → 진행 중 회차 중단, 실패 기록(ABORT) 없음
  ③ 일시 네트워크 단절 → 실행기 비정상 종료 → 사람이 볼 때까지 유휴 (수 시간)

교정
  ①  측정 = 별도 유닛(자기 cgroup) + ManagedOOMPreference=avoid
       (단 사용자 유닛의 avoid는 cgroup 소유자 조건에 따라 oomd가 무시할 수 있음 — systemd 문서)
  ②  loginctl enable-linger <user>  또는  시스템 유닛(User=<user>)
  ③  Restart=on-failure + RestartSec + StartLimit(횟수/기간)  +  멱등 재개
       재개 = 끝난 조건 건너뜀 · 계획과 다른 조건이면 거부 · 끊긴 회차는 .incomplete-<시각>으로 보존 후 재측정
```

## 핵심 문장

- 프로세스의 **수명과 자원 회계 단위는 cgroup**이다 — setsid·nohup은 세션·신호만 바꾸고, 어느 cgroup(어느 유닛) 안에서 태어났는지는 바꾸지 못한다.
- systemd-oomd는 프로세스가 아니라 **cgroup을 통째로** 죽인다 — 장기 작업을 무관한 앱과 같은 cgroup에 두면 둘의 사용량이 한 후보로 합산되고, 선택되면 같이 죽는다.
- 사용자 유닛은 **사용자 서비스 매니저**의 자식이다 — linger가 꺼져 있으면 마지막 로그인 세션과 함께 매니저가 끝나고 유닛도 정지한다.
- 자동 재시작은 **멱등 재개**가 있어야 복구다 — 재개가 처음부터 다시 하거나 이미 쓴 결과를 덮어쓰면 재시작이 손상을 만든다.
- 외부 요인(메모리 압박·로그아웃)으로 죽은 작업은 스스로 실패를 기록하지 못한다 — 생존 확인은 프로세스 검색이 아니라 진행 기록의 **마지막 갱신 시각**으로 한다.
