param(
    [string]$InputPath = "$PSScriptRoot/bilibili-seeds.json",
    [string]$OutputPath = "$PSScriptRoot/bilibili-metadata.json",
    [switch]$Refresh
)

$ErrorActionPreference = 'Stop'
$taskSeeds = @(Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json)
$taskResults = [System.Collections.Generic.List[object]]::new()
$taskCached = @{}
if ((Test-Path -LiteralPath $OutputPath) -and -not $Refresh) {
    foreach ($taskRow in @(Get-Content -LiteralPath $OutputPath -Raw | ConvertFrom-Json)) {
        if ($taskRow.status -eq 'ok') {
            # PowerShell may deserialize ISO strings to DateTime; keep offsets stable on re-save.
            $taskRow.fetchedAt = ([DateTimeOffset]$taskRow.fetchedAt).ToUniversalTime().ToString('o')
            $taskRow.publishedAt = ([DateTimeOffset]$taskRow.publishedAt).ToOffset([TimeSpan]::FromHours(8)).ToString('yyyy-MM-ddTHH:mm:sszzz')
            $taskCached[$taskRow.seedId] = $taskRow
        }
    }
}
foreach ($taskSeed in $taskSeeds) {
    if ($taskCached.ContainsKey($taskSeed.id) -and
        ((($taskSeed.bvid) -and ($taskCached[$taskSeed.id].bvid -eq $taskSeed.bvid)) -or
         (($taskSeed.aid) -and ($taskCached[$taskSeed.id].aid -eq $taskSeed.aid)))) {
        $taskResults.Add($taskCached[$taskSeed.id])
        continue
    }
    $taskKey = if ($taskSeed.bvid) { 'bvid=' + $taskSeed.bvid } else { 'aid=' + $taskSeed.aid }
    $taskApiUrl = 'https://api.bilibili.com/x/web-interface/view?' + $taskKey
    $taskFetchedAt = [DateTimeOffset]::UtcNow.ToString('o')
    try {
        $taskResponse = Invoke-RestMethod -Uri $taskApiUrl -TimeoutSec 20
        if ($taskResponse.code -ne 0) { throw "API code $($taskResponse.code): $($taskResponse.message)" }
        $taskVideo = $taskResponse.data
        $taskPublishedAt = [DateTimeOffset]::FromUnixTimeSeconds($taskVideo.pubdate).ToOffset([TimeSpan]::FromHours(8))
        $taskResults.Add([ordered]@{
            seedId = $taskSeed.id
            fetchedAt = $taskFetchedAt
            status = 'ok'
            apiUrl = $taskApiUrl
            bvid = $taskVideo.bvid
            aid = $taskVideo.aid
            url = 'https://www.bilibili.com/video/' + $taskVideo.bvid + '/'
            title = $taskVideo.title
            publishedAt = $taskPublishedAt.ToString('yyyy-MM-ddTHH:mm:sszzz')
            date = $taskPublishedAt.ToString('yyyy-MM-dd')
            owner = $taskVideo.owner | Select-Object mid, name
            durationSeconds = $taskVideo.duration
            stats = $taskVideo.stat | Select-Object view, like, coin, favorite, share, danmaku, reply, his_rank
            honors = @($taskVideo.honor_reply.honor | Select-Object type, desc)
            description = $taskVideo.desc
            state = $taskVideo.state
            copyright = $taskVideo.copyright
        })
    } catch {
        $taskResults.Add([ordered]@{ seedId = $taskSeed.id; fetchedAt = $taskFetchedAt; status = 'unavailable'; apiUrl = $taskApiUrl; error = $_.Exception.Message })
    }
    Start-Sleep -Milliseconds 350
}
$taskResults | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$taskResults | ForEach-Object {
    [pscustomobject]@{ id = $_.seedId; status = $_.status; date = $_.date; bvid = $_.bvid; title = $_.title; owner = $_.owner.name; views = $_.stats.view; rank = $_.stats.his_rank; error = $_.error }
} | ConvertTo-Json -Depth 3
