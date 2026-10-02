# reliability/50-sidecar-ambassador-and-service-mesh — 정답

## 정답

### 1. 세 패턴

- 사이드카: 주 컨테이너를 보강. 예: 웹 서버 로그를 모으는 logsaver, git에서 콘텐츠를 주기적으로 받아 오는 동기화 컨테이너.
- 앰배서더: 바깥 통신을 대리. 예: twemproxy로 memcache 샤드에 나눠 보내기. 앱은 localhost의 서버 하나에 붙는다고만 생각한다.
- 어댑터: 주 컨테이너의 출력을 바깥이 기대하는 형식으로 맞춤. 예: 지표 형식 통일.
- 공통: 같은 기계(파드)의 컨테이너가 localhost 네트워크와 볼륨을 공유할 수 있다는 성질.

### 2. 위임할 수 있는 것·없는 것

- 있는 것: mTLS(인증서 발급·교체 포함), RED 지표·홉 스팬, 연결 실패 재시도, 트래픽 분할. HTTP 수준에서 업무와 무관하게 똑같이 할 수 있다.
- 없는 것: 어떤 연산이 멱등인지, 재시도해도 되는지, 폴백 값. 업무 의미는 앱만 안다.
- Azure Ambassador 문서: 프록시가 재시도를 맡을 수 있지만 **모든 연산이 멱등이 아니면 안전하지 않을 수 있다**. 클라이언트가 헤더로 재시도를 끄거나 최대 횟수를 지정하는 장치를 고려하라고 적는다.

### 3. 재시도 곱셈

(실험, Envoy 1.35.13 + JDK 21)

- 백엔드 **9번**(앱 시도 1·2·3 각각에 Envoy 시도 1·2·3).
- 앱 로그에는 `HTTP 503` 세 줄과 `포기`만 보인다. Envoy 재시도는 앱에서 보이지 않는다.
- 일반식: 최악 증폭 = Π(1 + 각 계층 재시도 수).

### 4. Istio 기본 재시도

- 지정하지 않으면 메시 기본 정책 `attempts: 2`, `retryOn: "connect-failure,refused-stream,unavailable,cancelled"`(VirtualService 레퍼런스, MeshConfig `defaultHttpRetryPolicy`로 변경 가능).
- 기본값만으로 생기는 증폭: 연결 실패·거절된 스트림·gRPC UNAVAILABLE에서 앱 재시도 × 3.
- 3번의 모양: 누군가 `retryOn`에 `5xx`를 넣고 앱도 5xx에 재시도할 때. 기본 정책은 일반 HTTP 5xx 응답 전체를 대상으로 하지 않는다.

### 5. 사이드카 준비 전 호출

(실험)

- 앱 3번 모두 실패. JDK `HttpClient.send()`는 `java.net.ConnectException`(메시지 `null`)을 던졌고, 원인 체인 맨 끝이 `ClosedChannelException`이었다(실험 앱 출력은 맨 안쪽 원인).
- raw 소켓은 `java.net.ConnectException: Connection refused`. 4초 뒤에는 연결됐다.
- 쿠버네티스: 네이티브 사이드카(`initContainers` + `restartPolicy: Always`, 1.33 stable). 사이드카가 started가 된 뒤 다음 컨테이너가 시작된다. `startupProbe`를 두면 그 성공이 started 조건이다.
- Istio: `holdApplicationUntilProxyStarts: true`(기본 false).

### 6. Chassis vs 메시

| | Chassis | 메시 |
|---|---|---|
| 언어 | 언어마다 | 무관 |
| 업그레이드 | 서비스마다 재빌드·배포 | 프록시만 교체 |
| 업무 문맥 | 안다 | 모른다 |
| 장애 반경 | 그 서비스 | 설정 오류가 메시 전체 |

- 원칙: 같은 일을 두 곳에 두지 않는다. 예: mTLS·기본 관측은 메시, 업무 재시도·폴백·멱등 키는 앱. 재시도를 둘 다 하면 곱을 계산하고 예산을 둔다.

### 7. 디스커버리와 등록

- 클라이언트 측: 클라이언트가 레지스트리에 묻고 직접 골라 부른다(Eureka + Ribbon).
- 서버 측: 클라이언트는 잘 알려진 라우터·LB로 보내고 라우터가 고른다(AWS ELB, 쿠버네티스 Service).
- 자기 등록: 인스턴스가 시작 때 등록, 종료 때 해제, 주기적으로 갱신(Eureka 클라이언트).
- 제3자 등록: 등록기가 인스턴스를 지켜보며 대신 등록·해제(Registrator, 쿠버네티스).

### 8. TTL과 죽은 인스턴스

(실험, 가상 시계 시뮬레이션)

- B의 마지막 하트비트는 t=1초. 빠지는 시각 ≈ 1초 + TTL.
- TTL 3초: t=4초까지 B로 간 호출 **7건** 실패(마지막 실패 t=4000ms).
- TTL 10초: t=10.9초까지 **30건** 실패.
- 종료 전 해제(`graceful`): 0건.

### 9. 메시 설정 오류

- 볼 것: 무관한 서비스들의 오류가 같은 시각에 오르는지, 그 시각의 메시 설정 배포 이력, 프록시 로그(라우트 없음·인증서 검증 실패), `istioctl analyze`·`proxy-config`로 실제 받은 설정.
- 반경이 큰 이유: 컨트롤 플레인이 설정을 모든 프록시에 내려보낸다. 라우팅·mTLS 정책·기본 재시도 오류는 메시 전체에 퍼진다.
- 줄이는 법: 설정도 리뷰·정적 검사·단계적 배포(일부 네임스페이스·워크로드부터), 되돌리기 절차, 셀 단위로 메시를 나누기(51번).
