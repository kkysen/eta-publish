#import "template.typ": capped_image, report

#show: report.with(
  title: "No Need to Wait: Automated Light Metro is Right for the IBX",
  short: "",
  phase: "Composition",
  dateline: "",
  contributors: ("dariusj@etany.org", "Madison Feinberg", "Robert Hale", "Alon Levy", "Khyber Sen", "Franklin Tang", ),
  contributors_note: "We wish to acknowledge the following ETA members who contributed to this report, and without whose hard work it would not be possible:",
  warnings: (
    [dropped a line before the #raw("Header") section: #raw("IBX Automation")],
    [the #raw("Header") section has an unrecognized #raw("Before:") line; check it for a typo],
    [unfinished text in the document: #raw("Caption: TODO")],
    [unfinished text in the document: #raw("On the IBX, in contrast, light rail has little cost advantages, and in fact may ")],
    [the image #raw("img-e3ef182e") has no #raw("Credit:") line],
    [1 image is unnamed, so each publishes under a hash; give each a #raw("Source:") line naming its file:#list([#raw("img-e3ef182e"): Caption: TODO], )],
    [5 suggestions still open on this tab; the build publishes the document without them, as it reads today],
    [7 comment threads still open on this tab],
    [the #raw("Header") section has no #raw("Publish Due Date:") line],
    [the #raw("Header") section has no #raw("Short:") line],
    [the #raw("Header") section has no #raw("SEO Description:") line],
    [style: #raw("5-minute") should be #raw("5-min"): #raw("...time and the currently stated 5-minute peak headways. If peak headwa...")],
    [style: #raw("2 minutes") should be #raw("2 min"): #raw("... peak headways are reduced to 2 minutes instead, with off-peak headwa...")],
    [style: #raw("3 minutes") should be #raw("3 min"): #raw("...ff-peak headways ranging from 3 minutes midday to 5 minutes in the ev...")],
    [style: #raw("5 minutes") should be #raw("5 min"): #raw("...ging from 3 minutes midday to 5 minutes in the evening, ridership ris...")],
    [style: #raw("5-minute") should be #raw("5 min"), with no hyphen: #raw("...time and the currently stated 5-minute peak headways. If peak headwa...")],
    [style: #raw("90 seconds") should be #raw("90 sec"): #raw("...ways could go as low as every 90 seconds, as seen in existing systems ...")],
    [style: a dash is written with a space beside it, and the house style closes it up: #raw("...ibly cheap metro systems ($200 – 300 million/mile) that run tr...")],
    [style: #raw("2 minutes") should be #raw("2 min"): #raw("...t high frequency, often every 2 minutes. Automation eliminates the la...")],
    [style: #raw("100 meters") should be #raw("100 m"): #raw("...le) that run trains less than 100 meters long and build stations barel...")],
    [style: #raw("8 minutes") should be #raw("8 min"): #raw("...ership. SkyTrain runs every 6-8 minutes off-peak on each of two branc...")],
    [style: #raw("6 minutes") should be #raw("6 min"): #raw("...Copenhagen Metro runs every 4-6 minutes off-peak on each of two branc...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("6 minutes") should be #raw("6 min"): #raw("...ss VAL technology run every 3-6 minutes off-peak in Lille, Rennes, To...")],
    [style: #raw("15 minutes") should be #raw("15 min"): #raw("...Marseille Metro runs every 10-15 minutes.")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...f city center, offering about 3-minute frequencies on a lengthy trun...")],
    [style: #raw("72.5 percent") should be #raw("72.5%"): #raw("...ency and ridership increases. 72.5 percent of NYCT operating costs today...")],
    [style: #raw("5-minute") should be #raw("5-min"): #raw("...ously publicly planned around 5-minute peak frequencies, and has con...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...equencies, and has considered 3-minute peak frequencies. Automated o...")],
    [style: #raw("3-minute") should be #raw("3-min"): #raw("...instead permit, at a minimum, 3-minute peak and 6-minute off-peak se...")],
    [style: #raw("6-minute") should be #raw("6-min"): #raw("... a minimum, 3-minute peak and 6-minute off-peak service, increasing ...")],
    [style: #raw("5-minute") should be #raw("5 min"), with no hyphen: #raw("...ously publicly planned around 5-minute peak frequencies, and has con...")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...equencies, and has considered 3-minute peak frequencies. Automated o...")],
    [style: #raw("3-minute") should be #raw("3 min"), with no hyphen: #raw("...instead permit, at a minimum, 3-minute peak and 6-minute off-peak se...")],
    [style: #raw("6-minute") should be #raw("6 min"), with no hyphen: #raw("... a minimum, 3-minute peak and 6-minute off-peak service, increasing ...")],
    [style: #raw("Fordham Road") should be #raw("Fordham Rd"): #raw("...ircumferential routes such as Fordham Road in the Bronx and Main Street ...")],
    [style: #raw("Main Street") should be #raw("Main St"): #raw("...Fordham Road in the Bronx and Main Street in Queens are appropriate to ...")],
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

#emph[The MTA recently released new renderings of the IBX.
They appear to show high-level trains and platforms, an excellent decision if accurate.
The canopies and station entrances look very sleek and modern, but the stations are missing one crucial thing: platform screen doors (PSDs), which are now the standard for new build metro lines across the world.
Moreover, this once again indicates that MTA remains hesitant to commit to automating the IBX.]

== Draft Environmental Impact Statement looming

Now is the time to decide how the IBX should be built.
Later this fall, the MTA is slated to release the draft environmental impact statement for the IBX.
The public response to that will be one of the last times to shape the broadest contours of the project design, as the final environmental impact statement will lock in major decisions.

We’ve had some 

After the decision to tunnel under the All Faiths Cemetery, the IBX right-of-way will already be completely grade-separated, significantly improving the levels of system reliability possible to achieve.

== Rising Ridership

Projections for the ridership of the IBX have steadily risen as plans materialize and improve.
Ridership projections have risen 84%#footnote[(160,000/day) / (87,800/day) = 1.839], all the way from #link("https://www.mta.info/document/72081#page=16")[87,800/day]#super[#link(<src2>)[\[2\]]] in the #link("https://www.mta.info/document/72081")[initial feasibility study in 2022]#super[#link(<src3>)[\[3\]]] to #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[160,000/day]#super[#link(<src4>)[\[4\]]] in the more detailed and higher-speed 2025 design, higher than both the #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[BQE (130k/day)]#super[#link(<src5>)[\[5\]]] and #link("https://anita.garden/nycriders/")[G train (148k/day)]#super[#link(<src6>)[\[6\]]], which also connect Brooklyn and Queens.
This has been driven by all of the following factors:

- Refinement of the ridership model as more details have been decided
- Improved station locations
- A #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[31% reduction in runtime]#super[#link(<src7>)[\[7\]]] after #link("https://www.etany.org/ibx-all-faiths-tunnel")[ETA successfully pressured the MTA to drop street running] around All Faiths Cemetery#footnote[#link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/]#super[#link(<src19>)[\[19\]]] #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/]#super[#link(<src20>)[\[20\]]]]

An independent study by #link("https://arxiv.org/abs/2408.01562")[Yang et al]#super[#link(<src8>)[\[8\]]] found that the maximum ridership, barring land-use changes, should be 254k riders/day.
Another independent study by Tang at NYU Marron using the FTA’s STOPS ridership modeling software#footnote[STOPS depends on extensive calibration with existing ridership, which includes statistics like per-platform ridership, which the MTA does not make available.
Thus, there is a limit to its accuracy.
But the fact that it found a very similar number to the MTA’s closed-source Regional Transit Forecasting Model (RTFM) bodes well, and it also quite accurately predicted SAS Phase 1 ridership.
Including detailed ridership in open data would enable more accurate independent analyses confirming higher ridership potential.] found the same 160k figure, albeit with the old runtime and the currently stated 5-minute peak headways.
If peak headways are reduced to 2 minutes instead, with off-peak headways ranging from 3 minutes midday to 5 minutes in the evening, ridership rises to 200k.
Combined with the recent trip time reductions, this could climb even higher, putting the IBX even above the Second Avenue Subway’s Phase 1, which saw about 200k daily riders as well.

Ridership could rise even further with additional transit-oriented development (TOD) beyond current conditions.
All studies above look purely at present-day land use, as the FTA forbids the use of promises of future upzoning in ridership analysis.
However, the Mamdani administration is interested in extending City of Yes upzoning to IBX, and ongoing analysis by Ensari at Marron is finding that a large number of additional housing units could be built profitably in the area if current programs were extended and IBX were built.

It is imperative that the IBX be future-proofed for much higher ridership in the future.
Luckily, there is a cost-effective solution to this that will also deliver unparalleled service to riders.

== Automated Light Metro

Automated light metro technology would enable the IBX to feature significantly higher frequencies from day one by lowering operating costs.
It would also allow for future ridership growth by enabling raising frequencies to the point that headways could go as low as every 90 seconds, as seen in existing systems today internationally.

Modern metro technology increasingly runs automatically.
This is classified in the following grades of automation (GoA):

- GoA1: manual operation
- GoA2: automated driving: the train drives automatically, but the operator opens the doors, closes the doors, and presses a button to start the automatic driving until the next station
- GoA3: driverless operation: the train runs automatically, but there is an on-board attendant to operate the train in emergencies
- GoA4: unattended operation: the train runs automatically, with no crew on board except perhaps for security

New subway lines in developed and even middle-income countries are usually driverless in the sense of GoA 4, unless they are extensions of older lines.
The technology is mature enough that the additional capital costs of systems are lower than the lifetime labor costs of drivers.

Automated light metro (ALM) systems have become popular worldwide.
These systems run short, driverless trains at high frequency, often every 2 minutes.
Automation eliminates the largest cost of operating a metro system: onboard personnel while using systems like platform screen doors and cameras to keep people safe.
Shrinking the station sizes minimizes capital costs.
Small and medium cities in Italy have delivered incredibly cheap metro systems (\$200 – 300 million/mile) that run trains less than 100 meters long and build stations barely any longer than the trains.#footnote[#link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf]#super[#link(<src21>)[\[21\]]]] 

ALM is an intermediate-capacity system.
It relies on a combination of short trains to allow cheap underground station construction and driverless trains to allow the very high frequency required for sufficient throughput.
On IBX, most stations will be above ground, so any cost savings from shortening platform length will be lesser, but still present in reducing material costs.
For the one underground station planned at Atlantic Av, shortening the platform and thus reducing the dig volume may be more significant where existing MTA practices lead to stations costing around 75% of overall hard underground construction costs.
On IBX, most stations will be above ground, so any cost savings from shortening platform length will be lesser, but still present in reducing material costs.
For the one underground station planned at Atlantic Av, shortening the platform and thus reducing the dig volume may be more significant where existing MTA practices lead to stations costing around 75% of overall hard underground construction costs.

The core value of driverless operation is that it permits high off-peak frequency, even in smaller cities with lower possible ridership or lines with lower ridership.
SkyTrain runs every 6-8 minutes off-peak on each of two branches, and the Copenhagen Metro runs every 4-6 minutes off-peak on each of two branches, and in all cases the branches separate quite far out of city center, offering about 3-minute frequencies on a lengthy trunk.
The systems using driverless VAL technology run every 3-6 minutes off-peak in Lille, Rennes, Toulouse, and Turin; in contrast, the non-driverless Marseille Metro runs every 10-15 minutes.

Thus, the earliest adopters of the technology have historically been smaller cities, which looked for medium capacity at low cost while still maintaining the high speed of a fully grade-separated metro system.
Larger cities have more recently started applying ALM technology on lines that do not expect to have ridership that warrants metro or regional rail.
In all cases, the comparison is not with a conventional subway, but with a light rail system.
A conventional subway on such routes is usually rejected because it would be overkill for the expected ridership.

The tradeoff between light rail (which has a driver) and ALM is generally that light rail is cheaper if it can be done on the street in dedicated lanes, but ALM offers the higher speed of a subway, much lower operating costs due to driverless operations, and, because of those low costs, high frequency all day.
The cost increase stemming from complete grade separation is defrayed by shrinking the footprint of the stations.#footnote[In Italy, where many urban subway lines have been built this century, some driverless and some not, the cost of station construction has been fairly consistent at €500 per cubic meter outside the most difficult environments (such as Classical Roman sites), producing smaller driverless stations in Turin and Milan at €15 million per station and larger ones in more modern parts of Rome at €40 million.\# Nonetheless, with soft costs included, the construction cost of ALM is about four to five times as high as that of on-street tramways.]

On the IBX, in contrast, light rail has little cost advantages, and in fact may be more expensive.
After the decision to tunnel under the All Faiths Cemetery, the IBX right-of-way will already be completely grade-separated, significantly improving the levels of system reliability possible to achieve.
As a result, however, the light rail mode thus does not save on grade separation costs, as it would have in earlier project designs.
Thus, the implementation of ALM only requires the installation of a CBTC signaling system, like those used on the subway, enabling automated operation.
Since CBTC is the MTA’s choice of signaling technology on the subway moving forward, maintaining this choice on the IBX enables economies of scale with existing expertise and industry relationships.
It also usually includes installing platform screen doors, which are discussed more in TODO.
These requirements are defrayed by the shorter platform lengths enabled by improving system throughput by enabling higher frequencies. 

As the costs for opting for ALM technology are very low or even negative, it would be a missed opportunity to forgo the operational cost decreases and frequency and ridership increases.
72.5 percent of NYCT operating costs today are labor expenditures.
Not all of this goes to onboard train staff, since other roles, like maintenance, are also critical to operate the system.
Nonetheless, about one-third to two-fifths of subway personnel operate trains.
As a ballpark estimate, avoiding the need to hire operators would reduce long-term operating costs by about 25%, enabling additional frequency at no extra cost.
Future frequency improvements serving higher potential ridership would be even cheaper by reducing marginal operating costs.
This would also insulate the system from further operational cost increases due to potential legislative requirements to increase staffing levels, a threat that the subway system’s shuttles currently face.

Meanwhile, in terms of frequency, the MTA has previously publicly planned around 5-minute peak frequencies, and has considered 3-minute peak frequencies.
Automated operations would instead permit, at a minimum, 3-minute peak and 6-minute off-peak service, increasing system ridership and overall value to regional mobility.

Elsewhere in New York, ALM may be appropriate on other lines that have no expectation of more than 15,000-25,000 passengers per hour per direction, and that do not make sense as short extensions of existing subway lines.
Circumferential routes such as Fordham Road in the Bronx and Main Street in Queens are appropriate to study for this technology.
These routes have never been studied as rail routes, because light rail may be too slow for their needs and a full-size subway too expensive.
The IBX offers the best testing ground for expanding the use of ALM as an enabling technology for lower-cost and higher-quality transit construction technology.
The IBX thus has the potential to open the door to more interborough connectivity in the future.

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
And then high reliability means#footnote[#link("https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[https://en.wikipedia.org/wiki/Automatic\_train\_operation\#Accidents\_and\_incidents\_involving\_ATO]#super[#link(<src22>)[\[22\]]]] schedule padding can be reduced, further cutting runtimes.

== Light Metro

While a light metro can be as small and limited as an airport’s people mover system, it can also be as large as the #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[narrow 6B trains]#super[#link(<src9>)[\[9\]]] serving Guangzhou Metro Line 3, which carried #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[2.76 million riders a day]#super[#link(<src10>)[\[10\]]] in 2019 and is perhaps the busiest metro line in the world.#footnote[As far as we are aware, the only rapid transit lines that carry more riders per day are Tokyo’s Yamanote Line (~5 million/day) and Mumbai Suburban Railway’s Western Line (~3 million/day).
However, both are technically mainline rail lines, and Mumbai’s Western Line is quad-tracked for much of its length.]

=== Off-the-shelf rolling stock

Importantly, the MTA has its pick of makers for standardized light metro railcars and seems intent on selecting an off-the-shelf design.
If it follows through, it would, happily, break a trend of insisting carmakers comply with exacting standards, which started back in 1977 in the wake of the #link("https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[R46 truck-cracking debacle]#super[#link(<src11>)[\[11\]]].
As we have#link("https://www.etany.org/a-not-so-capital-plan-1-most-expensive-subway-train")[ ]#link("https://www.etany.org/a-not-so-capital-plan-1-most-expensive-subway-train")[chronicled], trusting experienced firms to meet their needs is what most other transit agencies do, and it is a major reason why they have generally beaten out New York City on subway costs, especially as of late.

=== High platforms

To really seal the IBX’s fate as a transit project, the MTA needs to commit to high-floor vehicles.
While high-floor vehicles require straight or only gently curved platforms, the IBX right-of-way is generally wide enough for them.
High-floor vehicles are generally cheaper than low-floor ones, and passengers can circulate more easily in the former than in the latter where wheel wells take up valuable floor space.
Furthermore, building high platforms at the outset would greatly simplify any further capacity expansion later—practically all systems running frequent trains of the length seen on the New York City Subway (180 meters) or longer exclusively use high-floor vehicles.

== Conclusion

IBX provides an excellent opportunity to import the ALM concept firmly into the MTA from preexisting examples such as the Montréal REM or the JFK Airtrain.
In addition to the immense benefits for IBX itself, it would serve as a proof-of-concept for, and facilitate maintenance and acquisition economies of scale with, potential future ALM systems on other corridors, such as in outer Queens and Brooklyn, or potentially New Jersey.

Hitachi Driverless Metro railcars are used on Honolulu’s Skyline, are proven in the US (important to the MTA), and are cheaper at \$2.2 million/car (need to inflation-adjust) without bundled maintenance (it is bundled, as are operations, but costs are given separately).  This is a Buy America cost, while the Alstom Metropolis Saint-Laurent cars are built in India.

With a 32-min runtime, 2-min turns, and a 90% utilization rate, 38 trainsets are needed.
At 4 cars/trainset and using Honolulu’s costs of \$2.2 million/car inflation-adjusted to June 2025, this fleet would cost \$421 million.
Assuming #link("https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[3.5% future inflation]#super[#link(<src12>)[\[12\]]] (used by the MTA’s 20-Year Needs Comparative Evaluation), this would be \$444 million in 2027,#footnote[ceil(((32 min + 2 min) \* 2) / 2 min / 90%) trainsets \* 4 cars/trainset \* \$2.2 million/car \* 124% (Apr 2020 to Jan 2025 inflation) \* 103.5%^(2027-2025)] only slightly higher than the MTA’s estimated \$432 million for fleet cost.
But this is with 2-min peak headways, not 5-min peak headways.
And with a 92% utilization rate, the cost comes down to exactly \$432 million.

#underline[Hitachi Driverless Metro Honolulu]

cost: #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[\$2.2 million/car]#super[#link(<src13>)[\[13\]]] (#link("http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[contract in 2011]#super[#link(<src14>)[\[14\]]], #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[first delivered on March 25, 2016]#super[#link(<src15>)[\[15\]]], #link("https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[last delivered on April 24, 2024]#super[#link(<src16>)[\[16\]]])

fleet: 80 cars

cost/length in June 2025: \$2.2 million/car / 65 ft/car \* 1.26 (April 2020 to June 2025 inflation) = \$140k/m

length: 65 ft (19.81 m)

width: 10 ft (3.048 m)

weight: #link("http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[72,000 lbs per 65 ft AW0 car]#super[#link(<src17>)[\[17\]]]

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

weight: #link("https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[232 t per 76.2 m AW3 4-car trainset]#super[#link(<src18>)[\[18\]]]

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
+ #link("https://www.mta.info/document/72081#page=16")[https://www.mta.info/document/72081\#page=16] (archived #link("https://web.archive.org/web/20260518002035id_/https://www.mta.info/document/72081#page=16")[May 18, 2026]) <src2>
+ #link("https://www.mta.info/document/72081")[https://www.mta.info/document/72081] (archived #link("https://web.archive.org/web/20260518002035/https://www.mta.info/document/72081")[May 18, 2026]) <src3>
+ #link("https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up] (archived #link("https://web.archive.org/web/20260829123215/https://www.governor.ny.gov/news/governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=ridership%20projections%20to-,160%2C000,-per%20day%2C%20up")[August 29, 2026]) <src4>
+ #link("https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml\#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily] (archived #link("https://web.archive.org/web/20260912070442/https://www.nyc.gov/html/dot/html/infrastructure/bqecentral.shtml#:~:text=130%2C000%20vehicles%20use%20the%20BQE%20daily")[September 12, 2026]) <src5>
+ #link("https://anita.garden/nycriders/")[https://anita.garden/nycriders/] (archived #link("https://web.archive.org/web/20260822120542/https://anita.garden/nycriders/")[August 22, 2026]) <src6>
+ #link("https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase\#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes] (archived #link("https://web.archive.org/web/20260518022508/https://www.mta.info/press-release/icymi-governor-hochul-announces-interborough-express-advancing-planning-active-phase#:~:text=This%20refinement%20has%20reduced%20projected%20running%20times%20of%20the%20new%20line%20from%2039%20minutes%20to%2032%20minutes")[May 18, 2026]) <src7>
+ #link("https://arxiv.org/abs/2408.01562")[https://arxiv.org/abs/2408.01562] (archived #link("https://web.archive.org/web/20260416140808/https://arxiv.org/abs/2408.01562")[April 16, 2026]) <src8>
+ #link("https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/] (archived #link("https://web.archive.org/web/20260515114508/https://rail.kychung.com/en/2d-en/guangzhou-metro-line-6-csr-sifang-emu/")[May 15, 2026]) <src9>
+ #link("http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html] (archived #link("https://web.archive.org/web/20250828081856/http://sn.people.com.cn/n2/2020/0102/c378296-33682040.html")[August 28, 2025]) <src10>
+ #link("https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16] (archived #link("https://web.archive.org/web/20251008074227/https://timesmachine.nytimes.com/timesmachine/1980/09/27/111295852.html?pageNumber=16")[October 8, 2025]) <src11>
+ #link("https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[https://future.mta.info/documents/20-YearNeedsAssessment\_ComparativeEvaluation.pdf\#page=3] (archived #link("https://web.archive.org/web/20260821175057id_/https://future.mta.info/documents/20-YearNeedsAssessment_ComparativeEvaluation.pdf#page=3")[August 21, 2026]) <src12>
+ #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html\#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to] (archived #link("https://web.archive.org/web/20210120105720/https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html#:~:text=cars%2C%20valued%20at-,%242.2%20million%20each,-and%20designed%20to")[January 20, 2021]) <src13>
+ #link("http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf] (archived #link("https://web.archive.org/web/20251013003705/http://hartdocs.honolulu.gov/docushare/dsweb/Get/Document-14729/Agreement.pdf")[October 13, 2025]) <src14>
+ #link("https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html] (archived #link("https://web.archive.org/web/20210120105720/https://www.govtech.com/fs/honolulus-first-two-rail-cars-for-new-transit-system-arrive-on-oahu.html")[January 20, 2021]) <src15>
+ #link("https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train] (archived #link("https://web.archive.org/web/20260419060929/https://www.masstransitmag.com/rail/vehicles/press-release/55021467/honolulu-authority-for-rapid-transportation-hart-honolulu-accepts-delivery-of-20th-train")[April 19, 2026]) <src16>
+ #link("http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[http://www.staradvertiser.com/news/20110322\_Have\_a\_seat.html\#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.] (archived #link("https://web.archive.org/web/20140808010159/http://www.staradvertiser.com/news/20110322_Have_a_seat.html#:~:text=to%20weigh%20about-,72%2C000%20pounds,-.")[August 8, 2014]) <src17>
+ #link("https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[https://rem.info/en/rolling-stock\#:~:text=Maximum%20weight%3A%20232%20tonnes] (archived #link("https://web.archive.org/web/20260616144315/https://rem.info/en/rolling-stock#:~:text=Maximum%20weight%3A%20232%20tonnes")[June 16, 2026]) <src18>
+ #link("https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/] (archived #link("https://web.archive.org/web/20260719213805/https://qns.com/2024/10/mta-looking-to-dig-tunnel-underneath-cemetery-in-middle-village-for-interborough-express-scrapping-street-running-plan/")[July 19, 2026]) <src19>
+ #link("https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/] (archived #link("https://web.archive.org/web/20260513035917/https://www.6sqft.com/mta-awards-166m-design-contract-for-interborough-express/")[May 13, 2026]) <src20>
+ #link("https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[https://transitcosts.com/wp-content/uploads/Italian\_Case\_Study.pdf] (archived #link("https://web.archive.org/web/20260512184237/https://transitcosts.com/wp-content/uploads/Italian_Case_Study.pdf")[May 12, 2026]) <src21>
+ #link("https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[https://en.wikipedia.org/wiki/Automatic\_train\_operation\#Accidents\_and\_incidents\_involving\_ATO] (archived #link("https://web.archive.org/web/20260906195011/https://en.wikipedia.org/wiki/Automatic_train_operation#Accidents_and_incidents_involving_ATO")[September 6, 2026]) <src22>
