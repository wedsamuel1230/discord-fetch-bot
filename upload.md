# HAOS Upload And Rebuild

1. 建立目錄

```powershell
ssh root@homeassistant.local "mkdir -p /mnt/data/supervisor/share/dc-bot/data"
```

1. 確認目錄建立成功

```powershell
ssh root@homeassistant.local "ls /mnt/data/supervisor/share/"
```

1. 上傳所有檔案，`.env` 分開傳

```powershell
scp -P 22 -r D:\projects\dc-bot\fetch\* root@homeassistant.local:/mnt/data/supervisor/share/dc-bot/
scp -P 22 D:\projects\dc-bot\fetch\.env root@homeassistant.local:/mnt/data/supervisor/share/dc-bot/.env
```

1. 在 HA 主機重新 build 映像檔

```powershell
ssh root@homeassistant.local "cd /mnt/data/supervisor/share/dc-bot && docker build --pull -t discord-bot ."
```

1. 重啟 container

```powershell
ssh root@homeassistant.local "docker rm -f discord-bot; docker run -d --name discord-bot --restart unless-stopped -v /mnt/data/supervisor/share/dc-bot/data:/app/data --env-file /mnt/data/supervisor/share/dc-bot/.env discord-bot"
```

1. 驗證

```powershell
ssh root@homeassistant.local "docker ps"
ssh root@homeassistant.local "docker logs discord-bot --tail=50"
```

## 注意

- 目前 `docker run` 只有掛載 `/app/data`，沒有掛載整個程式碼目錄，所以每次改完 `main.py`、`Dockerfile`、`requirements.txt` 都要重新上傳後再 `docker build`。
- 這次 `git` 缺失錯誤的根因就是映像檔沒有重建，container 仍然使用舊版 `discord-bot` image。
