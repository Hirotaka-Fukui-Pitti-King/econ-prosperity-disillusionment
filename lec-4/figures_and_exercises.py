#!/usr/bin/env python3
"""Lecture IV: reproducible illustrative diagrams and calibrated source-reported points.
Run: python figures_and_exercises.py
All synthetic figures are labeled. No confidential datasets are imputed.
Dependencies: numpy scipy matplotlib pandas.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import brentq

OUT=Path(__file__).resolve().parent/'figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'figure.figsize':(8.3,5.2),'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160})

def save(n, note='Illustrative simulation; not an empirical replication'):
    fig=plt.gcf(); fig.text(0.01,0.012,note,fontsize=8,color='#666666')
    fig.tight_layout(rect=[0,.045,1,1]); fig.savefig(OUT/f'figure_{n:02d}.png'); plt.close(fig)

def ces(H,L,AH,AL,sigma):
    assert H>0 and L>0 and AH>0 and AL>0 and sigma>0 and abs(sigma-1)>1e-6
    rho=(sigma-1)/sigma
    y=((AH*H)**rho+(AL*L)**rho)**(1/rho)
    wh=y**(1-rho)*AH**rho*H**(rho-1)
    wl=y**(1-rho)*AL**rho*L**(rho-1)
    assert abs((wh*H+wl*L)/y-1)<1e-10
    return y,wh,wl

def task_technology(n=400,auto=0.20,new=0):
    """Independent task input unit productivity; automated technology available for low-index tasks.
    New tasks: labor-only, normalized in the Cobb-Douglas task aggregator.
    """
    x=(np.arange(n)+.5)/n
    labor_prod=np.exp(.14*np.sin(2*np.pi*x))
    capital_prod=np.where(x<auto, np.exp(.11*np.cos(2*np.pi*x)),0.)
    if new:
        xx=1+(np.arange(new)+.5)/n
        x=np.concatenate([x,xx]); labor_prod=np.concatenate([labor_prod,np.full(new,1.15)]); capital_prod=np.concatenate([capital_prod,np.zeros(new)])
    return x,labor_prod,capital_prod

def task_ge(labor_prod,capital_prod,L=1.,r=0.32):
    """One-sector competitive GE, Cobb-Douglas across tasks, labor supply L;
    final-good-produced capital services available elastically at cost r.
    Output Y=wL/labor_share, capital services K=(Y-wL)/r, C=Y-rK=wL.
    Numeraire P=geometric mean of unit task costs=1, so zero profits are exact.
    """
    assert np.all(labor_prod>0) and np.any(capital_prod==0) and L>0 and r>0
    def unitcost(w):
        lc=w/labor_prod
        kc=np.divide(r,capital_prod,out=np.full_like(capital_prod,np.inf),where=capital_prod>0)
        return np.minimum(lc,kc)
    def logP(logw): return np.log(unitcost(np.exp(logw))).mean()
    a,b=-18.,18.
    assert logP(a)<0<logP(b), (logP(a),logP(b))
    w=float(np.exp(brentq(logP,a,b,xtol=1e-13)))
    lc=w/labor_prod
    kc=np.divide(r,capital_prod,out=np.full_like(capital_prod,np.inf),where=capital_prod>0)
    labor=lc<=kc
    sL=float(labor.mean()); assert 0<sL<=1
    Y=w*L/sL; K=(Y-w*L)/r; C=Y-r*K
    result=dict(w=w,Y=Y,K=K,C=C,sL=sL,owner=labor)
    assert abs(logP(np.log(w)))<1e-10
    assert abs(sL*Y-w*L)<1e-9
    assert abs((1-sL)*Y-r*K)<1e-9
    assert abs(Y-C-r*K)<1e-9
    assert abs(Y-w*L-r*K)<1e-9
    return result


def task_ge_fixed_capital(labor_prod,capital_prod,L,K):
    """Competitive one-sector GE with pre-existing durable capital K (not an input purchase).
    Fixed supplies (L,K), Cobb-Douglas task aggregator. Unit expenditure by task is equal.
    At a tie, split one task's expenditure between factors for exact clearing.
    Resources: Y=C for zero depreciation/no investment, Y=wL+rK.
    """
    assert L>0 and K>0 and np.any(capital_prod>0) and np.any(capital_prod==0)
    n=len(labor_prod)
    threshold=np.divide(labor_prod,capital_prod,out=np.full(n,np.inf),where=capital_prod>0)
    def residual(u):
        # choose labor when its task cost is lower
        return np.mean(u<threshold)-u*L/(u*L+K)
    low=1e-12; high=1e12
    assert residual(low)>0 and residual(high)<0
    for _ in range(200):
        mid=(low+high)/2
        if residual(mid)>0: low=mid
        else: high=mid
    u=(low+high)/2
    finite_thresholds=threshold[np.isfinite(threshold)]
    nearest=finite_thresholds[np.argmin(np.abs(finite_thresholds-u))]
    if abs(u-nearest)<1e-8:
        u=float(nearest)
    # Determine whether the exact price equality involves a split at a marginal task.
    ties=np.isclose(u,threshold,atol=2e-8,rtol=0)
    below=(u<threshold)&(~ties)
    target=u*L/(u*L+K)
    shares=below.astype(float)
    if np.any(ties):
        fill=(target*n-shares.sum())/ties.sum()
        assert -1e-7<=fill<=1+1e-7,(fill,target)
        shares[ties]=np.clip(fill,0.,1.)
    assert abs(shares.mean()-target)<1e-8
    unit_cost=np.minimum(u/labor_prod,np.divide(1.,capital_prod,out=np.full(n,np.inf),where=capital_prod>0))
    r=np.exp(-np.log(unit_cost).mean());w=u*r
    Y=w*L+r*K;C=Y
    assert abs(np.log(r*unit_cost).mean())<1e-9
    assert abs(shares.mean()*Y-w*L)<1e-7
    assert abs((1-shares.mean())*Y-r*K)<1e-7
    return dict(w=w,r=r,Y=Y,K=K,C=C,sL=shares.mean())

def rent_adoption_example(multipliers,w=1.,social_wage=1.,capital_cost=1.25):
    """This is the unit-task adoption example (not the 2026 structural estimation)."""
    multipliers=np.asarray(multipliers,dtype=float)
    private=w*multipliers>=capital_cost
    social=social_wage>=capital_cost
    lost_resources=np.where(private & (not social),capital_cost-social_wage,0.)
    return pd.DataFrame({'rent_multiplier':multipliers,'private_automates':private,
                         'efficient_automates':np.full(len(multipliers),social),
                         'real_resource_loss_per_unit_task':lost_resources})

def nash_wage(v,b,theta):
    assert v>b and 0<=theta<=1
    w=b+theta*(v-b)
    assert b-1e-12<=w<=v+1e-12
    return w

# Figure 1: schematic trend; DO NOT treat as official time series
x=np.arange(1980,2021)
prod=100*np.exp(.023*(x-1980)); avg=100*np.exp(.0175*(x-1980)); med=100*np.exp(.010*(x-1980))
plt.figure(); plt.plot(x,prod,label='Productivity');plt.plot(x,avg,label='Mean compensation');plt.plot(x,med,label='Median compensation');plt.legend();plt.ylabel('Index (1980=100)');plt.xlabel('Year');plt.title('');save(1)

# Figure 2: CES skill premium
plt.figure(); supplies=np.linspace(.4,2.2,200)
for sig in [1.2,1.8,3.0]:
    premium=np.array([ces(h,1,1.5,1.,sig)[1]/ces(h,1,1.5,1.,sig)[2] for h in supplies])
    plt.plot(supplies,premium,label=f'Elasticity {sig}')
plt.xlabel('Relative high-skill supply H/L');plt.ylabel('Skill premium wH/wL');plt.title('');plt.legend();save(2)

# Baseline and after adoption; all task data are generated, not observed
x,la,ka=task_technology(auto=.20); b=task_ge(la,ka)
x1,la1,ka1=task_technology(auto=.42); a=task_ge(la1,ka1)
x2,la2,ka2=task_technology(auto=.42,new=120); n=task_ge(la2,ka2)

plt.figure(); plt.scatter(x,b['owner'].astype(int),s=10);plt.yticks([0,1],['Capital','Labor']);plt.ylim(-.3,1.3);plt.xlabel('Task index');plt.ylabel('Assigned factor');plt.title('3. Equilibrium task allocation');save(3)

plt.figure();plt.fill_between(x,0,1,where=~b['owner'],alpha=.4,label='Capital: baseline');plt.fill_between(x1,0,.65,where=~a['owner'],alpha=.45,label='Capital: automated');plt.xlabel('Task index');plt.yticks([]);plt.title('4. Automation expands capital-performed tasks');plt.legend();save(4)

plt.figure();lab_shares=[b['sL'],a['sL'],n['sL']];plt.bar(['Baseline','Automation','Automation + new tasks'],lab_shares)
plt.ylabel('Labor share');plt.ylim(0,1);plt.title('5. Displacement and reinstatement');save(5)

# Figure 6: deliberately synthetic negative relationship; no paper estimates recreated
rng=np.random.default_rng(183)
exposure=rng.uniform(0,.32,180);wagechange=.14-.65*exposure+rng.normal(0,.065,len(exposure))
plt.figure();plt.scatter(exposure,wagechange,alpha=.55,s=19);plt.plot([0,.32],[.14,.14-.65*.32],color='black',label='Illustrative slope, not estimated')
plt.xlabel('Direct task displacement');plt.ylabel('Change in log relative wage');plt.title('6. Automation exposure and relative wages');plt.legend();save(6,'Synthetic scatter: NOT Figure 6 or coefficients in Acemoglu–Restrepo (2022)')

# Figure 7: adoption gain by rent wedge
rents=np.linspace(1,2,150);laborcost=rents;capitalcost=np.full_like(rents,1.3)
plt.figure();plt.plot(rents,laborcost,label='Private labor cost: w × rent wedge');plt.plot(rents,capitalcost,label='Capital cost');plt.axvline(1.3,color='black',ls='--',alpha=.5);plt.xlabel('Rent multiplier μ');plt.ylabel('Unit task cost');plt.title('7. High-rent tasks and private adoption');plt.legend();save(7)

# Figure 8: threshold gap and misallocation
plt.figure();mu=np.linspace(1,1.8,170);plt.plot(mu,mu,label='Private cost of labor');plt.plot(mu,np.ones_like(mu),label='Opportunity cost of labor');plt.axhline(1.25,color='black',ls='--',label='Capital resource cost = 1.25');plt.fill_between(mu,1,1.25,where=mu>1.25,alpha=.18,label='Inefficient adoption region');plt.ylim(.85,1.85);plt.xlabel('Rent multiplier');plt.ylabel('Task unit cost');plt.title('8. Private versus efficient automation');plt.legend();save(8)

# Figure 9: exact Shapley decomposition, continuing firms
v0=np.array([.25,.35,.40]);v1=np.array([.20,.30,.50]);s0=np.array([.75,.50,.25]);s1=np.array([.72,.49,.22])
S0=v0@s0;S1=v1@s1
within=.5*(v0+v1)@(s1-s0);between=.5*(s0+s1)@(v1-v0)
assert abs(S1-S0-within-between)<1e-12
plt.figure();plt.bar(['Within firms','Between firms','Total'],[within,between,S1-S0]);plt.axhline(0,color='black',lw=.7);plt.ylabel('Change in aggregate labor share');plt.title('9. Exact labor-share decomposition');save(9)

# Figure 10: published coefficients, not replicated from confidential data
plt.figure();plt.bar(['Median-paid workers','Top-paid workers'],[.04,.10]);plt.ylabel('Elasticity of pay with respect to firm productivity');plt.ylim(0,.12);plt.title('10. Within-firm pay-productivity elasticities');save(10,'Published point estimates: Wallskog et al. (2026) abstract; not independently re-estimated')

# Figure 11: comparability caution via textual estimate types
fig,ax=plt.subplots(figsize=(9,4.5));ax.axis('off');texts=[
 ('United States (2020)','Local wages: -0.42% per additional robot / 1,000 workers'),
 ('Germany (2021)','Manufacturing displacement offset by service job growth'),
 ('Japan (2024)','Robot price declines increased employment in adopting industries')]
for i,(country,claim) in enumerate(texts):
    ax.text(.02,.85-i*.29,country,transform=ax.transAxes,weight='bold',fontsize=12)
    ax.text(.02,.75-i*.29,claim,transform=ax.transAxes,fontsize=10)
ax.set_title('11. Robots and employment: different country estimands',fontsize=12);save(11,'Qualitative summary of separate original estimates; NOT a common-scale meta-analysis')

# Figure 12: hypothesis-specific qualitative predictions
pred=pd.DataFrame([
 ['Task displacement','May fall','Typically falls','Routine-task exposure'],
 ['Capital substitution','Ambiguous','Falls if substitution high','Investment-goods prices'],
 ['Superstar reallocation','Ambiguous','Falls with low-share winners','Within / between firms'],
 ['Oligopsony','Below marginal product','Often falls','Labor supply elasticity'],
 ['IPP capitalization','No necessary change','Measured share changes','National accounts']
],columns=['Mechanism','Real wages','Labor share','Discriminating evidence'])
pred['Real wages']=pred['Real wages'].replace({'Below marginal product':'Wage markdown', 'No necessary change':'Unrestricted'})
pred['Labor share']=pred['Labor share'].replace({'Falls with low-share winners':'Falls if low-share firms gain share','Falls if substitution high':'Falls if elasticity > 1'})
fig,ax=plt.subplots(figsize=(12,5.4));ax.axis('off');
from textwrap import fill
wrapped=[[fill(str(val),width=30) for val in row] for row in pred.values]
tbl=ax.table(cellText=wrapped,colLabels=pred.columns,loc='center',cellLoc='left',colLoc='left',colWidths=[.18,.16,.24,.42]);tbl.auto_set_font_size(False);tbl.set_fontsize(8.5);tbl.scale(1,2.7);ax.set_title('12. Competing mechanisms: different predictions');save(12,'Research synthesis; directional statements are conditional, not universal estimates')

# Source-reported estimates captured in a machine-readable table
reported=pd.DataFrame([
 ['Acemoglu & Restrepo 2020','US commuting zones','Wage effect per extra robot / 1000 workers',-.42,'percent','Published abstract'],
 ['Acemoglu & Restrepo 2026','US 1980-2016','Share of increase in between-group inequality explained',52,'percent','QJE published abstract'],
 ['Acemoglu & Restrepo 2026','US 1980-2016','Fraction of automation contribution due to rent dissipation',20,'percent approximately','QJE published abstract'],
 ['Wallskog et al. 2026','US within firm','Median worker pay-productivity elasticity',.04,'elasticity','Economic Journal abstract'],
 ['Wallskog et al. 2026','US within firm','Top worker pay-productivity elasticity',.10,'elasticity','Economic Journal abstract'],
 ['Kline et al. 2019','US patent allowances','Worker share of patent-induced operating surplus',29,'cents per dollar','Author working paper abstract'],
 ['Autor & Kausik 2026','US 1954-2019','Share of real wage growth attributable to declining labor share',16,'percent','MIT working paper abstract'],
],columns=['paper','sample','estimand','value','unit','provenance'])
reported.to_csv(OUT/'source_reported_values.csv',index=False)
summary=pd.DataFrame([
 ['Baseline',b['w'],b['Y'],b['K'],b['C'],b['sL']],
 ['Automation',a['w'],a['Y'],a['K'],a['C'],a['sL']],
 ['Automation+new tasks',n['w'],n['Y'],n['K'],n['C'],n['sL']],
],columns=['scenario','real_wage','gross_output','intermediate_capital_services','net_consumption','labor_share'])
summary.to_csv(OUT/'task_model_equilibria.csv',index=False)
fixed=[]
for label,tech in [('Baseline',(la,ka)),('Automation',(la1,ka1)),('Automation+new tasks',(la2,ka2))]:
    fixed.append(dict(scenario=label,**task_ge_fixed_capital(*tech,L=1.,K=b['K'])))
fixed_df=pd.DataFrame(fixed)
fixed_df.to_csv(OUT/'task_model_fixed_capital_equilibria.csv',index=False)
rent_adoption_example(np.linspace(1,1.8,81)).to_csv(OUT/'rent_adoption_exercise.csv',index=False)
rows=[]
for theta in (.2,.5,.8):
    for outside in (.3,.5,.7):
        wage=nash_wage(1.6,outside,theta)
        rows.append(dict(bargaining_power=theta,outside_option=outside,product_value=1.6,
                         wage=wage,rent=wage-outside,automate_if_capital_cost_1_2_less_than_wage=(1.2<wage)))
pd.DataFrame(rows).to_csv(OUT/'nash_bargaining_exercise.csv',index=False)

print('Elastic intermediate-capital GE:');print(summary.to_string(index=False));print('Fixed durable-capital GE:');print(fixed_df.to_string(index=False))
print(f'Labor share decomposes: ΔS={S1-S0:.12f}; within={within:.12f}; between={between:.12f}')
print('Created',len(list(OUT.glob('figure_*.png'))),'figures in',OUT)
