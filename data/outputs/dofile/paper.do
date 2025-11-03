

est clear    
	
estpost summarize total_score_norm ln_ev revenue_growth size debt_ratio nwc roa treated post


	
esttab using "./tables/table1.tex", replace ///
    cells("mean(fmt(%9.2f)) sd(fmt(%9.2f)) min max count") ///
    nonumber nomtitle nonote noobs label booktabs ///
    collabels("Mean" "SD" "Min" "Max" "N")

esttab m1 m2 m3 m4 using "./tables/regression.tex", replace ///
    se label b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
    nogaps compress booktabs ///
    title("Regression results") ///
    alignment(D{.}{.}{-1})


coefplot, keep(int_m4 int_m3 int_m2 int_0 int_p1) ///
    vertical yline(0, lpattern(dash)) ci(95) ///
    coeflabels(int_m4 = "-4 years" ///
               int_m3 = "-3 years" ///
               int_m2 = "-2 years" ///
               int_0  = "Treatment year" ///
               int_p1 = "+1 year") ///
    order(int_m4 int_m3 int_m2 int_0 int_p1) ///
    mcolor(blue) lcolor(blue) ciopts(color(gs12)) ///
    title("Parallel Trends Test") ///
    xtitle("Event Time") ///
    ytitle("Coefficient Estimate")
