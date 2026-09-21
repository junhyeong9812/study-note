# 업데이터

상위: [클래스 컴포넌트](../README.md)

`this.setState` 가 fiber 를 찾아가는 길이다. 다리가 **두 줄**이고, 세 메서드의 뼈대가 같다.

## 위치

`packages/react-reconciler` / `src` / `ReactFiberClassComponent.js` L165-L243 ([GitHub](https://github.com/facebook/react/blob/68631c0453b08e2c7c96a40910f4c91db1f66d5a/packages/react-reconciler/src/ReactFiberClassComponent.js#L165-L243))

## 실제 코드

`enqueueSetState` 가 원형이다.

```js
// ReactFiberClassComponent.js L167-L190
  enqueueSetState(inst: any, payload: any, callback) {
    const fiber = getInstance(inst);
    const lane = requestUpdateLane(fiber);

    const update = createUpdate(lane);
    update.payload = payload;
    if (callback !== undefined && callback !== null) {
      if (__DEV__) {
        warnOnInvalidCallback(callback);
      }
      update.callback = callback;
    }

    const root = enqueueUpdate(fiber, update, lane);
    if (root !== null) {
      startUpdateTimerByLane(lane, 'this.setState()', fiber);
      scheduleUpdateOnFiber(root, fiber, lane);
      entangleTransitions(root, fiber, lane);
    }

    if (enableSchedulingProfiler) {
      markStateUpdateScheduled(fiber, lane);
    }
  },
```

`enqueueForceUpdate` 는 한 칸이 빈다.

```js
// ReactFiberClassComponent.js L218-L242
  enqueueForceUpdate(inst: any, callback) {
    const fiber = getInstance(inst);
    const lane = requestUpdateLane(fiber);

    const update = createUpdate(lane);
    update.tag = ForceUpdate;

    if (callback !== undefined && callback !== null) {
      if (__DEV__) {
        warnOnInvalidCallback(callback);
      }
      update.callback = callback;
    }

    const root = enqueueUpdate(fiber, update, lane);
    if (root !== null) {
      startUpdateTimerByLane(lane, 'this.forceUpdate()', fiber);
      scheduleUpdateOnFiber(root, fiber, lane);
      entangleTransitions(root, fiber, lane);
    }

    if (enableSchedulingProfiler) {
      markForceUpdateScheduled(fiber, lane);
    }
  },
```

그리고 생명주기 안에서 `this.state` 를 직접 건드리면 여기서 가로챈다.

```js
// ReactFiberClassComponent.js L715-L725
  if (oldState !== instance.state) {
    if (__DEV__) {
      console.error(
        '%s.componentWillMount(): Assigning directly to this.state is ' +
          "deprecated (except inside a component's " +
          'constructor). Use setState instead.',
        getComponentNameFromFiber(workInProgress) || 'Component',
      );
    }
    classComponentUpdater.enqueueReplaceState(instance, instance.state, null);
  }
```

## 동작 흐름

```text
 세 메서드의 뼈대가 같다

 L168/192/219  fiber = getInstance(inst)
 L169/193/220  lane = requestUpdateLane(fiber)
 L171/195/222  update = createUpdate(lane)
               (tag / payload / callback 을 채운다 - 여기가 갈린다)
 L180/206/232  root = enqueueUpdate(fiber, update, lane)
 L181/207/233  root !== null 이면
                 startUpdateTimerByLane(lane, '<이름>', fiber)
                 scheduleUpdateOnFiber(root, fiber, lane)
                 entangleTransitions(root, fiber, lane)

 갈리는 자리

 enqueueSetState      L167  tag 를 안 건드린다 (createUpdate 의 기본값 UpdateState)
                      L172  update.payload = payload
                      L182  'this.setState()'
                      L188  markStateUpdateScheduled

 enqueueReplaceState  L196  update.tag = ReplaceState
                      L197  update.payload = payload
                      L208  'this.replaceState()'
                      L214  markStateUpdateScheduled

 enqueueForceUpdate   L223  update.tag = ForceUpdate
                      ★ **payload 를 안 건드린다**. 대입 자체가 없다
                      L234  'this.forceUpdate()'
                      L240  markForceUpdateScheduled
```

```text
 ★ instance 와 fiber 를 잇는 다리가 두 줄이다

 [02] constructClassInstance
   L605  instance.updater = classComponentUpdater
   L608  setInstance(instance, workInProgress)

 여기
   L168  fiber = getInstance(inst)

 => this.setState 는 React.Component 의 메서드가
    this.updater.enqueueSetState(this, ...) 를 부르는 것이고,
    그 updater 가 L605 에서 꽂힌 이 객체다.
    그리고 inst 에서 fiber 로 돌아오는 길이 L608 이 심어 둔 것이다
```

```text
 ★ root 가 null 이면 아무 일도 안 일어난다

 L181 / L207 / L233 의 `if (root !== null)` 이 세 줄을 전부 감싼다.
 스케줄도, 타이머도, 트랜지션 엮기도 그 안이다

 enqueueUpdate 가 null 을 돌려주는 경우는 하나다 -
   UPD L229-231  fiber.updateQueue === null
   주석 UPD L230 - "Only occurs if the fiber has been unmounted."

 => 언마운트된 컴포넌트에 setState 하면 업데이트 객체는 만들어지고
    조용히 버려진다. 경고가 없다
    ([업데이트 큐 02](../../update-queue/02_enqueue/README.md)에 그 자리가 있다)

 ★ 그런데 markStateUpdateScheduled (L187-189)는 그 if **밖**이다.
   root 가 null 이어도 프로파일러 마커는 찍힌다
```

```text
 ★★ 생명주기 안의 this.state = x 를 React 가 번역한다

 callComponentWillMount  L705-726
 L706  oldState = instance.state
 L708  componentWillMount 가 함수이면 L709 부른다
 L711  UNSAFE_componentWillMount 가 함수이면 L712 부른다
 L715  oldState !== instance.state 이면        (직접 대입했다는 뜻이다)
 L717    [__DEV__] console.error('... Assigning directly to this.state is
                    deprecated (except inside a component's constructor).
                    Use setState instead.')
 L724    classComponentUpdater.enqueueReplaceState(instance, instance.state, null)

 ★ 경고만 DEV 이고 **변환은 프로덕션에서도 일어난다**.
   L724 가 __DEV__ 블록 밖이다

 callComponentWillReceiveProps (L728-758)도 같은 모양인데 셋이 다르다
   L742  비교 피연산자 순서가 반대다  `instance.state !== oldState`
   L746  경고를 컴포넌트 이름당 한 번만 찍는다
         (didWarnAboutStateAssignmentForComponent Set)
   반면 L715 쪽은 Set 이 없어 **매번** 찍는다
```

```text
 ★★ 그런데 이 번역이 모든 길에서 일어나지는 않는다

 헬퍼를 거칠 때만이다
   [03] mountClassInstance   L836  callComponentWillMount  -> 잡는다
   [04] resume / update      L902 / L1050
        callComponentWillReceiveProps                      -> 잡는다

 [04] resumeMountClassInstance 는 componentWillMount 를 **인라인으로** 부른다
   L965  if (typeof instance.componentWillMount === 'function') {
   L966    instance.componentWillMount();
   L968-970  UNSAFE_ 쪽도 인라인
   L972  바로 다음 줄이 componentDidMount 플래그다

 => 이어서 마운트하는 길에서 componentWillMount 안에 this.state = x 를 쓰면
    경고도 못 받고 ReplaceState 변환도 못 받는다.
    같은 길에서 processUpdateQueue 도 안 불린다 ([03] L839 와 다르다)
```

```text
 ReplaceState tag 가 실제로 쓰이는 자리가 이 둘뿐이다

 L724  callComponentWillMount 의 직접 대입 변환
 L756  callComponentWillReceiveProps 의 직접 대입 변환

 공개 this.replaceState 가 없기 때문이다 -
 react/src/ReactBaseClasses.js L101-102 의 deprecatedAPIs 에 'replaceState' 가
 들어 있다 (경고하고 undefined 를 돌려주는 getter 다)

 => 그래서 enqueueReplaceState 의 callback 블록(L199-204)은 **[DEAD]** 다.
    두 호출처가 모두 null 을 넘긴다.
    시그니처의 `callback: null`(L191)이 타입 실수가 아니라 정확한 기술이다
```

```text
 세 메서드의 callback 처리가 같다

 L173 / L199 / L225  callback 이 undefined 도 null 도 아니면
 L175 / L201 / L227    [__DEV__] warnOnInvalidCallback(callback)
 L177 / L203 / L229    update.callback = callback

 셋 중 가운데 것만 도달 불가다 (위 [DEAD] 블록 참고)
```

## 결과가 쓰이는 곳

```text
 update.tag
      --> [업데이트 큐 04] getStateFromUpdate 의 switch 가 가른다
      --> ForceUpdate 는 payload 가 없어도 된다. 상태를 안 바꾸니까

 update.callback
      --> queue.callbacks 에 쌓이고 커밋 레이아웃 패스에서 불린다

 반환 root
      --> scheduleUpdateOnFiber 의 인자
      --> null 이면 업데이트가 버려진다

 lane
      --> entangleTransitions 가 트랜지션이면 엮는다
      --> [lane 우선순위]가 그 lane 을 어떻게 고르는지 다룬다
```

## 다루지 않는 것

`getInstance` / `setInstance`(`ReactFiberTreeReflection`)가 instance 에 fiber 를 저장하는 방식, `requestUpdateLane` 이 lane 을 고르는 규칙([lane 우선순위](../../lanes/README.md)에 있다), `startUpdateTimerByLane`(`ReactProfilerTimer`)과 `enableSchedulingProfiler` 마커(`markStateUpdateScheduled` / `markForceUpdateScheduled`)의 본문, `warnOnInvalidCallback`(L95)의 검사 내용, `entangleTransitions`(UPD L276)의 트랜지션 엮기, `React.Component.prototype.setState`(`react` 패키지)가 `this.updater` 를 부르기까지의 얇은 층은 같은 뼈대의 곁가지라 요약만 했다.
