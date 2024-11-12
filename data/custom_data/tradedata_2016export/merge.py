#dta

import pandas as pd

import os

# 指定文件夹路径
folder_path = os.getcwd()  # 替换为你的文件夹路径

# 获取文件夹中的所有 .dta 文件
file_paths = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.dta')]

# 读取所有的 .dta 文件

total_rows = 0

# 读取所有的 .dta 文件，并计算每个文件的行数
dfs = []
for file in file_paths:
    df = pd.read_stata(file)
    dfs.append(df)
    total_rows += len(df)
    print(f"{file} 行数: {len(df)}")

# 按行合并
merged_df = pd.concat(dfs, ignore_index=True)

# 打印合并后的数据
print(merged_df.head())

# 打印合并后的总行数
print(f"合并后的总行数: {len(merged_df)}")
print(f"原始文件的总行数: {total_rows}")

# 检查合并后的总行数是否等于原始文件的总行数
if len(merged_df) == total_rows:
    print("合并后的数据包含所有原始文件中的行数据！")
    # 保存为 Parquet 文件
    merged_df.to_parquet('merged_data.parquet', index=False)
else:
    print("警告：合并后的数据行数与原始文件总行数不匹配。")

