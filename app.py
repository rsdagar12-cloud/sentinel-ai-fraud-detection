import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(page_title="Sentinel | Retail Leakage Control Tower", page_icon="🛡️", layout="wide")

CSS = """
<style>
.stApp{background:radial-gradient(circle at 12% 8%,rgba(37,99,235,.24),transparent 30%),radial-gradient(circle at 88% 18%,rgba(34,197,94,.13),transparent 28%),linear-gradient(180deg,#020617 0%,#06101f 48%,#020617 100%);color:#e5eefb}.block-container{padding-top:2.2rem;max-width:1280px}section[data-testid="stSidebar"]{background:linear-gradient(180deg,#050b16,#091524);border-right:1px solid rgba(148,163,184,.14)}h1,h2,h3{color:#f8fafc!important}.hero{background:linear-gradient(135deg,rgba(29,78,216,.98),rgba(2,6,23,.96));border:1px solid rgba(147,197,253,.22);border-radius:28px;padding:28px 32px;margin-bottom:18px;box-shadow:0 24px 55px rgba(0,0,0,.42)}.tag{color:#bfdbfe;text-transform:uppercase;letter-spacing:1.7px;font-size:.78rem;font-weight:900}.title{font-size:3.05rem;line-height:.98;font-weight:950;letter-spacing:-2px;color:white;margin:10px 0 12px}.sub{color:#dbeafe;font-size:1rem;line-height:1.45;max-width:980px}.kpi{background:rgba(8,15,28,.94);border:1px solid rgba(148,163,184,.16);border-radius:22px;padding:18px;min-height:120px;box-shadow:0 14px 28px rgba(0,0,0,.25)}.klabel{color:#93c5fd;font-size:.72rem;text-transform:uppercase;letter-spacing:1.2px;font-weight:900}.kval{color:#fff;font-size:2rem;font-weight:950;margin-top:7px}.knote{color:#cbd5e1;font-size:.9rem;line-height:1.28;margin-top:6px}.decision{background:linear-gradient(135deg,rgba(248,113,113,.18),rgba(245,158,11,.13));border:1px solid rgba(251,113,133,.35);border-radius:24px;padding:22px;margin:18px 0}.decision h3{font-size:1.35rem;margin:0 0 8px}.decision .big{font-size:1.9rem;font-weight:950;line-height:1.05;color:#fff;margin:0 0 10px}.pill{display:inline-block;background:rgba(15,23,42,.8);border:1px solid rgba(148,163,184,.18);border-radius:999px;padding:7px 10px;margin:4px 5px 0 0;color:#dbeafe;font-size:.86rem;font-weight:800}.panel{background:rgba(8,15,28,.9);border:1px solid rgba(148,163,184,.14);border-radius:22px;padding:18px;box-shadow:0 14px 30px rgba(0,0,0,.2);margin-bottom:16px}.ptitle{font-size:1.12rem;font-weight:900;color:#f8fafc;margin-bottom:12px}.micro{background:rgba(10,17,31,.95);border:1px solid rgba(148,163,184,.13);border-radius:18px;padding:16px;min-height:142px}.microtitle{font-weight:950;color:white;font-size:1.02rem;margin-bottom:8px}.microcopy{color:#cbd5e1;font-size:.92rem;line-height:1.38}.flow{display:flex;align-items:center;gap:12px;background:rgba(10,17,31,.9);border:1px solid rgba(96,165,250,.16);border-radius:18px;padding:15px}.icon{font-size:1.7rem}.flowtitle{color:white;font-weight:900}.flowcopy{color:#cbd5e1;font-size:.86rem}.value{display:flex;justify-content:space-between;gap:16px;align-items:center;background:rgba(2,6,23,.6);border:1px solid rgba(148,163,184,.14);border-radius:14px;padding:13px 14px;margin-bottom:10px}.vlabel{color:#cbd5e1;font-weight:800}.vnum{color:white;font-weight:950;font-size:1.12rem;text-align:right}.story{background:linear-gradient(135deg,rgba(251,191,36,.13),rgba(59,130,246,.10));border:1px solid rgba(251,191,36,.28);border-radius:18px;padding:16px}.warn{background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.30);border-radius:16px;padding:14px;color:#dcfce7;font-weight:750}.small{color:#94a3b8;font-size:.84rem;line-height:1.35}div[data-testid="stMetric"]{background:rgba(8,15,28,.82);border:1px solid rgba(148,163,184,.13);border-radius:16px;padding:10px 14px}button[kind="primary"]{border-radius:12px!important}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def money(x): return f"${x:,.0f}"

def pick(cols, opts):
    low={c.lower():c for c in cols}
    for o in opts:
        if o.lower() in low: return low[o.lower()]
    return None

def demo_data():
    rows=[
        ["T001","2026-05-20 10:04","Union Station","Xbox Series X",2,649,"CARD_8841","C201"],
        ["T002","2026-05-20 13:10","Eaton Centre","Xbox Series X",3,649,"CARD_8841","C202"],
        ["T003","2026-05-20 15:05","Scarborough Town","Xbox Series X",2,649,"CARD_8841","C203"],
        ["T004","2026-05-20 16:12","Square One","Xbox Series X",1,649,"CARD_8841","C204"],
        ["T005","2026-05-21 11:30","Union Station","AirPods Pro",1,329,"CARD_9211","C205"],
        ["T006","2026-05-21 12:40","Eaton Centre","iPhone 15",2,1129,"CARD_2230","C206"],
        ["T007","2026-05-21 13:15","Union Station","PlayStation 5",2,649,"CARD_6200","C207"],
        ["T008","2026-05-21 15:50","Scarborough Town","Nintendo Switch OLED",2,449,"CARD_6200","C208"],
        ["T009","2026-05-22 10:08","Square One","Xbox Series X",2,649,"CARD_8841","C209"],
        ["T010","2026-05-22 14:24","Union Station","MacBook Air",1,1499,"CARD_4040","C210"],
        ["T011","2026-05-22 17:05","Eaton Centre","Xbox Series X",2,649,"CARD_8841","C211"],
        ["T012","2026-05-22 18:15","Square One","Gift Card",6,100,"CARD_7711","C212"],
        ["T013","2026-05-23 11:45","Scarborough Town","Xbox Series X",3,649,"CARD_8841","C213"],
        ["T014","2026-05-23 12:55","Union Station","Xbox Series X",2,649,"CARD_8841","C214"],
        ["T015","2026-05-23 16:35","Eaton Centre","Samsung S24",2,1199,"CARD_5300","C215"],
    ]
    return pd.DataFrame(rows,columns=["transaction_id","timestamp","store","product","quantity","unit_price","payment_signal","customer_id"])

def normalize(df):
    cols=list(df.columns); out=pd.DataFrame()
    m={
        "transaction_id":pick(cols,["transaction_id","txn_id","id","transaction"]),
        "timestamp":pick(cols,["timestamp","date","datetime","time"]),
        "store":pick(cols,["store","store_id","location","branch"]),
        "product":pick(cols,["product","item","sku","category"]),
        "quantity":pick(cols,["quantity","qty","units"]),
        "unit_price":pick(cols,["unit_price","price","amount","value","ticket"]),
        "payment_signal":pick(cols,["payment_signal","payment_method","payment","card","payment_id"]),
        "customer_id":pick(cols,["customer_id","customer","client","user_id"]),
    }
    out["transaction_id"]=df[m["transaction_id"]].astype(str) if m["transaction_id"] else [f"TX{i+1:03d}" for i in range(len(df))]
    out["timestamp"]=pd.to_datetime(df[m["timestamp"]],errors="coerce") if m["timestamp"] else pd.Timestamp.today()
    out["store"]=df[m["store"]].astype(str) if m["store"] else "Store A"
    out["product"]=df[m["product"]].astype(str) if m["product"] else "Unknown Product"
    out["quantity"]=pd.to_numeric(df[m["quantity"]],errors="coerce").fillna(1).clip(lower=1) if m["quantity"] else 1
    out["unit_price"]=pd.to_numeric(df[m["unit_price"]],errors="coerce").fillna(100) if m["unit_price"] else 100
    out["payment_signal"]=df[m["payment_signal"]].astype(str) if m["payment_signal"] else [f"SIG_{i%5}" for i in range(len(df))]
    out["customer_id"]=df[m["customer_id"]].astype(str) if m["customer_id"] else [f"C{i+1:03d}" for i in range(len(df))]
    out["total_value"]=out["quantity"]*out["unit_price"]
    out["date"]=out["timestamp"].dt.date
    return out

def analyze(raw, capture=.55, attach=175, mins=4):
    df=normalize(raw)
    scarce=["xbox","playstation","ps5","iphone","s24","macbook","switch","airpods","gpu","gift card"]
    df["scarce_flag"]=df["product"].str.lower().apply(lambda x:any(k in x for k in scarce))
    sig_tx=df.groupby("payment_signal")["transaction_id"].transform("count")
    sig_store=df.groupby("payment_signal")["store"].transform("nunique")
    sig_units=df.groupby("payment_signal")["quantity"].transform("sum")
    cust_tx=df.groupby("customer_id")["transaction_id"].transform("count")
    score=np.zeros(len(df))
    score+=np.where(df["scarce_flag"],25,0)+np.where(df["quantity"]>=2,15,0)+np.where(df["total_value"]>=1000,10,0)
    score+=np.where(sig_tx>=3,20,0)+np.where(sig_store>=2,20,0)+np.where(sig_units>=8,15,0)+np.where(cust_tx>=2,10,0)
    df["risk_score"]=score.astype(int)
    df["risk_tier"]=pd.cut(df["risk_score"],[-1,44,69,999],labels=["Low","Medium","High"]).astype(str)
    def reasons(r):
        bits=[]
        if r.scarce_flag: bits.append("scarce product")
        if r.quantity>=2: bits.append("multi-unit purchase")
        if sig_tx.loc[r.name]>=3: bits.append("repeat payment signal")
        if sig_store.loc[r.name]>=2: bits.append("cross-store pattern")
        if sig_units.loc[r.name]>=8: bits.append("cumulative volume")
        return ", ".join(bits) if bits else "standard purchase"
    df["reasons"]=df.apply(reasons,axis=1)
    flagged=df[df.risk_tier.isin(["High","Medium"])].copy().sort_values(["risk_score","total_value"],ascending=False)
    store=flagged.groupby("store").agg(flagged_transactions=("transaction_id","count"), exposure=("total_value","sum"), avg_risk=("risk_score","mean")).reset_index().sort_values("exposure",ascending=False)
    signal=flagged.groupby("payment_signal").agg(transactions=("transaction_id","count"),stores=("store","nunique"),units=("quantity","sum"),exposure=("total_value","sum")).reset_index().sort_values(["stores","exposure"],ascending=False)
    exposure=float(flagged.total_value.sum()) if len(flagged) else 0
    protected=round(exposure*capture,0)
    rev=round((protected/max(float(flagged.unit_price.mean() if len(flagged) else 1),1))*attach,0)
    summary={
        "transactions_reviewed":len(df),"flagged_transactions":len(flagged),"inventory_exposure":exposure,"protected_inventory":protected,
        "stores_hit":flagged.store.nunique() if len(flagged) else 0,"linked_signals":int((signal.stores>=2).sum()) if len(signal) else 0,
        "revenue_protected":rev,"review_minutes_saved":int(max(len(flagged)*mins,0)),
        "high_risk_count":int((flagged.risk_tier=="High").sum()),"medium_risk_count":int((flagged.risk_tier=="Medium").sum()),
        "customer_visits_protected":int(round(protected/max(float(flagged.unit_price.mean() if len(flagged) else 1),1),0))
    }
    return {"raw":raw,"scored":df,"flagged":flagged,"store":store,"signal":signal,"summary":summary,
            "top_store":store.iloc[0].store if len(store) else "No store","top_signal":signal.iloc[0].payment_signal if len(signal) else "No linked signal",
            "capture":capture,"attach":attach,"mins":mins}

def ensure():
    if "raw" not in st.session_state:
        st.session_state.raw=demo_data(); st.session_state.source="Executive demo dataset"
    if "capture" not in st.session_state:
        st.session_state.capture=.55; st.session_state.attach=175; st.session_state.mins=4
    st.session_state.report=analyze(st.session_state.raw,st.session_state.capture,st.session_state.attach,st.session_state.mins)

def hero(title,sub,tag="Retail Leakage Control Tower"):
    st.markdown(f'<div class="hero"><div class="tag">{tag}</div><div class="title">{title}</div><div class="sub">{sub}</div></div>',unsafe_allow_html=True)

def kpi(label,value,note):
    st.markdown(f'<div class="kpi"><div class="klabel">{label}</div><div class="kval">{value}</div><div class="knote">{note}</div></div>',unsafe_allow_html=True)

def value_line(label,value):
    st.markdown(f'<div class="value"><div class="vlabel">{label}</div><div class="vnum">{value}</div></div>',unsafe_allow_html=True)

def store_chart(r):
    d=r["store"]
    fig=px.bar(d,x="store",y="exposure",text="flagged_transactions",color="avg_risk",color_continuous_scale=["#fde68a","#f97316","#ef4444"])
    fig.update_traces(texttemplate="%{text} txn",textposition="outside")
    fig.update_layout(height=315,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e5eefb"),margin=dict(l=10,r=10,t=10,b=10),coloraxis_showscale=False,xaxis_title="",yaxis_title="Exposure ($)")
    return fig

def risk_donut(s):
    vals=[s["high_risk_count"],s["medium_risk_count"],max(s["transactions_reviewed"]-s["flagged_transactions"],0)]
    fig=go.Figure(data=[go.Pie(labels=["High","Medium","Clear"],values=vals,hole=.64,marker=dict(colors=["#fb7185","#fbbf24","#34d399"]),sort=False,textinfo="label+value")])
    fig.update_layout(height=315,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e5eefb"),margin=dict(l=10,r=10,t=10,b=10),showlegend=False)
    return fig

def brief_text(r):
    s=r["summary"]
    return f"""Sentinel Executive Brief
Prepared by: Rahul Singh

Problem
Retail teams often see only isolated transactions. Reseller/proxy behavior becomes visible only when signals are connected across stores, products, payment methods, and time.

Finding
Sentinel reviewed {s['transactions_reviewed']} transactions and prioritized {s['flagged_transactions']} for manager review. Estimated inventory exposure is {money(s['inventory_exposure'])} across {s['stores_hit']} store(s). The strongest concentration is {r['top_store']}; the strongest linked signal is {r['top_signal']}.

Today's Decision
Review scarce-product transactions linked to {r['top_signal']} before the next restock cycle. Do not automatically deny customers. Use Sentinel as a review queue for fair, evidence-based inspection.

Value Hypothesis
- Protected inventory opportunity: {money(s['protected_inventory'])}
- Attach/accessory revenue preserved: {money(s['revenue_protected'])}
- Customer visits protected: {s['customer_visits_protected']}
- Manager review time saved: {s['review_minutes_saved']} minutes per cycle

Responsible AI
Sentinel flags behavioral risk indicators only. It does not prove fraud or illegal activity. Final action requires human review, consistent policy, and fair treatment of all customers.
"""

def command_center(r):
    s=r["summary"]
    hero("Resellers adapt. Sentinel catches the shift.","Retailers block bots online. Sentinel detects the offline proxy-buying patterns that still leak scarce inventory across physical stores.")
    cols=st.columns(4)
    data=[("Inventory exposure",money(s["inventory_exposure"]),"Value sitting behind review signals"),("Stores impacted",s["stores_hit"],"Locations needing manager attention"),("Linked signals",s["linked_signals"],"Repeated payment/proxy patterns"),("Revenue protected",money(s["revenue_protected"]),"Attach opportunity preserved")]
    for c,d in zip(cols,data):
        with c: kpi(*d)
    st.markdown(f'<div class="decision"><h3>Today’s decision</h3><div class="big">Review {s["high_risk_count"]} high-risk transaction(s) before the next scarce-product restock.</div><span class="pill">Top store: {r["top_store"]}</span><span class="pill">Linked signal: {r["top_signal"]}</span><span class="pill">Exposure: {money(s["inventory_exposure"])}</span><span class="pill">Action: human review, not automatic denial</span></div>',unsafe_allow_html=True)
    left,right=st.columns([1.15,1])
    with left:
        st.markdown('<div class="panel"><div class="ptitle">Where the issue is concentrated</div>',unsafe_allow_html=True); st.plotly_chart(store_chart(r),use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="ptitle">Risk mix</div>',unsafe_allow_html=True); st.plotly_chart(risk_donut(s),use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("## The story in one screen")
    c1,c2,c3,c4=st.columns(4)
    cards=[("🧱","1. Online wall","Bot controls reduce checkout abuse."),("🧍","2. Offline proxy","Buyers split scarce items across stores."),("🕳️","3. Leakage","Real customers miss stock and attach revenue drops."),("🛡️","4. Sentinel","Managers get a fair review queue before restock.")]
    for c,(ic,t,cp) in zip([c1,c2,c3,c4],cards):
        with c: st.markdown(f'<div class="flow"><div class="icon">{ic}</div><div><div class="flowtitle">{t}</div><div class="flowcopy">{cp}</div></div></div>',unsafe_allow_html=True)

def todays_decision(r):
    s=r["summary"]
    hero("Today’s decision", "A manager should not hunt through raw transactions. Sentinel turns the day into one clear operating move.", "Decision System")
    st.markdown(f'<div class="decision"><h3>Recommended move</h3><div class="big">Hold a manager review for scarce-product transactions connected to {r["top_signal"]}.</div><span class="pill">{s["flagged_transactions"]} transactions prioritized</span><span class="pill">{s["stores_hit"]} stores affected</span><span class="pill">{money(s["protected_inventory"])} protected inventory opportunity</span></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a: st.markdown('<div class="micro"><div class="microtitle">Store manager</div><div class="microcopy">Check the queue before releasing scarce stock. Verify pattern context. Escalate only the linked cases.</div></div>',unsafe_allow_html=True)
    with b: st.markdown('<div class="micro"><div class="microtitle">District manager</div><div class="microcopy">Look across stores. Decide whether the pattern is isolated, coordinated, or policy-relevant.</div></div>',unsafe_allow_html=True)
    with c: st.markdown('<div class="micro"><div class="microtitle">Operations lead</div><div class="microcopy">Use weekly patterns to adjust restock guardrails, coaching, and scarce-item handling.</div></div>',unsafe_allow_html=True)

def scenario(r):
    hero("Scenario calculator", "Tune assumptions like a consulting model. See how leakage, attach revenue, customer experience, and review time move together.", "Business Impact")
    c1,c2,c3=st.columns(3)
    with c1: cap=st.slider("Inventory protection assumption",10,90,int(st.session_state.capture*100),5)/100
    with c2: attach=st.slider("Attach revenue per genuine customer",50,400,int(st.session_state.attach),25)
    with c3: mins=st.slider("Manual review minutes saved / transaction",1,15,int(st.session_state.mins),1)
    st.session_state.capture=cap; st.session_state.attach=attach; st.session_state.mins=mins
    r=analyze(st.session_state.raw,cap,attach,mins); st.session_state.report=r; s=r["summary"]
    cols=st.columns(4)
    for c,d in zip(cols,[("Protected inventory",money(s["protected_inventory"]),"Inventory likely preserved"),("Attach protected",money(s["revenue_protected"]),"Accessory/service value"),("Visits protected",s["customer_visits_protected"],"Genuine customer opportunities"),("Time saved",f'{s["review_minutes_saved"]} min',"Per review cycle")]):
        with c: kpi(*d)
    st.markdown('<div class="panel"><div class="ptitle">Executive value bridge</div>',unsafe_allow_html=True)
    for label,val in [("Inventory exposure identified",money(s["inventory_exposure"])),("Protection assumption",f"{int(cap*100)}%"),("Protected inventory opportunity",money(s["protected_inventory"])),("Attach revenue preserved",money(s["revenue_protected"]))]: value_line(label,val)
    st.markdown('</div>',unsafe_allow_html=True)

def manager_review(r):
    hero("Manager review", "Upload a CSV or use the demo. Sentinel creates a clear, explainable queue for daily retail operations.", "Daily Workflow")
    col1,col2=st.columns([1,1])
    with col1:
        if st.button("Load executive demo",use_container_width=True): st.session_state.raw=demo_data(); st.session_state.source="Executive demo dataset"; st.rerun()
    with col2:
        up=st.file_uploader("Upload transaction CSV",type=["csv"])
        if up is not None:
            st.session_state.raw=pd.read_csv(up); st.session_state.source=up.name; st.rerun()
    r=st.session_state.report; view=r["flagged"][["transaction_id","timestamp","store","product","quantity","total_value","risk_score","risk_tier","payment_signal","reasons"]].copy()
    view["timestamp"]=view["timestamp"].astype(str); view["total_value"]=view["total_value"].map(money)
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.download_button("Download prioritized CSV",view.to_csv(index=False),"sentinel_priority_review.csv","text/csv",use_container_width=True)

def network(r):
    hero("Store network", "The core insight: one store sees a sale. The network sees the pattern.", "Network View")
    a,b=st.columns([1.1,1])
    with a: st.plotly_chart(store_chart(r),use_container_width=True)
    with b:
        show=r["signal"].copy()
        if len(show): show["exposure"]=show["exposure"].map(money)
        st.dataframe(show,use_container_width=True,hide_index=True)

def executive_brief(r):
    hero("Executive brief", "A one-click summary for leadership, hiring panels, or project submission.", "Downloadable Output")
    txt=brief_text(r)
    st.text_area("Brief preview",txt,height=420)
    st.download_button("Download Executive Brief",txt,"sentinel_executive_brief.txt","text/plain",use_container_width=True)

def responsible_ai(r):
    hero("Responsible AI", "Sentinel is a decision-support tool, not an accusation engine.", "Governance")
    st.markdown('<div class="warn">Sentinel flags behavioral risk indicators only. It does not prove fraud, deny customers, or replace manager judgment.</div>',unsafe_allow_html=True)
    st.markdown("## Guardrails")
    c1,c2,c3=st.columns(3)
    for c,t,cp in [(c1,"Human review","Every flagged transaction requires manager review before action."),(c2,"Fair policy","Rules must apply consistently to all customers and locations."),(c3,"Explainability","Every score is tied to visible signals: product, quantity, payment, store, and timing.")]:
        with c: st.markdown(f'<div class="micro"><div class="microtitle">{t}</div><div class="microcopy">{cp}</div></div>',unsafe_allow_html=True)

ensure()
r=st.session_state.report
with st.sidebar:
    st.markdown("## 🛡️ Sentinel")
    st.caption("Retail Leakage Control Tower")
    page=st.radio("Navigate",["Command Center","Today’s Decision","Scenario Calculator","Store Network","Manager Review","Executive Brief","Responsible AI"],label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Answers in 10 seconds**")
    st.caption("What is happening? Where? What should we do? What value is protected?")
    st.markdown("---")
    st.caption(f"Source: {st.session_state.source}")

if page=="Command Center": command_center(r)
elif page=="Today’s Decision": todays_decision(r)
elif page=="Scenario Calculator": scenario(r)
elif page=="Store Network": network(r)
elif page=="Manager Review": manager_review(r)
elif page=="Executive Brief": executive_brief(r)
else: responsible_ai(r)
