#!/usr/bin/env python3
"""Lecture IV addendum: Saving for the Machines (Fernandez-Villaverde 2026).

Figures 13,14,16,17 replot only author-reported discrete points from the
1 November 2026 84-page manuscript. Figure 15 is an independent analytic
example of immediate full automation (NOT the author's 2025-2045 transition).

Requires numpy, pandas, matplotlib. Run: python saving_for_machines_exercises.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / 'figures'
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'figure.figsize':(8.5,5.5), 'font.size':10,
                     'axes.spines.top':False, 'axes.spines.right':False,
                     'savefig.dpi':160})

# 1 November 2026 manuscript Table 4, Panel A: full automation by 2045,
# constant machine productivity; 2025 is the announcement of the path.
reported = pd.DataFrame({
    'sigma':[1., .5, .2],
    'growth_2045_opt_pct':[21.9,14.9,11.7],
    'growth_2045_fixed_pct':[6.5,3.5,2.2],
    'saving_2025_impact_pct':[15.4,24.2,29.7],
    'saving_2045_opt_pct':[53.8,55.2,56.1],
    'saving_2065_opt_pct':[54.0,55.5,56.6],
    'ten_year_yield_2025_pct':[13.6,10.7,9.3],
    'min_wage_relative_trend':[.46,.34,.28],
})
reported.to_csv(FIG/'saving_machines_reported_table4_panel_a.csv', index=False)

# Table 6: different capital supply and household ownership regimes,
# sigma=0.2, full automation, constant machines. DO NOT infer causal effects.
heterogeneous = pd.DataFrame({
    'scenario':['Representative','Fixed saving','Dissipation shocks',
                'Perpetual youth','Hand-to-mouth (30%)'],
    'growth_2045_pct':[11.7,2.2,8.2,10.4,11.6],
    'growth_limit_pct':[11.6,1.6,7.7,10.3,11.6],
    'saving_2045_pct':[56.1,22.9,44.2,51.8,55.6],
})
heterogeneous.to_csv(FIG/'saving_machines_reported_table6_sigma02.csv',index=False)


def save(n, note):
    fig=plt.gcf()
    fig.text(.013,.012,note,fontsize=8,color='#555555')
    fig.tight_layout(rect=(0,.055,1,1))
    fig.savefig(FIG/f'figure_{n:02d}.png')
    plt.close(fig)


def static_task_allocation(K,L,alpha,psi_l,psi_k,sigma):
    """FV (2026), Props. 1-2, common comparative advantage.

    Correctly distinguishes automatable alpha from actually capital-used beta.
    Uses aggregation formulas; interior capital and labor; alpha in (0,1].
    """
    assert K>0 and L>0 and 0<alpha<=1 and psi_l>0 and psi_k>0 and sigma>0
    beta=min(alpha, psi_k*K/(psi_k*K+psi_l*L))
    if alpha == 1 or beta < alpha - 1e-12:
        Y=psi_k*K+psi_l*L
        R=psi_k; w=psi_l
    elif abs(sigma-1) < 1e-10:
        Y=(psi_k*K/beta)**beta*(psi_l*L/(1-beta))**(1-beta)
        R=beta*Y/K; w=(1-beta)*Y/L
    else:
        rho=(sigma-1)/sigma
        term_k=beta**(1/sigma)*(psi_k*K)**rho
        term_l=(1-beta)**(1/sigma)*(psi_l*L)**rho
        Y=(term_k+term_l)**(1/rho)
        sK=term_k/(term_k+term_l)
        R=sK*Y/K; w=(1-sK)*Y/L
    sK=R*K/Y; sL=w*L/Y
    assert abs(sK+sL-1)<2e-11
    assert abs(Y-R*K-w*L)<1e-10*Y
    if beta < alpha-1e-10:
        assert abs(R-psi_k)<1e-10 and abs(w-psi_l)<1e-10
    else:
        assert R/psi_k <= w/psi_l*(1+1e-9)
    return dict(Y=Y,R=R,w=w,sK=sK,sL=sL,beta=beta)


def full_automation_closed_form(t, K0, L, psi_l0, psi_k, gl, delta, gamma, discount, fixed_s):
    """Exact immediate full-automation AK economy; not FV's gradual transition.

    Y = psi_k*K + psi_l0*L*exp(gl*t); consumption and K solve Euler and
    resource identities exactly for optimizer; fixed rate solves linear ODE.
    Requires r>gC>gl, making present-value labor income finite.
    """
    t=np.asarray(t,dtype=float)
    r=psi_k-delta
    gC=(r-discount)/gamma
    assert 0<fixed_s<1 and r>gC>gl>=0
    human_wealth=psi_l0*L/(r-gl)
    wealth=K0+human_wealth
    C0=(r-gC)*wealth
    K_opt=wealth*np.exp(gC*t)-human_wealth*np.exp(gl*t)
    C_opt=C0*np.exp(gC*t)
    Y_opt=psi_k*K_opt+psi_l0*L*np.exp(gl*t)
    Kdot_opt=wealth*gC*np.exp(gC*t)-human_wealth*gl*np.exp(gl*t)
    saved_opt=Y_opt-C_opt
    assert np.max(np.abs(Kdot_opt-(saved_opt-delta*K_opt)))<1e-9
    assert np.max(np.abs(C_opt/C0-np.exp(gC*t)))<1e-9
    assert np.all(K_opt>0) and np.all(C_opt>0)
    s_opt=saved_opt/Y_opt
    assert np.all(s_opt>0) and np.all(s_opt<1)
    assert np.max(np.abs(s_opt-((Kdot_opt+delta*K_opt)/Y_opt)))<1e-10
    k_rate=fixed_s*psi_k-delta
    if abs(k_rate-gl)<1e-10:
        K_fixed=np.exp(gl*t)*(K0+fixed_s*psi_l0*L*t)
        Kdot_fixed=np.exp(gl*t)*(gl*(K0+fixed_s*psi_l0*L*t)+fixed_s*psi_l0*L)
    else:
        K_fixed=K0*np.exp(k_rate*t)+fixed_s*psi_l0*L*(np.exp(gl*t)-np.exp(k_rate*t))/(gl-k_rate)
        Kdot_fixed=k_rate*K_fixed+fixed_s*psi_l0*L*np.exp(gl*t)
    Y_fixed=psi_k*K_fixed+psi_l0*L*np.exp(gl*t)
    C_fixed=(1-fixed_s)*Y_fixed
    assert np.max(np.abs(Kdot_fixed-(Y_fixed-C_fixed-delta*K_fixed)))<1e-9
    assert np.all(K_fixed>0) and np.all(C_fixed>0)
    assert np.max(np.abs((Y_fixed-C_fixed)/Y_fixed-fixed_s))<1e-12
    assert np.max(np.abs(psi_k*K_opt/Y_opt+sL_opt(K_opt,Y_opt,L,psi_l0,gl,t)-1))<1e-11
    return dict(t=t,K_opt=K_opt,C_opt=C_opt,Y_opt=Y_opt,s_opt=s_opt,
                K_fixed=K_fixed,C_fixed=C_fixed,Y_fixed=Y_fixed,
                gC=gC,gfixed_limit=max(gl,k_rate),r=r,human_wealth=human_wealth)


def sL_opt(K,Y,L,psi_l0,gl,t):
    return psi_l0*L*np.exp(gl*t)/Y


def make_figures():
    x=np.arange(len(reported))
    labels=[f'{v:g}' for v in reported.sigma]
    width=.35
    plt.figure()
    plt.bar(x-width/2,reported.growth_2045_opt_pct,width,label='Optimal saving')
    plt.bar(x+width/2,reported.growth_2045_fixed_pct,width,label='Fixed saving (23%)')
    plt.xticks(x,labels);plt.xlabel('Task elasticity of substitution (sigma)')
    plt.ylabel('GDP growth in 2045 (%)');plt.title('Same automation path, different capital supply')
    plt.legend()
    save(13,'Source: Fernandez-Villaverde (2026), Nov 1 manuscript Table 4A; author-reported points, NOT re-estimation')

    plt.figure()
    for _, row in reported.iterrows():
        plt.plot([2025,2045],[row.saving_2025_impact_pct,row.saving_2045_opt_pct],marker='o',
                 label=f'sigma = {row.sigma:g}')
    plt.axhline(23,ls='--',color='.5',label='Saving fixed at 23%')
    plt.xlabel('Year');plt.xticks([2025,2045]);plt.ylabel('Gross saving / GDP (%)')
    plt.title('Optimal saving response to an announced 2025-2045 automation path')
    plt.legend(loc='lower right')
    save(14,'Source: Fernandez-Villaverde (2026), Nov 1 manuscript Table 4A; straight segments just connect reported endpoints')

    # Immediate full automation at t=0 is illustrative. NO claim of reproducing
    # the published 2025-2045 path, and no imported series or invented data.
    t=np.linspace(0,30,301)
    res=full_automation_closed_form(t,K0=3,L=1,psi_l0=.187,psi_k=.311,
                 gl=.0162,delta=.06,gamma=2,discount=.019,fixed_s=.23)
    pd.DataFrame({'years_since_immediate_full_automation':t,
                  'Y_opt':res['Y_opt'],'Y_fixed':res['Y_fixed'],
                  'K_opt':res['K_opt'],'K_fixed':res['K_fixed'],
                  'saving_opt':res['s_opt']}).to_csv(FIG/'saving_machines_immediate_ak_analytic_example.csv',index=False)
    plt.figure()
    plt.plot(2025+t,res['Y_opt']/res['Y_opt'][0],label='Optimizing household')
    plt.plot(2025+t,res['Y_fixed']/res['Y_fixed'][0],label='Fixed saving at 23%')
    plt.yscale('log');plt.xlabel('Year');plt.ylabel('Output / initial output (log scale)')
    plt.title('Illustrative immediate full-automation AK transition')
    plt.legend()
    save(15,'Exact closed-form calculation with full automation already at 2025; NOT the source paper transition')

    plt.figure(figsize=(9,5.2))
    yy=np.arange(len(heterogeneous))
    plt.barh(yy,heterogeneous.growth_2045_pct)
    plt.yticks(yy,heterogeneous.scenario)
    plt.gca().invert_yaxis()
    plt.xlabel('GDP growth in 2045 (%)');plt.title('Household capital supply alters growth')
    for i,val in enumerate(heterogeneous.growth_2045_pct):
        plt.text(val+.12,i,f'{val:.1f}%',va='center',fontsize=9)
    plt.xlim(0,13.2)
    save(16,'Source: Fernandez-Villaverde (2026), Nov 1 manuscript Table 6; sigma = 0.2, author-reported points')

    plt.figure()
    plt.bar(x,reported.ten_year_yield_2025_pct,width=.55,label='10-year real yield immediately after news')
    plt.axhline(5.1,ls='--',color='.5',label='Prior flat real yield (5.1%)')
    plt.xticks(x,labels);plt.xlabel('Task elasticity of substitution (sigma)')
    plt.ylabel('10-year real zero-coupon yield (%)')
    plt.title('Expected future machine returns reprice long bonds today')
    plt.legend()
    save(17,'Source: Fernandez-Villaverde (2026), Nov 1 manuscript Table 4A; calibrated announcement scenario')
    return res


def test_model():
    count=0
    for sigma in (1., .5, .2):
        for alpha in (.2,.45,.85,1.):
            for K in (.005,.03,.2,.9,3.,20.,200.):
                eq=static_task_allocation(K,1.,alpha,.187,.311,sigma)
                count+=1
                # factor expenditure equals value added in each regime
                assert abs(eq['sK']+eq['sL']-1)<2e-11
                if alpha<1:
                    Kbar=alpha/(1-alpha)*(.187/.311)
                    if K < Kbar - 1e-11:
                        assert abs(eq['R']-.311)<1e-10
                        assert abs(eq['w']-.187)<1e-10
                    elif K>Kbar+1e-11:
                        assert abs(eq['beta']-alpha)<1e-12
    # Finite-difference verify static GE marginal products away from cost parity.
    for sigma in (1.,.5,.2):
        for K in (.01,1.,10.):
            for alpha in (.3,.7):
                L=1.0
                eq=static_task_allocation(K,L,alpha,.187,.311,sigma)
                eps=1e-6
                dk=(static_task_allocation(K+eps,L,alpha,.187,.311,sigma)['Y']-
                    static_task_allocation(K-eps,L,alpha,.187,.311,sigma)['Y'])/(2*eps)
                dl=(static_task_allocation(K,L+eps,alpha,.187,.311,sigma)['Y']-
                    static_task_allocation(K,L-eps,alpha,.187,.311,sigma)['Y'])/(2*eps)
                assert abs(dk-eq['R'])<2e-6,('capital FOC',sigma,K,alpha,dk,eq['R'])
                assert abs(dl-eq['w'])<2e-6,('labor FOC',sigma,K,alpha,dl,eq['w'])
    # Check the calibrated long-run threshold and saving/AK growth formula.
    sigma02_psi_k=.311
    threshold=(.06+.0162)/sigma02_psi_k
    opt_growth=(sigma02_psi_k-.06-.019)/2
    opt_saving=(opt_growth+.06)/sigma02_psi_k
    assert abs(threshold-.2450)<.0001
    assert abs(opt_growth-.116)<1e-12
    assert abs(opt_saving-.5659)<.001
    assert .23<threshold
    res=make_figures()
    assert abs(res['gC']-.116)<1e-12
    assert abs(res['gfixed_limit']-.0162)<1e-12
    report=(f'PASS static cost parity / capital cheaper: {count} grid points\n'
            f'PASS static factor shares / zero-profit and finite-difference marginal product identities\n'
            f'PASS analytical full-automation dynamic Euler / goods resource / saving identity\n'
            f'PASS long-run fixed-saving threshold: {threshold:.6f}; calibrated optimizer growth: {opt_growth:.6f}\n'
            f'PASS figure generation: 13, 14, 15, 16, 17\n'
            f'NOTE Figure 15 is an immediate-AK mathematical exercise, not a reproduction of 2025-2045 paper transition.\n')
    (ROOT/'saving_for_machines_test_output.txt').write_text(report)
    print(report)


if __name__=='__main__':
    test_model()
