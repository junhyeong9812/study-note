# infra — 플랫폼·툴·배포

배포·빌드·컨테이너·버전 관리 도구에서 반복되는 패턴이다.\
공통 원리: **도구는 이름에서 떠올리는 직관과 다른 암묵 입력(파싱 채널·소유 uid·인덱스·전이 의존)을 쓴다** — 값이 어느 채널로 누구에게 도달하는지 확인한다.

## 공통 원리

```
  설정·코드 ──▶ 도구의 암묵 입력 ──▶ 실제 동작
                   │
                   ├─ 변수: 파싱 시점 vs 런타임 채널
                   ├─ 권한: 실제로 여는 주체(uid·그룹)
                   ├─ 상태: 삭제가 사본에 전파되지 않음
                   └─ 버전: 선언 ≠ 실제 런타임 호환
                                   ▼
                  "설정했는데 안 먹는다" / 조용한 드리프트
```

## 패턴 카드

- [bottleneck-identification](bottleneck-identification/) — 처리량 설정(병렬도·스레드풀·힙)은 실제 병목(디스크 IOPS·코어·요청 지연)에 상대적이다 — 병목을 실측하지 않고 늘리거나 이식하면 경합·기동 실패가 난다.
- [compose-variable-resolution-timing](compose-variable-resolution-timing/) — compose의 변수·설정은 파싱 채널과 런타임 채널, 명령별 로드 범위가 다르다 — 값이 어느 채널로 누구에게 도달하는지 확인해야 한다.
- [dependency-and-toolchain-compat](dependency-and-toolchain-compat/) — 의존성·툴체인은 선언·버전·런타임 호환(JDK·Node·Docker API·shade·peer deps·전이 의존)이 맞아야 동작한다 — 게시된 메타데이터·실제 해석 트리·대상 런타임으로 확인한다.
- [effective-uid-file-access](effective-uid-file-access/) — 파일 접근 권한은 실제로 여는 주체(컨테이너 uid·리다이렉트를 여는 셸·기동 시 확정된 보조 그룹)의 것이다 — "존재"가 아니라 그 주체의 읽기·쓰기 가능성으로 판단한다.
- [firewall-and-network-policy-layers](firewall-and-network-policy-layers/) — 패킷 필터·MAC·클라우드 보안목록·Docker 체인은 계층마다 따로 동작한다 — 한 계층(ufw)의 설정이 다른 계층(Docker publish·SELinux)을 보장하지 않는다.
- [git-pitfalls](git-pitfalls/) — git은 인덱스·ref·시퀀서 상태·출력 인용·소유권·ignore 규칙을 암묵 입력으로 쓰므로, 이름에서 떠올리는 직관과 실제 정의가 다른 지점을 명시적으로 다뤄야 한다.
- [llm-serving-vram-and-backend](llm-serving-vram-and-backend/) — LLM 서빙은 VRAM 예산(가중치+KV cache×동시 시퀀스)과 GPU 아키텍처별 백엔드 지원이 결정한다 — 기동 성공은 추론 성공을 보장하지 않는다.
- [nginx-broadband-defense-friendly-fire](nginx-broadband-defense-friendly-fire/) — 출처를 구분하지 않는 광역 방어(UA 차단·단일 버킷 레이트리밋)는 자기 자동화·검증 트래픽·정상 사용자를 오사한다 — allowlist·정확한 키로 범위를 좁힌다.
- [path-derived-key-on-move](path-derived-key-on-move/) — 가변 속성(절대 경로)에서 파생한 키·캐시는 폴더 이동 순간 고아가 된다 — 이동은 키 재계산·캐시 무효화를 동반해야 한다.
- [state-drift-delete-propagation](state-drift-delete-propagation/) — 같은 사실의 사본(설정·배포본·파생 상태·인덱스)은 삭제·변경이 전파되지 않으면 원본과 어긋난다 — 정본 단일 채널과 명시적 삭제(tombstone)로 수렴시킨다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(2) · `least-privilege`(2) · `environment-drift`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
