# 요구사항 명세서 — reliability-writing

> 작성일: 2026-10-01 · 작업 폴더: `docs/plans/2026-10-01/reliability-writing/` · 브랜치: 분산 커밋 뒤 `docs/distributed-writing`에서 `docs/reliability-writing`을 딴다(그전까지 노트는 작업 트리에서 미추적 상태로 쓴다).
> 선행: network·os·database(완료·push), distributed(`docs/plans/2026-10-01/distributed-writing/`, 판정·정합 진행 중). 브리핑·실험 규칙·도구를 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "진행하고 다음 내용 진행하자"
- Q/A (2026-10-01): 영역 **운영·신뢰성**(`cs/reliability/`, 커리큘럼 §11) · 검증 **분산과 같게**(실험 근거 우선 I7, 로컬 Docker 재현 허용, 기존 노트 새 leaf 보강, codex 2차 리뷰 한도 시 Opus 대체) · **명세 합의·auto를 인터뷰에서 함께 받음**(명세 파일 생성 → 즉시 승인 기록 — 진행 중인 분산 워커 쓰기 차단 방지)
- 이미 정한 것: 집필 Opus, `cs/<area>/NN-slug/` 3파일 + metadata.md(머리말 없음), 통일 골격 7절, 코드 Java·JS·TS, 종합 leaf는 마지막

## 1. 목표·대상 (필수)

- `cs/reliability/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **53편**(커리큘럼 §11 전 leaf: 01~53)
  - 신규 29편 · 기존 노트 보강 24편(커리큘럼 「기존」 칸의 `ops-patterns/*`·`systems/server-design/*`·`systems/{Hysteresis,straggler}`·`engineering/failure-point-checklist` — 원본은 그대로 두고 링크로 이어받음, 분할 지정 절만)
  - 종합 2편(52 reliability-symptom-index·53 reliability-incidents)은 나머지를 쓴 뒤에 쓴다.
- 영역 표 `cs/reliability/README.md` 재생성: 53편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 2-summary 최상위 7절 순서, Q/A 번호 일치 6~10개, 제목 아래 머리말·표식 없음, metadata.md 단계 `초안`(날짜).
- **I2 근거**: SRE 책·SRE Workbook(온라인판 장 번호 확인), Nygard 『Release It!』(원문 확인 못 하면 장 단위·`[?]`), Gregg 『Systems Performance』·brendangregg.com, Dean–Barroso 2013 "The Tail at Scale", Avižienis 외 2004, Little's Law·USL(Gunther), 제품 문서·소스(Resilience4j·Envoy·gRPC deadline·OpenTelemetry·Prometheus·Kubernetes·JDK/JFR·async-profiler 등), 사고 보고서 원문, 실험으로 확인한 것만 사실. 확인 못 하면 `[?]`. 제품 동작은 제품·버전 한정.
- **I3 커리큘럼 일치**: §11 각 행의 요지·⚠·🔧·📚 전부, 선행 링크(distributed·database·os·network leaf 포함).
- **I4 기존 보존**: 원본·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 분산 작업 규칙과 같음 — 공용 컨테이너 `sn-rl-*`(필요 시 메인이 띄움) 접두사 쓰기만, 파괴 실험·부하 실험은 워커 전용 일회용 `sn-rl-w<NN>-*` → 삭제·확인. 부하는 작게(수십 초, 코어 몇 개 이하, 호스트를 포화시키는 부하 테스트 금지). 저장소 루트 파일 금지, 절대 경로.
- **I7 실험 근거 우선**: 편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 작은 실험의 실제 출력으로 보인다(예: 재시도 지터 유무에 따른 동시 재시도 폭주, 서킷 브레이커 상태 전이, 토큰 버킷 거절률, 꼬리 지연과 hedged request, Little's Law 검증, Amdahl 한계, 메모리 누수 힙 덤프, 콜드 스타트 JIT 워밍업, graceful shutdown 중 요청 유실, 데드라인 전파 vs 미전파). 출력은 손으로 만들지 않는다. 실험이 과한 주장은 1차 출처로 대신하고 밝힌다(종합 52·53 제외).

## 3. 기준소스 (필수)

- `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §11, `cs/reliability/README.md`
- I2의 교재·논문·제품 문서·소스·사고 보고서, §1의 원본 노트

## 4. 금지영역 (필수)

- reliability 밖 영역의 노트(분산 작업 중인 `cs/distributed/**` 포함 — 읽기만), 원본 노트, 커리큘럼 본문(필요 시 NEXT에 기록)
- 생성 문서 수기 수정
- 이번 작업이 만들지 않은 컨테이너·볼륨·이미지(`sn-dw-*`·`sn-dbw-*`·`payment-codex-*` 등)

## 5. 검증 방법 (필수)

- **V1** `check_new.py` · **V1b** 사실 점검 워커가 편당 실험 1개 이상 재실행
- **V2** Opus 전수 사실 점검 · **V3** codex(high) 2차 리뷰, 한도 시 Opus 적대 리뷰 → Opus 판정
- **V4** 노트 간 정합(distributed 03·17·18·36, database 21·22 등 선행 leaf 포함)
- **V5** 웹 교차 표본 24건 이상, linkcheck 신규 깨짐 0, 영역 README 재생성, 컨테이너 정리 확인

## 6. stakes (필수)

- **중간** — 새 학습 자료 53편, 사실 오류 위험 큼. Docker·부하 실험은 전용 이름·상한으로 되돌릴 수 있다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험 대부분은 JVM·Node 단일 프로세스 시뮬레이션 + 일회용 컨테이너(nginx/envoy/redis/postgres/prometheus 등 작은 이미지)로 된다. 새 이미지가 필요하면 워커가 받고 끝나면 지운다.
- **A2**: 분산 작업의 남은 리뷰와 codex 한도를 나눠 쓴다 — 한도면 Opus 대체(명세 V3).

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(분산 브리핑 이식 + 신뢰성 실험 예시·부하 상한) | 브리핑 파일 |
| 02 | 집필(Opus 병렬, 워커당 5~6편), 종합 52·53 후속 | 53 PASS |
| 03 | Opus 사실 점검 + 실험 재실행 | 편별 packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 표본 | V3~V5 |
| 05 | README 재생성·정리·커밋·(사용자 확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 인터뷰 3건에서 영역·검증·명세 합의를 함께 받음(2026-10-01)
- [x] auto
