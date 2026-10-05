# data-structure/44-ds-incidents — 정답

## 정답

### 1. 깨진 가정과 진단의 어려움

- HashDoS: "키가 고르게 퍼진다"는 가정을 외부 공격자가 깬다. 같은 해시의 키를 대량으로 보내 버킷 하나에 몰아넣는다.
- JDK 7 `HashMap` 순환: "한 번에 한 스레드만 구조를 바꾼다"는 가정을 내부 코드가 깬다. 동기화 없는 동시 resize가 버킷을 순환시킨다.
- 진단의 어려움
  - 예외·로그가 없다. CPU 그래프와 지연만 보인다.
  - 평소 부하 테스트로는 재현되지 않는다. 공격 입력이나 드문 타이밍이 있어야 한다.
  - 그래서 덤프를 여러 장 떠서 "진행 중인가, 멈췄나"를 보는 것이 첫 진단이다([43-ds-symptom-index](../43-ds-symptom-index/2-summary.md) 2절).

### 2. n²과 증폭

- i번째 키를 넣을 때 앞의 i-1개와 비교한다. 총 0 + 1 + … + (n-1) = n(n-1)/2번, O(n²)이다.
- 공격자의 비용: 요청 하나(크기 ∝ n)와 미리 계산한 키 목록. `"Aa"`·`"BB"` 블록 조합처럼 계산도 싸다.
- 서버의 비용: n²에 비례하는 비교. advisory 원문은 "100% of CPU usage which can last up to several hours"라고 적고, 공격자 쪽은 "little bandwidth and time"이라고 적는다. 이 비대칭이 증폭이다.

### 3. advisory의 원인과 수정 판

- 원인 두 가지
  - 해시 쪽: 하위 해시 알고리즘의 예측 가능한 충돌(predictable collisions).
  - 웹 서버 쪽: POST 요청 파라미터 수에 충분한 제한이 없음.
- Java의 수정 판: "N/A"(영향 판 "all versions"). advisory 시점에 Java 자체 수정은 없었다. Tomcat(>= 7.0.23 등)·Jetty(>= 7.6.0.RC3)처럼 컨테이너 쪽 수정이 따로 표에 있다.
- Python 2.7.3·3.2.3 등: 수정 판이지만 "hash randomization disabled by default, use -R flag to enable it" — 기본으로 꺼져 있었다. 기본으로 켜진 것은 Python 3.3부터다(언어 레퍼런스 "Changed in version 3.3").

### 4. 두 갈래와 한계

- 해시를 예측 불가능하게
  - Python: 2.6.8/2.7.3/3.1.5/3.2.3에 `-R`(기본 꺼짐), 3.3에서 기본 켜짐, 3.4에서 PEP 456으로 `str`·`bytes` 기본 해시를 SipHash로(64비트 정수형이 없는 플랫폼 등은 FNV 유지). PEP 456의 이유: 기존 수정 FNV 해시와 그 랜덤화로는 비밀 시드를 뽑아낼 수 있다(Aumasson–Bernstein 시연). 3.11부터 기본 변형은 SipHash-1-3.
  - Java 7u6: 대체 해시 함수, 그러나 기본 임계값 -1(꺼짐), `jdk.map.althashing.threshold`로 켬.
  - 막지 못하는 경우: 시드가 새거나 고정된 경우(`PYTHONHASHSEED=0`). 시드를 뽑을 수 있는 약한 해시.
- 최악 비용을 줄이기
  - Java 8: JEP 180 — 긴 버킷을 균형 트리로, 최악 O(n) → O(log n). 7u6의 대체 문자열 해시는 제거.
  - 막지 못하는 경우: 키가 `Comparable`이 아니거나 `compareTo`가 0이면 트리가 찾을 방향을 못 정해 양쪽을 뒤지므로 사실상 선형(실험 A). O(log n)이어도 키 수 자체에 상한이 없으면 요청 하나의 비용은 계속 는다.
- 두 갈래 모두 입력 상한(Tomcat `maxParameterCount` 기본 10000 등)을 대신하지 않는다.

### 5. 실험 A의 수치

- n = 32,768(집필 두 번): 충돌 `String` 68 ms·51 ms, 충돌 비`Comparable` 32,101 ms·31,737 ms, 보통 키 13 ms·11 ms. 점검 재실행 두 번: 46·64 ms, 32,688·35,324 ms, 12·17 ms.
- 비`Comparable` 열: 8,192 → 16,384 → 32,768에서 두 배마다 약 5~6.6배(1,053 → 6,354 → 32,101, 두 번째 1,068 → 6,433 → 31,737, 점검 924 → 6,111 → 32,688과 1,050 → 6,438 → 35,324). 2,048 → 4,096 → 8,192는 실행마다 달랐다(집필 약 2배씩: 257 → 591 → 1,053, 279 → 541 → 1,068 / 점검: 66 → 193 → 924, 363 → 203 → 1,050).
- O(n²)이면 두 배마다 4배가 예상된다. 큰 n에서는 그보다 크다(캐시 미스 등 상수로 보임 — 해석, 따로 재지 않음). 작은 n의 값은 첫 측정의 JIT 워밍업이 섞여 흔들리므로(해석) 비율 판단에 쓰지 않는다 — 2,048 → 32,768(16배) 전체 배율도 집필 114~125배, 점검 97~495배로 크게 달랐다.
- 같은 해시인데 `String`은 수십 ms에 머문 것이 JEP 180 트리 버킷의 효과다.

### 6. 머리 삽입 순환

```text
  옛 버킷: A -> B -> null      (새 표에서 A, B 둘 다 같은 칸)
  T1: e = A, next = B  ← 읽고 선점
  T2: 끝까지 옮김 → 새 칸 B -> A -> null   (공유 객체: B.next = A, A.next = null)
  T1: A 를 머리에      → A -> null          (A.next = null)
      e = B, next = B.next = A               ← T2 가 바꾼 값
      B 를 머리에      → B -> A -> null      (B.next = A)
      e = A, next = A.next = null
      A 를 머리에      → A.next = B         → A -> B -> A -> B -> ...
```

- 실험 C가 보인 것: 이 실행 순서를 정해 놓고 재연하면 세 단계 만에 `A.next=B, B.next=A`가 되고, 없는 키 조회가 100만 칸 상한에서 멈춘다(결정적).
- 보이지 않은 것: 실제 스레드 경쟁에서 이 순서가 얼마나 자주 나는지, 실제 JDK 7에서의 재현. 이 환경엔 JDK 7 이미지가 없고 실제 경쟁은 재현하지 않았다. JDK-6423457 보고와 jdk7u 소스로 대신했다.

### 7. 덤프 세 장으로 가르기

- 2~5초 간격으로 `jcmd <pid> Thread.print`를 세 번.
- 같은 스레드의 맨 위 프레임이 세 장 모두 **같은 줄**(`HashMap.get` 루프, JDK 21이면 `HashMap$TreeNode.root`·`balanceInsertion` 등)이면 사건 2형(공유 맵 손상)이다.
  - 처방: 그 맵이 필드·static으로 공유되는지 찾아 `ConcurrentHashMap`이나 불변 맵으로 바꾼다. 멈춘 프로세스는 재시작해야 한다.
- 프레임이 `putVal`·`TreeNode.find`·`getNode` 사이에서 **바뀌며** 진행하고, 그 요청의 파라미터·키 수가 비정상적으로 많으면 사건 1형(HashDoS)이다.
  - 처방: 요청당 키 수·본문 크기 상한, 키 타입 확인(`Comparable`), 런타임 방어 유지.

### 8. JDK 8 이후의 공유 `HashMap`

- 안전하지 않다. JDK 8은 resize에서 순서를 보존해(`loHead`/`hiHead`, "preserve order") 머리 삽입 순환 경로만 없앴다.
- `HashMap` Javadoc(OpenJDK 21)은 여전히 "Note that this implementation is not synchronized."다.
- JDK 21 실험([29-concurrent-data-structures](../29-concurrent-data-structures/2-summary.md) 3절): 스레드 4개가 서로 다른 키 10만 개씩 넣었을 때, 집필 16번 중 14번은 `size()`가 기대보다 작았고(leaf 전체 범위 15만~34만, 기대 40만 — 키를 다시 센 점검에서도 실제로 사라졌다) 2번은 10초 안에 끝나지 않았다(점검 8번 중 1번도 멈춤)(`HashMap$TreeNode.root`·`putTreeVal`, 또는 `balanceInsertion` ← `treeify` ← `split`).

### 9. `PYTHONHASHSEED=0`

- 실험 B(CPython 3.12.14): 기본 설정에서는 `hash("Aa")`가 세 프로세스에서 모두 달랐다(5457046695198189700, 2645493569435583083, 6210981154125699700). `PYTHONHASHSEED=0`이면 두 번 다 -3747738680037904767로 같았다.
- 끄는 것: 해시 랜덤화. 해시가 프로세스 밖에서 예측 가능해져 HashDoS 갈래 (가)의 방어가 사라진다.
- 원래 이유와 대체
  - 재현 가능한 테스트(같은 순회 순서): 해시 순서에 기대지 말고 결과를 정렬한다. 시드 고정은 테스트 환경에서만 한다.
  - 여러 프로세스가 같은 해시 값을 공유: 내장 `hash()` 대신 명시적인 해시(예: `hashlib`나 키 있는 해시를 직접 지정)를 저장·전송 계약으로 쓴다.
