"""Aggregate verified MOIS year-end dong age profiles to Busan's 16 districts.

Population is resident background, never an inferred patient age or automatic
denominator for receipt rates. Age 100 is the open-ended 100+ group.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/신고인구특성재정립-20260917/population"
GROUPS = (("0_14", 0, 15), ("15_39", 15, 40), ("40_64", 40, 65), ("65_plus", 65, 101))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def csv_out(name, records):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def describe(year, code, name, ages):
    total = sum(ages)
    record = {
        "year": year,
        "referenceDate": f"{year}-12-31",
        "districtCode": code,
        "district": name,
        "total": total,
    }
    for label, start, end in GROUPS:
        record[f"n_{label}"] = sum(ages[start:end])
        record[f"pct_{label}"] = 100 * record[f"n_{label}"] / total
    assert sum(record[f"n_{label}"] for label, _, _ in GROUPS) == total
    return record


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior_path = ROOT / "data/processed/컬럼선별-결측제외-20260915/population/manifest.json"
    prior = read_json(prior_path)
    prior_hashes = {r["year"]: r["sha256"] for r in prior["sources"]}
    dash_path = ROOT / "web/final/data/dashboard.json"
    dash = read_json(dash_path)
    dash_by_key = {(r["year"], r["code"]): r for r in dash["population"]}
    assert len(dash_by_key) == len(dash["population"]) == 1025
    final_manifest_path = ROOT / "data/processed/최종결과-20260915/manifest.json"
    final_manifest = read_json(final_manifest_path)
    dashboard_record = next(r for r in final_manifest["outputs"] if r["path"] == "web/final/data/dashboard.json")
    assert sha(dash_path) == dashboard_record["sha256"]
    district_records, city_records, all_age_records, dong_records, input_records, checks = [], [], [], [], [], []

    for year in range(2020, 2025):
        source = ROOT / f"data/raw/인구배경/MOIS_{year}12_연령별인구_부산전체읍면동.csv"
        actual_sha = sha(source)
        assert actual_sha == prior_hashes[year], f"Prior input no longer matches: {source}"
        rows = list(csv.DictReader(io.StringIO(source.read_bytes().decode("cp949"))))
        assert len(rows) == 222
        prefix = f"{year}년12월_계_"
        age_keys = [f"{prefix}{age}세" for age in range(100)] + [f"{prefix}100세 이상"]
        total_key = f"{prefix}총인구수"
        aggregate_rows = {}
        dongs = []
        for source_row, row in enumerate(rows, start=2):
            match = re.fullmatch(r"(.+?)\s*\((\d{10})\)", row["행정구역"])
            assert match, row["행정구역"]
            fullname, code = match.groups()
            names = fullname.split()
            assert names[0] == "부산광역시"
            ages = [int(row[key].replace(",", "")) for key in age_keys]
            total = int(row[total_key].replace(",", ""))
            assert sum(ages) == total
            if code == "2600000000" or code.endswith("00000"):
                aggregate_rows[code] = {"ages": ages, "total": total, "name": names[-1]}
                continue
            assert len(names) == 3
            district_code = code[:5] + "00000"
            record = {
                "year": year, "referenceDate": f"{year}-12-31",
                "districtCode": district_code, "district": names[1],
                "code": code, "name": names[2], "total": total, "ages": ages,
            }
            assert record == dash_by_key[(year, code)], f"Dashboard population mismatch: {year}/{code}"
            dongs.append(record)
            dong_records.append(record)
        assert len(dongs) == 205 and len(aggregate_rows) == 17
        assert len({r["code"] for r in dongs}) == 205
        district_codes = sorted({r["districtCode"] for r in dongs})
        assert len(district_codes) == 16
        for district_code in district_codes:
            members = [r for r in dongs if r["districtCode"] == district_code]
            ages = [sum(r["ages"][i] for r in members) for i in range(101)]
            declared = aggregate_rows[district_code]
            assert ages == declared["ages"]
            assert sum(ages) == declared["total"]
            record = describe(year, district_code, declared["name"], ages)
            district_records.append(record)
            all_age_records.append({**record, "dongRows": len(members), "ages": ages, "ageSharesPct": [100 * n / sum(ages) for n in ages]})
        city_ages = [sum(r["ages"][i] for r in dongs) for i in range(101)]
        assert city_ages == aggregate_rows["2600000000"]["ages"]
        city_records.append(describe(year, "2600000000", "부산광역시", city_ages))
        input_records.append({
            "year": year, "path": source.relative_to(ROOT).as_posix(), "sha256": actual_sha,
            "bytes": source.stat().st_size, "priorHashMatch": True,
            "priorManifest": prior_path.relative_to(ROOT).as_posix(),
            "rawRows": 222, "dongRowsUsed": 205, "aggregateRowsValidationOnly": 17,
        })
        checks.append({"year": year, "dongRowsMatchDashboard": 205, "districtAll101AgesMatch": 16, "cityAll101AgesMatch": True, "ageBandsSumToTotal": True})

    old = {r["districtCode"]: r for r in district_records if r["year"] == 2020}
    summaries = []
    for current in (r for r in district_records if r["year"] == 2024):
        baseline = old[current["districtCode"]]
        summaries.append({
            **current,
            "total2020": baseline["total"],
            "totalChange2020To2024": current["total"] - baseline["total"],
            "pct65plus2020": baseline["pct_65_plus"],
            "pct65plusChangePp2020To2024": current["pct_65_plus"] - baseline["pct_65_plus"],
        })
    csv_out("district-age-bands-2020-2024.csv", district_records)
    csv_out("district-summary-2024.csv", summaries)
    csv_out("busan-age-bands-2020-2024.csv", city_records)
    age_long = []
    for record in all_age_records:
        for age, count in enumerate(record["ages"]):
            age_long.append({"year": record["year"], "referenceDate": record["referenceDate"], "districtCode": record["districtCode"], "district": record["district"], "age": "100+" if age == 100 else str(age), "population": count, "sharePct": 100 * count / record["total"]})
    csv_out("district-single-age-2020-2024.csv", age_long)
    save_json("profiles.json", {"districts": all_age_records, "summary2024": summaries, "city": city_records, "dongs": dong_records})
    report = [
        "# 부산 구·군 주민 연령 배경 — 2024년 말", "",
        "신고자·환자의 연령이 아니라 해당 지역 주민의 구성이다. 각 연도 말 주민등록인구로, 연평균 인구·생활인구와 다르다.", "",
        "원본 읍면동 205행만 합산했으며 시 1행·구군 16행은 검산에만 사용했다. 0~99세 및 100세 이상 101구간은 별도 파일에 모두 유지했다.", "",
        "| 구·군 | 총인구 | 0~14세 | 15~39세 | 40~64세 | 65세 이상 | 65세 이상 비중 변화(2020→2024) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summaries:
        cells = [f"{r[f'n_{label}']:,}명 ({r[f'pct_{label}']:.1f}%)" for label, _, _ in GROUPS]
        report.append(f"| {r['district']} | {r['total']:,}명 | " + " | ".join(cells) + f" | {r['pct65plusChangePp2020To2024']:+.2f}%p |")
    (OUT / "population-summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    save_json("validation.json", {
        "status": "pass", "authorChecksOnly": True,
        "checks": checks, "dashboardSha256": sha(dash_path),
        "dashboardPriorHashMatch": True, "populationRowsMatchingDashboard": 1025,
        "districtYearRows": len(district_records), "singleAgeRows": len(age_long),
        "sexAndDuplicateColumns": "Existing full numeric audit reused after raw SHA256 match; not rerun.",
    })
    save_json("manifest.json", {
        "script": Path(__file__).relative_to(ROOT).as_posix(), "scriptSha256": sha(Path(__file__)),
        "inputs": input_records,
        "dashboard": {"path": dash_path.relative_to(ROOT).as_posix(), "sha256": sha(dash_path), "priorManifestSha256": sha(final_manifest_path)},
        "policy": {
            "aggregation": "Sum only the 205 township/dong rows within each year's district code; city/district source totals used only for validation.",
            "time": "Each December 31, 2020–2024, not annual averages or floating population.",
            "ages": "Retain 0–99 and 100+ counts and shares; four exhaustive age bands only for concise display, not medical/policy categories.",
            "join": "District code/name resident background; no inferred patients, no raw-dong forced allocation, no per-capita receipt rate.",
        },
        "outputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"],
    })
    print("Population analysis: PASS (1,025 dong profiles, 80 district-year profiles, 8,080 single-age rows)")
    print("\n".join(report[6:]))


if __name__ == "__main__":
    main()
