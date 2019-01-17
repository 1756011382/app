# -*- coding: utf-8 -*-
"""
Created on Thu May  3 16:45:31 2018
1 支持对组合进行单期和多期brison分解
@author: Administrator
"""
from pymom.model.pyffn.caculateBrinsonFunction import cacu_BaseData, getrpt_contribution_summary, \
    getrpt_brison_detail, getrpt_brison_detail_industry, getrpt_industry_weight_rtn,\
    getrpt_contribution_summary_ts
from pymom.finandata.derivativedata import getDetailbrison
from pymom.model.pyffn import brison
import pandas as pd
from matplotlib import pyplot
from pylab import *
import datetime
import numpy as np



def statsBrisonRpt(para_dict):
    '''
    此函数是用来给前段调用的，
    返回产品的Brinson多期归因、汇总以及多个结果集
    '''
    
    # 时间的处理，是为了判断前段传过来的时间是否合法
    # 例如：前段传过来的是一个'-'字符串或者其他字符串
    try:
        st = datetime.datetime.strptime(para_dict['startdate'],'%Y-%m-%d')
    except ValueError as e:
        para_dict['startdate']='2000-01-01'
    try:
        et = datetime.datetime.strptime(para_dict['enddate'],'%Y-%m-%d')
    except ValueError as e:
        para_dict['enddate']=datetime.datetime.now().strftime('%Y-%m-%d')

    #empty_df = pd.DataFrame([0])
    out = cacu_BaseData(para_dict)
#    try:
#        out = cacu_BaseData(para_dict)
#    except:
#        return {'cmp_ctr_df':empty_df,'total_brison_ctr_df_sm_cumsum':empty_df,'ag_brison_ctr_hy_df':empty_df,
#                'hk_brison_ctr_hy_df':empty_df,'industry_cmp_df':empty_df}        
    # 没有持仓数据
    if out==dict():
        rpt = dict()
        rpt['ret_code'] = 1
        rpt['ret_msg'] = "没有持仓数据"
        return rpt
#        cmp_ctr_df = pd.DataFrame([[0 for i in range(8)]],
#                                  columns=['port_code', 'total_rtn_ctr_cum', 'ag_stock_rtn_ctr_cum',
#                                           'hk_stock_rtn_ctr_cum', 'other_rtn_ctr_cum', 'ag_stk_wght',
#                                           'hk_stk_wght', 'other_wght'])
#        total_brison_ctr_df_sm_cumsum = pd.DataFrame([[0 for i in range(15)]],
#                                                     columns=['enddate', 'RP_s_t_ag', 'RB_s_t_ag', 'TR_t_ag', 'PR_t_ag',
#                                                              'AR_t_ag',
#                                                              'SR_t_ag', 'IR_t_ag', 'RP_s_t_hk', 'RB_s_t_hk', 'TR_t_hk',
#                                                              'PR_t_hk',
#                                                              'AR_t_hk', 'SR_t_hk', 'IR_t_hk'])
#        ag_brison_ctr_hy_df = pd.DataFrame([[0 for i in range(9)]],
#                                           columns=['Industry_ag', 'RP_s_t_ag', 'RB_s_t_ag', 'TR_t_ag', 'PR_t_ag',
#                                                    'AR_t_ag', 'SR_t_ag', 'IR_t_ag', 'ARSRIR_sum_ag'])
#        hk_brison_ctr_hy_df = pd.DataFrame([[0 for i in range(9)]],
#                                           columns=['Industry_hk', 'RP_s_t_hk', 'RB_s_t_hk', 'TR_t_hk', 'PR_t_hk',
#                                                    'AR_t_hk', 'SR_t_hk', 'IR_t_hk', 'ARSRIR_sum_hk'])
#        industry_cmp_df = pd.DataFrame([[0 for i in range(9)]],
#                                       columns=['Industry', 'fund_ag_weight', 'benchmark_ag_weight', 'fund_hk_weight',
#                                                'benchmark_hk_weight', 'fund_ag_rtn', 'benchmark_ag_rtn', 'fund_hk_rtn',
#                                                'benchmark_hk_rtn'])
#        return {'cmp_ctr_df':cmp_ctr_df,'total_brison_ctr_df_sm_cumsum':total_brison_ctr_df_sm_cumsum,'ag_brison_ctr_hy_df':ag_brison_ctr_hy_df,
#                'hk_brison_ctr_hy_df':hk_brison_ctr_hy_df,'industry_cmp_df':industry_cmp_df}
    
    ##1 获取产品净值及 持仓的权重及收益率
    # =============================================================================
    #  2  brison分解 ASSETSTYPE
    # =============================================================================
    
    brison_detail = getDetailbrison(para_dict['port_code'], startdate=para_dict['startdate'], enddate=para_dict['enddate'], classstandard=para_dict['standard'])

    # 没有初始化产品数据
    if brison_detail.empty:
        rpt = dict()
        rpt['ret_code'] = 2
        rpt['ret_msg'] = "没有初始化产品数据"
        return rpt
#        cmp_ctr_df = pd.DataFrame([[0 for i in range(8)]],
#                                  columns=['port_code', 'total_rtn_ctr_cum', 'ag_stock_rtn_ctr_cum',
#                                           'hk_stock_rtn_ctr_cum', 'other_rtn_ctr_cum', 'ag_stk_wght',
#                                           'hk_stk_wght', 'other_wght'])
#        total_brison_ctr_df_sm_cumsum = pd.DataFrame([[0 for i in range(15)]],
#                                                     columns=['enddate', 'RP_s_t_ag', 'RB_s_t_ag', 'TR_t_ag', 'PR_t_ag',
#                                                              'AR_t_ag',
#                                                              'SR_t_ag', 'IR_t_ag', 'RP_s_t_hk', 'RB_s_t_hk', 'TR_t_hk',
#                                                              'PR_t_hk',
#                                                              'AR_t_hk', 'SR_t_hk', 'IR_t_hk'])
#        ag_brison_ctr_hy_df = pd.DataFrame([[0 for i in range(9)]],
#                                           columns=['Industry_ag', 'RP_s_t_ag', 'RB_s_t_ag', 'TR_t_ag', 'PR_t_ag',
#                                                    'AR_t_ag', 'SR_t_ag', 'IR_t_ag', 'ARSRIR_sum_ag'])
#        hk_brison_ctr_hy_df = pd.DataFrame([[0 for i in range(9)]],
#                                           columns=['Industry_hk', 'RP_s_t_hk', 'RB_s_t_hk', 'TR_t_hk', 'PR_t_hk',
#                                                    'AR_t_hk', 'SR_t_hk', 'IR_t_hk', 'ARSRIR_sum_hk'])
#        industry_cmp_df = pd.DataFrame([[0 for i in range(9)]],
#                                       columns=['Industry', 'fund_ag_weight', 'benchmark_ag_weight', 'fund_hk_weight',
#                                                'benchmark_hk_weight', 'fund_ag_rtn', 'benchmark_ag_rtn', 'fund_hk_rtn',
#                                                'benchmark_hk_rtn'])
#        return {'cmp_ctr_df':cmp_ctr_df,'total_brison_ctr_df_sm_cumsum':total_brison_ctr_df_sm_cumsum,'ag_brison_ctr_hy_df':ag_brison_ctr_hy_df,
#            'hk_brison_ctr_hy_df':hk_brison_ctr_hy_df,'industry_cmp_df':industry_cmp_df}
    
    
    # ----------------------------------------------------------------------------------------
    # fund_ag_stock_w = out['fund_ctr_df'][['enddate', 'ag_stk_wght']].set_index('enddate')
    # benchmark_ag_stock_w = out['benchmark_ctr_df'][['enddate', 'ag_stk_wght']].set_index('enddate')
    ag_brison_detail = brison_detail[brison_detail['assetstype']=='AG']
    ag_brison_detail.columns = ['portcode', 'enddate', 'assetstype', 'classstandard', 'benchmarkid',
       'Industry', 'RP_s_t', 'RB_s_t', 'TR_t', 'PR_t', 'AR_t', 'SR_t','IR_t']
    # fund_hk_stock_w = out['fund_ctr_df'][['enddate', 'hk_stk_wght']].set_index('enddate')
    # benchmark_hk_stock_w = out['benchmark_ctr_df'][['enddate', 'hk_stk_wght']].set_index('enddate')
    hk_brison_detail = brison_detail[brison_detail['assetstype']=='HK']
    hk_brison_detail.columns = ['portcode', 'enddate', 'assetstype', 'classstandard', 'benchmarkid',
       'Industry', 'RP_s_t', 'RB_s_t', 'TR_t', 'PR_t', 'AR_t', 'SR_t','IR_t']
    # -------------------------------------------------------------------------------------------
    ag_brison_detail_sm = brison.smooth_multi_birson_detail_w(ag_brison_detail, out['kt_df'])
    hk_brison_detail_sm = brison.smooth_multi_birson_detail_w(hk_brison_detail, out['kt_df'])

    out['ag_brison_detail'] = ag_brison_detail
    out['hk_brison_detail'] = hk_brison_detail
    out['ag_brison_detail_sm'] = ag_brison_detail_sm
    out['hk_brison_detail_sm'] = hk_brison_detail_sm

    # =============================================================================
    #  4  汇总结果展示
    # =============================================================================
    # 第一层分解效应(组合组合累计超额收益的分解)
    rpt = dict()
    rpt['ret_code'] = 0
    rpt['ret_msg'] = "查询成功"

    cmp_ctr_df = getrpt_contribution_summary(out)

    rpt['cmp_ctr_df'] = cmp_ctr_df  # 各个市场的收益率、总收益率，跟权重

    # 第二层主动收益时序分解

    # total_brison_ctr_df = getrpt_brison_detail(ag_brison_detail,hk_brison_detail)
    # 调整后数值
    total_brison_ctr_df_sm = getrpt_brison_detail(ag_brison_detail_sm, hk_brison_detail_sm)

    total_brison_ctr_df_sm_cumsum = total_brison_ctr_df_sm.cumsum()

    # rpt['total_brison_ctr_df']=total_brison_ctr_df.reset_index()
    # rpt['total_brison_ctr_df_sm']=total_brison_ctr_df_sm.reset_index()
    rpt['total_brison_ctr_df_sm_cumsum'] = total_brison_ctr_df_sm_cumsum.reset_index()
    # 修改时间格式返回给前台
    rpt['total_brison_ctr_df_sm_cumsum']['enddate'] = rpt['total_brison_ctr_df_sm_cumsum']['enddate'].apply(lambda x: x.strftime('%Y/%m/%d'))
    rpt['total_brison_ctr_df_sm_cumsum']['SRIR_ag'] = rpt['total_brison_ctr_df_sm_cumsum']['SR_t_ag'] + \
                                                      rpt['total_brison_ctr_df_sm_cumsum']['IR_t_ag']
    rpt['total_brison_ctr_df_sm_cumsum']['SRIR_hk'] = rpt['total_brison_ctr_df_sm_cumsum']['SR_t_hk'] + \
                                                      rpt['total_brison_ctr_df_sm_cumsum']['IR_t_hk']

    ##主动收益含行业分解

    ag_brison_ctr_hy_df = getrpt_brison_detail_industry(ag_brison_detail_sm)
    ag_brison_ctr_hy_df.columns=[x+'_ag' for x in ag_brison_ctr_hy_df.columns]


    hk_brison_ctr_hy_df = getrpt_brison_detail_industry(hk_brison_detail_sm)
    hk_brison_ctr_hy_df.columns=[x+'_hk' for x in hk_brison_ctr_hy_df.columns]



    rpt['ag_brison_ctr_hy_df'] = ag_brison_ctr_hy_df

    if ag_brison_ctr_hy_df.empty:
        rpt['ag_brison_ctr_hy_df']=pd.DataFrame(data=[['-','-','-','-','-','-','-','-','-','-']],columns=['Industry_ag', 'RP_s_t_ag', 'RB_s_t_ag', 'TR_t_ag', 'PR_t_ag',
       'AR_t_ag', 'SR_t_ag', 'IR_t_ag', 'ARSRIR_sum_ag','SRIR_ag'])
    else:
        add = pd.DataFrame(rpt['ag_brison_ctr_hy_df'].apply(sum)).T
        rpt['ag_brison_ctr_hy_df']= rpt['ag_brison_ctr_hy_df'].append(add).reset_index().drop(['index'], axis=1)
        rpt['ag_brison_ctr_hy_df'].iloc[-1, 0] = '合计'
        rpt['ag_brison_ctr_hy_df']['SRIR_ag'] = rpt['ag_brison_ctr_hy_df']['SR_t_ag'] + rpt['ag_brison_ctr_hy_df']['IR_t_ag']


    rpt['hk_brison_ctr_hy_df'] = hk_brison_ctr_hy_df

    if hk_brison_ctr_hy_df.empty:
        rpt['hk_brison_ctr_hy_df']=pd.DataFrame(data=[['-','-','-','-','-','-','-','-','-','-']],columns=['Industry_hk', 'RP_s_t_hk', 'RB_s_t_hk', 'TR_t_hk', 'PR_t_hk',
       'AR_t_hk', 'SR_t_hk', 'IR_t_hk', 'ARSRIR_sum_hk','SRIR_hk'])
    else:
        add = pd.DataFrame(rpt['hk_brison_ctr_hy_df'].apply(sum)).T
        rpt['hk_brison_ctr_hy_df'] = rpt['hk_brison_ctr_hy_df'].append(add).reset_index().drop(['index'], axis=1)
        rpt['hk_brison_ctr_hy_df'].iloc[-1, 0] = '合计'
        rpt['hk_brison_ctr_hy_df']['SRIR_hk'] = rpt['hk_brison_ctr_hy_df']['SR_t_hk'] + rpt['hk_brison_ctr_hy_df']['IR_t_hk']

    ##行情平均权重（占产品的权重）

    industry_cmp_df = getrpt_industry_weight_rtn(out)

    rpt['industry_cmp_df'] = industry_cmp_df

    #累计贡献分解序列
    cmp_ctr_ts = getrpt_contribution_summary_ts(out)
    cmp_ctr_ts['enddate'] = cmp_ctr_ts['enddate'].apply(lambda x: x.strftime('%Y/%m/%d'))
    rpt['cmp_ctr_ts'] = cmp_ctr_ts
    
    #产品和基准的累计收益对比序列
    fund_nav_adj=out['fund_ctr_df'][['enddate','nav']].set_index('enddate')
    benchmark_nav_adj=out['benchmark_ctr_df'][['enddate','nav']].set_index('enddate')
    fund_rtn_cum=fund_nav_adj-1
    fund_rtn_cum=fund_rtn_cum.rename(columns={'nav':para_dict['port_code']})
    benchmark_rtn_cum=benchmark_nav_adj-1
    benchmark_rtn_cum=benchmark_rtn_cum.rename(columns={'nav':para_dict['benchmarklist_ag']+'+'+para_dict['benchmarklist_hk']})
    rtn_cum_cmpr=pd.merge(fund_rtn_cum,benchmark_rtn_cum,left_index=True,right_index=True,how='outer')
    rtn_cum_cmpr=rtn_cum_cmpr.replace(np.nan,0)
    rtn_cum_cmpr.columns = ['fund_rtn_cum','benchmark_rtn_cum']
    rtn_cum_cmpr.reset_index(inplace=True)
    rpt['rtn_cum_cmpr']=rtn_cum_cmpr
    
    return rpt




if __name__ == '__main__':
    import time
    t = time.time()
    para_dict = dict()
    para_dict['port_code'] = '001290'
    para_dict['benchmarklist_ag'] = '000300.SH'
    para_dict['benchmarklist_hk'] = 'HSML100.HI'
    para_dict['standard'] = 'WIND'
    para_dict['startdate'] = '2016-01-01'
    para_dict['enddate'] = '2018-11-30'

    rpt = statsBrisonRpt(para_dict)



    print(rpt['rtn_cum_cmpr'])
    print(time.time() - t)
