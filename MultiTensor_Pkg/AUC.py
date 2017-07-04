import numpy as np


def calculate_AUC(M,Pos,Neg):
    # M= # SORTED (from small to big) List of 2-tuple, each entry is M[n]=(mu_ij,A_ij)      
    # Pos= # positive entries (graph edges)         
    # Neg= # negative entries (graph non-edges) 
    y=0.;bad=0.;
    for m,a,n in M:
        if(a>=1.):
            y+=1;
        else:
            bad+=y;      
    AUC=1.-(bad/(Pos*Neg));     
    return AUC;


def calculate_AUC_weighted(M,max_w):
    """"
    AUC for weighted entries A_ij. Ideally, if an observed edge has A_ij=4, it will have a bigger M entry than an observed edge with A_ij<4
    - M= # SORTED (from small to big) List of 2-tuple, each entry is M[n]=(mu_ij,A_ij)    
    - m_k= multiplicity of A_ij=k entries      
    - max_w is the maximum edge weigth, needed to order the y[k]
    """

    bad=0.
    y=np.zeros(max_w+1)

    for m, a in M:
        y[a] += 1   # number of entries with A_ij=a already encountered
        for q in range(a+1,max_w+1):
            # number of entries with A_ij>a already encountered --> penalty
            bad += y[q]
    # calculate denominator --> normalization    
    Z = 0
    for k in range(max_w+1):
        m = 0.
        for q in range(k+1, max_w+1):
            m += y[q]
        Z += m*y[k]

    AUC = 1.-(bad/float(Z))

    return AUC;