# 上傳新檔案指令（HAOS）

## 1. 上傳整個專案到 HAOS 持久路徑
```powershell
scp -r D:\projects\dc-bot\fetch\* root@homeassistant.local:/mnt/data/supervisor/share/dc-bot
```

## 2. 在 HAOS 啟動（重建）
```bash
ssh root@homeassistant.local "cd /mnt/data/supervisor/share/dc-bot && docker compose up -d --build"
```

## 3) 確認 `RUN_ON_STARTUP=false`（開機不推播）
```bash
ssh root@homeassistant.local "grep RUN_ON_STARTUP /mnt/data/supervisor/share/dc-bot/.env"
```

## 4) 看運行日誌
```bash
ssh root@homeassistant.local "cd /mnt/data/supervisor/share/dc-bot && docker compose logs --tail=120"
```

## 5) 若要完整覆蓋（先清空再上傳）
```bash
ssh root@homeassistant.local "rm -rf /mnt/data/supervisor/share/dc-bot && mkdir -p /mnt/data/supervisor/share/dc-bot/data"
```

