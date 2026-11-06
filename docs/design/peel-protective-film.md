# 보호필름 벗기기 태스크 시뮬레이션 설계

작성 2026-11-06 · 상태: 구현·GPU 검증·미디어 업로드 완료 (PR 미제출)

## 구현 검토 업데이트 (2026-11-06)

아래 본문은 최초 초안입니다. 현재 작업 코드는 `tasks/peel-protective-film/`에 있으며,
다음 사항은 본문보다 우선합니다. 상세 근거는 [진행 감사표](peel-protective-film-status.md)에 있습니다.

- 최신 공개 PR 조사에서 #588 **Split a lamp cord apart to the white band**가 발견됐습니다.
  양팔로 전선을 연속 분리하므로, 순차 파단 자체는 새로운 아이디어라고 주장하지 않습니다.
  차별점은 자유롭게 움직이는 금속판의 지지와 표면 접착 필름의 박리·정리입니다.
  로그인된 공식 보드 701개(승인 17, 대기 582, 수정 중 12, 이전 기수 계획 90)를
  확인했고 직접적인 보호필름 제거 과제는 발견되지 않았습니다. 승인 보장은 아닙니다.
- 방향 무관 3 N 파단 대신 **박리 선두의 상향 회전만 허용하는 접착 힌지**를 사용합니다.
  각도 스프링 0.03 N·m/rad, 선두 띠가 60° 열리면 해제, 판정은 제어 주기 20 Hz입니다.
  물성 실측에 맞춰 보정한 모델은 아닙니다. GPU에서 압박·전단 시 미박리와
  상향 박리 시 순차 해제를 확인했습니다.
- 판은 팔 간섭을 줄이기 위해 350×100×1 mm, 280 g으로 변경했습니다. 중심은
  (0.28, −0.01, 0.7480), 필름 위치는 그대로이며 지지 위치는 (0.30, 0.14)입니다.
  560 g 버전에서는 지지 없이도 성공해 1 mm 판으로 변경했습니다. 280 g 버전의
  단팔 실행은 판 이동 제한을 넘어서 0점으로 끝났습니다.
- 탭 각도 유지 스프링은 조작 이후 필름이 손가락에 걸리는 현상을 줄이기 위해
  최대 토크를 0.0002 N·m로 제한했습니다. 힘 제한 없는 스프링을 실제 얇은 PE의
  접힌 자국과 같다고 간주하지 않습니다.
- 파단 개수는 trial 동안 유지합니다. 필름을 제자리로 가져와도 재접착으로 판정하지 않습니다.
- 판의 30 mm 수평 이동, 5 mm 수직 이동, 10° yaw 또는 tilt 이탈은 trial 내내 추적하며,
  한 번 위반하면 복귀해도 0점입니다.
- 완료는 전체 필름이 판 밖 2 mm 여유를 두고 테이블에 지지된 채 정지하고,
  모든 조각이 테이블 위 30 mm 이내에 있으며 양손 TCP가 판과 필름에서 80 mm 이상
  물러난 상태가 1초 유지돼야 합니다. 접힌 탭이 조금 서 있는 상태는 허용합니다.
- 확대된 배치의 데모는 IK 오차 0.1 mm 이내이며, 20 Hz로 검사한 팔 껍데기에서
  기존 겹침이 사라졌습니다. 이 오프라인 근사는 실제 접촉 검증을 대신하지 않습니다.
- 최종 코어 hash `252f2275…`에서 CPU 테스트 31개, 정지·압박·전단·단팔 baseline이
  통과했습니다. 같은 소스의 양팔 데모는 reset 3회 모두 704스텝에 1.0점입니다.
  정리할 때 필름을 펼쳐 내려놓으며, 1초 정착을 scorer 자체에서 확인해 시간 제한
  직전의 순간 만점도 방지합니다.
- 표준 녹화 데모는 704스텝 1.0점(실제 102.6초), Dream-1은 2,400스텝 0.0점
  (실제 315.1초, 정상 실행 후 스텝 제한 종료)입니다.
- 두 H.264 영상과 시작 스크린샷 업로드가 완료됐고 media ID는 `M-F2ULE4`입니다.
  실제 PR 생성·제출은 하지 않았습니다. 과거 실패 이력은 진행 감사표에 보존합니다.

> 팀 내부 설계 메모입니다. 제출 PR에는 넣지 않습니다. PR은 `tasks/<task-name>/` 폴더 하나만 바꿔야 하고,
> 이 저장소와 포크는 공개라서 제출 전에 아이디어가 드러나면 다른 팀이 먼저 낼 수 있습니다.

스테인리스 판(170×100×2 mm)에 붙은 파란 보호필름을 세워 둔 탭부터 끝까지 벗기는 양팔 task입니다.
한 팔은 판을 눌러 잡고, 다른 팔은 필름을 낮게 뒤로 젖혀 당깁니다. 필름은 탭 1개와 10 mm 강체 띠 13개로 만들고,
띠마다 3 N에서 끊어지는 관절로 접착을 근사합니다. 물체가 15개뿐이라 연산 부담은 없고, 구현은 PR #531(종이타월
찢기)과 같은 scene 패치 방식입니다.

## 1. 태스크 정의

로봇은 판을 움직이지 않은 채 보호필름 130 mm를 탭부터 끝까지 떼어 판 밖에 내려놓아야 합니다. 카테고리는
Impact on jobs로 둡니다.

- **지시문(초안):** Peel the blue protective film off the steel plate, starting from its raised tab, and put the
  film down off the plate. Keep the plate where it is.
- **실제 맥락:** 판금 부품은 용접, 절곡, 조립, 도장 전에 보호필름을 벗깁니다. 필름을 당기면 판도 딸려 오므로,
  한 손으로 판을 누르고 다른 손으로 필름을 낮게 젖혀 당깁니다.
- **양팔이 필요한 이유:** 박리력 약 3 N이 판의 마찰력(약 1.1 N, 270 g 판에 마찰계수 0.4 가정)보다 커서, 판을
  누르지 않으면 판이 끌려옵니다.
- **요구하는 능력:** 얇은 탭 집기, 일정한 각도와 속도로 당기기, 누르는 팔과 당기는 팔의 협조, 끝난 필름 치우기.

**기존 PR과의 차별점:** #1–#664 중 필름, 라벨, 껍질을 벗기는 task는 없습니다. 가장 가까운 #531(종이타월
찢기)은 절취선 한 곳을 한 번에 끊는 task입니다. 이 task는 박리 지점이 10 mm씩 13번 연속으로 이동하고, 판을
누르는 팔과의 협조가 필요합니다. LIBERO, RoboCasa 등 주요 공개 task set에서도 필름 박리 task는 본 적이 없지만,
제출 전에 한 번 더 확인해야 합니다.

## 2. 씬 구성

`station` 씬에 판 1개와 필름 조각 14개만 놓습니다. 좌표는 yam_arena 월드 좌표(x 앞, y 왼쪽, z 위, m)이고,
팔 베이스는 (0, ±0.305), 테이블 윗면은 z 0.7475입니다.

| 물체 | 시뮬레이션 형태 | 크기 (mm) | 질량 | 재질·색 | 위치 (중심, m) | 고정 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 스테인리스 판 | Box | 170 × 100 × 2, 긴 변이 좌우(y) | 270 g | 304 스테인리스, 회색, 마찰 0.4(가정) | (0.28, −0.10, 0.7485) | 놓아둠 |
| 필름 탭 | Box | 80 × 20 × 1 | 1.5 g | 파란 PE, 마찰 1.2 | 주름선 y −0.055, 판에서 70° 서 있음 | 띠 1과 관절 |
| 필름 띠 1–13 | Box × 13 | 80 × 10 × 1 | 각 0.74 g | 파란 PE | x 0.28, y −0.060 ~ −0.180 (10 mm 간격), z 0.7500 | 판에 접착 관절 |

- **필름 영역:** y −0.185 ~ −0.035 (150 mm) 중 왼쪽 20 mm가 탭이고, 나머지 130 mm가 붙어 있습니다. 판 왼쪽
  끝 20 mm에는 필름이 없어서, 탭을 세우면 맨 판이 y −0.055 ~ −0.015 (40 mm) 드러납니다.
- **판을 좌우로 놓는 이유:** 180° 가까이 젖혀 벗기면 손은 박리 길이의 2배(약 280 mm)를 움직입니다. 앞뒤(x)로
  벗기면 도달 범위(자기 베이스 앞 0.10–0.50 m, 중앙선에서는 0.40 m)를 벗어납니다.
- **동작 배치:** 오른팔이 필름을 −y(자기 베이스 쪽)로 당기며, 끝날 때 손 위치는 약 (0.28, −0.335)입니다.
  왼팔은 맨 판의 앞쪽 모서리 (0.315, −0.03)를 누릅니다. 모든 위치는 초안이고, 오프라인 IK 확인 후 확정합니다.
- **보이는 정도:** 320×176 상단 카메라는 픽셀당 약 5 mm라 탭이 4픽셀 정도입니다. 파란 필름과 회색 판의 대비로
  구분하고, 세부는 손목 카메라가 봅니다.

## 3. 필름·접착 모델

필름은 탭 1개와 강체 띠 13개를 경첩으로 잇고, 띠마다 판과 잇는 관절 하나가 3 N에서 끊어지게 해 접착을 흉내
냅니다. PhysX 천(cloth)은 찢기를 표현한 선례가 없고 느려서(#295) 쓰지 않습니다.

옆에서 본 단면입니다. 띠 3이 들리는 순간이며, 가로 4글자가 10 mm입니다(두께는 과장).

```text
    (1)                          (2)        (3)
     |                      o---o---o-------[G] ===> -y
     |                      |
     v                      | (4)
+-------------------x---x---V===V===V===V===V===V===V===V===V===V===V+
|                                                                    |
+--------------------------------------------------------------------+
+y end                                                          -y end
```

- `V` 판-띠 관절: 3 N에서 끊어짐. `(4)` 바로 아래 `V`가 지금의 박리 지점입니다.
- `o` 띠-띠 경첩: 끊어지지 않음
- `x` 이미 끊어진 관절 (띠 1, 2)
- `=` 아직 붙어 있는 띠 4–13 (각 10 mm)
- `(1)` 왼팔이 맨 판을 약 5 N으로 눌러, 판이 끌려가지 않게 함
- `(2)` 떨어진 띠 1·2와 탭. 뒤로 접혀 붙은 띠 위를 지나감
- `(3)` 오른팔 그리퍼 `[G]`가 −y로 당김. 손 속도는 박리 속도의 2배
- `(4)` 띠 3. 당기는 힘을 이 띠의 관절 하나만 받고, 3 N을 넘으면 끊어져 오른쪽 띠가 다음 박리 지점이 됨

붙어 있는 띠는 양쪽 가장자리가 모두 묶여 움직이지 않고, 맨 앞 띠만 자기 관절을 중심으로 돌 수 있습니다. 그
관절이 끊어지면 다음 띠가 박리 지점이 되고, PhysX는 끊어진 관절을 되살리지 않아 박리 길이는 줄지 않습니다.

| 항목 | 값 | 근거·메모 |
| --- | --- | --- |
| 물리·제어 주기 | 240 Hz 물리, 20 Hz 제어 (제어 1스텝에 물리 12번) | yam_arena 기본값 |
| 띠 | 80 × 10 × 1 mm, 각 0.74 g, 13개 | 실제 두께는 약 0.05 mm. 접촉 안정성을 위해 1 mm로 키움 |
| 탭 | 80 × 20 × 1 mm, 1.5 g | 잡기 어려우면 2 mm(접어 겹친 상태) |
| 판-띠 관절 | revolute, 축 x, 띠의 −y 가장자리, breakForce 3 N | 80 mm 폭 기준 약 0.94 N/25 mm. 저점착 필름 범위로 가정했고, 사양서 확인 필요 |
| 띠-띠 경첩 | revolute, 축 x, 각도 한계 ±175°, 끊어지지 않음 | 180° 가까이 접혀도 이웃 띠가 서로 파고들지 않게 함 |
| 탭 세움 | 탭-띠 1 경첩에 각도 드라이브, 목표 70°, 강성 약 0.01 N·m/rad | 탭 자중 토크(최대 약 0.00015 N·m)를 1° 안팎으로 버팀. 당기는 힘에는 거의 영향 없음 |
| 마찰 | 탭·띠 1.2/1.0, 판 0.4 | yam_arena는 모든 물체에 1.2/1.0을 주므로 판은 따로 지정. 테이블 재질값 확인 필요 |
| 접촉 | contact offset 5 mm, rest offset 0 | yam_arena 기본값 |
| solver iteration | 판·띠 32회 (가정) | 정착 테스트로 조정 |

- **연산량:** 몸체 15개, 관절 26개입니다. 구슬 101개를 쓴 #447도 문제없이 돌았으므로 부담은 없을 것으로 봅니다.
- **대안 모델 B:** 판-띠를 스프링(D6 관절의 직선 드라이브)으로 잡고, 매 제어 스텝 코드가 판에서 떨어지는
  방향의 변위만 보고 일정 값을 넘으면 관절을 끕니다. 힘의 방향을 구분하지만, 끊는 판정이 20 Hz로만 일어납니다.

## 4. 채점

점수는 붙어 있던 130 mm 중 탭 쪽부터 연속으로 떨어진 길이로 매기며, 판이 제자리에 있어야만 점수가 납니다.
실제 환경에서도 자와 사진만으로 똑같이 판정할 수 있습니다.

| 결과 | 조건 | 점수 |
| --- | --- | --- |
| 판 이탈 | 끝났을 때 판이 시작 위치에서 30 mm 넘게 움직임, 10° 넘게 기울어짐, 또는 테이블 밖 | 0 |
| 거의 못 벗김 | 박리 길이 30 mm 미만 | 0 |
| 시작 | 30 mm 이상 | 0.25 |
| 절반 | 70 mm 이상 | 0.5 |
| 대부분 | 110 mm 이상 | 0.75 |
| 완료 | 130 mm 전부 떨어짐, 판 위에 놓인 필름 없음 | 1.0 |

**시뮬레이션에서 재는 방법**

- **띠가 떨어졌다는 판정:** 띠의 접착선(−y 쪽 가장자리 중점)이 판 기준 원래 자리에서 3 mm 넘게 벗어나면 떨어진
  것입니다. 붙어 있는 동안 이 선은 관절에 묶여 움직이지 않으므로, 움직였다면 관절이 끊어진 것입니다.
- **박리 길이:** 탭 쪽부터 연속으로 떨어진 띠 수 × 10 mm입니다.
- **판 위에 필름 없음:** 모든 조각의 가장 낮은 점이 판 윗면보다 5 mm 이상 높거나, 중심이 판의 xy 범위 밖이면
  됩니다.
- **판 조건:** 판의 위치와 기울기는 ObjectState의 위치와 쿼터니언으로 계산합니다.
- **종료와 점수 기준:** 1.0 조건이 1초 유지되면 `success()`가 에피소드를 끝냅니다. 끊어진 관절은 다시 붙지 않아
  박리 길이는 줄지 않으므로, `SCORE_OVER`는 기본값 `end`로 둡니다.
- **실제 환경:** 자로 주름선부터 필름이 아직 붙은 첫 지점까지 잽니다. 판 위치는 테이블에 붙인 테이프 표시와
  사진으로 확인합니다.

**막아야 할 편법**

| 편법 | 막는 방법 |
| --- | --- |
| 필름째로 판을 끌거나 들어 올림 | 판이 30 mm 넘게 움직이거나 10° 넘게 기울면 0점 |
| 떼어낸 필름을 판 위에 다시 내려놓음 | 1.0은 판 위에 필름이 없어야 함 |
| 그리퍼로 중간 띠를 밀거나 눌러 관절을 끊음 (시뮬레이션에서는 힘의 방향과 관계없이 끊어지는 점을 이용) | 탭부터 연속된 띠만 셈 |
| (실제 환경) 필름이 찢어져 조각이 남음 | 남은 조각이 있으면 그 지점이 박리 끝, 1.0 불가 |

## 5. 스크립트 데모

데모는 약 27초(약 540스텝)에 1.0을 목표로 합니다. `--policy yam_scripted`가 재생하는 개루프 웨이포인트이므로
`-E object_jitter=0`으로 돌립니다. 높이는 판 윗면(z 0.7495) 기준입니다.

| 단계 | 시간 (s) | 오른팔 (벗기기) | 왼팔 (누르기) |
| --- | --- | --- | --- |
| 1 | 0–3 | 탭 위 (0.28, −0.062, +0.08)로 이동, 손가락 30 mm만 벌림, yaw 0 | 대기 |
| 2 | 3–5 | TCP +0.016까지 내려가 손가락을 닫아 탭을 잡음 | (0.315, −0.03, +0.06)로 이동 |
| 3 | 5–6.5 | 유지 | 손가락을 닫은 채 내려가, 목표를 접촉면보다 3 mm 아래로 두어 판을 누름 |
| 4 | 6.5–21 | 높이 +0.02–0.03을 유지하며 y −0.062에서 −0.335까지 초속 2 cm로 당김 (박리 각 약 170°, 박리 속도 초속 1 cm) | 누름 유지 |
| 5 | 21–24 | 필름을 +0.10까지 들어 (0.20, −0.30) 위로 옮기고 내려놓아 놓음 | 누름 유지 |
| 6 | 24–27 | READY 복귀 | READY 복귀, 1초 성공 유지 후 종료 |

- **잡는 높이:** 패드 끝은 TCP보다 13 mm 아래에 있어, TCP +0.016에서 패드 끝이 필름 윗면보다 약 2 mm 높습니다.
  탭 윗끝(+0.019)까지 약 17 mm를 물게 됩니다.
- **손가락을 30 mm만 벌리는 이유:** 끝까지 열면 패드 간격이 94 mm가 되어 옆의 왼팔과 부딪힙니다. 손가락 관절
  목표는 −0.015 m입니다.
- **누르는 힘:** 판을 잡아두려면 약 1.2 N 이상이면 됩니다(그리퍼-판 마찰 1.2, 판-테이블 마찰 0.4 가정). 여유를
  두어 5 N을 목표로 하고, 3 mm 아래 목표가 실제로 내는 힘은 시뮬레이터에서 잽니다.
- **오프라인 확인:** `yam_arena.demo.ArmPlan`으로 모든 웨이포인트의 IK와 관절 한계를 확인합니다.
  `yam_arena.analysis`의 링크 충돌 껍데기로 두 그리퍼의 최소 간격도 확인합니다. 둘 다 GPU는 필요 없습니다.

## 6. 구현 구조

yam_arena는 수정하지 않고, task 폴더 안의 `filmkit.py`가 import 훅으로 관절과 재질만 더합니다. #140, #531을
비롯해 약 240개 PR이 같은 방식을 씁니다.

```text
tasks/peel-protective-film/
  task.json          제출 정보 (영어)
  README.md          실행·채점 명령, trial당 시간, 시드
  task.py            SCENE, OBJECTS, success/score/distance, demo
  filmkit.py         관절·재질 작성, 리셋 때 관절 재활성화
  tests/
    test_scoring.py    점수 구간별 가상 상태 테스트
    test_demo_plan.py  IK·관절 한계·두 팔 간격
    test_task_json.py  필수 필드와 글자 수 제한
```

1. **물체 선언:** `task.py`의 OBJECTS에 판, 탭, 띠 1–13을 이 순서로 둡니다. 뒤에 생기는 몸체가 자기 관절을
   만들기 때문에 순서가 중요합니다.
2. **훅:** `filmkit.py`를 import하면, `yam_arena.scene`이 처음 로드될 때 `task_object`를 감쌉니다. 필름과 판은
   우리 spawner로 만들어 rigid body의 prim 경로를 알 수 있게 합니다(#531과 같은 구조).
3. **spawner가 하는 일:** 상자 형상, 질량, 마찰 재질, solver iteration을 설정합니다. 그리고 이미 생긴 이웃과의
   `UsdPhysics.RevoluteJoint`를 만듭니다. 판-띠 관절에는 `breakForce`, 탭-띠 1 관절에는 각도 드라이브를 넣습니다.
4. **리셋:** PhysX는 끊어진 관절을 되살리지 않습니다. 그래서 임바디먼트의 `reset()`을 감싸, 리셋 직후 각 관절의
   `jointEnabled`를 끄다 켜서 다시 만듭니다(#531의 방식).
5. **상태 읽기:** 채점은 yam_arena가 넘겨주는 ObjectState(위치, 쿼터니언, 바운딩 박스)만 씁니다. 우리 spawner로
   만든 몸체에서도 값이 맞는지 확인해야 합니다.

PR #531의 `bodykit.py`는 라이선스 표기가 없으므로 구조만 참고하고 코드는 직접 작성합니다. 라이선스가 없는 코드를
그대로 쓰면 저작권 문제가 생길 수 있습니다.

## 7. 검증 계획

GPU 없이 되는 확인을 먼저 끝낸 뒤 시뮬레이터를 돌립니다. 가장 먼저 볼 것은 "정착·누름·스침에는 안 끊기고,
당기면 탭 쪽부터 하나씩 끊기는지"입니다.

**GPU 없이 (pytest)**

- [ ] `yam_arena.task_file.load`로 task.py가 열리고, 이름이 예약어(`table`, `left_robot` 등)와 겹치지 않음
- [ ] 채점: 각 점수 구간, 중간 띠만 끊긴 경우, 판 이탈 0점, 필름이 판 위에 남은 경우를 가상 ObjectState로 테스트
- [ ] 데모: 모든 웨이포인트의 IK와 관절 한계(`ArmPlan`), 두 그리퍼의 최소 간격(`yam_arena.analysis`)
- [ ] task.json: 필수 필드, category 값, fidelity ≤ 500자, instruction·context ≤ 1000자, scores ≤ 300자

**시뮬레이터 (Isaac Sim, L40S 또는 로컬 RTX)**

- [ ] 정착: 아무것도 하지 않고 10초 둘 때 끊는 관절 0개, 띠 이동 1 mm 미만, 탭이 70° 근처 유지
- [ ] 누름: 왼팔이 맨 판을 5 N으로 눌러도 끊는 관절 0개, 판 미끄러짐 없음
- [ ] 스침: 그리퍼가 붙은 필름을 스치거나 가볍게 눌러도 끊지 않음
- [ ] 박리 순서: 170°, 135°, 90°로 일정하게 당길 때 띠가 탭 쪽부터 하나씩 떨어짐
- [ ] 양팔 필요성: 누르지 않고 한 팔로 당기면 판이 30 mm 넘게 끌려옴
- [ ] 아무것도 안 하는 정책(`hold`)은 0.0, 판을 끌고 가는 스크립트도 0.0
- [ ] 스크립트 데모 1.0, `--epochs 3`으로 두·세 번째 trial도 같은 결과 (관절 재활성화 확인)
- [ ] 스텝당 시간 측정: Dream-1 요청 사이 간격이 8초를 넘지 않음 (넘으면 Dream 세션이 끊김, #295 참고)
- [ ] Dream-1 2,400스텝 실행, 카메라별 MP4 렌더링, 보정된 상단 카메라로 스크린샷

## 8. task.json 초안

글자 수는 모두 봇의 제한 안입니다: fidelity 377/500, instruction 145/1000, context 263/1000, scores 27/300.
`scores`와 `media`는 실행 후에 채웁니다. 심사는 블라인드라서 팀을 알 수 있는 내용은 넣지 않습니다.

```json
{
  "title": "Peel the protective film off a steel plate while holding the plate down",
  "category": "Impact on jobs",
  "keywords": ["bimanual", "peeling", "adhesive film", "sheet metal", "hold-down", "assembly prep"],
  "instruction": "Peel the blue protective film off the steel plate, starting from its raised tab, and put the film down off the plate. Keep the plate where it is.",
  "context": "Before welding, bending, assembly or painting, workers peel the protective film off sheet-metal parts. The film pulls the plate along as it comes off, so one hand has to hold the plate down while the other peels from the tab, keeping the film low and folded back.",
  "setup": "Positions are on the table from the midpoint between the two arm bases: forward is away from the arms, left and right as seen from behind the arms. A brushed 304 stainless steel plate, 170 x 100 x 2 mm (about 270 g), lies flat and loose with its long side running left-right, centred 28 cm forward and 10 cm right. Blue low-tack polyethylene protective film, 80 mm wide and about 0.05 mm thick, is stuck to its top face, centred across the width, from the plate's right end to 20 mm short of its left end. The film's last 20 mm at its left end is not stuck: it is creased up to stand about 70 degrees from the plate, leaning over the stuck film, as a pull tab. Nothing else is on the table.",
  "scoring": "Peeled length is measured along the plate from the tab's crease to the nearest point where the film is still stuck. Any score needs the plate to end flat on the table (tilted under 10 degrees) within 30 mm of where it started; otherwise 0. 0.25 at 30 mm peeled or more; 0.5 at 70 mm; 0.75 at 110 mm; 1.0 when all 130 mm is unstuck and no part of the film rests on the plate.",
  "run_limit": "2,400 steps (2 minutes at 20 Hz)",
  "reset_notes": "The film is used up: stick a new film on for every trial, pressed flat from the right end, and crease its tab as in the setup.",
  "fidelity": "Approximate, in Isaac Lab-Arena (Isaac Sim 6.1, PhysX at 240 Hz) on the calibrated YAM station. The film is a 20 mm tab and thirteen 10 mm rigid strips, 1 mm thick, joined by hinges: it bends only at the joins and cannot stretch, wrinkle or tear. Its stick is one PhysX joint per strip that breaks at 3 N, the same at any peel angle. The plate is a rigid box with set friction.",
  "scores": "Dream-1 run: TBD; demo: TBD",
  "media": "M-XXXXXX"
}
```

## 9. 위험과 결정할 사항

가장 큰 기술 위험은 관절이 힘의 방향과 관계없이 끊어지는 점이고, 심사 위험은 단순화된 필름 모델에 대한
지적입니다.

| 위험 | 영향 | 대응 |
| --- | --- | --- |
| 관절이 힘의 방향과 관계없이 끊어져, 누르거나 스치기만 해도 박리로 잡힘 | 점수가 실제와 달라짐 | 탭부터 연속인 띠만 셈. 임계값을 우발 하중보다 높게 둠. 그래도 문제면 접착 모델 B로 전환 |
| 같은 선 위에 겹친 두 관절이 떨림을 일으킴 | 정착 실패, 우발 파단 | solver iteration을 올리고 정착 테스트로 확인. 안 되면 붙은 띠는 fixed 관절 하나로 단순화 |
| 1 mm 탭을 잡지 못하거나 미끄러짐 | 데모 실패 | 탭만 2 mm(접어 겹친 상태)로, 마찰 1.2, 손가락은 30 mm만 벌림 |
| 두 그리퍼가 가까워 부딪힘 | 데모 실패 | 누르는 위치를 x 0.315로 띄움. 오른팔이 먼저 잡고 왼팔이 나중에 누름. 간격은 오프라인으로 확인 |
| 도달 범위 밖 | 데모 불가 | IK로 배치를 먼저 확정한 뒤 시뮬레이터 실행 |
| 강체 띠와 각도 무관 접착이 실제와 다르다는 지적 | 반려 | fidelity에 명시. 채점은 박리 길이만 쓰므로 이 단순화의 영향이 작음 |
| scene 패치 허용 여부가 공식적으로 불분명 (#212 질문에 답 없음) | 규칙 위험 | 약 240개 PR이 같은 방식. 필요하면 주최 측에 문의 |
| 다른 팀이 비슷한 아이디어를 먼저 제출 | 중복으로 불인정 | 제출 직전 보드와 새 PR을 확인하고 빨리 제출 |

**정해야 할 선택지**

| 결정 | 선택지 | 권장 |
| --- | --- | --- |
| 1. 판 고정 | A 놓아두고 다른 팔이 누름 / B 코너 스톱(지그)에 대고 한 팔로 벗김 | A. 양팔 협조가 핵심이고, 데모가 불안정하면 B |
| 2. 띠 길이 | 10 mm (몸체 15개, 관절 26개) / 5 mm (몸체 28개, 관절 52개) | 10 mm로 시작하고, 굽힘이 너무 각지면 5 mm |
| 3. 접착 모델 | A 일정한 힘에서 끊어지는 관절 / B 스프링으로 잡고, 코드가 당기는 방향의 변위만 보고 끊음 | A. 선례(#531)가 있고 단순함. 방향 문제가 실제로 나타나면 B |
| 4. 떼어낸 필름 | 판 밖 아무 곳 / 지정 트레이 | 판 밖. 단계를 늘리지 않음 |
| 5. 탭 모양 | 필름 전폭 탭 / 모서리 탭 | 전폭. 모서리 탭은 띠 대신 2차원 격자가 필요함 |

## 10. 출처

- [yam-isaac-lab-arena](https://github.com/kairosiann/yam-isaac-lab-arena): 팔·그리퍼 상수, 접촉 설정, task 파일
  API, 도달 범위, 카메라 렌즈값 (commit bd62771, 2026-11-01)
- [PR #531](https://github.com/robocurve/benchmark-tasks/pull/531): 끊어지는 관절(3 N)과 리셋 때 관절 재활성화
- [PR #140](https://github.com/robocurve/benchmark-tasks/pull/140): `yam_arena.scene`을 감싸는 import 훅
- [PR #295](https://github.com/robocurve/benchmark-tasks/pull/295): PhysX 천(cloth) 사용 사례와 Dream 세션 8초 끊김
- [PR #212](https://github.com/robocurve/benchmark-tasks/pull/212): scene 패치 허용 여부에 대한 참가자 질문
- 저장소의 [AGENTS.md](../../AGENTS.md): 제출 절차와 심사 기준 5가지
- 확인하지 못한 값: 보호필름 점착력(저점착 약 1 N/25 mm로 가정)과 강철-나무 마찰계수(0.4로 가정)는 실측이나
  제품 사양서로 확인해야 합니다.
