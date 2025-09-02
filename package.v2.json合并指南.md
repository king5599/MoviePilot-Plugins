# package.v2.json 合并指南

## 🔧 如何正确合并package.v2.json

如果你的MoviePilot目录中已经存在`package.v2.json`文件，你需要手动合并插件配置，而不是直接覆盖。

### 当前MoviePilot中已有package.v2.json的情况

**示例：现有的package.v2.json**
```json
{
  "existingplugin1": {
    "name": "现有插件1",
    "version": "1.0.0",
    "v2": true
  },
  "existingplugin2": {
    "name": "现有插件2", 
    "version": "2.0.0",
    "v2": true
  }
}
```

**需要添加CD2备份空文件夹清理插件配置：**

**正确的合并结果：**
```json
{
  "existingplugin1": {
    "name": "现有插件1",
    "version": "1.0.0",
    "v2": true
  },
  "existingplugin2": {
    "name": "现有插件2", 
    "version": "2.0.0",
    "v2": true
  },
  "emptyfilecleaner": {
    "name": "CD2备份空文件夹清理",
    "description": "专为CD2备份清理而设计，自动删除指定目录下的空文件（包括子目录），支持排除指定目录。可以设置最小文件大小阈值，支持定时任务和手动执行，具有测试模式确保安全性。",
    "labels": "CD2,备份清理,空文件,目录管理,定时任务,安全",
    "version": "1.0.4",
    "icon": "delete.jpg",
    "author": "assistant",
    "level": 1,
    "v2": true,
    "history": {
      "v1.0.4": "修改插件名称为CD2备份空文件夹清理，优化安装兼容性",
      "v1.0.3": "根据V2插件标准修复bug，增加版本检测和兼容性处理",
      "v1.0.2": "改进空目录检测逻辑，增加详细日志输出，新增扫描空目录功能",
      "v1.0.1": "优化代码结构，增加线程安全锁",
      "v1.0.0": "初始版本，支持空文件清理和目录排除功能"
    }
  }
}
```

### 操作步骤

1. **备份现有配置**
   ```bash
   cp /path/to/moviepilot/package.v2.json /path/to/moviepilot/package.v2.json.backup
   ```

2. **编辑现有的package.v2.json**
   - 打开MoviePilot目录中的`package.v2.json`
   - 在最后一个插件配置后添加逗号（如果需要）
   - 复制我们的`emptyfilecleaner`配置块到文件中
   - 确保JSON格式正确（可使用在线JSON验证器）

3. **验证格式**
   ```bash
   # 检查JSON格式是否正确
   python3 -m json.tool /path/to/moviepilot/package.v2.json
   ```

### 如果没有现有package.v2.json

如果MoviePilot目录中没有`package.v2.json`文件，直接复制我们的文件即可：

```bash
cp package.v2.json /path/to/moviepilot/
```

### ❌ 常见错误

**错误1：数组格式**
```json
[
  {
    "id": "emptyfilecleaner",
    "name": "CD2备份空文件夹清理"
  }
]
```
这会导致错误：`'list' object has no attribute 'items'`

**错误2：重复键**
```json
{
  "emptyfilecleaner": {...},
  "emptyfilecleaner": {...}  // 重复的键！
}
```

**错误3：JSON格式错误**
```json
{
  "emptyfilecleaner": {
    "name": "CD2备份空文件夹清理",
    "version": "1.0.4"  // 最后一项后面不应该有逗号
  },
}
```

### 🔍 验证安装

安装后可以通过以下方式验证：

1. **检查MoviePilot日志**
   ```bash
   tail -f /path/to/moviepilot/logs/moviepilot.log | grep -i emptyfilecleaner
   ```

2. **查看插件管理页面**
   - 重启MoviePilot
   - 进入插件管理页面
   - 搜索"CD2备份空文件夹清理"

3. **API检查**
   ```bash
   # 如果MoviePilot有API接口，可以通过API查看插件列表
   curl http://your-moviepilot-host/api/v1/plugins
   ```
