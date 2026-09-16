"""Reproducible receipt-row analysis; no administrative-dong assignment or deduplication.
Run from repository root with .venv-check/Scripts/python.exe.
"""
from pathlib import Path
from collections import Counter, defaultdict
import calendar, csv, gzip, hashlib, json
import numpy as np
import pandas as pd
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/동별예방분석-20260914/receipts'
INPUT = ROOT / 'data/interim/분석입력-2020-2024/manifest.json'
TYPE, SUB, RESULT = 'EMRG_RSCU_ASSRT_NM', 'EMRG_RSCU_CLSF_NM', 'PRCS_RSLT_SE_NM'
SGG, EMD = 'CLMTY_SGG_NM', 'CLMTY_EMD_NM'
EXCLUDE = ['업무운행', '훈련출동', '구급차소독']
WEEK = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
SEASON = {1:'겨울',2:'겨울',3:'봄',4:'봄',5:'봄',6:'여름',7:'여름',8:'여름',9:'가을',10:'가을',11:'가을',12:'겨울'}

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def write_json(name, value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(INPUT.read_text(encoding='utf-8-sig'))
    tables=defaultdict(Counter); columns={}; audits=[]; reconc=[]; previous_ids=set()
    def add(name,frame,keys):
        columns[name]=keys
        tables[name].update(frame.groupby(keys,dropna=False,sort=False).size().to_dict())
    workbook=ROOT/'data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx'
    wb=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    write_json('column_dictionary.json',{'file':str(workbook.relative_to(ROOT)),'sha256':sha(workbook),'sheets':{s.title:list(s.values) for s in wb}})
    wb.close()
    for entry in manifest['reports']:
        year=entry['year']; path=ROOT/entry['file']
        priorpath=ROOT/f'data/interim/119접수감사/{year}.json'
        prior=json.loads(priorpath.read_text(encoding='utf-8-sig'))
        digest=sha(path)
        with path.open(encoding=entry['encoding'],newline='') as f: headers=next(csv.reader(f))
        assert digest==entry['sha256']==prior['sha256'], f'Hash mismatch {year}'
        assert headers==prior['originalHeaders'], f'Header mismatch {year}'
        q=Counter(); offset=0; distances=Counter(); daycounts=Counter(); year_ids=set()
        audit={'year':year,'file':entry['file'],'sha256':digest,'header_verified':True,'original_headers':headers,'prior_audit_file':str(priorpath.relative_to(ROOT)),'prior_audit_sha256':sha(priorpath),'reused':{k:prior[k] for k in ['rows','blankRecords','malformedRows','id','missing','coordinates']},'prior_date_checks':{k:v for k,v in prior['date'].items() if k not in ['byDay','byMonth']},'prior_busan_coordinates':prior['busan']['coordinates']}
        with gzip.open(OUT/f'ledger_{year}.csv.gz','wt',encoding='utf-8',newline='',compresslevel=3) as ledger:
            for df in pd.read_csv(path,encoding=entry['encoding'],dtype=str,keep_default_na=False,chunksize=100000):
                df.columns=df.columns.str.upper(); n=len(df); df['year']=year
                current_ids=set(df['DCLR_RCPT_NO']); q['identifiers_seen_in_prior_years']+=int(df['DCLR_RCPT_NO'].isin(previous_ids).sum()); year_ids.update(current_ids)
                df['region_status']=np.select([df['CLMTY_CTPV_NM'].eq('부산광역시'),df['CLMTY_CTPV_NM'].eq('')],['busan_explicit','province_missing'],default='other_province')
                dttext=df['DCLR_DT'].str.strip(); dt=pd.to_datetime(dttext,format='%Y%m%d%H%M%S',errors='coerce')
                endtext=df['RCPT_END_DT'].str.strip(); end=pd.to_datetime(endtext,format='%Y%m%d%H%M%S',errors='coerce')
                df['month']=dt.dt.month.fillna(-1).astype(int); df['hour']=dt.dt.hour.fillna(-1).astype(int)
                df['weekday']=dt.dt.dayofweek.map(dict(enumerate(WEEK))).fillna('invalid')
                df['season']=df['month'].map(SEASON).fillna('invalid'); df['date']=dt.dt.strftime('%Y-%m-%d').fillna('invalid')
                df['hour_band']=pd.cut(df['hour'],[-1,5,11,17,23],labels=['00-05','06-11','12-17','18-23']).astype(str)
                checks={'datetime_invalid':dt.isna(),'datetime_vs_ymd_tm':dttext.ne(df['DCLR_YMD'].str.strip()+df['DCLR_TM'].str.strip()),'weekday_mismatch':df['weekday'].ne(df['DCLR_DOW']),'season_mismatch':df['season'].ne(df['SEASN_NM']),'quarter_mismatch':dt.dt.quarter.astype('Int64').astype(str).ne(df['QTR_NO']),'end_invalid_nonblank':endtext.ne('')&end.isna(),'end_before_receipt':end.lt(dt),'end_components_mismatch':endtext.ne(df['RCPT_END_YMD'].str.strip()+df['RCPT_END_TM'].str.strip())}
                for field,expected in [('DCLR_YR',dt.dt.year),('DCLR_MM',dt.dt.month),('DCLR_DAY',dt.dt.day),('DCLR_HR',dt.dt.hour),('DCLR_MN',dt.dt.minute)]: checks[field+'_mismatch']=pd.to_numeric(df[field],errors='coerce').ne(expected)
                busan=df['region_status'].eq('busan_explicit')
                checks['busan_with_other_grounds_province']=busan&~df['GRNDS_CTPV_NM'].isin(['','부산광역시'])
                checks['busan_with_other_province_flag']=busan&df['OTR_CTPV_DCLR_YN'].eq('Y')
                checks['busan_district_vs_grounds_mismatch']=busan&df[SGG].ne('')&df['GRNDS_SGG_NM'].ne('')&df[SGG].ne(df['GRNDS_SGG_NM'])
                for k,v in checks.items(): q[k]+=int(v.sum())
                # Degree-coordinate separation is diagnostic only; no CRS assertion or substitution.
                xy=[pd.to_numeric(df[c],errors='coerce') for c in ['ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']]
                valid=busan&xy[0].between(-180,180)&xy[2].between(-180,180)&xy[1].between(-90,90)&xy[3].between(-90,90)
                a,b,c,d=[np.radians(x[valid]) for x in xy]
                km=6371*2*np.arcsin(np.sqrt((np.sin((d-b)/2)**2+np.cos(b)*np.cos(d)*np.sin((c-a)/2)**2).clip(0,1)))
                distances.update(pd.cut(km,[-0.001,0.1,1,5,20,float('inf')],labels=['0-100m','100m-1km','1-5km','5-20km','over20km']).value_counts().to_dict())
                normal=df[RESULT].eq('정상'); substantive=normal&~df[SUB].isin(EXCLUDE)
                df['include_A']=busan; df['include_B']=busan&normal; df['include_C']=busan&substantive
                df['exclusion_C_reason']=np.select([~busan,~normal,df[SUB].isin(EXCLUDE)],['region_not_established_busan','processing_not_normal','operational_subtype'],default='included')
                df['spatial_join_status']='unverified_administrative_dong'
                df['spatial_unlinked_reason']=np.select([~busan,df[SGG].eq(''),df[EMD].eq('')],['region_not_established_busan','district_missing','original_dong_missing'],default='historical_boundary_and_coordinate_semantics_unverified')
                add('region_processing',df,['year','region_status',RESULT,TYPE,SUB])
                add('flow',df,['year','region_status','include_A','include_B','include_C','exclusion_C_reason','spatial_unlinked_reason'])
                add('region_flags',df,['year','region_status','GRNDS_CTPV_NM','OTR_CTPV_DCLR_YN','OTR_CTPV_DSPT_YN'])
                for scope,mask in [('A',busan),('B',busan&normal),('C',busan&substantive)]:
                    f=df.loc[mask].copy(); f['scope']=scope
                    add('annual_types',f,['year','scope',TYPE,SUB,RESULT])
                    add('district_types',f,['year','scope',SGG,TYPE])
                    add('original_dong_types',f,['year','scope',SGG,EMD,TYPE,SUB,RESULT])
                    for dim in ['month','season','weekday','hour','date']:
                        add('time_'+dim,f,['year','scope',TYPE,SUB,dim])
                    for dim in ['month','hour_band']:
                        add('original_dong_'+dim,f,['year','scope',SGG,EMD,TYPE,dim])
                daycounts.update(df['date'].value_counts().to_dict())
                df['source_file']=entry['file']; df['csv_record_index']=np.arange(offset+1,offset+n+1)
                keep=['source_file','csv_record_index','year','DCLR_YMD','DCLR_TM','DCLR_DOW','SEASN_NM','region_status','CLMTY_CTPV_NM',SGG,EMD,TYPE,SUB,RESULT,'include_A','include_B','include_C','exclusion_C_reason','spatial_join_status','spatial_unlinked_reason']
                df[keep].to_csv(ledger,index=False,header=offset==0); offset+=n
        assert offset==prior['rows']
        previous_ids.update(year_ids)
        audit['new_checks']=dict(q); audit['busan_coordinate_pair_distance_diagnostic']=dict(distances)
        dates=pd.date_range(f'{year}-01-01',f'{year}-12-31').strftime('%Y-%m-%d')
        audit['zero_observation_dates']=[x for x in dates if not daycounts[x]]
        audit['interpretation']='No deduplication. Receipt identifiers checked within year (prior verified audit) and across source years (new check); unique incident identity not established. Degree-distance bins do not validate coordinate CRS, positional accuracy or incident location. Empty dates/zero days cannot by themselves establish extraction completeness.'
        audits.append(audit); print(f'{year}: {offset:,} source records processed',flush=True)
    frames={}
    for name,counts in tables.items():
        keys=columns[name]; rows=[list(k if isinstance(k,tuple) else (k,))+[int(v)] for k,v in counts.items()]
        frame=pd.DataFrame(rows,columns=keys+['count']).sort_values(keys)
        if name.startswith('time_'):
            dim=name[5:]
            def denom(row):
                dates=pd.date_range(f'{row.year}-01-01',f'{row.year}-12-31')
                if dim=='month': return int((dates.month==row.month).sum())
                if dim=='season': return sum(SEASON[m]==row.season for m in dates.month)
                if dim=='weekday': return sum(WEEK[d]==row.weekday for d in dates.dayofweek)
                return 1 if dim=='date' else len(dates)
            unique=frame[['year',dim]].drop_duplicates(); unique['calendar_days']=unique.apply(denom,axis=1)
            frame=frame.merge(unique,on=['year',dim]); frame['receipts_per_calendar_day']=frame['count']/frame['calendar_days']
        frame.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig'); frames[name]=frame
    changes=[]
    for field in [TYPE,SUB,RESULT]:
        f=frames['region_processing']; last=None
        for year in sorted(f.year.unique()):
            vals=set(f.loc[f.year.eq(year),field]); vals.discard('')
            changes.append({'year':int(year),'field':field,'observed_values':sorted(vals),'newly_observed_vs_previous_year':sorted(vals-last) if last is not None else None,'not_observed_vs_previous_year':sorted(last-vals) if last is not None else None,'warning':'Observed label appearances are not proof of official code revisions.'}); last=vals
    for year in manifest['analysisYears']:
        total=int(frames['flow'].loc[frames['flow'].year.eq(year),'count'].sum())
        scopes={}
        for scope in ['A','B','C']:
            f=frames['annual_types']; expected=int(f.loc[f.year.eq(year)&f.scope.eq(scope),'count'].sum()); scopes[scope]=expected
            for name in ['district_types','original_dong_types','time_month','time_season','time_weekday','time_hour','time_date','original_dong_month','original_dong_hour_band']:
                g=frames[name]; assert int(g.loc[g.year.eq(year)&g.scope.eq(scope),'count'].sum())==expected,(year,scope,name)
        reconc.append({'year':year,'source_rows':total,'scopes':scopes,'all_aggregate_sums_match':True})
    write_json('audit_evidence.json',audits); write_json('classification_changes.json',changes)
    write_json('manifest.json',{'input_manifest':str(INPUT.relative_to(ROOT)),'input_manifest_sha256':sha(INPUT),'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(Path(__file__)),'unit':'CSV receipt record, not unique incident/dispatch/patient','scopes':{'A':'CLMTY_CTPV_NM == 부산광역시; all processing results','B':'A and PRCS_RSLT_SE_NM == 정상','C':'B excluding exact subtype labels '+', '.join(EXCLUDE)},'geography':'Original CLMTY dong strings only; administrative dong unresolved for every row. No name-based population join.','calendar_average':'Counts divided by calendar days in corresponding within-year month/season/weekday, or annual days for each hour. Calendar-year winter joins Jan-Feb and Dec; not a contiguous winter episode.','zero_cells':'Aggregate CSVs contain observed combinations only; absent cells may be treated as zero only inside a confirmed source-year/category observation domain.','ledger':'Local restricted intermediate; source file + 1-based parsed CSV record index, no receipt identifier or coordinates. Not intended as public web data.','reconciliation':reconc,'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']})

if __name__=='__main__': main()
