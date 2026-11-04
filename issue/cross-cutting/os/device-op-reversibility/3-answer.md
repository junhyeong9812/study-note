# issue/cross-cutting/os/device-op-reversibility — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **드라이버를 내리면 장치가 더 깊은 절전 상태로 갈 수 있고, 다시 올릴 때 그 상태에서 깨우는 데 실패하면 장치를 쓸 수 없게 된다.**\
   PCI 장치의 전원 상태는 D0(동작)부터 D3hot·D3cold(전원 차단)까지 있다 — 드라이버가 없으면 커널·플랫폼이 장치를 더 깊은 상태로 내릴 수 있다(일반론).\
   이 사례에서 재로드한 드라이버는 장치를 D3cold에서 D0로 올리지 못했고 probe가 입출력 오류로 끝났다 — 재로드 전에는 링크만 없던 장치가, 뒤에는 드라이버가 붙지 않은 장치가 됐다.\
   그래서 드라이버 재로드는 "다시 시도"가 아니라 장치 상태를 바꾸는 조작이다 — 처음의 링크 없음 원인은 끝내 확인하지 못했다.
   > **D3cold** — PCI 전원 관리에서 장치 전원이 끊긴 상태. 돌아오려면 위쪽 브리지·플랫폼이 전원을 다시 넣고 장치를 다시 초기화해야 한다.

2. **위쪽 포트가 절전 중이면 그 아래는 훑어도 보이지 않을 수 있고, 깨운 뒤에도 장치가 응답하지 않으면 콜드 부팅만 남는다.**\
   PCI `remove`는 커널이 그 장치를 잊게 하고(드라이버 분리 · 장치 객체 삭제), `rescan`은 버스를 다시 훑어 응답하는 장치만 다시 만든다.\
   이 사례는 remove 뒤 장치가 PCI 목록에서 사라졌고, 위쪽 PCIe 포트가 runtime suspended였다 — 포트의 `power/control`을 `on`으로 바꾸고 다시 훑고 포트를 reset하자 포트는 정상이 됐지만 NIC는 여전히 응답하지 않았다.\
   남은 수단은 완전 종료 뒤 재기동이었다 — 재부팅 직후 링크가 1Gbps로 올라왔고, 포트의 `power/control`은 기본값(`auto`)으로 돌아와 있었다.\
   "포트가 절전이라 rescan이 못 찾았다"는 순서상의 해석이고, 장치가 응답하지 않은 정확한 기전은 확인하지 않았다(추정).
   > **runtime PM** — 리눅스가 쓰지 않는 장치·포트를 실행 중에 절전시키는 기능. `power/control`이 `auto`면 허용, `on`이면 늘 켜 둔다.

3. **읽기는 상태를 바꾸지 않고, 조작은 바꾼다 — 읽기로 원인 층을 먼저 좁힌다.**\
   읽기: `ip link`(carrier 유무) · `ethtool <if>`(속도·협상·광고 모드·링크 감지) · 커널 로그(링크 Up/Down·드라이버 오류 시각) · `/sys/.../power/runtime_status`(절전 여부) — 모두 되돌릴 것이 없다.\
   조작은 아래로 갈수록 되돌리기 어렵다: 링크 재협상(`ethtool -r`) → 드라이버 재로드 → PCI remove·rescan → 재부팅.\
   이 사례는 읽기로 "케이블을 다시 꽂아도 carrier 0"까지 본 뒤 곧바로 셋째·넷째 단계로 갔다 — 둘째 단계와 전원 상태 읽기를 건너뛰었다.

4. **같은 호스트에서 무엇이 돌고 있는지, 그 조작이 무엇을 끊을 수 있는지를 먼저 말하고 확인을 받아야 했다.**\
   그 호스트에는 다른 실험의 컨테이너 9개가 돌고 있었고 부하 평균이 7~18이었다 — 그런데 드라이버 언로드·PCI 제거를 위험 설명 없이 권했고, 다른 실험 중인 프로세스의 종료까지 권했다(사용자가 지적).\
   공유 호스트의 장치·전원 조작은 내 작업만이 아니라 남의 작업도 건다 — 권하기 전에 ① 돌고 있는 작업 ② 그 조작의 최악 결과(장치 소실 · 재부팅 필요) ③ 되돌리는 방법을 함께 말하고, 확인 뒤에 한다.\
   지적 뒤에는 아무것도 끄지 않았고, 다른 실험이 끝난 뒤 사용자가 한 재부팅으로 복구했다.

5. **그 NIC가 유일한 경로였다면 조작한 순간 호스트에 다시 들어갈 길이 없어진다 — 되돌림 경로는 조작 전에 있어야 한다.**\
   이 사례는 로컬 PC라 무선으로 우회했고 사람이 전원을 다시 넣을 수 있었다.\
   원격 서버라면 같은 조작은 원격 콘솔(BMC·IPMI 등)이나 다른 링크가 없는 한 현장 방문이 된다 — 조작 전에 대체 접속 경로와 "실패하면 무엇으로 되돌리나"를 정해 둔다(일반론).

## 문제 구조 (추상화 코드)

### 변형 A — 읽기 단계를 건너뛰고 상태를 바꾸는 조작으로 감
① 문제 흐름
```sh
ip link show $IF                     # NO-CARRIER
# (케이블 재연결) → 여전히 carrier 0
modprobe -r $DRIVER && modprobe $DRIVER          # → "D3cold → D0 실패" · probe 오류
echo 1 > /sys/bus/pci/devices/$BDF/remove        # → 장치가 목록에서 사라짐
echo 1 > /sys/bus/pci/rescan                     # → 찾지 못함 (위쪽 포트 runtime suspended)
echo on > /sys/bus/pci/devices/$PORT/power/control; echo 1 > /sys/bus/pci/rescan   # → 포트 정상 · NIC 무응답
# → 다른 실험이 끝난 뒤 완전 종료·재기동으로 복구
```
② 고친 흐름
```sh
# 1. 읽기만: 원인 층 좁히기
ip link show $IF; ethtool $IF; journalctl -k --since -2h | grep -i "$IF\|$DRIVER"
cat /sys/bus/pci/devices/$BDF/power/runtime_status /sys/bus/pci/devices/$PORT/power/runtime_status
# 2. 공유 호스트 점검 + 위험 고지 + 확인
docker ps; uptime                     # 다른 작업 · 부하
confirm "다음 조작은 장치를 재부팅 전까지 잃을 수 있다 — 지금 돌고 있는 작업: …"
# 3. 되돌리기 쉬운 것부터 하나씩, 매 단계 결과를 읽고 멈출지 정한다
ethtool -r $IF                        # 재협상
# 드라이버 재로드·PCI remove는 재부팅이 허용될 때만
```
무엇이 깨졌나: 증상을 고치려는 조작이 되돌리기 어려운 순서로, 위험 설명과 다른 작업 확인 없이 진행됐다.

## 검증 기록
- 2026-11-04: 사건 기록 대조·추상화(Claude 초안) — 조작 순서·결과(D0 전환 실패 · PCI 목록에서 사라짐 · 포트 runtime suspended · 재부팅 뒤 복구)는 기록 그대로, 전원 상태·runtime PM 설명과 원격 콘솔 대비는 일반론, 처음 NO-CARRIER의 원인과 rescan 실패의 정확한 기전은 확인하지 않음.

## 관련 카드
- [job-lifetime-bound-to-user-session](../job-lifetime-bound-to-user-session/) — 공유 호스트에서 내 조작이 다른 작업의 수명에 닿는 다른 경로(cgroup·사용자 세션).
- [performance-measurement-validity](../../testing/performance-measurement-validity/) — 같은 링크 문제가 측정에 섞인 쪽(비교 9 — 생성기 링크).
