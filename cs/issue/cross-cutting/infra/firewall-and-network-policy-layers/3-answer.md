# cs/issue/infra/firewall-and-network-policy-layers — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **ufw는 INPUT 체인, Docker publish는 FORWARD→DOCKER 체인.** \
   ufw는 "호스트로 들어오는" 패킷이 지나는 INPUT 체인에 규칙을 건다. \
   Docker가 포트를 publish하면 목적지를 컨테이너 IP로 바꾸는 NAT가 먼저 걸리고, 그 패킷은 호스트 프로세스가 아니라 브리지 너머 컨테이너로 **전달(FORWARD)**된다. \
   Docker는 이 경로의 DOCKER 체인에 `0.0.0.0/0 → 컨테이너:9200 ACCEPT`를 스스로 넣으므로, INPUT의 ufw 화이트리스트는 이 패킷을 한 번도 보지 못한다.
   > **iptables 체인** — 패킷이 경로(들어옴 INPUT / 통과 FORWARD / 나감 OUTPUT)에 따라 지나는 규칙 목록. 같은 호스트라도 경로가 다르면 다른 체인이 판정한다.

2. **알 수 없다.** \
   인증이 꺼져 있으면 요청에 "누구"가 없고, 감사 로그가 꺼져 있으면 호출 기록도 없다. 저장소 내부 로그로 "한 번의 호출에 이름을 명시해 지웠다"(같은 스레드·1ms 간격, 시스템 인덱스는 보존)까지는 좁혔지만 호출자 IP·주체는 남지 않았다. \
   유일하게 작동한 가드는 "와일드카드 대량 삭제 거부(이름 명시 요구)"였다 — 실수로 `*`를 지우는 사고는 막지만, **이름을 정확히 적은 삭제는 그대로 통과**시킨다. \
   쓰기 차단 블록도 삭제는 막지 못했고, 사후에 택한 정식 방어는 **역할 기반 권한(삭제 권한을 운영 계정에서 제거)**이었다(엔진에 따라 메타데이터까지 잠그는 읽기 전용 블록은 삭제도 막지만 정상 쓰기까지 멈추므로 상시 방어로는 부적합).
   > **감사 로그(audit log)** — 누가·언제·무엇을 호출했는지 남기는 로그. 사후 포렌식의 유일한 재료다.

3. **MAC(SELinux)이다.** \
   RHEL 계열의 SELinux 기본(targeted) 정책은 웹서버 도메인(`httpd_t`)의 **임의 포트로의 아웃바운드 연결을 막는다**(`httpd_can_network_connect=off` — 허용 범위는 대상 포트 라벨·다른 boolean 조합에 따라 다름). \
   리버스 프록시는 바로 "웹서버가 밖으로 connect"하는 일이라 커널이 `EACCES(13)`로 즉시 거부한다. \
   셸의 `curl`은 비제한(unconfined) 도메인에서 돌아 허용되므로 "나는 되는데 nginx만 안 된다"는 착시가 생긴다. \
   `setsebool -P httpd_can_network_connect 1`로 켠다(전역·재부팅 유지·reload 불필요). 같은 계층의 인접 함정: `/tmp`에서 옮긴 설정 파일은 임시 파일 라벨을 달고 있어 `restorecon`으로 라벨을 되돌려야 한다.
   > **MAC(강제 접근 제어)** — 파일 소유자 권한(DAC)과 별개로, 정책이 프로세스 도메인별로 허용 동작을 정하는 방식. enforcing 모드에서는 root로 실행돼도 제한된 도메인이면 정책을 넘지 못한다.

4. **빠른 502 = 능동 거부, 느린 504 = 무응답**(nginx 기준 일반론 — 502는 잘못된 upstream 응답 등 다른 원인도 있다). \
   프록시가 upstream에 connect하다 refused·reset·EACCES를 받으면 즉시 502를 돌려준다. \
   패킷이 DROP되면 응답이 없어 타임아웃까지 기다린 뒤 504가 된다. \
   이번엔 connect 0.06초 만의 502였으므로 "경로가 끊겼다(DROP·timeout)"가 아니라 "누군가 즉시 거부했다"였다. 단, upstream 프로세스가 죽어 있어도 connection refused로 빠른 502가 나므로 **이 구분만으로는 "upstream 사망"을 배제하지 못한다.** 구간별로 잘라 보니(upstream 직접 호출 200·포트 OPEN·설정 일치) 거부 주체는 프록시 호스트 자신이었고, error.log의 `Permission denied`가 결정타였다. \
   "502 = upstream 미연결"이라는 런북의 단정을 반증한 것은 이 구간별 확인(upstream 직접 200)과 `EACCES`였다 — 속도 분별은 후보를 좁혔을 뿐이고, 런북은 한 계층만 의심해 오진을 부를 뻔했다.

5. **출발지 포트는 클라이언트가 임의로 고른다.** \
   브라우저가 443에 접속할 때 자기 쪽 포트는 OS가 고른 임시 포트(예: 50000번대)다. \
   Source Port Range = 443은 "출발지 포트가 443인 패킷만 허용"이므로 현실의 어떤 클라이언트와도 매칭되지 않아 보안 목록에서 전량 버려진다 — 호스트까지 오지도 않으니 tcpdump는 0패킷이다. \
   서비스 포트는 **Destination Port**에, Source Port는 All로 둔다.
   > **ephemeral port(임시 포트)** — 클라이언트가 연결마다 OS로부터 받는 임의의 출발지 포트.

6. **바깥→안쪽 점검 목록.** \
   ① 클라우드 보안 목록/보안 그룹(목적지 포트·출발지 대역) → ② 호스트 패킷 필터(ufw/firewalld — INPUT) → ③ 컨테이너 런타임의 체인(publish 바인딩 주소 — ufw와 무관) → ④ MAC(SELinux 도메인 boolean·파일 라벨) → ⑤ 애플리케이션 인증·권한·감사. \
   각 계층은 **다른 계층의 설정을 알지 못한다.** 한 곳을 열었다고 통하지 않고(보안 목록·SELinux 사례), 한 곳을 닫았다고 막히지 않는다(ufw·Docker 사례).

7. **단기 = 네트워크 계층, 중기 = 앱 계층.** \
   `127.0.0.1:` 바인딩·publish 제거는 [3] 컨테이너 체인에서 **도달 자체를 줄인다**. \
   인증+TLS+감사+역할 분리(운영 계정에 삭제 권한 없음·초기화는 관리자만)는 [5] 앱 계층에서 **도달해도 할 수 있는 일을 줄인다.** \
   네트워크 계층은 이번처럼 다른 계층의 설정 하나로 조용히 우회될 수 있으므로, "도달 = 전권"인 구조를 없애는 앱 계층 권한이 따로 있어야 한다 — 최소 권한은 계층마다 적용한다. 여기에 스냅샷 저장소 등록(백업)이 복구의 마지막 선이 된다.
   > **최소 권한(least privilege)** — 각 주체에 그 일에 필요한 권한만 주는 원칙. 한 방어선이 뚫려도 피해 범위를 제한한다.

## 문제 구조 (추상화 코드)

### 변형 A — 컨테이너 publish가 호스트 방화벽을 우회 (앱 인증도 꺼짐)

① 문제 구조
```yaml
# compose
services:
  store:
    ports:
      - "9200:9200"            # 바인딩 주소 생략 = 0.0.0.0 (모든 인터페이스)
    environment:
      security.enabled: "false" # 인증·감사 없음
      cors.allow-origin: "*"
```
```text
# 호스트: ufw allow from <허용 IP>       → INPUT 체인
# docker 가 넣은 규칙 (iptables -L DOCKER):
ACCEPT tcp -- !br-x br-x 0.0.0.0/0 <container-ip> dpt:9200   → FORWARD 경로, ufw 무관
```
② 고친 구조
```yaml
services:
  store:
    ports:
      - "127.0.0.1:9200:9200"  # 도달 자체를 로컬로 제한 (또는 publish 제거)
    environment:
      security.enabled: "true" # + TLS + audit
# 역할: app_user = 읽기/쓰기만, 인덱스 삭제 없음 / 초기화는 admin 만
# 백업: 스냅샷 저장소 등록 (스케줄만 있고 저장소 0개였음)
```
무엇이 깨졌나: ufw 화이트리스트를 "호스트 전체의 방화벽"으로 믿었지만 컨테이너 행 패킷은 다른 체인을 지났고, 앱 계층 인증도 없어 네트워크 도달이 곧 삭제 권한이었다.\
같은 구조: 같은 사건의 사후 분석 — 이름 명시 요구 가드는 와일드카드만 막고, 쓰기 블록은 삭제를 못 막으며, 역할 권한만이 정식 방어라는 결론.

### 변형 B — MAC이 데몬의 아웃바운드 연결을 거부

① 문제 구조
```nginx
location / {
    proxy_pass http://<upstream>:<port>;   # 설정은 정상
}
# error.log: connect() to <upstream> failed (13: Permission denied)
# 같은 호스트 셸: curl http://<upstream>:<port>  → 200  (unconfined 도메인)
```
② 고친 구조
```bash
setsebool -P httpd_can_network_connect 1   # 웹서버 도메인의 외부 connect 허용 (전역·영속)
mv /tmp/site.conf /etc/nginx/conf.d/ && restorecon -v /etc/nginx/conf.d/site.conf   # 옮긴 파일 라벨 복원
```
무엇이 깨졌나: 파일 권한·방화벽·upstream이 모두 정상이어도 MAC 정책이 프로세스 도메인 단위로 connect를 막았고, 셸에서의 성공이 데몬의 성공을 보증하지 않았다.

### 변형 C — 클라우드 보안 목록에 출발지 포트를 제한

① 문제 구조
```text
Ingress rule:  source CIDR 0.0.0.0/0   source port 443   dest port (all)
               → 클라이언트 출발지 포트는 임의 → 매칭 0 → 호스트 tcpdump 0 패킷
```
② 고친 구조
```text
Ingress rule:  source CIDR 0.0.0.0/0   source port (all)   dest port 443
```
무엇이 깨졌나: 서비스 포트를 목적지가 아니라 출발지 칸에 넣어, 호스트 방화벽까지 오기 전 가장 바깥 계층에서 전부 버려졌다.\
같은 구조: 같은 작업의 인접 함정 — 서버 버전에 따라 `http2` 지시어 문법이 달라(구버전은 `listen ... ssl http2`) 설정 계층에서도 "다른 판본의 규칙"이 적용된다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
