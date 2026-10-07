# log — network-lb-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-07 | 사용자 지시 "남은 커리큘럼도 전부 진행 계획에 넣어서 쭉 진행" → 순서 네트워크 원고 1 → 언어 27 → 데이터 분석 28, push는 끝에 한 번 · 이 작업: network/46 load-balancers-and-proxies 보강(원고 systems/server-design/02 §3·§5) · 브랜치 docs/network-lb-writing(ea99abb5에서) · 명세·브리핑 3종(data-engineering판 이식) | SPEC=1·MODE=auto |
| 2026-10-07 | 집필 발사(Opus 1 — 46편, 원고 §3·§5 분할 이어받기, nginx 1.27 + JDK 백엔드 실험) | 회수 대기 |
| 2026-10-07 | 집필 회수 46(PASS, Q/A 9, [?] 3 — Maglev NSDI 2016 §3.4·§5.3, RFC 7239, nginx·HAProxy 3.0·Envoy·ALB·K8s·Spring 문서, nginx 1.27.5 소스) — 실험(nginx 1.27.5 + JDK 21, --internal 네트워크): 느린 백엔드 RR 33% vs least_conn 5~6%, Maglev 모형 논문 Table 1 재현·N=100 이동 1.58~1.60% vs 링 0.89~1.12% vs mod-N 99%, 깊은 헬스체크 모형 503 89/280 vs 얕음 0, max_fails/next_upstream 재시도로 502 회피, reload 드레이닝 vs 즉시 종료 502(POST), XFF 덧붙이기만 하면 위조 IP 기록 vs realip recursive, ip_hash /24 쏠림 300/0/0 · 원고 정정 1(least_conn '기본값') · 영역 밖 원고 경로·미작성 표기 후보 9곳 보고 → 사실 점검 발사 | PASS |
| 2026-10-07 | 사실 점검 회수 46 (PASS, 중대 0 / 중간 6: HAProxy·Envoy 기본 roundrobin/ROUND_ROBIN 확인, Envoy Maglev table_size 가변, 실험 2 출력 손질 → 실제 줄로, ip_hash 실험 '주소 300개' → 250개에서 300건(Q7 포함) / 경미 9, [?] 5→2, 실험 5개 재실행 — 결정적 출력 일치) → codex 2차 발사 | PASS |
| 2026-10-07 | codex(high) 2차 회수 46(지적 7) → 판정 + 정합(영역 밖 원고 경로·미작성 링크 교정) + 웹 교차 표본 단일 워커 발사 | 회수 대기 |
| 2026-10-07 | 판정·정합·웹 회수: codex 7(채택 4·부분 3·기각 0, 표 일치 — NLB 해시 입력·UDP, TLS 종료는 L7만이 아님, NLB 클라이언트 IP 보존, 스티키 예외, Maglev 연결 추적 조건, 해시 링 1/N vs Maglev 모형 수치 구분, '이 노트의 선택' 표기) · 노트 간 모순 0(원고·network/35·47·52·reliability/14·50·api-design/19) · **링크 교정 14곳/12파일**(git word-diff: 링크 추가·'미작성/원고 경로' 교체, 예외 2곳 — 47 원고 CDN 절 링크·14 원고 graceful 링크는 의도적이라 유지, 50의 '기존 노트'→'원고' 표기·'헬스체크·연결 드레이닝' 설명 덧붙임은 문장 의미 유지) · 링크 390 깨짐 0 · 웹 18건 전부 일치 · 13 PASS · README 재생성(network 원고 있음 1→0) · 정리 sn-net46 0 | PASS |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 46 | Opus 독립 | 0 | 6 | 9 | 5→2 | 웹 표본 3 · 실험 재실행 5 |
| 46 판정 | Opus(codex 지적 7) | 채택 4 | 부분 3 | 기각 0 | | 재실험 0 |

## 생략한 검증

- 없음(빚 0). 참고 한계: nginx 능동 헬스체크·slow_start는 상용판 전용이라 문서로만 · AWS ALB/NLB·Envoy·HAProxy는 실물 없이 공식 문서 · Maglev는 논문 알고리즘의 Java 모형(Table 1 재현) · P2C 원 논문(Mitzenmacher) 미열람 `[?]` · 실험 3(깊은 헬스체크 모형)·5(드레이닝)는 사실 점검 재실행 생략(출력 합계 대조만).

## 완료 요약

- 산출: `cs/network/46-load-balancers-and-proxies` 1편(원고 `systems/server-design/02-request-path.md` §3·§5 분할 이어받기, 원고 오류 1건 "참고:" 줄) + 영역 표 재생성(network 53편 전부 초안) + 영역 밖·영역 안 원고 경로/미작성 링크 교정 14곳(12파일).
- 검증: V1 PASS · V1b/V2 Opus 사실 점검(중대 0·중간 6, 실험 5 재실행 — 결정적 출력 일치, 손질된 출력 블록 1개를 실제 출력으로) · V3 codex(high) 지적 7 → 채택 4·부분 3·기각 0 · V4 정합(모순 0) · V5 웹 18건 일치 + 사실 점검 표본 3 · 링크 390 깨짐 0.
- 관측: 지적의 대부분은 **제품별 차이 일반화**(NLB vs ALB, L4도 TLS 종료 가능, 스티키가 알고리즘을 건너뜀). 메인 실수 2: heredoc 백틱 확장(무해), 마감 스크립트의 assert 실패 뒤에도 커밋이 진행돼 docs 커밋을 amend(미push).
- 핵심 diff(실파일에서 복사): `cs/network/README.md` before `> 현황: 미작성 0 · 원고 있음 1 · 초안(Claude) 52 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 53 · 검수 완료 0`
- CS 이슈 아카이브: 0건(문서 작업).
