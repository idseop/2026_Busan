<!--
  📖 작업 전에 CONTRIBUTING.md 를 읽으셨나요?
  브랜치 네이밍 · 커밋 타입 · 병합 방식 · 충돌 방지 규칙이 거기 있습니다.
-->

## 무엇을

<!-- 이 PR 이 무엇을 바꾸는지 2~3줄 -->

## 왜

<!-- 왜 이렇게 했는지. 나중에 이 판단을 다시 볼 사람을 위해 -->

## 체크리스트

- [ ] **[CONTRIBUTING.md](../CONTRIBUTING.md) 를 읽었다**
- [ ] `.venv/bin/python scripts/check_harness.py` 가 **통과**한다 (결함 ✗ 없음)
- [ ] 데이터 파일이 포함되지 않았다 (`git status` 확인)
- [ ] 노트북 **출력을 clear** 했다
- [ ] 코드를 실제로 **실행해봤다**
- [ ] 모든 수치에 **출처**가 있다 (하드 룰 5) · **꾸며낸 값이 없다** (하드 룰 6)
- [ ] 받은 데이터를 **카탈로그에 등재**했다 (하드 룰 3) — 해당 시

## 병합 방식

- [ ] 작업 브랜치 → `develop` : `--squash --delete-branch`
- [ ] `develop` → `main` : **`--merge --delete-branch=false`**
      *(squash 를 쓰면 develop 커밋이 main 의 조상이 되지 않아 다음 PR 부터 충돌납니다)*
