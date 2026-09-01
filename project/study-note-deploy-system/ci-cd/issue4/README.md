# issue4 — Claude 브리지: 서브넷을 못 넘어서, 역방향으로 넘다

- (도구) deploy-study-note/tools/claude-bridge · backend PR #28·#29

## 1. 배경

에스컬레이션(모르는 질문을 Claude에게)은 PC의 `claude -p`(구독)를 쓰기로 했다(⑤ⓑ).
문제는 연결 방향.

## 2. 문제 — 홈랩이 PC에 도달 못 함

**상황**: backend(.158, `192.168.55.x`)가 PC(`192.168.45.29`)의 브리지를 호출해야 함.

**문제**:
```
$ ssh …158  'ping -c1 192.168.45.29'   →  unreachable
   ip route: default via 192.168.55.1   (45.x로 가는 경로 없음)
```
두 대역이 다른 세그먼트 — 홈랩→PC 직접 경로가 없다.

**접근**: 방향을 뒤집는다. PC→홈랩은 이미 뚫려 있다(배포 ssh가 그 경로). 그래서
**역방향 노출**:
```
backend → socat(.158:15100) → 역 SSH 터널(PC가 -R로 걺) → PC:15100 브리지 → claude -p
```
- 역터널: `ssh -N -R 15101:localhost:15100 jun@.158` (PC 루프백을 .158 루프백으로)
- socat 컨테이너: `.158:0.0.0.0:15100 → 127.0.0.1:15101` (backend가 LAN으로 닿게, sudo 불요)

## 3. 구현 중 마주친 문제 — dubious ownership의 사촌 격, "성공인데 빈 응답"

byte 본문 문제(backend issue12)와 socat 이미지 pull 누락(첫 시도 "Unable to find image"
→ `docker pull alpine/socat` 선행)을 거쳐 관통.

## 4. 리뷰 반영 — 인증 없는 원격 실행은 위험 (codex F2~F8)

리뷰가 정확히 짚었다: 이대로면 relay 포트에 닿는 누구나 PC의 Claude를 임의 실행한다.
채택 강화:
- **인증**: `X-Bridge-Secret` 공유 시크릿 상수시간 검증, 빈 시크릿이면 전부 거절(F2)
- **동시 1건**: 세마포어 — 느린 요청 하나가 전체를 점유하지 못하게, 초과는 503(F4)
- **상한**: 프롬프트 60KB·출력 20KB·Content-Length 범위 검증·chunked 거부(F6·F7)
- **프롬프트 주입 완화**: `claude -p --allowedTools ""` — 문서에 "파일 읽어라" 같은
  지시가 있어도 도구를 못 써서 텍스트 답만(F3)
- **stderr 비노출**(F8)

검증: 무인증 401·인증 200, 엣지 에스컬레이션 재관통("SSTable은 …").

## 5. 결론

서브넷 격리는 "방향을 뒤집어" 풀고, 원격 실행 표면은 인증·상한·도구차단으로 좁혔다.
브리지는 세션 프로세스라 상시 운용은 PC에서 스크립트 기동(README). backend PR #28·#29
