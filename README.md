# Wealth distribution, 2021 and 2024

Two log-scale charts compare estimated adult counts in decade-wide personal net-wealth bands from $10,000–$100,000 through $100 billion–$1 trillion.

A third paired chart contrasts the number of adults in each 2021 band with its share of global household wealth. Its nine bands, including the group below $10k, reconcile to Credit Suisse's full universe of 5.2985 billion adults and $463.6 trillion. WIR divides Credit Suisse's $1m+ totals into exact decade bands. This avoids incompatible global denominators, but the upper-band percentages remain harmonized estimates rather than directly published shares.

The paired 2024 chart keeps the same nine decade-wide bands in both panels. No source publishes total wealth for all three non-billionaire decade bands. Their totals are therefore modelled from the published counts above $1m, $10m, $100m and $1b. Within each decade, a power-law tail estimates average wealth; the resulting three totals are scaled proportionally to reconcile to UBS's $226.47 trillion millionaire total after subtracting $14.2096 trillion of Forbes billionaire wealth. A power-law tail means that the population falls at an approximately steady rate as wealth rises tenfold. The Forbes tabulation reproduces the published count of 2,781 exactly. All nine wealth bars reconcile to UBS's $470.51 trillion covered total.

Each paired chart also has a `_linear` version. It keeps the wealth panel unchanged and replaces the top panel's logarithmic population axis with a linear axis measured in billions of adults.

Charts are exported as 300 DPI PNG files. Dollar ranges are paired with familiar tier names such as millionaire, decamillionaire, centimillionaire, and centibillionaire.

Two additional views show wealth share relative to population share:

- `wealth_population_ratio_2021` divides each band's wealth share by its adult share; 1× is the global-average reference.
- `wealth_population_ratio_2024` shows the same measure for 2024; pale bars identify the three modelled wealth bands.

The chart cannot add to the full human population. Both reports measure wealth per adult; children are excluded and household wealth is assigned to adults. The 2021 world population was about 7.8 billion, not yet 8 billion.

The first two bands come from the Credit Suisse *Global Wealth Databook 2022*. Every band above $1 million comes directly from Table 7.1 of the World Inequality Lab's *World Inequality Report 2022*. Both sources measure 2021 and define wealth as assets minus debts at market exchange rates.

The sources independently report 62.5 million and 62.17 million adults above $1 million, a difference of about 0.5%. Nevertheless, all values are statistical estimates rather than a global census.

Independent checks support the main scale, not every narrow band. WIR's market-exchange-rate global wealth is about $470.4 trillion versus Credit Suisse's $463.6 trillion (1.5% apart); Knight Frank estimates 69.75 million millionaires versus 62.5 million (11.6% apart); and Forbes counts 2,755 billionaires worth $13.1 trillion versus WIR's 2,750 worth $13.07 trillion (both under 0.3% apart). The exact wealth shares within $1m–$1b remain modelled allocations, not a multi-source consensus.

The chart reports Pearson's correlation between the logarithmic wealth-band midpoint and logarithmic population count. It does not draw a regression line or claim that the distribution follows an exact power law.

The near-2025 comparison uses end-2024 data, the newest snapshot with directly reported totals at the required $1m, $10m and $100m boundaries. UBS reports 60 million adults above $1m; Knight Frank reports 2,341,378 above $10m and 104,060 above $100m; Forbes reports 2,781 billionaires, including 213 at $10b–$100b and 14 at $100b+. The plotted bands are simple subtractions of those totals, not interpolations. UBS's “global” estimate covers 56 markets representing more than 92% of global wealth, and its 60-million total is rounded.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make all
make test
```

The verified inputs and source URLs are stored in `data/*.csv`; the script performs no web requests.

## Sources

- [Credit Suisse Global Wealth Databook 2022](https://bibbase.org/f/nKAPSyp34A9azBzJd/Shorrocksetal2022.pdf)
- [World Inequality Report 2022](https://wir2022.wid.world/www-site/uploads/2021/12/WorldInequalityReport2022_Full_Report.pdf)
- [Knight Frank Wealth Report 2022](https://www.knightfrank.com/research/reports/wealthreport/archive-editions/the-wealth-report-2022/contentassets/the-knight-frank-wealth-report-2022.pdf)
- [Forbes World’s Billionaires 2021](https://www.forbes.com/sites/kerryadolan/2021/04/06/forbes-35th-annual-worlds-billionaires-list-facts-and-figures-2021/)
- [UBS Global Wealth Report 2025](https://www.ubs.com/content/dam/assets/wm/static/noindex/gwr-2025-digital-updated.pdf)
- [Knight Frank Wealth Report 2025](https://content.knightfrank.com/research/3000/documents/en/the-wealh-report-2025-2025-12186.pdf)
- [Forbes World’s Billionaires 2024](https://www.forbes.com/sites/chasewithorn/2024/04/02/forbes-38th-annual-worlds-billionaires-list-facts-and-figures-2024/)
- [Public tabulation of Forbes World’s Billionaires 2024](https://www.kaggle.com/datasets/vincentcampanaro/forbes-worlds-billionaires-list-2024/data)

## License

The MIT License applies to this repository's source code. Third-party reports
and source data remain subject to their respective owners' terms.
