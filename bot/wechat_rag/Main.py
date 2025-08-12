from data_loader.Wx_Parser import WeChatDialogConverter
import os
import logging
from data_loader.Qdrant_Loader import QdrantLoader


# 配置日志
logging.basicConfig(level=logging.INFO)

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    converter = WeChatDialogConverter(my_name="我")
    
    for dirpath, dirnames, filenames in os.walk(input_folder):  # 解包 os.walk() 的返回值
        for filename in filenames:  # 遍历文件名
            if filename.endswith('.csv'):  # 检查文件名后缀
                csv_path = os.path.join(dirpath, filename)  # 使用 dirpath 来构造完整的文件路径
                dialogs = converter.csv_to_dialogs(csv_path)
                
                if dialogs:
                    output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
                    converter.save_dialogs(dialogs, output_path)
    
    print("对话处理完成，结果已保存到输出文件夹。")

def process_qdrant(input_folder):
    qdrant_loader = QdrantLoader()
    qdrant_loader.process_files(input_folder)
    print("对话处理完成，结果已保存到Qdrant数据库。")

if __name__ == "__main__":
    input_folder = "wxdump_work\export"
    output_folder = "wxdump_work\export"

    if not os.path.exists(input_folder):
        logging.error(f"请导入聊天记录！")
    else:
        # 处理微信对话并保存为TXT
        process_folder(input_folder, output_folder)

        # 将处理后的对话数据存入 Qdrant
        process_qdrant(output_folder)
