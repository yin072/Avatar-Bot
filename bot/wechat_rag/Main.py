from data_loader.Wx_Parser import WeChatDialogConverter
import os
import logging
import shutil
from data_loader.Qdrant_Loader import QdrantLoader


# 配置日志
logging.basicConfig(level=logging.INFO)

def process_folder(input_folder, output_folder):
    """处理CSV文件并转换为TXT，返回生成的txt文件个数"""
    os.makedirs(output_folder, exist_ok=True)
    converter = WeChatDialogConverter(my_name="我")
    txt_count = 0
    
    for dirpath, dirnames, filenames in os.walk(input_folder):  # 解包 os.walk() 的返回值
        for filename in filenames:  # 遍历文件名
            if filename.endswith('.csv'):  # 检查文件名后缀
                csv_path = os.path.join(dirpath, filename)  # 使用 dirpath 来构造完整的文件路径
                dialogs = converter.csv_to_dialogs(csv_path)
                
                if dialogs:
                    output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
                    converter.save_dialogs(dialogs, output_path)
                    txt_count += 1
    
    print(f"对话处理完成，结果已保存到输出文件夹，共生成 {txt_count} 个txt文件。")
    return txt_count

def process_qdrant(input_folder):
    qdrant_loader = QdrantLoader()
    qdrant_loader.process_files(input_folder)
    print("对话处理完成，结果已保存到Qdrant数据库。")

def clear_qdrant_data():
    """清理local_qdrant目录下的所有数据"""
    try:
        # 获取local_qdrant目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        qdrant_dir = os.path.join(os.path.dirname(current_dir), "local_qdrand")
        
        if os.path.exists(qdrant_dir):
            # 删除collection目录下的所有内容
            collection_dir = os.path.join(qdrant_dir, "collection")
            if os.path.exists(collection_dir):
                shutil.rmtree(collection_dir)
                os.makedirs(collection_dir, exist_ok=True)
                print(f"已清理Qdrant数据目录: {collection_dir}")
            
            # 删除.lock文件
            lock_file = os.path.join(qdrant_dir, ".lock")
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"已删除锁文件: {lock_file}")
            
            # 保留meta.json文件，但清空内容
            meta_file = os.path.join(qdrant_dir, "meta.json")
            if os.path.exists(meta_file):
                with open(meta_file, 'w', encoding='utf-8') as f:
                    f.write('{}')
                print(f"已清空元数据文件: {meta_file}")
            
            return True
        else:
            print(f"Qdrant目录不存在: {qdrant_dir}")
            return False
            
    except Exception as e:
        print(f"清理Qdrant数据失败: {e}")
        return False

def clear_all_files(folder_path):
    """清空指定文件夹下的所有csv和txt文件，同时清理local_qdrant数据"""
    cleared_files = []
    if os.path.exists(folder_path):
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith(('.csv', '.txt')):
                    file_path = os.path.join(dirpath, filename)
                    try:
                        os.remove(file_path)
                        cleared_files.append(filename)
                        print(f"已删除文件: {filename}")
                    except Exception as e:
                        print(f"删除文件 {filename} 失败: {e}")
    
    # 同时清理Qdrant数据
    qdrant_cleared = clear_qdrant_data()
    
    return len(cleared_files), cleared_files, qdrant_cleared

def process_wechat_data():
    """完整的微信数据处理流程：先清理Qdrant数据，然后CSV转TXT + 存入Qdrant + 返回txt文件个数"""
    input_folder = "wxdump_work\export"
    output_folder = "wxdump_work\export"

    if not os.path.exists(input_folder):
        logging.error(f"请导入聊天记录！")
        return 0
    
    # 先清理Qdrant数据
    print("开始清理Qdrant数据...")
    clear_qdrant_data()
    print("Qdrant数据清理完成")
    
    # 处理微信对话并保存为TXT，同时获取txt文件个数
    txt_count = process_folder(input_folder, output_folder)

    # 将处理后的对话数据存入 Qdrant
    process_qdrant(output_folder)
    
    return txt_count

if __name__ == "__main__":
    txt_count = process_wechat_data()
    print(f"完整流程执行完毕，共生成 {txt_count} 个txt文件")
