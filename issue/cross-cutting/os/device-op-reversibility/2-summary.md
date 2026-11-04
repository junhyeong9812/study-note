# issue/cross-cutting/os/device-op-reversibility — 정리 (힌트)

## 전체 흐름

```text
증상: 유선 NIC NO-CARRIER (그날 앞서 두 번 끊김) · 케이블 재연결 뒤에도 carrier 0
      트래픽은 무선으로 우회 · 같은 호스트에서 다른 실험 컨테이너 9개 · load 7~18

조작 사다리 (아래로 갈수록 되돌리기 어렵다)
  ① 읽기      ip link · ethtool · dmesg/journalctl -k · /sys/.../power/{control,runtime_status}
  ② 링크 재협상  ethtool -r <if>                      (보통 되돌릴 필요 없음 — 권한 필요)
  ③ 드라이버 재로드  modprobe -r → modprobe            ← 실제로 함: "D3cold → D0 실패 · probe 오류"
  ④ PCI 제거·재탐색  echo 1 > …/remove ; echo 1 > /sys/bus/pci/rescan
                                                     ← 실제로 함: 장치가 PCI 목록에서 사라짐
     위쪽 포트 runtime suspended 확인 → power/control=on · rescan · 포트 reset
     → 포트는 정상 · NIC는 응답 없음
  ⑤ 완전 종료 뒤 재기동(콜드 부팅)                       ← 복구 (다른 실험이 끝난 뒤)
     → 부팅 직후 1Gbps Up · 포트 power/control은 기본값 auto로 돌아옴

교훈: ③④는 "다시 시도"가 아니라 장치를 잃을 수 있는 조작 — 위험·영향을 먼저 말하고, 다른 작업을 확인하고, 되돌림 경로를 확보한 뒤
```

## 핵심 문장

- 장치 조작은 되돌릴 수 있는 정도가 다르다 — 읽기 → 재협상 → 드라이버 재로드 → PCI 제거 → 재부팅 순으로 잃을 수 있는 것이 커진다.
- 전원 관리 중인 장치(D3cold)는 드라이버를 내리고 올리는 동안 다시 깨어나지 못할 수 있다 — 재로드는 "새로 고침"이 아니다.
- PCI 제거는 커널이 그 장치를 잊게 한다 — 다시 찾는 것은 위쪽 포트·전원 상태에 달렸고, 못 찾으면 콜드 부팅만 남는다.
- 공유 호스트의 장치·전원 조작은 다른 사람의 작업을 함께 건다 — 권하기 전에 위험과 영향을 먼저 말하고 확인을 받는다.
- 원격이면 그 NIC가 유일한 접속 경로인지 먼저 본다 — 조작 전에 다른 경로(콘솔·다른 링크)를 확보한다.
