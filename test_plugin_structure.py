#!/usr/bin/env python3
"""
插件结构验证脚本
检查CD2备份空文件夹清理插件是否符合MoviePilot V2标准
"""

import json
import os
import sys
from pathlib import Path

def test_plugin_structure():
    """测试插件结构"""
    print("🧪 开始测试CD2备份空文件夹清理插件结构...")
    
    base_dir = Path(__file__).parent
    errors = []
    warnings = []
    
    # 1. 检查package.v2.json
    package_file = base_dir / "package.v2.json"
    if not package_file.exists():
        errors.append("❌ package.v2.json 文件不存在")
    else:
        try:
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            if isinstance(package_data, dict):
                # 查找插件信息
                plugin_info = None
                for key, value in package_data.items():
                    if key == "emptyfilecleaner":
                        plugin_info = value
                        break
                
                if plugin_info:
                    print(f"✅ package.v2.json 格式正确（对象格式）")
                    print(f"   插件ID: emptyfilecleaner")
                    print(f"   插件名称: {plugin_info.get('name', 'N/A')}")
                    print(f"   版本: {plugin_info.get('version', 'N/A')}")
                    print(f"   V2标识: {plugin_info.get('v2', False)}")
                    
                    if not plugin_info.get('v2', False):
                        warnings.append("⚠️  V2标识为False或不存在")
                else:
                    errors.append("❌ 在package.v2.json中未找到emptyfilecleaner插件配置")
            elif isinstance(package_data, list) and len(package_data) > 0:
                # 旧的数组格式，虽然有些版本支持，但建议用对象格式
                plugin_info = package_data[0]
                warnings.append("⚠️  使用数组格式，建议改为对象格式")
                print(f"⚠️  package.v2.json 使用数组格式")
                print(f"   插件ID: {plugin_info.get('id', 'N/A')}")
                print(f"   插件名称: {plugin_info.get('name', 'N/A')}")
                print(f"   版本: {plugin_info.get('version', 'N/A')}")
                print(f"   V2标识: {plugin_info.get('v2', False)}")
                
                if not plugin_info.get('v2', False):
                    warnings.append("⚠️  V2标识为False或不存在")
            else:
                errors.append("❌ package.v2.json 格式不正确（应该是对象格式，键为插件ID）")
        except json.JSONDecodeError as e:
            errors.append(f"❌ package.v2.json JSON格式错误: {e}")
        except Exception as e:
            errors.append(f"❌ 读取package.v2.json失败: {e}")
    
    # 2. 检查插件目录结构
    plugin_dir = base_dir / "plugins.v2" / "emptyfilecleaner"
    if not plugin_dir.exists():
        errors.append("❌ plugins.v2/emptyfilecleaner 目录不存在")
    else:
        print(f"✅ 插件目录存在: {plugin_dir}")
        
        # 检查__init__.py
        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            errors.append("❌ __init__.py 文件不存在")
        else:
            print(f"✅ __init__.py 文件存在")
            
            # 检查插件类
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'class EmptyFileCleanerPlugin' in content:
                    print(f"✅ 插件类 EmptyFileCleanerPlugin 存在")
                else:
                    warnings.append("⚠️  未找到标准插件类名")
                
                if '_PluginBase' in content:
                    print(f"✅ 继承自 _PluginBase")
                else:
                    errors.append("❌ 未继承自 _PluginBase")
                
                if 'plugin_name = "CD2备份空文件夹清理"' in content:
                    print(f"✅ 插件名称正确")
                else:
                    warnings.append("⚠️  插件名称可能不正确")
                    
                if '__all__' in content:
                    print(f"✅ 包含模块导出声明")
                else:
                    warnings.append("⚠️  缺少 __all__ 导出声明")
                    
            except Exception as e:
                errors.append(f"❌ 读取__init__.py失败: {e}")
    
    # 3. 检查图标文件
    icon_file = base_dir / "icons" / "delete.jpg"
    if not icon_file.exists():
        warnings.append("⚠️  图标文件不存在")
    else:
        print(f"✅ 图标文件存在")
    
    # 4. 检查gitignore
    gitignore_file = base_dir / ".gitignore"
    if not gitignore_file.exists():
        warnings.append("⚠️  .gitignore 文件不存在")
    else:
        print(f"✅ .gitignore 文件存在")
    
    # 输出结果
    print("\n" + "="*50)
    print("📋 测试结果摘要:")
    
    if not errors:
        print("🎉 所有必需的结构检查都通过了！")
    else:
        print("❌ 发现以下错误:")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print("\n⚠️  以下项目需要注意:")
        for warning in warnings:
            print(f"   {warning}")
    
    print(f"\n📊 检查统计:")
    print(f"   错误: {len(errors)}")
    print(f"   警告: {len(warnings)}")
    
    if not errors:
        print("\n✅ 插件结构符合MoviePilot V2标准，可以尝试安装！")
        print("\n💡 安装建议:")
        print("   1. 将整个 plugins.v2/emptyfilecleaner 目录复制到 MoviePilot 的 plugins.v2 目录")
        print("   2. 将 package.v2.json 放到 MoviePilot 根目录（如果有现有的package.v2.json，请合并内容）")
        print("   3. 重启 MoviePilot")
        print("   4. 在插件管理中查看是否出现 'CD2备份空文件夹清理' 插件")
    else:
        print("\n❌ 请先修复上述错误再尝试安装")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_plugin_structure()
    sys.exit(0 if success else 1)
