<?php
// ========== CONFIG ==========
$remoteSource = "https://raw.githubusercontent.com/alex4528/m3u/refs/heads/main/jstar.m3u"; // Remote playlist containing cookie
$cookieFile   = __DIR__ . "/fetch.json";
$playlistFile = __DIR__ . "/playlist.php";

// ========== 1. FETCH COOKIE FROM REMOTE ==========
$response = @file_get_contents($remoteSource);
if (!$response) exit("❌ Failed to fetch remote playlist.\n");

if (!preg_match('/#EXTHTTP:\s*(\{.*\})/', $response, $matches)) {
    exit("❌ No #EXTHTTP JSON block found in remote playlist.\n");
}

$cookieJson = json_decode($matches[1], true);
if (!$cookieJson || !isset($cookieJson['cookie'])) {
    exit("❌ 'cookie' key missing or invalid JSON in remote playlist.\n");
}

$newCookie = $cookieJson['cookie'];
file_put_contents($cookieFile, json_encode(['cookie' => $newCookie], JSON_PRETTY_PRINT));
echo "✅ Cookie saved to fetch.json\n";

// ========== 2. LOAD playlist.php ==========
if (!file_exists($playlistFile)) exit("❌ playlist.php not found.\n");

$playlistContent = file_get_contents($playlistFile);

// ========== 3. REPLACE ALL #EXTHTTP: LINES WITH NEW COOKIE ==========
$playlistContent = preg_replace(
    '/^#EXTHTTP:.*$/mi',
    '#EXTHTTP:{"cookie":"' . $newCookie . '"}',
    $playlistContent
);

// ========== 4. REPLACE OLD %7Ccookie= IN URLS WITH NEW COOKIE ==========
$playlistContent = preg_replace_callback(
    '/(https?:\/\/[^\s"]+?)%7Ccookie=[^"\s|]*/i',
    fn($m) => $m[1] . '%7Ccookie=' . $newCookie,
    $playlistContent
);

// ========== 5. ADD %7Ccookie= TO .mpd LINKS THAT DON'T HAVE IT ==========
$playlistContent = preg_replace_callback(
    '/(https?:\/\/[^\s|"]+\.mpd)(?![^|"]*%7Ccookie=)/i',
    fn($m) => $m[1] . '%7Ccookie=' . $newCookie,
    $playlistContent
);

// ========== 6. SAVE UPDATED playlist.php ==========
file_put_contents($playlistFile, $playlistContent);
echo "✅ playlist.php updated with new cookie in all applicable places.\n";
