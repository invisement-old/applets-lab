# Asset pricing and stock valuation

## Model
We can not use net profit since it varies a lot and goes to negative easily for given industries. So we use gross profit.

discount rate * value = (1+n*g)R * GrossMargin * "Industry Net / Gross"
    fit last year => unknown
    - method 1: value(t)  and fundamentals (R, g, gross) of t-1
    - method 2: value(t-1) and fundamentals of t-1
    then apply to current fundamentals to get value

discount rate * value =R * (GorssMargin + conventer*g)*"industry Net/Gross"

Both means linear formula
## Formula
d*V/R ~ m + g 

### Method 1
fit linear line for each industry
- assumption: for each industry NetProfit/GrossProfit is fixed (parameter) 
- We have 3500 stocks and 70 industry which means 50 stock per industry:
- x=number of features = ln(50) - 1 = 3
- ideal number of features are 2 or 3: not more

### Method 2
fit general line for all, then cluster base on error (deviation from line) and then fit in each cluster 
    - assumption: for each cluster NetProfit/GrossProfit is fixed (parameter) 
    - number of features = ln(3500) - 1 = 7
    - 5 clusters (+2standard deviation, +1sd, sd, -1sd, -2sd)
    - size of cluster = .025 * 3500 = 70 (probability of bigger than 2 sd = 2.5%)
    - number of in-cluster features = ln(70) - 1 = 3

### 

