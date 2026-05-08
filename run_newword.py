# -*- coding: utf-8 -*-
"""兼容入口脚本

保持与原始用法兼容：python3 newword.py input_file output_file [newword.conf]
实际逻辑已迁移到 newword 包中，此脚本仅做转发。
"""

from newword.cli import main

if __name__ == "__main__":
    main()
