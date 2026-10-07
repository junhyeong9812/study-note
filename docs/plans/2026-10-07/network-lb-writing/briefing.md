# 집필 브리핑 — 커리큘럼 leaf 보강 1편 (네트워크 46 load-balancers-and-proxies, 2026-10-07)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/network/35-http-connection-management/`, `cs/network/47-cdn-and-edge/`, `cs/database/16-mvcc/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §7 네트워크 표의 `46-load-balancers-and-proxies` 행(요지: L4 vs L7, 리버스 프록시, 헬스체크, 연결 드레이닝 · 선행 35·11 · ⚠ 깊은 헬스체크 → 의존성 장애가 전 인스턴스 제외로 번짐, `X-Forwarded-For` 스푸핑, sticky 세션 불균형 · 🔧 라운드로빈·least-conn·**일관 해싱/Maglev** · 📚 `systems/server-design` 02 · Eisenbud 외 NSDI 2016(Maglev)). 요구사항 전부를 다룬다.
- **원고(읽기만, 분할 이어받기)**: `cs/systems/server-design/02-request-path.md`의 §3 로드밸런서(L4/L7·분배 알고리즘·헬스체크 3종·깊은 헬스체크 연쇄)와 §5 세션 처리(스티키 세션). §4 API 게이트웨이는 `api-design/19-api-gateway-and-bff`, graceful shutdown 절은 `reliability/14-graceful-shutdown`이 맡는다 — 링크만. 원고에서 틀리거나 근거 없는 내용(예: 분배 알고리즘 표 '함정' 칸에 "일반적으로 가장 무난한 기본값"이 들어간 것 등)은 새 leaf에 바르게 쓰고 `참고: 원고 §N의 "…"는 …(근거)` 한 줄.
- **겹치는 기존 노트(먼저 읽고 링크, 되풀이하지 않는다)**: `cs/network/{11-nat-and-conntrack,15-tcp-handshake-and-backlog,19-tcp-termination-fin-rst-half-open,21-tcp-keepalive-and-user-timeout,29-tls-handshake,32-mtls-and-cert-operations,33-http-semantics,35-http-connection-management,36-http2-multiplexing,38-websocket-sse-long-lived,47-cdn-and-edge,49-what-happens-when-url,52-network-symptom-index}`, `cs/reliability/{14-graceful-shutdown,50-sidecar-ambassador-and-service-mesh}` 및 서킷 브레이커·재시도 노트(ls로), `cs/api-design/19-api-gateway-and-bff`, `cs/algorithm/` 일관 해싱(대응표 `cs/algorithm/curriculum.md`·`cs/data-structure/curriculum.md`), `cs/security/` 신뢰 경계·헤더 스푸핑 관련(ls로). 이 노트들이 46을 "미작성"으로 가리키는 곳이 있으면 packet에 보고(고치지 않는다 — 정합 단계).
- **근거와 열 수 있는 1차 출처(검색 한도 대비)**:
  - Maglev: Eisenbud 외 NSDI 2016 https://www.usenix.org/system/files/conference/nsdi16/nsdi16-paper-eisenbud.pdf (테이블 채우기 알고리즘·테이블 크기 예·disruption 평가)
  - X-Forwarded-For / Forwarded: RFC 7239 https://www.rfc-editor.org/rfc/rfc7239.txt · MDN X-Forwarded-For https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For
  - nginx: upstream 모듈 https://nginx.org/en/docs/http/ngx_http_upstream_module.html (round-robin 기본·least_conn·hash consistent·ip_hash·max_fails/fail_timeout, 상용판 전용 지시어 구분) · realip 모듈 https://nginx.org/en/docs/http/ngx_http_realip_module.html · proxy 모듈 https://nginx.org/en/docs/http/ngx_http_proxy_module.html
  - HAProxy 문서 https://docs.haproxy.org/ (balance 알고리즘·health check·slowstart)
  - Envoy 문서 https://www.envoyproxy.io/docs/envoy/latest/ (load balancers·outlier detection·health checking·draining·Maglev/ring hash·XFF 처리 `xff_num_trusted_hops`)
  - Kubernetes probes https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/ · Pod lifecycle(종료) https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
  - AWS ELB 문서(ALB/NLB 헬스체크·deregistration delay·stickiness) https://docs.aws.amazon.com/elasticloadbalancing/ — 403이면 Internet Archive
  - Karger 외 1997 일관 해싱, Mitzenmacher "power of two choices" — 열 수 있는 사본이 없으면 서지 `[?]`.
  - Spring Boot Actuator 헬스 그룹·readiness/liveness https://docs.spring.io/spring-boot/reference/actuator/endpoints.html
- WebSearch는 한도 소진일 수 있다 — 위 주소를 먼저 쓰고, 못 열면 Internet Archive. 그래도 못 열면 `[?]`. **기억으로 쓴 절·페이지·연도·버전 번호에는 반드시 `[?]`**.

## 2. 출력 — `cs/network/46-load-balancers-and-proxies/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-07 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# network/46-load-balancers-and-proxies — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(요청 경로의 LB 위치, L4 vs L7 처리 단위, 연결 2개(클라이언트–프록시, 프록시–백엔드), 분배 알고리즘별 배정, 해시 링 vs Maglev 조회 테이블, 헬스체크 3종과 상태 전이, 드레이닝 타임라인, XFF 헤더 체인과 신뢰 경계, 스티키 쿠키), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 🔧 칸의 구조·알고리즘을 적고 기존 노트로 링크(대응표로 실제 폴더).
- **적용 — 풀어나가는 법**: 실무 순서: 증상(502·503·불균형 지표·잘못된 클라이언트 IP) → LB·프록시 원인 → 설정·로그·명령으로 확인. 코드는 Java 21 기본(`HttpServer`·`HttpClient`), 프록시는 nginx 설정. 진단(`curl -v`, nginx access log의 `$upstream_addr`·`$remote_addr`·`$http_x_forwarded_for`, `ss -tan`) 출력 읽기.
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(상태 코드·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 같은 영역 노트는 `../NN-slug/2-summary.md`(network 영역은 전부 작성됨), 다른 영역은 실제 경로 확인), 문서 URL·명세 절, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄(근거 있는 오해만).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java 21(기본)·SQL·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건.
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M, 실험 출력과 해석.
- **제품·버전 한정**: "nginx 1.27 오픈소스에서", "Envoy 문서 기준", "AWS ALB 기본값", "Kubernetes 문서 기준". 제품마다 다른 기본값(헬스체크 간격·드레이닝 시간·sticky 방식·XFF 처리)을 일반 원리로 쓰지 않는다. 상용판 전용 기능(nginx Plus의 능동 헬스체크·slow_start 등)은 그렇게 밝힌다.
- **모형 ≠ 실물**: Java 모형(Maglev 테이블·분배 시뮬레이션)은 "모형"이라고 쓰고 실제 제품 동작은 1차 문서로 따로 뒷받침한다.
- **보안 서술은 방어 관점**: XFF 스푸핑은 자기 로컬 nginx·백엔드에서 신뢰 경계 설정 유무의 차이만 보인다(외부 대상 금지, 우회 기법 금지).
- **원인 확정은 근거로**: 한 호스트 측정을 일반화하지 않는다.

## 4. 원고 이어받기

- 원고는 **수정하지 않는다.** 담당 절(§3·§5 세션)을 먼저 읽고, 이미 설명한 것은 "기초는 원고 §N" 링크 + 한두 줄 요약. 빈 곳(⚠ 장애, 실험, 적용, Maglev, XFF 신뢰 경계, 드레이닝, 질문·정답)을 채운다.

## 5. 실험 근거 (명세 I7 — 필수)

- 핵심 주장마다 실행으로 보인다. 예:
  - nginx(`nginx:1.27-alpine`) 앞에 Java 백엔드 3개: round-robin vs least_conn 배정 분포(느린 요청 섞기), `max_fails`·`fail_timeout` 수동 헬스체크로 죽은 백엔드 제외·복귀, `proxy_next_upstream` 재시도로 502 대신 성공.
  - 깊은 헬스체크 연쇄: 공유 의존성(가짜 DB 백엔드)을 느리게 하면 모든 인스턴스의 deep `/health`가 실패 → 전 인스턴스 제외 → 502/503, 얕은 헬스체크면 부분 저하(모형 또는 nginx + 헬스 판정 스크립트).
  - XFF: 클라이언트가 보낸 `X-Forwarded-For`를 그대로 믿는 백엔드 vs `realip`(`set_real_ip_from`·`real_ip_header`·`real_ip_recursive`)로 신뢰 경계를 둔 구성의 기록 IP 차이(로컬 내부 네트워크만).
  - 스티키 세션 불균형: 쿠키/ip_hash 고정에서 소수 큰 클라이언트(같은 NAT IP)로 쏠림.
  - Maglev: 논문 알고리즘대로 조회 테이블(M은 소수)을 Java로 만들어 백엔드 1개 제거 시 재배정 비율을 mod-N·해시 링과 비교, 백엔드별 칸 수 균형.
  - 드레이닝: nginx 백엔드 제거 후 진행 중 긴 요청이 끝나는지(`nginx -s reload`의 graceful 동작), 앱이 SIGTERM 즉시 종료 시 502.
- 노트에 싣는 것: 실험 코드 핵심, 환경(호스트·이미지 버전), **실제 출력**, 관찰과 해석. 비결정 값은 여러 번 돌린 범위.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-net46-w-*`, `--rm`, `--cpus=2` 이하, 가능하면 `--network none`(nginx + 백엔드 여러 개는 `docker network create --internal sn-net46-w-net`으로 묶고 끝나면 지운다 — 외부 접속 없음). 두 컨테이너가 통신해야 하면 `docker network create sn-net46-w-net --internal`로 만들고 끝나면 지운다. **이미 있는 이미지만**(`nginx:1.27-alpine`, `eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 볼륨은 가능하면 만들지 않는다(익명 볼륨은 `--rm`으로 같이 지워진다). 끝나면 `docker ps -a --filter name=sn-net46-w`·`docker network ls --filter name=sn-net46`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만). 백엔드는 JDK `com.sun.net.httpserver.HttpServer`(Java 21 단일 파일 실행)나 python `http.server`로 만든다.
- **호스트 도구**: python3(표준 라이브러리·sqlite3 모듈)만. **sudo·패키지 설치 금지**(pip·apt·npm install 포함). 실험은 수십 초~몇 분 이내·메모리 1GB 이하.
- **데이터**: 합성 데이터만(사람 이름·이메일·전화번호 같은 실제 개인정보 금지 — `user_001` 형식).
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/net46/w/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다(nginx 설정 파일은 읽기 전용 바인드 마운트 `:ro`로 넣고, 로그는 `docker logs`로 꺼낸다).
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지).
- **금지**: `sn-de-*`·`sn-arch-*`·`payment-*`·`jun-bank-*`·`text-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(문서 URL·명세 절·논문)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·네트워크를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
