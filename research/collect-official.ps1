$ErrorActionPreference = 'Stop'
$response = Invoke-RestMethod -Uri 'https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1668940&count=1000&maxlength=0' -TimeoutSec 45
$updates = @($response.appnews.newsitems | Where-Object { $_.title -match '版本.*更新公告|更新公告.*版本' } | ForEach-Object {
    $main = ($_.contents -split '游戏调整及优化')[0]
    $plain = [regex]::Replace($main, '\[/?(?:p|h[123]|b|i|u)\]', "`n")
    $headings = @([regex]::Matches($plain, '(?m)^\s*(?:★|[1-9][0-9]?、)[^\r\n]+') | ForEach-Object { $_.Value.Trim() })
    [PSCustomObject]@{
        title = $_.title
        announcementDate = [DateTimeOffset]::FromUnixTimeSeconds($_.date).ToOffset([TimeSpan]::FromHours(8)).ToString('yyyy-MM-dd')
        url = 'https://steamcommunity.com/announcements/detail/' + $_.gid
        headings = $headings
    }
})
$updates | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'official-steam-updates.json') -Encoding utf8
$updates | ForEach-Object { $_.announcementDate + ' | ' + $_.title + ' | ' + ($_.headings -join ' / ') }
