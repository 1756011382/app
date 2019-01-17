# encoding: utf-8
"""
Created on Thu May  3 16:45:31 2018
计算基金产品上下行捕获率
@author: Administrator
"""
import datetime
import pandas as pd
import numpy as np
import time
import calendar
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from pymom import utils
from pymom import  database_config
from pymom.finandata import funddata, derivativedata


db_tos_res=database_config.db_engine['TOS_RES']

def getbenchmarknav(benchmarkid=None,startdate=None,enddate=None,):

    '''
    提取基准收盘价格
    '''
    if startdate is None:
        startdate=datetime.datetime(1990,1,1)
    if enddate is None:
        enddate=datetime.datetime.now()
    conn=db_tos_res.connect()

    if benchmarkid=='SHE.000300':
        cn1 = " t.innercode='3145'"
    elif benchmarkid=='SHE.000905':
        cn1 = " t.innercode='4978'"
    else:
        cn1 = " t.innercode='3145'"

    if startdate is None:
        cn2=' and 1=1'
    else:
        cn2=" and t.tradingday >=" + utils.to_datestr(startdate,'%Y%m%d')

    if enddate is None:
        cn3=' and 1=1'
    else:
        cn3=" and t.tradingday <=" + utils.to_datestr(enddate,'%Y%m%d')

    sqlstr="select t.tradingday as enddate,t.closeprice from jy_qt_indexquote t where " + cn1 + cn2 + cn3
    benchclose=pd.io.sql.read_sql(sqlstr,conn)
    if len(benchclose)>0:
        benchclose=benchclose.sort_values(by=['enddate'])
    conn.close()
    benchclose['enddate'] = pd.to_datetime(benchclose['enddate'], format='%Y%m%d')

    return benchclose



def updowncapture(para_dict):
    '''
    计算上下行捕获率
    '''
    fundnav = funddata.getFundNAV1([para_dict['port_code']], para_dict['startdate'], para_dict['enddate']).reset_index()
    if fundnav.empty:
        return None
    elif utils.to_datestr(parse(para_dict['startdate'])+relativedelta(years=3),'%Y-%m-%d')>=utils.to_datestr(parse(para_dict['enddate']),'%Y-%m-%d') and utils.to_datestr(parse(para_dict['startdate'])+relativedelta(years=1),'%Y-%m-%d') <= utils.to_datestr(fundnav['enddate'][0],'%Y-%m-%d'):
        return 0,0


    benchmarknav = getbenchmarknav(para_dict['benchmarkid'],para_dict['startdate'],para_dict['enddate'])

    benchmarknav['bmrtn'] = (benchmarknav['closeprice'] / benchmarknav['closeprice'].shift(1) - 1).replace(np.nan, 0)
    rtnup = benchmarknav.loc[benchmarknav['bmrtn']>0][['enddate','bmrtn']]
    rtndown = benchmarknav.loc[benchmarknav['bmrtn'] < 0][['enddate', 'bmrtn']]
    fundnav['rtn'] = (fundnav['fund_cumulative_nav'] / fundnav['fund_cumulative_nav'].shift(1) - 1).replace(np.nan, 0)
    rtn = fundnav[['enddate','rtn']]


    T1 = len(rtnup['bmrtn'])
    T2 = len(rtndown['bmrtn'])
    rtnup = rtnup.merge(rtn,on='enddate',how='left').dropna()
    rtndown = rtndown.merge(rtn,on='enddate',how='left').dropna()

    if not rtnup.empty:
        URC = (np.array(rtnup['rtn']+1).cumprod()[-1])**(1/T1)-1
        URCbm = (np.array(rtnup['bmrtn']+1).cumprod()[-1])**(1/T1)-1
        UC = URC/URCbm
    else:
        UC = 0

    if not rtndown.empty:
        DRC = (np.array(rtndown['rtn']+1).cumprod()[-1])**(1/T2)-1
        DRCbm = (np.array(rtndown['bmrtn']+1).cumprod()[-1])**(1/T2)-1
        DC = DRC/DRCbm
    else:
        DC = 0


    return UC,DC




def rpt(para_dict):
    '''
    输出前端需要的数据
    '''

    para_dict['startdate'] = utils.to_datestr(para_dict['enddate'].split()[0].split("-")[0]+'-01-01','%Y-%m-%d')

    thisyear = updowncapture(para_dict)
    if thisyear==None:
        result = dict()
        result['ret_code'] = 1
        result['ret_msg'] = "没有持仓数据"
        return result

    para_dict['startdate'] = utils.to_datestr(parse(para_dict['enddate']) - relativedelta(years=1),'%Y-%m-%d')
    oyear = updowncapture(para_dict)

    para_dict['startdate'] = utils.to_datestr(parse(para_dict['enddate']) - relativedelta(years=2),'%Y-%m-%d')
    tyear = updowncapture(para_dict)

    para_dict['startdate'] = utils.to_datestr(parse(para_dict['enddate']) - relativedelta(years=3),'%Y-%m-%d')
    syear = updowncapture(para_dict)

    para_dict['startdate'] = utils.to_datestr(datetime.datetime(1990,1,1),'%Y-%m-%d')
    cl = updowncapture(para_dict)


    fundnav = funddata.getFundNAV1([para_dict['port_code']], para_dict['startdate'], para_dict['enddate'])
    benchmarknav = getbenchmarknav(para_dict['benchmarkid'],para_dict['startdate'],para_dict['enddate'])
    benchmarknav['bmrtn'] = (benchmarknav['closeprice'] / benchmarknav['closeprice'].shift(1) - 1).replace(np.nan, 0)
    start = fundnav['enddate'][0]
    end = start + relativedelta(months=1)
    now = fundnav['enddate'][len(fundnav.index)-1]

    b = pd.DataFrame(columns=['enddate','UC','DC'])

    while True:
        if end > now:
            break
        else:
            fundnav0 = fundnav.loc[(fundnav['enddate'] >= start) & (fundnav['enddate'] <= end)]
            benchmarknav0 = benchmarknav.loc[(benchmarknav['enddate'] >= start) & (benchmarknav['enddate'] <= end)]
            rtnup = benchmarknav0.loc[benchmarknav0['bmrtn'] > 0][['enddate', 'bmrtn']]
            rtndown = benchmarknav0.loc[benchmarknav0['bmrtn'] < 0][['enddate', 'bmrtn']]
            fundnav0['rtn'] = (fundnav0['fund_cumulative_nav'] / fundnav0['fund_cumulative_nav'].shift(1) - 1).replace(
                np.nan, 0)
            rtn = fundnav0[['enddate', 'rtn']]
            T1 = len(rtnup['bmrtn'])
            T2 = len(rtndown['bmrtn'])
            rtnup = rtnup.merge(rtn, on='enddate', how='left').dropna()
            rtndown = rtndown.merge(rtn, on='enddate', how='left').dropna()
            URC = (np.array(rtnup['rtn'] + 1).cumprod()[-1]) ** (1 / T1) - 1
            URCbm = (np.array(rtnup['bmrtn'] + 1).cumprod()[-1]) ** (1 / T1) - 1
            UC = URC / URCbm
            DRC = (np.array(rtndown['rtn'] + 1).cumprod()[-1]) ** (1 / T2) - 1
            DRCbm = (np.array(rtndown['bmrtn'] + 1).cumprod()[-1]) ** (1 / T2) - 1
            DC = DRC / DRCbm
            udc = pd.DataFrame({'enddate':[end],
                                'UC':[UC],
                                'DC':[DC]})
            b = b.append(udc)

            end = end + relativedelta(months=1)
    b = b.reset_index()
    b['z'] = range(1,len(b['UC'])+1)
    b['z'] = b['z'].map(lambda x: (x - 1) / (b['z'][len(b.index)-1] - 1))


    result = dict()
    result['ret_code'] = 0
    result['ret_msg'] = "查询成功"
    result['b'] = b
    result['a'] = pd.DataFrame([thisyear, oyear, tyear, syear, cl],columns=['UC','DC'])
    result['a']['y'] = ['今年以来','近一年','近两年','近三年','成立以来']


    return result










if __name__=='__main__':
    t = time.time()


    para_dict = dict()
    para_dict['port_code'] ='008390'
    para_dict['enddate'] = '2019-01-03'
    para_dict['benchmarkid'] = 'SHE.000300'  #SHE.000905 SHE.000300

    # rpt = updowncapture(para_dict)


    rpt = rpt(para_dict)


    print(rpt)


    print('t =',time.time()-t)
