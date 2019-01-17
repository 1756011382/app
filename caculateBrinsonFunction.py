# -*- coding: utf-8 -*-
"""
本文件设计目标：定义brison分解，归因的各个逻辑函数，供etl数据生产和实时计算调用。保证逻辑统一
主要包括：
1 计算产品和基准每日行业权重、收益率
2 计算brison每日明细
3 计算产品行业平均权重和收益率
"""
import datetime
import pandas as pd
import numpy as np

from pymom.finandata import funddata, derivativedata
from pymom.model.pyffn import brison
import time
from pymom.finandata.funddata import getfofproductlist
def cacu_BaseData(para_dict):
    '''
    计算产品和基准每日行业权重、收益率
    '''
    out = dict()
# =============================================================================
# #计算产品数据
# =============================================================================
    st = datetime.datetime.strptime(para_dict['startdate'],'%Y-%m-%d')
    et = datetime.datetime.strptime(para_dict['enddate'],'%Y-%m-%d')


#    t0=time.time()
#    #提取产品净值 根据产品代码，开始结束时间，查出产品的单位净值
#    fundnav = funddata.getFundNAV1([para_dict['port_code']],para_dict['startdate'],para_dict['enddate'])
#    if fundnav.empty:
#        return dict()
#    print(time.time()-t0)
##    提取持仓 根据产品代码，开始结束时间，查出产品的持仓   
#    fund_stk_hlds = funddata.getFundStockHoldings1([para_dict['port_code']],para_dict['startdate'],para_dict['enddate'])
####    # 当持仓为空，就不做计算
#    if fund_stk_hlds.empty:
#        return dict()
###
#    #分解产品的大类资产配置 ： A股，港股，其他
#     #新增将总资产改为净资产
#    fund_assetallocation,fund_ag_stk_holdings,fund_hk_stk_holdings = funddata.cacu_FundAssetsAllocation(fundnav[['port_code','enddate','fund_cumulative_nav','total_asset']] ,fund_stk_hlds)
    FOFproductList = getfofproductlist()
    if para_dict['port_code'] in FOFproductList:   
        fund_assetallocation = derivativedata.getassetallocation(para_dict['port_code'], para_dict['startdate'], para_dict['enddate'], 'fes_mom_stock_weight')
    else:
        fund_assetallocation = derivativedata.getassetallocation(para_dict['port_code'], para_dict['startdate'], para_dict['enddate'], 'fes_stock_weight')
    if fund_assetallocation.empty:
        return dict()

    dateindex = pd.DatetimeIndex(fund_assetallocation.enddate)

    #分解产品的行业配置及收益率
    fund_ag_stock_hy_df = derivativedata.getFundClassWeight(para_dict['port_code'],st,et,para_dict['standard'],'AG')
    if not fund_ag_stock_hy_df.empty:

        # 捕获异常，是为了防止某一天港股或者A股突然新增或者抛掉，又或者数据缺失
        try:
            fund_ag_stock_hy_r = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
            fund_ag_stock_hy_w = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].replace(np.nan,0).ffill()
        except:
            fund_ag_stock_hy_r = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='rtn').replace(np.nan,0)
            fund_ag_stock_hy_w = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='weight').replace(np.nan,0).ffill()
    else:
        fund_ag_stock_hy_r = pd.DataFrame()
        fund_ag_stock_hy_w = pd.DataFrame()


    fund_hk_stock_hy_df = derivativedata.getFundClassWeight(para_dict['port_code'],st,et,para_dict['standard'],'HK')
    if not fund_hk_stock_hy_df.empty:
        # 捕获异常，是为了防止某一天港股或者A股突然新增或者抛掉，又或者数据缺失
        try:
            fund_hk_stock_hy_r = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
            fund_hk_stock_hy_w = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].replace(np.nan,0).ffill()
        except:
            fund_hk_stock_hy_r = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='rtn').replace(np.nan,0)
            fund_hk_stock_hy_w = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='weight').replace(np.nan,0).ffill()

    else:
        fund_hk_stock_hy_r = pd.DataFrame()
        fund_hk_stock_hy_w = pd.DataFrame()

    fund_assetsrtn = funddata.cacu_FundAssetsReturn(fund_assetallocation,fund_ag_stock_hy_w, fund_ag_stock_hy_r,fund_hk_stock_hy_w,fund_hk_stock_hy_r)

    out['fund_ag_stock_hy_r']=fund_ag_stock_hy_r
    out['fund_ag_stock_hy_w']=fund_ag_stock_hy_w
    out['fund_hk_stock_hy_r']=fund_hk_stock_hy_r
    out['fund_hk_stock_hy_w']=fund_hk_stock_hy_w


# =============================================================================
# #虚拟构造一个业绩基准
# =============================================================================

    benchmarklist_ag = para_dict['benchmarklist_ag']
    benchmarklist_hk = para_dict['benchmarklist_hk']

    #计算指数的的行业配置及收益率

    benchmark_ag_stock_hy_df = derivativedata.getIndexClassWeight(benchmarklist_ag,dateindex[0],dateindex[-1],para_dict['standard'])
    if not benchmark_ag_stock_hy_df.empty:

        benchmark_ag_stock_hy_r = pd.pivot_table(benchmark_ag_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        benchmark_ag_stock_hy_w = pd.pivot_table(benchmark_ag_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].replace(np.nan,0).ffill()

    else:
        benchmark_ag_stock_hy_r = pd.DataFrame()
        benchmark_ag_stock_hy_w = pd.DataFrame()

    

    benchmark_hk_stock_hy_df = derivativedata.getIndexClassWeight(benchmarklist_hk,dateindex[0],dateindex[-1],para_dict['standard'])
    if not benchmark_hk_stock_hy_df.empty:

        benchmark_hk_stock_hy_r = pd.pivot_table(benchmark_hk_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        benchmark_hk_stock_hy_w = pd.pivot_table(benchmark_hk_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].replace(np.nan,0).ffill()
    else:
        benchmark_hk_stock_hy_r = pd.DataFrame()
        benchmark_hk_stock_hy_w = pd.DataFrame()


    out['benchmark_ag_stock_hy_r']=benchmark_ag_stock_hy_r
    out['benchmark_ag_stock_hy_w']=benchmark_ag_stock_hy_w
    out['benchmark_hk_stock_hy_r']=benchmark_hk_stock_hy_r
    out['benchmark_hk_stock_hy_w']=benchmark_hk_stock_hy_w





    #业绩基准的大类资产权重和产品的一致。
    benchmark_nav = fund_assetallocation[['enddate','ag_stk_wght','hk_stk_wght','other_wght']]


    #计算基准的收益率
    benchmark_ag_stock_hy_w = benchmark_ag_stock_hy_w.replace(np.nan,0)
    ag_stk_rtn=(benchmark_ag_stock_hy_r*benchmark_ag_stock_hy_w.shift(1)).sum(axis = 1).reset_index()
    ag_stk_rtn.columns=['enddate','ag_stock_rtn']

    benchmark_hk_stock_hy_w = benchmark_hk_stock_hy_w.replace(np.nan,0)
    hk_stk_rtn=(benchmark_hk_stock_hy_r*benchmark_hk_stock_hy_w.shift(1)).sum(axis = 1).reset_index()
    hk_stk_rtn.columns=['enddate','hk_stock_rtn']


    benchmark_nav = pd.merge(benchmark_nav,ag_stk_rtn,how='left',on=['enddate']).replace(np.nan,0)
    benchmark_nav = pd.merge(benchmark_nav,hk_stk_rtn,how='left',on=['enddate']).replace(np.nan,0)
    benchmark_nav = pd.merge(benchmark_nav,fund_assetsrtn[['enddate','other_rtn']],how='left',on=['enddate']).replace(np.nan,0)
    benchmark_nav['total_rtn']=benchmark_nav['ag_stk_wght'].shift(1)*benchmark_nav['ag_stock_rtn']+\
                                benchmark_nav['hk_stk_wght'].shift(1)*benchmark_nav['hk_stock_rtn']+\
                                benchmark_nav['other_wght'].shift(1)*benchmark_nav['other_rtn']
    benchmark_nav['total_rtn']=benchmark_nav['total_rtn'].replace(np.nan,0)


    #构造出基准的净值曲线
    benchmark_nav['fund_cumulative_nav']=(benchmark_nav['total_rtn']+1).cumprod()
    benchmark_nav['total_asset']=benchmark_nav['fund_cumulative_nav']
    benchmark_nav['port_code']=benchmarklist_ag+'-'+benchmarklist_hk



    benchmark_assetallocation = benchmark_nav[['port_code', 'enddate', 'fund_cumulative_nav', 'total_asset',
        'ag_stk_wght', 'hk_stk_wght','other_wght', 'total_rtn']]

    benchmark_assetallocation.loc[:,'ag_stk_mkv']=benchmark_assetallocation['total_asset']*benchmark_assetallocation['ag_stk_wght']
    benchmark_assetallocation.loc[:,'hk_stk_mkv']=benchmark_assetallocation['total_asset']*benchmark_assetallocation['hk_stk_wght']
    benchmark_assetallocation.loc[:,'other_mkv']=benchmark_assetallocation['total_asset']*benchmark_assetallocation['other_wght']


    #计算基准产品收益率
    benchmark_assetsrtn = funddata.cacu_FundAssetsReturn(benchmark_assetallocation,benchmark_ag_stock_hy_w, benchmark_ag_stock_hy_r,benchmark_hk_stock_hy_w,benchmark_hk_stock_hy_r)




   #调整后的brison#计算调整系数矩阵
    kk = brison._cacu_k(fund_assetsrtn['total_rtn_cum'].iloc[-1],benchmark_assetsrtn['total_rtn_cum'].iloc[-1])
    kt=[]
    for i in range(0,len(fund_assetsrtn)):
        k1 = brison._cacu_k(fund_assetsrtn['total_rtn'][i],benchmark_assetsrtn['total_rtn'][i])
        k2 = fund_assetsrtn['enddate'][i]
        ki=[kk,k1,k2]
        kt.append(ki)
    kt_df = pd.DataFrame(kt,columns=['kk','k_t','enddate'])

    out['kt_df']=kt_df

    #合并产品和基准指数基本要输
    out['fund_ctr_df']=pd.merge(fund_assetallocation,fund_assetsrtn,on=['port_code','enddate','total_rtn'])
    out['benchmark_ctr_df']=pd.merge(benchmark_assetallocation,benchmark_assetsrtn,on=['port_code','enddate','total_rtn'])
    return  out

#第一层分解效应(组合组合累计超额收益的分解) 各个市场的收益率、总收益率，跟权重
def getrpt_contribution_summary(out):
    '''
    计算brison报告需要的各类资产汇总贡献
    '''
    cls1=['port_code','total_rtn_ctr_cum','ag_stock_rtn_ctr_cum','hk_stock_rtn_ctr_cum','other_rtn_ctr_cum']
    cls2=['ag_stk_wght','hk_stk_wght','other_wght']

#    fund_ctr1 = pd.concat([out['fund_ctr_df'][cls1].iloc[-1,:],out['fund_ctr_df'][cls2].mean()])
    fund_ctr1 = out['fund_ctr_df'][cls1].iloc[-1,:].append(out['fund_ctr_df'][cls2].mean())
#    benchmark_ctr1 = pd.concat([out['benchmark_ctr_df'][cls1].iloc[-1,:],out['benchmark_ctr_df'][cls2].mean()])
    benchmark_ctr1 = out['benchmark_ctr_df'][cls1].iloc[-1,:].append(out['benchmark_ctr_df'][cls2].mean())

    cmp_ctr_df = pd.concat([fund_ctr1,benchmark_ctr1],axis = 1).T
    return cmp_ctr_df

def getrpt_contribution_summary_ts(out):
    '''
    计算brison报告需要的各类资产汇总贡献
    '''
    cls1=['port_code','enddate','total_rtn_ctr_cum','ag_stock_rtn_ctr_cum','hk_stock_rtn_ctr_cum','other_rtn_ctr_cum']
    cls2=['ag_stk_wght','hk_stk_wght','other_wght']
    
    ndays=len(out['fund_ctr_df'])
    wght=out['fund_ctr_df'][cls2]
    wght_cnts=pd.DataFrame([np.arange(1,ndays+1),np.arange(1,ndays+1),np.arange(1,ndays+1)]).T
    wght_avg_move=np.divide(wght.cumsum(),wght_cnts)

    fund_ctr1 =pd.concat([out['fund_ctr_df'][cls1],wght_avg_move],axis=1)
    fund_ctr1=fund_ctr1.replace(np.nan,0)

    return fund_ctr1

def getrpt_brison_detail_industry(brison_detail ):
    '''
    行行业纬度汇总计算产品的brison贡献
    '''
    if not brison_detail.empty:
        gp_hy = brison_detail.groupby('Industry')
        brison_ctr_hy_df = gp_hy[[  'RP_s_t', 'RB_s_t', 'TR_t','PR_t', 'AR_t','SR_t', 'IR_t']].sum().replace(np.nan,0).reset_index()
        brison_ctr_hy_df['ARSRIR_sum']=brison_ctr_hy_df[['AR_t','SR_t', 'IR_t']].sum(axis=1) #AR，SR，IR 求和
    else:
        brison_ctr_hy_df = pd.DataFrame()

    return  brison_ctr_hy_df


def getrpt_brison_detail(ag_brison_detail,hk_brison_detail):
    '''
    计算产品brison汇总值
    '''
    if not  ag_brison_detail.empty:
        ag_gp = ag_brison_detail.groupby('enddate')
        ag_brison_ctr_df1 = ag_gp[[ 'PR_t', 'AR_t','SR_t', 'IR_t']].sum()
        ag_brison_ctr_df2 = ag_gp[[ 'RP_s_t', 'RB_s_t', 'TR_t']].mean()
        ag_brison_ctr_df = pd.merge(ag_brison_ctr_df2,ag_brison_ctr_df1,left_index = True,right_index = True).replace(np.nan,0)
    else:
        ag_brison_ctr_df = pd.DataFrame()

    if not  hk_brison_detail.empty:
        hk_gp = hk_brison_detail.groupby('enddate')
        hk_brison_ctr_df1 = hk_gp[[ 'PR_t', 'AR_t','SR_t', 'IR_t']].sum()
        hk_brison_ctr_df2 = hk_gp[[ 'RP_s_t', 'RB_s_t', 'TR_t']].mean()
        hk_brison_ctr_df = pd.merge(hk_brison_ctr_df2,hk_brison_ctr_df1,left_index = True,right_index = True).replace(np.nan,0)
    else:
        hk_brison_ctr_df = pd.DataFrame()

    if (ag_brison_ctr_df.empty) and (not hk_brison_ctr_df.empty) :
        ag_brison_ctr_df = np.nan*hk_brison_ctr_df
    elif (not ag_brison_ctr_df.empty) and ( hk_brison_ctr_df.empty) :
        hk_brison_ctr_df = np.nan*ag_brison_ctr_df

    total_brison_ctr_df = pd.merge(ag_brison_ctr_df,hk_brison_ctr_df,left_index = True,right_index = True,suffixes=('_ag','_hk'),how='outer').replace(np.nan,0)

    return total_brison_ctr_df


def getrpt_industry_weight_rtn(out ):
    '''
    计算产品在一段时间内的平均权重和收益率
    '''
    fund_ag_stk_wght_mean = out['fund_ag_stock_hy_w'].multiply(out['fund_ctr_df'].set_index('enddate')['ag_stk_wght'],axis = 0).replace(np.nan,0).mean().T
    fund_hk_stk_wght_mean = out['fund_hk_stock_hy_w'].multiply(out['fund_ctr_df'].set_index('enddate')['hk_stk_wght'],axis = 0).replace(np.nan,0).mean().T

    benchmark_ag_stk_wght_mean = out['benchmark_ag_stock_hy_w'].multiply(out['benchmark_ctr_df'].set_index('enddate')['ag_stk_wght'],axis = 0).replace(np.nan,0).mean().T
    benchmark_hk_stk_wght_mean = out['benchmark_hk_stock_hy_w'].multiply(out['benchmark_ctr_df'].set_index('enddate')['hk_stk_wght'],axis = 0).replace(np.nan,0).mean().T

    industry_wt_ag = pd.concat([fund_ag_stk_wght_mean,benchmark_ag_stk_wght_mean],axis = 1).replace(np.nan,0)
    industry_wt_ag.columns=['fund_ag_weight','benchmark_ag_weight']
    industry_wt_hk = pd.concat([fund_hk_stk_wght_mean,benchmark_hk_stk_wght_mean],axis = 1).replace(np.nan,0)
    industry_wt_hk.columns=['fund_hk_weight','benchmark_hk_weight']



    '''
      modified by hc at 2018-09-29
      此处与66行fund_assetsrtn计算贡献前后不一致
      不一致的差异在于，前面用的行业权重为昨日，净值为昨日，股票权重为昨日，
      而此处除了净值是昨日净值，行业权重和股票权重用的都是今日的
    '''
    
    fund_ag_stk_rtn_sum=(out['fund_ag_stock_hy_r']*out['fund_ag_stock_hy_w'].shift(1)).\
        multiply(out['fund_ctr_df'].set_index('enddate')['ag_stk_wght'].shift(1),axis = 0).\
        multiply(out['fund_ctr_df'].set_index('enddate')['nav'].shift(1),axis = 0).\
        replace(np.nan,0).sum().T

    fund_hk_stk_rtn_sum=(out['fund_hk_stock_hy_r']*out['fund_hk_stock_hy_w'].shift(1)).\
        multiply(out['fund_ctr_df'].set_index('enddate')['hk_stk_wght'].shift(1),axis = 0).\
        multiply(out['fund_ctr_df'].set_index('enddate')['nav'].shift(1),axis = 0).\
        replace(np.nan,0).sum().T


    benchmark_ag_stk_rtn_sum=(out['benchmark_ag_stock_hy_r']*out['benchmark_ag_stock_hy_w'].shift(1)).\
        multiply(out['benchmark_ctr_df'].set_index('enddate')['ag_stk_wght'].shift(1),axis = 0).\
        multiply(out['benchmark_ctr_df'].set_index('enddate')['nav'].shift(1),axis = 0).\
        replace(np.nan,0).sum().T

    benchmark_hk_stk_rtn_sum=(out['benchmark_hk_stock_hy_r']*out['benchmark_hk_stock_hy_w'].shift(1)).\
        multiply(out['benchmark_ctr_df'].set_index('enddate')['hk_stk_wght'].shift(1),axis = 0).\
        multiply(out['benchmark_ctr_df'].set_index('enddate')['nav'].shift(1),axis = 0).\
        replace(np.nan,0).sum().T


    industry_rtn_ag = pd.concat([fund_ag_stk_rtn_sum,benchmark_ag_stk_rtn_sum],axis = 1).replace(np.nan,0)
    industry_rtn_ag.columns=['fund_ag_rtn','benchmark_ag_rtn']
    industry_rtn_hk = pd.concat([fund_hk_stk_rtn_sum,benchmark_hk_stk_rtn_sum],axis = 1).replace(np.nan,0)
    industry_rtn_hk.columns=['fund_hk_rtn','benchmark_hk_rtn']

    # 使用外链接合并港股跟A股行业权重跟收益
    industry_cmp1 = pd.merge(industry_wt_ag,industry_wt_hk,left_index = True,right_index = True,how='outer')
    industry_cmp2 = pd.merge(industry_rtn_ag,industry_rtn_hk,left_index = True,right_index = True,how='outer')
    industry_cmp_df = pd.merge(industry_cmp1,industry_cmp2,left_index = True,right_index = True,how='outer').reset_index().replace(np.nan,0)
    industry_cmp_df.columns=['Industry', 'fund_ag_weight', 'benchmark_ag_weight', 'fund_hk_weight',
       'benchmark_hk_weight', 'fund_ag_rtn', 'benchmark_ag_rtn', 'fund_hk_rtn',
       'benchmark_hk_rtn']

    return industry_cmp_df




#################################################################

def cacu_BrisonDetail(fund_stock_w,benchmark_stock_w,fund_hy_w,benchmark_hy_w,fund_hy_r,benchmark_hy_r):
    '''
    计算产品和基准每一期的brison分解结果
    '''
    fund_hy_w.columns.name=None  #add 
    cls = list(set(list(fund_hy_w.columns)+list(benchmark_hy_w.columns)))
    idx = fund_hy_w.index

    temp_wt = pd.DataFrame(np.zeros((len(idx),len(cls))),index = idx,columns = cls)*np.nan

    w_p_df = temp_wt.combine_first(fund_hy_w).replace(np.nan,0)
    w_b_df = temp_wt.combine_first(benchmark_hy_w.replace(np.nan,0)).ffill().loc[idx,:].replace(np.nan,0)

    r_p_df = temp_wt.combine_first(fund_hy_r).replace(np.nan,0)
    r_b_df = temp_wt.combine_first(benchmark_hy_r).ffill().loc[idx,:].replace(np.nan,0)

    brison_detail = brison.multi_brison_detail_w(fund_stock_w,benchmark_stock_w,w_p_df,r_p_df,w_b_df,r_b_df)
    return brison_detail
   
    
if __name__=='__main__':

#    print('project start...')
#    para_dict = dict()
#    para_dict['port_code'] ='001274' # 001806
#    para_dict['benchmarklist_ag'] ='000300.SH'
#    para_dict['benchmarklist_hk'] ='HSML100.HI'
#    para_dict['standard']='WIND'
#    para_dict['startdate'] ='2016-07-01'
#    para_dict['enddate'] ='2018-09-28'
#
#    out = cacu_BaseData(para_dict)

    assetallocation = derivativedata.getassetallocation('001364', '20150331', '20181214','hold_ag_and_hk')