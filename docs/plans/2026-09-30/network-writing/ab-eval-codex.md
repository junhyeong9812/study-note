**A를 추천합니다. 차이는 결정적(decisive)입니다.** 두 작성자 모두 수정이 필요하지만, B는 잘못된 규칙을 질문과 정답에서 반복해 암기시키는 문제가 더 큽니다. 특히 TCP의 “첫 쓰기 성공·두 번째 쓰기 실패”, TLS의 ALPN 처리와 0-RTT 재전송 방어가 그렇습니다.

평가는 제공된 12개 파일만 대상으로 했으며, 작성자 신원은 추정하지 않았습니다. 심각도는 **높음＝보안·데이터 처리·핵심 개념을 잘못 판단하게 함**, **중간＝중요한 조건·예외 누락**, **낮음＝국소적 표현·진단 정확성 문제**로 구분했습니다. `[?]` 부재 자체는 오류가 아닙니다. 실제 근거가 확인되는 수치와 API에는 감점하지 않았습니다.

**A — TCP 종료 노트**

**① 사실 오류**

| 심각도 | 원문 인용·위치 | 교정 및 근거 |
|---|---|---|
| 높음 | 요약 C 코드: `if (n == 0) { /* 서버 FIN: 응답 완결 */ }` | EOF는 TCP 송신 종료입니다. 애플리케이션 응답의 완결을 보증하지 않습니다. 길이·프레이밍·프로토콜 종료 조건을 별도로 확인해야 합니다. [recv(2), RETURN VALUE](https://man7.org/linux/man-pages/man2/recv.2.html) |
| 중간 | “어느 상태에서든 RST를 받으면 CLOSED(또는 LISTEN)로 바로 간다” | 유효성 검사와 상태별 예외가 있습니다. LISTEN에서는 무시합니다. [RFC 9293 §3.5.3](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5.3) |
| 중간 | “수신 윈도 안의 시퀀스여야 인정된다”, “RST에는 응답 안 함” | §3.5.3의 기본 설명에는 근거가 있습니다. 다만 RFC 5961 방어를 구현한 스택은 `RCV.NXT`와 정확히 일치하지 않는 윈도 내부 RST에 challenge ACK를 보냅니다. 무조건적인 일반화가 문제입니다. [RFC 9293 §3.10.7.4](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.10.7.4) |
| 중간 | `close()` 후 “A는 FIN-WAIT-2에서 그 데이터를 계속 받는다” | 커널의 TCP 상태와 앱의 수신 가능성을 구분해야 합니다. POSIX `close()`로 해당 fd를 닫으면 앱은 그 fd로 읽지 못합니다. 계속 읽으려면 `shutdown(SHUT_WR)`을 사용합니다. [Oracle, Connection Release](https://docs.oracle.com/javase/8/docs/technotes/guides/net/articles/connection_release.html) |
| 중간 | “상대의 버그다”; “상대 FIN을 받았으면 반드시 `close()`한다” | FIN-WAIT-2/CLOSE-WAIT는 정상 half-close에서도 나타납니다. 남은 송신을 마친 뒤 종료해야 하며, 상태나 개수만으로 버그를 확정할 수 없습니다. [RFC 1122 §4.2.2.13](https://www.rfc-editor.org/info/rfc1122/) |
| 중간 | C 코드: `send(fd, req, len, MSG_NOSIGNAL); shutdown(...)` | `send()`가 전체 `len`을 보냈는지 확인하지 않습니다. 부분 전송·오류 후 바로 송신을 종료하면 요청이 잘릴 수 있습니다. [send(2), RETURN VALUE](https://man7.org/linux/man-pages/man2/send.2.html) |
| 중간 | “재전송까지 보장한다”; “그 뒤 쓰기는 `EPIPE`가 된다” | 정상 종료도 전송 실패·타임아웃으로 끝날 수 있습니다. 오류가 노출되는 호출과 순서 역시 고정되지 않습니다. [tcp(7), Error handling·ERRORS](https://man7.org/linux/man-pages/man7/tcp.7.html), [send(2), ERRORS](https://man7.org/linux/man-pages/man2/send.2.html) |
| 낮음 | “NAT·LB idle timeout이 먼저 연결 상태를 지우면 keepalive는 효과가 없다” | 연결 상태 삭제를 **예방하지 못한다**는 뜻이면 맞습니다. 이후 단절을 탐지하는 효과까지 없어지는 것은 아닙니다. [tcp(7), tcp_keepalive_time](https://man7.org/linux/man-pages/man7/tcp.7.html) |

추가로 “half-open 탐지는 주기적으로 말을 걸기뿐”이라는 문장과 read 타임아웃 표가 충돌합니다. 타임아웃은 상대 사망을 증명하지 않고, 기다림의 한계를 정합니다. `TCP_USER_TIMEOUT`도 자체적으로 유휴 연결에 탐지 패킷을 보내는 기능은 아닙니다. [tcp(7), TCP_USER_TIMEOUT](https://man7.org/linux/man-pages/man7/tcp.7.html)

**② `[?]` 없는 미확인·범위 미지정 단정**

- `Java ... Connection reset`, `Node Error: read ECONNRESET`는 가능한 예시입니다. 그러나 패킷 하나와 정확한 문자열·호출 결과를 일대일로 고정하려면 OS·런타임 버전과 재현 조건이 필요합니다.
- “Cloudflare 측정 약 940초”는 특정 실험 결과입니다. 기본 대기 시간처럼 외우게 해서는 안 됩니다.
- `resetAndDestroy()`는 실제 API지만 버전 조건이 빠졌습니다. Node 문서상 도입 버전은 **v18.3.0, v16.17.0**입니다. [Node net, resetAndDestroy](https://nodejs.org/api/net.html#socketresetanddestroy)
- 반대로 `tcp_retries2=15`, keepalive `7200/75/9`, `tcp_fin_timeout=60`, `TCP_USER_TIMEOUT`의 Linux 2.6.37 도입은 문서 근거가 있습니다. “검증되지 않은 숫자”로 분류하지 않습니다. [tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html)

**③ 가공된 API·옵션·수치**

확인된 가공 항목은 없습니다. 특히 **“RST 송신 측도 TIME-WAIT에 들어가기를 권한다”는 문장은 실제 RFC에 있습니다.** 소문자 `should`라는 강도까지 구분한 것은 장점입니다. [RFC 9293 §3.5.2](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5.2)

**④ 질문·정답 정확성**

- **1·2·6·7번:** 전형적인 종료·재부팅 시나리오에서는 대체로 정확합니다. 2번 상태 경로는 가능한 모든 경로가 아닌 대표 경로입니다.
- **3번:** “write는 성공할 수 있다”가 좋습니다. 이후 오류를 반드시 EPIPE로 고정한 부분은 수정해야 합니다.
- **4·5번:** 전송 보장 표현과 구현 범위를 수정해야 합니다. SHLD-3은 모든 소켓 API에 대한 무조건적 MUST가 아닙니다.
- **8번:** 제시한 원인은 가능합니다. SIGPIPE의 원인을 RST 수신 뒤 쓰기로 한정하면 안 됩니다.
- **9번:** 유휴 탐지와 미확인 송신 데이터 타임아웃을 구분해야 합니다.
- **10번:** 기본 윈도 검사는 맞지만 challenge ACK 설명을 추가해야 합니다.

**⑤ 가독성: 4/5**

첫 비교 그림이 FIN/RST/무응답을 빠르게 구분합니다. TCB·MSL·RTO를 근처에서 풀이하고 문장도 짧습니다. 다만 **11상태 전체 그림보다 정상 종료 패킷 그림을 먼저** 두는 편이 학습 목표에 맞습니다. “영원히”, “반드시”, “양쪽 다 안다” 같은 표현은 읽기는 쉽지만 조건을 숨깁니다.

---

**A — TLS 핸드셰이크 노트**

**① 사실 오류**

| 심각도 | 원문 인용·위치 | 교정 및 근거 |
|---|---|---|
| 높음 | “(EC)DHE만”; “모든 키 교환이 전방 비밀성을 가진다”; 정답 9 | `psk_ke`는 DHE 없는 PSK 단독 모드입니다. 이 일반화는 틀립니다. [RFC 8446 §2.2·§4.2.9](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.2.9) |
| 중간 | “모든 키는 transcript 해시를 넣은 HKDF로 유도된다”; 정답 5 | Extract 단계의 비밀과 transcript에 결합된 traffic secret을 구분해야 합니다. 변경 이후의 모든 키가 소급해서 바뀌지는 않습니다. [RFC 8446 §7.1](https://www.rfc-editor.org/rfc/rfc8446.html#section-7.1) |
| 중간 | “0-RTT는 멱등 요청에만 쓴다” | 멱등성만으로 허용 여부를 결정하면 부족합니다. HTTP의 기본 규칙은 추가 정보가 없을 때 safe 메서드만 허용하며, safe 메서드도 자원별 부작용을 검토해야 합니다. [RFC 8470 §3·§4](https://www.rfc-editor.org/rfc/rfc8470.html#section-4) |
| 중간 | “SNI가 빠지면 기본 인증서가 와서 호스트명 검증이 실패한다” | 기본 인증서가 대상 이름을 포함하면 성공할 수 있습니다. 서버가 즉시 거절할 수도 있습니다. SNI 누락은 인증서 불일치의 충분조건이 아닙니다. [RFC 6066 §3](https://www.rfc-editor.org/rfc/rfc6066.html#section-3) |
| 중간 | “`-tls1_2` / `-tls1_3`와 `-cipher`로 … 조합을 확인” | TLS 1.3 암호군은 `-ciphersuites`로 설정합니다. `-cipher`는 1.2 이하에 적용됩니다. [OpenSSL s_client, OPTIONS](https://docs.openssl.org/3.0/man1/openssl-s_client/) |
| 중간 | `openssl ... -sess_out s.pem </dev/null`을 재개 시험 절차로 제시 | stdin EOF로 세션 티켓을 받기 전에 종료할 수 있습니다. 티켓 수신·저장을 확인해야 합니다. [OpenSSL s_client, Note on Non-Interactive Use](https://docs.openssl.org/3.0/man1/openssl-s_client/#note-on-non-interactive-use) |
| 낮음 | “협상된 버전·암호군·ALPN 한눈에” 아래 `-brief` 사용 | 인용한 OpenSSL 3.0 계열의 brief 요약에는 ALPN 출력이 없습니다. 일반 출력에서 확인해야 합니다. [OpenSSL 3.0, print_ssl_summary](https://github.com/openssl/openssl/blob/openssl-3.0/apps/lib/s_cb.c) |

정답 5의 공격 방어 결론 자체는 맞습니다. 다만 handshake 키가 달라졌다면 Finished 검증에 이르기 전에 암호화 레코드 처리에서 실패할 수 있으므로, **실패 지점까지 고정하면 안 됩니다.**

**② `[?]` 없는 미확인·범위 미지정 단정**

- “HTTPS 요청의 첫 지연 대부분”은 측정 조건 없는 성능 일반화입니다.
- “재전송 중복이 네트워크가 불안한 모바일 사용자에게 몰린다”는 관측 근거가 없습니다. 가능한 시나리오라고 표시해야 합니다.
- OpenSSL의 DNS 이름 기반 자동 SNI는 **1.1.1부터**입니다. 버전 범위를 보충해야 합니다. [OpenSSL s_client, -servername](https://docs.openssl.org/3.0/man1/openssl-s_client/)
- nginx의 `ssl_early_data off`, 현재 `TLSv1.2 TLSv1.3` 기본값은 확인됩니다. TLS 1.3 기본 포함은 1.23.4부터라는 설명을 더하면 좋습니다. [nginx ssl module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- Java의 SAN 불일치 문자열은 실제 OpenJDK 코드에 있습니다. 따라서 가공 문자열은 아니며, **항상 이 문자열이 나온다는 보장만 피하면 됩니다.** [OpenJDK HostnameChecker.matchDNS](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/sun/security/util/HostnameChecker.java)

**③ 가공된 API·옵션·수치**

확인된 가공 항목은 없습니다. 제시한 alert 번호도 맞습니다. **RFC 9849는 실제 ECH RFC**이므로 가공 인용으로 판정하지 않습니다. [RFC 9849](https://www.rfc-editor.org/rfc/rfc9849.html)

**④ 질문·정답 정확성**

- **1·2·3·4·10번:** 명시한 전형적 핸드셰이크 범위에서 대체로 정확합니다. 10번은 TLS 1.2 False Start·TCP Fast Open 등을 제외한 계산임을 적으면 명확합니다.
- **5번:** 방어 원리는 맞지만 키 스케줄·실패 지점 설명을 수정해야 합니다.
- **6번:** SNI 누락 후 실패를 필연으로 만들면 안 됩니다.
- **7번:** ALPN을 지원하고 협상에 참여하는 서버라는 조건이 필요합니다.
- **8번:** TLS 1.3용 `-ciphersuites`가 빠졌습니다.
- **9번:** 질문의 전제와 정답 모두 PSK 단독 모드를 누락한 핵심 오류입니다.

**⑤ 가독성: 4/5**

1.3 전체 흐름을 먼저 보여 주고 1.2와 비교하는 순서가 좋습니다. `{}`와 `[]`로 키 종류를 구분하고 ECDHE·MAC·RTT를 가까이 설명합니다. 다만 요약·핵심 문장·정답의 반복량이 많고, 잘못된 “항상 전방 비밀성”도 반복됩니다.

---

**B — TCP 종료 노트**

**① 사실 오류**

| 심각도 | 원문 인용·위치 | 교정 및 근거 |
|---|---|---|
| 높음 | 정답 2: “첫 번째 `write()`: 성공한다”; “두 번째 `write()`: 실패한다” | 호출 횟수로 결과를 결정할 수 없습니다. RST 도착·처리 시점, 버퍼, 다른 호출의 오류 소비에 따라 성공·부분 전송·ECONNRESET·EPIPE 등이 달라집니다. [send(2), DESCRIPTION·ERRORS](https://man7.org/linux/man-pages/man2/send.2.html) |
| 중간 | 도입: “프로세스 죽음… FIN을 보낼 주체가 없다” | 프로세스 종료 뒤에도 커널은 살아 있고 fd를 정리합니다. FIN/RST 없이 사라지는 호스트 장애와 다릅니다. 뒤의 half-open 절은 이를 바로잡아 문서 내부에서도 모순됩니다. [_exit(2), DESCRIPTION](https://man7.org/linux/man-pages/man2/_exit.2.html) |
| 중간 | “이미 닫은(FIN 또는 RST를 보낸) 소켓에 `write()` → … EPIPE와 SIGPIPE” | FIN 수신만으로 내 송신 방향이 닫히지는 않습니다. 정상 half-close에서는 계속 쓸 수 있습니다. [RFC 1122 §4.2.2.13](https://www.rfc-editor.org/info/rfc1122/) |
| 중간 | “SYN-RECEIVED면 LISTEN으로 복귀”; “사용자에게 알림이 … ECONNRESET” | LISTEN에서 진입한 경우만 복귀합니다. 능동 open 경로에서는 CLOSED와 연결 거절 처리가 가능합니다. [RFC 9293 §3.10.7.4](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.10.7.4) |
| 중간 | “시퀀스 번호가 윈도 안이면 유효한 RST” | A와 동일하게 challenge ACK 방어의 적용 조건을 누락했습니다. [RFC 9293 §3.10.7.4](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.10.7.4) |
| 중간 | 상태도에서 SYN_SENT가 SYN_RECEIVED를 거쳐 ESTABLISHED로 이어짐 | 정상 능동 연결의 SYN-SENT → ESTABLISHED 경로가 빠졌습니다. 종료 부분의 화살표도 ESTABLISHED로 돌아가는 것처럼 연결돼 있습니다. 단순 생략보다 잘못된 경로 학습 위험이 큽니다. [RFC 9293 Figure 5](https://www.rfc-editor.org/rfc/rfc9293.html#figure-5) |
| 중간 | “FIN_WAIT_2 누적 = 상대 앱이 close 안 함”; 정답 6 “내 앱 잘못” | 정상 half-close·처리 중인 연결·네트워크 장애도 고려해야 합니다. 상태만으로 책임을 확정할 수 없습니다. [RFC 1122 §4.2.2.13](https://www.rfc-editor.org/info/rfc1122/) |
| 중간 | “그동안 `write()`는 성공한다” | 버퍼 여유가 있는 동안 성공할 수 있을 뿐입니다. 버퍼가 차면 블록되거나 비차단 호출에서 EAGAIN 등이 발생합니다. [send(2), DESCRIPTION](https://man7.org/linux/man-pages/man2/send.2.html) |
| 중간 | 질문 5: “먼저 `close()`한 쪽만 TIME_WAIT에 들어간다” | 동시 종료에서는 양쪽 모두 진입합니다. 본문에 있는 설명과 질문의 전제가 충돌합니다. [RFC 9293 Figure 13](https://www.rfc-editor.org/rfc/rfc9293.html#figure-13) |

`tcp_retries2=15`를 “항상 정확히 15회 재전송한 뒤 종료”로 외우게 하는 것도 부정확합니다. 실제 구현은 재전송 시간 한계를 계산하며, 커널 문서는 해당 값에서 유도한 시간이 실효 타임아웃의 하한이라고 설명합니다. [Linux IP sysctl, tcp_retries2](https://docs.kernel.org/networking/ip-sysctl.html)

**② `[?]` 없는 미확인·범위 미지정 단정**

- 정답 2의 `Broken pipe`·`Connection reset`·Node EPIPE 매핑은 특정 호출 순서의 재현 결과로 제한해야 합니다.
- `SocketInputStream.socketRead0`는 JDK 구현·버전 의존적인 스택 예시입니다.
- 풀의 `validationTimeout`을 “모든 read의 타임아웃”과 나란히 놓았습니다. 풀 제품도 명시하지 않았고, 연결 검증 제한과 요청 읽기 제한은 구분해야 합니다.
- “타이머가 없으면 half-open”, “상대 ESTABLISHED가 있으면 그냥 느림”처럼 읽히는 진단은 충분조건이 아닙니다. 양쪽 상태가 남아 있어도 경로가 단절될 수 있습니다.
- 반대로 Linux `TCP_TIMEWAIT_LEN = 60*HZ`와 `__tcp_close`는 실제 코드에 있습니다. [Linux tcp.h](https://github.com/torvalds/linux/blob/master/include/net/tcp.h), [Linux tcp.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp.c)

**③ 가공된 API·옵션·수치**

확인된 가공 항목은 없습니다. `validationTimeout`은 출처·의미가 불명확한 항목이지, 존재하지 않는 API라고 단정할 수는 없습니다.

“Java·Node는 SIGPIPE를 기본적으로 무시한다”는 설명에도 근거가 있습니다. 다만 “시그널을 EPIPE로 변환한다”보다는 **시그널 종료를 피하고 I/O 오류를 전달한다**가 정확합니다. [OpenJDK POSIX signal 처리](https://github.com/openjdk/jdk/blob/master/src/hotspot/os/posix/signals_posix.cpp), [Node process, Signal events](https://nodejs.org/api/process.html#signal-events)

`K&R 3.5 (TCP)`는 서지 정보가 불충분합니다. 이 약칭만으로 가공 출처라고 판정하지 않습니다.

**④ 질문·정답 정확성**

- **1·3·4·9·10번:** 기본 방향은 좋습니다. 4번의 재연결은 같은 포트만이 아니라 **같은 4-튜플**이 조건입니다. 9번의 시간·횟수와 10번의 종료 필요성에는 구현·프로토콜 조건이 필요합니다.
- **2번:** 질문 자체가 고정된 두 호출 결과를 요구하므로 전면 수정해야 합니다.
- **5번:** “먼저 닫은 쪽만”이라는 전제가 틀렸습니다.
- **6번:** 상태 진단을 책임 확정으로 바꾼 잘못된 정답입니다.
- **7번:** SIGPIPE 대처는 맞지만 FIN 수신만으로 쓰기 오류가 난다는 설명은 틀립니다.
- **8번:** 로컬 `ss`만으로는 half-open과 정상 유휴·느린 상대를 확정 구분할 수 없다고 먼저 답해야 합니다.

**⑤ 가독성: 3/5**

FIN 흐름을 먼저 제시하고 `shutdown`과 `close`를 명시적으로 구분한 점은 A보다 좋습니다. 반면 상태도 화살표가 불명확하고, “상태＝누구 잘못”이라는 강한 표제가 오진을 유도합니다. 질문 2·8번은 여러 조건과 언어별 결과를 한꺼번에 요구해 한 문항의 부담도 큽니다.

---

**B — TLS 핸드셰이크 노트**

**① 사실 오류**

| 심각도 | 원문 인용·위치 | 교정 및 근거 |
|---|---|---|
| 높음 | “(EC)DHE만… 항상 전방 비밀성”; 정답 2·3 | A와 동일한 PSK 단독 모드 누락입니다. [RFC 8446 §4.2.9](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.2.9) |
| 높음 | “셋 중 하나 MUST: 단일 사용 티켓 / ClientHello 기록 / freshness 검사” | freshness 검사만으로 중복 수락을 막지 못합니다. 최소 요구는 인스턴스별 동일 0-RTT 핸드셰이크 최대 한 번 수락입니다. [RFC 8446 §8·§8.3](https://www.rfc-editor.org/rfc/rfc8446.html#section-8.3) |
| 중간 | “서버는… 클라이언트 선호가 가장 높은 것을 고른다” | RFC의 SHOULD는 **서버 선호 순서**에 따른 공통 프로토콜 선택입니다. [RFC 7301 §3.2](https://www.rfc-editor.org/rfc/rfc7301.html#section-3.2) |
| 중간 | 정답 6: 교집합이 없으면 “ALPN 확장을 응답에서 빼고 진행”도 선택지 | ALPN 협상에 참여한 서버의 교집합이 비면 fatal alert가 규칙입니다. ALPN 미지원·미협상과 교집합 부재를 혼동했습니다. [RFC 7301 §3.2](https://www.rfc-editor.org/rfc/rfc7301.html#section-3.2) |
| 중간 | “재개 연결은 0-RTT”; 표·핵심 문장 반복 | PSK 재개가 0-RTT를 자동으로 뜻하지 않습니다. early data는 선택 기능입니다. [RFC 8446 §2.2·§2.3](https://www.rfc-editor.org/rfc/rfc8446.html#section-2.2) |
| 중간 | 0-RTT 그림의 `{NewSessionTicket}`, `{EndOfEarlyData}` | 자체 범례와 맞지 않습니다. 전자는 application traffic 키, 후자는 RFC 본문상 early traffic 키로 보호됩니다. [RFC 8446 §4.5·§4.6](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.5) |
| 중간 | “RSA PKCS#1 v1.5 서명… 제거(서명은 RSASSA-PSS)” | CertificateVerify의 RSA 제한과 인증서 서명을 구분해야 합니다. ECDSA·EdDSA도 존재합니다. [RFC 8446 §4.2.3·§4.4.3](https://www.rfc-editor.org/rfc/rfc8446.html#section-4.4.3) |
| 중간 | 정답 8: “각 Derive-Secret에는 그 시점까지의… 해시” | `derived`·binder 등은 빈 transcript를 사용합니다. [RFC 8446 §7.1](https://www.rfc-editor.org/rfc/rfc8446.html#section-7.1) |
| 낮음 | 근거 목록: “§9.2 필수 확장(server_name·ALPN)” | ALPN은 그 필수 구현 목록에 없습니다. [RFC 8446 §9.2](https://www.rfc-editor.org/rfc/rfc8446.html#section-9.2) |

A와 같은 `-sess_out ... </dev/null` 문제도 있습니다. 반면 B는 TLS 1.3용 `-ciphersuites`를 정확하게 사용했습니다. [OpenSSL s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/)

**② `[?]` 없는 미확인·범위 미지정 단정**

- curl·Node/OpenSSL 오류 문자열과 출력 예시는 백엔드·버전 범위를 표시해야 합니다.
- 정답 9의 “버전을 고정했더니 통과하면 버전 문제”는 진단 가설입니다. 버전 고정은 다른 협상 조건도 바꾸므로 단독 증명이 아닙니다.
- 정답 10의 “가장 흔한 원인”에는 빈도 근거가 없습니다. HRR의 원인을 그룹 불일치로만 설명한 것도 범위가 좁습니다.
- SNI가 없거나 IP로 접속하면 반드시 같은 인증서 오류가 난다는 설명 역시 조건부로 고쳐야 합니다.
- `setApplicationProtocols`의 Java 9 도입은 맞습니다. 그러나 예제 전체의 TLS 1.3 지원까지 Java 9부터라고 읽히지 않도록 구분해야 합니다. [Java SSLParameters, setApplicationProtocols](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/javax/net/ssl/SSLParameters.html#setApplicationProtocols(java.lang.String%5B%5D))

**③ 가공된 API·옵션·수치**

확인된 가공 API·옵션은 없습니다. alert 번호, ALPN 확장 번호 16, 티켓 수명 상한 604800초는 맞습니다. 문제는 숫자를 만들어 낸 것이 아니라 **실제 표준의 적용 조건과 의무 수준을 잘못 설명한 것**입니다.

**④ 질문·정답 정확성**

- **1·7번:** 전형적인 인증서 기반 핸드셰이크와 버전 협상 설명으로 대체로 정확합니다.
- **2·4·6번:** 각각 PSK 누락, freshness 검사, ALPN 처리 때문에 핵심 정답이 틀렸습니다.
- **3번:** 0-RTT의 두 약점은 맞지만 “1-RTT에는 항상 DHE가 섞인다”는 설명은 수정해야 합니다.
- **5번:** 인증서 이름이 맞으면 성공할 수 있다는 조건을 넣어야 합니다.
- **8번:** 세 비밀의 큰 구조는 좋지만 transcript 적용 범위를 수정해야 합니다.
- **9번:** 진단 순서는 유용합니다. 한 번의 성공으로 원인을 확정하는 부분은 과도합니다.
- **10번:** 그룹 재선택 사례에는 맞지만 HRR 전체의 설명은 아닙니다.

**⑤ 가독성: 4/5**

암호군 이름 비교표와 키 스케줄 설명이 유용하고, 용어 풀이도 비교적 가깝습니다. 다만 1.3이 주제인데 1.2 전체 흐름부터 시작하며, “압축·DSA·RSA 서명 제거”처럼 서로 다른 규칙을 한 칸에 압축합니다. 간결한 핵심 문장이 오히려 잘못된 일반화를 강화합니다.

| 비교 항목 | A | B |
|---|---|---|
| TCP 정확성 | EOF·응답 완결 혼동과 조건 누락 | 추가로 쓰기 횟수별 결과를 고정하고 상태만으로 책임 확정 |
| TLS 정확성 | PSK 예외 누락, 일부 도구·보안 조건 오류 | 공통 오류에 ALPN·재전송 방어·재개 설명 오류 추가 |
| 질문·정답의 신뢰도 | 부분 수정으로 살릴 문항이 많음 | 질문 전제부터 바꿔야 하는 핵심 문항이 더 많음 |
| 불확실성 표시 | `[?]`를 사용하지만 적용이 일관되지는 않음 | 구현·버전 의존 주장을 거의 모두 단정 |
| 가공 API·옵션·수치 | 확인되지 않음 | 확인되지 않음 |
| TCP 가독성 | **4/5** | **3/5** |
| TLS 가독성 | **4/5** | **4/5** |
| 채택 판단 | **수정용 원본으로 추천** | 핵심 정답 재작성 필요 |

**최종 추천: A — 결정적 우세(decisive).** 특히 B의 0-RTT 방어 정답은 실제 보안 설계를 잘못 이끌 수 있습니다. 다만 A도 **PSK 단독 모드와 FIN≠응답 완결**을 고치기 전에는 검수 완료된 학습 자료로 사용하면 안 됩니다.