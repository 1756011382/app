# -*- coding: utf-8 -*-
"""
Created on Thu May  3 16:45:31 2018
1 支持对组合进行单期和多期brison分解
@author: Administrator
"""
import numpy as np

import pandas as pd
from pymom.model.pyffn import brison

from pymom.finandata import funddata,derivativedata
import datetime

def saveXlsxData(xlsxfname, dictdf):
    with pd.ExcelWriter(xlsxfname) as writer:
        keylist=dictdf.keys()
        #keylist.sort()
        for key in keylist:
            print (key)
            if type(dictdf[key])==pd.DataFrame:
                dictdf[key].to_excel(writer, sheet_name=key,encoding='utf8')



def cacu_BaseData(para_dict):


    out = dict()
# =============================================================================
# #计算产品数据
# =============================================================================
    st = datetime.datetime.strptime( para_dict['startdate'],'%Y-%m-%d')
    et = datetime.datetime.strptime(para_dict['enddate'],'%Y-%m-%d')


    #提取产品净值 根据产品代码，开始结束时间，查出产品的单位净值
    fundnav = funddata.getFundNAV([para_dict['port_code']],para_dict['startdate'],para_dict['enddate'])

    #提取持仓 根据产品代码，开始结束时间，查出产品的持仓
    fund_stk_hlds = funddata.getFundStockHoldings([para_dict['port_code']],para_dict['startdate'],para_dict['enddate'])

    #分解产品的大类资产配置 ： A股，港股，其他
    fund_assetallocation,fund_ag_stk_holdings,fund_hk_stk_holdings = funddata.cacu_FundAssetsAllocation(fundnav[['port_code','enddate','fund_cumulative_nav','total_asset']] ,fund_stk_hlds)

    dateindex = pd.DatetimeIndex(fund_assetallocation.enddate)

    #分解产品的行业配置及收益率
    fund_ag_stock_hy_df = derivativedata.getFundClassWeight(para_dict['port_code'],st,et,para_dict['standard'],'AG')
    if not fund_ag_stock_hy_df.empty:

        fund_ag_stock_hy_r = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        fund_ag_stock_hy_w = pd.pivot_table(fund_ag_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].ffill()
    else:
        fund_ag_stock_hy_r = pd.DataFrame()
        fund_ag_stock_hy_w = pd.DataFrame()


    fund_hk_stock_hy_df = derivativedata.getFundClassWeight(para_dict['port_code'],st,et,para_dict['standard'],'HK')
    if not fund_hk_stock_hy_df.empty:

        fund_hk_stock_hy_r = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        fund_hk_stock_hy_w = pd.pivot_table(fund_hk_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].ffill()

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

    ag_benchmarkid = para_dict['ag_benchmarkid']
    hk_benchmarkid = para_dict['hk_benchmarkid']

    #计算指数的的行业配置及收益率

    benchmark_ag_stock_hy_df = derivativedata.getIndexClassWeight(ag_benchmarkid,dateindex[0],dateindex[-1],para_dict['standard'])
    if not benchmark_ag_stock_hy_df.empty:

        benchmark_ag_stock_hy_r = pd.pivot_table(benchmark_ag_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        benchmark_ag_stock_hy_w = pd.pivot_table(benchmark_ag_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].ffill()

    else:
        benchmark_ag_stock_hy_r = pd.DataFrame()
        benchmark_ag_stock_hy_w = pd.DataFrame()



    benchmark_hk_stock_hy_df = derivativedata.getIndexClassWeight(hk_benchmarkid,dateindex[0],dateindex[-1],para_dict['standard'])
    if not benchmark_hk_stock_hy_df.empty:

        benchmark_hk_stock_hy_r = pd.pivot_table(benchmark_hk_stock_hy_df,index='enddate',columns='classname',values='rtn').loc[dateindex,:].replace(np.nan,0)
        benchmark_hk_stock_hy_w = pd.pivot_table(benchmark_hk_stock_hy_df,index='enddate',columns='classname',values='weight').loc[dateindex,:].ffill()
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
    benchmark_nav['net_asset']=benchmark_nav['fund_cumulative_nav']
    benchmark_nav['port_code']=ag_benchmarkid+'-'+hk_benchmarkid



    benchmark_assetallocation = benchmark_nav[['port_code', 'enddate', 'fund_cumulative_nav', 'net_asset',
        'ag_stk_wght', 'hk_stk_wght','other_wght', 'total_rtn']]

    benchmark_assetallocation.loc[:,'ag_stk_mkv']=benchmark_assetallocation['net_asset']*benchmark_assetallocation['ag_stk_wght']
    benchmark_assetallocation.loc[:,'hk_stk_mkv']=benchmark_assetallocation['net_asset']*benchmark_assetallocation['hk_stk_wght']
    benchmark_assetallocation.loc[:,'other_mkv']=benchmark_assetallocation['net_asset']*benchmark_assetallocation['other_wght']


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



def cacu_BrisonDetail(fund_stock_w,benchmark_stock_w,fund_hy_w,benchmark_hy_w,fund_hy_r,benchmark_hy_r):
    '''
    计算产品和基准每一期的brison分解结果
    '''

    cls = list(set(list(fund_hy_w.columns)+list(benchmark_hy_w.columns)))
    idx = fund_hy_w.index

    temp_wt = pd.DataFrame(np.zeros((len(idx),len(cls))),index = idx,columns = cls)*np.nan

    w_p_df = temp_wt.combine_first(fund_hy_w).replace(np.nan,0)
    w_b_df = temp_wt.combine_first(benchmark_hy_w.replace(np.nan,0)).ffill().loc[idx,:].replace(np.nan,0)

    r_p_df = temp_wt.combine_first(fund_hy_r).replace(np.nan,0)
    r_b_df = temp_wt.combine_first(benchmark_hy_r).ffill().loc[idx,:].replace(np.nan,0)

    brison_detail = brison.multi_brison_detail_w(fund_stock_w,benchmark_stock_w,w_p_df,r_p_df,w_b_df,r_b_df)
    return brison_detail

def getrpt_contribution_summary(out):
    cls1=['port_code','total_rtn_ctr_cum','ag_stock_rtn_ctr_cum','hk_stock_rtn_ctr_cum','other_rtn_ctr_cum']
    cls2=['ag_stk_wght','hk_stk_wght','other_wght']


    fund_ctr1 = pd.concat([out['fund_ctr_df'][cls1].iloc[-1,:],out['fund_ctr_df'][cls2].mean()])
    benchmark_ctr1 = pd.concat([out['benchmark_ctr_df'][cls1].iloc[-1,:],out['benchmark_ctr_df'][cls2].mean()])

    cmp_ctr_df = pd.concat([fund_ctr1,benchmark_ctr1],axis = 1).T
    return cmp_ctr_df


def getrpt_brison_detail(ag_brison_detail,hk_brison_detail):
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

    total_brison_ctr_df = pd.merge(ag_brison_ctr_df,hk_brison_ctr_df,left_index = True,right_index = True,suffixes=('_ag','_hk')).replace(np.nan,0)

    return total_brison_ctr_df

def getrpt_brison_detail_industry(brison_detail ):
    if not brison_detail.empty:
        gp_hy = brison_detail.groupby('Industry')
        brison_ctr_hy_df = gp_hy[[  'RP_s_t', 'RB_s_t', 'TR_t','PR_t', 'AR_t','SR_t', 'IR_t']].sum().replace(np.nan,0)
        brison_ctr_hy_df['ARSRIR_sum']=brison_ctr_hy_df[['AR_t','SR_t', 'IR_t']].sum(axis=1) #AR，SR，IR 求和
        brison_ctr_hy_df.loc['合计',['AR_t','SR_t', 'IR_t','ARSRIR_sum']]=brison_ctr_hy_df.loc[:,['AR_t','SR_t', 'IR_t','ARSRIR_sum']].sum(axis=0)
        brison_ctr_hy_df.loc['合计',['RP_s_t', 'RB_s_t', 'TR_t','PR_t']]=brison_ctr_hy_df.iloc[0,:4]

        brison_ctr_hy_df=brison_ctr_hy_df.reset_index()
    else:
        brison_ctr_hy_df = pd.DataFrame()

    return  brison_ctr_hy_df


def getrpt_industry_weight_rtn(out ):
    #计算每类资产中行业的平均权重
    fund_ag_stk_wght_mean = out['fund_ag_stock_hy_w'].multiply(out['fund_ctr_df'].set_index('enddate')['ag_stk_wght'],axis = 0).replace(np.nan,0).mean().T
    fund_hk_stk_wght_mean = out['fund_hk_stock_hy_w'].multiply(out['fund_ctr_df'].set_index('enddate')['hk_stk_wght'],axis = 0).replace(np.nan,0).mean().T

    benchmark_ag_stk_wght_mean = out['benchmark_ag_stock_hy_w'].multiply(out['benchmark_ctr_df'].set_index('enddate')['ag_stk_wght'],axis = 0).replace(np.nan,0).mean().T
    benchmark_hk_stk_wght_mean = out['benchmark_hk_stock_hy_w'].multiply(out['benchmark_ctr_df'].set_index('enddate')['hk_stk_wght'],axis = 0).replace(np.nan,0).mean().T

    industry_wt_ag = pd.concat([fund_ag_stk_wght_mean,benchmark_ag_stk_wght_mean],axis = 1).replace(np.nan,0)
    industry_wt_ag.columns=['fund_ag_weight','benchmark_ag_weight']
    industry_wt_hk = pd.concat([fund_hk_stk_wght_mean,benchmark_hk_stk_wght_mean],axis = 1).replace(np.nan,0)
    industry_wt_hk.columns=['fund_hk_weight','benchmark_hk_weight']



    #计算每类资产对产品净值的累计贡献
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


    industry_cmp1 = pd.merge(industry_wt_ag,industry_wt_hk,how='outer',left_index = True,right_index = True)
    industry_cmp2 = pd.merge(industry_rtn_ag,industry_rtn_hk,how='outer',left_index = True,right_index = True)
    industry_cmp_df = pd.merge(industry_cmp1,industry_cmp2,how='outer',left_index = True,right_index = True)
    industry_cmp_df.loc['合计',:]=industry_cmp_df.sum(axis=0)
    industry_cmp_df=industry_cmp_df.replace(np.nan,0).reset_index()
    industry_cmp_df.columns=['Industry', 'fund_ag_weight', 'benchmark_ag_weight', 'fund_hk_weight',
       'benchmark_hk_weight', 'fund_ag_rtn', 'benchmark_ag_rtn', 'fund_hk_rtn',
       'benchmark_hk_rtn']

    return industry_cmp_df

def statsBrisonRpt(para_dict):

    out =cacu_BaseData(para_dict   )
    ##1 获取产品净值及 持仓的权重及收益率
# =============================================================================
#  2  brison分解
# =============================================================================
    
#----------------------------------------------------------------------------------------
    fund_ag_stock_w = out['fund_ctr_df'][['enddate','ag_stk_wght']].set_index('enddate')
    benchmark_ag_stock_w = out['benchmark_ctr_df'][['enddate','ag_stk_wght']].set_index('enddate')
    ag_brison_detail = cacu_BrisonDetail(fund_ag_stock_w.shift(1),
                                       benchmark_ag_stock_w.shift(1),
                                       out['fund_ag_stock_hy_w'].shift(1),
                                       out['benchmark_ag_stock_hy_w'].shift(1),
                                       out['fund_ag_stock_hy_r'],
                                       out['benchmark_ag_stock_hy_r'])


    fund_hk_stock_w = out['fund_ctr_df'][['enddate','hk_stk_wght']].set_index('enddate')
    benchmark_hk_stock_w = out['benchmark_ctr_df'][['enddate','hk_stk_wght']].set_index('enddate')
    hk_brison_detail = cacu_BrisonDetail(fund_hk_stock_w.shift(1),
                                       benchmark_hk_stock_w.shift(1),
                                       out['fund_hk_stock_hy_w'].shift(1),
                                       out['benchmark_hk_stock_hy_w'].shift(1),
                                       out['fund_hk_stock_hy_r'],
                                       out['benchmark_hk_stock_hy_r'])

#-------------------------------------------------------------------------------------------
    ag_brison_detail_sm = brison.smooth_multi_birson_detail_w(ag_brison_detail,out['kt_df'])
    hk_brison_detail_sm = brison.smooth_multi_birson_detail_w(hk_brison_detail,out['kt_df'])


    out['ag_brison_detail']=ag_brison_detail
    out['hk_brison_detail']=hk_brison_detail
    out['ag_brison_detail_sm']=ag_brison_detail_sm
    out['hk_brison_detail_sm']=hk_brison_detail_sm


# =============================================================================
#  4  汇总结果展示
# =============================================================================
    #第一层分解效应(组合组合累计超额收益的分解)
    rpt = dict()

    cmp_ctr_df = getrpt_contribution_summary(out)

    rpt['cmp_ctr_df']=cmp_ctr_df # 各个市场的收益率、总收益率，跟权重


    #第二层主动收益时序分解

    #total_brison_ctr_df = getrpt_brison_detail(ag_brison_detail,hk_brison_detail)
    #调整后数值
    total_brison_ctr_df_sm = getrpt_brison_detail(ag_brison_detail_sm,hk_brison_detail_sm)


    total_brison_ctr_df_sm_cumsum = total_brison_ctr_df_sm.cumsum()

    #rpt['total_brison_ctr_df']=total_brison_ctr_df.reset_index()
    #rpt['total_brison_ctr_df_sm']=total_brison_ctr_df_sm.reset_index()

    rpt['total_brison_ctr_df_sm_cumsum']=total_brison_ctr_df_sm_cumsum.reset_index()



    ##主动收益含行业分解

    ag_brison_ctr_hy_df = getrpt_brison_detail_industry(ag_brison_detail_sm )
    hk_brison_ctr_hy_df = getrpt_brison_detail_industry(hk_brison_detail_sm )

    rpt['ag_brison_ctr_hy_df']=ag_brison_ctr_hy_df
    rpt['hk_brison_ctr_hy_df']=hk_brison_ctr_hy_df


    ##行情平均权重（占产品的权重）

    industry_cmp_df = getrpt_industry_weight_rtn(out )


    rpt['industry_cmp_df']=industry_cmp_df

    return  rpt,out

if __name__=='__main__':


    para_dict = dict()
    para_dict['port_code'] ='010678'
    para_dict['ag_benchmarkid'] ='000300.SH'
    para_dict['hk_benchmarkid'] ='HSML100.HI'
    para_dict['standard']='WIND'
    para_dict['startdate'] ='2017-11-14'
    para_dict['enddate'] ='2018-09-13'


    rpt  ,out = statsBrisonRpt(para_dict)


    fname=para_dict['port_code']+'_brion报告2.xlsx'
    saveXlsxData(fname,rpt)


    fname1=para_dict['port_code']+'_brion报告2_out.xlsx'
    saveXlsxData(fname1,out)
