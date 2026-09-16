from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'web/final/index.html';s=p.read_text(encoding='utf-8')
s=s.replace('<link rel="stylesheet" href="assets/vendor/leaflet/leaflet.css">','<link rel="stylesheet" href="assets/vendor/leaflet/leaflet.css"><link rel="stylesheet" href="assets/vendor/maplibre/maplibre-gl.css">')
s=s.replace('<script defer src="assets/basemap.js"></script>','<script defer src="assets/vendor/maplibre/maplibre-gl.js"></script><script defer src="assets/vendor/maplibre/leaflet-maplibre-gl.js"></script><script defer src="data/context-style.js"></script><script defer src="assets/basemap.js"></script>')
s=s.replace('지역명에 마우스를 올리거나 선택해 접수 확인','지역을 선택해 접수 확인')
p.write_text(s,encoding='utf-8')
