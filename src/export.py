import pandas as pd
import numpy as np
from src.config import BLD, RAW, YEAR_RANGE
import pdfplumber
import re

df_basic_file = RAW/'csmar'/'基本信息'/'上市公司基本信息年度表215937759'/'STK_LISTEDCOINFOANL.csv'
df_basic = pd.read_csv(df_basic_file, dtype={'Symbol': str})
df_basic = df_basic.fillna(0) 
df_basic["year"] = pd.to_datetime(df_basic["EndDate"]).dt.year.astype(int)
df_basic.rename(columns={'Symbol': 'Stkcd'}, inplace=True)
df_basic = df_basic[(df_basic['Stkcd'] >= "000001") & (df_basic['Stkcd'] <= "679999")]
df_basic['Industry_Main'] = df_basic['IndustryCode'].str[0]
industry_changes = df_basic[df_basic['year'].between(2014, 2019)].groupby('Stkcd')['Industry_Main'].apply(set)

# 筛选出行业代码集合长度大于1的公司，表示发生过行业代码变化
companies_with_changes = industry_changes[industry_changes.apply(len) > 1].index

df_basic = df_basic[~df_basic['Stkcd'].isin(companies_with_changes)]
df_basic = df_basic[df_basic['Industry_Main'] != 'G']
df_basic = df_basic[df_basic['Industry_Main'] != 'K']
#df_basic = df_basic[df_basic['Stkcd'] != '000595']


###################################################################################

df_subsidiary_file = RAW/'csmar'/'基本信息'/'上市公司子公司情况表220415924'/'FN_Fn061.csv'
df_subsidiary = pd.read_csv(df_subsidiary_file, dtype={'Stkcd': str})
df_subsidiary["year"] = pd.to_datetime(df_subsidiary["EndDate"]).dt.year.astype(int)
df_subsidiary = df_subsidiary[(df_subsidiary['Stkcd'] >= "000001") & (df_subsidiary['Stkcd'] <= "679999")]

industry_changes = df_basic[df_basic['year'].between(2014, 2019)].groupby('Stkcd')['Industry_Main'].apply(set)
companies_with_changes = industry_changes[industry_changes.apply(len) > 1].index
df_subsidiary = df_subsidiary[~df_subsidiary['Stkcd'].isin(companies_with_changes)]
df_basic['company'] = df_basic['FullName']  # 母公司名称列
df_subsidiary['company'] = df_subsidiary['FN_Fn06101']
merged_df_list = pd.concat(
    [
        df_basic[['Stkcd', 'year', 'company']], 
        df_subsidiary[['Stkcd', 'year', 'company']],
    ],
    axis=0,
    ignore_index=True
)
merged_df_list.sort_values(by=['Stkcd', 'year'], inplace=True)
##########################################################################################
df_export_file = RAW / 'cn_custom_data'/'2014_2016_export_data.parquet'
df_export = pd.read_parquet(df_export_file)
result_df = pd.merge(
    merged_df_list,  # 包含母公司和子公司名称的表
    df_export[['Company_Name', 'Year', 'Country_Name', 'Export_Amount', 'Product_Code']],
    left_on=['company', 'year'],
    right_on=['Company_Name', 'Year'],
    how='inner'
)
result_df['hs_code'] = result_df['Product_Code'].astype(str).str[:6].astype(int)
# 筛选出出口美国的数据
df_usa = result_df[result_df['Country_Name'] == '美国']
exchange_rates = {2014: 6.128333, 2015: 6.205000, 2016: 6.614167}
df_usa = df_usa.copy()

# 计算转换后的金额
df_usa['export'] = df_usa.apply(lambda row: row['Export_Amount'] * exchange_rates[row['year']], axis=1)

# 按HS代码、公司代码、年份分类
grouped_df = df_usa.groupby(['Stkcd', 'year', 'hs_code'], as_index=False).agg({
    'Export_Amount': 'sum',  # 汇总出口金额
    'export': 'sum'  # 汇总转换后的金额
})

# 按公司代码（Stkcd）和年份（year）排序
df_usa = grouped_df.sort_values(by=['Stkcd', 'year']).reset_index(drop=True)
# 筛选出至少有2年数据的公司代码
company_year_counts = df_usa.groupby('Stkcd')['year'].nunique()
valid_companies = company_year_counts[company_year_counts >= 2].index

# 筛选出这些公司代码对应的行
df_usa = df_usa[df_usa['Stkcd'].isin(valid_companies)]
# 计算2014-2016年的公司-商品组合的平均出口金额
df_usa_avg = df_usa.groupby(['Stkcd', 'hs_code'])['export'].mean().reset_index()

# 重命名列
df_usa_avg.rename(columns={'export': 'avg_export_amount'}, inplace=True)

####################################################################################
pdf_path = RAW/'us_tariff'/'FRN301.pdf'
all_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        all_text += page.extract_text() + " "

# Continue with your regex extraction as before
hts_codes = re.findall(r'\b\d{8}\b', all_text)
hts_prefixes = {code[:6] for code in hts_codes}
hts_list_1 = sorted(hts_prefixes)


pdf_path = RAW/'us_tariff'/'list_2.pdf'  # 替换为您的PDF路径

all_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page_number in range(4, 9):  # 页码从 0 开始，第 5 页是索引 4
        page = pdf.pages[page_number]
        all_text += page.extract_text() + " "

# 使用正则表达式提取8位 HTSUS 代码

hts_codes = re.findall(r'\b\d{4}\.\d{2}\.\d{2}\b', all_text)

# 格式化为6位代码（去掉圆点和后两位）
hts_prefixes = {code.replace(".", "")[:6] for code in hts_codes}
hts_list_2 = sorted(hts_prefixes)


pdf_path = RAW/'us_tariff'/'list_3.pdf'  # 替换为您的PDF路径

# 合并所有页面的文本
all_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page_number in range(3, 28): 
        page = pdf.pages[page_number]
        all_text += page.extract_text() + " "

# 使用正则提取所有符合8位格式的代码
hts_codes = re.findall(r'\b\d{4}\.\d{2}\.\d{2}\b', all_text)

# 格式化为6位代码（去掉圆点和后两位）
hts_prefixes = {code.replace(".", "")[:6] for code in hts_codes}

# 排序结果
hts_list_3 = sorted(hts_prefixes)


# 文件路径
pdf_path = RAW/'us_tariff'/'list_4.pdf'  # 替换为您的PDF路径

# 合并所有页面的文本
all_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page_number in range(3, 25): 
        page = pdf.pages[page_number]
        all_text += page.extract_text() + " "

# 使用正则提取所有符合8位格式的代码
hts_codes = re.findall(r'\b\d{4}\.\d{2}\.\d{2}\b', all_text)

# 格式化为6位代码（去掉圆点和后两位）
hts_prefixes = {code.replace(".", "")[:6] for code in hts_codes}

# 排序结果
hts_list_4 = sorted(hts_prefixes)

set1 = set(hts_list_1)
set2 = set(hts_list_2)
set3 = set(hts_list_3)
set4 = set(hts_list_4)
set5 = set1 | set2 | set3 
set6 = (set4 - set5)
hts_list_1_3 = sorted([int(item) for item in set5])
hts_list_4 = sorted([int(item) for item in set6])

df_usa_avg['affected_1_3'] = df_usa_avg['hs_code'].isin(hts_list_1_3)
df_usa_avg['affected_4'] = df_usa_avg['hs_code'].isin(hts_list_4)

# 按公司代码计算总金额
df_total = df_usa_avg.groupby('Stkcd')['avg_export_amount'].sum().reset_index()
df_total.rename(columns={'avg_export_amount': 'total_export_amount'}, inplace=True)

# 按公司代码计算受影响金额
df_1_3 = df_usa_avg[df_usa_avg['affected_1_3']].groupby('Stkcd')['avg_export_amount'].sum().reset_index()
df_1_3.rename(columns={'avg_export_amount': 'amount_affected_1_3'}, inplace=True)

df_4 = df_usa_avg[df_usa_avg['affected_4']].groupby('Stkcd')['avg_export_amount'].sum().reset_index()
df_4.rename(columns={'avg_export_amount': 'amount_affected_4'}, inplace=True)

# 合并结果
result = pd.merge(df_total, df_1_3, on='Stkcd', how='left')
result = pd.merge(result, df_4, on='Stkcd', how='left')

result.fillna(0, inplace=True)


##################################################################################
income_columns = {"Stkcd": "Stkcd","Accper": "year", "B001100000": "revenue"}
df_income_file = RAW/'csmar'/'基本信息'/'利润表000222262'/'FS_Comins.csv'
df_income = pd.read_csv(df_income_file, usecols=income_columns.keys(), dtype={'Stkcd': str}).rename(columns=income_columns)
df_income.loc[:, "year"] = pd.to_datetime(df_income["year"]).dt.year
df_income = df_income[(df_income['Stkcd'] >= "000001") & (df_income['Stkcd'] <= "679999")]
merged_df = pd.merge(df_income, df_basic[['Stkcd', 'year', 'Industry_Main']], on=['Stkcd', 'year'], how='left')
merged_df = merged_df.dropna()  # 去掉包含 NaN 的行
average_revenue_df = (
    merged_df[(merged_df['year'] >= 2014) & (merged_df['year'] <= 2016)]
    .groupby('Stkcd')['revenue']
    .mean()
    .reset_index()
    .rename(columns={'revenue': 'average_revenue'})
)
merged_df = pd.merge(average_revenue_df, result, on='Stkcd', how='left').fillna(0)
merged_df['ratio_affected_1_3'] = merged_df['amount_affected_1_3'] / merged_df['average_revenue']
merged_df['ratio_affected_4'] = merged_df['amount_affected_4'] / merged_df['average_revenue']
merged_df = merged_df[merged_df["total_export_amount"] > 0]
#############################################
threshold_1_3 = 0.1
threshold_4 = 0.1

def classify_impact(row):
    if row['ratio_affected_1_3'] > threshold_1_3 and row['ratio_affected_4'] > threshold_4:
        return 3  # both impacted
    elif row['ratio_affected_1_3'] > threshold_1_3:
        return 1  # list1-3
    elif row['ratio_affected_4'] > threshold_4:
        return 2  # list4
    else:
        return 4  # unaffected

# 新增分类列
merged_df['impact_category'] = merged_df.apply(classify_impact, axis=1)
df_c = merged_df.loc[merged_df['Industry_Main'] == 'C', :].copy()
df_c.loc[:, 'treatment'] = df_c['impact_category'].apply(lambda x: 1 if x in [1, 2, 3] else 0)
df_c = df_c[['Stkcd', 'treatment']]
df_c.loc[:, 'year'] = '2018Q3'
df_c
######################################
df_fi_file_2 = BLD/ 'financial_data2.parquet'
df_fi_2 = pd.read_parquet(df_fi_file_2)
df_filtered = df_fi_2[df_fi_2['Stkcd'].isin(df_c['Stkcd'])]
df_filtered2 = pd.merge(df_filtered, df_c[['Stkcd', 'year','treatment']], on= ['Stkcd', 'year'], how='left')
df_filtered2['treatment'] = df_filtered2['treatment'].fillna(0).astype(int)  # 未匹配的默认为 0
df_filtered2['treatment_post'] = df_filtered2['treatment'].cumsum().clip(upper=1)
######################
def load_financial_data(bld_path):
    """
    加载财务数据。

    :param bld_path: 财务数据所在目录（Path对象）
    :return: DataFrame
    """
    df_fi_file_2 = bld_path / 'financial_data2.parquet'
    return pd.read_parquet(df_fi_file_2)

def filter_and_merge_financial_data(df_fi_2, df_c):
    """
    筛选财务数据中符合 df_c 公司的数据，并合并 treatment 变量。

    :param df_fi_2: 财务数据 DataFrame
    :param df_c: 处理后的行业 C 数据 DataFrame
    :return: 处理后的 DataFrame
    """
    # 筛选符合条件的公司
    df_filtered = df_fi_2[df_fi_2['Stkcd'].isin(df_c['Stkcd'])]

    # 合并 treatment 变量
    df_filtered2 = pd.merge(df_filtered, df_c[['Stkcd', 'year', 'treatment']], on=['Stkcd', 'year'], how='left')

    # 未匹配的默认为 0
    df_filtered2['treatment'] = df_filtered2['treatment'].fillna(0).astype(int)

    # 计算 post-treatment 变量（累计到 1）
    df_filtered2['treatment_post'] = df_filtered2['treatment'].cumsum().clip(upper=1)

    return df_filtered2
