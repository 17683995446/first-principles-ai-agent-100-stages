
#!/usr/bin/env python3
"""
修复文件中的HTML实体编码语法错误
"""
import os
import re


def fix_file(file_path):
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 修复常见的HTML实体
        replacements = {
            '&gt;': '>',
            '&lt;': '<',
            '&amp;': '&',
            '&quot;': '"',
            '&#39;': "'"
        }
        
        for entity, char in replacements.items():
            content = content.replace(entity, char)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ 处理失败 {file_path}: {e}")
        return False


def main():
    print("="*80)
    print("🔧 批量修复HTML实体编码语法错误")
    print("="*80)
    
    src_dir = '/workspace/src/first_principles_agent'
    test_dir = '/workspace'
    
    fixed_count = 0
    
    # 修复源代码目录
    if os.path.exists(src_dir):
        for filename in os.listdir(src_dir):
            if filename.endswith('.py'):
                file_path = os.path.join(src_dir, filename)
                if fix_file(file_path):
                    fixed_count += 1
    
    # 修复测试文件
    for filename in os.listdir(test_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            file_path = os.path.join(test_dir, filename)
            if fix_file(file_path):
                fixed_count += 1
    
    print(f"\n📊 总计修复: {fixed_count} 个文件")
    print("="*80)


if __name__ == '__main__':
    main()

