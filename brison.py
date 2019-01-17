# -*- coding: utf-8 -*-
"""
Created on Fri May 11 10:10:19 2018

@author: Administrator
本文件主要目标： 实现对产品进行单期、多期的brison分解。
"""

import pandas as pd
import numpy as np
import copy



def single_brison_w(Wp, Wb, wp, rp1, wb, rb1):

    '''
    单期带权重的brison模型
    输入：
    Wp 组合中股票的权重，scalar
    Wb 基准中股票的权重，scalar
    wp 各行业占组合股票部分的权重（而不是占组合）,Series
    rp 组合股票部分在各行业上的收益率,Series
    wb 各行业占基准股票部分的权重（而不是占基准）,Series
    rb 基准股票部分在各行业上的收益率,Series

    输出:
    RP_S 组合由股票带来的收益率
    RB_S 基准由股票带来的收益率
    TR, 主动收益率
    PR, 仓位管理效应
    AR, 行业选择效应
    SR, 选股效应
    IR, 其它效应
    --k  调整系数

    中间变量：
    Rp 组合中股票的收益率,scalar
    Rb 基准中股票的收益率,scalar
    '''
    rp, rb = copy.deepcopy(rp1), copy.deepcopy(rb1)
    #rp, rb = copy.deepcopy(rp1), rb1
    #基准有持仓，组合没有持仓（或持仓权重小于0.01），则组合的收益率调整和基准一致
    #cn1 = wp.map(lambda x:True if x==0 else False) & wb.map(lambda x:True if x!=0 else False)
    cn1 = wp.map(lambda x:True if x<0.01 else False) & wb.map(lambda x:True if x!=0 else False)
    rp[cn1]=rb[cn1]
    #基准没有持仓，组合有持仓，则基准收益率调整和组合一致
    #cn2 = wp.map(lambda x:True if x!=0 else False) & wb.map(lambda x:True if x==0 else False)
    cn2 = wp.map(lambda x:True if x!=0 else False) & wb.map(lambda x:True if x<0.01 else False)
    rb[cn2]=rp[cn2]

    #调整行业收益率前股票的收益
    Rp1 = (wp*rp1).sum()
    Rb1 = (wb*rb1).sum()
    #调整后的股票的收益
    #Rp = (wp*rp).sum()

    #基准股票的收益

    Rb = (wb*rb).sum()

    RP_S1 = Wp*Rp1
    RB_S1 = Wb*Rb1

    TR1=RP_S1-RB_S1                        #调整前超额收益

    PR = (Wp-Wb)*Rb                         #调整前仓位管理效应

    AR1 = Wp*(wp-wb)*rb1                      #调整前配置效应

    SR1 = Wp*wb*(rp1-rb1)                      #调整前的选择效应

    IR1 = Wp*(wp-wb)*(rp1-rb1)              #调整前的其它效应

    temp_ASI=AR1+SR1+IR1                          #调整前AR1+SR1+IR1



    AR = Wp*(wp-wb)*rb                      #调整后配置效应

    SR = Wp*wb*(rp-rb)                      #调整后的选择效应

    IR=temp_ASI-AR-SR                    #调整后的其它效应


    return RP_S1, RB_S1 ,PR , AR , SR , IR , TR1

def _cacu_k(R_p , R_b):

    '''
    R_p 组合累计收益率
    R_b 基准累计收益率
    '''
    if R_p==R_b: #除数为0时的情形
        k=np.nan
    else:
        k=(np.log(1+R_p)-np.log(1+R_b))/(R_p-R_b)
    return k


def multi_brison_detail_w(Wp_df,Wb_df,wp_df,rp_df,wb_df,rb_df):

    '''
    多期带权重的brison模型
    输入：
    Wp_df 组合中股票的权重,DataFrame,每一行代表一期,只有一列
    Wb_df 基准中股票的权重,DataFrame,每一行代表一期,只有一列
    wp_df 第s个行业占组合股票部分（非组合）的权重, DataFrame,每一行代表一期,列代表各个行业类别
    rp_df 组合股票部分在第s个行业的收益率, DataFrame,每一行代表一期,列代表各个行业的收益率
    wb_df 第s个行业占基准股票部分（非组合）的权重, DataFrame,每一行代表一期,列代表各个行业类别
    rb_df 基准股票部分在第s个行业的收益率, DataFrame,每一行代表一期,列代表各个行业的收益率

    wp_df , rp_df , wb_df , rb_df 要求结构一致
    Wp_df , Wb_df 的行数与上述各变量一致

    输出:
    RP_St, 每一期组合由股票带来的收益率
    RB_St, 每一期基准由股票带来的收益率
    TR_t, 每一期主动收益率
    PR_t, 每一期仓位管理效应
    AR_t, 每一期行业选择效应
    SR_t, 每一期选股效应
    IR_t, 每一期其它效应
    --k_t,  每一期的kt

    '''

    dt = wp_df.index
    brison_detail = pd.DataFrame()
    brison_t1=pd.DataFrame()
    brison_t2=pd.DataFrame()

    for t in dt :
        Wp,Wb,wp,rp,wb,rb = Wp_df.loc[t][0],Wb_df.loc[t][0],wp_df.loc[t],rp_df.loc[t],wb_df.loc[t],rb_df.loc[t]
        RP_St,RB_St,PR_t,AR_t,SR_t,IR_t,TR_t = single_brison_w(Wp,Wb,wp,rp,wb,rb)
        #组合中股票的行业配置、选股、其它效应
        brison_t = pd.concat([AR_t,SR_t,IR_t],axis = 1)
        brison_t.columns=['AR_t','SR_t','IR_t']
        brison_t.loc[:,'enddate']=t
        brison_t1 = brison_t1.append(brison_t)

        #组合、基准由股票带来的收益、仓位配置、超额收益
        t2=pd.DataFrame([[RP_St, RB_St ,TR_t , PR_t]],columns=['RP_s_t','RB_s_t','TR_t','PR_t'])
        t2.loc[:,'enddate']=t
        brison_t2 = brison_t2.append(t2)

    brison_t1=brison_t1.reset_index().rename(columns={'index':'Industry'})
    brison_detail=pd.merge(brison_t2,brison_t1,on='enddate').fillna(method='ffill')

    return  brison_detail



def smooth_multi_birson_detail_w(brison_detail,p_k_t):
     '''
       多期调整后组合的brison
       brison_detail 某个类别资产的多期brison
       p_k_t  组合多期的每一期的kt，组合多期的K

     '''
     if brison_detail.empty:
         return brison_detail
     brison_detail=pd.merge(brison_detail,p_k_t,on='enddate',how='left')
     brison_detail=brison_detail[['enddate','Industry','RP_s_t',
                                'RB_s_t','TR_t','PR_t','AR_t','SR_t','IR_t','k_t','kk']]

     brison_detail.loc[:,['RP_s_t','RB_s_t','TR_t','PR_t','AR_t','SR_t','IR_t']]=\
        brison_detail[['RP_s_t','RB_s_t','TR_t','PR_t','AR_t','SR_t','IR_t']].multiply(brison_detail['k_t'],axis = 0).divide(brison_detail['kk'],axis = 0)

     return brison_detail



if __name__=='__main__':
     #股票
     Wp_df=pd.DataFrame([[0.8],[0.9]],columns=['weight'])
     Wb_df=pd.DataFrame([[0.8],[0.9]],columns=['weight'])
     #Wps_df=pd.DataFrame([[0.3,0.7],[0.4,0.6]],columns=['hy1','hy2'])
     Wps_df=pd.DataFrame([[0.009,0.991],[0.008,0.992]],columns=['hy1','hy2'])
     Wbs_df=pd.DataFrame([[0.5,0.5],[0.6,0.4]],columns=['hy1','hy2'])
     #Wbs_df=pd.DataFrame([[0.009,0.991],[0.008,0.992]],columns=['hy1','hy2'])
     Rps_df=pd.DataFrame([[0.04,0.01],[0.03,0.015]],columns=['hy1','hy2'])
     Rbs_df=pd.DataFrame([[0.01,0.02],[0.02,0.02]],columns=['hy1','hy2'])
     brison_det=multi_brison_detail_w(Wp_df,Wb_df,Wps_df,Rps_df,Wbs_df,Rbs_df)
     #brison_det['asset_type']='Astock'
     #股票资产带来的收益
     R_S_DF=brison_det[['RP_s_t','RB_s_t','enddate']].drop_duplicates()
    # print (brison_det)

     #其它资产
     Wp_df1=pd.DataFrame([[0.2],[0.1]],columns=['weight'])
     Wb_df1=pd.DataFrame([[0.2],[0.1]],columns=['weight'])
     Wps_df1=pd.DataFrame([[1.0],[1.0]],columns=['unkown_hy'])
     Wbs_df1=pd.DataFrame([[1.0],[1.0]],columns=['unkown_hy'])
     Rps_df1=pd.DataFrame([[0.01],[0.01]],columns=['unkown_hy'])
     Rbs_df1=pd.DataFrame([[0.01],[0.01]],columns=['unkown_hy'])
     brison_det1=multi_brison_detail_w(Wp_df1,Wb_df1,Wps_df1,Rps_df1,Wbs_df1,Rbs_df1)
     #brison_det1['asset_type']='Cash'
     #其它资产带来的收益
     R_O_DF=brison_det1[['RP_s_t','RB_s_t','enddate']].drop_duplicates().sort_values('enddate')
     #print (brison_det1)
     #组合的收益、累计收益、累计超额收益
     R_S_O=pd.concat([R_S_DF,R_O_DF],axis=0)
     R_P_B=R_S_O[['RP_s_t','RB_s_t']].groupby(R_S_O.enddate).sum().reset_index().sort_values('enddate')
     R_P_B.columns=['enddate','RP_t','RB_t']
     R_cum=(1+R_P_B[['RP_t','RB_t']]).cumprod()-1
     R_cum.columns=['RP_t_cum','RB_t_cum']
     R_P_B=pd.concat([R_P_B,R_cum],axis=1)
     R_P_B['TR_t_cum']=R_P_B['RP_t_cum']-R_P_B['RB_t_cum']
     #计算组合的K
     K=_cacu_k(R_P_B.RP_t_cum.iloc[-1],R_P_B.RB_t_cum.iloc[-1])

     #print (R_P_B)
     #计算组合的kt
     kt=[]
     for i in range(0,len(R_P_B)):
         ki=_cacu_k(R_P_B['RP_t'][i],R_P_B['RB_t'][i])
         kt.append(ki)

     #print (kt)
     #计算调整后的股票部分和其它资产的brison
     kt_df=pd.DataFrame([kt,[0,1]]).T

     kt_df.columns=['k_t','enddate']
     kt_df['kk']=K

     brison_det_sm=smooth_multi_birson_detail_w(brison_det,kt_df)
     brison_det_sm['asset_type']='Astock'
     brison_det_sm1=smooth_multi_birson_detail_w(brison_det1,kt_df)
     brison_det_sm1['asset_type']='Cash'
     brison_p_det=pd.concat([brison_det_sm,brison_det_sm1],axis=0)
     brison_p_det=pd.merge(R_P_B,brison_p_det,on='enddate',how='outer')
     brison_p_det=brison_p_det[['enddate','asset_type','Industry','RP_t','RB_t','RP_s_t',
                                'RB_s_t','TR_t','PR_t','AR_t','SR_t','IR_t','k_t']]

     print (brison_p_det)

     #组合累计超额收益的分解（股票和其它资产的累计TR）
     #第一层分解效应
     brison_p_tr=brison_p_det[['enddate','asset_type','TR_t']].drop_duplicates()
     brison_pv_tr=pd.pivot_table(brison_p_tr,values='TR_t',index=['enddate'],columns=['asset_type'])
     R_P_B=R_P_B.join(brison_pv_tr.cumsum(),how='outer')
     print (R_P_B)

     #第二层分解效应
     #股票和其它资产的累计TR的分解（PR+AR+SR+IR)
     #PR效应
     brison_pr=brison_p_det[['enddate','asset_type','PR_t']].drop_duplicates()
     brison_pr_pt=pd.pivot_table(brison_pr,values='PR_t',index=['enddate'],columns=['asset_type'])
     brison_pr_cum=brison_pr_pt.cumsum().unstack().reset_index()
     brison_pr_cum.columns=['asset_type','enddate','PR_t_cum']
     #股票和其它资产AR+SR+IR分解
     brison_trs=brison_p_det[['enddate','asset_type','Industry','AR_t','SR_t','IR_t']]
     brison_trs_pt=pd.pivot_table(brison_trs,values=['AR_t','SR_t','IR_t'],index=['enddate'],columns=['asset_type'],aggfunc='sum')
     brison_trs_cum=brison_trs_pt.cumsum().unstack().reset_index()
     brison_trs_cum.columns=['t_cmpt','asset_type','enddate','t_cum']
     brison_trs_cum=pd.pivot_table(brison_trs_cum,values=['t_cum'],index=['asset_type','enddate'],columns=['t_cmpt']).reset_index()
     brison_trs_cum.columns=['asset_type','enddate','AR_t_cum','IR_t_cum','SR_t_cum']
     brison_trs_cum=brison_trs_cum[['asset_type','enddate','AR_t_cum','SR_t_cum','IR_t_cum']]
     #合并PR与AR+SR+IR
     R_PS_BS=pd.merge(brison_pr_cum,brison_trs_cum,on=['asset_type','enddate'],how='inner')
     R_P_TR=R_P_B[['enddate','Astock','Cash']].set_index('enddate').unstack().reset_index()
     R_P_TR.columns=['asset_type','enddate','TR_t_cum']
     R_PS_BS=pd.merge(R_P_TR,R_PS_BS,on=['asset_type','enddate'],how='inner')
     R_PS_BS['TRS_t_cum']=R_PS_BS['AR_t_cum']+R_PS_BS['SR_t_cum']+R_PS_BS['IR_t_cum']
     print (R_PS_BS)

     #第三层行业和个股分解效应、内部效应TRS分解（AR+SR+IR)
     brison_trs_hy=brison_p_det[['enddate','asset_type','Industry','AR_t','SR_t','IR_t']]
     brison_trs_hypt=pd.pivot_table(brison_trs_hy,values=['AR_t','SR_t','IR_t'],index=['enddate'],columns=['asset_type','Industry'])
     brison_trs_hycum=brison_trs_hypt.cumsum().unstack().reset_index()
     brison_trs_hycum.columns=['t_cmpt','asset_type','Industry','enddate','t_cum']
     brsion_trs_hycum=pd.pivot_table(brison_trs_hycum,values='t_cum',index=['asset_type','enddate','Industry'],columns=['t_cmpt']).reset_index()
     brsion_trs_hycum['TR_t']=brsion_trs_hycum['AR_t']+brsion_trs_hycum['SR_t']+brsion_trs_hycum['IR_t']
     brsion_trs_hycum.columns=['asset_type','enddate','Industry','AR_t_cum','IR_t_cum','SR_t_cum','TR_t_cum']
     brsion_trs_hycum=brsion_trs_hycum[['asset_type','enddate','Industry','TR_t_cum','AR_t_cum','SR_t_cum','IR_t_cum']]
     R_PT_BT=pd.merge(R_PS_BS[['asset_type','enddate','TRS_t_cum']],brsion_trs_hycum,on=['asset_type','enddate'])
     print (R_PT_BT)

     atype='Astock'
     dt=R_PT_BT.enddate.drop_duplicates().max() #最大日期
     #股票部分的累计效应分解
     brison_ts=R_PS_BS[R_PS_BS.asset_type==atype]
     brison_ts=brison_ts[['enddate','AR_t_cum','SR_t_cum','IR_t_cum','TR_t_cum']].reset_index(drop=1)
     print (brison_ts)
     #股票部分的行业分解效应
     brison_hy=R_PT_BT[(R_PT_BT.enddate==dt)&(R_PT_BT.asset_type==atype)]
     brison_hy=brison_hy[['AR_t_cum','SR_t_cum','IR_t_cum','TR_t_cum']].reset_index(drop=1)
     print (brison_hy)

     brison_total=brison_hy.sum(axis=0)
     print (brison_total)

