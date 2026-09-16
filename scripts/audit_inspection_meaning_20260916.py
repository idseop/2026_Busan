"""Audit the meaning of inspection remarks directly from four HWP cell records."""
from pathlib import Path
import csv, hashlib, json, re, struct, zlib
from collections import Counter
import olefile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/processed/후속입증-20260916/services'
OUT = ROOT / 'data/processed/최종논리검증-20260916/inspection'
OUT.mkdir(parents=True, exist_ok=True)
STATIONS = {'gijang':'기장소방서','dongnae':'동래소방서','geumjeong':'금정소방서','busanjin':'부산진소방서'}

def clean(data):
    codes=list(struct.unpack('<'+'H'*(len(data)//2),data[:len(data)//2*2])); out=[]; i=0
    while i<len(codes):
        c=codes[i]
        if c in [1,2,3,11,12,14,15,16,17,18,21,22,23]: i+=8; continue
        if c in [9,10,13]: out.append(' ')
        elif c>=32: out.append(chr(c))
        i+=1
    return ''.join(out).strip()

def cells(path):
    result=[]
    with olefile.OleFileIO(path) as o:
        compressed=bool(o.openstream('FileHeader').read()[36]&1)
        for sec in o.listdir():
            if sec[0]!='BodyText': continue
            raw=o.openstream(sec).read(); raw=zlib.decompress(raw,-15) if compressed else raw
            i=0; current=None
            while i<len(raw):
                h=struct.unpack_from('<I',raw,i)[0];i+=4; tag=h&1023;level=(h>>10)&1023; n=h>>20
                if n==4095:n=struct.unpack_from('<I',raw,i)[0];i+=4
                data=raw[i:i+n];i+=n
                if tag==72 and len(data)>=34:
                    if current:result.append(current)
                    col,row,colspan,rowspan=struct.unpack_from('<4H',data,8)
                    current={'section':'/'.join(sec),'level':level,'row':row,'col':col,'colspan':colspan,'rowspan':rowspan,'text':''}
                elif tag==67 and current: current['text']+=' '+clean(data)
            if current:result.append(current)
    for c in result:c['text']=c['text'].strip()
    return result

def writecsv(name, rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run():
    originals=list(csv.DictReader((SRC/'inspection-internal-rows.csv').open(encoding='utf-8-sig')))
    summary=[]; public=[]; manifest=[];headers=[]
    for key,station in STATIONS.items():
        p=SRC/f'{key}-inspection202608.hwp'; cc=cells(p)
        start=next(i for i,c in enumerate(cc) if c['text']=='화재안전조사 결과 세부내역')
        selected=cc[start:]; baselevel=selected[0]['level']; selected=[c for c in selected if c['level']==baselevel]
        groups=[];columns={}
        for c in selected:
            if c['col']==0:
                if columns:groups.append(columns)
                columns={}
            columns[c['col']]=c['text']
        if columns:groups.append(columns)
        extracted=[]
        for row,columns in enumerate(groups):
            if not columns.get(0,'').isdigit():continue
            assert set(columns)==set(range(6)),(key,row,columns.keys())
            r={'station':station,'source_row':int(columns[0]),'name':columns[1],'address':columns[2],'fire':columns[3],'escape':columns[4],'remark':columns[5]}
            old=next(r0 for r0 in originals if r0['station']==station and int(r0['source_row'])==r['source_row'])
            for a,b in [('fire','fire_facility_result'),('escape','escape_firewall_result')]:assert re.sub(r'\s+','',r[a])==re.sub(r'\s+','',old[b]),(key,row,a)
            oldremark=re.sub(r'[\x00-\x1f]|氠瑢','',old['remark']).strip()
            assert re.sub(r'\s+','',r['remark'])==re.sub(r'\s+','',oldremark),(key,row,'remark')
            extracted.append(r)
            public.append({k:r[k] for k in ['station','source_row','fire','escape','remark']})
        bad=[r for r in extracted if '불량' in (r['fire'],r['escape'])]
        blank=[r for r in bad if not r['remark']]
        norm=lambda x:re.sub(r'\s+','',x)
        names=Counter(norm(r['name']) for r in extracted);addresses=Counter(norm(r['address']) for r in extracted)
        summary.append({'station':station,'rows':len(extracted),'assessed':sum(r['fire']!='-' for r in extracted),'defect_rows':len(bad),'defect_remark_onsite':sum('현지시정' in r['remark'] for r in bad),'defect_remark_blank':len(blank),'defect_other_remark':sum(bool(r['remark']) and '현지시정' not in r['remark'] for r in bad),'all_rows_remark_blank':sum(not r['remark'] for r in extracted),'blank_defect_distinct_name_strings':len(set(norm(r['name']) for r in blank)),'blank_defect_distinct_address_strings':len(set(norm(r['address']) for r in blank)),'duplicate_name_groups_all':sum(v>1 for v in names.values()),'duplicate_address_groups_all':sum(v>1 for v in addresses.values()),'unique_physical_facilities_confirmed':False})
        safeheaders=[x for x in groups if not str(x.get(0,'')).isdigit()]
        headers.append({'station':station,'source':p.name,'cells':safeheaders,'columnMeaning':'비고는 범용 비고란이며 조치완료일·조치명령번호·이행상태 전용열은 없다.'})
        manifest.append({'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    assert [sum(r[x] for r in summary) for x in ['rows','assessed','defect_rows','defect_remark_onsite','defect_remark_blank']]==[132,131,19,6,13],summary
    writecsv('reconstructed-public-rows.csv',public);writecsv('form-summary.csv',summary)
    for name,data in [('form-header-cells.json',headers),('original-hashes.json',manifest),('form-summary.json',summary)]: (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    prior=OUT/'geumjeong-inspection202607.hwp'
    if prior.exists():
        cc=cells(prior);start=next(i for i,c in enumerate(cc) if c['text']=='화재안전조사 결과 세부내역');level=cc[start]['level'];groups=[];current={}
        for c in cc[start:]:
            if c['level']!=level:continue
            if c['col']==0:
                if current:groups.append(current)
                current={}
            current[c['col']]=c['text']
        if current:groups.append(current)
        July=[r for r in groups if r.get(0,'').isdigit()]
        norm=lambda x:re.sub(r'\s+','',x)
        aug=[r for r in originals if r['station']=='금정소방서']
        comparisons=[]
        for a in aug:
            same=[j for j in July if norm(j.get(1,''))==norm(a['target_name']) and norm(j.get(2,''))==norm(a['address_internal'])]
            for j in same:comparisons.append({'station':'금정소방서','july_row':int(j[0]),'august_row':int(a['source_row']),'july_fire':j.get(3),'july_escape':j.get(4),'august_fire':a['fire_facility_result'],'august_escape':a['escape_firewall_result'],'same_name_and_address':True,'same_inspection_items_or_reinspection_confirmed':False})
        (OUT/'prior-month-comparison.json').write_text(json.dumps({'july_rows':len(July),'august_rows':len(aug),'exact_matches':comparisons,'interpretation':'동일 명칭·주소가 반복돼도 조사문항·조사시각·재점검 사유가 없어 동일 결함의 시정 전후라고 판단하지 않는다.','scope':'금정 7월과 8월 원본만 대조. 부산진 직전·9월 후속 첨부는 미확보.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
