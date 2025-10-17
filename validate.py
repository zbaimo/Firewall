"""
代码完整性验证脚本
验证所有模块是否可以正常导入和运行
"""
import sys
import os

# 设置UTF-8编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

def test_imports():
    """测试所有模块导入"""
    print("正在验证模块导入...")
    print("=" * 60)
    
    tests = [
        ("核心模块", "from core import *"),
        ("数据库模型", "from models.database import Database"),
        ("Web应用", "from web.app import create_app"),
        ("工具函数", "from utils.helpers import load_config"),
        ("日志工具", "from utils.logger import setup_logger"),
    ]
    
    passed = 0
    failed = 0
    
    for name, code in tests:
        try:
            exec(code)
            print(f"[OK] {name:20} imported")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name:20} error: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    
    return failed == 0


def test_config():
    """测试配置文件"""
    print("\n正在验证配置文件...")
    print("=" * 60)
    
    try:
        from utils.helpers import load_config
        config = load_config('config.yaml')
        
        # 检查关键配置
        checks = [
            ('nginx.access_log', "Nginx日志路径"),
            ('database.path', "数据库路径"),
            ('redis.enabled', "Redis配置"),
            ('scoring_system.enabled', "评分系统"),
            ('web_dashboard.enabled', "Web后台"),
        ]
        
        for key, name in checks:
            keys = key.split('.')
            value = config
            for k in keys:
                value = value.get(k, {})
            
            if value:
                print(f"[OK] {name:20} configured")
            else:
                print(f"[WARN] {name:20} not configured")
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 配置文件错误: {e}")
        print("=" * 60)
        return False


def test_database():
    """测试数据库初始化"""
    print("\n正在验证数据库...")
    print("=" * 60)
    
    try:
        from models.database import Database
        from utils.helpers import load_config
        
        config = load_config('config.yaml')
        db = Database(config)
        
        print("[OK] Database initialized")
        print("[OK] Tables created")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ 数据库错误: {e}")
        print("=" * 60)
        return False


def check_required_files():
    """检查必需文件"""
    print("\n正在检查必需文件...")
    print("=" * 60)
    
    import os
    
    required_files = [
        'main.py',
        'config.yaml',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        '.gitignore',
        'README.md',
        'LICENSE',
        '.github/workflows/docker-build.yml',
        '.github/workflows/ci.yml',
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[MISSING] {file}")
            all_exist = False
    
    print("=" * 60)
    return all_exist


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Nginx防火墙系统 - 代码完整性验证")
    print("=" * 60 + "\n")
    
    results = []
    
    # 1. 检查文件
    results.append(("必需文件检查", check_required_files()))
    
    # 2. 测试导入
    results.append(("模块导入测试", test_imports()))
    
    # 3. 测试配置
    results.append(("配置文件测试", test_config()))
    
    # 4. 测试数据库
    results.append(("数据库测试", test_database()))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:10} {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n[SUCCESS] All validation passed! Code is ready.")
        print("\nNext steps:")
        print("1. Edit sensitive info in config.yaml")
        print("2. Edit .github/workflows/docker-build.yml image name")
        print("3. Run push_to_github.bat to push to GitHub")
        print("")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please check errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

