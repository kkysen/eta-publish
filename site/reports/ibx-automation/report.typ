#import "template.typ": capped_image, report

#show: report.with(
  title: "No Need to Wait: Automated Light Metro is Right for the IBX",
  short: "",
  phase: "Composition",
  dateline: "",
  contributors: ("John Ericson", "Madison Feinberg", "Daniel Fleer", "Robert Hale", "Darius Jankauskas", "Alon Levy", "Khyber Sen", ),
  contributors_note: "We wish to acknowledge the following ETA members who contributed to this report, and without whose hard work it would not be possible:",
  warnings: (
    [the #raw("Header") section has an unrecognized #raw("Before:") line; check it for a typo],
    [unfinished text in the document: #raw("Caption: TODO")],
    [the image #raw("img-e3ef182e") has no #raw("Credit:") line],
    [1 image is unnamed, so each publishes under a hash; give each a #raw("Source:") line naming its file:#list([#raw("img-e3ef182e"): Caption: TODO], )],
    [12 suggestions still open on this tab; the build publishes the document without them, as it reads today],
    [16 comment threads still open on this tab],
    [1 source still carries the tag it was copied with; take it off the link in the doc:#list([#raw("utm_source=chatgpt.com") on #raw("https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056&utm_source=chatgpt.com")], )],
    [the #raw("Header") section has no #raw("Publish Due Date:") line],
    [the #raw("Header") section has no #raw("Short:") line],
    [the #raw("Header") section has no #raw("SEO Description:") line],
    [style: #raw("90 seconds") should be #raw("90 sec"): #raw("...lows headways as low as every 90 seconds, as seen in many existing sys...")],
    [style: #raw("90 second") should be #raw("90 sec"): #raw("...ial ridership may not warrant 90 second headways, but ALM would allow...")],
    [style: #raw("5-minute") should be #raw("5-min"): #raw("...000 with the currently stated 5-minute peak headway, with off-peak h...")],
    [style: #raw("10 minutes") should be #raw("10 min"): #raw("...ff-peak headways ranging from 10 minutes midday to 15 minutes in the e...")],
    [style: #raw("15 minutes") should be #raw("15 min"): #raw("...ing from 10 minutes midday to 15 minutes in the evening. If peak headw...")],
    [style: #raw("2 minutes") should be #raw("2 min"): #raw("... peak headways are reduced to 2 minutes, with off-peak headways rangi...")],
    [style: #raw("3 minutes") should be #raw("3 min"): #raw("...ff-peak headways ranging from 3 minutes midday to 8 minutes in the ev...")],
    [style: #raw("8 minutes") should be #raw("8 min"): #raw("...ging from 3 minutes midday to 8 minutes in the evening, ridership ris...")],
    [style: #raw("5-minute") should be #raw("5 min"), with no hyphen: #raw("...000 with the currently stated 5-minute peak headway, with off-peak h...")],
    [style: two words should be separated by 1 space, not 2: #raw("...r, enabling agencies to reduce··capital costs while retaining ...")],
    [style: #raw("100 meters") should be #raw("100 m"): #raw("...le) that run trains less than 100 meters long and build stations barel...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("180 meters") should be #raw("180 m"): #raw("... on the New York City Subway (180 meters) or longer exclusively use hi...")],
  ),
  hero: [
#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/img-e3ef182e.jpg")[#capped_image("print/img-e3ef182e.jpg", alt: "Caption: TODO")],
  caption: [Caption: TODO],
)
  ],
)

Credit: MTA, #link("https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[via Gothamist]#super[#link(<src1>)[\[1\]]]

== Introduction

The MTA recently released new renderings of the IBX.
They appear to show high-level trains and platforms, an excellent decision if accurate.
The canopies and station entrances look very sleek and modern, but the stations are missing one crucial thing: platform screen doors (PSDs), which are now the standard for new build metro lines across the world.
Moreover, this once again indicates that MTA remains hesitant to commit to automating the IBX.

Now is the time to decide how the IBX should be built.
Later this fall, the MTA is slated to release the draft environmental impact statement for the IBX.
The public response to that will be one of the last times to shape the broadest contours of the project design, as the final environmental impact statement will lock in major decisions.
What broad type of service should be run, and what type of construction is needed to enable that service, should be decided now.

The original design for the IBX was forced by a street-running section to be a light rail design.
That section, by All Faiths Cemetery was thankfully removed, as we had suggested before this change was made.

This is a huge improvement: the IBX right-of-way is now guaranteed to be completely grade-separated, significantly improving system reliability and achievable frequency.
It also raises the question of what mode is now best for the project, since the original factors motivating the choice of light rail have since changed dramatically.

We believe the answer to the question is #emph[automated light metro] (ALM).
The key properties of ALMs are:

- Short trains
- Frequent trains
- Automated operations

In the rest of the document, we will explain how those three properties of ALM work together to ensure fast, reliable, and low-operating cost rapid transit, particularly fitting circumferential lines like IBX.

== Automated Light Metro at a Glance

ALM technology would enable the IBX to feature significantly higher all-day frequencies from day one by lowering operating costs.
ALM allows headways as low as every 90 seconds, as seen in many existing systems today internationally.
Initial ridership may not warrant 90 second headways, but ALM would allow peak and off-peak headways much lower than the MTA currently plans, which would increase ridership from day one and future-proof the IBX for significant growth.
It would also mean installing platform screen doors (PSDs) to protect riders from the risks of falling onto the tracks, the biggest source of risk to riders on the subway today.

The ALM operating paradigm has become increasingly popular around the globe for a variety of transit needs.
For a circumferential line like the IBX, it is especially well-suited.
Circumferential lines support and enable rides that are far more likely to involve transfers: Indeed, the #link("https://ibx.transitcosts.com/ibx-1/")[largest share of new jobs made accessible to commuters by the IBX is in Manhattan]#super[#link(<src2>)[\[2\]]], where IBX will not run, purely through better transfers between the IBX and lines that do run into Manhattan.
High frequency and reliability is especially important for facilitating transfers, since the wait between trains can make or break riders’ willingness to transfer. 

From the elimination of at-grade segments to the raising of platform heights in artistic renderings, ETA has been pleased to see the MTA’s continuing emphasis on designing the IBX in keeping with principles that maximize capacity and service quality.
We hope to see this trend continue through this next most important phase of the design process.
Choosing to design, construct, and operate the IBX as ALM will set up the line for success, and best serve its future riders.

== Rising Ridership

IBX ridership projections have steadily risen as plans materialize and improve.
Ridership projections have risen 84%#footnote[(160,000/day) / (87,800/day) = 1.839], from #link("https://www.mta.info/document/72081#page=16")[87,800/day]#super[#link(<src3>)[\[3\]]] in the #link("https://www.mta.info/document/72081")[initial feasibility study in 2022]#super[#link(<src4>)[\[4\]]], to #link("https://www.mta.info/document/103691#page=150")[115,000/day]#super[#link(<src5>)[\[5\]]] in the #link("https://www.mta.info/document/114891")[PEL study]#super[#link(<src6>)[\[6\]]], and to #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[160,000/day]#super[#link(<src7>)[\[7\]]] in the more detailed and higher-speed 2025 design—higher than the ridership of the #link("https://anita.garden/nycriders/")[G train (149,000/day)]#super[#link(<src8>)[\[8\]]] and the vehicle count on the #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[BQE (130,000/day)]#super[#link(<src9>)[\[9\]]], both of which also connect Brooklyn and Queens.
This has been driven by all of the following factors:

- Refinement of the ridership model as plans for the project have solidified
- Improved station siting
- A #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[31% reduction in runtime]#super[#link(<src10>)[\[10\]]] after #link("https://www.etany.org/ibx-all-faiths-tunnel")[ETA successfully pressured the MTA to drop street running] around All Faiths Cemetery#footnote[#link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/]#super[#link(<src29>)[\[29\]]] #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/]#super[#link(<src30>)[\[30\]]]]

Automated operations, enabling higher peak and off-peak frequencies, could unlock even more ridership.
An independent study by #link("https://arxiv.org/abs/2408.01562")[Hai Yang et al]#super[#link(<src11>)[\[11\]]] found that the upper bound of ridership, barring land-use changes, is 254,000 riders/day.
Another independent study by Franklin Tang at NYU Marron using the FTA’s STOPS ridership modeling software#footnote[STOPS depends on extensive calibration with existing ridership, which includes statistics like per-platform ridership, which the MTA does not make available.
Thus, there is a limit to its accuracy.
But the fact that it found a very similar number to the MTA’s closed-source Regional Transit Forecasting Model (RTFM) bodes well, and it also quite accurately (retroactively) predicted SAS Phase 1 ridership.
Including detailed ridership in open data would enable more accurate independent analyses confirming higher ridership potential.] found 198,000 with the currently stated 5-minute peak headway, with off-peak headways ranging from 10 minutes midday to 15 minutes in the evening.
If peak headways are reduced to 2 minutes, with off-peak headways ranging from 3 minutes midday to 8 minutes in the evening, ridership rises to 212,000, putting the IBX even above the Second Avenue Subway’s Phase 1, which saw about 160,000 daily pre-pandemic riders.

Ridership could also rise further with additional transit-oriented development (TOD) beyond current conditions, since the models referenced above assume present-day land use.#footnote[The FTA forbids the use of promises of future upzoning in ridership analysis.]
The Mamdani administration is interested in #link("https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[extending City of Yes upzoning to IBX]#super[#link(<src12>)[\[12\]]] and #link("https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[upzoning south of Prospect Park]#super[#link(<src13>)[\[13\]]].
Ongoing analysis by Elif Ensari at Marron previewed to ETA is finding that about 300,000 additional housing units could be built profitably along the IBX corridor if upzoned.

It is imperative that the IBX be future-proofed for higher ridership in the future.
We believe ALM is the most cost-effective way to future-proof the IBX, because it allows capacity to scale to meet future demand with comparatively little additional capital and operational investment.

While a light metro can be as small and limited as an airport’s people mover system, it can also be as large as the not fully automated #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[narrow 6B trains]#super[#link(<src14>)[\[14\]]] serving Guangzhou Metro Line 3, which carried #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[2.76 million riders a day]#super[#link(<src15>)[\[15\]]] in 2019, making it one of the busiest metro lines in the world.

== Automation

It’s important to understand that modern metro technology increasingly runs automatically, and ALM is merely the culmination of a trend.
This is classified in the following grades of automation (GoA):

- GoA1: manual operation
- GoA2: automated driving: the train drives automatically, but the operator opens the doors, closes the doors, and presses a button to start the automatic driving until the next station
- GoA3: driverless operation: the train runs automatically, but there is an on-board attendant to operate the train in emergencies
- GoA4: unattended operation: the train runs automatically, with no crew on board except perhaps for security

Today, entirely new metro lines in developed and even middle-income countries are usually driverless in the sense of GoA4.
When installed with platform screen doors and sensors, it eliminates intrusion and unintentional falls onto tracks, eliminating the #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[largest source of risk to passenger safety]#super[#link(<src16>)[\[16\]]].
Moreover, because automation allows trains to run at higher frequencies relative to manual operation, trains and stations can be smaller, enabling agencies to reduce  capital costs while retaining overall capacity.
For example, Italian cities have delivered incredibly cheap metro systems (\$200–300 million/mile) that run trains less than 100 meters long and build stations barely any longer than the trains.#footnote[#link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf]#super[#link(<src31>)[\[31\]]] In Italy, where many urban subway lines have been built this century, some driverless and some not, the cost of station construction has been fairly consistent at €500 per cubic meter outside the most difficult environments (such as Classical Roman sites), producing smaller driverless stations in Turin and Milan at €15 million per station and larger ones in more modern parts of Rome at €40 million.
Nonetheless, with soft costs included, the construction cost of ALM is about four to five times as high as that of on-street tramways.]
Despite the short lengths, capacity is high: Paris’s upcoming M15 ring, projected to run 360’ long trains, is projected to see 1.5 million riders a day over a length of 47 miles, a higher ridership per mile than the New York City Subway.

Driverless operation also has the unique benefit of permitting high off-peak frequency without incurring a commensurate increase in operating cost even in smaller cities with lower possible ridership or lines with lower ridership.
SkyTrain runs every 6–8 minutes off-peak on each of two branches, and the Copenhagen Metro runs every 4–6 minutes off-peak on each of two branches, and in all cases the branches separate quite far out of city center, offering about 3-minute frequencies on a lengthy trunk.
The systems using driverless VAL technology run every 3–6 minutes off-peak in Lille, Rennes, Toulouse, and Turin; in contrast, the non-driverless Marseille Metro runs every 10–15 minutes.

The costs of operating ALM technology in these cities are impressively low: the Expo and Millennium Lines of SkyTrain in Vancouver #link("https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[averaged US\$8.11/car-mile in 2025]#super[#link(<src17>)[\[17\]]],#footnote[This is imputed from C\$0.064/capacity-km per p. 37, a capacity of 91.86 per p. 19, and standard US-Canada PPP conversions #link("https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[per the OECD]#super[#link(<src32>)[\[32\]]].] less than half as much as New York City Transit, #link("https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[which averaged \$18.63 in 2024]#super[#link(<src18>)[\[18\]]].
This is important, as 72.5% of NYCT operating costs today are labor expenditures, and about 20% of subway workers are train operators.
In contrast, #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[SkyTrain is very light on employees, and expanded service dramatically in the late 2000s with little increase in the number of workers]#super[#link(<src19>)[\[19\]]].
This also insulates the system from fiscal pressure to cut service in order to save small amounts of money during a funding crisis.
The MTA plans 3–6 minute peak frequencies for IBX.
ALM can not only do better at the peak, but is more resilient to cuts off-peak that would degrade service to the point of unusability, a problem that has plagued many recently built American light rail networks coping with budget cuts.

For the IBX, achieving these operational benefits requires a minimal upfront increase in construction costs.
Since the corridor will already be grade separated, the only remaining requirement is protecting passengers from automatically driven trains.
In almost every ALM system, this protection is provided by platform screen doors, which physically prevent passengers from falling onto the tracks, preventing these collisions.
Existing American practice demonstrates this can be done at minimal cost. 

== Safety and Platform Screen Doors

Honolulu provides virtually the only US example pertinent to IBX.
The #link("https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056&utm_source=chatgpt.com")[PSDs for all 21 stations]#super[#link(<src20>)[\[20\]]] cost about \$27 million in 2013 USD.
Adjusted for inflation and the length of IBX stations, equipping all IBX platforms with PSDs would cost about \$31 million, #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[equal to 0.6% of its projected cost of \$5.5 billion]#super[#link(<src21>)[\[21\]]]. 

The safety benefits of PSDs are so strong that they should be installed on the IBX regardless of automation.
Indeed, Honolulu Authority for Rapid Transit board members #link("https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[swiftly approved the change order for PSDs]#super[#link(<src22>)[\[22\]]] after seeing a video of babies falling in front of trains.

== High Platforms

While we are encouraged that the renderings appear to show high-level platforms, the MTA should formally commit to high-floor vehicles.
While high-floor vehicles require straight or only gently curved platforms, the IBX right-of-way is generally wide enough for them.
High-floor vehicles are generally cheaper than low-floor ones, and passengers can circulate more easily in the former than in the latter where wheel wells take up valuable floor space.
Furthermore, building high platforms at the outset would greatly simplify any further capacity expansion later—practically all systems running frequent trains of the length seen on the New York City Subway (180 meters) or longer exclusively use high-floor vehicles.

== Rolling Stock

The MTA has not yet officially made rolling stock procurement decisions.
However, the influences of earlier project phases continue to be seen.
Prior to the complete grade separation of the corridor, trains would have needed to run on city streets, and curves in this section would have been much sharper.
These factors might have justified tram-like light rail vehicles designed for this purpose.

The All Faiths Tunnel removes the need for street running.
However, the MTA is still claiming that light rail vehicles are required in order to “#link("https://ibx.mta.info/about/")[travel through tight curves]#super[#link(<src23>)[\[23\]]].”
In fact, the tightest curve on the IBX route has a #link("https://www.mta.info/document/114891#page=992")[radius of 465 ft]#super[#link(<src24>)[\[24\]]]#footnote[The IBX1 LRT-18 curve in the PEL study has a radius of 465 ft. The wider-radius (917 ft) IBX2 LRT-11 curve is for the Brooklyn Army Terminal station option further west, but the MTA has decided on the eastern option closer to 2 Av, which has the 465 ft curve radius.], so generous that any train can fit.
The tightest curve on the NYC subway has a radius of #link("https://www.mta.info/document/172206#page=6")[100±10 ft]#super[#link(<src25>)[\[25\]]]#footnote[We’re not sure where the ~100 ft curve is, but the old South Ferry loop is close (110 ft) and is still in occasional revenue service.
Other tighter curves may be in yard trackage.], with the #link("https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[old South Ferry loop being 111 ft]#super[#link(<src26>)[\[26\]]].
Even the Washington, DC mMetro, designed to avoid the squeal of the tight curves of the oldest sections of the New York City Subway, #link("http://www.wmata.com/business/procurement_and_contracting/solicitations/uploads/RFP%20Energy%20Storage-Attachment%20B-Rail%20Car%20Performance%20for%20Design-Simulation.pdf")[has a minimum curve radius of 225 ft]#super[#link(<src27>)[\[27\]]], less than half of that of the IBX’s. The only tight curves were the #link("https://www.mta.info/document/114891#page=1014")[100 ft street-running curves]#super[#link(<src28>)[\[28\]]]#footnote[In the former street-running section, there were multiple 100 ft curves: IBX1 LRT-647, IBX1 LRT-661, IBX2 LRT641, IBX2 LRT656.]ones that have since been removed with the All Faiths tunnelare now ejected from the plan.

Hopefully this is a case where the public-facing website was not updated with the latest planning.
The alternatives far worse—whether its good right-of-way decisions not percolating over to rolling stock procurement, or the MTA making the right decision without understanding #emph[why] it is the right decision, this is not good. 

== Conclusion

IBX provides an excellent opportunity to import the ALM concept firmly into the MTA from preexisting examples such as the Montréal REM or the JFK Airtrain.
ALM stands to reinforce the benefits to Queens and Brooklyn that the already strong IBX project would deliver.
In addition to the immense benefits for IBX itself, it would serve as a proof-of-concept for, and facilitate maintenance and acquisition economies of scale with, potential future ALM systems on other corridors, such as in outer Queens and Brooklyn, or potentially New Jersey.

= Sources

+ #link("https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out] (archived #link("https://web.archive.org/web/20260910231933/https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[September 10, 2026]) <src1>
+ #link("https://ibx.transitcosts.com/ibx-1/")[https://ibx.transitcosts.com/ibx-1/] (archived #link("https://web.archive.org/web/20260512184007/https://ibx.transitcosts.com/ibx-1/")[May 12, 2026]) <src2>
+ #link("https://www.mta.info/document/72081#page=16")[https://www.mta.info/document/72081\#page=16] (archived #link("https://web.archive.org/web/20260518002035id_/https://www.mta.info/document/72081#page=16")[May 18, 2026]) <src3>
+ #link("https://www.mta.info/document/72081")[https://www.mta.info/document/72081] (archived #link("https://web.archive.org/web/20260518002035/https://www.mta.info/document/72081")[May 18, 2026]) <src4>
+ #link("https://www.mta.info/document/103691#page=150")[https://www.mta.info/document/103691\#page=150] (archived #link("https://web.archive.org/web/20260518002014id_/https://www.mta.info/document/103691#page=150")[May 18, 2026]) <src5>
+ #link("https://www.mta.info/document/114891")[https://www.mta.info/document/114891] (archived #link("https://web.archive.org/web/20260518002024/https://www.mta.info/document/114891")[May 18, 2026]) <src6>
+ #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up] (archived #link("https://web.archive.org/web/20260829123215/https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[August 29, 2026]) <src7>
+ #link("https://anita.garden/nycriders/")[https://anita.garden/nycriders/] (archived #link("https://web.archive.org/web/20260822120542/https://anita.garden/nycriders/")[August 22, 2026]) <src8>
+ #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml\#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily] (archived #link("https://web.archive.org/web/20260912070442/https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[September 12, 2026]) <src9>
+ #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes] (archived #link("https://web.archive.org/web/20260518022508/https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[May 18, 2026]) <src10>
+ #link("https://arxiv.org/abs/2408.01562")[https://arxiv.org/abs/2408.01562] (archived #link("https://web.archive.org/web/20260416140808/https://arxiv.org/abs/2408.01562")[April 16, 2026]) <src11>
+ #link("https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park] (archived #link("https://web.archive.org/web/20260902012928/https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[September 2, 2026]) <src12>
+ #link("https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi] (archived #link("https://web.archive.org/web/20260918152353/https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[September 18, 2026]) <src13>
+ #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/] (archived #link("https://web.archive.org/web/20260515114508/https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[May 15, 2026]) <src14>
+ #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html] (archived #link("https://web.archive.org/web/20250828081856/http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[August 28, 2025]) <src15>
+ #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/] (archived #link("https://web.archive.org/web/20260422232822/https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[April 22, 2026]) <src16>
+ #link("https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly\_reports/2025/2025-q2-financial-and-performance-report.pdf] (archived #link("https://web.archive.org/web/20260215035655/https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[February 15, 2026]) <src17>
+ #link("https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[https://www.transit.dot.gov/sites/fta.dot.gov/files/transit\_agency\_profile\_doc/2024/20008.pdf] (archived #link("https://web.archive.org/web/20260910171300/https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[September 10, 2026]) <src18>
+ #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[http://www.th.gov.bc.ca/publications/reports\_and\_studies/Review\_of\_TransLink.pdf] (archived #link("https://web.archive.org/web/20130515042955/http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[May 15, 2013]) <src19>
+ #link("https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056&utm_source=chatgpt.com")[https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056&utm\_source=chatgpt.com] (not archived) <src20>
+ #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review] (archived #link("https://web.archive.org/web/20260914114804/https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[September 14, 2026]) <src21>
+ #link("https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/] (archived #link("https://web.archive.org/web/20180704003258/https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[July 4, 2018]) <src22>
+ #link("https://ibx.mta.info/about/")[https://ibx.mta.info/about/] (archived #link("https://web.archive.org/web/20260921162613/https://ibx.mta.info/about/")[September 21, 2026]) <src23>
+ #link("https://www.mta.info/document/114891#page=992")[https://www.mta.info/document/114891\#page=992] (archived #link("https://web.archive.org/web/20260518002024id_/https://www.mta.info/document/114891#page=992")[May 18, 2026]) <src24>
+ #link("https://www.mta.info/document/172206#page=6")[https://www.mta.info/document/172206\#page=6] (archived #link("https://web.archive.org/web/20260519070421id_/https://www.mta.info/document/172206#page=6")[May 19, 2026]) <src25>
+ #link("https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[https://www.nycsubway.org/wiki/Chapter\_03.\_General\_Arrangement\_for\_Construction\#:~:text=150-,South%20Ferry%20loop,-111] (archived #link("https://web.archive.org/web/20251205012113/https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[December 5, 2025]) <src26>
+ #link("http://www.wmata.com/business/procurement_and_contracting/solicitations/uploads/RFP%20Energy%20Storage-Attachment%20B-Rail%20Car%20Performance%20for%20Design-Simulation.pdf")[http://www.wmata.com/business/procurement\_and\_contracting/solicitations/uploads/RFP%20Energy%20Storage-Attachment%20B-Rail%20Car%20Performance%20for%20Design-Simulation.pdf] (archived #link("https://web.archive.org/web/20160114052554/http://www.wmata.com/business/procurement_and_contracting/solicitations/uploads/RFP%20Energy%20Storage-Attachment%20B-Rail%20Car%20Performance%20for%20Design-Simulation.pdf")[January 14, 2016]) <src27>
+ #link("https://www.mta.info/document/114891#page=1014")[https://www.mta.info/document/114891\#page=1014] (archived #link("https://web.archive.org/web/20260518002024id_/https://www.mta.info/document/114891#page=1014")[May 18, 2026]) <src28>
+ #link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/] (archived #link("https://web.archive.org/web/20260719213805/https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[July 19, 2026]) <src29>
+ #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/] (archived #link("https://web.archive.org/web/20260513035917/https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[May 13, 2026]) <src30>
+ #link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf] (archived #link("https://web.archive.org/web/20260512184237/https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[May 12, 2026]) <src31>
+ #link("https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[https://data-explorer.oecd.org/vis?df\[ds\]=dsDisseminateFinalDMZ&df\[id\]=DSD\_NAMAIN10%40DF\_TABLE4&df\[ag\]=OECD.SDD.NAD&df\[vs\]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP\_B1GQ.......&lom=LASTNPERIODS&lo=10&to\[TIME\_PERIOD\]=false&ly\[cl\]=TIME\_PERIOD&ly\[rw\]=REF\_AREA,COMBINED\_UNIT\_MEASURE&vw=tb] (archived #link("https://web.archive.org/web/20260313233214/https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[March 13, 2026]) <src32>
