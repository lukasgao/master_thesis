use "did_data_5pct.dta", clear 
xtset firm_id year
*gen ln_ev = ln(ev)
*winsor2 ln_ev, cut(2.5 97.5)
gen capex_ratio = exp(capex - size)

winsor2 roa roe tobinq revenue_growth debt_ratio nwc  capex_ratio,cut(2.5, 97.5) 

******************************
***  statistics summary  ***
******************************
est clear
estpost tabstat roa_w gov_score capex_ratio_w revenue_growth_w size debt_ratio_w nwc_w ///
    if inrange(year, 2014, 2019), ///
    statistics(mean sd median min max count) columns(statistics)
	

esttab using "./tables/descriptive.tex", replace ///
    cells("mean(fmt(%9.2f)) sd(fmt(%9.2f)) median(fmt(%9.2f)) min max count") ///
    nonumber nomtitle nonote noobs label booktabs ///
    collabels("Mean" "SD" "Median" "Min" "Max" "N")
*******************************
***  t-test  ***
*******************************
est clear

estpost ttest roa_w gov_score size revenue_growth_w debt_ratio_w nwc_w if inrange(year, 2014, 2019) , by(treated) unequal

esttab using "./tables/ttest.tex", replace ///
	cells("mu_2(fmt(4)) mu_1(fmt(4)) b(fmt(4)) t(fmt(2)) p(fmt(3))") ///
    collabels("Treatment Mean" "Control Mean" "Difference" "T-stat" "P-value") ///
    nonumber noobs label
*******************************
***  parallel trends test ***
*******************************
gen relative_year = year - 2018
tab relative_year, gen(D)
rename D2 pre_4  
rename D3 pre_3  
rename D4 pre_2  
rename D5 pre_1  
rename D6 post_0 
rename D7 post_1 

***********test pre_4 pre_3 pre_2

global event_dummies "pre_4 pre_3 pre_2 post_0 post_1"

foreach var of varlist $event_dummies {
    gen `var'_treated = `var' * treated
}

reghdfe roa_w pre_4_treated pre_3_treated pre_2_treated post_0_treated post_1_treated L.(size gov_score revenue_growth_w debt_ratio_w nwc_w), absorb(firm_id year) vce(cluster firm_id)

coefplot, keep(*_treated) vertical yline(0) ci(95)   ytitle("Coefficient on Treated x Year") xtitle("Years Relative to Trade War Shock") coeflabels(pre_4_treated = "-4" pre_3_treated = "-3" pre_2_treated = "-2" post_0_treated = "0" post_1_treated = "1") graphregion(fcolor(white)) addplot(line @b @at, lcolor(gs1) ) ciopts(lpattern(dash) recast(rcap) msize(medium))  
*******************************
***   regression  ****
*******************************
gen treated_post = post*treated
gen treated_post_gov = treated_post *  l.gov_score
******* main regression  *****
est clear  
reghdfe roa_w  treated_post  if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m1
reghdfe roa_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m2
reghdfe roa_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m3

esttab m1 m2 m3  using "./tables/main_regression.tex", replace ///
	collabels(none) ///
    cells(b(fmt(3) star) t(par fmt(3))) ///
    booktabs  ///
    order(treated_post l.gov_score treated_post_gov l.size l.debt_ratio_w l.nwc_w l.revenue_growth_w l.capex_ratio_w _cons) ///
    stats(N r2_a firmfe yearfe, labels("Observations" "Adjusted R-squared" "Firm FE" "Year FE")) ///
    label star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress ///
    alignment(D{.}{.}{-1})
	
******* robustness test ****** 
est clear
******************************
* 1% 
******************************
use "did_data_1pct.dta", clear 
xtset firm_id year
gen capex_ratio = exp(capex - size)
gen treated_post = post*treated
gen treated_post_gov = treated_post *  l.gov_score
winsor2 roa roe tobinq revenue_growth debt_ratio nwc  capex_ratio,cut(2.5, 97.5) 

reghdfe roa_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m1
reghdfe roa_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m2
******************************
* 10% 
******************************
use "did_data_10pct.dta", clear 
xtset firm_id year
gen capex_ratio = exp(capex - size)
gen treated_post = post*treated
gen treated_post_gov = treated_post *  l.gov_score
winsor2 roa roe tobinq revenue_growth debt_ratio nwc  capex_ratio,cut(2.5, 97.5) 

reghdfe roa_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m3

reghdfe roa_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m4

esttab m1 m2 m3 m4 using "./tables/robustness_regression.tex", replace ///
	collabels(none) ///
    cells(b(fmt(3) star) t(par fmt(3))) ///
    booktabs  ///
    order(treated_post l.gov_score treated_post_gov l.size l.debt_ratio_w l.nwc_w l.revenue_growth_w l.capex_ratio_w _cons) ///
    stats(N r2_a firmfe yearfe, labels("Observations" "Adjusted R-squared" "Firm FE" "Year FE")) ///
    label star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress ///
    alignment(D{.}{.}{-1})

	
******************************
* alternative performance measures
******************************
est clear
reghdfe roe_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m1

reghdfe roe_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m2

reghdfe tobinq_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m3

reghdfe tobinq_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
estadd local firmfe "\checkmark" 
estadd local yearfe "\checkmark" 
est store m4

esttab m1 m2 m3 m4 using "./tables/alternative_regression.tex", replace ///
	collabels(none) ///
    cells(b(fmt(3) star) t(par fmt(3))) ///
    booktabs  ///
    order(treated_post l.gov_score treated_post_gov l.size l.debt_ratio_w l.nwc_w l.revenue_growth_w l.capex_ratio_w _cons) ///
    stats(N r2_a firmfe yearfe, labels("Observations" "Adjusted R-squared" "Firm FE" "Year FE")) ///
    label star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress ///
    alignment(D{.}{.}{-1})

	
******************************
* placebo tests
******************************
	
gen post_placebo = (year >= 2016)
gen treated_post_pb     = treated * post_placebo
gen treated_post_gov_pb = treated_post_pb  * l.gov_score

reghdfe roa_w treated_post_gov_pb treated_post_pb l.gov_score ///
        l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w ///
        if inrange(year,2014,2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)

	
	
	
	
	
	
	
	
******************************
* 异质性分析
******************************
* SOE 子样本
reghdfe roa_w treated_post_gov treated_post l.gov_score ///
        l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w ///
        if inrange(year,2014,2019) & year!=2018 & soe==1, ///
        absorb(firm_id year) vce(cluster firm_id)

* 非 SOE 子样本
reghdfe roa_w treated_post_gov treated_post l.gov_score ///
        l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w ///
        if inrange(year,2014,2019) & year!=2018 & soe==0, ///
        absorb(firm_id year) vce(cluster firm_id)
		
******************************
* 机制分析
******************************
* Step 1: 机制回归
reghdfe debt_ratio_w treated_post_gov treated_post l.gov_score ///
        l.revenue_growth_w l.size l.nwc_w l.capex_ratio_w ///
        if inrange(year,2014,2019) & year!=2018, ///
        absorb(firm_id year) vce(cluster firm_id)

		
		
		




	
	



reghdfe capex_ratio_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w  if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe debt_ratio_w treated_post_gov treated_post l.gov_score  l.size   if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
***************************************************















***********************************************
xtset firm_id year
gen capex_ratio = exp(capex - size)

winsor2 roa roe tobinq revenue_growth debt_ratio nwc  capex_ratio,cut(2.5, 97.5) 

gen treated_post = post*treated
gen treated_post_gov = treated_post *  gov_score


reghdfe roa_w treated_post_gov treated_post gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe roe_w treated_post_gov treated_post gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe roe_w treated_post_gov treated_post gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)










est clear   
reghdfe roe_w treated_post if year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m1
reghdfe roe_w treated_post_gov treated_post l.gov_score if year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m2
reghdfe roe_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m3
reghdfe roe_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if year!= 2018, absorb(firm_id year) vce(cluster firm_id)
est store m4

esttab m1 m2 m3 m4 using "./tables/regression.tex", replace ///
	collabels(none) ///
    cells(b(fmt(3) star) t(par fmt(3))) ///
    booktabs  ///
    order(treated_post treated_post_gov l.gov_score l.size l.debt_ratio_w l.nwc_w l.revenue_growth_w l.capex_ratio_w _cons) ///
    stats(N r2_a firmfe yearfe, labels("Observations" "Adjusted R-squared" "Firm FE" "Year FE")) ///
    label star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress ///
    alignment(D{.}{.}{-1})


