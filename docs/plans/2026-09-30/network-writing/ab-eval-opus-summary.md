# A/B 블라인드 평가 — Opus 평가자 요약 (A=Opus 집필, B=Fable 집필)

- 결론: A 권고, 근소하나 방향 분명. 중간 사실 오류 A 0 / B 3.
- B 오류: RFC 8446 §8 SHOULD를 MUST로 격상 · ALPN 선택 기준 역전(서버 선호가 기준, RFC 7301 §3.2) · 19 Q2 두 번째 write → 리눅스는 ECONNRESET(sk_stream_error, SIGPIPE 없음), EPIPE는 그 다음 · "FIN 받은 소켓 write → EPIPE" 부정확 · PKCS#1 v1.5 제거 과장(핸드셰이크 서명만) · ALPN 교집합 부재 시 RFC 밖 동작을 대등하게 소개.
- A 경미: HPBN 링크 404(정답 https://hpbn.co/transport-layer-security-tls/) · 0-RTT 블룸 필터 거짓 양성 = 0-RTT만 거절하고 1-RTT 진행(§8.2, 핸드셰이크 중단 MUST NOT) · 19 Q3 RST 뒤 첫 쓰기는 ECONNRESET · Go는 비표준 fd SIGPIPE를 EPIPE로 변환.
- [?]: B 0개(미확인 단정 다수) · A 10개 중 8개는 실제로 맞음(과잉 보수).
- B에만 있는 깊이 요소(이식 후보): 리눅스 TCP_TIMEWAIT_LEN 60초·__tcp_close(RFC 2525 §2.17 RST), ss -o 타이머 해석, tcp_orphan_retries, 11상태 완결 상태도, legacy_version·미들박스·HRR, TLS 경보 표, 키 스케줄 표, s_client -msg -state 진단 절차.
