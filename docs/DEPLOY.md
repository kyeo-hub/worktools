# 打包与自动更新部署指南

## 一、安装依赖

```bash
pip install -r requirements.txt
```

## 二、打包应用程序

### 1. 清理旧的构建文件

```bash
python build.py clean
```

### 2. 打包成EXE

```bash
python build.py build
```

打包完成后，`dist/` 目录下会生成 `WorkTools.exe`。

### 3. 创建更新包（可选）

```bash
python build.py update
```

这会生成：
- `WorkTools_v{版本号}.zip` - 更新包
- `server_version.json` - 服务器版本信息文件

## 三、配置自动更新

### 1. 修改版本信息

编辑 `version.json`：

```json
{
  "version": "1.0.0",
  "app_name": "WorkTools",
  "update_url": "https://your-server.com/updates/version.json",
  "download_url": "https://your-server.com/updates/"
}
```

### 2. 部署到服务器

将以下文件上传到服务器：

```
your-server.com/updates/
├── version.json          # 版本信息文件
└── WorkTools_v1.0.1.zip  # 更新包
```

### 3. 服务器版本文件格式

`version.json` 示例：

```json
{
  "version": "1.0.1",
  "app_name": "WorkTools",
  "changelog": [
    "修复已知问题",
    "新增功能X"
  ],
  "download_url": "https://your-server.com/updates/WorkTools_v1.0.1.zip",
  "mandatory": false,
  "published_at": "2024-02-05",
  "min_version": "1.0.0"
}
```

字段说明：
- `version`: 最新版本号
- `changelog`: 更新日志列表
- `download_url`: 更新包下载地址
- `mandatory`: 是否强制更新（true/false）
- `published_at`: 发布日期
- `min_version`: 最低兼容版本

## 四、发布新版本流程

### 1. 更新版本号

编辑 `build.py`，修改 `VERSION`：

```python
VERSION = "1.0.1"  # 新版本号
```

### 2. 重新打包

```bash
python build.py clean
python build.py build
python build.py update
```

### 3. 上传到服务器

```bash
# 假设使用SCP
scp dist/WorkTools.exe user@server:/path/to/latest/
scp WorkTools_v1.0.1.zip user@server:/path/to/updates/
scp server_version.json user@server:/path/to/updates/version.json
```

## 五、自动更新流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户点击   │────▶│  检查版本   │────▶│  对比版本号 │
│ 检查更新    │     │  信息文件   │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                           ┌────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    有新版本？           │
              └───────┬────────┬────────┘
                      │        │
                   是 ▼        ▼ 否
            ┌──────────┐   ┌──────────┐
            │显示更新  │   │提示已是最│
            │对话框    │   │新版本    │
            └────┬─────┘   └──────────┘
                 │
            用户确认更新
                 │
                 ▼
            ┌──────────┐
            │下载更新包│
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │解压并替换│
            │程序文件  │
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │重启程序  │
            └──────────┘
```

## 六、注意事项

### 1. 服务器要求
- 支持HTTPS（推荐）
- 允许跨域访问（CORS）
- 提供静态文件下载

### 2. 版本号规则
- 使用语义化版本：`主版本.次版本.修订号`
- 例如：`1.0.0`, `1.0.1`, `1.1.0`, `2.0.0`

### 3. 强制更新
- 设置 `mandatory: true` 可强制用户更新
- 适用于修复严重bug或安全漏洞

### 4. 更新包结构

```
WorkTools_v1.0.1.zip
├── WorkTools.exe      # 主程序
└── version.json       # 版本信息
```

## 七、测试自动更新

### 1. 本地测试

使用本地HTTP服务器测试：

```bash
# 进入server目录
cd server

# 启动简单HTTP服务器（Python）
python -m http.server 8000
```

修改 `version.json` 中的 `update_url`：

```json
"update_url": "http://localhost:8000/version.json"
```

### 2. 模拟新版本

将 `server/version.json` 中的版本号改为高于当前版本，然后检查更新。

## 八、常见问题

### Q: 打包后程序无法运行？
A: 检查是否包含了所有依赖库，尝试使用 `--debug` 参数打包查看错误信息。

### Q: 更新下载失败？
A: 检查网络连接和服务器URL是否正确，确保服务器允许下载。

### Q: 如何回滚版本？
A: 将服务器上的 `version.json` 中的版本号改回旧版本即可。

### Q: 支持增量更新吗？
A: 当前版本使用全量更新（替换整个程序），后续可考虑实现增量更新。
