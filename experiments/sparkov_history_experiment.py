#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

SEED=42
BASE=["gender","merchant","category","amt"]
CAT=["gender","merchant","category"]
HIST=["previous_transaction_count","previous_amount_mean","previous_amount_std","previous_amount_max","previous_amount_last","amount_vs_previous_mean","has_previous_history"]
ORDER=["0","1","2-3","4-5","6-10","11-20","21+"]

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True)
    p.add_argument("--output-dir",default="results/sparkov")
    p.add_argument("--iterations",type=int,default=300)
    p.add_argument("--bootstrap",type=int,default=500)
    p.add_argument("--seed",type=int,default=SEED)
    return p.parse_args()

def add_history(df):
    df=df.sort_values(["cc_num","unix_time","trans_num"]).copy()
    g=df.groupby("cc_num",sort=False)
    df["previous_transaction_count"]=g.cumcount()
    df["previous_amount_mean"]=g["amt"].transform(lambda s:s.expanding().mean().shift(1))
    df["previous_amount_std"]=g["amt"].transform(lambda s:s.expanding().std().shift(1))
    df["previous_amount_max"]=g["amt"].transform(lambda s:s.cummax().shift(1))
    df["previous_amount_last"]=g["amt"].shift(1)
    df["amount_vs_previous_mean"]=np.where(df["previous_amount_mean"].notna() & (df["previous_amount_mean"]>0),df["amt"]/df["previous_amount_mean"],np.nan)
    df["has_previous_history"]=(df["previous_transaction_count"]>0).astype(int)
    df["history_group"]=pd.cut(df["previous_transaction_count"],[-0.5,0.5,1.5,3.5,5.5,10.5,20.5,np.inf],labels=ORDER)
    return df

def split(df,seed):
    cards=df["cc_num"].drop_duplicates().to_numpy()
    tr,tmp=train_test_split(cards,test_size=.30,random_state=seed)
    va,te=train_test_split(tmp,test_size=.50,random_state=seed)
    return (df[df.cc_num.isin(tr)].copy(),df[df.cc_num.isin(va)].copy(),df[df.cc_num.isin(te)].copy())

def prep(df,features):
    x=df[features].copy()
    for c in CAT:
        if c in x: x[c]=x[c].fillna("__MISSING__").astype(str)
    return x

def fit(tr,va,features,iters,seed):
    m=CatBoostClassifier(iterations=iters,learning_rate=.05,depth=7,loss_function="Logloss",eval_metric="AUC",random_seed=seed,verbose=False,allow_writing_files=False)
    m.fit(prep(tr,features),tr.is_fraud.astype(int),cat_features=[c for c in CAT if c in features],eval_set=(prep(va,features),va.is_fraud.astype(int)),use_best_model=True,verbose=False)
    return m

def thr(y,p):
    ts=np.linspace(.01,.99,99); fs=[f1_score(y,p>=t,zero_division=0) for t in ts]
    return float(ts[int(np.argmax(fs))])

def metrics(y,p,t):
    pr=p>=t
    return {"n":int(len(y)),"fraud_n":int(np.sum(y)),"fraud_rate":float(np.mean(y)),"pr_auc":float(average_precision_score(y,p)) if np.sum(y)>0 else None,"roc_auc":float(roc_auc_score(y,p)) if len(np.unique(y))>1 else None,"precision":float(precision_score(y,pr,zero_division=0)),"recall":float(recall_score(y,pr,zero_division=0)),"f1":float(f1_score(y,pr,zero_division=0)),"threshold":t}

def bootstrap(test,sp,hp,n,seed):
    rng=np.random.default_rng(seed)
    cards=test.cc_num.drop_duplicates().to_numpy()
    w=test[["cc_num","is_fraud"]].copy(); w["s"]=sp; w["h"]=hp
    frames={c:g for c,g in w.groupby("cc_num",sort=False)}
    diffs=[]
    for _ in range(n):
        samp=rng.choice(cards,size=len(cards),replace=True)
        b=pd.concat([frames[c] for c in samp],ignore_index=True)
        y=b.is_fraud.to_numpy()
        if y.sum()==0: continue
        diffs.append(average_precision_score(y,b.h)-average_precision_score(y,b.s))
    a=np.asarray(diffs)
    return {"mean_difference":float(a.mean()),"ci95_low":float(np.quantile(a,.025)),"ci95_high":float(np.quantile(a,.975)),"bootstrap_replicates":int(len(a))}

def main():
    a=args(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    use=["trans_date_trans_time","cc_num","merchant","category","amt","gender","trans_num","unix_time","is_fraud"]
    df=pd.read_csv(a.csv,usecols=use)
    df["amt"]=pd.to_numeric(df.amt); df["unix_time"]=pd.to_numeric(df.unix_time); df["is_fraud"]=pd.to_numeric(df.is_fraud).astype(int); df["cc_num"]=df.cc_num.astype(str)
    df=add_history(df)
    tr,va,te=split(df,a.seed)
    sm=fit(tr,va,BASE,a.iterations,a.seed); hm=fit(tr,va,BASE+HIST,a.iterations,a.seed)
    sv=sm.predict_proba(prep(va,BASE))[:,1]; hv=hm.predict_proba(prep(va,BASE+HIST))[:,1]
    st=thr(va.is_fraud.to_numpy(),sv); ht=thr(va.is_fraud.to_numpy(),hv)
    sp=sm.predict_proba(prep(te,BASE))[:,1]; hp=hm.predict_proba(prep(te,BASE+HIST))[:,1]
    overall={"simple":metrics(te.is_fraud.to_numpy(),sp,st),"history":metrics(te.is_fraud.to_numpy(),hp,ht)}
    overall["pr_auc_difference_history_minus_simple"]=overall["history"]["pr_auc"]-overall["simple"]["pr_auc"]
    overall["customer_bootstrap_pr_auc_difference"]=bootstrap(te,sp,hp,a.bootstrap,a.seed)
    te=te.copy(); te["simple_probability"]=sp; te["history_probability"]=hp
    rows=[]
    for gr in ORDER:
        x=te[te.history_group.astype(str)==gr]
        if len(x)==0: continue
        s=metrics(x.is_fraud.to_numpy(),x.simple_probability.to_numpy(),st)
        h=metrics(x.is_fraud.to_numpy(),x.history_probability.to_numpy(),ht)
        rows.append({"history_group":gr,"n":len(x),"fraud_n":int(x.is_fraud.sum()),"simple_pr_auc":s["pr_auc"],"history_pr_auc":h["pr_auc"],"pr_auc_difference":None if s["pr_auc"] is None or h["pr_auc"] is None else h["pr_auc"]-s["pr_auc"]})
    pd.DataFrame(rows).to_csv(out/"history_group_results.csv",index=False)
    summary={"rows":int(len(df)),"cards":int(df.cc_num.nunique()),"fraud_rows":int(df.is_fraud.sum()),"split_cards":{"train":int(tr.cc_num.nunique()),"validation":int(va.cc_num.nunique()),"test":int(te.cc_num.nunique())},"overall":overall}
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))
if __name__=="__main__": main()
