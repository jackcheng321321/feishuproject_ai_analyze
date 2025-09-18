#!/usr/bin/env python3
"""
Markdown转飞书富文本转换器
专注处理基础文字格式：粗体、斜体、删除线、标题、段落
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MarkdownToFeishuConverter:
    """Markdown转飞书富文本转换器"""
    
    def __init__(self):
        """初始化转换器"""
        # 文字格式正则表达式
        self.patterns = {
            # 粗体：**文字** 或 __文字__
            'bold': re.compile(r'\*\*(.*?)\*\*|__(.*?)__'),
            # 斜体：*文字* 或 _文字_
            'italic': re.compile(r'\*(.*?)\*|_(.*?)_'),
            # 删除线：~~文字~~
            'strikethrough': re.compile(r'~~(.*?)~~'),
            # 标题：# 标题
            'h1': re.compile(r'^# (.+)$', re.MULTILINE),
            'h2': re.compile(r'^## (.+)$', re.MULTILINE),
            'h3': re.compile(r'^### (.+)$', re.MULTILINE),
            'h4': re.compile(r'^#### (.+)$', re.MULTILINE),
            'h5': re.compile(r'^##### (.+)$', re.MULTILINE),
            'h6': re.compile(r'^###### (.+)$', re.MULTILINE),
            # 表格行：| 列1 | 列2 | 列3 |
            'table_row': re.compile(r'^\|(.+)\|$'),
            # 表格分隔符：|---|---|---|
            'table_separator': re.compile(r'^\|[\s\-:]+\|$'),
        }
    
    def convert(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        将markdown文本转换为飞书富文本格式
        
        Args:
            markdown_text: markdown格式的文本
            
        Returns:
            飞书富文本JSON结构
        """
        try:
            logger.info("开始转换markdown到飞书富文本")
            logger.debug(f"原始markdown长度: {len(markdown_text)}")
            
            # 按行分割文本
            lines = markdown_text.split('\n')
            rich_text_blocks = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                logger.debug(f"处理第{i+1}行: {line[:50]}...")
                
                # 处理空行
                if not line.strip():
                    rich_text_blocks.append({"type": "blank"})
                    i += 1
                    continue
                
                # 处理表格（需要多行处理）
                table_result, lines_consumed = self._process_table(lines, i)
                if table_result:
                    rich_text_blocks.extend(table_result)
                    i += lines_consumed
                    continue
                
                # 处理标题
                title_block = self._process_title(line)
                if title_block:
                    rich_text_blocks.append(title_block)
                    i += 1
                    continue
                
                # 处理普通段落（含格式）
                paragraph_block = self._process_paragraph(line)
                if paragraph_block:
                    rich_text_blocks.append(paragraph_block)
                
                i += 1
            
            logger.info(f"转换完成，生成{len(rich_text_blocks)}个富文本块")
            return rich_text_blocks
            
        except Exception as e:
            logger.error(f"markdown转换失败: {str(e)}", exc_info=True)
            # 降级处理：返回纯文本格式
            return self._fallback_to_plain_text(markdown_text)
    
    def _process_title(self, line: str) -> Optional[Dict[str, Any]]:
        """处理标题行"""
        # 检查各级标题，并设置对应的字体大小（飞书规范）
        title_font_sizes = {
            'h1': "h1",  # 一级标题
            'h2': "h2",  # 二级标题  
            'h3': "h3",  # 三级标题
            'h4': "h4",  # 四级标题
            'h5': "h5",  # 五级标题
            'h6': "h6",  # 六级标题
        }
        
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            pattern = self.patterns[level]
            match = pattern.match(line)
            if match:
                title_text = match.group(1).strip()
                font_size = title_font_sizes[level]
                logger.debug(f"识别{level}标题: {title_text}, 字体大小: {font_size}")
                
                return {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": title_text,
                            "attrs": {
                                "fontSize": font_size,
                                "bold": "true"  # 飞书要求字符串格式
                            }
                        }
                    ]
                }
        return None
    
    def _process_paragraph(self, line: str) -> Dict[str, Any]:
        """处理普通段落，包含文字格式"""
        logger.debug(f"处理段落: {line}")
        
        # 解析文字格式并构建内容块
        content_blocks = self._parse_inline_formats(line)
        
        return {
            "type": "paragraph",
            "content": content_blocks
        }
    
    def _parse_inline_formats(self, text: str) -> List[Dict[str, Any]]:
        """解析行内格式（粗体、斜体、删除线）"""
        content_blocks = []
        remaining_text = text
        
        # 创建所有格式的匹配列表
        all_matches = []
        
        # 查找所有格式匹配
        for format_name, pattern in self.patterns.items():
            if format_name.startswith('h'):  # 跳过标题模式
                continue
                
            for match in pattern.finditer(text):
                # 获取匹配的文本（处理不同的捕获组）
                matched_text = None
                for group in match.groups():
                    if group:
                        matched_text = group
                        break
                
                if matched_text:
                    all_matches.append({
                        'start': match.start(),
                        'end': match.end(),
                        'format': format_name,
                        'text': matched_text,
                        'original': match.group(0)
                    })
        
        # 按位置排序匹配项
        all_matches.sort(key=lambda x: x['start'])
        
        # 处理重叠和嵌套格式
        processed_matches = self._resolve_overlapping_matches(all_matches)
        
        # 构建内容块
        current_pos = 0
        
        for match in processed_matches:
            # 添加格式前的普通文本
            if match['start'] > current_pos:
                plain_text = text[current_pos:match['start']].strip()
                if plain_text:
                    content_blocks.append({
                        "type": "text",
                        "text": plain_text
                    })
            
            # 添加格式化文本
            attrs = self._get_format_attrs(match['format'])
            content_blocks.append({
                "type": "text",
                "text": match['text'],
                "attrs": attrs
            })
            
            current_pos = match['end']
        
        # 添加剩余的普通文本
        if current_pos < len(text):
            remaining_text = text[current_pos:].strip()
            if remaining_text:
                content_blocks.append({
                    "type": "text",
                    "text": remaining_text
                })
        
        # 如果没有任何格式，返回纯文本
        if not content_blocks:
            content_blocks.append({
                "type": "text",
                "text": text.strip()
            })
        
        return content_blocks
    
    def _resolve_overlapping_matches(self, matches: List[Dict]) -> List[Dict]:
        """处理重叠的格式匹配，优先保留较短的匹配"""
        if not matches:
            return matches
        
        resolved = []
        for current in matches:
            # 检查是否与已处理的匹配重叠
            overlapping = False
            for existing in resolved:
                if (current['start'] < existing['end'] and 
                    current['end'] > existing['start']):
                    overlapping = True
                    break
            
            if not overlapping:
                resolved.append(current)
        
        return resolved
    
    def _get_format_attrs(self, format_name: str) -> Dict[str, str]:
        """获取格式对应的属性"""
        format_mapping = {
            'bold': {"bold": "true"},
            'italic': {"italic": "true"}, 
            'strikethrough': {"strikethrough": "true"}
        }
        
        return format_mapping.get(format_name, {})
    
    def _process_table(self, lines: List[str], start_index: int) -> tuple[List[Dict[str, Any]], int]:
        """处理Markdown表格，返回(表格块列表, 消耗的行数)"""
        current_line = lines[start_index].strip()
        
        # 检查是否是表格行
        if not self.patterns['table_row'].match(current_line):
            return None, 0
        
        logger.debug(f"开始处理表格，起始行: {current_line}")
        
        table_rows = []
        lines_consumed = 0
        
        # 收集所有表格行
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if not line:  # 空行结束表格
                break
                
            # 表格行
            if self.patterns['table_row'].match(line):
                # 跳过分隔符行
                if self.patterns['table_separator'].match(line):
                    lines_consumed += 1
                    continue
                
                # 解析表格行
                cells = self._parse_table_row(line)
                table_rows.append(cells)
                lines_consumed += 1
            else:
                break  # 非表格行，结束表格
        
        if not table_rows:
            return None, 0
        
        # 计算表格尺寸
        max_cols = max(len(row) for row in table_rows) if table_rows else 0
        row_count = len(table_rows)
        
        # 构建cellList
        cell_list = []
        for row_index, row_cells in enumerate(table_rows):
            for col_index, cell_text in enumerate(row_cells):
                cell_attrs = {"bold": "true"} if row_index == 0 else {}  # 表头粗体
                
                cell_content = [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": cell_text.strip(),
                                "attrs": cell_attrs
                            }
                        ]
                    }
                ]
                
                cell_list.append({
                    "row": row_index + 1,  # 飞书行号从1开始
                    "col": col_index + 1,  # 飞书列号从1开始
                    "cellContent": cell_content
                })
        
        # 构建飞书表格结构
        table_block = {
            "type": "table",
            "tableInfo": {
                "rowSize": row_count,
                "colSize": max_cols,
                "cellList": cell_list
            }
        }
        
        logger.debug(f"表格处理完成，共{row_count}行{max_cols}列，生成标准飞书表格")
        return [table_block], lines_consumed
    
    def _parse_table_row(self, line: str) -> List[str]:
        """解析表格行，提取单元格内容"""
        # 移除首尾的 |，然后按 | 分割
        content = line.strip('|').strip()
        cells = [cell.strip() for cell in content.split('|')]
        return cells
    
    def _fallback_to_plain_text(self, text: str) -> List[Dict[str, Any]]:
        """降级处理：转换为纯文本格式"""
        logger.warning("使用降级处理，转换为纯文本格式")
        
        lines = text.split('\n')
        blocks = []
        
        for line in lines:
            if line.strip():
                blocks.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": line.strip()
                        }
                    ]
                })
            else:
                blocks.append({"type": "blank"})
        
        return blocks


# 便利函数
def convert_markdown_to_feishu(markdown_text: str) -> List[Dict[str, Any]]:
    """
    便利函数：将markdown文本转换为飞书富文本格式
    
    Args:
        markdown_text: markdown格式的文本
        
    Returns:
        飞书富文本JSON结构
    """
    converter = MarkdownToFeishuConverter()
    return converter.convert(markdown_text)


# 测试用例
if __name__ == "__main__":
    # 测试转换器
    test_markdown = """# 详细对比分析

这是普通段落，包含**粗体文字**和*斜体文字*。

## 共同点 (Common Ground)

游戏类型与目标：

### 表格数据示例

| 特征 | 游戏A | 游戏B |
|------|-------|-------|
| 类型 | RPG | RPG |  
| 平台 | PC/Mobile | Console |
| 评分 | 4.5/5 | 4.2/5 |

#### 四级标题测试

这里有~~删除线~~文字和**粗体**结合。

##### 五级标题

普通文字段落。

###### 六级标题

最小标题级别。
"""
    
    result = convert_markdown_to_feishu(test_markdown)
    import json
    import sys
    
    # 设置输出编码
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("转换结果:")
    print(f"生成了 {len(result)} 个富文本块")
    
    for i, block in enumerate(result):
        print(f"\n块 {i+1}: {block.get('type', 'unknown')}")
        if block.get('type') == 'paragraph' and block.get('content'):
            for content in block['content']:
                if content.get('type') == 'text':
                    text = content.get('text', '')
                    attrs = content.get('attrs', {})
                    print(f"  文本: {text}")
                    if attrs:
                        print(f"  格式: {attrs}")
        elif block.get('type') == 'blank':
            print("  空行")