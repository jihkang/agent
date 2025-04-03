#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

def install_hooks():
    """Git hooks 설치"""
    # 프로젝트 루트 디렉토리 찾기
    root_dir = Path(__file__).parent.parent.parent
    hooks_dir = root_dir / '.git' / 'hooks'
    
    # pre-commit 훅 복사 및 실행 권한 부여
    source = root_dir / 'scripts' / 'git-hooks' / 'pre-commit.py'
    target = hooks_dir / 'pre-commit'
    
    shutil.copy2(source, target)
    os.chmod(target, 0o755)
    
    print("Git hooks 설치 완료!")

if __name__ == '__main__':
    install_hooks() 