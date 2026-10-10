#import "template.typ": capped_image, report

#show: report.with(
  title: "No Need to Wait: Automated Light Metro is Right for the IBX",
  short: "",
  phase: "Editing",
  dateline: "October 12, 2026",
  contributors: ("John Ericson", "Madison Feinberg", "Daniel Fleer", "Robert Hale", "Darius Jankauskas", "Alon Levy", "Blair Lorenzo", "Khyber Sen", ),
  contributors_note: "We wish to acknowledge the following ETA members who contributed to this report, and without whose hard work it would not be possible:",
  warnings: (
    [the #raw("Header") section has an unrecognized #raw("SME/Liaison:") line; check it for a typo],
    [the #raw("Header") section has an unrecognized #raw("Goals:") line; check it for a typo],
    [the #raw("Header") section has an unrecognized #raw("Audience:") line; check it for a typo],
    [unfinished text in the document: #raw("[cite]")],
    [unfinished text in the document: #raw("[picture of JFK AirTrain]")],
    [unfinished text in the document: #raw("[picture of NYC CBTC trains extremely close to each other]")],
    [unfinished text in the document: #raw("[explain one example about how crewing affects this]")],
    [unfinished text in the document: #raw("[cite, bqrail]")],
    [unfinished text in the document: #raw("[car-mile operating costs graph NYCT vs Vancouver]")],
    [unfinished text in the document: #raw("[caption]")],
    [unfinished text in the document: #raw("[cite]")],
    [unfinished text in the document: #raw("[insert image of at-grade station crossing on HBLR]")],
    [image #raw("kix.jgxhj1hqsf1i") has no alt text and no caption; add a description to it in the doc],
    [image #raw("kix.tx1fjdbmxbaz") has no alt text and no caption; add a description to it in the doc],
    [unfinished text in the document: #raw("[cite]")],
    [unfinished text in the document: #raw("[explain 6B]")],
    [unfinished text in the document: #raw("[cite RAPTOR results, all are around 20k/km]")],
    [unfinished text in the document: #raw("On the existing NYC subway, retrofitting PSDs at every station is unfortunately ")],
    [unfinished text in the document: #raw("[cite]")],
    [unfinished text in the document: #raw("[TODO finish and adapt to footnote]")],
    [the image #raw("automated_share_by_year_2016_to_2026") has no caption],
    [the image #raw("automated_share_by_year_ex_china_2016_to_2026") has no caption],
    [2 images are unnamed, so each publishes under a hash; give each a #raw("Source:") line naming its file:#list([#raw("img-e3ef182e"): A new artistic rendering of the IBX at New Utrecht Av. They appear to...], [#raw("img-dfdefb85"): \[caption\]], )],
    [19 suggestions still open on this tab; the build publishes the document without them, as it reads today],
    [21 comment threads still open on this tab],
    [the #raw("Header") section has no #raw("Short:") line],
    [the #raw("Header") section has no #raw("SEO Description:") line],
    [style: #raw("90 seconds") should be #raw("90 sec"): #raw("...lows headways as low as every 90 seconds, as seen in many existing sys...")],
    [style: #raw("90 second") should be #raw("90 sec"): #raw("...ial ridership may not warrant 90 second headways, but ALM would allow...")],
    [style: #raw("5 minute") should be #raw("5 min"): #raw("...000 with the currently stated 5 minute peak headway, with off-peak h...")],
    [style: #raw("10 minutes") should be #raw("10 min"): #raw("...ff-peak headways ranging from 10 minutes midday to 15 minutes in the e...")],
    [style: #raw("15 minutes") should be #raw("15 min"): #raw("...ing from 10 minutes midday to 15 minutes in the evening. If peak headw...")],
    [style: #raw("2 minutes") should be #raw("2 min"): #raw("... peak headways are reduced to 2 minutes, with off-peak headways rangi...")],
    [style: #raw("3 minutes") should be #raw("3 min"): #raw("...ff-peak headways ranging from 3 minutes midday to 8 minutes in the ev...")],
    [style: #raw("8 minutes") should be #raw("8 min"): #raw("...ging from 3 minutes midday to 8 minutes in the evening, ridership ris...")],
    [style: two words should be separated by 1 space, not 2: #raw("...metro can scale from something··as small and limited as an air...")],
    [style: #raw("100 meters") should be #raw("100 m"): #raw("...le) that run trains less than 100 meters long and build stations barel...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...te far out of city center, so 3-minute frequencies are offered on a ...")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...te far out of city center, so 3-minute frequencies are offered on a ...")],
    [style: #raw("5 minute") should be #raw("5 min"): #raw("... The MTA currently plans only 5 minute peak frequencies for the IBX ...")],
    [style: #raw("3 minutes") should be #raw("3 min"): #raw("...ng higher peak frequencies of 3 minutes [cite, bqrail] as well, which...")],
    [style: #raw("3 minute") should be #raw("3 min"): #raw("... to affordably maintain those 3 minute headways throughout the day i...")],
    [style: #raw("10 minutes") should be #raw("10 min"): #raw("... day instead of collapsing to 10 minutes off-peak.")],
    [style: #raw("180 meters") should be #raw("180 m"): #raw("... on the New York City Subway (180 meters) or longer exclusively use hi...")],
    [style: a dash is written with a space beside it, and the house style closes it up: #raw("...urage walking across the track — note this doesn’t matter so m...")],
    [style: #raw("Ball Square") should be #raw("Ball Sq"): #raw("...Green Line Extension designed Ball Square and East Somerville to requir...")],
    [style: #raw("Jersey Avenue") should be #raw("Jersey Av"): #raw("...s Newport, Harsimus Cove, and Jersey Avenue. This is not acceptable for a...")],
    [style: #raw("32 minute") should be #raw("32 min"): #raw("...ntimes. The MTA’s commendable 32 minute runtime target, for example, ...")],
    [style: two words should be separated by 1 space, not 2: #raw("...il). The presentation was done··on 3/26/2024 by WSP, the consu...")],
  ),
  hero: [
#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/img-e3ef182e.jpg")[#capped_image("print/img-e3ef182e.jpg", alt: "A new artistic rendering of the IBX at New Utrecht Av. They appear to show a high-level platform on the far-side platform, although this is not yet confirmed. The station still lacks any platform screen doors (PSDs).")],
  caption: [A new artistic rendering of the IBX at New Utrecht Av. They appear to show a high-level platform on the far-side platform, although this is not yet confirmed. The station still lacks any platform screen doors (PSDs). \
  Credit: MTA, #link("https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[via Gothamist]#super[#link(<src1>)[\[1\]]]],
)
  ],
)

== Introduction

Now is the time to decide how the IBX should be built.
The MTA is slated to release the draft environmental impact statement (DEIS) for the IBX in #link("https://ibx.mta.info/#:~:text=anticipated%20release%20in-,late%202026,-)")[late 2026]#super[#link(<src2>)[\[2\]]].
The public response to that will be one of the last times to shape the broadest contours of the project design, as the final environmental impact statement (FEIS) will lock in major decisions.
What broad type of service should be run, and what type of construction is needed to enable that service, should be decided now.

The original design for the IBX was forced at the time to be light rail by a street-running section with truly tight curves.
That section, by All Faiths Cemetery, will thankfully now be #link("https://www.youtube.com/watch?v=HEfH7R6j6QY")[built as a tunnel]#super[#link(<src3>)[\[3\]]], as #link("https://www.etany.org/ibx-all-faiths-tunnel")[ETA had pushed for] before this change was made.
This is a huge improvement: the IBX right-of-way is now guaranteed to be completely grade-separated, significantly improving speed, reliability, and achievable frequency.
A key way grade separation does this is by unlocking better service and rolling stock designs.
Will the MTA actually seize that opportunity?
On this front, there have been mixed signals.
This document aims to make clear what the needs of IBX are, what constraints no longer apply, and how all this determines clear best choices for the IBX going forward.

Since announcing the All Faiths tunnel, the MTA has started to describe the IBX more as a light metro.
Jamie Torres-Springer, head of MTA Construction & Development, described the IBX at that press conference as a #link("https://www.youtube.com/live/HEfH7R6j6QY?t=911s")[“light rail metro,”]#super[#link(<src4>)[\[4\]]] and at IBX Open Houses, MTA IBX staff also said that the IBX will now be a lot closer to a light metro.

However, other parts of the MTA perhaps didn't get the memo.
The IBX website #link("https://ibx.mta.info/about/#:~:text=to%20travel%20through-,tight%20curves,-Fit%20through%20the")[claims light rail is necessary to deal with tight curves]#super[#link(<src5>)[\[5\]]], but in fact, due to the removal of the street-running segment, the minimum IBX curve radius is exceptionally gentle and #link("https://www.wmata.com/business/procurement/solicitations/documents/General%20Design%20Criteria%20-%208K%202017%2001%2024.pdf#page=4")[twice as much as that of the Washington Metro]#super[#link(<src6>)[\[6\]]], more than enough to permit any type of train at over 30 mph (see #link("#rolling-stock")[Rolling Stock] for more detail).
Failure to cull unneeded constraints like this from the rolling stock procurement process will likely drive up costs without benefiting IBX riders in any way.

Therefore, while the words have been a welcoming and encouraging sign, the MTA has yet to commit to the concrete details underlying this: high-floor light metro vehicles.
And more importantly, they are missing one crucial piece: automation.

We believe the solution is #emph[automated light metro] (ALM).
The key properties of ALMs are:

- Automated operations
- Short trains
- High frequency

ALM technology would enable the IBX to feature significantly higher all-day frequencies from day one by lowering operating costs.
ALM allows headways as low as every 90 seconds, as seen in many existing systems today internationally.
Initial ridership may not warrant 90 second headways, but ALM would allow peak and off-peak headways much lower than the MTA currently plans, which would increase ridership from day one and future-proof the IBX for significant growth.
It would also mean installing platform screen doors (PSDs) to protect riders from the risks of falling onto the tracks, the biggest source of risk to riders on the subway today.

== Rising Ridership

IBX ridership projections have steadily risen as plans materialize and improve.
The design of the IBX must be future-proofed to accommodate this rising ridership, and utilizing ALM technology is critical to do so in a cost-effective manner.

In particular, ridership projections have risen 84%#footnote[(160,000/day) / (87,800/day) = 1.839], from #link("https://www.mta.info/document/72081#page=16")[87,800/day]#super[#link(<src7>)[\[7\]]] in the #link("https://www.mta.info/document/72081")[initial feasibility study in 2022]#super[#link(<src8>)[\[8\]]], to #link("https://www.mta.info/document/103691#page=5")[115,000/day]#super[#link(<src9>)[\[9\]]] in the #link("https://www.mta.info/document/114891")[PEL study]#super[#link(<src10>)[\[10\]]], and to #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[160,000/day]#super[#link(<src11>)[\[11\]]] in the more detailed and higher-speed 2025 design.
This is higher than the ridership of the #link("https://anita.garden/nycriders/")[G train (149,000/day)]#super[#link(<src12>)[\[12\]]] and the vehicle count on the #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[BQE (130,000/day)]#super[#link(<src13>)[\[13\]]], both of which also connect Brooklyn and Queens.
This has been driven by all of the following factors:

- Refinement of the ridership model as plans for the project have solidified
- Improved station siting
- A #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[31% reduction in runtime]#super[#link(<src14>)[\[14\]]] after #link("https://www.etany.org/ibx-all-faiths-tunnel")[ETA’s analysis] and #link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[Ben Brachfeld’s reporting]#super[#link(<src15>)[\[15\]]] successfully pressured the MTA to #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[drop street running]#super[#link(<src16>)[\[16\]]] around All Faiths Cemetery

Ridership could also rise further with additional transit-oriented development (TOD) beyond current conditions, since the models referenced above assume present-day land use.
The Mamdani administration is interested in #link("https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[extending City of Yes upzoning to the IBX]#super[#link(<src17>)[\[17\]]] and #link("https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[upzoning south of Prospect Park]#super[#link(<src18>)[\[18\]]].
Ongoing analysis by Elif Ensari at NYU Marron previewed to ETA is finding that about 300,000 additional housing units could be built profitably along the IBX corridor if it is upzoned.

Automated operations, beyond accommodating increased ridership from external factors like housing growth, also themselves unlock even more ridership, by enabling higher peak and off-peak frequencies.
An independent study by #link("https://arxiv.org/abs/2408.01562")[Hai Yang et al]#super[#link(<src19>)[\[19\]]] found that the upper bound of ridership, barring land-use changes, is 254,000 riders/day.
Another independent study by Franklin Tang at NYU Marron using the #link("https://www.transit.dot.gov/funding/grant-programs/capital-investments/stops")[FTA’s STOPS ridership modeling software]#super[#link(<src20>)[\[20\]]]#footnote[STOPS depends on extensive calibration with existing ridership, which includes statistics like per-platform ridership, which the MTA does not make available.
Thus, there is a limit to its accuracy.
But the fact that it found a very similar number to the MTA’s closed-source Regional Transit Forecasting Model (RTFM) bodes well, and it also quite accurately (retroactively) predicted SAS Phase 1 ridership.
Including detailed ridership in open data would enable more accurate independent analyses confirming higher ridership potential.] found 198,000 with the currently stated 5 minute peak headway, with off-peak headways ranging from 10 minutes midday to 15 minutes in the evening.
If peak headways are reduced to 2 minutes, with off-peak headways ranging from 3 minutes midday to 8 minutes in the evening, ridership rises to 212,000, putting the IBX above even the Second Avenue Subway’s Phase 1, which saw somewhere between 175,000 and #link("https://www.governor.ny.gov/news/governor-hochul-and-mta-announce-second-avenue-subway-phase-2-moves-forward#:~:text=carried%20more%20than-,200%2C000,-passengers%20on%20a")[200,000]#super[#link(<src21>)[\[21\]]]#footnote[This number is somewhat higher than what MTA data suggests.
A naive count of SAS Phase 1 ridership that counts double the entries (as a proxy for entries and exits) at the 3 new SAS Phase 1 stations, plus Lexington Av/63 St, including all of its F riders, is 198,338, close to the MTA’s 200,000.
A more detailed analysis of the fall 2025 origin destination data with the RAPTOR routing algorithm #strong[\[cite\]] and then scaling for both pandemic recovery at the SAS Phase 1 stations and subway fare evasion gives around ~175,000.
A September Wednesday gives around ~193,000.
Transfer sensitivity analysis shows there is little variance in these numbers for SAS Phase 1.
However, if the true number is lower than what the MTA suggests, this only strengthens the case for the IBX’s ridership.] daily pre-pandemic riders.

It is imperative that the IBX be future-proofed for higher ridership in the future.
ALM is the most cost-effective way to accomplish this: it allows capacity to scale to meet future demand with comparatively little additional capital and operational investment.
Light metro can scale from something  as small and limited as an airport’s people mover system to systems as large as the (not fully automated) #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[narrow 6B trains]#super[#link(<src22>)[\[22\]]]#footnote[#strong[\[explain 6B\]]] serving Guangzhou Metro Line 3, which carried #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[2.76 million riders a day]#super[#link(<src23>)[\[23\]]] in 2019, making it one of the busiest metro lines in the world.

== Automation

The rider capacity and high frequency needs of the IBX described above make automation the obvious best choice for the IBX.
Not only is it the best choice, but it should also be seen as the default choice for any new line not extending a pre-existing line.
Without the constraint of needing to interoperate with a legacy line, automation is a clear net-benefit and a cornerstone of modern rapid transit planning.

Modern metro technology increasingly runs automated, and ALM is merely the culmination of that trend.
Today, entirely new metro lines in developed and even middle-income countries are usually driverless, and increasingly so: in 2025, 73% of new metro lines#footnote[This counts all new-build, grade-separated, non-mainline urban rail lines.] were automated.
In fact, when talking to major rolling stock vendors at InnoTrans 2026 who were bidding on the IBX, they could not understand why the MTA would ever consider building the IBX unautomated.
The global standard for a new-build metro line these days, light or heavy, simply is to be automated.
They have told the MTA this, and hopefully the MTA follows their advice.

#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/automated_share_by_year_2016_to_2026.svg")[#capped_image("print/automated_share_by_year_2016_to_2026.svg")],
  caption: [#link("https://github.com/kkysen/automated-metro-data")[Credit: ETA (Khyber Sen)]#super[#link(<src24>)[\[24\]]], #link("https://www.urbanrail.net/news.htm")[UrbanRail.net]#super[#link(<src25>)[\[25\]]], #link("https://www.camet.org.cn/")[CAMET]#super[#link(<src26>)[\[26\]]]],
)

#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/automated_share_by_year_ex_china_2016_to_2026.svg")[#capped_image("print/automated_share_by_year_ex_china_2016_to_2026.svg")],
  caption: [#link("https://github.com/kkysen/automated-metro-data")[Credit: ETA (Khyber Sen)]#super[#link(<src24>)[\[24\]]], #link("https://www.urbanrail.net/news.htm")[UrbanRail.net]#super[#link(<src25>)[\[25\]]], #link("https://www.camet.org.cn/")[CAMET]#super[#link(<src26>)[\[26\]]]],
)

Moreover, even the MTA IBX staff have told us at IBX Open Houses that they would prefer the IBX to be automated, but that this is ultimately the MTA board and governor’s decision.
We know the MTA has been considering this already, as even 2 years ago, #link("https://bqrail.substack.com/api/v1/file/332c7174-b5cf-4d76-9462-e72ad568bdd8.pdf#page=5")[consultants presented to the MTA about driverless operations]#super[#link(<src27>)[\[27\]]]#footnote[As #link("https://bqrail.substack.com/p/interborough-express-progress-reports#:~:text=driverless%20vehicle%20operations")[FOILed]#super[#link(<src51>)[\[51\]]] by John Pegram (BQRail).
The presentation was done on 3/26/2024 by WSP, the consultant for the environmental review.] for the IBX.
More recently, they have visited REM in Montreal and the under-construction Ontario Line in Toronto #strong[\[cite\]], both of which are ALM.
Now we need those with the power to make such a decision to follow through and commit to automation.

Automation is classified in the following internationally standardized grades, each called #emph[grades of automation] (GoA) with an associated number:

- GoA0: line of sight manual operation with no signaling protection
- GoA1: manual operation with signaling that protects train safety through Automatic Train Protection (ATP)
- GoA2: automated driving: the train drives automatically under Automatic Train Operation (ATO), but the operator opens the doors, closes the doors, and presses a button to start the automatic driving until the next station
- GoA3: driverless operation (DTO): the train runs automatically, but there is an on-board attendant to operate the train in emergencies
- GoA4: unattended operation (UTO): the train runs automatically, with no crew on board except perhaps for security

#strong[\[picture of JFK AirTrain\]]

#strong[\[picture of NYC CBTC trains extremely close to each other\]]

In NYC, most subways are currently GoA1, but lines with the new communications-based train control (CBTC) signaling like the 7 and L#footnote[The Queens Boulevard Line (E/F/M/R) between 50 St/8 Av and 47-50 Sts/6 Av to Kew Gardens-Union Tpke (QBL West), in addition to the Culver Line (F) between Church Av and West 8 St, are also equipped with CBTC and are GoA2 now.] are GoA2.
The JFK AirTrain is GoA4.
MTA IBX staff have told us that the IBX will very likely use CBTC and thus be at least GoA2, but our goal is to reach GoA4.
Only GoA4 provides the operational efficiency that unlocks the frequency the IBX needs.

Moreover, because automation allows trains to run at higher frequencies relative to manual operation, trains and stations can be smaller, enabling agencies to reduce capital costs while retaining overall capacity.
For example, Italian cities have delivered incredibly cheap metro systems (#link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[\$200–400 million/mile]#super[#link(<src28>)[\[28\]]]#footnote[In Italy, where many urban subway lines have been built this century, some driverless and some not, the cost of underground station excavation has been fairly consistent at €500 per cubic meter outside the most difficult environments (such as Classical Roman sites), producing smaller driverless stations in Turin and Milan at €15 million per station and larger ones in more modern parts of Rome at €40 million.]) that run trains less than 100 meters long and build stations barely any longer than the trains.
Despite the short lengths, ALM capacity can be very high: Paris’s upcoming M15 ring line, projected to run #link("https://www.iledefrance-mobilites.fr/medias/portail-idfm/d2b73925-aa17-452d-b662-c466dbbe3e04_Journe%CC%81e-dinformation-aux-ope%CC%81rateurs-_Socie%CC%81te%CC%81-du-Grand-Paris-_-13062019.pdf#page=29")[354 ft long trains]#super[#link(<src29>)[\[29\]]], is projected to see #link("https://www.grandparisexpress.fr/ligne-15#:~:text=jour%20plus%20d%27-,1%2C5%20million,-de%20voyageurs.")[1.5 million]#super[#link(<src30>)[\[30\]]] riders a day over a length of 47 miles, which is roughly the same ridership per mile as the 1 or L.#footnote[#strong[\[cite RAPTOR results, all are around 20k/km\]]] For the IBX, the #link("https://www.mta.info/document/187036#page=20")[Draft Scoping planned for 325 ft trains]#super[#link(<src31>)[\[31\]]].
A standard ALM with 325 ft long trains that fits in the East NY Tunnel would hold about 1000 people per train,#footnote[A 4-car Alstom Metropolis Saint-Laurent as used on REM holds 780 passengers and is 76.2 m long and 2.94 m wide, small enough to fit in the East NY Tunnels.
780/76.2 m \* 325 ft = 1014 ≈ 1000.] and thus have a peak capacity of 40,000 people per hour per direction (pphpd).
This is more than any #link("https://www.nymtc.org/sites/default/files/rfp/2024%20Hub%20Bound%20Report%20%282%29.pdf#page=50")[rail crossing into Manhattan south of 60 St]#super[#link(<src32>)[\[32\]]] in 2024, and more than double the 14 St tunnel.

The ALM operating paradigm has become increasingly popular around the globe for a variety of transit needs.
For a circumferential line like the IBX, it is especially well-suited, given those lines’ extreme need for frequency discussed above.
Circumferential lines support and enable rides that are far more likely to involve transfers.
Indeed, the #link("https://ibx.transitcosts.com/ibx-1/")[largest share of new jobs made accessible to commuters by the IBX is in Manhattan]#super[#link(<src33>)[\[33\]]], where the IBX will not run, purely through better transfers between the IBX and lines that do run into Manhattan.
High frequency and reliability is especially important for facilitating transfers, since the wait between trains can make or break riders’ willingness to transfer.

Driverless operation has the unique benefit of permitting high off-peak frequency without incurring a commensurate increase in operating cost, even in smaller cities with lower possible ridership or lines with lower ridership.
Vancouver’s SkyTrain runs every 6–8 minutes off-peak on each of two branches, and the Copenhagen Metro runs every 4–6 minutes off-peak on each of two branches, and in all cases the branches separate quite far out of city center, so 3-minute frequencies are offered on a lengthy trunk.
The systems using driverless VAL#footnote[VAL is Véhicule Automatique Léger, which translates from French to light automated vehicle.] technology run every 3–6 minutes off-peak in Lille, Rennes, Toulouse, and Turin.
In contrast, the non-driverless Marseille Metro runs every 10–15 minutes.

The costs of operating ALM technology in these cities are impressively low: the Expo and Millennium Lines of SkyTrain in Vancouver #link("https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[averaged US\$8.11/car-mile in 2025]#super[#link(<src34>)[\[34\]]],#footnote[This is imputed from C\$0.064/capacity-km per p. 37, a capacity of 91.86 per p. 19, and standard US-Canada PPP conversions #link("https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[per the OECD]#super[#link(<src52>)[\[52\]]].] less than half as much as New York City Transit (NYCT), #link("https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[which averaged \$18.63]#super[#link(<src35>)[\[35\]]]#link("https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[/car-mile]#super[#link(<src34>)[\[34\]]]#link("https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[ in 2024]#super[#link(<src35>)[\[35\]]].
This is important, as 72.5% of NYCT operating costs today are labor expenditures, and about 20% of subway workers are train operators.
In contrast, #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[SkyTrain is very light on employees, and expanded service dramatically in the late 2000s with little increase in the number of workers]#super[#link(<src36>)[\[36\]]].
Similarly, WMATA estimates that automating the Red Line would #link("https://www.wmata.com/about/board/meetings/board-pdfs/upload/4C-Rail-Modernization-Program.pdf#page=28")[reduce marginal operating costs by 41%]#super[#link(<src37>)[\[37\]]]. #strong[\[explain one example about how crewing affects this\]]

This also insulates the system from fiscal pressure to cut service in order to save small amounts of money during a funding crisis.
The MTA currently plans only 5 minute peak frequencies for the IBX and even lower frequencies off-peak.
ALM can not only do better at the peak, but is more resilient to cuts off-peak that would degrade service to the point of unusability, a problem that has plagued many recently built American light rail networks coping with budget cuts.
The MTA is studying higher peak frequencies of 3 minutes #strong[\[cite, bqrail\] ]as well, which ALM would make substantially cheaper and easier.
But more importantly, it would allow the MTA to affordably maintain those 3 minute headways throughout the day instead of collapsing to 10 minutes off-peak.

#strong[\[car-mile operating costs graph NYCT vs Vancouver\]]

For the IBX, achieving these operational benefits requires a minimal upfront increase in construction costs.
Since the corridor will already be grade separated, the only remaining requirement is protecting passengers from automatically driven trains.
Existing American practice demonstrates this can be done at minimal cost, so that protection will quickly pay for itself with automation.
Furthermore, as discussed in the next section, it is also good for its own sake and so should be pursued no matter what. 

The MTA should be careful to avoid letting legacy technology and standards hold back the IBX.
It’s a new, isolated line, which gives it a chance to start fresh for once and make better choices without the legacy constraints.
Accordingly, the MTA should be careful as it reviews legacy subway standards for applicability for the IBX project, as technology has come a long way since many of these standards like the I2S signalling standard used for CBTC was created.

Platform Screen Doors

On metros globally, including NYC, the #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[largest risk to passenger safety is track intrusion]#super[#link(<src38>)[\[38\]]]: intentional and unintentional falls onto the tracks, getting pushed in front of a train, climbing on top of the train, and trash and other items falling on the tracks, which can start fires.
New Yorkers know this all too well.
In 2021, there were #link("https://www.mta.info/document/77166#page=2")[1267 track intrusions, 200 collisions, and 68 fatalities]#super[#link(<src39>)[\[39\]]].
The proven solution is to physically prevent passengers from accessing the track with platform screen doors.
NYC has played around with blue lighting for suicide prevention, lasers, and recently, platform edge fences.
These do not stop people from falling and dying, but PSDs do, and now the #link("https://ny1.com/nyc/brooklyn/transit/2025/11/22/mta-ordered-to-pay--81-7-million-to-woman-struck-by-subway-in-brooklyn")[MTA has been held liable for their failure to do so]#super[#link(<src40>)[\[40\]]].
Automation and PSDs are generally considered together, but the safety benefits of PSDs are so strong that they should be installed on the IBX regardless.

#link("https://x.com/ThoughtPolic3HQ/status/1874861375857541619/video/1")[Thought Police HQ (\@ThoughtPolic3HQ) on X: “\#UPDATE Joseph Lynskey, a 45-year-old NYC music programmer, was viciously pushed in front of a subway train, leaving him with serious injuries but stable.
The assailant, 23-year-old Kamel Hawkins, faces charges of attempted murder and assault.
Hawkins has a criminal record that…”]#super[#link(<src41>)[\[41\]]]

#figure(
  link("https://kkysen.github.io/eta-publish/reports/ibx-automation/images/img-dfdefb85.png")[#capped_image("print/img-dfdefb85.jpg", alt: "[caption]")],
  caption: [#strong[\[caption\]] \
  #link("https://commons.wikimedia.org/wiki/File:Skyline_platform_screen_doors.jpg")[Credit: Eli Fessler]#super[#link(<src42>)[\[42\]]]],
)

Honolulu provides virtually the only US example#footnote[There are numerous Automated People Movers (APMs) at airports in the US.
Every single one is automated with PSDs.
However, Honolulu Skyline is the first metro with either PSDs or GoA4 automation.] pertinent to IBX.
The #link("https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056")[PSDs for all 21 stations]#super[#link(<src43>)[\[43\]]] cost about \$27 million in 2013 USD.
Adjusted for inflation and the number of IBX stations#footnote[IBX stations are planned to be #link("https://www.mta.info/document/187036#page=20")[325 ft]#super[#link(<src31>)[\[31\]]], a bit longer than the 260 ft Hitachi Driverless Metro trains on Honolulu Skyline.
However, this is an upper bound for IBX stations, as they are just ensuring everything is built for at least 325 ft until rolling stock is selected.
The 260 ft length and 800/train capacity of Honolulu’s trains should be plenty sufficient.], equipping all IBX platforms with PSDs would cost about \$33 million#footnote[\$27 million / (21 \* 260 ft) \* (18 \* 325 ft) \* 1.431 inflation from Sep 2013 to Aug 2026 = \$33.1 million. \$5.5 billion / \$33.1 million = 0.602%.], equal to only 0.6% of its #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[projected cost of \$5.5 billion]#super[#link(<src44>)[\[44\]]].
The safety benefits of PSDs were key to this decision: Honolulu Authority for Rapid Transit board members #link("https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[swiftly approved the change order for PSDs]#super[#link(<src45>)[\[45\]]] after seeing a video of babies falling in front of trains.
The cost is only a small part of the larger project, and yet adds incredible value.
But if the MTA waits until after IBX opens, then retrofitting PSDs will grow far more expensive.

Indeed, while the cost of a new PSD in Honolulu is \$1.8 million per station in 2026 USD, the cost of a retrofit is an order of magnitude higher.
Installations in Paris and Hong Kong #strong[\[cite\]] have run over \$10 million per station, scaled to the length of an NYC Subway train.
In 2020, the MTA suggested that a systemwide retrofit would cost \$55 million per station.#footnote[On the existing NYC subway, retrofitting PSDs at every station is unfortunately very difficult.
There are issues with ADA clearance, platform edges that can’t support a PSD’s weight, different train door positions #strong[\[cite\]], and more. #strong[\[TODO finish and adapt to footnote\]]]

#strong[\[insert image of at-grade station crossing on HBLR\]]

While safety is of course critical, PSDs also bring numerous other benefits.
Track incursions are not just a safety risk; they are also abysmal for reliability.
PSDs do often add slightly to dwell time, as they are another door to close, but they pay it back in extreme reliability.
In combination with automation, running time variability becomes extremely low, allowing more runtime padding to be cut.

== High Platforms

While it is encouraging that the latest IBX renderings appear to show high-level platforms, the MTA should formally commit to high-floor vehicles.
While high-floor vehicles require straight or only gently curved platforms, the IBX right-of-way is always wide enough for them.
High floors create more space for train internals below the floor.
This yields direct benefits such as allowing passengers to circulate more easily, without wheel wells protruding through the train floor and taking up valuable space.
It historically has also led to indirect benefits of cheaper and more reliable vehicles, as the spaciousness below the platforms relaxes various engineer trade-offs.
We must note that in recent years, manufacturers have made impressive strides, and the indirect benefits no longer readily show up in the data the way they used to.
Still, the rule of thumb for rolling stock procurement is that low platforms should only be pursued for a reason, and without tight turns or street running, IBX doesn’t have such a reason.
High floors remain the good default.

Furthermore, building high platforms at the outset would greatly simplify any further capacity expansion later—practically all systems running frequent trains of the length seen on the New York City Subway (180 meters) or longer exclusively use high-floor vehicles.

- #strong[\[Reliability of high platform\]]
- #strong[\[Smaller station configuration\]]
- #strong[\[Flexibility with more seating arrangements, because wheel wells do not protrude above floor\]]
- #strong[\[High platforms discourage walking across the track — note this doesn’t matter so much with PSDs\]]

== Rolling Stock

The MTA has not yet officially made rolling stock procurement decisions.
However, the influences of earlier project phases continue to be seen.
Prior to the complete grade separation of the corridor, trains would have needed to run on city streets, and curves in this section would have been much sharper.
These factors might have justified tram-like light rail vehicles designed for this purpose.

The All Faiths Tunnel removes the need for street running.
However, the MTA is still claiming that light rail vehicles are required in order to “#link("https://ibx.mta.info/about/")[travel through tight curves]#super[#link(<src46>)[\[46\]]].”
In fact, the tightest curve on the IBX route has a #link("https://www.mta.info/document/114891#page=992")[radius of 465 ft]#super[#link(<src47>)[\[47\]]]#footnote[The IBX1 LRT-18 curve in the PEL study has a radius of 465 ft. The wider-radius (917 ft) IBX2 LRT-11 curve is for the Brooklyn Army Terminal station option further west, but the MTA has decided on the eastern option closer to 2 Av, which has the 465 ft curve radius.], so generous that any train can fit.
The tightest curve on the NYC subway has a radius of #link("https://www.mta.info/document/172206#page=6")[100±10 ft]#super[#link(<src48>)[\[48\]]]#footnote[We’re not sure where the ~100 ft curve is, but the old South Ferry loop is close (110 ft) and is still in occasional revenue service.
Other tighter curves may be in yard trackage.], with the #link("https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[old South Ferry loop being 111 ft]#super[#link(<src49>)[\[49\]]].
Even the Metro in Washington, DC, designed to avoid the squeal of the tight curves of the oldest sections of the New York City Subway, has a #link("https://www.wmata.com/business/procurement/solicitations/documents/General%20Design%20Criteria%20-%208K%202017%2001%2024.pdf#page=4")[minimum curve radius of 225 ft]#super[#link(<src6>)[\[6\]]], less than half of that of the IBX.
The only tight curves were the #link("https://www.mta.info/document/114891#page=1014")[100 ft street-running curves]#super[#link(<src50>)[\[50\]]]#footnote[In the former street-running section, there were multiple 100 ft curves: IBX1 LRT-647, IBX1 LRT-661, IBX2 LRT641, IBX2 LRT656.] that have since been removed with the All Faiths tunnel.

LRVs are optimized for street-running lines, or lines that are at least partly street-running.
On fully grade-separated corridors, they are weaker: for example, the vehicles are short, and at the scale expected for IBX several would need to be coupled, wasting space that on an ALM train would be carrying passengers.

In contrast to ALMs, light rail systems in the US often force passengers to cross the tracks to get to the opposite-side platform, even when they run in private rights-of-way and not on the street.
For example, Boston’s Green Line Extension designed Ball Square and East Somerville to require crossing the live tracks at-grade, as a last-minute cost-saving measure.
Similarly, Jersey City’s Hudson-Bergen Light Rail (HBLR) does that at many stations such as Newport, Harsimus Cove, and Jersey Avenue.
This is not acceptable for an ALM system, which requires higher levels of safety as a driver cannot operate the train by sight.
Even without automation, pedestrian grade crossings at stations would force trains to enter those stations at reduced speed, driving up runtimes.
The MTA’s commendable 32 minute runtime target, for example, would be difficult to meet if grade crossings for passengers were built.

Hopefully this is a case where the public-facing website was not updated with the latest planning.
The alternatives are far worse: either good right-of-way decisions are not percolating over to rolling stock procurement, or the MTA is simply making the right decision without understanding the deeper reasons #emph[why] full grade separation is the right decision.

== Conclusion

IBX provides an excellent opportunity to import the ALM concept firmly into the MTA from preexisting examples such as the Montréal REM or the JFK Airtrain.
ALM stands to reinforce the benefits to Queens and Brooklyn that the already strong IBX project would deliver.
In addition to the immense benefits for IBX itself, it would serve as a proof-of-concept for, and facilitate maintenance and acquisition economies of scale with, potential future ALM systems on other corridors, such as in outer Queens and Brooklyn, across the Bronx, or potentially New Jersey.

We know the MTA has listened to us before about the IBX.
After we discovered that, in the #link("https://www.mta.info/document/114891")[IBX’s Planning and Environmental Linkages (PEL) study]#super[#link(<src10>)[\[10\]]], peak ridership was #link("https://www.etany.org/ibx-all-faiths-tunnel#:~:text=exceed%20the%20maximum%20capacity")[already above the maximum capacity] of street-running LRT, rendering street-running LRT infeasible, and then #link("https://www.etany.org/ibx-all-faiths-tunnel")[pushed for an All Faiths tunnel], the #link("https://www.youtube.com/watch?v=HEfH7R6j6QY")[MTA announced the tunnel]#super[#link(<src3>)[\[3\]]].
After we suggested in the Draft Scoping Public Comment that the IBX should consider 1500 V DC catenary, not just 750 V, in order to reduce the number of substations and thus takings needed, the MTA studied it and has shifted to planning for 1500 V DC.
We hope the MTA will continue to recognize the merits of our suggestions and build the IBX as ALM: fully automated with PSDs and high-floor light metro rolling stock.

= Sources

+ #link("https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out] (archived #link("https://web.archive.org/web/20260910231933/https://gothamist.com/news/new-renderings-of-the-mtas-ibx-project-serving-brooklyn-queens-are-out")[September 10, 2026]) <src1>
+ #link("https://ibx.mta.info/#:~:text=anticipated%20release%20in-,late%202026,-)")[https://ibx.mta.info/\#:~:text=anticipated%20release%20in-,late%202026,-)] (archived #link("https://web.archive.org/web/20261004181426/https://ibx.mta.info/#:~:text=anticipated%20release%20in-,late%202026,-)")[October 4, 2026]) <src2>
+ #link("https://www.youtube.com/watch?v=HEfH7R6j6QY")[https://www.youtube.com/watch?v=HEfH7R6j6QY] (archived #link("https://web.archive.org/web/20241213120427/https://www.youtube.com/watch?v=HEfH7R6j6QY")[December 13, 2024]) <src3>
+ #link("https://www.youtube.com/live/HEfH7R6j6QY?t=911s")[https://www.youtube.com/live/HEfH7R6j6QY?t=911s] (archived #link("https://web.archive.org/web/20261009033625/https://www.youtube.com/live/HEfH7R6j6QY?t=911s")[October 9, 2026]) <src4>
+ #link("https://ibx.mta.info/about/#:~:text=to%20travel%20through-,tight%20curves,-Fit%20through%20the")[https://ibx.mta.info/about/\#:~:text=to%20travel%20through-,tight%20curves,-Fit%20through%20the] (archived #link("https://web.archive.org/web/20260921162613/https://ibx.mta.info/about/#:~:text=to%20travel%20through-,tight%20curves,-Fit%20through%20the")[September 21, 2026]) <src5>
+ #link("https://www.wmata.com/business/procurement/solicitations/documents/General%20Design%20Criteria%20-%208K%202017%2001%2024.pdf#page=4")[https://www.wmata.com/business/procurement/solicitations/documents/General%20Design%20Criteria%20-%208K%202017%2001%2024.pdf\#page=4] (archived #link("https://web.archive.org/web/20221022205203id_/https://www.wmata.com/business/procurement/solicitations/documents/General%20Design%20Criteria%20-%208K%202017%2001%2024.pdf#page=4")[October 22, 2022]) <src6>
+ #link("https://www.mta.info/document/72081#page=16")[https://www.mta.info/document/72081\#page=16] (archived #link("https://web.archive.org/web/20260518002035id_/https://www.mta.info/document/72081#page=16")[May 18, 2026]) <src7>
+ #link("https://www.mta.info/document/72081")[https://www.mta.info/document/72081] (archived #link("https://web.archive.org/web/20260518002035/https://www.mta.info/document/72081")[May 18, 2026]) <src8>
+ #link("https://www.mta.info/document/103691#page=5")[https://www.mta.info/document/103691\#page=5] (archived #link("https://web.archive.org/web/20260518002014id_/https://www.mta.info/document/103691#page=5")[May 18, 2026]) <src9>
+ #link("https://www.mta.info/document/114891")[https://www.mta.info/document/114891] (archived #link("https://web.archive.org/web/20260518002024/https://www.mta.info/document/114891")[May 18, 2026]) <src10>
+ #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up] (archived #link("https://web.archive.org/web/20260829123215/https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[August 29, 2026]) <src11>
+ #link("https://anita.garden/nycriders/")[https://anita.garden/nycriders/] (archived #link("https://web.archive.org/web/20260822120542/https://anita.garden/nycriders/")[August 22, 2026]) <src12>
+ #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml\#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily] (archived #link("https://web.archive.org/web/20260912070442/https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[September 12, 2026]) <src13>
+ #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes] (archived #link("https://web.archive.org/web/20260518022508/https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[May 18, 2026]) <src14>
+ #link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/] (archived #link("https://web.archive.org/web/20260719213805/https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[July 19, 2026]) <src15>
+ #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/] (archived #link("https://web.archive.org/web/20260513035917/https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[May 13, 2026]) <src16>
+ #link("https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park] (archived #link("https://web.archive.org/web/20260902012928/https://gothamist.com/news/mamdani-eyes-sweeping-housing-plan-for-blocks-south-of-brooklyns-prospect-park")[September 2, 2026]) <src17>
+ #link("https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi] (archived #link("https://web.archive.org/web/20260918152353/https://www.nyc.gov/mayors-office/news/2026/05/mamdani-administration-advances-first-neighborhood-plans-for-whi")[September 18, 2026]) <src18>
+ #link("https://arxiv.org/abs/2408.01562")[https://arxiv.org/abs/2408.01562] (archived #link("https://web.archive.org/web/20260416140808/https://arxiv.org/abs/2408.01562")[April 16, 2026]) <src19>
+ #link("https://www.transit.dot.gov/funding/grant-programs/capital-investments/stops")[https://www.transit.dot.gov/funding/grant-programs/capital-investments/stops] (archived #link("https://web.archive.org/web/20260512184009/https://www.transit.dot.gov/funding/grant-programs/capital-investments/stops")[May 12, 2026]) <src20>
+ #link("https://www.governor.ny.gov/news/governor-hochul-and-mta-announce-second-avenue-subway-phase-2-moves-forward#:~:text=carried%20more%20than-,200%2C000,-passengers%20on%20a")[https://www.governor.ny.gov/news/governor-hochul-and-mta-announce-second-avenue-subway-phase-2-moves-forward\#:~:text=carried%20more%20than-,200%2C000,-passengers%20on%20a] (archived #link("https://web.archive.org/web/20260223051453/https://www.governor.ny.gov/news/governor-hochul-and-mta-announce-second-avenue-subway-phase-2-moves-forward#:~:text=carried%20more%20than-,200%2C000,-passengers%20on%20a")[February 23, 2026]) <src21>
+ #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/] (archived #link("https://web.archive.org/web/20260515114508/https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[May 15, 2026]) <src22>
+ #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html] (archived #link("https://web.archive.org/web/20250828081856/http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[August 28, 2025]) <src23>
+ #link("https://github.com/kkysen/automated-metro-data")[https://github.com/kkysen/automated-metro-data] (archived #link("https://web.archive.org/web/20261009033813/https://github.com/kkysen/automated-metro-data")[October 9, 2026]) <src24>
+ #link("https://www.urbanrail.net/news.htm")[https://www.urbanrail.net/news.htm] (archived #link("https://web.archive.org/web/20261005121320/https://www.urbanrail.net/news.htm")[October 5, 2026]) <src25>
+ #link("https://www.camet.org.cn/")[https://www.camet.org.cn/] (archived #link("https://web.archive.org/web/20260609080936/https://www.camet.org.cn/")[June 9, 2026]) <src26>
+ #link("https://bqrail.substack.com/api/v1/file/332c7174-b5cf-4d76-9462-e72ad568bdd8.pdf#page=5")[https://bqrail.substack.com/api/v1/file/332c7174-b5cf-4d76-9462-e72ad568bdd8.pdf\#page=5] (archived #link("https://web.archive.org/web/20240921120558id_/https://bqrail.substack.com/api/v1/file/332c7174-b5cf-4d76-9462-e72ad568bdd8.pdf#page=5")[September 21, 2024]) <src27>
+ #link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf] (archived #link("https://web.archive.org/web/20260512184237/https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[May 12, 2026]) <src28>
+ #link("https://www.iledefrance-mobilites.fr/medias/portail-idfm/d2b73925-aa17-452d-b662-c466dbbe3e04_Journe%CC%81e-dinformation-aux-ope%CC%81rateurs-_Socie%CC%81te%CC%81-du-Grand-Paris-_-13062019.pdf#page=29")[https://www.iledefrance-mobilites.fr/medias/portail-idfm/d2b73925-aa17-452d-b662-c466dbbe3e04\_Journe%CC%81e-dinformation-aux-ope%CC%81rateurs-\_Socie%CC%81te%CC%81-du-Grand-Paris-\_-13062019.pdf\#page=29] (archived #link("https://web.archive.org/web/20260406153437id_/https://www.iledefrance-mobilites.fr/medias/portail-idfm/d2b73925-aa17-452d-b662-c466dbbe3e04_Journe%CC%81e-dinformation-aux-ope%CC%81rateurs-_Socie%CC%81te%CC%81-du-Grand-Paris-_-13062019.pdf#page=29")[April 6, 2026]) <src29>
+ #link("https://www.grandparisexpress.fr/ligne-15#:~:text=jour%20plus%20d%27-,1%2C5%20million,-de%20voyageurs.")[https://www.grandparisexpress.fr/ligne-15\#:~:text=jour%20plus%20d%27-,1%2C5%20million,-de%20voyageurs.] (archived #link("https://web.archive.org/web/20260313040341/https://www.grandparisexpress.fr/ligne-15#:~:text=jour%20plus%20d%27-,1%2C5%20million,-de%20voyageurs.")[March 13, 2026]) <src30>
+ #link("https://www.mta.info/document/187036#page=20")[https://www.mta.info/document/187036\#page=20] (archived #link("https://web.archive.org/web/20260920230007id_/https://www.mta.info/document/187036#page=20")[September 20, 2026]) <src31>
+ #link("https://www.nymtc.org/sites/default/files/rfp/2024%20Hub%20Bound%20Report%20%282%29.pdf#page=50")[https://www.nymtc.org/sites/default/files/rfp/2024%20Hub%20Bound%20Report%20%282%29.pdf\#page=50] (archived #link("https://web.archive.org/web/20261009033606id_/https://www.nymtc.org/sites/default/files/rfp/2024%20Hub%20Bound%20Report%20%282%29.pdf#page=50")[October 9, 2026]) <src32>
+ #link("https://ibx.transitcosts.com/ibx-1/")[https://ibx.transitcosts.com/ibx-1/] (archived #link("https://web.archive.org/web/20260512184007/https://ibx.transitcosts.com/ibx-1/")[May 12, 2026]) <src33>
+ #link("https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly\_reports/2025/2025-q2-financial-and-performance-report.pdf] (archived #link("https://web.archive.org/web/20260215035655/https://www.translink.ca/-/media/translink/documents/about-translink/corporate-reports/quarterly_reports/2025/2025-q2-financial-and-performance-report.pdf")[February 15, 2026]) <src34>
+ #link("https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[https://www.transit.dot.gov/sites/fta.dot.gov/files/transit\_agency\_profile\_doc/2024/20008.pdf] (archived #link("https://web.archive.org/web/20260910171300/https://www.transit.dot.gov/sites/fta.dot.gov/files/transit_agency_profile_doc/2024/20008.pdf")[September 10, 2026]) <src35>
+ #link("http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[http://www.th.gov.bc.ca/publications/reports\_and\_studies/Review\_of\_TransLink.pdf] (archived #link("https://web.archive.org/web/20130515042955/http://www.th.gov.bc.ca/publications/reports_and_studies/Review_of_TransLink.pdf")[May 15, 2013]) <src36>
+ #link("https://www.wmata.com/about/board/meetings/board-pdfs/upload/4C-Rail-Modernization-Program.pdf#page=28")[https://www.wmata.com/about/board/meetings/board-pdfs/upload/4C-Rail-Modernization-Program.pdf\#page=28] (archived #link("https://web.archive.org/web/20260423181419id_/https://www.wmata.com/about/board/meetings/board-pdfs/upload/4C-Rail-Modernization-Program.pdf#page=28")[April 23, 2026]) <src37>
+ #link("https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/] (archived #link("https://web.archive.org/web/20260422232822/https://communityofmetros.org/research-enhancing-platform-safety-without-platform-doors/")[April 22, 2026]) <src38>
+ #link("https://www.mta.info/document/77166#page=2")[https://www.mta.info/document/77166\#page=2] (archived #link("https://web.archive.org/web/20260518163429id_/https://www.mta.info/document/77166#page=2")[May 18, 2026]) <src39>
+ #link("https://ny1.com/nyc/brooklyn/transit/2025/11/22/mta-ordered-to-pay--81-7-million-to-woman-struck-by-subway-in-brooklyn")[https://ny1.com/nyc/brooklyn/transit/2025/11/22/mta-ordered-to-pay--81-7-million-to-woman-struck-by-subway-in-brooklyn] (archived #link("https://web.archive.org/web/20260708134117/https://ny1.com/nyc/brooklyn/transit/2025/11/22/mta-ordered-to-pay--81-7-million-to-woman-struck-by-subway-in-brooklyn")[July 8, 2026]) <src40>
+ #link("https://x.com/ThoughtPolic3HQ/status/1874861375857541619/video/1")[https://x.com/ThoughtPolic3HQ/status/1874861375857541619/video/1] (not archived: error:blocked-url) <src41>
+ #link("https://commons.wikimedia.org/wiki/File:Skyline_platform_screen_doors.jpg")[https://commons.wikimedia.org/wiki/File:Skyline\_platform\_screen\_doors.jpg] (archived #link("https://web.archive.org/web/20251205134012/https://commons.wikimedia.org/wiki/File:Skyline_platform_screen_doors.jpg")[December 5, 2025]) <src42>
+ #link("https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056")[https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056] (archived #link("https://web.archive.org/web/20261009033703/https://myemail.constantcontact.com/News-from-the-Honolulu-Rail-Transit-Project.html?aid=Hx5Y3V3IrQE&soid=1102697428056")[October 9, 2026]) <src43>
+ #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review] (archived #link("https://web.archive.org/web/20260914114804/https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-project-design-and-environmental-review")[September 14, 2026]) <src44>
+ #link("https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/] (archived #link("https://web.archive.org/web/20180704003258/https://www.civilbeat.org/2013/09/19830-honolulu-rails-new-27-million-safety-feature-to-avert-track-fatalities/")[July 4, 2018]) <src45>
+ #link("https://ibx.mta.info/about/")[https://ibx.mta.info/about/] (archived #link("https://web.archive.org/web/20260921162613/https://ibx.mta.info/about/")[September 21, 2026]) <src46>
+ #link("https://www.mta.info/document/114891#page=992")[https://www.mta.info/document/114891\#page=992] (archived #link("https://web.archive.org/web/20260518002024id_/https://www.mta.info/document/114891#page=992")[May 18, 2026]) <src47>
+ #link("https://www.mta.info/document/172206#page=6")[https://www.mta.info/document/172206\#page=6] (archived #link("https://web.archive.org/web/20260519070421id_/https://www.mta.info/document/172206#page=6")[May 19, 2026]) <src48>
+ #link("https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[https://www.nycsubway.org/wiki/Chapter\_03.\_General\_Arrangement\_for\_Construction\#:~:text=150-,South%20Ferry%20loop,-111] (archived #link("https://web.archive.org/web/20251205012113/https://www.nycsubway.org/wiki/Chapter_03._General_Arrangement_for_Construction#:~:text=150-,South%20Ferry%20loop,-111")[December 5, 2025]) <src49>
+ #link("https://www.mta.info/document/114891#page=1014")[https://www.mta.info/document/114891\#page=1014] (archived #link("https://web.archive.org/web/20260518002024id_/https://www.mta.info/document/114891#page=1014")[May 18, 2026]) <src50>
+ #link("https://bqrail.substack.com/p/interborough-express-progress-reports#:~:text=driverless%20vehicle%20operations")[https://bqrail.substack.com/p/interborough-express-progress-reports\#:~:text=driverless%20vehicle%20operations] (archived #link("https://web.archive.org/web/20260304064215/https://bqrail.substack.com/p/interborough-express-progress-reports#:~:text=driverless%20vehicle%20operations")[March 4, 2026]) <src51>
+ #link("https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[https://data-explorer.oecd.org/vis?df\[ds\]=dsDisseminateFinalDMZ&df\[id\]=DSD\_NAMAIN10%40DF\_TABLE4&df\[ag\]=OECD.SDD.NAD&df\[vs\]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP\_B1GQ.......&lom=LASTNPERIODS&lo=10&to\[TIME\_PERIOD\]=false&ly\[cl\]=TIME\_PERIOD&ly\[rw\]=REF\_AREA,COMBINED\_UNIT\_MEASURE&vw=tb] (archived #link("https://web.archive.org/web/20260313233214/https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NAMAIN10%40DF_TABLE4&df[ag]=OECD.SDD.NAD&df[vs]=2.0&dq=A.AUS%2BAUT%2BBEL%2BCAN%2BCHL%2BCOL%2BCRI%2BCZE%2BDNK%2BEST%2BFIN%2BFRA%2BDEU%2BGRC%2BHUN%2BISL%2BIRL%2BISR%2BITA%2BJPN%2BKOR%2BLVA%2BLTU%2BLUX%2BMEX%2BNLD%2BNZL%2BNOR%2BPOL%2BPRT%2BSVK%2BSVN%2BESP%2BSWE%2BCHE%2BTUR%2BGBR%2BUSA...PPP_B1GQ.......&lom=LASTNPERIODS&lo=10&to[TIME_PERIOD]=false&ly[cl]=TIME_PERIOD&ly[rw]=REF_AREA,COMBINED_UNIT_MEASURE&vw=tb")[March 13, 2026]) <src52>
