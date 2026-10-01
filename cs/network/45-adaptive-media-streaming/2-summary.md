# network/45-adaptive-media-streaming — HLS·DASH: 세그먼트·매니페스트·적응형 비트레이트(ABR) — 정리 (힌트)

## 해결하는 문제

영상 파일 하나를 통째로 내려받아 재생하면 세 가지가 안 된다.

```text
  1. 망 속도가 바뀌면 대응 못 함      -> 느려지면 멈추고(리버퍼링), 빨라져도 화질 그대로
  2. 생방송을 못 함                  -> 파일이 아직 끝나지 않았다
  3. CDN에 잘 안 맞음                -> 거대한 파일 하나보다 작은 조각이 캐시·재시도에 유리
```

적응형 스트리밍은 영상을 **몇 초짜리 조각(세그먼트)** 으로 자르고, 같은 내용을 **여러 화질로** 미리 인코딩해 둔다.\
그리고 조각 목록(**매니페스트**)을 준다.\
플레이어는 조각을 하나씩 평범한 HTTP GET으로 받는다. 받을 때마다 망 상태를 보고 다음 조각의 화질을 고른다.

쉬운 예: 택배를 한 트럭에 몰아 보내지 않고 작은 상자로 나눠 보낸다.\
길이 막히면 다음 상자는 가벼운 것으로 보낸다.\
받는 사람은 "도착 예정 목록"을 보고 어느 상자가 다음인지 안다.

똑같은 구조다.\
세그먼트 = 작은 상자, 매니페스트 = 도착 예정 목록, ABR = 다음 상자의 무게를 고르는 규칙.

실무 예:
- 동영상 강의·OTT의 VOD 재생.
- 스포츠 생중계. 매니페스트가 몇 초마다 갱신된다.
- 둘 다 대부분 CDN(47번)을 거쳐 전달된다.

  - *HLS(HTTP Live Streaming)*: Apple이 만든 방식이다. 매니페스트는 `.m3u8` 텍스트 재생목록이다(RFC 8216, Informational).
  - *DASH(Dynamic Adaptive Streaming over HTTP)*: MPEG 표준(ISO/IEC 23009-1)이다. 매니페스트는 XML인 MPD다.

## 동작·원리

### 1. 전체 구조 — 매니페스트 2단 + 세그먼트

```text
  master.m3u8 (마스터 재생목록: 화질 목록)
    |-- BANDWIDTH=1280000  -> low.m3u8  (미디어 재생목록) -> seg100.ts, seg101.ts, ...
    |-- BANDWIDTH=2560000  -> mid.m3u8                     -> seg100.ts, seg101.ts, ...
    +-- BANDWIDTH=7680000  -> hi.m3u8                      -> seg100.ts, seg101.ts, ...

  플레이어:  master 1회 -> 화질 하나 고름 -> 그 미디어 재생목록 -> 세그먼트 GET 반복
                                  ^                                  |
                                  +---- 다운로드 속도·버퍼 보고 전환 ----+
```

RFC 8216 §8.4의 마스터 재생목록 예(원문의 오디오 전용 변형 한 줄은 생략):

```text
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1280000,AVERAGE-BANDWIDTH=1000000
http://example.com/low.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2560000,AVERAGE-BANDWIDTH=2000000
http://example.com/mid.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=7680000,AVERAGE-BANDWIDTH=6000000
http://example.com/hi.m3u8
```

- `BANDWIDTH`는 그 변형(variant)의 **최대(peak) 세그먼트 비트레이트**(bps)다. 모든 `EXT-X-STREAM-INF`에 있어야 한다(MUST, §4.3.4.2).
  - 세그먼트가 모두 만들어졌다면, 재생 가능한 렌디션 조합(비디오+별도 오디오 등)의 peak 합 중 최댓값이어야 한다(MUST).
  - 라이브처럼 인코딩이 끝나기 전에 공개하면, 같은 설정으로 인코딩한 비슷한 콘텐츠의 대표 구간 값을 쓴다(SHOULD).
  - 값이 틀리면 재생이 멈추거나 그 변형을 못 틀 수 있다고 RFC가 적는다.
- `AVERAGE-BANDWIDTH`는 평균 세그먼트 비트레이트다.

  - *변형 스트림(variant stream)*: 같은 내용을 다른 비트레이트·해상도로 인코딩한 판이다. DASH에서는 Representation이라 부른다.

### 2. 미디어 재생목록 — VOD와 라이브

VOD(RFC 8216 §8.1):

```text
#EXTM3U
#EXT-X-TARGETDURATION:10
#EXT-X-VERSION:3
#EXTINF:9.009,
http://media.example.com/first.ts
#EXTINF:9.009,
http://media.example.com/second.ts
#EXTINF:3.003,
http://media.example.com/third.ts
#EXT-X-ENDLIST                 <- 더 추가되지 않음
```

라이브(§8.2) — `ENDLIST`가 없고, 앞에서 빠지고 뒤에 붙는다.

```text
  시각 t    : MEDIA-SEQUENCE:2680  [2680][2681][2682]
  시각 t+8s : MEDIA-SEQUENCE:2681        [2681][2682][2683]     <- 창이 앞으로 민다
```

- `EXT-X-TARGETDURATION`은 **최대 세그먼트 길이**(정수 초)다. 각 `EXTINF`를 반올림한 값이 이보다 크면 안 된다(MUST, §4.3.3.1).
- 세그먼트를 빼면 `EXT-X-MEDIA-SEQUENCE`를 하나씩 올려야 한다(MUST, §6.2.2).
- `ENDLIST`가 없는 재생목록에서, 서버는 전체 길이가 **목표 길이의 3배 미만**이 되도록 세그먼트를 빼면 안 된다(MUST NOT, §6.2.2).
- 뺀 세그먼트도 "세그먼트 길이 + 그 세그먼트가 든 가장 긴 재생목록 길이"만큼은 계속 받을 수 있어야 한다(MUST, §6.2.2).

### 3. 재생목록 갱신 규칙 — 라이브 지연의 뿌리

```text
  플레이어                                      서버/CDN
  GET live.m3u8  ----------------------------->
                 <--- 새 세그먼트 있음(변경됨)
  (목표 길이 TD만큼 기다림)
  GET live.m3u8  ----------------------------->
                 <--- 변경 없음
  (TD/2 기다림)
  GET live.m3u8  ----------------------------->
```

- 처음 받았거나 바뀌었으면, 다음 갱신까지 **최소 목표 길이만큼** 기다려야 한다(MUST, §6.3.4).
- 바뀌지 않았으면 **목표 길이의 절반** 뒤에 다시 시도해야 한다(MUST).
- 라이브 시작점: `ENDLIST`가 없으면, 재생목록 끝에서 **목표 길이 3개 미만** 떨어진 세그먼트에서 시작하지 않는 것이 좋다(SHOULD NOT, §6.3.3).
  - 그래서 목표 길이 6초(예시)면, 시작부터 끝에서 18초 이상 뒤처져 재생한다. 여기에 인코딩·패키징·CDN 지연이 더해진다.

### 4. DASH의 MPD — 같은 개념, XML 계층

```text
  MPD (type="dynamic": 세그먼트가 시간에 따라 생김(라이브) / "static": 주로 VOD)
   +-- Period                       (시간 구간: 본편, 광고 ...)
        +-- AdaptationSet            (같은 종류의 트랙: 비디오 / 오디오 / 자막)
             +-- Representation      (한 화질: bandwidth, width, height, codecs)
                  +-- SegmentBase / SegmentList / SegmentTemplate   (세그먼트 위치)
```

- HLS의 변형 스트림 ≈ DASH의 Representation이다.
- 라이브 MPD는 `MPD@minimumUpdatePeriod`로 "이 스냅숏이 유효한 기간"을 알려 갱신 주기를 정한다(DASH-IF IOP).
- 브라우저에서 DASH를 재생하려면 dash.js 같은 JS 플레이어와 **Media Source Extensions(MSE)** 지원이 필요하다(MDN).
  - *MSE*: JS가 받은 미디어 바이트를 `<video>`에 조각조각 넣을 수 있게 하는 브라우저 API다.

### 5. 세그먼트 — 전환이 가능하려면

```text
  low :  [IDR ...... ][IDR ...... ][IDR ...... ]
  mid :  [IDR ...... ][IDR ...... ][IDR ...... ]   <- 경계·타임스탬프가 맞아야
  hi  :  [IDR ...... ][IDR ...... ][IDR ...... ]      중간에 갈아탈 수 있다
                      ^ 여기서 low -> hi 전환
```

- 비디오 세그먼트는 디코더를 초기화할 정보를 담는 것이 좋다. H.264라면 세그먼트에 IDR 프레임이 있어야 한다(SHOULD, §3).
  - *IDR 프레임*: 앞 프레임을 참조하지 않고 혼자 디코딩되는 프레임이다. 여기서부터 재생을 새로 시작할 수 있다.
- 변형끼리 같은 내용은 **타임스탬프가 일치**해야 하고, 모든 변형의 목표 길이가 같아야 한다(MUST, §6.2.4).
- 세그먼트 형식은 MPEG-2 TS나 fragmented MP4 등이다(§3.1).
- 저지연 HLS(부분 세그먼트 `EXT-X-PART`, 블로킹 재생목록 갱신)는 RFC 8216의 후속 초안 `draft-pantos-hls-rfc8216bis`에 있다. 아직 RFC가 아니다.

### 6. ABR — 다음 세그먼트의 화질을 고르는 규칙

```text
     다운로드 완료 -> 처리량 샘플 = 바이트 × 8 / 걸린 시간
                         |
                   EWMA로 평활  ---> 추정 처리량 B
                         |
     버퍼 수준 b (재생 대기 중인 초)
                         |
     선택: B × 안전계수 보다 낮은 최고 화질   (처리량 기반)
           b가 낮으면 낮은 화질, 높으면 높은 화질 (버퍼 기반)
```

두 계열이 있다.

- **처리량 기반**: 최근 다운로드 속도를 평균 내서 "감당할 수 있는 최고 화질"을 고른다.
  - Shaka Player는 반감기가 다른 **EWMA 두 개**(빠른 것 2초, 느린 것 5초)의 **최솟값**을 추정치로 쓴다. 코드 주석은 이를 "내려갈 때는 빨리, 올라갈 때는 천천히"라고 설명한다.
  - *EWMA(지수 가중 이동 평균)*: 새 샘플에 가중치 α, 이전 평균에 1−α를 곱해 더한다. 오래된 샘플의 영향이 지수적으로 줄어든다.
- **버퍼 기반**: 버퍼에 쌓인 재생 시간으로 화질을 정한다.
  - Huang 외(SIGCOMM 2014, Netflix)는 정상 상태에서는 용량 추정이 필요 없고, **시작 구간**에서만 직전 처리량 기반 추정이 중요하다고 보고했다. 버퍼 기반 방식이 당시 Netflix 기본 ABR 대비 리버퍼링을 10~20% 줄였다고 한다.
- dash.js는 기본으로 처리량 규칙(`ThroughputRule`)과 버퍼 기반 규칙(`BolaRule`)을 함께 켜고, 버퍼 수준에 따라 둘 사이를 동적으로 바꾼다(dash.js 문서).

## 쓰이는 자료구조·알고리즘

- **EWMA(지수 가중 이동 평균)** — 처리량 추정의 평활. 상수 메모리로 최근 값에 무게를 준다. TCP RTO의 SRTT 계산과 같은 형태다.
- **이중 EWMA의 최솟값** — 빠른 평균은 급락을 빨리 잡고, 느린 평균은 일시적 급등을 무시한다. 둘 중 작은 값을 쓰면 비대칭(빠른 하향, 느린 상향)이 된다.
- **버퍼 수준 → 비트레이트 사상(rate map)** — 버퍼가 적으면 최저, 많으면 최고, 그 사이는 단조 증가 함수로 고른다(버퍼 기반 제어). BOLA는 이를 효용 최적화로 푼다.
- **히스테리시스** — 올릴 때와 내릴 때의 문턱을 다르게 둔다. 문턱 근처에서 화질이 오르내리는 진동을 막는다.
- **슬라이딩 윈도 재생목록** — 라이브 재생목록은 앞에서 빼고 뒤에 붙이는 큐다. 시퀀스 번호가 단조 증가해 위치 추적 키가 된다. [04-queue-deque](../../data-structure/04-queue-deque/2-summary.md) 참고.
- **CDN 계층 캐시** — 인기 세그먼트는 엣지에, 원점 요청은 상위 계층으로 모은다([47-cdn-and-edge](../47-cdn-and-edge/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 설계 순서

```text
  1. 세그먼트 길이 정하기   짧게: 지연↓·전환 빠름 / 길게: 요청 수↓·압축 효율↑
  2. 키프레임 간격 맞추기   세그먼트 경계마다 IDR (인코더 GOP = 세그먼트 길이의 약수)
  3. 화질 사다리 정하기     예시: 360p 0.8M / 720p 2.5M / 1080p 6M
  4. 캐시 정책 정하기       세그먼트: 오래(불변 URL) / 라이브 재생목록: 짧게
  5. 플레이어 ABR 확인      시작 화질·안전계수·전환 간격
```

### 2. 캐시 헤더를 역할별로 나눈다

```text
  대상                   변하나?                 캐시 정책(예시)
  VOD 세그먼트           안 변함(URL이 곧 버전)    Cache-Control: max-age=31536000, immutable
  VOD 재생목록           안 변함                   길게
  라이브 세그먼트         안 변함                   길게 (창에서 빠진 뒤에도 잠시 남아 있게)
  라이브 미디어 재생목록   목표 길이마다 변함         목표 길이보다 짧게 (예: TD의 절반 이하)
  마스터 재생목록         드물게                    짧게~중간
```

- 라이브 재생목록의 TTL이 목표 길이보다 길면, CDN이 옛 목록을 주는 동안 플레이어는 새 세그먼트를 모른다. 그 사이 버퍼가 줄어든다.
- 세그먼트를 창에서 뺄 계획이면 서버는 HTTP 응답에 계획된 수명을 반영한 `Expires`를 두는 것이 좋다(SHOULD, RFC 8216 §6.2.2).

### 3. 전달 경로를 진단한다

```bash
# 재생목록 캐시 상태: Age가 목표 길이보다 크면 옛 목록이다
curl -s -D - -o /dev/null https://cdn.example.com/live/hi.m3u8 \
  | grep -i -E '^(cache-control|age|x-cache|cf-cache-status)'

# 세그먼트 다운로드 시간 vs 세그먼트 길이(예: 6초)
curl -s -o /dev/null -w 'ttfb=%{time_starttransfer}s total=%{time_total}s size=%{size_download}\n' \
  https://cdn.example.com/live/seg2681.ts
#   total이 세그먼트 길이에 가까우면 그 화질은 이 경로에서 지속 불가

# 재생목록 갱신 추적: 시퀀스 번호가 목표 길이마다 오르는가
while true; do date +%T; curl -s https://cdn.example.com/live/hi.m3u8 | grep MEDIA-SEQUENCE; sleep 2; done
```

### 4. ABR 뼈대를 코드로

처리량 EWMA와 버퍼 문턱을 섞은 최소 예다(TypeScript, 개념 설명용).

```ts
type Variant = { bandwidth: number; uri: string };   // bps, 오름차순 정렬

class Ewma {
  private est = 0; private totalWeight = 0;
  constructor(private halfLifeSec: number) {}
  sample(durationSec: number, bps: number) {
    const alpha = Math.pow(0.5, durationSec / this.halfLifeSec);
    this.est = alpha * this.est + (1 - alpha) * bps;
    this.totalWeight += durationSec;
  }
  get value() { // 초기 편향 보정
    const zeroFactor = 1 - Math.pow(0.5, this.totalWeight / this.halfLifeSec);
    return zeroFactor > 0 ? this.est / zeroFactor : 0;
  }
}

const fast = new Ewma(2), slow = new Ewma(5);

function onSegmentDownloaded(bytes: number, seconds: number) {
  const bps = (bytes * 8) / seconds;
  fast.sample(seconds, bps);
  slow.sample(seconds, bps);
}

function chooseVariant(variants: Variant[], bufferSec: number, current: Variant): Variant {
  const estimate = Math.min(fast.value, slow.value);   // 빠른 하향, 느린 상향
  const safety = 0.8;                                  // 안전계수(예시)
  if (bufferSec < 5) return variants[0];               // 버퍼 위험 -> 최저 화질(예시 문턱)
  let pick = variants[0];
  for (const v of variants) if (v.bandwidth <= estimate * safety) pick = v;
  // 히스테리시스: 올릴 때는 버퍼가 충분할 때만
  if (pick.bandwidth > current.bandwidth && bufferSec < 15) return current;
  return pick;
}
```

- 반감기 2초·5초와 최솟값 규칙은 Shaka Player `EwmaBandwidthEstimator`를 따랐다. 문턱 5초·15초와 안전계수 0.8은 예시다.
- 실무에서는 직접 짜기보다 hls.js·dash.js·Shaka Player의 ABR 설정을 조정한다.

## 장애 시나리오와 대처

### 1. 세그먼트 캐시 미스 → 리버퍼링

- **현상**: 생중계 시작 직후나 인기 VOD 공개 직후 "로딩 중" 동그라미가 자주 뜬다.
- **보이는 형태**
  - 플레이어 지표: rebuffer 횟수·시간 증가.
  - CDN 지표: 세그먼트 요청이 미스(Cloudflare `cf-cache-status: MISS`, CloudFront 로그 `x-edge-result-type`=`Miss`), 원점 응답 지연 증가.
  - 세그먼트 다운로드 시간(`time_total`)이 세그먼트 길이에 가깝거나 넘는다.
- **원인**
  - 새 세그먼트가 나오는 순간, 모든 엣지에서 동시에 원점으로 요청이 몰린다.
  - 원점이 느려지면 다운로드 시간이 재생 시간보다 길어진다. 버퍼가 줄어 0이 된다.
- **대처**
  - 계층 캐시·원점 방패(origin shield)로 원점 요청을 한 곳으로 모은다([47-cdn-and-edge](../47-cdn-and-edge/2-summary.md)).
  - 같은 객체의 동시 미스를 하나로 합치는 요청 병합(request collapsing)을 켠다. CloudFront Origin Shield는 같은 객체 요청을 합쳐 원점 요청을 줄인다(AWS 문서).
  - 세그먼트 URL을 불변으로 두고 캐시 기간을 길게 둔다.

### 2. 매니페스트 TTL 과다 → 라이브 지연 증가

- **현상**: 생중계가 TV보다 수십 초 늦다. 가끔 멈췄다가 몇 초를 건너뛴다.
- **보이는 형태**
  - 재생목록 응답의 `Age`가 목표 길이보다 크다.
  - 여러 번 받아도 `EXT-X-MEDIA-SEQUENCE`가 한동안 그대로다.
- **원인**
  - CDN이 라이브 재생목록을 목표 길이보다 오래 캐시한다.
  - 플레이어는 "변경 없음"을 보고 TD/2씩 기다리며 재시도한다(RFC 8216 §6.3.4). 그 사이 라이브 끝에서 점점 멀어진다.
  - 창에서 이미 빠진 세그먼트를 가리키는 옛 목록이면 404까지 난다.
- **대처**
  - 라이브 미디어 재생목록의 TTL을 목표 길이보다 짧게 둔다. 세그먼트 TTL과 분리한다.
  - 원점이 `Cache-Control`을 역할별로 내보내게 한다. CDN 규칙이 이를 덮어쓰지 않는지 확인한다.
  - 지연 자체를 줄이려면 목표 길이를 줄이거나 저지연 HLS(초안)를 검토한다.

### 3. 화질 진동 — 올라갔다 내려갔다

- **현상**: 화질이 몇 초마다 선명↔흐림을 반복한다. 사용자 체감이 나쁘다.
- **보이는 형태**: 플레이어 로그의 variant 전환 이벤트가 짧은 간격으로 반복된다. 선택 비트레이트 그래프가 톱니 모양이다.
- **원인**
  - 처리량 추정이 한두 샘플에 크게 흔들린다. 평활이 약하거나 표본이 짧은 세그먼트 하나다.
  - 높은 화질로 올라가면 다운로드가 느려져 추정치가 떨어진다. 다시 내리면 추정치가 오른다. 되먹임 루프다.
  - 여러 플레이어가 같은 병목 링크를 공유하면 서로의 추정을 흔든다.
- **대처**
  - 평활을 강화한다(느린 EWMA, 최솟값 규칙).
  - 올리는 문턱과 내리는 문턱을 다르게 둔다(히스테리시스). 최소 전환 간격을 둔다.
  - 버퍼 기반 규칙을 섞는다. 버퍼가 충분하면 순간 처리량 변화에 덜 반응한다.

### 4. 변형 간 전환 때 화면이 깨지거나 멈춘다

- **현상**: 화질이 바뀌는 순간 화면이 깨지거나 1~2초 멈춘다.
- **보이는 형태**: 플레이어 디코딩 에러 로그. 전환 직후 몇 프레임이 깨진다.
- **원인**
  - 변형마다 세그먼트 경계·타임스탬프가 맞지 않는다(RFC 8216 §6.2.4 위반).
  - 세그먼트가 IDR로 시작하지 않아 전환 지점에서 디코더를 초기화하지 못한다.
- **대처**
  - 인코더의 키프레임 간격을 세그먼트 길이에 맞추고, 모든 화질에서 같은 위치에 둔다.
  - 패키저 설정에서 변형 간 정렬을 켠다.

### 5. `BANDWIDTH` 값이 실제보다 작다 → 고른 화질을 못 버틴다

- **현상**: 특정 화질에서만 반복적으로 리버퍼링한다.
- **보이는 형태**: 그 변형의 실제 세그먼트 비트레이트가 마스터 재생목록의 `BANDWIDTH`보다 크다.
- **원인**: 플레이어는 `BANDWIDTH`를 믿고 고른다. 값이 과소 표기되면 감당 못 할 화질을 고른다. RFC 8216은 세그먼트가 모두 만들어진 경우 이 값이 렌디션 조합의 **최대** 세그먼트 비트레이트 합이어야 하고, 틀리면 재생이 멈출 수 있다고 적는다(§4.3.4.2).
- **대처**: 패키징 후 실제 세그먼트 크기로 `BANDWIDTH`를 다시 계산해 넣는다. 오디오가 별도 렌디션이면 비디오 peak에 오디오 peak를 더한다(비디오만 보면 과소 표기).

## 핵심 문장

- 적응형 스트리밍은 영상을 몇 초짜리 세그먼트로 자르고 여러 화질로 인코딩한 뒤, 매니페스트로 목록을 주고 평범한 HTTP GET으로 받게 한다.
- HLS는 마스터 재생목록(화질 목록)과 미디어 재생목록(세그먼트 목록) 2단이고, DASH는 MPD의 Period → AdaptationSet → Representation 계층이다.
- 라이브 지연의 바닥은 규칙에서 나온다. 끝에서 목표 길이 3개 이상 떨어져 시작하고, 재생목록은 목표 길이마다(변경 없으면 절반마다) 다시 받는다.
- ABR은 처리량 추정(EWMA)과 버퍼 수준을 섞어 다음 세그먼트의 화질을 고른다. 진동은 평활·히스테리시스·버퍼 기반 규칙으로 줄인다.
- 세그먼트는 불변이라 길게 캐시하고, 라이브 재생목록은 목표 길이보다 짧게 캐시한다. 둘을 같은 TTL로 묶으면 지연이나 리버퍼링이 생긴다.

## 관련 주제·근거

- 선행
  - [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md) — HTTP 스트리밍 응답
  - [47-cdn-and-edge](../47-cdn-and-edge/2-summary.md) — 세그먼트 전달·원점 보호
  - [34-http-caching](../34-http-caching/2-summary.md) — `Cache-Control`·`Age`
- RFC 8216 HTTP Live Streaming <https://www.rfc-editor.org/rfc/rfc8216>
  - §3 세그먼트(IDR SHOULD) · §4.3.3.1 TARGETDURATION · §4.3.3.4 ENDLIST · §4.3.4.2 STREAM-INF(BANDWIDTH) · §6.2.2 라이브 재생목록 · §6.2.4 변형 제약 · §6.3.3 재생 시작점 · §6.3.4 재생목록 갱신 · §8 예시
- draft-pantos-hls-rfc8216bis (저지연 HLS, 부분 세그먼트) <https://datatracker.ietf.org/doc/draft-pantos-hls-rfc8216bis/>
- DASH-IF Interoperability Guidelines(`MPD@type`·`minimumUpdatePeriod`) <https://dashif.org/docs/DASH-IF-IOP-v4.2-clean.htm>
- ISO/IEC 23009-1 (MPEG-DASH) — 원문은 유료라 직접 확인하지 못했다. MPD 구조는 MDN "Setting up adaptive streaming media sources"로 확인했다 <https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Audio_and_video_delivery/Setting_up_adaptive_streaming_media_sources>
- Huang, Johari, McKeown, Trunnell, Watson, "A Buffer-Based Approach to Rate Adaptation: Evidence from a Large Video Streaming Service", SIGCOMM 2014 <https://dl.acm.org/doi/10.1145/2619239.2626296>
- Shaka Player `lib/abr/ewma_bandwidth_estimator.js` <https://github.com/shaka-project/shaka-player/blob/main/lib/abr/ewma_bandwidth_estimator.js>
- dash.js ABR 설정 문서 <https://dashif.org/dash.js/pages/usage/abr/settings.html>
- AWS CloudFront "Use Amazon CloudFront Origin Shield" <https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html>
