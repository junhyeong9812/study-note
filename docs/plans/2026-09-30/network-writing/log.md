# log — network-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-09-30 | 인터뷰: 네트워크 51 먼저 · 집필+Opus 전수 점검+웹 표본 · 모델은 A/B 시범 후 결정 · cs/network/NN-slug 3파일 통일 골격 | spec·briefing·check_new.py, SPEC=1·auto, 브랜치 docs/network-writing(main d313fe16) |
| 2026-09-30 | A/B 시범: worktree 2개(scratchpad/ab-fable·ab-opus, detached d313fe16)에서 19·29를 Fable·Opus가 각각 집필 | 둘 다 check 2 PASS. Opus [?] 10 · Fable [?] 0(단, 워커가 "1차 확인 못 했는데 [?] 없이 쓴 항목" 다수 자진 보고 — 경보 번호·에러 문자열·SIGPIPE 무시 등) |
| 2026-09-30 | check_new.py 코드 펜스 안 `# 주석` 헤딩 오탐 수정(Fable 워커 보고) | 재실행 PASS 유지 |
| 2026-09-30 | 블라인드 사본 scratchpad/blind — **A = Opus, B = Fable**(평가자에게 비공개) · 지표: 요약 줄 A 383/426·B 349/358, 그림 A 12/13·B 11/11, 즉석 용어 A 7/8·B 8/14, [?] A 7/3·B 0/0, 평균 문장 길이 A 52/50·B 57/74 | 평가 발사: 독립 Opus(웹 대조) ∥ codex(high) |
| 2026-09-30 | 블라인드 평가 회수 — Opus: A 권고(근소·방향 분명, 중간 오류 A0/B3, 가독성 A 4~4.5/B 3) · codex: A 권고(결정적), A·B 공통 수정: FIN≠응답 완결(C 코드), PSK 단독 모드는 전방 비밀성 없음 | 사용자 결정 "진행해보자" → **집필 Opus, 점검 독립 Opus 전수 + codex 표본**, A판 19·29를 두 평가 반영·B 깊이 요소(확인된 것) 이식해 완성 |
| 2026-09-30 | 브리핑 §3-1 추가(시범 교훈: [?] 기준·규범 수준·"항상" 금지·계층 구분·구현 의존 에러 순서·옵션 대조) · 메모리 갱신(새 노트 집필=Opus) · A판 19·29를 cs/network로 복사 | — |
| 2026-09-30 | 완성 워커(19·29, 두 평가 반영·B 깊이 이식) + Opus 집필 워커 9개(01~05·06~10·11~15·16~18,20,21·22,23,25~27·28,51,30~32·33~37·38~42·43~45,47,48 = 45편) 발사. 종합 4편(49·50·52·53)은 후속 | 회수 대기 |
| 2026-09-30 | 회수 1/9: 01~05(Opus) — check 5 PASS 재확인, [?] 8(04 요약 4·05 요약 3·03 정답 1), ⚠ 칸 5/5 커버 | 커리큘럼 02행 "12로 이어짐" 오기(실제 10 fragmentation-mtu-pmtud) → NEXT 기록 대상(커리큘럼 본문은 금지영역) |
| 2026-09-30 | 회수 2/9: 22·23·25·26·27(Opus) — check 5 PASS 재확인, [?] 약 13, ⚠ 칸 5/5 커버(25: rx_missed_errors가 /proc/net/dev drop에 합산됨을 명시) | 후속 과제: 병렬 집필 중 "미작성"으로 적힌 형제 노트 참조 → 전원 회수 후 직접 링크로 일괄 전환 패스 필요 |
| 2026-09-30 | 회수 3/9: 43·44·45·47·48(Opus) — check 5 PASS 재확인, [?] 5, ⚠ 칸 5/5 커버. ISO 23009-1(유료)·CRIME 원 슬라이드는 MDN·DASH-IF·IETF85로 대체 명시 | 커리큘럼 44행 "47의 사이드채널" 오기(실제 43) → NEXT 기록 대상 |
| 2026-09-30 | 회수 4/9: 28·51·30·31·32(Opus) — check 5 PASS 재확인, [?] 13, ⚠ 칸 5/5 커버. 29/30/31/32 분담(핸드셰이크/체인/폐기·CT/mTLS·ACME) | 웹 표본 필수 대상: RFC 9989(DMARCbis 2026-05), LE 45일 수명 일정, SC-081 200/100/47일, LE clientAuth EKU 종료일 — 최신 사실이라 교차 확인 |
| 2026-09-30 | 회수 5/9: 38~42(Opus) — check 5 PASS 재확인, [?] 4, ⚠ 칸 5/5 커버. curl (18) 메시지는 로컬 재현(curl 8.5.0)으로 확인 | 29 파일 변경 알림은 완성 워커(19·29) 작업 — 정상. 웹 표본 후보: nginx 1.29.7 proxy_http_version 기본값 변경, IETF resumable-upload draft-12 |
| 2026-09-30 | 회수 6/9: 16·17·18·20·21(Opus) — check 5 PASS 재확인, [?] 약 21, ⚠ 칸 5/5 커버(21의 커리큘럼 "≈15분 [?]"은 ip-sysctl tcp_retries2 924.6s 하한으로 확인) | tcp(7) vs 커널 문서 기본값 충돌(tcp_tw_reuse disabled vs 2, tcp_rmem 87380 vs 131072) → 커널 문서 채택 명시. 19→20·21 "미작성" 링크는 일괄 링크 패스에서 전환 |
| 2026-09-30 | 회수 7/9: 06~10(Opus) — check 5 PASS 재확인, [?] 18(06 벤더 기능 8건 다수), ⚠ 칸 5/5 커버 | 커리큘럼 08행 선행 "data-structure/13-radix-trie" 오기(실제 20-radix-trie) → NEXT 기록 대상 |
| 2026-09-30 | 회수 8/9: 33~37(Opus) — check 5 PASS 재확인, [?] 2(확인 못 한 주장 일부는 삭제), ⚠ 칸 5/5 커버 | 남은 집필: 11~15 |
| 2026-09-30 | 회수 9/9: 11~15(Opus) — check 5 PASS, [?] 10, ⚠ 칸 5/5 커버. 전체 check: 47 PASS / 0 FAIL. "미작성" 표기 141건(형제 노트 다수는 이제 존재) | 링크 전환 패스는 종합 4편 후 일괄 |
| 2026-09-30 | 종합 집필 워커 2개 발사(Opus): 49·50 ∥ 52·53 | 회수 대기 |
| 2026-09-30 | factcheck-briefing.md 작성 → 독립 Opus 사실 점검 워커 8개 발사(01~06·07~12·13~18·19~25·26~30·31~36·37~42·43~51 = 47편, 최신 날짜 주장 교차 지시). 49~53은 집필 후 별도 점검 | 회수 대기 |
| 2026-09-30 | 사실 점검 회수 1/8: 01~06 — 수정 중간 6(RFC 1122 절 번호 §1.3.1→§1.1.3, RFC 7348 권고 왜곡, duplex 불일치 증상 쪽 반대, unres_qlen 구 기본값, STP designated port 정의 오류, …)·경미 6, [?] 16→10(6 확인 제거), check 6 PASS | 01 ENETUNREACH/EHOSTUNREACH 서술과 ip(7) 인용 어긋남 보고(미수정) → 종합 판단 대상 |
| 2026-09-30 | 사실 점검 회수 2/8: 43~51 — 중간 5(SameSite 조건 누락, nginx text/html 항상 압축, Java EHOSTUNREACH→NoRouteToHostException 누락, RFC 5321 재시도 '최소 4~5일', …)·경미 약 10, [?] 6→4, RFC 9989 원문 확인(7489·9091 대체), check 6 PASS | 교차 확인 과제: 다른 노트의 Java 예외 매핑(OpenJDK Net.c: ECONNREFUSED/ETIMEDOUT→ConnectException, EHOSTUNREACH→NoRouteToHostException)과 일관성 |
| 2026-09-30 | 사실 점검 회수 3/8: 37~42 — 중대 0, 중간 1(WebSocket curl에 --http1.1 누락), 경미 12(규범 조건·절 번호·ss -H), [?] 5→3, 최신 주장(nginx 1.29.7·resumable draft-12·RFC 9842·9659) 원문 확인, check 6 PASS | — |
| 2026-09-30 | 사실 점검 회수 4/8: 31~36 — 중대 0, 중간 5(CRLite 현행 설계, nginx non_idempotent 조건, 기본 Lax 2분 예외, Vary SHOULD 격상 오류, RFC 9218 스케줄링), 경미 약 12, [?] 10→3. 최신 날짜 주장(LE OCSP·45일·clientAuth, SC-081, nginx 1.29.7) 전부 공식 원문 일치, check 6 PASS | — |
| 2026-09-30 | 종합 회수 1/2: 49·50(Opus) — check 2 PASS, [?] 0, ⚠ 커버(49 구간별 실패 지도 표+5 시나리오, 50 추측 진단 오판 5 + BPF 절). 로컬 도구 출력 (예시) 표기 | 49·50은 집필 후 독립 사실 점검 필요(52·53과 함께) |
| 2026-09-30 | 사실 점검 회수 5/8: 19~25 — 중대 1(25: ip -s link가 missed를 dropped에 합산한다는 서술 — 실제는 /proc/net/dev만 합산, ip -s link는 별도 칸; 메인이 로컬 `ip -s link`로 재확인), 중간 4(20 TIME-WAIT 메모리 수치 날조→Bernat 수치, CLOSE-WAIT 타이머 예외, 21 타이머 구조, 23 rtx/ofo 큐는 rbtree), 경미 8, [?] 14→3, 19 무수정, check 6 PASS | — |
| 2026-09-30 | 사실 점검 회수 6/8: 07~12 — 중대 0, 중간 8(08 blackhole에서 ip route get은 EINVAL로 실패 — man+커널 소스 추론·실행 미검증, Java ENETUNREACH→SocketException·EACCES→BindException, 09 TCP traceroute SYN-ACK, 10 AWS 1500/8500 조건·Cloudflare 수치, 12 DHCP 메시지 8종·주소 선택 순서), 경미 약 17, [?] 12→9, check 6 PASS | — |
| 2026-09-30 | 종합 회수 2/2: 52·53(Opus) — check 2 PASS, [?] 5, 커리큘럼 행 증상 전부 + 추가 5종, 로컬 재현(ECONNRESET→EPIPE 순서·EADDRNOTAVAIL·EMFILE·Node ESERVFAIL). 51편 집필 완료 | 노트 간 불일치 보고: ①SERVFAIL→EAI_AGAIN 27은 [?]·28·48은 단정 ②accept 큐 넘침 23은 listen(2) 양갈래만, 리눅스는 무시(SYN 드롭) 명시 필요 ③15 Java ETIMEDOUT [?] 제거 가능 ④35 Node globalAgent keepAlive(Node 19+ 추정, 미확인) → 점검 전원 회수 후 일관성 패스 |
| 2026-09-30 | 49·50·52·53 독립 사실 점검 워커 발사(Opus, 리프 대조 포함) | 회수 대기 |
| 2026-09-30 | 사실 점검 회수 7/8: 26~30 — 중대 0, 중간 11(26 mtr -T root 오기·ARP 실패→EHOSTUNREACH 커널 경로 확인, 27 TCP 재시도 근거 RFC 7766·RA 서술, 28 RFC 8767/2308 규범 수준·Q2 자기모순, 30 critical 확장 MUST 절 §4.2·JSSE·Node rejectUnauthorized), 경미 약 10, [?] 13→4, 29 무수정, check 5 PASS | 노트 간 불일치 ①(EAI_AGAIN) 해소: 27에서 glibc 소스로 확인 → 28·48 단정과 일치 |
| 2026-09-30 | 사실 점검 회수 8/8: 13~18 — 중대 0, 중간 9(15 Node net timeout은 idle·REJECT 기본 ICMP port-unreach→ECONNREFUSED, 16 ECMP 재정렬 개념 오류·rb-tree 이유 귀속, 17 tcp_adv_win_scale 6.6 폐지·Q10 keepalive 조건 혼동, 18 SSR은 RFC 2861·CUBIC RTT 공정성 과장), 경미 약 15, [?] 26→11, 13 무수정, check 6 PASS. **47편 점검 완료** | — |
| 2026-09-30 | 노트 간 불일치 정리(메인): ②23 accept 큐 넘침에 리눅스 기본(tcp_abort_on_overflow=0 → 무시) 한 줄 + 15 링크 · ④35는 이미 globalAgent v19 keep-alive 명시 — 수정 불요 · ③15 [?]는 메시지 문구 한정이라 유지 | 23 check 재실행 대상 |
| 2026-09-30 | codex 표본(high, stdin 인라인) 5편 발사: 12·18·25·31·52 · 웹 교차 표본 24건(web-sample.md) 독립 Opus 워커 발사 | 회수 대기 |
| 2026-09-30 | 웹 교차 표본 회수: 24/24 일치(불일치 0·확인 불가 0), 노트 본문 대조 전부 같은 뜻 — 출처 직접 curl | 판정 칸 `||` 표 깨짐 메인 수정. 참고: LE tlsclient 2026-03-16 갱신(기존 사용자 연장) — 노트와 모순 없음, 08 blackhole `ip route get` EINVAL은 실행 미검증(userns 불가) |
| 2026-09-30 | 49~53 사실 점검 회수: 중간 약 9(49 DNS 에러 뭉개짐 서술→Java/Node 구분, 52 Java 매핑 EPIPE·EMFILE accept·Node 공통 에러 목록, 53 OpenSSL 블로그 **날조 인용** 교체·1.0.2zb 서술·Meta out-of-band도 다운·/25 전파 RIPE 수치), 경미 약 6, check 4 PASS | 리프 27:293 "UnknownHostException·ENOTFOUND 하나로" 조건 필요(같은 노트 235행·glibc와 모순) → 판정 패스에 포함 |
| 2026-09-30 | **codex 표본 결과(12·18·25·31·52 사전판)**: Opus 전수 점검 뒤에도 편당 9~11건 — 무조건 단정·노트 내부 모순(18 CUBIC 그림 K 이후 하강, 18 장애1 IW 리셋 vs 본문 단계 반감, 31 정답 4 vs 6), 절·규범 수준 | **승격 판단**: 표본 전부에서 잔존 결함 → 중간 stakes 듀얼 리뷰 규칙대로 codex 전수(나머지 47편) + Opus 판정 워커가 1차 출처 대조 후 채택/기각. 전체 check 51 PASS |
| 2026-09-30 | codex 전수 47편 실행 → **전건 실패**: 사용 한도 초과("try again at 11:18 PM"), 스크립트 내 2회 재시도 포함 | core §4 규칙(中↑ codex 실패 → 대체 리뷰어): **Opus 적대 리뷰어**가 codex와 같은 프롬프트로 지적만 작성(out-NN.md) → Opus 판정 워커가 출처 대조 후 반영. 모델 다양성 손실은 codex 표본 5편(12·18·25·31·52)이 보완 |
| 2026-09-30 | codex 지적 판정 회수(12·18·25·31, Opus): 40건 중 채택 29·부분 9·기각 0 — 18 CUBIC 그림 재작도·IW 리셋 모순 해소, 31 정답 4↔6 모순 해소·LE Must-Staple 일정 정정, 25 큐 드롭 앱 가시성·TX 링·skb 복사 조건, 12 DISCOVER 유니캐스트·RFC 3118 인증, check 4 PASS | 기각 0 → codex 지적 정밀도 높음(판정자 원문 대조) |
| 2026-09-30 | 적대 리뷰 회수 01~06: 8건(01 ECONNREFUSED는 ICMP port-unreach로도·ENETUNREACH 원격 가능, 02 라우터/스위치 단정, 03 rmem_max·tcp_rmem 커널 버전 조건, 04 duplex 쪽 반대 주장, 06 bridge VLAN 1 잔존), 05 없음 | **04 판정(메인)**: 1차 점검이 Cisco 10561-3에 맞춰 고친 것을 리뷰어가 Wikipedia로 반대 지적 → 메인이 Cisco 원문 재조회('FCS and alignment errors on the half-duplex side, and runts on the full-duplex port') → Cisco 유지, 이견 자료 1줄 병기(되돌림 금지 — 정지 규칙). 판정 워커 발사 |
| 2026-09-30 | 적대 리뷰 회수 42~48: 10건(42 SHA-256 무키 해시 변조 방지 오류, 43 s_client로 압축 탐지 불가, 44 no_context_takeover 메모리 절감 오류, 45 BANDWIDTH 조건, 47 Age 정의, 48 nf_conntrack_max 커널 버전 조건 …) | 판정 워커 발사 |
| 2026-09-30 | 적대 리뷰 회수 36~41: 7건(37 QUIC 유실 판정 규칙·QPACK 기본 0·migration 예외, 40 Node highWaterMark 64KiB는 v22부터, 41 416 비보장·suffix 범위 식), 36·38·39 없음 | 판정 워커 발사(37·40·41) |
| 2026-09-30 | 적대 리뷰 회수 21~28: 6건(21 재전송 고정 횟수, 23 close→RST 예외·**메인이 넣은 accept 넘침 줄 메커니즘 부정확**, 26 스위치 태그, 27 EAI_AGAIN 노트 내부 모순 확인, 28 nginx resolve 조건 zone·1.27.3), 22 없음 | 판정 워커 발사 |
| 2026-09-30 | 적대 리뷰 회수 14~20: 8건(14 UDP EMSGSIZE는 PMTUDISC_DO에서만·RFC 8085 keepalive 수준, 15 SYN 큐 한도=listen backlog·**SYN 재시도 127초는 6.5 이전 값**, 16 SYN 1/3/7초 패턴·ss rto 이중 계산, 17 zero window keepalive 원인, 19 tcp_orphan_retries 저장값 0), 20 없음 | **메인 확인**: 로컬 `sysctl tcp_syn_linear_timeouts=4`, kernel ip-sysctl '67seconds … final timeout … 131seconds' → tcp(7) 127초는 구 커널. 영향 노트 15·16·48·49 판정자에 전달(48은 실행 중 워커에 SendMessage). 웹 표본 #14(127초) '일치'는 tcp(7) 대조로는 맞으나 tcp(7) 자체가 구버전 — 표본 한계로 기록 |
| 2026-09-30 | 적대 리뷰 회수 29~35: 10건(29 0-RTT 외부 PSK·handshake_failure 대안, 30 CN 폴백 단정, 32 ssl_verify_depth 의미, 33 PATCH 캐시·4xx 재시도·Lax 예외 범위, 35 재사용 연결 cwnd·LB 요청 단위), 34 없음 | 판정 워커 발사 |
| 2026-09-30 | 적대 리뷰 회수 07~13: 12건(07 0.0.0.0/8 SSRF 누락, 08 경로 없음=ICMP net unreach·uRPF, 09 isReachable false 원인, 10 min_pmtu 아래 DF 해제·RFC 6864, 11 **포트 매핑 그림이 EIM MUST와 모순**·early_drop 서술 오류, 13 counting-to-infinity 그림 모순·GR) | 판정 워커 발사 |
| 2026-09-30 | 판정 회수 37·40·41: 7건 중 채택 6·부분 1(41 §14.2 인용은 맞음 — 416 비보장 주의만 추가)·기각 0, check 3 PASS | — |
| 2026-09-30 | 판정 회수 21·23·26·27·28: 7건 전부 채택(23 close RST 예외·accept 넘침 메커니즘 정정 — 서버 SYN-ACK 재전송·synack_retries 소진 시 버림, 27 EAI_AGAIN 모순 해소, 26 표에 EAI_AGAIN, 28 nginx resolve 조건), check 5 PASS | 23 한도 소진 뒤 결과(RST/타임아웃)는 커널 동작 추론 — 코드 줄 단위 미확인 |
| 2026-09-30 | 판정 회수 01~06: 9건 채택 6·부분 3·기각 0(03 rmem_max 4MiB는 6.18+·tcp_rmem 32MB는 6.16+ 커널 소스로 확인, 04 Cisco 유지+이견 1줄, 06 VLAN 1 제거 명령), check 6 PASS | — |
| 2026-09-30 | 판정 회수 42~48: 9건 채택 8·부분 1·기각 0(44 no_context_takeover 메모리 — zlib reset은 해제 안 함, 내부 모순 해소; 43 s_client -comp; 47 Age 정의) + 48 SYN 131초 6곳 반영, check 6 PASS | — |
| 2026-09-30 | 적대 리뷰 회수 49~53: 25건(49 6: REJECT=RST 오기·127초·구간 직렬 단정·503 게이트웨이 코드, 50 2, 51 5: RFC 8058 content-type·5xx 일괄 억제, **52 11: 사전 codex 지적 9건 중 7건이 Opus 점검 뒤에도 잔존** + SYN 타이밍 로컬 실측 133.7초, 53 1) | 판정 워커 2개(52 단독 · 49·50·51·53) 발사. 관찰: 1차 Opus 점검이 codex 지적과 겹치는 오류를 대부분 놓침 → 대체 리뷰가 유효 |
| 2026-09-30 | 판정 회수 14~19: 8건 채택 5·부분 3·기각 0(15·16 SYN 6.5+ 131초·선형 재시도 양쪽 병기, 14 UDP EMSGSIZE 조건, 17 keepalive 원인 = send queue 비어 있지 않음). 부분 3(15 SYN cookie 임계, 16 ss rto, 19 orphan_retries 저장값 0)은 man 페이지와 커널 소스가 어긋나는 곳 — 본문 유지 + 소스 근거 주의 줄, check 5 PASS | 관찰: man 페이지(tcp(7)·ss(8)·udp(7)·listen(2))가 최신 커널보다 뒤처진 곳이 반복 — NEXT 교훈 후보 |
| 2026-09-30 | 판정 회수 29~35: 9건 채택 7·부분 2·기각 0(32 ssl_verify_depth 1은 중간 1장 허용 — OpenSSL 1.1.0+ build_chain·man 확인, 30 CN 폴백 OpenSSL·JDK·Node 소스 확인, 33 PATCH 캐시·408/429·Lax 예외 범위, 35 idle 후 cwnd·L7 요청 단위 LB), check 5 PASS | 35 'Kubernetes Service 류 L4' 예시는 미확인 추가 |
| 2026-09-30 | 판정 회수 07~13: 12건 채택 9·부분 3·기각 0(11 포트 매핑 그림 EIM 모순 해소 + 리눅스 SNAT는 EIM 비보장·early_drop 소스 대로 정정, 13 counting-to-infinity 예시 재구성, 09 isReachable RST=true, 07 0.0.0.0/8), check 6 PASS | — |
| 2026-09-30 | 판정 회수 52: 11건 채택 9·부분 2·기각 0(SYN 6.5+ 양쪽 병기, accept 넘침 두 경로, REJECT ICMP→ECONNREFUSED, 경로 없음=ENETUNREACH 로컬 재현(IPv6), CLOSE-WAIT EPIPE는 RST 수신 조건, NODATA 정의, keepalive ETIMEDOUT), 리프 15·19·23·01·27과 일치 확인, check PASS | — |
| 2026-09-30 | 판정 회수 49·50·51·53: 14건 전부 채택(49 REJECT ICMP·SYN 2분·503 분리·HTTP/1.1 다중 연결·Happy Eyeballs 조건, 50 undici UND_ERR_CONNECT_TIMEOUT 문서 확인, 51 RFC 8058 multipart·5xx 정책 거절 분리·RFC 9989 §4.1, 53 serve-stale 조건). **대체 리뷰 판정 전부 완료: 51편** | 다음: 링크 전환 패스 → 전체 check·linkcheck → README 재생성 → post-fix 재점검 |
| 2026-09-30 | 링크 전환 패스(netrelink.py): 74줄 "미작성" → 직접 링크, 남은 네트워크 미작성 0(타 영역 미작성 참조 7건은 유효). 전체 check 51 PASS | linkcheck: base(HEAD) 209 → now 211, 신규 2건은 briefing.md 템플릿 자리표시자 링크(노트 아님) — 노트 신규 깨짐 0 |
| 2026-09-30 | gen_area_readme.py 보강: 커리큘럼 '기존' 칸이 신규인 leaf는 `cs/<area>/NN-slug/1-question.md` 존재로 노트 인식(3줄) → 재생성: network 미작성 0·원고 1(46)·초안 52(51 새 + 24). 다른 영역 README 변화 없음 | — |
| 2026-09-30 | post-fix 재점검(Opus, 노트 간 공통 사실 10종 일관성) 발사 | 회수 대기 |
| 2026-09-30 | 시범 worktree 2개 제거(scratchpad/ab-fable·ab-opus, 내용은 pilot 초안뿐 — 완성본은 cs/network, 블라인드 사본 scratchpad/blind 보존). 다른 세션 worktree(sn-37351)는 무관 — 유지 | — |
| 2026-09-30 | NEXT.md 갱신: N0-c(미작성 413, 네트워크 교훈·권장 파이프라인), N0-e(커리큘럼 오기 3건), N0-f(네트워크 51편 검수) | — |
| 2026-09-30 | 아카이브: CS 이슈 0건 — 사건형 문제(발생→원인→해결) 없음. 발견한 기술 사실(tcp(7) 127초는 6.5 이전 값, udp(7) EMSGSIZE 조건 등)은 노트 본문 15·16·48·52·14에 반영. codex 사용 한도·bwrap은 도구 사정(CS 원리 아님) | — |
| 2026-09-30 | post-fix 재점검 회수: 공통 사실 10종 노트 간 일관 — 14곳 9파일 정정(01 EHOSTUNREACH 설명·EAI_AGAIN, 04 요약 줄 runt 쪽, 15·16 선형 재전송 5회·[?] 2 제거·tcp_retries2 시간 한도, 27·48 resolver 무응답=EAI_AGAIN), 미수정 4건은 근거 있음(23 listen(2) 인용 등). check 51 PASS | 검증 완료 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 01~06 | Opus 독립 | 0 | 6 | 6 | 16→10 | 웹 표본 18건 제출 |
| 43~51 | Opus 독립 | 0 | 5 | ~10 | 6→4 | 웹 표본 18건 제출 |
| 37~42 | Opus 독립 | 0 | 1 | 12 | 5→3 | 웹 표본 18건 제출 |
| 31~36 | Opus 독립 | 0 | 5 | ~12 | 10→3 | 웹 표본 18건 제출 |
| 19~25 | Opus 독립 | 1 | 4 | 8 | 14→3 | 웹 표본 18건 제출, 중대 1건 메인 로컬 재확인 |
| 07~12 | Opus 독립 | 0 | 8 | ~17 | 12→9 | 웹 표본 18건 제출 |
| 26~30 | Opus 독립 | 0 | 11 | ~10 | 13→4 | 웹 표본 15건 제출 |
| 13~18 | Opus 독립 | 0 | 9 | ~15 | 26→11 | 웹 표본 18건 제출 |
| 49~53 | Opus 독립(리프 대조) | 0 | ~9 | ~6 | 6→3(+1) | 53 날조 인용 1건 교체 |
| 12·18·25·31·52 | codex 표본(high) | — | — | — | — | 편당 9~11건 잔존 → codex 전수 승격 |
| 웹 교차 | Opus 독립 | 24/24 일치 | | | | web-sample.md |
| 12·18·25·31 판정 | Opus(codex 지적) | 채택 29 | 부분 9 | 기각 0 | | 내부 모순 3건 해소 |
| 37·40·41 판정 | Opus(대체 리뷰 지적) | 채택 6 | 부분 1 | 기각 0 | | |
| 21·23·26·27·28 판정 | Opus(대체 리뷰 지적) | 채택 7 | 부분 0 | 기각 0 | | 27 내부 모순 해소 |
| 01~06 판정 | Opus(대체 리뷰 지적) | 채택 6 | 부분 3 | 기각 0 | | 04 메인 판정 적용 |
| 42~48 판정 | Opus(대체 리뷰 지적) | 채택 8 | 부분 1 | 기각 0 | | 44 내부 모순 해소 |
| 14~19 판정 | Opus(대체 리뷰 지적) | 채택 5 | 부분 3 | 기각 0 | | man vs 커널 소스 주의 줄 |
| 29~35 판정 | Opus(대체 리뷰 지적) | 채택 7 | 부분 2 | 기각 0 | | 29 내부 모순 해소 |
| 07~13 판정 | Opus(대체 리뷰 지적) | 채택 9 | 부분 3 | 기각 0 | | 11·13 내부 모순 해소 |
| 52 판정 | Opus(대체 리뷰 지적) | 채택 9 | 부분 2 | 기각 0 | | 리프 대조 |
| 49·50·51·53 판정 | Opus(대체 리뷰 지적) | 채택 14 | 부분 0 | 기각 0 | | |
| post-fix 재점검 | Opus(노트 간 일관성) | 정정 14 | | | 48(전체 잔여) | 51 PASS |

## 생략한 검증

- codex 전수(47편): 사용 한도 초과로 실행 불가 → 규칙대로 Opus 적대 리뷰로 대체(모델 다양성은 codex 표본 5편만). 한도 해제(23:18) 뒤 codex post-fix 표본은 이번 사이클에서 하지 않음 — 선택 후속.
- 08 blackhole `ip route get` EINVAL, 23 SYN-ACK 한도 소진 뒤 결과: 실행 검증 불가(userns 권한 없음) — man·커널 소스 근거.

## 완료 요약

- **산출**: `cs/network/` 새 노트 51편(01~23·25~45·47~53) × 3파일 = 153파일, 약 24,400줄, 질문 494개. 전부 통일 골격 7절·"Claude 초안" 표기. 24(systems/resp-protocol 초안)·46(원고)은 링크만.
- **모델**: A/B 시범(19·29) 결과 집필 Opus(중간 오류 A0/B3). 워커: 집필 Opus ×12(9+종합 2+완성 1), 사실 점검 Opus ×9, codex 표본 5, 대체 적대 리뷰 Opus ×8, 판정 Opus ×10, 웹 교차 Opus ×1, post-fix Opus ×1.
- **검증 경로와 수치**: check_new.py 51 PASS · 1차 사실 점검 중대 1·중간 약 58 수정, [?] 약 137→약 50 · 2차 리뷰(codex 표본 40 + 대체 리뷰 약 90) 판정 채택 약 110·부분 약 23·**기각 0** · 웹 교차 24/24 일치 · post-fix 공통 사실 정정 14 · 남은 [?] 48.
- **before → after(대표, 실파일)**: 25 `ip -s link`가 missed를 dropped에 합산 → 별도 칸(로컬 `ip -s link` 확인) · 15 SYN 포기 "약 127초(tcp(7))" → "6.5 이전 약 127초 / 6.5+ 약 131초(tcp_syn_linear_timeouts=4, 로컬 확인)" · 18 CUBIC 그림 K 이후 하강 → W_max 위 볼록 상승 · 11 포트 매핑 그림(EIM MUST 위반) → 호스트별 공인 포트 + 리눅스 SNAT는 EIM 비보장.
- **링크·트리**: "미작성" → 직접 링크 74줄, 노트 신규 깨진 링크 0 · 영역 README 재생성(network 미작성 0·초안 52·원고 1) · gen_area_readme.py에 leaf 폴더 인식 3줄.
