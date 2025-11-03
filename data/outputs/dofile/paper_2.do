xtset firm_id year
*gen ln_ev = ln(ev)
*winsor2 ln_ev, cut(2.5 97.5)
gen capex_ratio = exp(capex - size)

winsor2 roa roe tobinq revenue_growth debt_ratio nwc  capex_ratio,cut(2.5, 97.5) 

***********************************************
gen treated_post = post*treated
gen treated_post_gov = treated_post *  l.gov_score

*reghdfe ln_ev_w treated_post_gov treated_post gov_score  if year!=2018, absorb(firm_id year) vce(cluster firm_id)
*reghdfe roe_w treated_post if year!= 2018, absorb(firm_id year) vce(cluster firm_id)
*reghdfe tobinq_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe roa_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
*reghdfe roe_w treated_post_gov treated_post l.gov_score if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe roa_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
*reghdfe roe_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w l.capex_ratio_w if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)


reghdfe capex_ratio_w treated_post_gov treated_post l.gov_score l.revenue_growth_w l.size l.debt_ratio_w l.nwc_w  if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)
reghdfe debt_ratio_w treated_post_gov treated_post l.gov_score  l.size   if inrange(year, 2014, 2019) & year!= 2018, absorb(firm_id year) vce(cluster firm_id)

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
    order(treated_post l.gov_score treated_post_gov l.size l.debt_ratio_w l.nwc_w l.revenue_growth_w l.capex_ratio_w _cons) ///
    stats(N r2_a firmfe yearfe, labels("Observations" "Adjusted R-squared" "Firm FE" "Year FE")) ///
    label star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress ///
    alignment(D{.}{.}{-1})


