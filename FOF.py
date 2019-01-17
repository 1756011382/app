# encoding: utf-8
"""
Created on Thu May  3 16:45:31 2018
计算FOF产品子产品的相关性和贡献度分解
@author: Administrator
"""

import pandas as pd
import numpy as np
from pymom.finandata import funddata, derivativedata
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import datetime
import time

from pymom.model.pyffn.caculateBrinsonFunction import cacu_BaseData, getrpt_contribution_summary, \
    getrpt_brison_detail, getrpt_brison_detail_industry, getrpt_industry_weight_rtn
from pymom.finandata.derivativedata import getDetailbrison
from pymom.model.pyffn import brison




def saveXlsxData(xlsxfname, dictdf):
    with pd.ExcelWriter(xlsxfname) as writer:
        keylist=dictdf.keys()
        #keylist.sort()
        for key in keylist:
            print (key)
            if type(dictdf[key])==pd.DataFrame:
                dictdf[key].to_excel(writer, sheet_name=key,encoding='utf8')


# FOF子产品的相关性分析
def get_FOF_correlation(para_dict):

    # 得到估值日期的三年前日期
    time3 = parse(para_dict['enddate']) - relativedelta(years=3)
    rtn = pd.DataFrame({'enddate':pd.date_range(start=time3, end=para_dict['enddate'])})

    # 获取母产品的子产品持仓
    data = funddata.get_his_mom_relation([para_dict['port_code']], None, para_dict['enddate'])
    if data.empty:
        result = dict()
        result['ret_code'] = 1
        result['ret_msg'] = "没有数据"
        return result
    sub_port_code = data['sub_port_code']


    clist = []
    nlist = []

    for i in sub_port_code:
        codelist = [i]
        columns = np.array(data.loc[data['sub_port_code']==i,'sub_port_name'])[0]
        # 获取子产品的净值数据
        sub_port_nav = funddata.getFundNAV1(codelist,None,para_dict['enddate'])
        # print(sub_port_nav)

        if not sub_port_nav.empty:
            # 剔除估值日期三年以前的数据
            sub_port_nav = sub_port_nav[sub_port_nav['enddate'] >= time3].reset_index()
            # 填补缺失数据，按前一天数据填补
            sub_port_nav = sub_port_nav.set_index(['enddate']).asfreq('1D').ffill().reset_index()
            code = i

            i = pd.DataFrame()
            i[[columns,'enddate']] = sub_port_nav[['fund_cumulative_nav','enddate']]
            #根据基金每日累计净值计算每日收益率
            i[columns] = (sub_port_nav['fund_cumulative_nav']/sub_port_nav['fund_cumulative_nav'].shift(1) - 1).replace(np.nan, 0)

            # 根据日期整合子产品的每日收益率
            rtn = rtn.merge(i, on='enddate')


            clist.append(code)
            name = np.array(data.loc[data['sub_port_code']==code,'sub_port_name'])[0]
            nlist.append(name)

    rtn = rtn.loc[rtn['enddate']>=para_dict['startdate']]
    rtn = rtn.drop('enddate', axis=1)

    correlation = rtn.corr()

    # 根据前端需要处理数据
    outdata = pd.DataFrame({'sub_port_code':clist, 'sub_port_name':nlist})


    outdata['sub_port_code'] = outdata['sub_port_code'].map(lambda x:'a'+x)

    outdata1 = outdata.set_index('sub_port_name')
    use = outdata1.to_dict()['sub_port_code']
    correlation = correlation.rename(columns=use)
    correlation = correlation.applymap(lambda x: '%.4f' % x)
    correlation = correlation.reset_index()

    result = dict()
    result['ret_code'] = 0
    result['ret_msg'] = "查询成功"

    result['explain'] = outdata[['sub_port_code','sub_port_name']]

    result['corr'] = correlation



    return result










def fof_subportcode_ctr(para_dict):

    result = dict()
    #FOF产品的子基金贡献度分解

    fundnav = funddata.getFundNAV1([para_dict['port_code']], para_dict['startdate'], para_dict['enddate'])
    if fundnav.empty:
        result['ret_code'] = 1
        result['ret_msg'] = "没有净值数据"
        return result
    fundnav = fundnav.set_index('enddate')
        
    fundnav['total_rtn'] = (fundnav['fund_cumulative_nav'] / fundnav['fund_cumulative_nav'].shift(1) - 1).replace(np.nan, 0)
    fundnav['nav'] = (1 + fundnav['total_rtn']).cumprod()
    fundnav['total_rtn_cum'] = fundnav['nav']-1
    fundnav = fundnav[['total_asset','nav','total_rtn_cum']]

    data = funddata.get_his_mom_relationship([para_dict['port_code']], para_dict['startdate'], para_dict['enddate'])
    if data.empty:        
        result['ret_code'] = 1
        result['ret_msg'] = "没有子产品持仓数据"
        return result

    #各子基金的权重占比
    sub_mktvalue = pd.pivot_table(data,index='gz_date',columns='sub_port_code',values='sub_mktvalue').replace(np.nan,0)
    parent_nav=fundnav.loc[sub_mktvalue.index]
    sub_weight=sub_mktvalue.divide(parent_nav['total_asset'],axis=0)
    #子基金本身的收益率
    sub_nav= pd.pivot_table(data,index='gz_date',columns='sub_port_code',values='cum_navps').replace(0,np.nan)
    sub_rtn=sub_nav/sub_nav.shift(1)-1
    sub_rtn=sub_rtn.replace(np.nan,0)
    
    wgt_rtn=sub_weight*sub_rtn
    wgt_rtn=wgt_rtn.dropna(axis=1)
    #计算各子基金的贡献
    sub_ctr=wgt_rtn.multiply(parent_nav['nav'].shift(1),axis=0)
    sub_ctr=sub_ctr.replace(np.nan,0)
    sub_ctr=sub_ctr.cumsum()
    sub_ctr['sub_cum']=sub_ctr.sum(axis=1)
    #合并总贡献
    sub_ctr=pd.merge(sub_ctr,parent_nav[['total_rtn_cum']],left_index=True,right_index=True,how='inner')
    sub_ctr['other']=sub_ctr['total_rtn_cum']-sub_ctr['sub_cum']
    sub_ctr=sub_ctr.drop(['sub_cum'],axis=1)
    #取产品的名称信息
    fundcodelist=sub_ctr.columns
    sub_name=funddata.getFundInfoByPortcode(fundcodelist)
    sub_name_dict=sub_name[['port_code','fund_name']].set_index(['port_code']).to_dict()
    sub_ctr=sub_ctr.rename(columns=sub_name_dict['fund_name'])
    #对贡献正负分解
    for col in sub_ctr.columns:
        if col not in ('total_rtn_cum'):            
            sub_ctr[col+'up'] = sub_ctr[col].apply(lambda x: x if x>=0 else 0)
            sub_ctr[col+'down'] = sub_ctr[col].apply(lambda x: x if x<0 else 0)
    sub_ctr=sub_ctr.reset_index().rename(columns={'gz_date':'enddate'})

    result['ret_code'] = 0
    result['ret_msg'] = "查询成功"
    result['data'] = sub_ctr

    return result



if __name__ == '__main__':

    t = time.time()

    # para_dict = dict()
    # para_dict['port_code'] = '001288'
    # para_dict['startdate'] = '2017-01-01'
    # para_dict['enddate'] = '2018-10-31'
    # a = get_FOF_correlation(para_dict)
    # print(a)


    para_dict = dict()
    para_dict['port_code'] = '001288'
    para_dict['startdate'] = '1990-05-31'
    para_dict['enddate'] = '2005-12-14'
    rpt = fof_subportcode_ctr(para_dict)
    #rpt = ctr(para_dict)
    print(rpt)


    # para_dict = dict()
    # para_dict['port_code'] = '001288'
    # para_dict['benchmarklist_ag'] = '000300.SH'
    # para_dict['benchmarklist_hk'] = 'HSML100.HI'
    # para_dict['standard'] = 'WIND'
    # para_dict['startdate'] = '2018-01-01'
    # para_dict['enddate'] = '2018-11-22'
    # rpt = FOFstatsBrisonRpt(para_dict)
    # print(rpt)


    # fname=para_dict['port_code']+'FOF报告.xlsx'
    # saveXlsxData(fname,rpt)


    print(time.time() - t)
