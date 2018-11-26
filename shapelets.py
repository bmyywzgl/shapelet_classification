import numpy as np
import math
from operator import itemgetter

def generate_shapelets(light_curve, minlen, maxlen, time_res=1.):
    """Create a list of all possible subsegments from light_curve, which is a 2D array, where [0,:] are the time values in seconds, and [1,:] are the count rate values. minlen and maxlen are the lower and upper limits of subsegment length in the unit of seconds. Output is a list of 1D arrays.The shortest shapelet will be an array of length minlen+1 etc. time_res is the time interval between two data points in seconds, so that for time_res=0.5 and minlen=100, the smallest produced shapelet would be an array of length (100/0.5)+1. Thus time_res should be set to a value that produces an integer.
    """
    pool=[]
    lc = light_curve
    minlen=int(minlen/time_res); maxlen=int(maxlen/time_res)
    for l in range(minlen,maxlen+1):
        end=l+1; start=0
        while end<=len(lc[0]):
            sh=lc[1,start:end]
            inter=(lc[0,end-1]-lc[0,start])
            end+=1; start+=1
            if inter/time_res==float(l):
                pool.append(sh)
    return pool

def information_gain(distances, set_entropy, split_point):
    """Calculate the information gain from splitting the dichotomous set of time-series objects into subsets below and above the split_point, depending on their distances to the tested shapelet. "distances" is a list of tuples, where each tuple corresponds to a time-series object, and distances[i][0] is the id number of the ith object, distances[i][1] is the minimal distance between the shapelet and the object, distances[i][2] is equal to 1 if the object belongs to the tested object class, or to 0 otherwise (other_class objects). Information gain is dependent on the entropy of the entire set and the split set, where entropy is I(set)=-Alog2(A)-Blog2(B) (A=proportion of object in the set that belong to the class, B=proportion of other objects). Information gain is then I(set)-
    """
    if split_point !=0 and split_point !=np.inf:
        above=[lc for lc in distances if lc[1]>=split_point]
        above_belong=sum([lc[2] for lc in above])
        below=[lc for lc in distances if lc[1]<split_point]
        below_belong=sum([lc[2] for lc in below])
        prop_above_belong=above_belong/len(above)
        prop_below_belong=below_belong/len(below)
        if prop_above_belong==1. or prop_above_belong==0.:
            above_entropy=0
        else:
            above_entropy = -(prop_above_belong)*math.log2(prop_above_belong)-(1-prop_above_belong)*math.log2(1-prop_above_belong)
        if prop_below_belong==1. or prop_below_belong==0.:
            below_entropy =0
        else:
            below_entropy = -(prop_below_belong)*math.log2(prop_below_belong)-(1-prop_below_belong)*math.log2(1-prop_below_belong)
        return set_entropy-(len(above)/(len(above)+len(below)))*(above_entropy)-(len(below)/(len(above)+len(below)))*(below_entropy)
    else:
        return "Invalid split point (0 or infinity)."

def distance_calculation(n_lc, lc, shapelet, time_res, belong_class):
    """
    """
    best_dist=np.inf #for "early abandon"
    lc_l = len(lc[0])
    sha_l=len(shapelet)
    for start_p in range(lc_l-sha_l+1):#length difference+1 will give the number of iterations required to shift the moving windown from start to end of the LC (with a difference of one point, two window positions are required etc.)
        end_p=start_p+sha_l-1 #-1 to give the index of the last included point
        if lc[0,end_p]-lc[0,start_p] != (sha_l-1)*time_res:
            continue
        skip=False
        sha_dist=0 #distance between shapelet and LC subsegment
        for i in range(sha_l):
            sha_dist += (lc[1,i+start_p]-shapelet[i])**2
            if sha_dist>=best_dist: 
                skip=True#"early abandon"
                break#break out of the distance calculation and skip the position of the moving window
        if skip ==False:
            best_dist=sha_dist
    if n_lc in belong_class:
        class_assign=1
    else:
        class_assign=0
    return (n_lc, best_dist, class_assign)
    
def best_split_point(distances, set_entropy):
    """
    """
    distances.sort(key=itemgetter(1))
    best_gain_split=0
    best_split=0
    for distance in range(len(distances)-1):
        split_point=(distances[distance][1] + distances[distance+1][1])/2
        gain=information_gain(distances, set_entropy, split_point)
        if isinstance(gain, str) == True:
            continue
        if gain>best_gain_split:
            best_gain_split=gain
            best_split=split_point
    return best_split

def entropy_pruning(best_gain, distances, best_split, belong_class_count, other_class_count, set_entropy):
    """
    """
    calc_belong=sum([lc[2] for lc in distances])
    calc_other=len(distances)-calc_belong
    distances_bcs=distances #best case scenario when all the distances are included
    distances_bcs.sort(key=itemgetter(1))
    maxdist=distances_bcs[-1][1]+1
    for add_belong in range(belong_class_count-calc_belong):
        distances_bcs.append((-1,0,1))
    for add_other in range(other_class_count-calc_other):
        distances_bcs.append((-1,maxdist,0))
    gain_bcs=information_gain(distances_bcs, set_entropy, best_split)
    if isinstance(gain_bcs, str) == True:
        return True
    else:
        if gain_bcs<best_gain:
            return True
        else:
            return False

def import_labels(file_name, id_extension):
    """load the classified observation ids and their states (from the file provided by Huppenkothen et al. 2017)
    """
    clean_belloni = open(file_name)
    lines = clean_belloni.readlines()
    states = lines[0].split()
    belloni_clean = {}
    for h,l in zip(states, lines[1:]):
        belloni_clean[h] = l.split()
        #state: obsID1, obsID2...
    ob_state = {}
    for state, obs in belloni_clean.items():
        if state == "chi1" or state == "chi2" or state == "chi3" or state == "chi4": state = "chi"
        for ob in obs:
            ob_state[ob+id_extension] = state
    return ob_state
    #xp10408013100_lc.txt classified as chi1 and chi4, xp20402011900_lc.txt as chi2 and chi2
    #del ob_state["10408-01-31-00{}".format(extension)] as long as training and test sets are checked for duplicates when appending, it should be ok to keep
    