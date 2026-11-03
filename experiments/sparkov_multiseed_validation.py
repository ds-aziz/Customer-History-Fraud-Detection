#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

BASE=["age","gender","merchant","category","amt"]
CAT=["gender","merchant","category"]
HIST=["previous_transaction_count","previous_amount_mean","previous_amount_std","previous_amount_max","previous_amount_last","amount_vs_previous_mean","has_previous_history"]
ORDER=["0","1","2-3","4-5","6-10","11-20","21+"]

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True)
    p.add_argument("--output-dir",default="results/sparkov_robustness")
    p.add_argument("--iterations",type=int,default=60)
    p.add_argument("--seeds",default="11,22,33,44,55")
    p.add_argument("--group-bootstrap",type=int,default=200)
    return p.parse_args()

def load_data(path):
    use=["trans_date_trans_time","cc_num","merchant","category","amt","gender","dob","trans_num","unix_time","is_fraud"]
    df=pd.read_csv(path,usecols=use)
    df["trans_date_trans_time"]=pd.to_datetime(df["trans_date_trans_time"],errors="coerce")
    df["dob"]=pd.to_datetime(df["dob"],errors="coerce")
    df["age"]=(df["trans_date_trans_time"]-df["dob"]).dt.days/365.25
    df["amt"]=pd.to_numeric(df["amt"],errors="coerce")
    df["unix_time"]=pd.to_numeric(df["unix_time"],errors="coerce")
    df["is_fraud"]=pd.to_numeric(df["is_fraud"],errors="coerce").astype(int)
    df["cc_num"]=df["cc_num"].astype(str)
    return df

def add_history(df):
    df=df.sort_values(["cc_num","unix_time","trans_num"]).copy()
    g=df.groupby("cc_num",sort=False)
    df["previous_transaction_count"]=g.cumcount()
    df["previous_amount_mean"]=g["amt"].transform(lambda s:s.expanding().mean().shift(1))
    df["previous_amount_std"]=g["amt"].transform(lambda s:s.expanding().std().shift(1))
    df["previous_amount_max"]=g["amt"].transform(lambda s:s.cummax().shift(1))
    df["previous_amount_last"]=g["amt"].shift(1)
    df["amount_vs_previous_mean"]=np.where(
        df["previous_amount_mean"].notna() & (df["previous_amount_mean"]>0),
        df["amt"]/df["previous_amount_mean"],np.nan)
    df["has_previous_history"]=(df["previous_transaction_count"]>0).astype(int)
    df["history_group"]=pd.cut(
        df["previous_transaction_count"],
        [-0.5,0.5,1.5,3.5,5.5,10.5,20.5,np.inf],
        labels=ORDER)
    return df

def split_cards(df,seed):
    cards=df["cc_num"].drop_duplicates().to_numpy()
    tr,tmp=train_test_split(cards,test_size=.30,random_state=seed)
    va,te=train_test_split(tmp,test_size=.50,random_state=seed)
    return (
        df[df.cc_num.isin(tr)].copy(),
        df[df.cc_num.isin(va)].copy(),
        df[df.cc_num.isin(te)].copy()
    )

def prep(df,features):
    x=df[features].copy()
    for c in CAT:
        if c in x:
            x[c]=x[c].fillna("__MISSING__").astype(str)
    return x

def fit(tr,va,features,iters,seed):
    m=CatBoostClassifier(
        iterations=iters,learning_rate=.06,depth=7,
        loss_function="Logloss",eval_metric="AUC",
        random_seed=seed,verbose=False,allow_writing_files=False)
    m.fit(
        prep(tr,features),tr.is_fraud,
        cat_features=[c for c in CAT if c in features],
        eval_set=(prep(va,features),va.is_fraud),
        use_best_model=True,verbose=False)
    return m

def ap(y,p):
    y=np.asarray(y)
    return float(average_precision_score(y,p)) if y.sum()>0 and len(np.unique(y))>1 else np.nan

def group_bootstrap(x,n,seed):
    if len(x)==0 or x.is_fraud.sum()==0:
        return (np.nan,np.nan,np.nan,0)
    rng=np.random.default_rng(seed)
    cards=x.cc_num.drop_duplicates().to_numpy()
    frames={c:g for c,g in x.groupby("cc_num",sort=False)}
    diffs=[]
    for _ in range(n):
        samp=rng.choice(cards,size=len(cards),replace=True)
        b=pd.concat([frames[c] for c in samp],ignore_index=True)
        if b.is_fraud.sum()==0 or b.is_fraud.nunique()<2:
            continue
        diffs.append(ap(b.is_fraud,b.history_probability)-ap(b.is_fraud,b.simple_probability))
    if not diffs:
        return (np.nan,np.nan,np.nan,0)
    a=np.asarray(diffs)
    return (float(a.mean()),float(np.quantile(a,.025)),float(np.quantile(a,.975)),len(a))

def main():
    a=parse_args()
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    seeds=[int(x) for x in a.seeds.split(",") if x.strip()]
    df=add_history(load_data(a.csv))

    overall_rows=[]
    group_rows=[]

    for seed in seeds:
        tr,va,te=split_cards(df,seed)
        sm=fit(tr,va,BASE,a.iterations,seed)
        hm=fit(tr,va,BASE+HIST,a.iterations,seed)
        sp=sm.predict_proba(prep(te,BASE))[:,1]
        hp=hm.predict_proba(prep(te,BASE+HIST))[:,1]
        sap=ap(te.is_fraud,sp); hap=ap(te.is_fraud,hp)
        overall_rows.append({
            "seed":seed,"test_cards":te.cc_num.nunique(),"test_n":len(te),
            "fraud_n":int(te.is_fraud.sum()),"simple_pr_auc":sap,
            "history_pr_auc":hap,"pr_auc_difference":hap-sap})
        tmp=te[["cc_num","is_fraud","history_group"]].copy()
        tmp["simple_probability"]=sp
        tmp["history_probability"]=hp
        for gr in ORDER:
            x=tmp[tmp.history_group.astype(str)==gr]
            if len(x)==0:
                continue
            s=ap(x.is_fraud,x.simple_probability)
            h=ap(x.is_fraud,x.history_probability)
            mean,lo,hi,reps=group_bootstrap(x,a.group_bootstrap,seed+1000)
            group_rows.append({
                "seed":seed,"history_group":gr,"n":len(x),
                "fraud_n":int(x.is_fraud.sum()),
                "simple_pr_auc":s,"history_pr_auc":h,
                "pr_auc_difference":h-s if np.isfinite(s) and np.isfinite(h) else np.nan,
                "bootstrap_mean_difference":mean,
                "bootstrap_ci95_low":lo,
                "bootstrap_ci95_high":hi,
                "bootstrap_replicates":reps})

    overall=pd.DataFrame(overall_rows)
    groups=pd.DataFrame(group_rows)
    overall.to_csv(out/"multiseed_overall.csv",index=False)
    groups.to_csv(out/"multiseed_history_groups.csv",index=False)

    agg=[]
    for gr in ORDER:
        x=groups[groups.history_group==gr]
        if len(x)==0: continue
        d=x.pr_auc_difference.dropna()
        agg.append({
            "history_group":gr,
            "splits_tested":int(len(d)),
            "positive_splits":int((d>0).sum()),
            "mean_pr_auc_difference":float(d.mean()) if len(d) else None,
            "min_pr_auc_difference":float(d.min()) if len(d) else None,
            "max_pr_auc_difference":float(d.max()) if len(d) else None,
            "mean_fraud_n":float(x.fraud_n.mean()),
            "splits_with_bootstrap_ci_above_zero":int((x.bootstrap_ci95_low>0).sum())
        })
    pd.DataFrame(agg).to_csv(out/"history_group_summary.csv",index=False)

    summary={
        "rows":int(len(df)),"cards":int(df.cc_num.nunique()),"fraud_rows":int(df.is_fraud.sum()),
        "base_features":BASE,
        "seeds":seeds,
        "overall":{
            "positive_splits":int((overall.pr_auc_difference>0).sum()),
            "splits_tested":int(len(overall)),
            "mean_simple_pr_auc":float(overall.simple_pr_auc.mean()),
            "mean_history_pr_auc":float(overall.history_pr_auc.mean()),
            "mean_pr_auc_gain":float(overall.pr_auc_difference.mean()),
            "min_pr_auc_gain":float(overall.pr_auc_difference.min()),
            "max_pr_auc_gain":float(overall.pr_auc_difference.max())
        }
    }
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    print("\nOverall:")
    print(overall.to_string(index=False))
    print("\nHistory groups:")
    print(pd.DataFrame(agg).to_string(index=False))

if __name__=="__main__":
    main()
