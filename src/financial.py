import pandas as pd
import numpy as np
from src.config import BLD, RAW, YEAR_RANGE


# Asset Data Processing
def process_asset_data(raw_dir):
    columns = {
        "Stkcd": "Stkcd",
        "Accper": "year",
        "A001000000": "total_asset",
        "A003100000": "net_asset",
        "A001100000": "current_asset",
        "A002100000": "current_liability",
        "A002101000": "short_debt",
        "A002201000": "long_debt",
        "A002203000": "bonds_payable",
        "A002211000": "leasing",
    }
    df_asset_file = raw_dir / 'csmar' / '基本信息' / '资产负债表024800027' / 'FS_Combas.csv'
    df_asset = pd.read_csv(df_asset_file, usecols=columns.keys(), dtype={'Stkcd': str}).rename(columns=columns)
    df_asset = df_asset.fillna(0)
    df_asset['year'] = pd.to_datetime(df_asset['year'], errors='coerce', format='%Y-%m-%d')  # 指定日期格式
    df_asset = df_asset[df_asset['year'].dt.month != 1]  # 删除所有 1 月的数据
    df_asset['year'] = df_asset['year'].dt.to_period('Q').astype(str)  # 转换为季度格式


    df_asset = df_asset[(df_asset['Stkcd'] >= "000001") & (df_asset['Stkcd'] <= "679999")]
    df_asset.loc[df_asset["total_asset"] == 0, "total_asset"] = np.nan  # 先替换 0 为 NaN
    df_asset = df_asset.dropna(subset=["total_asset"]) 
    df_asset["size"] = np.log(df_asset["total_asset"])
    df_asset["debt_ratio"] = (df_asset["short_debt"] + df_asset["long_debt"] + df_asset["bonds_payable"]) / df_asset["total_asset"]
    df_asset["nwc"] = (df_asset["current_asset"] - df_asset["current_liability"]) / df_asset["total_asset"]

    df_asset = df_asset[["Stkcd", "year", "total_asset", "size", "debt_ratio", "nwc", "net_asset"]]
    complete_quarters = {f"{year}Q{q}" for year in YEAR_RANGE for q in range(1, 5)}  
    company_year_counts = df_asset.groupby("Stkcd")["year"].apply(set)
    valid_companies = company_year_counts[company_year_counts.apply(lambda x: complete_quarters.issubset(x))].index
    return df_asset[df_asset["Stkcd"].isin(valid_companies)]

# Income Data Processing
def process_income_data(raw_dir):
    income_columns = {"Stkcd": "Stkcd", "Accper": "year", "B001100000": "revenue", "B002000101": "net_profit"}
    df_income_file = raw_dir / 'csmar' / '基本信息' / '利润表000222262' / 'FS_Comins.csv'
    df_income = pd.read_csv(df_income_file, usecols=income_columns.keys(), dtype={'Stkcd': str}).rename(columns=income_columns)
    df_income['year'] = pd.to_datetime(df_income['year'], errors='coerce', format='%Y-%m-%d')  # 指定日期格式
    df_income = df_income[df_income['year'].dt.month != 1]  # 删除所有 1 月的数据
    df_income['year'] = df_income['year'].dt.to_period('Q').astype(str)  # 转换为季度格式

    df_income = df_income[(df_income['Stkcd'] >= "000001") & (df_income['Stkcd'] <= "679999")]

    df_income['q_revenue'] = df_income.groupby('Stkcd')['revenue'].diff()
    df_income.loc[df_income['year'].str.endswith('Q1'), 'q_revenue'] = df_income['revenue']
    df_income = df_income.sort_values(by=["Stkcd", "year"])
    df_income['revenue_growth'] = df_income.groupby('Stkcd')['q_revenue'].pct_change(periods=4)
    df_income = df_income[df_income["revenue_growth"].notna()]
    df_income['q_profit'] = df_income.groupby('Stkcd')['net_profit'].diff()
    df_income.loc[df_income['year'].str.endswith('Q1'), 'q_profit'] = df_income['net_profit']

    complete_quarters = {f"{year}Q{q}" for year in YEAR_RANGE for q in range(1, 5)}  
    company_year_counts = df_income.groupby("Stkcd")["year"].apply(set)
    valid_companies = company_year_counts[company_year_counts.apply(lambda x: complete_quarters.issubset(x))].index
    return df_income[df_income["Stkcd"].isin(valid_companies)]

# Basic Information Processing
def process_basic_data(raw_dir):
    df_basic_file = raw_dir / 'csmar' / '基本信息' / '上市公司基本信息年度表215937759' / 'STK_LISTEDCOINFOANL.csv'
    df_basic = pd.read_csv(df_basic_file, dtype={'Symbol': str}).fillna(0)

    df_basic = df_basic.assign(
    year=pd.to_datetime(df_basic["EndDate"]).dt.year.astype(int),
    industry=df_basic['IndustryCode'].str[0]
    )
    df_basic.rename(columns={'Symbol': 'Stkcd'}, inplace=True)
    df_basic = df_basic[(df_basic['Stkcd'] >= "000001") & (df_basic['Stkcd'] <= "679999")]

    complete_years = set(YEAR_RANGE) 
    company_year_counts = df_basic.groupby('Stkcd')['year'].apply(set)
    companies_with_full_coverage = company_year_counts[company_year_counts.apply(lambda x: complete_years.issubset(x))].index
    df_basic = df_basic[df_basic['Stkcd'].isin(companies_with_full_coverage)]
    
    industry_changes = df_basic.loc[df_basic['year'].between(2014, 2019)].groupby('Stkcd')['industry'].apply(set)
    companies_with_changes = industry_changes[industry_changes.apply(len) > 1].index
    return df_basic[~df_basic['Stkcd'].isin(companies_with_changes)]

# Main Function
def clean_financial():
    df_asset = process_asset_data(RAW)
    df_income = process_income_data(RAW)
    df_basic = process_basic_data(RAW)
    df_merged = pd.merge(df_income, df_asset, on=["Stkcd", "year"])

    df_merged = df_merged.assign(
    roe=df_merged["q_profit"] / df_merged["net_asset"],
    roa=df_merged["q_profit"] / df_merged["total_asset"]
    ).drop(columns=["total_asset", "net_asset", "revenue", "net_profit", 'q_profit', 'q_revenue'])

    df_merged["year_int"] = df_merged["year"].str[:4].astype(int)


    df_basic = df_basic[["Stkcd", "year", "industry"]]
    df_final = pd.merge(df_merged, df_basic, left_on=["Stkcd", "year_int"], right_on=["Stkcd", "year"], how="inner")
    df_final = df_final.rename(columns={'year_x': 'year'}).drop(columns=['year_y', 'year_int'])
    complete_quarters = {f"{year}Q{q}" for year in YEAR_RANGE for q in range(1, 5)}
    df_final = df_final[df_final['year'].isin(complete_quarters)]
    
    output_file = BLD / 'financial_data2.parquet'
    df_final.to_parquet(output_file, index=False)
    print(f"Processed data saved to {output_file}")

if __name__ == "__main__":
    clean_financial()