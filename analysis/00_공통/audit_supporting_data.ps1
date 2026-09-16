# 공식 보완 원본 전체 셀·행 검사. 원본을 변경하지 않는다.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$resultDir=Join-Path $projectRoot 'data/interim/보완자료'
function Read-ZipXml($zip,$name) {
    $entry=$zip.GetEntry($name)
    $reader=[IO.StreamReader]::new($entry.Open())
    try { return [xml]$reader.ReadToEnd() } finally { $reader.Dispose() }
}
$book=[IO.Compression.ZipFile]::OpenRead((Join-Path $projectRoot 'data/raw/보완자료/부산_노인일자리_2026.xlsx'))
try {
    $stringXml=Read-ZipXml $book 'xl/sharedStrings.xml'
    $strings=@($stringXml.SelectNodes('//*[local-name()="si"]') | ForEach-Object {
        (@($_.SelectNodes('.//*[local-name()="t"]') | ForEach-Object {$_.InnerText}) -join '')
    })
    $sheets=@()
    foreach($entry in $book.Entries) {
        if($entry.FullName -notmatch '^xl/worksheets/sheet\d+\.xml$') { continue }
        $xml=Read-ZipXml $book $entry.FullName
        $rows=@()
        foreach($row in $xml.SelectNodes('//*[local-name()="sheetData"]/*[local-name()="row"]')) {
            $cells=[ordered]@{}
            foreach($cell in $row.SelectNodes('./*[local-name()="c"]')) {
                $value=$cell.SelectSingleNode('./*[local-name()="v"]')
                $text=if($null -eq $value) { '' } else { $value.InnerText }
                if($cell.GetAttribute('t') -eq 's') { $text=$strings[[int]$text] }
                if($cell.GetAttribute('t') -eq 'inlineStr') { $text=$cell.InnerText }
                $cells[$cell.GetAttribute('r')]=$text
            }
            if((@($cells.Values) -join '').Trim()) { $rows+=,[pscustomobject]@{row=[int]$row.GetAttribute('r');cells=$cells} }
        }
        $sheets+=,[pscustomobject]@{sheet=$entry.FullName;nonemptyRows=$rows.Count;rows=$rows;merges=@($xml.SelectNodes('//*[local-name()="mergeCell"]') | ForEach-Object {$_.GetAttribute('ref')})}
    }
    $sheets | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $resultDir '노인일자리_전체셀.json') -Encoding UTF8
    foreach($sheet in $sheets) {
        Write-Output ($sheet.sheet+' 비어있지 않은 행 '+$sheet.nonemptyRows)
        $sheet.rows | Select-Object -First 7 | ConvertTo-Json -Depth 5
        $selected=@($sheet.rows | Where-Object {($_.cells.Values -join ' ') -match '노노케어|안부|순찰|스쿨|안전|돌봄'})
        Write-Output ('관련 단어 포함 행 '+$selected.Count)
        $selected | Select-Object -First 8 | ConvertTo-Json -Depth 5
    }
} finally { $book.Dispose() }
$csvPath=Join-Path $projectRoot 'data/raw/보완자료/부산_노인복지관_15042666.csv'
$csvText=[Text.Encoding]::GetEncoding(949).GetString([IO.File]::ReadAllBytes($csvPath))
$csvRows=@($csvText | ConvertFrom-Csv)
$columns=@($csvRows[0].PSObject.Properties.Name)
$blank=[ordered]@{}
foreach($column in $columns) { $blank[$column]=@($csvRows | Where-Object {[string]::IsNullOrWhiteSpace($_.$column)}).Count }
$audit=[pscustomobject]@{rows=$csvRows.Count;columns=$columns;blank=$blank;source='https://www.data.go.kr/data/15042666/fileData.do'}
$audit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resultDir '노인복지관_감사.json') -Encoding UTF8
$audit | ConvertTo-Json -Depth 5
