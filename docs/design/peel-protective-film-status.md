# 필름 벗기기 — 최종 진행 감사표

내부 기록 · 2026-11-06 06:01 UTC / 15:01 KST · 실제 PR 미생성

**요청한 실제 PR 제출 직전 준비가 완료됐다. 현재 확인된 잔여 블로커는 없다.**

현재 코어 SHA-256: `252f227537177e1f66e376d91265b3441fe49402e83f0bfed5e1074b2c34dc3f`.

## 완료

| 항목 | 확인 결과 | 근거 |
|---|---|---|
| 구현·회귀 검증 | CPU 31개 통과. scorer 자체에서 1초 정착을 누적하며 중단 시 초기화 | `/tmp/film-validation/run-Djrv4qr6/tests.log` |
| 부정 baseline | hold 200, press 400, shear 400 steps: 박리 0개·점수 0·무효 아님 | `artifacts/validation/{hold,press,shear}/0-summary.json` |
| 단팔 baseline | 740 steps, 박리 4개, 판 이동으로 무효·점수 0 | `artifacts/validation/single/0-summary.json` |
| 반복 demo | reset 3회 모두 704 steps, 1.0점, success true, invalid false | `artifacts/validation/demo/{0,1,2}-summary.json` |
| 표준 scripted 실행 | 704 steps, 1.0점, 102.553 s, 실행 오류 0 | `artifacts/scripted/adhoc_73167f85.json` |
| 표준 Dream-1 실행 | 2,400 steps, **0.0점**, 315.073 s, max_steps 종료, 실행 오류 0 | `artifacts/dream/adhoc_2528a94e.json` 및 하위 record.json |
| 미디어 | demo·Dream H.264 MP4와 setup.png 준비·시각 검토·업로드 완료 | `artifacts/{demo.mp4,model_run.mp4,setup.png}`, media **M-F2ULE4** |
| 보드 중복 | 인증된 공식 보드 701개에서 직접 보호필름 제거 중복 발견 없음 | `artifacts/novelty-report.json`, submission_watch의 공식 `/api/tasks` 검토 |
| 제출 metadata | task.json 필수 필드 전부 존재, 실제 점수·media 일치. README에 환경·실행·채점·시간·seed·한계 명시 | `task.json`, `README.md` |
| 제출 파일 범위 | task 폴더 하나의 코드·문서·테스트 14개만 staged. 내부 docs와 artifacts 제외 | `git diff --cached --name-only`, `.gitignore` |

표의 `artifacts/` 경로는 `tasks/peel-protective-film/artifacts/` 기준이다. 전체 suite는 `/tmp/film-validation-final.log`와 모든 summary를 감사했고 부모가 정상 exit 0을 확인했다.

Dream 결과의 `status success`는 실행 파이프라인 정상 종료를 뜻하며 **태스크 성공이 아니다**. 실제 태스크 점수는 0.0이다. 단팔 검사는 해당 scripted baseline의 실패를 입증하며 모든 단팔 전략의 불가능성을 증명하지 않는다.

## 근거 일치 최종 감사

- 현재 코어, `artifacts/source/` 스냅샷, `artifacts/manifest.json`, 표준 scripted/Dream 로그의 `environment_revision`이 위 전체 hash와 정확히 일치한다.
- 보존된 GPU summary 7개(hold/press/shear/single/demo 3개) 모두 같은 hash 및 `source_unchanged=true`다.
- demo.mp4: H.264, yuv420p, 960×352, 20 fps, 35.25 s, **1,314,214 bytes**.
- model_run.mp4: H.264, yuv420p, 960×352, 20 fps, 120.05 s, **5,988,397 bytes**. 두 영상 모두 50 MB 미만이다.
- 영상 2개와 setup.png의 실제 파일 크기·SHA-256이 manifest와 일치한다. task.json과 manifest의 media가 모두 `M-F2ULE4`다.
- 원본 `tools/upload_media.py`로 업로드 성공·exit 0을 부모가 확인했다. root 업로드 스크립트는 수정하지 않았다.
- setup.png는 감사자가 직접 시각 검토했다. 부모가 demo 영상 및 Dream 시작·중간·종료 화면을 검토했고 팀 식별 문구가 없음을 확인했다.
- 오프라인 20 Hz 경로 검사에서 팔 hull 겹침이 발견되지 않았고 IK 오차는 0.1 mm 미만이었다(`/tmp/film-layout-clearance.log`, 부모 설명). 정밀 충돌 보증은 아니다.
- 근접 아이디어 #588 램프전선 분리와 #531 종이타월 절취는 pending이다. 순차 분리 자체를 신규성으로 주장하지 않는다. 보드 검토는 확인 시점의 결과이며 승인 보장은 아니다.

## 진행 중 / 외부 정보 대기

- 구현·검증·미디어 업로드의 미완료 항목은 없다.
- Dream 및 팀 보드·업로드 자격증명은 모두 인증됐다. 외부 정보 대기는 없다. 감사자는 토큰을 읽거나 기록하지 않았다.
- submission_watch는 이후 새 submitted/accepted 변화를 감시한다. 새로운 중복이 생기면 상태를 다시 검토한다.

## 남은 순서와 범위

실제 제출을 시작할 때 현재 staged 파일을 커밋하고 등록된 GitHub 계정으로 push·PR 생성한다. **이번 요청 범위에서는 실제 PR을 열지 않는다.** 내부 설계·상태표, credentials, ignored artifacts는 PR에 넣지 않는다. 현재 staged 파일에는 task 폴더 밖 파일이 없다.

## 이전 검증 이력

현재 검증 완료와 구분해 실패 원인을 보존한다.

- `88c499832663b5711d02938d98ba6447fb5ce28b7fa666a8896d98c1e89dde03`: `/tmp/film-validation/run-GR1zENnb`. CPU 29개 및 hold/press/single 통과. demo 3회 모두 740 steps·0.75점으로 정착 실패, 전체 suite assertion 실패. 필름 13개는 분리됐으나 잔여 회전·이동이 있었다.
- `ed447417e18254fff8050e5a99bc4080420a7f4ff7adedcea9bda8164e2a0222`: 펼쳐 내려놓는 경로로 `/tmp/film-layout-demo/0-summary.json`에서 704 steps·1.0점. `/tmp/film-validation/run-s7CAUth8`은 hold/press 후 shear 도중 중단됐다. 성공 종료 대기와 순간 점수의 차이를 발견해 현재 버전은 scorer 자체 1초 정착으로 보강했다.
- 더 이전 560 g 판은 단팔도 1.0을 받아 280 g 판으로 변경했다. 이전 소스의 708-step 만점 및 thin-single 0점 실험은 현재 결과의 대체 근거로 사용하지 않았다.

감사 subagent는 기존 코드·로그·산출물을 읽고 이 상태표만 수정했다. 새 테스트, 시뮬레이터 조작, 제출 코드 수정, 외부 검색은 수행하지 않았다.
