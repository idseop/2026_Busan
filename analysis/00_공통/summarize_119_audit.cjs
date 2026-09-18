// 기존 원본 감사 결과만 요약한다. 분석·연령 결합·웹 생성 없음.
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const audit=JSON.parse(fs.readFileSync(path.join(root,'data/interim/119접수감사/audit.json'),'utf8'));
const files=audit.files.filter(f=>f.year>=2020&&f.year<=2024).sort((a,b)=>a.year-b.year);
assert.deepEqual(files.map(f=>f.year),[2020,2021,2022,2023,2024]);
const lines=['# 2020~2024년 부산 119 원본 감사 요약','','현재는 수집·검토·기획 단계다. 아래는 기존 감사 결과의 기록이며 지역 위험 분석이나 효과 검증이 아니다.','','| 연도 | 원본 행 | 부산 명시 행 | 열수 오류 |','|---|---:|---:|---:|',...files.map(f=>`| ${f.year} | ${f.rows} | ${f.busan.rows} | ${f.malformedRows} |`),'','출처: data/interim/119접수감사/audit.json. 원본 단위는 신고접수이며 사고·환자 수가 아니다. 원본 SHA·결측·중복·기간·위치 품질은 감사 JSON에서 확인한다. 나이 변수는 미확보이며 지역 인구로 보완하지 않는다.'];
fs.writeFileSync(path.join(root,'docs/20-데이터카탈로그/119신고접수-전수실사.md'),lines.join('\n')+'\n');
