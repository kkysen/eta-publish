#import "template.typ": capped_image, report

#show: report.with(
  title: "No Need to Wait: Automated Light Metro is Right for the IBX",
  short: "",
  phase: "Composition",
  dateline: "",
  contributors: ("dariusj@etany.org", "Madison Feinberg", "Robert Hale", "Alon Levy", "Khyber Sen", "Franklin Tang", ),
  contributors_note: "We wish to acknowledge the following ETA members who contributed to this report, and without whose hard work it would not be possible:",
  warnings: (
    [the #raw("Header") section has an unrecognized #raw("Before:") line; check it for a typo],
    [unfinished text in the document: #raw("Caption: TODO")],
    [the image #raw("img-e3ef182e") has no #raw("Credit:") line],
    [1 image is unnamed, so each publishes under a hash; give each a #raw("Source:") line naming its file:#list([#raw("img-e3ef182e"): Caption: TODO], )],
    [25 suggestions still open on this tab; the build publishes the document without them, as it reads today],
    [13 comment threads still open on this tab],
    [the #raw("Header") section has no #raw("Publish Due Date:") line],
    [the #raw("Header") section has no #raw("Short:") line],
    [the #raw("Header") section has no #raw("SEO Description:") line],
    [style: #raw("90 seconds") should be #raw("90 sec"): #raw("...lows headways as low as every 90 seconds, as seen in many existing sys...")],
    [style: #raw("90 second") should be #raw("90 sec"): #raw("...ial ridership may not warrant 90 second headways, but ALM would allow...")],
    [style: two words should be separated by 1 space, not 2: #raw("... changes are necessary to make··ALM on the IBX corridor possib...")],
    [style: #raw("5-minute") should be #raw("5-min"): #raw("...98k with the currently stated 5-minute peak headway, with off-peak h...")],
    [style: #raw("10 minutes") should be #raw("10 min"): #raw("...ff-peak headways ranging from 10 minutes midday to 15 minutes in the e...")],
    [style: #raw("15 minutes") should be #raw("15 min"): #raw("...ing from 10 minutes midday to 15 minutes in the evening. If peak headw...")],
    [style: #raw("2 minutes") should be #raw("2 min"): #raw("... peak headways are reduced to 2 minutes, with off-peak headways rangi...")],
    [style: #raw("3 minutes") should be #raw("3 min"): #raw("...ff-peak headways ranging from 3 minutes midday to 8 minutes in the ev...")],
    [style: #raw("8 minutes") should be #raw("8 min"): #raw("...ging from 3 minutes midday to 8 minutes in the evening, ridership ris...")],
    [style: #raw("5-minute") should be #raw("5 min"), with no hyphen: #raw("...98k with the currently stated 5-minute peak headway, with off-peak h...")],
    [style: two words should be separated by 1 space, not 2: #raw("...models referenced above assume··present-day land use. The Mamd...")],
    [style: #raw("100 meters") should be #raw("100 m"): #raw("...le) that run trains less than 100 meters long and build stations barel...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("72.5 percent") should be #raw("72.5%"): #raw("... opex.] This is important, as 72.5 percent of NYCT operating costs today...")],
    [style: #raw("180 meters") should be #raw("180 m"): #raw("... on the New York City Subway (180 meters) or longer exclusively use hi...")],
    [style: a sentence should end with 1 space, not 2: #raw("...t costs are given separately).··This is a Buy America cost, wh...")],
    [style: #raw("32-min") should be #raw("32 min"), with no hyphen: #raw("With a 32-min runtime, 2-min turns, and a 9...")],
    [style: #raw("2-min") should be #raw("2 min"), with no hyphen: #raw("With a 32-min runtime, 2-min turns, and a 90% utilization ...")],
    [style: #raw("2-min") should be #raw("2 min"), with no hyphen: #raw("... fleet cost. But this is with 2-min peak headways, not 5-min peak...")],
    [style: #raw("5-min") should be #raw("5 min"), with no hyphen: #raw("...with 2-min peak headways, not 5-min peak headways. And with a 92%...")],
    [style: #raw("72,000 lbs") should be #raw("72,000 lb"): #raw("weight: 72,000 lbs per 65 ft AW0 car")],
    [style: #raw("72,000 lbs") should be #raw("72,000 lb"): #raw("AW0 weight/length: 72,000 lbs / 65 ft = 1648 kg/m")],
    [style: #raw("88.5 kmh") should be #raw("88.5 km/h"): #raw("speed: 55 mph (88.5 kmh) service, 65 mph (104.6 kmh) ...")],
    [style: #raw("104.6 kmh") should be #raw("104.6 km/h"): #raw("...h (88.5 kmh) service, 65 mph (104.6 kmh) design")],
    [style: #raw("175 lbs") should be #raw("175 lb"): #raw("AW0 weight/length: (232 t - (175 lbs * 780)) / (19.05 m * 4) = 223...")],
    [style: #raw("90 kmh") should be #raw("90 km/h"): #raw("speed: 90 kmh service (100 kmh design)")],
    [style: #raw("100 kmh") should be #raw("100 km/h"): #raw("speed: 90 kmh service (100 kmh design)")],
  ),
  hero: [
#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/img-e3ef182e.jpg")[#capped_image("print/img-e3ef182e.jpg", alt: "Caption: TODO")],
  caption: [Caption: TODO],
)
  ],
)

Credit: MTA, #link("https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[via Gothamist]#super[#link(<src1>)[\[1\]]]

The MTA recently released new renderings of the IBX.
They appear to show high-level trains and platforms, an excellent decision if accurate.
The canopies and station entrances look very sleek and modern, but the stations are missing one crucial thing: platform screen doors (PSDs), which are now the standard for new build metro lines across the world.
Moreover, this once again indicates that MTA remains hesitant to commit to automating the IBX.

== Introduction

Now is the time to decide how the IBX should be built.
Later this fall, the MTA is slated to release the draft environmental impact statement for the IBX.
The public response to that will be one of the last times to shape the broadest contours of the project design, as the final environmental impact statement will lock in major decisions.
What broad type of service should be run, and what type of construction is needed to enable that service, should be decided now.

The answer to both of these questions is what’s called #link("#automated-light-metro")[Automated Light Metro] (ALM).
The key properties of ALMs are:

- Short trains
- Frequent trains
- Automated operations

ALM technology would enable the IBX to feature significantly higher all-day frequencies from day one by lowering operating costs.
ALM allows headways as low as every 90 seconds, as seen in many existing systems today internationally.
Initial ridership may not warrant 90 second headways, but ALM would allow peak and off-peak headways much lower than the MTA currently plans, which future proofs the IBX for significant growth.

We welcome the decision to tunnel under the All Faiths Cemetery, as we had suggested before this change was made.
The IBX right-of-way is now guaranteed to be completely grade-separated, significantly improving system reliability and achievable frequency.
These changes are necessary to make  ALM on the IBX corridor possible, but they are not yet sufficient for it—the MTA and Governor Hochul need the will to install PSDs and automate it.

The ALM operating paradigm has become increasingly popular around the globe for a variety of transit needs.
For a circumferential line like the IBX, it is especially well-suited.
Circumferential lines support and enable rides that are far more likely to involve transfers: Indeed, the #link("https://ibx.transitcosts.com/ibx-1/")[largest share of new jobs made accessible to commuters by the IBX is in Manhattan]#super[#link(<src2>)[\[2\]]], where IBX will not run, purely through better transfers between the IBX and lines that do run into Manhattan.
High frequency and reliability is especially important for facilitating transfers, since the wait between trains can make or break riders’ willingness to transfer. 

From the elimination of at-grade segments to the raising of platform heights in artistic renderings, ETA has been pleased to see the MTA’s continuing emphasis on designing the IBX in keeping with principles that maximize capacity and service quality.
We hope to see this trend continue through this next most important phase of the design process.
If the right decisions are made in the next few months, the IBX's success will be all but guaranteed. 

== Rising Ridership

IBX ridership projections have steadily risen as plans materialize and improve.
Ridership projections have risen 84%#footnote[(160,000/day) / (87,800/day) = 1.839], from #link("https://www.mta.info/document/72081#page=16")[87,800/day]#super[#link(<src3>)[\[3\]]] in the #link("https://www.mta.info/document/72081")[initial feasibility study in 2022]#super[#link(<src4>)[\[4\]]], to #link("https://www.mta.info/document/103691#page=150")[115,000/day]#super[#link(<src5>)[\[5\]]] in the #link("https://www.mta.info/document/114891")[PEL study]#super[#link(<src6>)[\[6\]]], and to #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[160,000/day]#super[#link(<src7>)[\[7\]]] in the more detailed and higher-speed 2025 design—higher than the ridership of the #link("https://anita.garden/nycriders/")[G train (149k/day)]#super[#link(<src8>)[\[8\]]] and the vehicle count on the #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[BQE (130k/day)]#super[#link(<src9>)[\[9\]]], both of which also connect Brooklyn and Queens.
This has been driven by all of the following factors:

- Refinement of the ridership model as plans for the project have solidified
- Improved station siting
- A #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[31% reduction in runtime]#super[#link(<src10>)[\[10\]]] after #link("https://www.etany.org/ibx-all-faiths-tunnel")[ETA successfully pressured the MTA to drop street running] around All Faiths Cemetery#footnote[#link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/]#super[#link(<src26>)[\[26\]]] #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/]#super[#link(<src27>)[\[27\]]]]

An independent study by #link("https://arxiv.org/abs/2408.01562")[Hai Yang et al]#super[#link(<src11>)[\[11\]]] found that the upper bound of ridership, barring land-use changes, is 254k riders/day.
Another independent study by Franklin Tang at NYU Marron using the FTA’s STOPS ridership modeling software#footnote[STOPS depends on extensive calibration with existing ridership, which includes statistics like per-platform ridership, which the MTA does not make available.
Thus, there is a limit to its accuracy.
But the fact that it found a very similar number to the MTA’s closed-source Regional Transit Forecasting Model (RTFM) bodes well, and it also quite accurately predicted SAS Phase 1 ridership.
Including detailed ridership in open data would enable more accurate independent analyses confirming higher ridership potential.] found 198k with the currently stated 5-minute peak headway, with off-peak headways ranging from 10 minutes midday to 15 minutes in the evening.
If peak headways are reduced to 2 minutes, with off-peak headways ranging from 3 minutes midday to 8 minutes in the evening, ridership rises to 212k.
Once the recent trip time reductions are factored in, ridership could climb even higher, putting the IBX even above the Second Avenue Subway’s Phase 1, which saw about 200k daily pre-pandemic riders.

Ridership could rise even further with additional transit-oriented development (TOD) beyond current conditions. since the models referenced above assume  present-day land use.#footnote[The FTA forbids the use of promises of future upzoning in ridership analysis.]
The Mamdani administration is interested in #link("https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[extending City of Yes upzoning to IBX]#super[#link(<src12>)[\[12\]]] and #link("https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[upzoning south of Prospect Park]#super[#link(<src13>)[\[13\]]], and ongoing analysis by Elif Ensari at Marron previewed to ETA is finding that about 300,000 additional housing units could be built profitably in the area if current programs were extended and IBX were built.

It is imperative that the IBX be future-proofed for higher ridership in the future.
Luckily, there is a cost-effective solution to this that will also deliver unparalleled service to riders.

== Automated Light Metro

To understand what ALM is, it’s important to understand that modern metro technology increasingly runs automatically, and ALM is merely the culmination of a trend.
This is classified in the following grades of automation (GoA):

- GoA1: manual operation
- GoA2: automated driving: the train drives automatically, but the operator opens the doors, closes the doors, and presses a button to start the automatic driving until the next station
- GoA3: driverless operation: the train runs automatically, but there is an on-board attendant to operate the train in emergencies
- GoA4: unattended operation: the train runs automatically, with no crew on board except perhaps for security

Entirely new subway lines in developed and even middle-income countries are usually driverless in the sense of GoA4.
Automation eliminates the largest cost of operating a metro system, and in combination with platform screen doors and cameras, eliminates the #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[largest source of unreliability and unsafety]#super[#link(<src14>)[\[14\]]].
Shrinking the station sizes minimizes capital costs.
Small and medium cities in Italy have delivered incredibly cheap metro systems (\$200–300 million/mile) that run trains less than 100 meters long and build stations barely any longer than the trains.#footnote[#link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf]#super[#link(<src28>)[\[28\]]] In Italy, where many urban subway lines have been built this century, some driverless and some not, the cost of station construction has been fairly consistent at €500 per cubic meter outside the most difficult environments (such as Classical Roman sites), producing smaller driverless stations in Turin and Milan at €15 million per station and larger ones in more modern parts of Rome at €40 million.\# Nonetheless, with soft costs included, the construction cost of ALM is about four to five times as high as that of on-street tramways.]

The core value of driverless operation is that it permits high off-peak frequency, even in smaller cities with lower possible ridership or lines with lower ridership.
SkyTrain runs every 6–8 minutes off-peak on each of two branches, and the Copenhagen Metro runs every 4–6 minutes off-peak on each of two branches, and in all cases the branches separate quite far out of city center, offering about 3-minute frequencies on a lengthy trunk.
The systems using driverless VAL technology run every 3–6 minutes off-peak in Lille, Rennes, Toulouse, and Turin; in contrast, the non-driverless Marseille Metro runs every 10–15 minutes.

Thus, the earliest adopters of the technology have historically been smaller cities, which looked for medium capacity at low cost while still maintaining the high speed of a fully grade-separated metro system.
Larger cities have more recently started applying ALM technology on lines that do not expect to have ridership that warrants metro or regional rail.
In all cases, the best comparison is not with a conventional subway, but with a light rail system.
A conventional subway on such routes is usually rejected because it would be overkill for the expected ridership.

The costs of operating ALM technology in these cities are very low as well. \[Cite Expo and Millennium Line opex.\] This is important, as 72.5 percent of NYCT operating costs today are labor expenditures, and about 20% of subway workers are train operators.
In contrast, #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[SkyTrain is very light on employees, and expanded service dramatically in the late 2000s with little increase in the number of workers]#super[#link(<src15>)[\[15\]]].
This also insulates the system from the threat of service cuts to save small amounts of money with every funding crisis.
The MTA plans 3–6 minute peak frequencies for IBX.
ALM can not only do better at the peak, but is more resilient to cuts off-peak that would degrade service to the point of unusability, a problem that has plagued many recently built American light rail networks.

== Safety and Platform Screen Doors

\[Discuss Honolulu Skyline.
Only US example.
Good rolling stock costs.
Appropriate rolling stock for IBX except it's third rail not catenary.
PSDs have a separate cost since it came as a change order, ~\$27M/21 stations.
Would be ~\$31M for the IBX if adjusted for inflation and number of stations, which is 0.5% of total project cost.\]

\[Honolulu board was convinced to add PSDs by showing them videos of babies falling in front of trains.
Might be a good strategy.
Also for subway surfing and open gangways.\]

Old text:

GoA4 automation generally requires platform screen doors (PSDs) with only a few grandfathered exceptions worldwide (Vancouver and Nuremberg).
This ensures the train operation is exceptionally safe, and no people, or objects are at risk of getting hit by trains.
No one can be pushed or fall into the tracks, and if open-gangways are used, no one can subway surf.
And crashes are exceedingly rare.
Of the handful of crashes, all but one were when human drivers took over control.

But automation and PSDs mean a lot more than safety.
Runtimes are highly reliable, as there is no operator variability and nothing can fall onto the tracks.
Precise acceleration and braking curves mean speed is increased, all while the ride is smoother, too.
And then high reliability means#footnote[#link("https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[https://en.wikipedia.org/wiki/Automatic\_train\_operation\#Accidents\_and\_incidents\_involving\_ATO]#super[#link(<src29>)[\[29\]]]] schedule padding can be reduced, further cutting runtimes.

== Light Metro

While a light metro can be as small and limited as an airport’s people mover system, it can also be as large as the #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[narrow 6B trains]#super[#link(<src16>)[\[16\]]] serving Guangzhou Metro Line 3, which carried #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[2.76 million riders a day]#super[#link(<src17>)[\[17\]]] in 2019 and is perhaps the busiest metro line in the world.#footnote[As far as we are aware, the only rapid transit lines that carry more riders per day are Tokyo’s Yamanote Line (~5 million/day) and Mumbai Suburban Railway’s Western Line (~3 million/day).
However, both are technically mainline rail lines, and Mumbai’s Western Line is quad-tracked for much of its length.]

=== Off-the-shelf rolling stock

Importantly, the MTA has its pick of makers for standardized light metro railcars and seems intent on selecting an off-the-shelf design.
If it follows through, it would, happily, break a trend of insisting carmakers comply with exacting standards, which started back in 1977 in the wake of the #link("https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[R46 truck-cracking debacle]#super[#link(<src18>)[\[18\]]].
As we have#link("https://www.etany.org/a-not-so-capital-plan-1-most-expensive-subway-train")[ ]#link("https://www.etany.org/a-not-so-capital-plan-1-most-expensive-subway-train")[chronicled], trusting experienced firms to meet their needs is what most other transit agencies do, and it is a major reason why they have generally beaten out New York City on subway costs, especially as of late.

=== High platforms

To really seal the IBX’s fate as a transit project, the MTA needs to commit to high-floor vehicles.
While high-floor vehicles require straight or only gently curved platforms, the IBX right-of-way is generally wide enough for them.
High-floor vehicles are generally cheaper than low-floor ones, and passengers can circulate more easily in the former than in the latter where wheel wells take up valuable floor space.
Furthermore, building high platforms at the outset would greatly simplify any further capacity expansion later—practically all systems running frequent trains of the length seen on the New York City Subway (180 meters) or longer exclusively use high-floor vehicles.

== Conclusion

IBX provides an excellent opportunity to import the ALM concept firmly into the MTA from preexisting examples such as the Montréal REM or the JFK Airtrain.
In addition to the immense benefits for IBX itself, it would serve as a proof-of-concept for, and facilitate maintenance and acquisition economies of scale with, potential future ALM systems on other corridors, such as in outer Queens and Brooklyn, or potentially New Jersey.

== FIXME More about rolling stock? Unclear where this was supposed to go. Not Conclusion

Hitachi Driverless Metro railcars are used on Honolulu’s Skyline, are proven in the US (important to the MTA), and are cheaper at \$2.2 million/car (need to inflation-adjust) without bundled maintenance (it is bundled, as are operations, but costs are given separately).  This is a Buy America cost, while the Alstom Metropolis Saint-Laurent cars are built in India.

With a 32-min runtime, 2-min turns, and a 90% utilization rate, 38 trainsets are needed.
At 4 cars/trainset and using Honolulu’s costs of \$2.2 million/car inflation-adjusted to June 2025, this fleet would cost \$421 million.
Assuming #link("https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[3.5% future inflation]#super[#link(<src19>)[\[19\]]] (used by the MTA’s 20-Year Needs Comparative Evaluation), this would be \$444 million in 2027,#footnote[ceil(((32 min + 2 min) \* 2) / 2 min / 90%) trainsets \* 4 cars/trainset \* \$2.2 million/car \* 124% (Apr 2020 to Jan 2025 inflation) \* 103.5%^(2027-2025)] only slightly higher than the MTA’s estimated \$432 million for fleet cost.
But this is with 2-min peak headways, not 5-min peak headways.
And with a 92% utilization rate, the cost comes down to exactly \$432 million.

#underline[Hitachi Driverless Metro Honolulu]

cost: #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[\$2.2 million/car]#super[#link(<src20>)[\[20\]]] (#link("http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[contract in 2011]#super[#link(<src21>)[\[21\]]], #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[first delivered on March 25, 2016]#super[#link(<src22>)[\[22\]]], #link("https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[last delivered on April 24, 2024]#super[#link(<src23>)[\[23\]]])

fleet: 80 cars

cost/length in June 2025: \$2.2 million/car / 65 ft/car \* 1.26 (April 2020 to June 2025 inflation) = \$140k/m

length: 65 ft (19.81 m)

width: 10 ft (3.048 m)

weight: #link("http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[72,000 lbs per 65 ft AW0 car]#super[#link(<src24>)[\[24\]]]

AW0 weight/length: 72,000 lbs / 65 ft = 1648 kg/m

formation: 4-car open-gangway sets

electrification: 750 V DC third rail

speed: 55 mph (88.5 kmh) service, 65 mph (104.6 kmh) design

capacity: 800

doors: 3/car

signaling: DTG (distance to go) ATC, Hitachi

seating: transverse and longitudinal

#underline[Alstom Metropolis Saint-Laurent]

cost: 

fleet: 

cost/length: 

length: 19.05 m

width: 2.94 m

weight: #link("https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[232 t per 76.2 m AW3 4-car trainset]#super[#link(<src25>)[\[25\]]]

AW0 weight/length: (232 t - (175 lbs \* 780)) / (19.05 m \* 4) = 2232 kg/m

formation: 2-car open-gangway sets coupled into 4-car sets

electrification: 1500 V DC catenary

speed: 90 kmh service (100 kmh design)

capacity: 780

doors: 3/car

signaling: Alstom Urbalis 400 CBTC

seating: longitudinal

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
+ #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/] (archived #link("https://web.archive.org/web/20260422232822/https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[April 22, 2026]) <src14>
+ #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[http://www.th.gov.bc.ca/publications/reports\_and\_studies/Review\_of\_TransLink.pdf] (archived #link("https://web.archive.org/web/20130515042955/http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[May 15, 2013]) <src15>
+ #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/] (archived #link("https://web.archive.org/web/20260515114508/https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[May 15, 2026]) <src16>
+ #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html] (archived #link("https://web.archive.org/web/20250828081856/http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[August 28, 2025]) <src17>
+ #link("https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16] (archived #link("https://web.archive.org/web/20251008074227/https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[October 8, 2025]) <src18>
+ #link("https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[https://future.mta.info/documents/20-YearNeedsAssessment\_ComparativeEvaluation.pdf\#page=3] (archived #link("https://web.archive.org/web/20260821175057id_/https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[August 21, 2026]) <src19>
+ #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html\#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to] (archived #link("https://web.archive.org/web/20210120105720/https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[January 20, 2021]) <src20>
+ #link("http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf] (archived #link("https://web.archive.org/web/20251013003705/http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[October 13, 2025]) <src21>
+ #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html] (archived #link("https://web.archive.org/web/20210120105720/https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[January 20, 2021]) <src22>
+ #link("https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train] (archived #link("https://web.archive.org/web/20260419060929/https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[April 19, 2026]) <src23>
+ #link("http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[http://www.staradvertiser.com/news/20110322\_Have\_a\_seat.html\#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.] (archived #link("https://web.archive.org/web/20140808010159/http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[August 8, 2014]) <src24>
+ #link("https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[https://rem.info/en/rolling-stock\#:~:text=Maximum%20weight%3A%20232%20tonnes] (archived #link("https://web.archive.org/web/20260616144315/https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[June 16, 2026]) <src25>
+ #link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/] (archived #link("https://web.archive.org/web/20260719213805/https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[July 19, 2026]) <src26>
+ #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/] (archived #link("https://web.archive.org/web/20260513035917/https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[May 13, 2026]) <src27>
+ #link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf] (archived #link("https://web.archive.org/web/20260512184237/https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[May 12, 2026]) <src28>
+ #link("https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[https://en.wikipedia.org/wiki/Automatic\_train\_operation\#Accidents\_and\_incidents\_involving\_ATO] (archived #link("https://web.archive.org/web/20260906195011/https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[September 6, 2026]) <src29>
