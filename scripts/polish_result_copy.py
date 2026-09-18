from pathlib import Path
p=Path(__file__).resolve().parents[1]/'web/final/assets/app.js'
s=p.read_text(encoding='utf-8')
for old,new in {
 '주민 배경 후보 ${choices.length}개 · 개별 선택 필요':'${choices.length}개 동의 주민 자료를 선택할 수 있습니다.',
 '${popYear()}년의 단일 주민 배경 후보 미확인':'${popYear()}년 연결된 주민 자료 없음',
 '단일 코드 후보 · 신고 행정동 미확정':'지역 주민 구성',
 '개별 선택 후보 · 신고 배정 미확정':'선택한 동의 주민 구성',
 '인구 후보 개별 선택':'주민 자료 선택',
 '후보를 선택하세요':'동을 선택하세요',
 '크게 버튼은 처음 범위로 돌아갑니다.':'선택 버튼은 선택한 구·군으로 이동합니다.',
 '지명은 현재 경계 내부의 대표점 가까이에 표시하며, 접수 건수는 지명에 마우스를 올리거나 선택하면 확인할 수 있습니다. 지명 위치는 실제 신고 위치가 아닙니다.':'도로·지명은 OpenStreetMap 배경지도에 표시됩니다. 구·군을 선택하면 해당 지역명으로 접수된 신고 결과를 확인할 수 있습니다. 배경지도의 상세 수준이 신고 위치의 정확도를 뜻하지는 않습니다.',
}.items():s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
