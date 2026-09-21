# 훅 이펙트

상위: [커밋 이펙트](../README.md)

`useEffect` / `useLayoutEffect` / `useInsertionEffect` 가 전부 이 두 함수를 지난다. 이름은 넷인데 **구현은 둘**이고, 그 둘이 예외를 다르게 다룬다.

## 위치

마운트 `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L141-L247 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L141-L247))

언마운트 `packages/react-reconciler` / `src` / `ReactFiberCommitEffects.js` L249-L303 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberCommitEffects.js#L249-L303))

이펙트 타입 `packages/react-reconciler` / `src` / `ReactFiberHooks.js` L216-L226 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberHooks.js#L216-L226))

## 실제 코드

래퍼 넷 중 둘. 나머지 둘은 본문이 **글자까지 같다**.

```js
// ReactFiberCommitEffects.js L97-L112
export function commitHookLayoutEffects(
  finishedWork: Fiber,
  hookFlags: HookFlags,
) {
  // At this point layout effects have already been destroyed (during mutation phase).
  // This is done to prevent sibling component effects from interfering with each other,
  // e.g. a destroy function in one component should never override a ref set
  // by a create function in another component during the same commit.
  if (shouldProfile(finishedWork)) {
    startEffectTimer();
    commitHookEffectListMount(hookFlags, finishedWork);
    recordEffectDuration(finishedWork);
  } else {
    commitHookEffectListMount(hookFlags, finishedWork);
  }
}
```

> At this point layout effects have already been destroyed (during mutation phase). This is done to prevent sibling component effects from interfering with each other, e.g. a destroy function in one component should never override a ref set by a create function in another component during the same commit.

```js
// ReactFiberCommitEffects.js L114-L139
export function commitHookLayoutUnmountEffects(
  finishedWork: Fiber,
  nearestMountedAncestor: null | Fiber,
  hookFlags: HookFlags,
) {
  // Layout effects are destroyed during the mutation phase so that all
  // destroy functions for all fibers are called before any create functions.
  // This prevents sibling component effects from interfering with each other,
  // e.g. a destroy function in one component should never override a ref set
  // by a create function in another component during the same commit.
  if (shouldProfile(finishedWork)) {
    startEffectTimer();
    commitHookEffectListUnmount(
      hookFlags,
      finishedWork,
      nearestMountedAncestor,
    );
    recordEffectDuration(finishedWork);
  } else {
    commitHookEffectListUnmount(
      hookFlags,
      finishedWork,
      nearestMountedAncestor,
    );
  }
}
```

> Layout effects are destroyed during the mutation phase so that all destroy functions for all fibers are called before any create functions.

마운트의 알맹이.

```js
// ReactFiberCommitEffects.js L162-L177
          // Mount
          let destroy;
          if (__DEV__) {
            if ((flags & HookInsertion) !== NoHookEffect) {
              setIsRunningInsertionEffect(true);
            }
            destroy = runWithFiberInDEV(finishedWork, callCreateInDEV, effect);
            if ((flags & HookInsertion) !== NoHookEffect) {
              setIsRunningInsertionEffect(false);
            }
          } else {
            const create = effect.create;
            const inst = effect.inst;
            destroy = create();
            inst.destroy = destroy;
          }
```

언마운트의 알맹이. 부르기 전에 지운다.

```js
// ReactFiberCommitEffects.js L264-L295
          const inst = effect.inst;
          const destroy = inst.destroy;
          if (destroy !== undefined) {
            inst.destroy = undefined;
            if (enableSchedulingProfiler) {
              if ((flags & HookPassive) !== NoHookEffect) {
                markComponentPassiveEffectUnmountStarted(finishedWork);
              } else if ((flags & HookLayout) !== NoHookEffect) {
                markComponentLayoutEffectUnmountStarted(finishedWork);
              }
            }

            if (__DEV__) {
              if ((flags & HookInsertion) !== NoHookEffect) {
                setIsRunningInsertionEffect(true);
              }
            }
            safelyCallDestroy(finishedWork, nearestMountedAncestor, destroy);
            if (__DEV__) {
              if ((flags & HookInsertion) !== NoHookEffect) {
                setIsRunningInsertionEffect(false);
              }
            }

            if (enableSchedulingProfiler) {
              if ((flags & HookPassive) !== NoHookEffect) {
                markComponentPassiveEffectUnmountStopped();
              } else if ((flags & HookLayout) !== NoHookEffect) {
                markComponentLayoutEffectUnmountStopped();
              }
            }
          }
```

그리고 `destroy` 가 사는 곳.

```js
// ReactFiberHooks.js L202-L218
// The effect "instance" is a shared object that remains the same for the entire
// lifetime of an effect. In Rust terms, a RefCell. We use it to store the
// "destroy" function that is returned from an effect, because that is stateful.
// The field is `undefined` if the effect is unmounted, or if the effect ran
// but is not stateful. We don't explicitly track whether the effect is mounted
// or unmounted because that can be inferred by the hiddenness of the fiber in
// the tree, i.e. whether there is a hidden Offscreen fiber above it.
//
// It's unfortunate that this is stored on a separate object, because it adds
// more memory per effect instance, but it's conceptually sound. I think there's
// likely a better data structure we could use for effects; perhaps just one
// array of effect instances per fiber. But I think this is OK for now despite
// the additional memory and we can follow up with performance
// optimizations later.
type EffectInstance = {
  destroy: void | (() => void),
};
```

> The effect "instance" is a shared object that remains the same for the entire lifetime of an effect. **In Rust terms, a RefCell.** ... The field is `undefined` if the effect is unmounted, or if the effect ran but is not stateful.

> It's unfortunate that this is stored on a separate object, because it adds more memory per effect instance, but it's conceptually sound. **I think** there's **likely** a better data structure we could use for effects; perhaps just one array of effect instances per fiber. But **I think** this is OK **for now** despite the additional memory and we can follow up with performance optimizations later.

## 동작 흐름

```text
 ★★ 래퍼 넷, 구현 둘

 L97   commitHookLayoutEffects
 L305  commitHookPassiveMountEffects
   본문 L105-111 과 L309-315 가 **바이트까지 같다**

 L114  commitHookLayoutUnmountEffects
 L318  commitHookPassiveUnmountEffects
   본문 L124-138 과 L323-337 이 **바이트까지 같다**

 넷 다 모양이 이렇다
   shouldProfile(finishedWork) 이면
     startEffectTimer() -> 본체 -> recordEffectDuration(finishedWork)
   아니면
     본체만

 => layout 과 passive 를 가르는 것은 이 함수들이 **아니다**.
    부르는 쪽이 넘기는 hookFlags 가 가른다
 => 래퍼가 같은 이유는 **분기를 전부 비트마스크로 밀어 넣었기 때문**이다.
    그 비트마스크에 차원이 둘 있다 (바로 아래)
```

```text
 ★★ 필터가 "모든 비트가 다 있어야" 다

 L153 / L262   (effect.tag & flags) === flags

 부분 일치가 아니다. flags 에 든 비트가 effect.tag 에 **전부** 있어야 통과한다.
 그래서 부르는 쪽이 비트를 **빼면 더 많이 걸린다**

 비트는 넷뿐이고 두 축으로 나뉜다
   축 1 (단계)  Insertion 0b0010 / Layout 0b0100 / Passive 0b1000
   축 2 (여부)  HasEffect 0b0001

 ★ 축 2 를 빼는 것이 이 파일의 숨은 스위치다
```

```text
 ★★ HookHasEffect 를 빼면 그 단계의 이펙트가 전부 걸린다

 붙인다 (deps 가 바뀐 것만)  = 보통 커밋
   CMW L614   layout 마운트
   CMW L2084  insertion 언마운트 / L2090 insertion 마운트 / L2091 layout 언마운트
   CMW L3673  passive 마운트
   CMW L4893  passive 언마운트
   CMW L5314 / L5333 / L5348 / L5374   DEV StrictMode 이중 호출

 뺀다 (그 단계 전부)          = 삭제 / 숨김 / 다시 보임
   CMW L1681  insertion 언마운트 / L1687 layout 언마운트   (삭제)
   CMW L3021  layout 언마운트                               (숨김)
   CMW L3161  layout 마운트                                 (다시 보임)
   CMW L4321  passive 마운트                                (다시 보임)
   CMW L5061 / L5174  passive 언마운트                      (삭제·숨김)

 => 언마운트할 때는 deps 와 무관하게 **모든** cleanup 이 돌아야 하고,
    다시 보이게 될 때는 **모든** 이펙트가 다시 돌아야 한다
 => Offscreen 으로 숨겼다 보이면 deps 가 그대로여도 useEffect 가 다시 돈다
    (뒷문장은 내가 호출표를 보고 낸 귀결이고 주석에 없다)
```

```text
 commitHookEffectListMount  L141-247

 L145  try {
 L146    updateQueue = finishedWork.updateQueue      (선언이 L146-147 이다)
 L148    lastEffect = updateQueue !== null ? updateQueue.lastEffect : null
 L149    lastEffect !== null 이면
 L150      firstEffect = lastEffect.next      ★ **원형 리스트다**
 L151      effect = firstEffect
 L152      do {
 L153        (effect.tag & flags) === flags 이면
 L154          [DEAD:enableSchedulingProfiler] 마커 시작 (L154-160)
 L164          [__DEV__]
 L165            HookInsertion 이면
 L166              setIsRunningInsertionEffect(true)
 L168            destroy = runWithFiberInDEV(finishedWork, callCreateInDEV, effect)
 L169            HookInsertion 이면
 L170              setIsRunningInsertionEffect(false)
 L172          아니면
 L173            create = effect.create
 L174            inst = effect.inst
 L175            destroy = create()             ★ **사용자 코드**
 L176            inst.destroy = destroy
 L179          [DEAD] 마커 끝 (L179-185)
 L187          [__DEV__]
 L188            destroy 가 undefined 도 함수도 아니면 경고 (L188-238)
 L241        effect = effect.next
 L242      } while (effect !== firstEffect)
 L244  } catch (error) {
 L245    captureCommitPhaseError(finishedWork, finishedWork.return, error)
```

```text
 commitHookEffectListUnmount  L249-303

 L254  try {
 L257    lastEffect = ...
 L259    firstEffect = lastEffect.next
 L260    effect = firstEffect
 L261    do {
 L262      (effect.tag & flags) === flags 이면
 L264        inst = effect.inst
 L265        destroy = inst.destroy
 L266        destroy !== undefined 이면
 L267          inst.destroy = undefined       ★ **부르기 전에 지운다**
 L268          [DEAD:enableSchedulingProfiler] 마커 시작 (L268-274)
 L276          [__DEV__]
 L277            HookInsertion 이면
 L278              setIsRunningInsertionEffect(true)
 L281          safelyCallDestroy(finishedWork, nearestMountedAncestor, destroy)
 L282          [__DEV__]
 L283            HookInsertion 이면
 L284              setIsRunningInsertionEffect(false)
 L288          [DEAD] 마커 끝 (L288-294)
 L297      effect = effect.next
 L298    } while (effect !== firstEffect)
 L300  } catch (error) ...
```

```text
 ★★ 예외 격리 범위가 둘에서 다르다

 둘 다 바깥 try 는 있다 (L145 / L254). 차이는 **안쪽**이다

 마운트    루프 안에 잡는 것이 없다
           L175 create() 가 던지면 곧장 L244 의 catch 로 간다
           DEV 도 같다 - runWithFiberInDEV 는 try/**finally** 라 되던지고,
           CUS L178-188 의 callCreate 에도 try/catch 가 없다
           => 이펙트 하나가 던지면 그 fiber 의 **나머지 이펙트가 건너뛰어진다**

 언마운트  루프 **안**에서 잡는다 - L281 safelyCallDestroy
           프로덕션은 그 함수 자기 catch (L930-932)
           DEV 는 CUS L195-207 의 callDestroy 안 catch (L201-205)
           => 하나가 던져도 나머지 cleanup 은 계속 돈다

 ★ 딸린 귀결 하나 - 마운트에서 던지면 L176 이 안 돌아
   inst.destroy 가 undefined 로 남는다.
   그래서 나중 언마운트가 L266 에서 그 훅을 건너뛴다.
   이미 마운트된 이펙트들은 destroy 를 갖고 있어 정상 정리된다

 ※ "건너뛰어진다" 와 딸린 귀결은 내가 두 파일을 맞춰 보고 낸 결론이고 주석에 없다
```

```text
 ★ 이펙트 리스트도 꼬리를 가리키는 원형 리스트다

 L150 / L259  firstEffect = lastEffect.next

 [업데이트 큐]의 shared.pending 과 같은 모양이다.
 다만 이쪽은 원형을 **끊지 않는다** - 순회가 firstEffect 로 돌아오면 끝낸다
 (L242 / L298 의 while 조건이 그것이다)
```

```text
 ★★ destroy 는 Effect 가 아니라 EffectInstance 에 산다

 Effect         Hooks L220-226   tag / inst / create / deps / next
 EffectInstance Hooks L216-218   destroy  ← 칸이 이것 하나다

 Effect 객체는 렌더마다 새로 만들어지는데 inst 는 이어진다.
 그래서 L176 이 담은 destroy 를 **다음 커밋의** L265 가 꺼내 쓸 수 있다

 ★ 그리고 undefined 가 두 뜻이다 (주석 Hooks L205-206)
     언마운트됐다  /  돌았는데 cleanup 을 안 돌려줬다
   주석 L206-208 이 구분하지 않는 이유를 적는다 -
     마운트 여부는 위쪽 Offscreen fiber 의 숨김 여부로 알 수 있어서다

 ★ L267 이 부르기 **전에** undefined 로 만드는 것도 이 칸 하나에 기대고 있다
   (두 번 불리지 않게 하려는 것으로 보인다 - 주석은 없다)
```

```text
 ★★ HookFlags 는 비트가 넷뿐이고, 주석 한 줄이 커밋 순서를 설명한다
```

```js
// ReactHookEffectTags.js L10-L20
export type HookFlags = number;

export const NoFlags = /*   */ 0b0000;

// Represents whether effect should fire.
export const HasEffect = /* */ 0b0001;

// Represents the phase in which the effect (not the clean-up) fires.
export const Insertion = /* */ 0b0010;
export const Layout = /*    */ 0b0100;
export const Passive = /*   */ 0b1000;
```

```text
 > Represents the phase in which the effect **(not the clean-up)** fires.

 이 괄호가 핵심이다.
 tag 가 Layout 이어도 **cleanup 은 변이 단계에서** 돈다.
 그 이유를 L119-121 주석이 적는다 -
   모든 fiber 의 destroy 가 어떤 create 보다 먼저 돌아야
   한 컴포넌트의 destroy 가 다른 컴포넌트의 create 가 세운 ref 를
   덮어쓰지 않는다

 그리고 같은 사정을 마운트 쪽(L101-102)은 반대편에서 적는다 -
   "At this point layout effects have already been destroyed
    (during mutation phase)."
 한쪽은 "여기서 파괴한다, 그 이유는", 다른 쪽은 "이미 파괴됐다" 다
```

```text
 ★ DEV 경고가 async 이펙트를 겨냥한다  L188-238

 destroy 가 undefined 도 함수도 아니면 세 갈래로 문구를 만든다
   L199  destroy === null 이면
           "You returned null. If your effect does not require clean up,
            return undefined (or nothing)."
   L204  destroy.then 이 함수이면
           "It looks like you wrote <hookName>(async () => ...) or returned
            a Promise." + 안쪽에 async 함수를 만들어 즉시 부르라는 예시 전체
   L221  그 밖이면 (L221-224)
           "You returned: " + destroy

 hookName 은 effect.tag 로 정한다 (L190-196) -
   Layout 이면 useLayoutEffect, Insertion 이면 useInsertionEffect,
   아니면 useEffect
```

```text
 ★ setIsRunningInsertionEffect 는 경고 하나를 위해 산다

 세우는 곳  L166 / L170 / L278 / L284   (insertion 이펙트 앞뒤)
 ★ 그런데 **짝이 맞지 않는다**. try/finally 가 없어서
   L168 이나 L281 이 던지면 L170 / L284 에 닿지 않는다
 사는 곳    WL L764  let isRunningInsertionEffect = false
 읽는 곳    WL L979  scheduleUpdateOnFiber 안에서 한 번
 하는 일    WL L980  console.error('useInsertionEffect must not schedule updates.')
 되돌리는 곳 WL L4900  ★ **captureCommitPhaseError 안**이다

 즉 켜진 채 남는 것을 **에러 경로가 치운다**.
 고치는 코드가 세우는 파일 밖에 있다

 => [업데이트 큐]의 isDisallowedContextReadInDEV 와 구조가 같다 -
    세우는 곳 몇, 읽는 곳 하나(경고 하나), 에러 경로에서 리셋
    (이 대비는 내가 붙인 것이다)
```

```text
 ★ safelyCallDestroy 에 쓰이지 않는 인자가 하나 있다  L910-934

 L913  destroy: (() => void) | (({...}) => void)
 L914  resource?: {...} | void | null
 L916  // $FlowFixMe[extra-arg] @poteto this is safe either way because
 L916  // the extra arg is ignored if it's not a CRUD effect
 L917  destroy_ = resource == null ? destroy : destroy.bind(null, resource)

 호출처가 L281 **하나뿐**이고 인자를 셋만 넘긴다.
 => resource 는 언제나 undefined 이고 L917 의 bind 갈래는 돌지 않는다
 => "CRUD effect" 라는 말이 리콘실러 전체에서 이 주석 한 줄에만 나온다

 아직 없는 훅을 위해 미리 낸 자리로 보인다
 (마지막 문장은 내 판단이다)
```

## 결과가 쓰이는 곳

```text
 inst.destroy
      --> 마운트가 담고 언마운트가 꺼내 쓰고 지운다
      --> 같은 칸을 두 함수가 번갈아 쓴다

 부르는 쪽의 hookFlags
      --> 어떤 이펙트가 이번 패스에 도는지를 정한다
      --> [커밋]이 mutation/layout 을, [패시브 이펙트]가 passive 를 넘긴다

 captureCommitPhaseError
      --> 이펙트의 예외를 가장 가까운 경계로 보낸다
```

## 다루지 않는 것

`Effect.deps` 가 렌더 단계에서 비교되어 `HasEffect` 비트가 붙는 경로([훅](../../hooks/README.md)에 있다), `updateQueue.lastEffect` 에 이펙트가 쌓이는 `pushEffect` 쪽, `runWithFiberInDEV` 의 DEV 스택, `startEffectTimer` / `recordEffectDuration` 의 측정, `enableSchedulingProfiler` 마커 여덟 자리(`markComponentPassiveEffectMountStarted` 계열)의 본문, `ReactFiberApplyGesture.js` 가 insertion 이펙트만 돌리는 사정은 같은 뼈대의 곁가지라 요약만 했다.
