# os — 프로세스·경로·터미널

프로세스 생성·종료, 경로, PTY 같은 OS 수준 의미에서 나오는 패턴이다.\
공통 원리: **자식 프로세스는 실행 방식에 따라 다른 문맥을 물려받고, 생성한 것은 회수·정리 책임까지 함께 진다.**

## 공통 원리

```
  부모 ──spawn──▶ 자식 ──▶ 손자
   │  env·PATH·cwd·TERM: 실행 방식(셸·런처·서비스)마다 다름
   │
   ├─ wait 없음         → 좀비
   ├─ 파이프 한쪽만 드레인 → 교착
   ├─ 부모만 kill        → 손자 고아
   └─ 경로 표기 여러 개   → 같은 파일을 다른 키로

  장기 작업의 수명·자원 단위 = 태어난 cgroup·유닛 (setsid·nohup으로 안 바뀜)
   ├─ 앱 cgroup 안에서 띄움   → oomd가 앱과 함께 cgroup째 종료
   └─ 사용자 유닛(linger 없음) → 마지막 로그인 세션과 함께 정지
```

## 패턴 카드

- [execution-context-inheritance](execution-context-inheritance/) — 자식 프로세스·서비스·훅은 실행 방식(셸·GUI 런처·systemd·영속 cd·플랫폼 주입)에 따라 env·PATH·cwd·TERM을 다르게 물려받는다 — 필요한 실행 문맥을 명시적으로 결정·정화한다.
- [job-lifetime-bound-to-user-session](job-lifetime-bound-to-user-session/) — 장기 작업의 수명·자원 단위는 띄운 곳의 cgroup·사용자 서비스 매니저에 묶인다 — oomd는 cgroup째 죽이고(setsid로 못 피함), 사용자 유닛은 linger 없이 로그아웃과 함께 정지한다, 별도 유닛·linger·Restart+멱등 재개로 떼어 낸다.
- [nested-sandbox-capability](nested-sandbox-capability/) — 샌드박스 안에서 자체 격리를 켜는 도구를 띄우면 상속된 실행 문맥이 내부 격리 초기화를 거부할 수 있다 — 결과는 exit 0 결과물·지연으로 숨는다, 읽기 의존은 입력 인라인 우회·완료는 산출물·본문과 함께 판정
- [os-api-limits-and-semantics](os-api-limits-and-semantics/) — OS API에는 고정 한계와 미정의 동작(UDS 경로 108바이트·소유하지 않은 디렉토리 chmod·순회 중 수정)이 있다 — 설계 전에 전제를 확인한다.
- [path-canonical-identity](path-canonical-identity/) — 같은 파일을 가리키는 경로 표기는 여러 개다(`./`·구분자·대소문자·빈 문자열=cwd) — 비교·키·잠금 전에 모든 진입점이 같은 정규형을 거쳐야 한다.
- [process-group-and-tree-termination](process-group-and-tree-termination/) — 부모만 죽이면 손자·다른 세션 자식은 고아로 남고, `pgrep/pkill -f`는 자기 명령줄도 매칭하며, SIGHUP·SIGKILL은 정리 경로를 건너뛴다 — 프로세스 그룹·신원 단위로 종료한다.
- [pty-semantics](pty-semantics/) — PTY에 쓴 바이트는 수신 TUI의 현재 모드(raw·canonical·bracketed paste)로 해석된다 — CR≠LF, write 성공≠전달, EIO=EOF를 명시적으로 다룬다.
- [subprocess-lifecycle-and-pipes](subprocess-lifecycle-and-pipes/) — spawn한 자식은 wait로 회수하고, 파이프는 양쪽 모두 드레인하며, stdio 프로토콜은 순수해야 하고 stdin은 닫아야 한다 — 아니면 좀비·교착·영구 대기가 된다.

> 이 폴더의 메타 태그: `silent-failure`(3) · `resource-bounding`(2) · `environment-drift`(3) — 태그별 전체 목록은 [issue 태그 역인덱스](../../README.md#태그-역인덱스).
