# security/25-supply-chain-security — 의존성 위험·SBOM·서명·재현 빌드·업데이트 운영 — 정리 (힌트)

## 해결하는 문제

내가 쓴 코드는 전체 바이트의 일부다.\
나머지는 **남이 만든 의존성**이고, 그 의존성도 또 남의 의존성을 끌어온다.

```text
  내 앱 ──depends──▶ A ──▶ C ──▶ xz(liblzma)      ← 내가 직접 고른 적 없는 "전이 의존성"
            └──────▶ B ──▶ C
  공격 지점
   ① 내가 고른 버전이 이미 취약 (미패치 — Equifax/Struts)
   ② 유지보수자 계정·빌드가 장악돼 정상 버전에 백도어 (xz 2024)
   ③ 비슷한 이름의 가짜 패키지를 설치 (typosquatting)
   ④ 빌드·배포 파이프라인이 산출물을 바꿔치기 (SolarWinds)
```

- *의존성(dependency)*: 내 코드가 가져다 쓰는 외부 라이브러리. *직접 의존성*은 내가 적은 것, *전이 의존성*은 그것들이 끌어온 것.
- 공급망 보안은 "내 코드가 안전한가"가 아니라 **"내가 실제로 실행하는 모든 바이트가 내가 의도한 것이 맞는가"**를 묻는다.
- OWASP Top 10 2021 A06 Vulnerable and Outdated Components(①)와 A08 Software and Data Integrity Failures(②③④)에 걸쳐 있다. 2025판에서는 "알려진 취약 구성 요소" 범주가 공급망 실패 전체로 넓어져 A03 Software Supply Chain Failures가 됐다(OWASP 2025 A03 Background).

쉬운 예: 식당이 쓰는 재료의 대부분은 납품업체가 댄다.\
① 리콜된 재료를 안 바꾸고 계속 쓰거나, ② 납품업체가 바꿔치기당했거나, ③ 상표를 흉내 낸 가짜가 섞이거나, ④ 운송 중 누가 상자를 열었다.\
"우리 주방은 깨끗하다"로는 안 되고, **재료의 출처와 무결성**을 봐야 한다. SBOM이 재료 명세서, 서명이 봉인, 재현 빌드가 "같은 재료면 같은 요리"다.

실무 예:
- Equifax(2017): Apache Struts(CVE-2017-5638, NVD 9.8)를 공개·패치 뒤에도 안 고쳐 최소 1억 4,550만 명(미국) 개인정보 유출(미 GAO-18-559).
- Log4Shell(2021): 전이 의존성으로 깊이 박힌 log4j-core. 내 코드엔 로그 한 줄뿐인데 영향(23번).
- xz/liblzma 백도어(2024, CVE-2024-3094): 업스트림 커미터가 낸 5.6.0·5.6.1에 백도어가 들어갔다. 위장한 테스트 파일은 git에도 있었고, 그것을 꺼내 빌드에 끼우는 스크립트 한 부분은 **배포 tarball에만** 있었다(oss-security, Andres Freund).

## 동작·원리

### 1. 의존성 그래프와 락파일

```text
  manifest(선언)          lock(해소 결과)
  "left-pad: ^1.0.0"  ──▶ left-pad 1.0.3  integrity sha512-...   ← 정확한 버전 + 해시 고정
                          그 전이 의존성도 버전·해시로 박제 (링크 항목 등은 해시 없음)
```

- *manifest*: `package.json`·`pom.xml`처럼 **원하는 범위**를 적는 파일(`^1.0.0`).
- *락파일*: `package-lock.json`·`Cargo.lock`처럼 범위를 푼 **정확한 버전 + 무결성 해시**를 박제한 파일. 그래서 어제 CI와 오늘 CI, 내 PC와 서버가 해시가 기록된 패키지에 대해 같은 바이트를 받는다. 다만 심볼릭 링크 항목처럼 해시가 없는 항목이 있고(npm `package-lock.json` 문서), `npm ci`도 기본으로 설치 스크립트를 돌리며 플랫폼별 선택 의존성이 있으므로 설치 결과 전체가 같다는 보장은 아니다(language/19-modules-and-dependency-resolution, [language README](../../language/README.md)).
- *semver*: `주.부.수(major.minor.patch)`. `^1.2.3`은 major 고정, minor·patch 허용.
  - 흔한 오해: "락파일이 있으면 새 취약점도 자동으로 막힌다." 락파일은 **바이트 고정**이다. 고정된 그 버전이 뒤늦게 취약으로 밝혀지면, 누가 올려 주기 전까지 취약한 채 고정돼 있다(바꿔치기 탐지(④의 일부)와 미패치(①)는 다른 문제).

(실험, Node 22.23.2 / npm 10.9.8, `--network none`, 2026-10-07 — 로컬에서 만든 tarball만 설치)

```text
"node_modules/demo-left-pad": {
  "version": "1.0.0",
  "resolved": "file:demo-left-pad-1.0.0.tgz",
  "integrity": "sha512-eOphyG8pHxwPE6BnsqD0EdBXHiO87m4NYwMGHDuZO5N6ZYDcAy87r/SjT4bnhxPORhrKR7ccQCGnju8Xc6vjgA=="
}
```

- 관찰: `npm install`이 락파일에 **설치한 바이트의 sha512**를 적었다. 다음부터 `npm ci`는 이 해시와 대조한다.

### 2. 무결성 검증 — 바꿔치기를 잡는다

(실험, 같은 환경 — 락파일은 그대로 두고 tarball 내용만 바꿔(같은 이름·버전) `npm ci`)

```text
npm warn tarball ... seems to be corrupted. Trying again.
npm error code EINTEGRITY
npm error sha512-eOphyG8p... integrity checksum failed when using sha512:
  wanted sha512-eOphyG8p...  but got sha512-c8/AcVBK...  (582 bytes)
```

- 관찰: 이름·버전이 같아도 **내용 해시가 다르면** `npm ci`가 `EINTEGRITY`로 거부했다(npm 캐시가 빈 새 컨테이너 기준).
- 조건: 점검 재실행에서 `npm install`과 `npm ci`를 **같은 컨테이너**(같은 `~/.npm` 캐시)에서 돌리자, `npm ci --offline`은 오류 없이 끝났고 설치된 내용은 바뀌기 **전** 바이트였다. 캐시가 integrity 해시로 내용을 찾기 때문이다. 바꿔치기가 설치되지 않은 것은 같지만, `EINTEGRITY` 경보는 뜨지 않았다(실험, 같은 환경, 2026-10-07). 재현 설치(§1)의 "같은 입력 → 같은 바이트"를 깨는 바꿔치기(④의 일부)를 잡는다.
- 한계: 이 해시는 **애초에 락파일에 박힌 그 바이트**를 기준으로 한다. 유지보수자가 처음부터 악성 버전을 정식 배포하면(②), 그 악성 바이트의 해시가 락파일에 박힐 뿐이다. 그래서 해시 고정만으로는 ②를 못 막는다 — 서명과 출처(§4)가 필요하다.

### 3. SBOM — 내가 실제로 싣는 것의 명세서

```text
  SBOM(Software Bill of Materials): 산출물에 들어간 구성 요소의 목록 (도구가 찾은 만큼 — 빠질 수 있다)
   이름 · 버전 · 고유 식별자(purl) · 해시 · 라이선스 · 관계(누가 누구를 끌어왔나)
   형식: CycloneDX, SPDX
```

(실험, 같은 환경 — `npm sbom --sbom-format cyclonedx`)

```text
bomFormat CycloneDX 1.5
  library demo-left-pad 1.0.0 pkg:npm/demo-left-pad@1.0.0 SHA-512
```

- 관찰: 도구가 구성 요소를 `type·name·version·purl·해시`로 뽑았다. `pkg:npm/...`는 **purl(package URL)** — 생태계·이름·버전을 한 문자열로 적는 표준 식별자다.
- SBOM의 쓸모: 새 CVE가 뜨면 "우리 산출물 중 어디에 그 버전이 들어 있나"를 **목록 조회**로 빠르게 답한다 — 단 SBOM이 그 산출물을 대상으로 빠짐없이 만들어졌을 때, 기록된 구성 요소에 한해서다. 위 실험의 `npm sbom`은 이 프로젝트의 npm 의존성만 나열했고, 배포 산출물 전체(OS 패키지·번들된 바이너리)를 확인한 것은 아니다. Log4Shell처럼 전이 의존성 깊이 박힌 취약점일수록 목록이 있느냐가 대응 속도를 가른다(해석 — 이 노트가 확인한 측정 자료는 없다).
- 도구: Maven은 `cyclonedx-maven-plugin`, 범용은 Syft 등. (환경에 설치된 `npm sbom`만 실험으로 확인, 나머지는 문서 근거.)

### 4. 서명과 출처 — ②를 겨눈다

```text
  빌드 → 산출물 ──sign──▶ 서명 ──┐
                                 ├─▶ 투명성 로그(append-only)에 기록
  검증자: "이 바이트가 기대한 빌더가 만든 그것이 맞나"
```

- *서명*: 산출물에 만든 주체의 서명(06번 전자서명). 받는 쪽이 공개키로 "출처+무결성"을 검증한다.
- *Sigstore*: 키 관리 부담을 줄인 서명 체계.
  - Fulcio: OIDC 신원을 확인하고 **짧은 수명 인증서**를 발급(14번 OIDC). 장기 키를 안 들고 다닌다("keyless").
  - Cosign: 서명 클라이언트.
  - Rekor: 서명 기록을 담는 **immutable, append-only ledger**(Sigstore 문서). 공개 Rekor 로그는 Trillian 위에서 돌았다(Sigstore Rekor 문서. Trillian README는 차세대 로그가 타일 방식 Tessera로 옮겨 간다고 적는다). Trillian — "Verifiable Data Structures" 백서(Certificate Transparency의 일반화)를 구현한 **머클 트리** 기반(network/31 CT, [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)).
- *SLSA*: 빌드 출처(provenance)의 성숙도 단계(SLSA v1.0 Build track).
  - L0: 보장 없음. L1: provenance가 있으나 위조·우회가 쉬움("trivial to bypass or forge"). L2: 호스팅 빌드 플랫폼 — 위조에 "explicit 'attack'"이 필요(쉬울 수는 있음). L3: 강화된 빌드 — 위조에 "대부분의 공격자 능력을 넘는 취약점 악용"이 필요.
- *재현 빌드(reproducible build)*: 같은 소스 + 같은 빌드 환경 + 같은 빌드 지시 → 누가 빌드해도 **같은 바이트**(reproducible-builds.org 정의). 서명된 소스와 내가 빌드한 바이트가 같은지 제3자가 검증할 수 있다(engineering-practice/07 재현 빌드).

### 5. 업데이트 운영 — 미패치(①)를 막는 절차

```text
  새 버전/CVE 공개
     │
     ├─ 봇이 PR 생성 (Renovate/Dependabot) ── 테스트 통과 → 검토/자동 병합
     ├─ minimumReleaseAge: 갓 나온 버전은 n일 묵혀 설치 (악성 배포 조기 탐지 시간 — ②③ 완화)
     └─ EOL 런타임 추적: 보안 패치가 끊기는 날짜 전에 올린다
```

- *Renovate / Dependabot*: 의존성 업데이트를 PR로 자동 제안하는 봇.
  - `minimumReleaseAge`(옛 `stabilityDays`): 릴리스 후 이 기간이 지나야 올린다. 새 버전이 악성이어도(②③) 커뮤니티가 알아챌 시간을 번다.
  - `vulnerabilityAlerts`·`packageRules`·`lockFileMaintenance`·`rangeStrategy: pin`으로 보안 업데이트는 빨리, 일반 업데이트는 천천히 같은 차등을 둔다.
- *EOL(End of Life)*: 보안 패치가 끊기는 시점. 예: Node.js 18은 2025-04-30, 20은 2026-04-30, 22는 2027-04-30, 24는 2028-04-30 보안 지원 종료(endoflife.date). EOL 런타임은 새 CVE가 나와도 패치가 안 나온다.
- Equifax(①)의 교훈: 패치가 **있었는데** 설치 대상 식별·적용이 안 됐다(GAO-18-559: "the scan did not detect the vulnerability on the online dispute portal"). 도구만이 아니라 **누가 언제까지 올리는가**라는 절차가 핵심이다.

## 쓰이는 자료구조·알고리즘

- **의존성 그래프(DAG) + 위상정렬** — 어느 버전을 설치할지 푸는 것은 제약을 만족하는 그래프 해소다. 빌드 순서도 위상정렬이다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [engineering-practice/07-build-systems-and-reproducibility](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md)
- **암호 해시** — 락파일 integrity·SBOM 해시·재현 빌드 대조가 전부 충돌 저항 해시다. 약한 해시면 바꿔치기를 못 잡는다(04번, [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)).
- **머클 트리 / 투명성 로그** — Sigstore Rekor·CT가 append-only 로그의 변조를 머클 트리로 **검증 가능하게** 만든다(포함·일관성 증명을 누군가 확인하고 감시할 때 드러난다). [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [network/31-revocation-ocsp-ct](../../network/31-revocation-ocsp-ct/2-summary.md)
- **전자서명** — 출처+무결성. [security 06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 순서

1. **락파일을 커밋**하고 CI는 `npm ci`처럼 락 그대로 설치한다(재현 설치). Maven은 기본 락파일이 없으므로 버전을 정확히 고정하고 체크섬 검증을 엄격하게(`--strict-checksums`) 둔다.
2. **정기 스캔**: CVE 데이터베이스 대조(SCA)를 CI와 스케줄 양쪽에서. 출시 때만 하면 그 사이 공개된 CVE를 놓친다.
3. **SBOM을 빌드 산출물로** 남긴다. 사고 때 영향 범위를 목록 조회로 답한다.
4. **업데이트 봇** + `minimumReleaseAge` + EOL 추적으로 "안 올려서 생기는 위험"과 "급하게 올려서 생기는 위험"을 함께 관리한다.
5. 핵심 산출물은 **서명**하고, 받는 쪽에서 검증한다.

### 2. 전이 의존성까지 보기

```bash
# 어떤 버전이 실제로 들어오나 (전이 포함)
mvn dependency:tree -Dincludes=org.apache.logging.log4j:log4j-core
npm ls somelib; npm ls --all | grep -i somelib

# 락 그대로, 무결성 검증하며 설치
npm ci                       # package-lock.json의 integrity와 대조 (실험에서 EINTEGRITY로 바꿔치기 거부)
```

- 직접 의존성만 보면 23번의 log4j처럼 **깊이 박힌** 취약점을 놓친다.

### 3. SCA — 알려진 취약 버전 찾기 (정기)

```bash
# OSV(Open Source Vulnerabilities) API에 설치된 버전을 질의 — 예시 (네트워크 필요)
# 패키지·버전 목록을 만들어 배치 질의하고, 매치가 있으면 CI 실패로 처리한다
mvn org.owasp:dependency-check-maven:check   # OWASP Dependency-Check (NVD 대조)
```

- engineering-practice/15-security-standards의 실험 B("어제 안전한 버전이 오늘 취약")와 같은 이유로 **반복**해야 한다. 코드가 안 바뀌어도 세상의 CVE 지식이 바뀐다.

### 4. 업데이트 정책 (Renovate 예시)

```json
{
  "extends": ["config:recommended"],
  "minimumReleaseAge": "3 days",
  "vulnerabilityAlerts": { "minimumReleaseAge": "0 days", "labels": ["security"] },
  "packageRules": [
    { "matchUpdateTypes": ["patch", "minor"], "automerge": true },
    { "matchUpdateTypes": ["major"], "automerge": false }
  ],
  "lockFileMaintenance": { "enabled": true }
}
```

- 보안 경보는 즉시(`minimumReleaseAge: 0`), 일반 업데이트는 3일 묵힘. patch·minor는 테스트 통과 시 자동 병합, major는 사람이 본다. (값은 예시 — 조직 위험 선호에 맞춘다.)

### 5. 진단 — "이 CVE가 우리에게 있나"

```bash
# SBOM(CycloneDX)에서 purl로 찾기
jq -r '.components[] | "\(.name) \(.version) \(.purl)"' sbom.json | grep -i log4j-core
# 배포물 안에서 직접 (중첩 jar·남아 있는 META-INF/maven 경로만 잡힌다.
#  패키지 이름을 바꾼(relocate) 셰이딩은 이 이름으로 못 찾는다 — 없다는 판정 아님)
unzip -l app.jar | grep -i 'log4j-core'
```

## 장애 시나리오와 대처

### 1. 미패치 구성 요소로 침해 (Equifax/Struts, ⚠ 커리큘럼)

- **현상**: 공개된 취약점이 오래전에 패치됐는데도 그 경로로 침해당한다.
- **보이는 형태**: 사고 조사에서 "패치는 있었으나 해당 서버에 적용 안 됨". 스캔이 그 자산을 못 봄.
- **원인**: 패치 대상 식별·적용 절차의 공백. 자산 목록·소유자 불명확.
- **대처**: SBOM으로 "어디에 무엇이 있나"를 항상 안다. 업데이트 봇 + SLA(며칠 안에 보안 패치). 자산마다 소유자를 둔다. 사고 전체는 30번.

### 2. 정상 버전에 백도어 (xz 2024형, ②)

- **현상**: 공식 배포 버전인데 악성 동작이 들어 있다. 일부는 git 소스에 없고 배포 tarball에만 있을 수 있다.
- **보이는 형태**: 특정 버전에서 이상 증상(xz는 "logins with ssh taking a lot of CPU, valgrind errors"로 발견됨, oss-security 2024-03-29 Andres Freund 보고). 배포 tarball과 git 소스가 다름(xz는 빌드 스크립트 한 부분이 tarball에만 있었다).
- **원인**: 유지보수자 계정·빌드 과정 장악. 해시 고정(§2)으로는 못 막는다 — 악성 바이트의 해시가 박힐 뿐.
- **대처**: `minimumReleaseAge`로 갓 나온 버전을 묵힌다. 배포 tarball을 저장소 태그와 대조하고, 재현 빌드로 배포 바이트를 독립 빌드 결과와 맞춰 본다("소스 = 배포물" 검증). 서명·출처(SLSA)로 신뢰 경로를 좁힌다. 영향 받으면 즉시 롤백·격리.

### 3. typosquatting — 비슷한 이름 가짜 (③)

- **현상**: 의존성 하나가 설치·빌드 중 네트워크로 데이터를 보내거나 이상 스크립트를 돈다.
- **보이는 형태**: 이름이 유명 패키지와 한 글자 다름(`reqeusts`·`lodahs`). 설치 스크립트(`postinstall`)가 외부 접속.
- **원인**: 오타·복붙으로 가짜를 설치. 락파일에 그대로 박힘.
- **대처**: 설치 스크립트 비활성(`npm ci --ignore-scripts`), 내부 프록시 레지스트리로 허용 목록, 새 의존성 추가 시 리뷰. `minimumReleaseAge`.

### 4. 빌드·파이프라인 바꿔치기 (SolarWinds형, ④)

- **현상**: 소스는 깨끗한데 **빌드된** 산출물에 악성 코드가 들어가 서명까지 받아 배포된다.
- **보이는 형태**: 재현 빌드가 공식 산출물과 다른 바이트를 냄. 빌드 로그에 예상 밖 단계.
- **원인**: CI/CD 자체가 침해됨. OWASP A08(2021)의 대표 예 — SolarWinds가 악성 업데이트를 1만 8천여 조직에 배포했고, 그중 약 100곳이 실제 피해를 입었다("distributed ... to more than 18,000 organizations, of which around 100 or so were affected").
- **대처**: 파이프라인 접근 분리·최소 권한, 빌드 환경 격리, SLSA L2+ 출처, 재현 빌드 검증. CI 비밀은 09번·KMS로.

### 5. EOL 런타임에 새 CVE (①의 변형)

- **현상**: 런타임·프레임워크에 새 취약점이 떴는데 패치 버전이 안 나온다.
- **보이는 형태**: 벤더 보안 공지가 "지원 종료 버전은 대상 아님". 사용 중 버전이 EOL 지난 상태.
- **원인**: EOL 추적 공백. 큰 메이저 업그레이드를 미룸.
- **대처**: EOL 날짜를 자산별로 추적(endoflife.date), 지원 종료 전 업그레이드 계획. 봇의 major 업데이트를 정기적으로 처리.

## 핵심 문장

- 공급망 보안은 "내 코드가 안전한가"가 아니라 "실행하는 모든 바이트가 의도한 것이 맞는가"를 묻는다.
- 락파일·integrity 해시는 바꿔치기(④의 일부)를 잡지만, 정상 배포에 심긴 백도어(②)는 못 막는다 — 서명·출처·재현 빌드가 필요하다.
- SBOM은 "새 CVE가 우리 어디에 있나"를 목록 조회로 답하게 한다. 전이 의존성 깊이 박힌 Log4Shell 같은 경우에 특히 쓸모 있다.
- 미패치(Equifax)는 도구가 아니라 "누가 언제까지 올리는가"라는 절차의 문제였다.
- 새 버전을 며칠 묵히는 것(minimumReleaseAge)은 악성 배포가 들통날 시간을 버는 값싼 방어다.

## 관련 주제·근거

- 선행
  - language 19-modules-and-dependency-resolution(원고 [language README](../../language/README.md)) — semver·락파일·해소
- 후속·연결
  - [security 06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) · [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — 서명·CI 비밀
  - [23-deserialization-and-parser-attacks](../23-deserialization-and-parser-attacks/2-summary.md) — 깊이 박힌 취약 라이브러리(Log4Shell)
  - [engineering-practice/07-build-systems-and-reproducibility](../../engineering-practice/07-build-systems-and-reproducibility/2-summary.md) · [15-security-standards](../../engineering-practice/15-security-standards/2-summary.md) — 재현 빌드, SCA
  - [network/31-revocation-ocsp-ct](../../network/31-revocation-ocsp-ct/2-summary.md) — Certificate Transparency(머클 로그의 선례)
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
  - security 29-security-symptom-index · 30-security-incidents(Equifax·Log4Shell·xz)
- 1차 출처
  - OWASP Top 10 2021 A06 Vulnerable and Outdated Components · A08 Software and Data Integrity Failures <https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/> · OWASP Top 10 2025 A03 Software Supply Chain Failures <https://owasp.org/Top10/2025/>
  - NVD CVE-2017-5638 Struts(게시 2017-03-11, CVSS 3.1 9.8, CISA KEV) · CVE-2024-3094 xz(게시 2024-03-29, CVSS 10.0) <https://nvd.nist.gov/vuln/detail/CVE-2024-3094>
  - 미 GAO-18-559 Data Protection(Equifax, 2018-08) — 최소 1억 4,550만 명, US-CERT 공개 2일 뒤인 2017-03-10 취약점 스캔·접근, 2017-05-13부터 별도 침입, 약 76일간 미탐지, 만료 인증서로 침해 전 약 10개월간 암호화 트래픽 미검사, 공지 수신자 목록이 낡아 패치 담당에게 미전달, "the scan did not detect the vulnerability on the online dispute portal" <https://www.gao.gov/products/gao-18-559>
  - oss-security "backdoor in upstream xz/liblzma"(Andres Freund, 2024-03-29) — 5.6.0·5.6.1, "The upstream xz repository and the xz tarballs have been backdoored", build-to-host.m4의 주입 줄은 "solely in the distributed tarballs" <https://www.openwall.com/lists/oss-security/2024/03/29/4>
  - SLSA v1.0 Build track L0–L3 <https://slsa.dev/spec/v1.0/levels> · Sigstore 개요(Fulcio·Cosign·Rekor "immutable, append-only ledger", keyless/OIDC) <https://docs.sigstore.dev/about/overview/> · Trillian("Verifiable Data Structures" 백서 구현) <https://github.com/google/trillian>
  - CycloneDX·SPDX·purl 명세 · OWASP Dependency-Check · Renovate `minimumReleaseAge`(옛 `stabilityDays`) <https://docs.renovatebot.com/configuration-options/> · Node.js EOL <https://endoflife.date/nodejs>
- 실험(로컬, `--network none`, Node 22.23.2 / npm 10.9.8)
  - 락파일 integrity sha512 기록 · `npm ci`가 내용 변조 tarball을 `EINTEGRITY`로 거부(캐시가 빈 환경, 캐시가 있으면 경보 없이 캐시의 원래 바이트 설치) · `npm sbom --sbom-format cyclonedx`가 purl·SHA-512로 구성 요소 출력
