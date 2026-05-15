# 依赖安装参考

## 系统依赖

### ffmpeg + ffprobe
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# 验证
ffmpeg -version
ffprobe -version
```

### auto-editor
```bash
pip3 install auto-editor --break-system-packages
# 或
pip3 install auto-editor
```

### faster-whisper
```bash
pip3 install faster-whisper requests
```

## 依赖检查脚本
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py --check-deps
```

## Whisper 模型选择

| 模型 | 内存占用 | 速度 | 精度 |
|------|---------|------|------|
| tiny | ~1GB | 最快 | 较低 |
| small | ~2GB | 较快 | 中等 |
| base | ~3GB | 中等 | 较高 |
| medium | ~5GB | 较慢 | 高 |

> 推荐 `small` 作为默认配置，平衡速度与精度。
