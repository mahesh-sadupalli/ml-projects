import { createEntry } from './store';

const SEED_ENTRIES = [
  {
    title: 'Bridge structural cracks detected on Highway 12',
    content: 'Severe cracking observed on the eastern support column of the Highway 12 overpass bridge. Cracks are approximately 15cm wide and extend vertically for about 2 meters. The concrete appears to be deteriorating with visible rebar exposure. Water damage evident from recent rainfall seeping through the cracks. This bridge carries heavy traffic daily and the structural integrity may be compromised. Urgent engineering assessment needed before the situation worsens. Load-bearing capacity tests should be conducted immediately.',
    category: 'Infrastructure',
    location_name: 'Highway 12, East Sector',
  },
  {
    title: 'Water contamination at Village Well #3',
    content: 'Water samples collected from Village Well #3 show elevated levels of bacterial contamination. Residents have reported gastrointestinal symptoms over the past week. The well serves approximately 200 households. Emergency water purification tablets have been distributed. The contamination source appears to be agricultural runoff from the nearby livestock farm. Immediate intervention required to prevent outbreak. Boil water advisory issued to all affected households.',
    category: 'Health',
    location_name: 'Riverside Village, Well #3',
  },
  {
    title: 'Crop yield survey - North District farms',
    content: 'Completed yield assessment across 12 farms in North District. Rice paddy yields are down 23% compared to last season due to irregular rainfall patterns. Wheat crops showing improved results with new drought-resistant seed varieties, up 15% from baseline. Irrigation systems functioning well in 8 of 12 farms. Four farms report water shortage issues. Soil samples collected for laboratory analysis. Farmers are requesting additional fertilizer support for the next planting cycle.',
    category: 'Agriculture',
    location_name: 'North District Farmlands',
  },
  {
    title: 'Community health screening results - March 2026',
    content: 'Conducted health screening for 340 residents at the community center. Key findings: 12% show signs of mild malnutrition, particularly in children under 5. Blood pressure readings elevated in 28% of adults over 40. Positive progress on vaccination coverage now at 89% for children. Three suspected cases of dengue fever have been referred to the district hospital for confirmation. Mental health concerns reported by 15% of participants, mainly related to economic stress.',
    category: 'Health',
    location_name: 'Community Center, Block A',
  },
  {
    title: 'Deforestation monitoring - Western Ridge',
    content: 'Satellite imagery comparison shows 8.5 hectares of forest cover lost in the Western Ridge area over the past 3 months. Ground verification confirms illegal logging activity near coordinates 12.34N, 98.76E. Species affected include teak and rosewood. Wildlife corridors appear disrupted. Local forest rangers have been notified but lack resources for enforcement. Soil erosion already visible on cleared slopes. Recommended immediate intervention before monsoon season causes landslides.',
    category: 'Environment',
    location_name: 'Western Ridge Forest',
  },
  {
    title: 'School infrastructure assessment - District 5',
    content: 'Inspected 6 schools in District 5. Building conditions vary significantly. Two schools have leaking roofs requiring urgent repair before monsoon. Classroom furniture adequate in 4 schools. Computer lab equipment outdated in all 6 schools. Sanitation facilities improved since last assessment with new toilets installed in 3 schools. Student attendance is good with 92% average across all schools. Teachers report need for updated textbooks and teaching materials.',
    category: 'Community',
    location_name: 'District 5 Schools',
  },
  {
    title: 'Road accident hotspot analysis - Quarter report',
    content: 'Analysis of accident data from January to March 2026 reveals dangerous pattern at the intersection of Main Road and Market Street. 14 accidents recorded in this quarter alone, up 40% from previous quarter. Poor visibility due to damaged street lighting is a contributing factor. Speed limit signage missing at two critical points. Recommended installing speed bumps, repairing lights, and adding reflective road markings. Two fatalities occurred at this location, making it the highest priority safety concern.',
    category: 'Safety',
    location_name: 'Main Road & Market St Junction',
  },
  {
    title: 'Positive: Solar panel installation progress',
    content: 'Excellent progress on the community solar panel project. 45 out of 60 planned installations completed this month. Energy output measurements show average of 4.2 kWh per household per day, exceeding the 3.5 kWh target. Community feedback has been overwhelmingly positive with residents reporting 40% reduction in electricity bills. The installation team has improved efficiency and can now complete 3 installations per day. Project is ahead of schedule and under budget.',
    category: 'Infrastructure',
    location_name: 'Solar Farm, South Valley',
  },
  {
    title: 'Wildlife census - Wetland Sanctuary',
    content: 'Annual bird census at the Wetland Sanctuary completed. Total species count: 127, up from 112 last year. Notable sighting of 3 endangered painted storks nesting in the eastern marsh. Migratory bird populations stable. Water levels adequate for current season. Fish stock appears healthy supporting the ecosystem. However, plastic waste accumulation increasing along the southern bank. Volunteer cleanup organized for next weekend. Overall ecosystem health trending positive.',
    category: 'Environment',
    location_name: 'Wetland Sanctuary',
  },
  {
    title: 'Emergency: Flooding in low-lying residential area',
    content: 'Critical flooding reported in Sector 7 residential zone following 48 hours of continuous heavy rainfall. Water levels reached 1.2 meters in several homes. Approximately 150 families displaced and moved to emergency shelter at District School. Emergency pumping operations underway but drainage system overwhelmed. Food and clean water supplies being coordinated. Medical team deployed for potential waterborne disease prevention. Power supply cut to affected area as safety precaution. Dam upstream showing dangerous water levels requiring monitoring.',
    category: 'Safety',
    location_name: 'Sector 7 Residential',
  },
  {
    title: 'Market price survey - Essential commodities',
    content: 'Weekly price tracking of essential commodities across 8 local markets. Rice prices stable at $0.45/kg. Vegetable prices increased 12% due to transport disruptions. Cooking oil showing slight decline. Medicine availability improved at 6 of 8 markets. Two markets report shortage of infant formula. Consumer confidence appears moderate. Traders report supply chain functioning normally except for fresh produce from northern regions affected by road conditions.',
    category: 'Community',
    location_name: 'Central Market District',
  },
  {
    title: 'Pest infestation alert - Eastern farmlands',
    content: 'Significant pest outbreak detected across eastern farmlands. Brown planthopper population has reached critical threshold in rice paddies covering approximately 200 hectares. Early morning inspection revealed damage to 30% of standing crop. Farmers using traditional pest control methods with limited success. Agricultural extension officers have been requested to assess situation and recommend integrated pest management approaches. If left untreated, estimated crop loss could reach 60% in affected areas within two weeks.',
    category: 'Agriculture',
    location_name: 'Eastern Farmlands, Zone B',
  },
];

export async function seedDatabase(): Promise<number> {
  let count = 0;
  for (const data of SEED_ENTRIES) {
    await createEntry(data);
    count++;
  }
  return count;
}
