import pandas as pd
import re
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class WeChatDialogConverter:
    def __init__(self, my_name="我"):
        self.my_name = my_name
        self._privacy_patterns = {
            'phone': re.compile(r'(?<!\d)(1[3-9]\d{9})(?!\d)'),
            'id_card': re.compile(r'([1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx])')
        }
    
    def csv_to_dialogs(self, csv_path: str) -> List[str]:
        """将CSV文件转换为对话文本列表"""
        try:
            df = pd.read_csv(csv_path)
            dialogs = []
            
            for _, row in df.iterrows():
                if pd.isna(row.get('msg')) or str(row['msg']).strip() == "":
                    continue
                
                # 确定发言人
                speaker = self.my_name if int(row['is_sender']) == 1 else row['talker']
                
                # 清洗消息内容
                cleaned_msg = self._clean_content(str(row['msg']))
                
                # 格式化时间 (可选)
                time_str = self._format_time(row['CreateTime'])
                
                # 构建对话行
                dialog_line = f"{speaker} ({time_str}): {cleaned_msg}"
                dialogs.append(dialog_line)
            
            return dialogs
            
        except Exception as e:
            logger.error(f"处理CSV文件失败: {e}")
            return []

    def _clean_content(self, text: str) -> str:
        """清洗消息中的隐私信息"""
        text = self._privacy_patterns['phone'].sub('[手机号]', text)
        text = self._privacy_patterns['id_card'].sub('[身份证]', text)
        return text.strip()

    def _format_time(self, time_str: str) -> str:
        """简化时间显示"""
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%H:%M")
        except:
            return time_str[:5]  # 取前5个字符 "18:30"

    def save_dialogs(self, dialogs: List[str], output_path: str):
        """保存对话到文本文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(dialogs))
        logger.info(f"已保存 {len(dialogs)} 条对话到 {output_path}")