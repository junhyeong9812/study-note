# Opus 표본 사실 검증 요약 (2026-09-28, 12편 — 메인 기록)

- 문제 없음: api-design/02-coupon-issue, domain-modeling/advanced/15-period-close(가정 수치 표시만)
- finding 30건(높음 0). 유형: 원본 코드 불일치 6(basic 10-payment 3·22-settlement 1, advanced 09·27) · 일반 CS 부정확 8(DS 05·16 5건, ops 04·06, advanced 27) · 논리 뒤집힘·기존 본문과 모순 5(algorithm 06·25, advanced 09 2, ops 04) · 편집 결함 5.
- **구조 결함(ops-patterns 전수)**: 재배치로 「문제」·「측정」 절이 참조 문장보다 **위**로 갔는데 새 도입문은 "아래 「문제」절" — 19편 전부 "위"로 교정 필요. 「실패」「한계」 참조는 실제 아래라 맞음 — 편마다 위치 확인.
- 대표 finding:
  - DS 05 "반복해서 묻는 질문의 답이 키" → 묻는 대상이 키, 답이 값 / Python dict 군집화 [?] 오류(perturb 탐사) / JDK 트리화: 사슬 8 초과 + 테이블 64 이상(05·16 통일)
  - DS 16 "메모리 안 균형의 유일한 답" → 삭제(AVL도 보장), 메모리 B-트리(Rust BTreeMap·Abseil) / VMA rbtree는 6.1 이전(maple tree), CFS→EEVDF(6.6) / ConcurrentSkipListMap은 락 없음(CAS)
  - algorithm 06 C5: 반열린 판 hi=mid-1은 오답, 닫힌 판 hi=mid·lo=mid가 제자리걸음 — 기존 3-answer 125-134와 일치시킬 것
  - algorithm 25 C3 논리 역전(둘 다 아니면 KMP) / 잘린 문장 / 최소 "주기" vs 반복 단위
  - ops 04: Resilience4j RateLimiter는 주기 재충전(고정 창 계열) / "서버에 닿지도 않음" → 비즈니스 로직에 닿지 않음
  - ops 06: ConcurrentHashMap.compute는 버킷 synchronized(CAS 아님)
  - basic 10: Money는 결과가 음수인 뺄셈(작은−큰)을 거부 / DUPLICATE 판정은 seenKeys(LinkedHashSet) / Money는 scale 0 정규화로 0≡0.00
  - basic 22: impl은 안정 정렬에 기대지 않으려고 thenComparingInt(i->i) 명시(주석) / 399원은 총액이 매일 다른 측정(10,000÷3 매일이면 365원)
  - advanced 09: 365건은 실패 총수(배치는 첫 실패에서 중단) / anchorsDisagree는 쌍별 equals(집합 크기는 06-tax) — 정답 4번 / C1 질문 전제(덮어쓰기) 부정확
  - advanced 27: String.hashCode는 명세 고정(JDK 1.2~) — 원본 유래 오류 → 정정 줄 / moved는 한 인스턴스 before/after 비교 / RESHUFFLE B→A 8,046·A→B 17,997
- 외부 사실(Resilience4j·maple tree·CHM 락)은 학습 지식 판단 — 수정 워커가 1회 교차 확인.
