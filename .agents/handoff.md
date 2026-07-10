# Agent Handoff: Anything_to_PDF

## 목적

Windows에서 여러 파일을 받아 PDF로 변환하고 지정된 순서로 하나의 PDF에 병합하는 PyQt6 GUI 프로그램을 완성·배포한다. 다른 컴퓨터, 다른 실행 환경, 다른 에이전트가 이 문서만 읽어도 현재 상태와 다음 작업을 즉시 이어갈 수 있어야 한다.

## 현재 상태

- 저장소: `https://github.com/manbavaran/Anything_to_PDF.git`
- 로컬 작업 폴더: `C:\Users\sucy\Desktop\Anything_to_PDF`
- 브랜치: `main`
- 최신 push 커밋: `73f87f1 한국어 UI 및 인수인계 문서 업데이트` (이 문서 수정 후 새 커밋으로 갱신 예정)
- 원격: `origin`이 위 GitHub 저장소를 가리킴
- 지원 형식: PDF, PNG, JPG, JPEG, WEBP, HWP, HWPX, DOC, DOCX, PPT, PPTX
- UI: 한국어로 변경 완료
- 로컬 단일 실행 파일: `dist\AnythingToPDF.exe` (생성물은 `.gitignore` 대상이며 GitHub에는 push하지 않음)

## 왜 이렇게 구현했는가

1. 이미지 변환은 Pillow로 처리한다. 외부 Office 설치 없이 로컬에서 안정적으로 동작하고 WEBP도 지원한다.
2. 기존 PDF는 재변환하지 않고 현재 목록 순서대로 직접 병합한다. 불필요한 품질 저하를 피하기 위한 결정이다.
3. 새 파일은 기본적으로 이름순 정렬하지만, 사용자가 드래그 또는 위/아래 이동 버튼으로 최종 순서를 바꿀 수 있다.
4. HWP/HWPX는 한컴오피스가 있을 때만 고품질 변환으로 표시한다. LibreOffice는 실험적 대체 경로이며, 둘 다 없으면 `rhwp-python` 렌더링 fallback을 사용한다.
5. DOC/DOCX/PPT/PPTX는 Microsoft Office COM을 우선 사용하고, 없으면 LibreOffice를 대체 경로로 검색한다.
6. `simple-hwp2pdf`는 제거했다. 패키지 설명과 달리 실제 구현이 MS Word COM에 의존해 독립적인 HWP 변환 경로가 아니었기 때문이다.
7. 사용자가 실행할 때 혼동하지 않도록 버튼, 상태, 오류, 변환 엔진 라벨을 한국어로 번역했다. 파일 형식명과 외부 프로그램명(Pillow, LibreOffice 등)은 식별을 위해 유지한다.

## 주요 파일

- `main.py`: PyQt6 GUI, 드래그 앤 드롭, 파일 선택, 정렬·순서 변경, 한국어 UI, `--self-test`, `--ui-smoke-test`
- `converter.py`: 엔진 감지, 이미지/Office/HWP 변환, PDF 병합 및 임시 파일 정리
- `tests/smoke_test.py`: PNG/JPG/WEBP 3개를 PDF로 변환하고 3페이지로 병합하는 소스 스모크 테스트
- `tests/verify_exe.ps1`: `dist\AnythingToPDF.exe --self-test`를 실제 실행해 종료 코드 검증
- `tests/rhwp_fallback_test.py`: Office 프로그램을 강제로 끄고 rhwp로 HWP/HWPX를 PDF 변환·병합
- `requirements.txt`: 재현 가능한 Python 의존성 버전
- `setup.py`: cx_Freeze 폴더형 빌드 설정
- `README.md`: 사용자·개발자용 설치, 테스트, 빌드, 변환 제한 문서
- `.gitignore`: `.venv`, `build`, `dist`, `*.spec`, 캐시·임시 산출물 제외

## 새 Windows 환경에서 이어서 시작하기

```powershell
git clone https://github.com/manbavaran/Anything_to_PDF.git
cd Anything_to_PDF
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

소스 실행:

```powershell
.venv\Scripts\python main.py
```

## 검증 순서

```powershell
.venv\Scripts\python tests\smoke_test.py
.venv\Scripts\python main.py --self-test
$env:QT_QPA_PLATFORM='offscreen'; .venv\Scripts\python main.py --ui-smoke-test
.venv\Scripts\python -m py_compile main.py converter.py tests\smoke_test.py
```

단일 EXE 빌드 및 검증:

```powershell
.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --name AnythingToPDF main.py
powershell -ExecutionPolicy Bypass -File tests\verify_exe.ps1
```

출력은 `dist\AnythingToPDF.exe`이다. GUI 빌드라 `--self-test` 결과는 콘솔에 표시되지 않지만, `verify_exe.ps1`가 종료 코드 0을 확인한다.

## 이 작업에서 확인된 범위

- 통과: 이미지 변환, WEBP 변환, PDF 병합, 파일 순서 로직, 소스 self-test, UI smoke test, PyInstaller 빌드, 단일 EXE self-test
- 통과: 한국어 UI가 오프스크린 Qt 환경에서 정상 초기화됨
- 검증 완료: Office 프로그램을 강제로 끈 상태에서 rhwp fallback으로 실제 HWP 1페이지와 HWPX 3페이지를 변환하고 HWP→HWPX 순으로 4페이지 병합
- rhwp는 복잡한 표·글꼴·페이지 배치에서 layout overflow 경고나 원본과 다른 배치를 만들 수 있으므로 제출용 문서는 육안 비교가 필요하다.
- 미검증: 실제 DOC/DOCX/PPT/PPTX 변환. Office/Hancom이 설치된 환경과 없는 환경에서 별도 검증이 필요하다.
- 따라서 Office/Hancom 변환을 수정할 때는 해당 프로그램이 설치된 Windows PC에서 실제 샘플 파일로 별도 검증해야 한다.

## 다음 작업

1. Office 설치 PC에서 DOCX/PPTX 실제 변환과 출력 PDF를 확인한다.
2. LibreOffice 설치 PC에서 fallback 변환을 확인한다.
3. 한컴오피스 설치 PC에서 HWP/HWPX 레이아웃 보존을 확인한다.
4. 라이선스 문제가 없는 샘플 fixture를 추가해 회귀 테스트를 확장한다.
5. 필요하면 PyInstaller 빌드를 GitHub Actions release artifact로 자동화한다.

## Git 작업 규칙

```powershell
$git='C:\Users\sucy\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git status
& $git pull --ff-only origin main
& $git add .
& $git commit -m '작업 내용 요약'
& $git push origin main
```

빌드 결과물은 기본적으로 커밋하지 않는다. 사용자가 명시적으로 요구할 때만 `dist` 산출물을 별도로 다룬다.

## Latest Implementation Update

- Added `rhwp-python==0.8.1` as the third HWP/HWPX-to-PDF fallback.
- Conversion order is Hancom Office, then LibreOffice, then rhwp.
- `tests/rhwp_fallback_test.py` forces Hancom and LibreOffice off, converts the real test files `260519_업무공유현황_보충자료1.hwp` and `260519_업무공유현황_보충자료2.hwpx`, and merges them in HWP -> HWPX order.
- Verified fallback output: HWP 1 page + HWPX 3 pages = merged 4-page PDF.
- `results/` contains local generated fixtures and PDFs and is intentionally ignored by Git.
- A fallback-enabled single-file build was verified as `dist/AnythingToPDF_rhwp.exe`; the original output name was temporarily locked by Windows during one rebuild attempt.
- rhwp may emit layout-overflow warnings for complex tables; visually compare important documents against Hancom output.
- For future HWP creation/editing requests, use a user-scope HWP agent such as `claw-hwp`; do not create a new HWP-to-HWPX MCP inside this project.
