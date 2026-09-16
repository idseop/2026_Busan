"""Fetch official local service evidence; preserve snapshots and checksums."""
from pathlib import Path
import urllib.request, ssl, hashlib, json, re
from html.parser import HTMLParser
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/services'
OUT.mkdir(parents=True,exist_ok=True)

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style'): self.skip+=1
    def handle_endtag(self,t):
        if t in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,d):
        if not self.skip and d.strip(): self.parts.append(d.strip())

def fetch(key,url):
    manifest_path=OUT/'manifest.json'
    manifest=json.loads(manifest_path.read_text('utf-8')) if manifest_path.exists() else []
    record={'id':key,'url':url,'accessed_at':datetime.now().astimezone().isoformat()}
    try:
        try: response=urllib.request.urlopen(url,timeout=30)
        except urllib.error.URLError as exc:
            if 'UNEXPECTED_EOF' in str(exc):
                import subprocess, io
                result=subprocess.run(['curl.exe','-fsSL','--max-time','25',url],capture_output=True,check=True)
                response=io.BytesIO(result.stdout); response.status=200
                record['transport']='curl (Windows TLS); Python TLS EOF fallback'
            elif 'CERTIFICATE_VERIFY_FAILED' not in str(exc): raise
            else:
                record['tls_note']='공개자료 사이트 인증서 체인 검증 실패; 비인증 HTTPS 재시도. 원문 출처 별도 교차확인 필요.'
                response=urllib.request.urlopen(url,timeout=30,context=ssl._create_unverified_context())
        b=response.read(); ext='.pdf' if b.startswith(b'%PDF') else '.html'
        path=OUT/(key+ext); path.write_bytes(b)
        if ext=='.pdf':
            import fitz
            doc=fitz.open(stream=b,filetype='pdf'); text='\n'.join(p.get_text() for p in doc)
        else:
            html=b.decode('utf-8',errors='replace'); parser=Plain(); parser.feed(html); text='\n'.join(parser.parts)
        (OUT/(key+'.txt')).write_text(text,encoding='utf-8')
        record.update(status=response.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),snapshot=path.name)
    except Exception as exc: record['error']=str(exc)
    manifest=[x for x in manifest if x['id']!=key]+[record]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))
    return record

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('key'); p.add_argument('url',nargs='?'); args=p.parse_args()
    if args.key=='figures':
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        font=font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name()
        plt.rcParams.update({'font.family':font,'font.size':15,'axes.unicode_minus':False,'svg.fonttype':'none','savefig.facecolor':'#f7fafb'})
        navy='#18394a'; teal='#16827f'; orange='#d49b46'; pale='#b5cbd0'
        def base(title,subtitle):
            fig,ax=plt.subplots(figsize=(13.5,7.8)); fig.patch.set_facecolor('#f7fafb'); ax.set_facecolor('#f7fafb')
            fig.subplots_adjust(left=.12,right=.96,top=.74,bottom=.32)
            fig.text(.06,.92,title,fontsize=23,weight='bold',color=navy)
            fig.text(.06,.845,subtitle,fontsize=14,color='#45606c')
            ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color('#cad7dc'); ax.tick_params(axis='y',length=0,pad=15)
            ax.grid(axis='x',color='#e0e8eb',zorder=0);ax.set_axisbelow(True)
            return fig,ax
        a=json.loads((OUT/'aed-summary.json').read_text('utf-8'))
        assert [(r['nonvehicle_listed'],r['nonvehicle_all_days_24h']) for r in a]==[(92,42),(70,41)]
        fig,ax=base('AED는 설치 등록 수와 이용시간을 함께 봐야 한다','공식 검색에서 주소를 확인한 차량 등록을 제외한 AED 등록 · 2026년 9월 16일 확보')
        for i,r in enumerate(a):
            n=r['nonvehicle_listed']; yes=r['nonvehicle_all_days_24h']; other=n-yes
            ax.barh(i,yes,color=teal,height=.43,label='매일·공휴일 24시간 모두 명시' if i==0 else None)
            ax.barh(i,other,left=yes,color=pale,height=.43,label='상시 24시간을 모두 명시하지 않음' if i==0 else None)
            ax.text(yes/2,i,f'{yes}건',ha='center',va='center',weight='bold',color='white',fontsize=18)
            ax.text(yes+other/2,i,f'{other}건',ha='center',va='center',weight='bold',color=navy,fontsize=18)
            ax.text(n+1.2,i,f'총 {n}건',va='center',color=navy,fontsize=16)
        ax.set_yticks([0,1],['기장읍','연산동']); ax.invert_yaxis(); ax.set_xlim(0,105); ax.set_xlabel('고유 AED 등록 ID 수 (건)',fontsize=14)
        fig.legend(loc='lower left',bbox_to_anchor=(.06,.19),frameon=False,ncol=1,fontsize=13)
        fig.text(.06,.13,'차량 탑재 10건·주소 미확인 1건은 비교에서 제외. 동일 기관에 여러 등록이 있을 수 있습니다.',fontsize=12,color='#45606c')
        fig.text(.06,.09,'시간 미기재·일요일 주차 제한 포함. 닫힘·고장·환자 미이용을 뜻하지 않으며 지역 전체 대장과 동일함을 보장하지 않습니다.',fontsize=11,color='#45606c')
        fig.text(.06,.045,'출처: 국립중앙의료원 E-GEN · 시설별 갱신일 미표시 · aed-facilities.json / aed-summary.json',fontsize=11,color='#45606c')
        for ext in ['png','svg']: fig.savefig(OUT/f'aed-operating-hours.{ext}',dpi=160)
        plt.close(fig)
        a=json.loads((OUT/'apartment-summary.json').read_text('utf-8'))
        assert [r['building_records'] for r in a]==[137,165]
        fig,ax=base('아파트의 스프링클러 설치 범위는 건물마다 다르다','부산소방 포털에 등록된 단지의 동 항목 · 관리사무소 조사자료 · 2026년 9월 16일 확보')
        labels=['있음(전층)','있음(16층 이상)','없음']; colors=[teal,orange,pale]
        for i,r in enumerate(a):
            left=0
            for label,color in zip(labels,colors):
                n=r['sprinkler_labels'].get(label,0); ax.barh(i,n,left=left,height=.43,color=color,label=label if i==0 else None)
                ax.text(left+n/2,i,str(n),ha='center',va='center',weight='bold',fontsize=18,color='white' if color==teal else navy); left+=n
            assert left==r['building_records']
            ax.text(left+2,i,f'{left}개',va='center',color=navy,fontsize=16)
        ax.set_yticks([0,1],['기장읍\n27개 단지','온천동\n44개 단지']); ax.invert_yaxis(); ax.set_xlim(0,188); ax.set_xlabel('포털 등록 동 항목 수 (개)',fontsize=14)
        fig.legend(loc='lower left',bbox_to_anchor=(.06,.19),frameon=False,ncol=3,fontsize=13)
        fig.text(.06,.13,'기장읍 137개·온천동 165개 등록 항목. 해당 지역 모든 주택·아파트의 설치율이나 가구 수가 아닙니다.',fontsize=12,color='#45606c')
        fig.text(.06,.09,'온천동 오피스텔 표기 1항목 포함. 미설치는 법 위반이 아니며 과거 신고를 이 건물들에 배정하지 않았습니다.',fontsize=11,color='#45606c')
        fig.text(.06,.045,'출처: 부산소방재난본부 「우리 아파트 화재안전 한눈에 보기」 · apartment-buildings.json',fontsize=11,color='#45606c')
        for ext in ['png','svg']: fig.savefig(OUT/f'apartment-sprinkler-conditions.{ext}',dpi=160)
        plt.close(fig)
        print('2 PNG + 2 SVG generated; input counts reconciled')
    elif args.key=='apartments':
        import csv
        rows=[]; inventory=[]
        def plain(s):
            q=Plain(); q.feed(s); return re.sub(r'\s+',' ',' '.join(q.parts)).strip()
        for region,district,dong in [('gijang','기장군','기장읍'),('oncheon','동래구','온천동')]:
            candidates=json.loads((OUT/f'apartment-{region}-list.html').read_text('utf-8'))
            selected=[r for r in candidates if r['apt_gu']==district and r['apt_dong']==dong]
            for apt in selected:
                inventory.append(apt)
                aptkey=f'apartment-{apt["idx"]}'
                url=f'https://119.busan.go.kr/safeapt/search/view?aptIdx={apt["idx"]}'
                path=OUT/(aptkey+'.html')
                if not path.exists(): fetch(aptkey,url)
                html=path.read_text('utf-8')
                section=re.search(r'<select id="dongList".*?</select>',html,re.S)
                buildings=re.findall(r'<option value="(\d+)"[^>]*>(.*?)</option>',section.group(0),re.S) if section else []
                for i,(building_id,building_name) in enumerate(buildings):
                    key=f'apartment-building-{building_id}'; burl=url+'&idx='+building_id
                    bp=OUT/(key+'.html')
                    if not bp.exists(): fetch(key,burl)
                    bh=bp.read_text('utf-8'); content=bh.split('<ul class="check_list">')[1].split('</ul>')[0]
                    facts={plain(k):plain(v) for k,v in re.findall(r'<p class="title">(.*?)</p>.*?<p class="cont">(.*?)</p>',content,re.S)}
                    row={**apt,'building_id':building_id,'building_name':plain(building_name),**facts,'source_id':key,'source_url':burl,'accessed_date':'2026-09-16','asof_date':'시설별 조사일 미표시','provenance':'부산소방재난본부; 관리사무소 조사자료'}
                    rows.append(row)
        (OUT/'apartment-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
        (OUT/'apartment-buildings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        fields=list(dict.fromkeys(k for r in rows for k in r))
        with (OUT/'apartment-buildings.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader();w.writerows(rows)
        from collections import Counter
        summary=[]
        for dong in ['기장읍','온천동']:
            subset=[r for r in rows if r['apt_dong']==dong]
            summary.append({'region':dong,'complexes_with_records':len(set(r['idx'] for r in subset)),'building_records':len(subset),'sprinkler_labels':dict(Counter(r.get('스프링클러','미기재') for r in subset)),'scope':'공식 검색에 등록된 단지의 동 항목(오피스텔 표기 포함). 부산 전체주택이나 해당 지역 전체아파트의 설치율 아님.'})
        (OUT/'apartment-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False))
    elif args.key!='aed': fetch(args.key,args.url)
    else:
        import csv
        from urllib.parse import quote
        rows=[]; days=['월요일','화요일','수요일','목요일','금요일','토요일','일요일','공휴일']
        def clean(s):
            q=Plain(); q.feed(s); return re.sub(r'\s+',' ',' '.join(q.parts)).strip()
        for region,code,dong in [('gijang','710','기장읍'),('yeonsan','470','연산동')]:
            first=(OUT/f'egen-target-{region}-1.html').read_text('utf-8')
            match=re.search(r'currentPageNum=(\d+)[^>]+title="마지막페이지',first)
            last=int(match.group(1)) if match else 1
            for page in range(1,last+1):
                key=f'egen-target-{region}-{page}'
                url=f'https://www.e-gen.or.kr/egen/search_aed.do?searchType=general&sidoCode=26&gugunCode={code}&addrhosp={quote(dong)}&currentPageNum={page}'
                path=OUT/(key+'.html')
                if not path.exists(): fetch(key,url)
                if not path.exists(): raise RuntimeError('Incomplete pagination '+key)
                html=path.read_text('utf-8'); listing=html.split('<ul id="placesList"')[1].split('</ul>')[0]
                for block in listing.split('<li>')[1:]:
                    a=re.search(r'data-key="([^"]+)".*?>(.*?)<span',block,re.S)
                    addresses=re.findall(r'<p class="info-addr-old">(.*?)</p>',block,re.S)
                    hours=re.findall(r'<div class="time-data">(.*?)</div>',block,re.S)
                    row={'region':dong,'district':'기장군' if region=='gijang' else '연제구','facility_id':a.group(1),'name':clean(a.group(2)),'address':clean(addresses[0]),'lot_address':clean(addresses[1]) if len(addresses)>1 else '', 'source_id':key,'source_url':url,'checked_date':'2026-09-16','source_asof':'표시 없음','status':clean(re.search(r'<p class="info-status">(.*?)</p>',block,re.S).group(1))}
                    for day,value in zip(days,hours): row[day]=clean(value).removeprefix(day).strip()
                    row['mobile_unit']=bool(re.search('구급차|구급차량|차량|[0-9]{2,3}[가-힣][0-9]{4}',row['name']))
                    row['all_days_24h']=all('00:00~24:00' in row.get(day,'') and ('째주' not in row.get(day,'') or all(str(k) in row[day].split('째주')[0] for k in range(1,6))) for day in days)
                    row['address_match']=any(dong in row[field] and row['district'] in row[field] for field in ('address','lot_address'))
                    rows.append(row)
        ids=[r['facility_id'] for r in rows]
        if len(ids)!=len(set(ids)):
            duplicates=[r for r in rows if ids.count(r['facility_id'])>1]
            (OUT/'aed-duplicate-review.json').write_text(json.dumps(duplicates,ensure_ascii=False,indent=2),encoding='utf-8')
            seen={}
            for row in rows:
                stable={k:v for k,v in row.items() if k not in ('source_id','source_url')}
                if row['facility_id'] in seen: assert stable==seen[row['facility_id']], 'Conflicting AED ID'
                seen[row['facility_id']]=stable
            # Same public facility ID and identical attributes across page boundary:
            # retain raw repeated rows in review log, count each AED ID once.
            rows=list({r['facility_id']:r for r in rows}.values())
        unmatched=[r for r in rows if not r['address_match']]
        (OUT/'aed-address-review.json').write_text(json.dumps(unmatched,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Address review',[(r['name'],r['address'],r['lot_address']) for r in unmatched])
        rows=[r for r in rows if r['address_match']]
        (OUT/'aed-facilities.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        with (OUT/'aed-facilities.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        summary=[]
        for dong in ['기장읍','연산동']:
            subset=[r for r in rows if r['region']==dong]; fixed=[r for r in subset if not r['mobile_unit']]
            summary.append({'region':dong,'listed':len(subset),'mobile_excluded_from_comparison':len(subset)-len(fixed),'nonvehicle_listed':len(fixed),'nonvehicle_all_days_24h':sum(r['all_days_24h'] for r in fixed),'nonvehicle_not_all_days_24h':sum(not r['all_days_24h'] for r in fixed),'source_asof':'확보일 2026-09-16; 시설별 갱신일 미표시','claim':'공식 검색 결과에 기재된 이용시간 분포. 실제 장비 작동·개방 상태 현장검증 아님.'})
        (OUT/'aed-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        source=ROOT/'data/processed/예방지원-근거분석-20260916/analysis/selected_case_year_weekday_exact_hour.csv'
        calls={}
        with source.open(encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                if r['caseId'] in ('action-1','action-2'):
                    key=(r['caseId'],r['scope'],int(r['weekday']),int(r['hour']))
                    calls[key]=calls.get(key,0)+int(r['count'])
        availability=[]
        def interval(value):
            m=re.search(r'(\d\d):(\d\d)~(\d\d):(\d\d)',value)
            return tuple(int(m[i])*60+int(m[i+1]) for i in (1,3)) if m else None
        for dong,case in [('연산동','action-1'),('기장읍','action-2')]:
            fixed=[r for r in rows if r['region']==dong and not r['mobile_unit']]
            for weekday,day in enumerate(days[:7]):
                for hour in range(24):
                    open_count=unknown=0
                    for r in fixed:
                        value=r.get(day,''); span=interval(value)
                        if span is None: unknown+=1; continue
                        # Instant at hour:00; midnight-crossing interval belongs to
                        # displayed service-day schedule, not a historical calendar.
                        start,end=span; t=hour*60
                        if start<end: opened=start<=t<end
                        elif start>end: opened=t>=start or t<end
                        else: opened=False; unknown+=1
                        if weekday==6 and '째주' in value and not all(str(k) in value.split('째주')[0] for k in range(1,6)):
                            unknown+=1; opened=False
                        open_count+=opened
                    for scope in sorted({k[1] for k in calls}):
                        availability.append({'region':dong,'caseId':case,'scope':scope,'weekday':weekday,'hour':hour,'calls_2020_2024':calls.get((case,scope,weekday,hour),0),'nonvehicle_aed_listed_20260916':len(fixed),'aed_scheduled_at_hour':open_count,'aed_hours_unknown':unknown,'aed_explicit_other_hours':len(fixed)-open_count-unknown,'calendar':'요일별 표기; 공휴일 분리 안 된 과거 신고와 별도 분모. AED는 각 정각 일정 판독.'})
        with (OUT/'aed-call-time-comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(availability[0])); writer.writeheader(); writer.writerows(availability)
        (OUT/'comparison-input.json').write_text(json.dumps({'calls_path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'facilities_file':'aed-facilities.json','snapshot_date':'2026-09-16','not_claimed':['신고당 AED 필요수','환자 미이용 수','실제 고장 수','2020~2024 당시 AED 운영상태']},ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(summary,ensure_ascii=False))
